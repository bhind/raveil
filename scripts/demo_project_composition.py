#!/usr/bin/env python3
"""Actual cached RTL demo for T-0197; never a hardware-performance measurement."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raveil import project_composition as composition
from raveil.project import Project, init_project, encoded, digest, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists() or target.is_symlink() or not target.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("demo output must be a new directory below repository artifacts")
    target.parent.mkdir(parents=True, exist_ok=True)
    root = init_project(target)
    biased = json.loads((ROOT / "examples/graph-workloads/inputs/sensor-energy-bias-descriptor.json").read_text())
    raw = copy.deepcopy(biased)
    raw["graph_id"] = "sensor-energy-raw"
    raw["nodes"] = raw["nodes"][:2] + [{"id": "store", "op": "STORE_U32", "input": "energy"}]
    values = [0, 1, 65535, 65536, 0xffffffff, 0x80000000, 17]
    words = [values[i % len(values)] for i in range(324)]
    write_new(root / "inputs/shared.json", encoded({"schema": "raveil.graph-input/v1", "words": words}))
    for label, descriptor in (("raw", raw), ("biased", biased)):
        write_new(root / f"inputs/{label}.json", encoded(descriptor))
        write_new(root / f"recipes/{label}.json", encoded({"schema": "raveil.project-recipe/v2",
                  "kind": "graph-device", "descriptor": f"{label}.json", "input": "shared.json"}))
    os.environ.setdefault("RAVEIL_SIMULATOR_REUSE", "1")
    project = Project(root)
    outputs = [("raw", "raw"), ("biased", "biased")]
    record = composition.compose(project, "shared.json", outputs)
    if record["status"] != "succeeded":
        raise RuntimeError(record["error"])
    composition.load(project, record["composition_id"])
    for slot, entry in enumerate(record["children"]):
        path = root / "compositions" / record["composition_id"] / "children" / str(slot) / "runs" / entry["run_id"] / "workspace/output.bin"
        actual = struct.unpack("<256I", path.read_bytes())
        expected = [0] * 256
        for row in range(8):
            for col in range(8):
                x = words[(row + 1) * 10 + col + 1]
                expected[row * 8 + col] = (x * x + (17 if slot else 0)) & 0xffffffff
        if actual != tuple(expected):
            raise RuntimeError("independent scalar formula differs")
    checks = 0
    def cancelled():
        nonlocal checks
        checks += 1
        return checks == 2
    interrupted = composition.compose(project, "shared.json", outputs, cancelled=cancelled)
    if interrupted["status"] != "incomplete" or len(interrupted["children"]) != 1:
        raise RuntimeError("between-child cancellation did not remain incomplete")
    composition.load(project, interrupted["composition_id"])
    receipt = {"schema": "raveil.project-composition-demo/v1", "evidence": "rtl-simulation-functional",
               "performance": "not-measured", "complete": record["composition_id"],
               "incomplete": interrupted["composition_id"], "scalar_words_checked": 512,
               "cancellation": "host boundary between actual RTL child invocations; not an in-flight device cancellation",
               "children": record["children"],
               "implementation": {name: digest((ROOT / name).read_bytes()) for name in
                 ("raveil/project.py", "raveil/project_composition.py", "scripts/demo_project_composition.py")}}
    write_new(root / "demo-receipt.json", encoded(receipt))
    print(composition.inspect(project, record["composition_id"]))
    print(composition.inspect(project, interrupted["composition_id"]))
    print(json.dumps({"status": "OK", "scalar_words_checked": 512, "evidence": receipt["evidence"]}))


if __name__ == "__main__":
    main()
