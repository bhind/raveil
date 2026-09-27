"""Offline actual-core workload/recovery evidence through the board bridge.

Private cooperative workspace only. No device access, performance claim, or
signed attestation. Source hashes and regenerated inputs bind the local run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import tempfile

from . import graph_device_board_bundle as board
from . import graph_device_axi4lite_export as rtl
from . import graph_device_dag as dag
from . import graph_device_affine as affine
from . import graph_device_mvp as mvp
from .graph_device_submit import admit

ROOT = board.ROOT
IMAGE = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
SOURCES = sorted(set((*dag.SOURCE_PATHS, *affine.SOURCE_PATHS, *mvp.SOURCE_PATHS,
    "raveil/graph_device_board_execute.py", "raveil/graph_device_submit.py",
    "raveil/graph_device_board_bundle.py", "raveil/graph_device_axi4lite_export.py",
    "hardware/chisel/graph_device_axi4lite_transport.h",
    "hardware/fpga/board_execute_test.cpp", "hardware/fpga/test-board-execute-in-container.sh")))
CASES = (("five-point", 1), ("compact-horizontal-three-point", 2),
         ("vertical-three-point", 4), ("five-point", 5))
MARKER = b"BoardExecute-V1 status=OK model_instances=1 matrix_completed=4 cancelled=1 recovery_completed=1 evidence=rtl-simulation-functional performance=not-measured\n"

class BoardExecuteError(ValueError): pass

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def read(path: Path) -> bytes:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 64 << 20:
        raise BoardExecuteError(f"unsafe file: {path.name}")
    return path.read_bytes()

def tree(root: Path) -> dict:
    if not stat.S_ISDIR(root.lstat().st_mode): raise BoardExecuteError("unsafe directory")
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        rel = path.relative_to(root).as_posix()
        if stat.S_ISDIR(mode): result[rel] = {"directory": True}
        else:
            data = read(path); result[rel] = {"bytes": len(data), "sha256": sha(data)}
    return result

def sources() -> dict: return {name: sha(read(ROOT / name)) for name in SOURCES}

def generated(root: Path) -> None:
    root.mkdir()
    dag.prepare(root / "matrix"); dag.prepare(root / "recovery")

def prepare(bundle: Path, output: Path) -> dict:
    manifest = board.verify(bundle)
    if output.is_symlink() or output.exists(): raise BoardExecuteError("output already exists")
    target = output.resolve()
    if not target.is_relative_to((ROOT / "artifacts").resolve()): raise BoardExecuteError("output must be below artifacts")
    # Fixed existing catalogue only; no new request/opcode admission is added.
    submissions = [admit(path, seed, ROOT) for path, seed in zip(dag.GRAPH_PATHS, (1, 2, 4))]
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        generated(staging / "inputs")
        packet = {"schema": "raveil.board-execute-input/v1", "base": manifest["base"],
                  "bundle_sha256": sha(read(bundle / "manifest.json")), "sources": sources(),
                  "inputs": tree(staging / "inputs"), "submissions": submissions, "image": IMAGE}
        target.parent.mkdir(parents=True, exist_ok=True); target.mkdir()
        shutil.copytree(bundle, target / "bundle", symlinks=True)
        shutil.copytree(staging / "inputs", target / "inputs")
        rtl._exclusive(target / "input.json", rtl._canonical(packet))
    verify_inputs(target)
    return packet

def verify_inputs(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir(): raise BoardExecuteError("unsafe run root")
    packet = json.loads(read(root / "input.json"))
    manifest = board.verify(root / "bundle")
    with tempfile.TemporaryDirectory() as temporary:
        expected_inputs = Path(temporary) / "inputs"; generated(expected_inputs)
        expected = {"schema": "raveil.board-execute-input/v1", "base": manifest["base"],
                    "bundle_sha256": sha(read(root / "bundle/manifest.json")), "sources": sources(),
                    "inputs": tree(expected_inputs),
                    "submissions": [admit(path, seed, ROOT) for path, seed in zip(dag.GRAPH_PATHS, (1, 2, 4))], "image": IMAGE}
    if packet != expected or tree(root / "inputs") != expected["inputs"]:
        raise BoardExecuteError("source, bundle or generated input identity differs")
    return packet

def trace_summary(data: bytes, base: int, expected_outputs: list[bytes]) -> dict:
    events = []; resets = []; lines = data.decode("ascii").splitlines()
    if not data.endswith(b"\n") or not 1000 < len(lines) < 100000:
        raise BoardExecuteError("trace bounds differ")
    for line in lines:
        if line == "reset": resets.append(len(events)); continue
        fields = line.split()
        if len(fields) != 7 or fields[1] not in {"read", "write"}: raise BoardExecuteError("trace schema")
        seq, rel, absolute, value, response, hold = [int(fields[i]) for i in (0, 2, 3, 4, 5, 6)]
        if seq != len(events) or not 0 <= rel < 0x4000 or rel % 4 or absolute != base + rel or not 0 <= value <= 0xffffffff or response not in (0, 2, 3) or hold != 1 + seq % 3:
            raise BoardExecuteError("trace address/sequence/value/hold differs")
        events.append((fields[1], rel, value, response))
    if len(resets) != 2 or resets[0] != 0: raise BoardExecuteError("reset count differs")
    at = resets[1]
    if not 2 <= at < len(events) - 2: raise BoardExecuteError("reset position differs")
    if events[at-2] != ("write", 0x10, 1, 0) or events[at-1][0:2] != ("read", 0x14) or events[at-1][3] != 0 or not events[at-1][2] & 1:
        raise BoardExecuteError("reset did not interrupt busy execution")
    if events[at] != ("read", 0x14, 0, 0) or events[at+1][0:2] != ("read", 0x1000) or events[at+1][3] != 2:
        raise BoardExecuteError("reset stale-output rejection differs")
    if sum(kind == "read" and 0x1000 <= rel < 0x1400 and response == 0
           for kind, rel, value, response in events[:at]) != 4 * 256:
        raise BoardExecuteError("reset/recovery output order differs")
    observed_outputs = [(rel, value) for kind, rel, value, response in events
                        if kind == "read" and 0x1000 <= rel < 0x1400 and response == 0]
    expected_reads = [(0x1000 + 4 * index, word) for payload in expected_outputs
                      for index, word in enumerate(struct.unpack("<256I", payload))]
    if observed_outputs != expected_reads:
        raise BoardExecuteError("trace output addresses/data differ from independent oracle")
    counts = {"transactions": len(events), "reset_assertions": len(resets)}
    for name, lo, hi, op in (("output_reads",0x1000,0x1400,"read"),("config_writes",0x2400,0x2440,"write"),("program_writes",0x3400,0x3480,"write")):
        counts[name] = sum(kind == op and lo <= rel < hi and response == 0 for kind, rel, value, response in events)
    if counts["output_reads"] != 5 * 256 or counts["config_writes"] < 5 * 16 or counts["program_writes"] < 5 * 32:
        raise BoardExecuteError("installation or output transaction count differs")
    return counts

def _results(root: Path, packet: dict) -> dict:
    result = root / "result"
    actual = tree(result)
    expected = dict(packet["inputs"])
    expected_outputs = []
    for phase, cases in (("matrix", CASES), ("recovery", (("five-point", 1),))):
        for graph, seed in cases:
            oracle = read(root / "inputs" / phase / "dag-oracles" / f"{graph}-seed-{seed}.bin")
            expected_outputs.append(oracle)
            for prefix in ("private", "fallback"):
                rel = f"{phase}/{prefix}-output-{graph}-seed-{seed}.bin"
                if read(result / rel) != oracle: raise BoardExecuteError(f"output/oracle mismatch: {rel}")
                expected[rel] = {"bytes": len(oracle), "sha256": sha(oracle)}
    cancelled = "matrix/fallback-output-compact-horizontal-three-point-seed-3.bin"
    oracle = read(root / "inputs/matrix/dag-oracles/compact-horizontal-three-point-seed-3.bin")
    if read(result / cancelled) != oracle: raise BoardExecuteError("cancelled fallback differs")
    expected[cancelled] = {"bytes": len(oracle), "sha256": sha(oracle)}
    observed_files = {"toolchain.txt", "build.log", "simulator.bin", "simulator.sha256", "device.log", "device.stderr", "transactions.log"}
    if set(actual) != set(expected) | observed_files: raise BoardExecuteError("result inventory differs (including cancelled output)")
    if any(actual[name] != metadata for name, metadata in expected.items()): raise BoardExecuteError("result input drift")
    if read(result / "device.stderr"): raise BoardExecuteError("device stderr not empty")
    log = read(result / "device.log")
    if not log.endswith(MARKER) or log.count(MARKER) != 1 or log.count(b"status=CANCELLED output_published=0") != 1 or log.count(b"status=COMPLETED output_published=1") != 5 or b"BoardReset-V1 busy=1 cleared=1 stale_output=denied\n" not in log:
        raise BoardExecuteError("runtime outcome log differs")
    observed_runs = re.findall(rb"^GraphDevice-DAG-RUN-V1 graph=([a-z0-9-]+) seed=([0-9]+) mode=([a-z-]+) status=(COMPLETED|CANCELLED) output_published=([01]) polls=([1-9][0-9]*)$", log, re.MULTILINE)
    expected_runs = [(b"five-point", b"1", b"complete", b"COMPLETED", b"1"),
        (b"compact-horizontal-three-point", b"2", b"complete", b"COMPLETED", b"1"),
        (b"compact-horizontal-three-point", b"3", b"cancel", b"CANCELLED", b"0"),
        (b"vertical-three-point", b"4", b"complete", b"COMPLETED", b"1"),
        (b"five-point", b"5", b"factory-restart", b"COMPLETED", b"1"),
        (b"five-point", b"1", b"complete", b"COMPLETED", b"1")]
    if [item[:5] for item in observed_runs] != expected_runs or any(int(item[5]) > 100000 for item in observed_runs):
        raise BoardExecuteError("runtime case order/identity differs")
    binary_sha = sha(read(result / "simulator.bin"))
    if read(result / "simulator.sha256") != (binary_sha + "  /out/simulator.bin\n").encode(): raise BoardExecuteError("binary identity differs")
    if not read(result / "toolchain.txt").startswith(b"Verilator "): raise BoardExecuteError("tool identity missing")
    summary = trace_summary(read(result / "transactions.log"), packet["base"], expected_outputs)
    control = json.loads(read(root / "container-result.json"))
    if control != {"returncode": 0, "stdout": "", "stderr": ""}:
        raise BoardExecuteError("container outcome differs")
    if json.loads(read(root / "command.json")) != command(root, packet):
        raise BoardExecuteError("container command differs")
    allowed = {"bundle", "inputs", "input.json", "result", "command.json", "container-result.json"}
    if {p.name for p in root.iterdir()} not in (allowed, allowed | {"receipt.json"}):
        raise BoardExecuteError("run inventory differs")
    return {"schema": "raveil.board-execute-result/v1", "evidence": "rtl-simulation-functional", "performance": "not-measured",
            "input_sha256": sha(read(root / "input.json")), "command_sha256": sha(read(root / "command.json")), "container_result_sha256": sha(read(root / "container-result.json")), "files": actual, "trace": summary, "completed": 5, "output_words_per_case": 256,
            "cancelled": 1, "model_instances": 1, "image": IMAGE}

def verify(root: Path) -> dict:
    packet = verify_inputs(root)
    receipt = _results(root, packet)
    if json.loads(read(root / "receipt.json")) != receipt: raise BoardExecuteError("receipt differs")
    return receipt

def command(root: Path, packet: dict) -> list[str]:
    output = root / "result"
    args = ["docker", "run", "--rm", "--pull=never", "--network", "none", "--platform", "linux/amd64"]
    for host, guest in ((ROOT,"/repo"),(root / "bundle","/bundle"),(root / "inputs","/inputs")):
        args += ["--mount", f"type=bind,src={host.resolve()},dst={guest},readonly"]
    args += ["--mount", f"type=bind,src={output.resolve()},dst=/out", IMAGE,
             "bash", "/repo/hardware/fpga/test-board-execute-in-container.sh", f"{packet['base']:08x}"]
    return args

def run(root: Path) -> dict:
    packet = verify_inputs(root)
    if (root / "receipt.json").exists(): raise BoardExecuteError("receipt already exists")
    output = root / "result"; output.mkdir()
    invocation = command(root, packet)
    rtl._exclusive(root / "command.json", rtl._canonical(invocation))
    completed = subprocess.run(invocation, capture_output=True)
    rtl._exclusive(root / "container-result.json", rtl._canonical({"returncode": completed.returncode, "stdout": completed.stdout.decode(errors="replace"), "stderr": completed.stderr.decode(errors="replace")}))
    if completed.returncode: raise BoardExecuteError("container failed; retained output and diagnostics")
    packet = verify_inputs(root)
    receipt = _results(root, packet)
    rtl._exclusive(root / "receipt.json", rtl._canonical(receipt))
    return receipt

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    p = commands.add_parser("prepare"); p.add_argument("bundle", type=Path); p.add_argument("output", type=Path)
    for name in ("run", "verify"):
        p = commands.add_parser(name); p.add_argument("output", type=Path)
    args = parser.parse_args()
    result = prepare(args.bundle, args.output) if args.action == "prepare" else globals()[args.action](args.output)
    print(json.dumps({"status": "OK", "schema": result["schema"]}, sort_keys=True))

if __name__ == "__main__": main()
