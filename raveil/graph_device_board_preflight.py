"""Source-bound generic Yosys structural checks; not FPGA mapping or PPA."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from . import graph_device_board_bundle as board
from . import graph_device_board_execute as evidence
from . import graph_device_axi4lite_export as rtl

ROOT = board.ROOT
IMAGE = "sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169"
YOSYS_SHA = "a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508"
SCRIPT = "hardware/fpga/board_structural_preflight.ys"
SOURCES = (SCRIPT, "raveil/graph_device_board_preflight.py", "raveil/graph_device_board_bundle.py",
           "raveil/graph_device_board_execute.py", "raveil/graph_device_axi4lite_export.py")
PORTS = {"aclk": ("input", 1), "aresetn": ("input", 1)}
for name, direction, width in (
    ("awaddr","input",32),("awprot","input",3),("awvalid","input",1),("awready","output",1),
    ("wdata","input",32),("wstrb","input",4),("wvalid","input",1),("wready","output",1),
    ("bresp","output",2),("bvalid","output",1),("bready","input",1),
    ("araddr","input",32),("arprot","input",3),("arvalid","input",1),("arready","output",1),
    ("rdata","output",32),("rresp","output",2),("rvalid","output",1),("rready","input",1)):
    PORTS["s_axi_" + name] = (direction, width)

class BoardPreflightError(ValueError): pass

def script(base: int) -> bytes:
    board._settings(base, 100)
    template = evidence.read(ROOT / SCRIPT)
    if template.count(b"@BASE@") != 1: raise BoardPreflightError("script placeholder differs")
    return template.replace(b"@BASE@", str(base).encode())

def source_identity() -> dict:
    return {name: evidence.sha(evidence.read(ROOT / name)) for name in SOURCES}

def check_netlist(payload: bytes, base: int) -> None:
    modules = json.loads(payload)["modules"]
    if set(modules) != {"GraphDeviceBoardBridge"}: raise BoardPreflightError("flattened closure differs")
    top = modules["GraphDeviceBoardBridge"]
    if int(top.get("attributes", {}).get("blackbox", "0"), 2): raise BoardPreflightError("blackbox top")
    if int(top.get("parameter_default_values", {}).get("BASE_ADDR", "-1"), 2) != base:
        raise BoardPreflightError("netlist base differs")
    ports = {name: (info["direction"], len(info["bits"])) for name, info in top["ports"].items()}
    if ports != PORTS: raise BoardPreflightError("netlist interface differs")
    if not top.get("cells"): raise BoardPreflightError("empty netlist")
    for cell in top["cells"].values():
        kind = cell["type"]
        if not kind.startswith("$") or "latch" in kind.lower(): raise BoardPreflightError("unresolved module or latch")
    if top.get("processes"): raise BoardPreflightError("unlowered processes")

def command(root: Path) -> list[str]:
    shell = ('set -eu; yosys -V > /out/toolchain.txt; '
             'sha256sum "$(command -v yosys)" | cut -d " " -f 1 > /out/yosys.sha256; '
             f'test "$(cat /out/yosys.sha256)" = {YOSYS_SHA}; '
             'yosys -Q -T -l /out/yosys.log -s /job/preflight.ys')
    args = ["docker", "run", "--rm", "--pull=never", "--network", "none", "--platform", "linux/amd64", "--security-opt", "no-new-privileges=true"]
    for host, guest in ((root / "bundle", "/bundle"), (root, "/job")):
        args += ["--mount", f"type=bind,src={host.resolve()},dst={guest},readonly"]
    return args + ["--mount", f"type=bind,src={(root / 'result').resolve()},dst=/out", IMAGE, "sh", "-c", shell]

def expected_input(root: Path) -> dict:
    bundle = board.verify(root / "bundle")
    return {"schema": "raveil.board-structural-input/v1", "base": bundle["base"],
            "bundle_sha256": evidence.sha(evidence.read(root / "bundle/manifest.json")),
            "sources": source_identity(), "image": IMAGE, "yosys_sha256": YOSYS_SHA}

def verify_inputs(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir(): raise BoardPreflightError("unsafe run root")
    expected = expected_input(root)
    if json.loads(evidence.read(root / "input.json")) != expected: raise BoardPreflightError("input/source identity differs")
    if evidence.read(root / "preflight.ys") != script(expected["base"]): raise BoardPreflightError("script differs")
    if json.loads(evidence.read(root / "command.json")) != command(root): raise BoardPreflightError("command differs")
    return expected

def result(root: Path) -> dict:
    packet = verify_inputs(root)
    outcome = json.loads(evidence.read(root / "outcome.json"))
    if set(outcome) != {"returncode", "stdout", "stderr"} or type(outcome["returncode"]) is not int or outcome["returncode"] != 0:
        raise BoardPreflightError("tool did not succeed")
    files = evidence.tree(root / "result")
    if set(files) != {"toolchain.txt", "yosys.sha256", "yosys.log", "structural.json"}:
        raise BoardPreflightError("result inventory differs")
    if evidence.read(root / "result/yosys.sha256") != (YOSYS_SHA + "\n").encode(): raise BoardPreflightError("tool binary differs")
    if not evidence.read(root / "result/toolchain.txt").startswith(b"Yosys 0.27+3 "): raise BoardPreflightError("tool version differs")
    log = evidence.read(root / "result/yosys.log")
    if b"Found and reported 0 problems." not in log or b"Found and expected 0 SCCs." not in log or b"ERROR:" in log:
        raise BoardPreflightError("strict checks not recorded")
    check_netlist(evidence.read(root / "result/structural.json"), packet["base"])
    allowed = {"bundle", "input.json", "preflight.ys", "command.json", "outcome.json", "result"}
    if {p.name for p in root.iterdir()} not in (allowed, allowed | {"receipt.json"}): raise BoardPreflightError("run inventory differs")
    return {"schema": "raveil.board-structural-receipt/v1", "evidence": "generic-structural-functional", "performance": "not-measured",
            "vendor_synthesis": "not-run", "mapping": "not-run", "input_sha256": evidence.sha(evidence.read(root / "input.json")),
            "command_sha256": evidence.sha(evidence.read(root / "command.json")), "outcome_sha256": evidence.sha(evidence.read(root / "outcome.json")), "files": files}

def run(bundle: Path, output: Path) -> dict:
    board.verify(bundle)
    if output.is_symlink() or output.exists(): raise BoardPreflightError("output already exists")
    root = output.resolve()
    if not root.is_relative_to((ROOT / "artifacts").resolve()): raise BoardPreflightError("output must be below artifacts")
    root.parent.mkdir(parents=True, exist_ok=True); root.mkdir()
    shutil.copytree(bundle, root / "bundle", symlinks=True)
    packet = expected_input(root)
    rtl._exclusive(root / "input.json", rtl._canonical(packet))
    rtl._exclusive(root / "preflight.ys", script(packet["base"]))
    invocation = command(root)
    rtl._exclusive(root / "command.json", rtl._canonical(invocation))
    verify_inputs(root); (root / "result").mkdir()
    completed = subprocess.run(invocation, capture_output=True)
    rtl._exclusive(root / "outcome.json", rtl._canonical({"returncode": completed.returncode, "stdout": completed.stdout.decode(errors="replace"), "stderr": completed.stderr.decode(errors="replace")}))
    if completed.returncode: raise BoardPreflightError("structural preflight failed; diagnostics retained")
    receipt = result(root)
    rtl._exclusive(root / "receipt.json", rtl._canonical(receipt))
    return receipt

def verify(root: Path) -> dict:
    receipt = result(root)
    if json.loads(evidence.read(root / "receipt.json")) != receipt: raise BoardPreflightError("receipt differs")
    return receipt

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    p = commands.add_parser("run"); p.add_argument("bundle", type=Path); p.add_argument("output", type=Path)
    p = commands.add_parser("verify"); p.add_argument("output", type=Path)
    args = parser.parse_args()
    value = run(args.bundle, args.output) if args.action == "run" else verify(args.output)
    print(json.dumps({"status": "OK", "evidence": value["evidence"], "mapping": value["mapping"]}, sort_keys=True))

if __name__ == "__main__": main()
