#!/usr/bin/env python3
"""Send malformed complete session envelopes to the actual guest admission path."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from raveil import fold_session as s
from raveil.sonatine_fold import command_for,digest
from scripts.affine_fold_vectors import vectors


def envelope(children,count=None):
    body=struct.pack("<4IQ",s.MAGIC,1,32+sum(map(len,children)),len(children) if count is None else count,99)+b"".join(children)
    return body+struct.pack("<2I",zlib.crc32(body),s.END)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    v=vectors()[0]
    manifest=dict(schema="raveil.fold-session.v1",jobs=[
        dict(name=f"job-{i}",region=v["descriptor"],inputs=v["inputs"]) for i in range(8)])
    original,children=s.encode(manifest,99,list(range(1,9)))
    last=bytearray(children[-1]);struct.pack_into("<I",last,32,0)
    struct.pack_into("<I",last,len(last)-8,zlib.crc32(last[:-8]))
    invalid={"ninth-job":envelope(children+[children[0]]),
             "duplicate-id":envelope([children[0],children[0]]),
             "bad-last-job":envelope(children[:-1]+[bytes(last)]),
             "truncated-footer":original[:-1]}
    rows=[];qemu=shutil.which("qemu-system-riscv64")
    for name,blob in invalid.items():
        target=root/name;target.mkdir()
        (target/"request.bin").write_bytes(blob);shutil.copyfile(args.kernel,target/"kernel.elf")
        command=command_for(qemu,target);(target/"command.json").write_text(json.dumps(command)+"\n")
        proc=subprocess.run(command,capture_output=True,timeout=15,check=True)
        (target/"stdout.log").write_bytes(proc.stdout);(target/"stderr.log").write_bytes(proc.stderr)
        lines=[line for line in proc.stdout.decode().splitlines() if line.startswith("RAVEIL-FOLD")]
        if lines!=["RAVEIL-FOLD-SESSION-REJECT-V1 reason=admission-or-initialization"]:
            raise AssertionError((name,lines))
        rows.append(dict(case=name,request_sha256=digest(target/"request.bin"),no_dispatch=True))
    (root/"report.json").write_text(json.dumps(dict(evidence_class="qemu-emulation-correctness",cases=rows),indent=2)+"\n")
    print(json.dumps(rows))


if __name__=="__main__":main()
