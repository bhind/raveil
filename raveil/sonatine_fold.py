"""MF01 software interpreter on RV64/QEMU; no RTL connection or timing claim."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import secrets
import shutil
import struct
import subprocess
import zlib
from pathlib import Path
from .affine_fold import compile_region, reference, validate_config, MASK
from .fold_evidence import loads, same

MAGIC = 0x51464631
END = 0x46454e44
PREFIX = "RAVEIL-FOLD-RESULT-V1 "


def encode(config, inputs, request_id):
    validate_config(config)
    if type(request_id) is not int or not 0 < request_id < 1 << 64:
        raise ValueError("nonzero uint64 request identity required")
    if not isinstance(inputs, list) or len(inputs) != 2:
        raise ValueError("two input arrays required")
    for values, length in zip(inputs, config[5:7]):
        if not isinstance(values, list) or len(values) != length:
            raise ValueError("input extent mismatch")
        if any(type(v) is not int or not 0 <= v <= MASK for v in values):
            raise ValueError("uint32 input required")
    words = config + inputs[0] + inputs[1]
    size = 40 + len(words)*4
    body = struct.pack("<6IQ", MAGIC, 1, size, len(inputs[0]), len(inputs[1]), 0, request_id)
    body += struct.pack(f"<{len(words)}I", *words)
    return body + struct.pack("<2I", zlib.crc32(body), END)


def parse(stdout, request_id, count):
    lines = [line for line in stdout.splitlines() if line.startswith("RAVEIL-FOLD-RESULT")]
    if len(lines) != 1:
        raise ValueError("missing or duplicate fold result")
    pattern = (r"RAVEIL-FOLD-RESULT-V1 request=([0-9a-f]{16}) status=([1243]) "
               r"approved=([01]) epoch=([0-9]+) sequence=([0-9]+) "
               r"cookie=([0-9a-f]{32}) chunks=([0-2]) version=([02]) "
               r"count=([0-9]+) output=([0-9a-f]+|-)")
    m = re.fullmatch(pattern, lines[0])
    if m is None:
        raise ValueError("malformed fold result")
    rid, status, approved, epoch, seq, cookie, chunks, version, n, values = m.groups()
    if int(rid,16) != request_id:
        raise ValueError("stale fold result")
    success = status == "1" and approved == "1"
    if success:
        if (int(epoch) != request_id or int(seq) != 1 or int(cookie,16) == 0 or
            int(chunks) != (count+127)//128 or version != "2" or
            int(n) != count or not 1 <= count <= 256 or len(values) != 8*count or values == "-"):
            raise ValueError("inconsistent committed fold result")
        output = [int(values[i:i+8],16) for i in range(0,len(values),8)]
    else:
        if approved != "0" or status == "1" or chunks != "0" or version != "0" or n != "0" or values != "-":
            raise ValueError("failure exposes output or claims approval")
        output = []
    return dict(status=int(status), approved=success, epoch=int(epoch),
                sequence=int(seq), cookie=cookie, chunks=int(chunks),
                version=int(version), output=output)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command_for(executable, directory):
    return [executable,"-machine","virt","-cpu","rv64","-m","128M","-smp","1",
            "-bios","none","-nographic","-kernel",str(Path(directory)/"kernel.elf"),
            "-device",f"loader,file={Path(directory)/'request.bin'},addr=0x87ff0000,force-raw=on"]


def run(descriptor, inputs, kernel, destination, *, qemu="qemu-system-riscv64", timeout=15):
    """Freeze inputs/kernel before execution; seal only full semantic agreement."""
    config = compile_region(descriptor)
    expected = reference(descriptor, inputs)
    request_id = secrets.randbits(64) or 1
    request = encode(config, inputs, request_id)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    (destination/"region.json").write_text(json.dumps(descriptor,sort_keys=True)+"\n")
    (destination/"inputs.json").write_text(json.dumps(inputs)+"\n")
    (destination/"request.bin").write_bytes(request)
    shutil.copyfile(kernel,destination/"kernel.elf")
    executable = shutil.which(qemu)
    if executable is None:
        raise ValueError("QEMU executable not found")
    command = command_for(executable,destination)
    if "," in str(destination):
        raise ValueError("QEMU loader path cannot contain commas")
    (destination/"command.json").write_text(json.dumps(command)+"\n")
    version=subprocess.check_output([executable,"--version"],text=True)
    (destination/"qemu-version.txt").write_text(version)
    try:
        proc = subprocess.run(command, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        (destination/"stdout.log").write_bytes(exc.stdout or b"")
        (destination/"stderr.log").write_bytes(exc.stderr or b"")
        raise
    (destination/"stdout.log").write_bytes(proc.stdout)
    (destination/"stderr.log").write_bytes(proc.stderr)
    if proc.returncode:
        raise ValueError(f"QEMU exited {proc.returncode}")
    result = parse(proc.stdout.decode("utf-8"),request_id,len(expected))
    if not result["approved"] or result["output"] != expected:
        raise ValueError("committed output differs from independent SSA reference")
    receipt = dict(schema="raveil.sonatine-fold.v1", evidence_class="qemu-emulation-correctness",
                   request_id=request_id, result=result,
                   qemu_version=version.splitlines()[0],execution_directory=str(destination),
                   qemu_executable=executable,
                   files={p.name:digest(p) for p in destination.iterdir() if p.is_file()})
    (destination/"receipt.tmp").write_text(json.dumps(receipt,indent=2)+"\n")
    (destination/"receipt.tmp").replace(destination/"receipt.json")
    return receipt


def verify(destination):
    destination = Path(destination)
    receipt = loads((destination/"receipt.json").read_text())
    required = {"region.json","inputs.json","request.bin","kernel.elf","command.json","stdout.log","stderr.log","qemu-version.txt"}
    fields = {"schema","evidence_class","request_id","result","qemu_version",
              "execution_directory","qemu_executable","files"}
    if (type(receipt) is not dict or set(receipt) != fields or receipt["schema"] != "raveil.sonatine-fold.v1" or
        receipt["evidence_class"] != "qemu-emulation-correctness" or
        type(receipt["files"]) is not dict or set(receipt["files"]) != required or
        type(receipt["result"]) is not dict or
        any(type(receipt[key]) is not str for key in ("execution_directory","qemu_executable","qemu_version"))):
        raise ValueError("unexpected receipt schema/files")
    for name in required:
        if digest(destination/name) != receipt["files"][name]:
            raise ValueError(f"modified evidence: {name}")
    versions=(destination/"qemu-version.txt").read_text().splitlines()
    if (not versions or not Path(receipt["execution_directory"]).is_absolute() or
        not Path(receipt["qemu_executable"]).is_absolute() or
        loads((destination/"command.json").read_text()) !=
        command_for(receipt["qemu_executable"],receipt["execution_directory"]) or
        receipt["qemu_version"] != versions[0]):
        raise ValueError("execution metadata mismatch")
    descriptor=loads((destination/"region.json").read_text())
    inputs=loads((destination/"inputs.json").read_text())
    config=compile_region(descriptor)
    if encode(config,inputs,receipt["request_id"]) != (destination/"request.bin").read_bytes():
        raise ValueError("request binding mismatch")
    expected=reference(descriptor,inputs)
    result=parse((destination/"stdout.log").read_text(),receipt["request_id"],len(expected))
    if not same(result,receipt["result"]) or not result["approved"] or result["output"] != expected:
        raise ValueError("semantic receipt mismatch")
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--region",type=Path)
    p.add_argument("--inputs",type=Path)
    p.add_argument("--kernel",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--verify",type=Path,help="verify a saved receipt without execution")
    args=p.parse_args()
    if args.verify:
        if any((args.region,args.inputs,args.kernel,args.output)):
            p.error("--verify cannot be combined with execution arguments")
        receipt=verify(args.verify)
    else:
        if not all((args.region,args.inputs,args.kernel,args.output)):
            p.error("--region, --inputs, --kernel and --output are required for execution")
        inputs=loads(args.inputs.read_text())
        if isinstance(inputs,dict):
            from .project_fold import _input
            inputs=_input(args.inputs.read_bytes())
        receipt=run(loads(args.region.read_text()),inputs,args.kernel,args.output)
        verify(args.output)
    print(json.dumps(receipt["result"]))


if __name__ == "__main__":
    main()
