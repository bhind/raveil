#!/usr/bin/env python3
"""Actual32x32 tiled RTL runs, independent scalar checks, edit and cancellation."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raveil import project_tiling as t
from raveil.project import Project, init_project, encoded, digest, tree, write_new


def scalar(words):
    # Full-grid scatter; independent of tile staging and production gather oracle.
    result = [0] * 1024
    for index, value in enumerate(words):
        row, col = divmod(index, 32)
        for r, c in ((row, col), (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= r < 32 and 0 <= c < 32:
                result[r * 32 + c] = (result[r * 32 + c] + value) & 0xffffffff
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists() or target.is_symlink() or not target.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("demo output must be a new directory below repository artifacts")
    sources = ("raveil/project_tiling.py", "raveil/project_composition.py", "raveil/project.py",
               "raveil/project_graph.py", "raveil/graph_device_dag.py", "raveil/graph_device_dynamic.py",
               "scripts/demo_project_tiling.py")
    identities = {name: digest((ROOT / name).read_bytes()) for name in sources}
    target.parent.mkdir(parents=True, exist_ok=True)
    root = init_project(target)
    project = Project(root)
    os.environ.setdefault("RAVEIL_SIMULATOR_REUSE", "1")
    words = [0] * 1024
    for r, c, value in ((0, 0, 1), (0, 31, 2), (31, 0, 4), (31, 31, 8),
                        (15, 15, 0xffffffff), (15, 16, 17), (16, 15, 31),
                        (16, 16, 0x80000000), (0, 16, 13), (16, 0, 23)):
        words[r * 32 + c] = value
    def save():
        (root / "inputs/grid.json").write_bytes(encoded({"schema": t.INPUT, "rows": 32, "columns": 32, "words": words}))
    def execute(label):
        print(f"{label}: starting four actual RTL children", flush=True)
        record = t.run(project, "grid.json")
        if record["status"] != "succeeded":
            raise RuntimeError(record["error"])
        assert record["output"]["words"] == scalar(words)
        assert t.load(project, record["tiling_id"]) == record
        print(f"{label}:1024 scalar cells PASS tiling={record['tiling_id']}", flush=True)
        return record
    save()
    first = execute("original")
    original_tree = tree(root / "tilings" / first["tiling_id"])
    words[15 * 32 + 16] += 1
    save()
    second = execute("edited")
    changed = [index for index, (a, b) in enumerate(zip(first["output"]["words"], second["output"]["words"])) if a != b]
    assert set(changed) == {15 * 32 + 16, 14 * 32 + 16, 16 * 32 + 16, 15 * 32 + 15, 15 * 32 + 17}
    assert tree(root / "tilings" / first["tiling_id"]) == original_tree
    calls = 0
    def cancelled():
        nonlocal calls
        calls += 1
        return calls == 2
    print("cancelled: starting one actual child then host-boundary cancellation", flush=True)
    incomplete = t.run(project, "grid.json", cancelled=cancelled)
    assert incomplete["status"] == "incomplete" and incomplete["output"] is None and len(incomplete["children"]) == 1
    assert t.load(project, incomplete["tiling_id"]) == incomplete
    children = first["children"] + second["children"] + incomplete["children"]
    assert all(all(c[k] == children[0][k] for k in t.BUILD_KEYS) for c in children)
    assert identities == {name: digest((ROOT / name).read_bytes()) for name in sources}, "implementation changed during acceptance"
    receipt = {"schema": "raveil.project-tiling-demo/v1", "status": "passed",
               "evidence_class": "rtl-simulation-functional", "performance": "not-measured",
               "complete": [first["tiling_id"], second["tiling_id"]], "incomplete": incomplete["tiling_id"],
               "scalar_cells_checked": 2048, "changed_cells": changed,
               "original_snapshot_preserved": True, "children": children,
               "cancellation": "host boundary after one actual RTL child; not in-flight device cancellation",
               "implementation": identities}
    write_new(root / "demo-receipt.json", encoded(receipt))
    print(t.history(project))
    print("PASS:2048 independent full-grid cell checks, five changed cells, original preserved, incomplete has no output")


if __name__ == "__main__":
    main()
