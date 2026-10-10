#!/usr/bin/env python3
"""Edit/run/compare saved named outputs with the existing offline RTL backend."""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raveil import project_composition as composition
from raveil.project import Project, init_project, encoded, digest, tree, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists() or target.is_symlink() or not target.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("demo output must be a new directory below repository artifacts")
    sources = ("raveil/project.py", "raveil/project_composition.py", "scripts/demo_project_composition_diff.py")
    identities = {name: digest((ROOT / name).read_bytes()) for name in sources}
    target.parent.mkdir(parents=True, exist_ok=True)
    root = init_project(target)
    biased = json.loads((ROOT / "examples/graph-workloads/inputs/sensor-energy-bias-descriptor.json").read_text())
    raw = copy.deepcopy(biased)
    raw["graph_id"] = "sensor-energy-raw"
    raw["nodes"] = raw["nodes"][:2] + [{"id": "store", "op": "STORE_U32", "input": "energy"}]
    values = [0, 1, 65535, 65536, 0xffffffff, 0x80000000, 17]
    before = [values[i % len(values)] for i in range(324)]
    write_new(root / "inputs/shared.json", encoded({"schema": "raveil.graph-input/v1", "words": before}))
    for label, descriptor in (("raw", raw), ("biased", biased)):
        write_new(root / f"inputs/{label}.json", encoded(descriptor))
        write_new(root / f"recipes/{label}.json", encoded({"schema": "raveil.project-recipe/v2",
                  "kind": "graph-device", "descriptor": f"{label}.json", "input": "shared.json"}))
    os.environ.setdefault("RAVEIL_SIMULATOR_REUSE", "1")
    project = Project(root)
    outputs = [("raw", "raw"), ("biased", "biased")]
    first = composition.compose(project, "shared.json", outputs)
    if first["status"] != "succeeded":
        raise RuntimeError(first["error"])
    old_root = root / "compositions" / first["composition_id"]
    old_manifest = tree(old_root)
    after = before.copy(); after[11] = 2
    (root / "inputs/shared.json").write_bytes(encoded({"schema": "raveil.graph-input/v1", "words": after}))
    biased["nodes"][2]["immediate"] = 23
    (root / "inputs/biased.json").write_bytes(encoded(biased))
    # Reordering also exercises pairing by name, rather than numeric child slot.
    second = composition.compose(project, "shared.json", list(reversed(outputs)))
    if second["status"] != "succeeded":
        raise RuntimeError(second["error"])
    checked = 0
    for record, words, bias in ((first, before, 17), (second, after, 23)):
        composition.load(project, record["composition_id"])
        for entry in record["children"]:
            path = root / "compositions" / record["composition_id"] / "children" / str(entry["slot"]) / "runs" / entry["run_id"] / "workspace/output.bin"
            actual = struct.unpack("<256I", path.read_bytes())
            expected = [0] * 256
            for row in range(8):
                for column in range(8):
                    value = words[(row + 1) * 10 + column + 1]
                    expected[row * 8 + column] = (value * value + (bias if entry["name"] == "biased" else 0)) & 0xffffffff
            if actual != tuple(expected):
                raise RuntimeError("independent scalar output differs")
            checked += 256
    all_saved = tree(root)
    command = [sys.executable, "-m", "raveil", "project", "composition-diff", first["composition_id"], second["composition_id"], "--project", str(root)]
    report = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True).stdout
    if "output: 1/64 active cells changed" not in report or "output: 64/64 active cells changed" not in report:
        raise RuntimeError("named edit deltas differ")
    composition.inspect(project, first["composition_id"])
    if tree(root) != all_saved or tree(old_root) != old_manifest:
        raise RuntimeError("saved evidence changed during comparison or source editing")
    if identities != {name: digest((ROOT / name).read_bytes()) for name in sources}:
        raise RuntimeError("implementation changed during demo")
    write_new(root / "comparison.txt", report.encode())
    receipt = {"schema": "raveil.project-composition-diff-demo/v1", "execution_evidence": "rtl-simulation-functional",
               "comparison_evidence": "host-functional", "performance": "not-measured",
               "before": first["composition_id"], "after": second["composition_id"], "scalar_words_checked": checked,
               "raw_changed_cells": 1, "biased_changed_cells": 64, "old_parent_unchanged": True,
               "comparison_sha256": digest(report.encode()), "implementation": identities,
               "parent_records": {record["composition_id"]: digest((root / "compositions" / record["composition_id"] / "record.json").read_bytes()) for record in (first, second)}}
    write_new(root / "demo-receipt.json", encoded(receipt))
    print(report)
    print(json.dumps({"status": "OK", "scalar_words_checked": checked, "old_parent_unchanged": True}))


if __name__ == "__main__":
    main()
