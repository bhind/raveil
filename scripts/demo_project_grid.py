#!/usr/bin/env python3
"""Local candidate acceptance: editable rectangular grids through actual RTL."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from raveil import grid_kernel as k, project_tiling as t
from raveil.project import Project, init_project, encoded, digest, tree, write_new


def rich():
    return {"schema": k.KERNEL, "graph_id": "general-rich", "nodes": [
        {"id": "decision", "op": "GE_IMM_U32", "input": "bias", "immediate": 1000},
        {"id": "bias", "op": "ADD_IMM_U32", "input": "max", "immediate": 7},
        {"id": "center", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": 0}},
        {"id": "diagonal", "op": "LOAD_U32", "address": {"row_delta": -1, "column_delta": 1}},
        {"id": "sum", "op": "ADD_U32", "inputs": ["center", "diagonal"]},
        {"id": "square", "op": "MUL_U32", "inputs": ["sum", "sum"]},
        {"id": "max", "op": "MAX_U32", "inputs": ["square", "center"]},
        {"id": "out", "op": "STORE_U32", "input": "decision"}]}


def neighbor(bias):
    return {"schema": k.KERNEL, "graph_id": "general-neighbor", "nodes": [
        {"id": "c", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": 0}},
        {"id": "w", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": -1}},
        {"id": "max", "op": "MAX_U32", "inputs": ["c", "w"]},
        {"id": "bias", "op": "ADD_IMM_U32", "input": "max", "immediate": bias},
        {"id": "out", "op": "STORE_U32", "input": "bias"}]}


def scalar(grid, kind, mode, bias):
    # Direct workload formulas, no graph interpreter/compiler/halo helper.
    rows, cols, words = grid["rows"], grid["columns"], grid["words"]
    expected = []
    for r in range(rows):
        for c in range(cols):
            value = words[r * cols + c]
            nr, nc = (r - 1, c + 1) if kind == "rich" else (r, c - 1)
            if mode == "wrap": nr, nc = nr % rows, nc % cols
            elif mode == "clamp": nr, nc = max(0, min(rows - 1, nr)), max(0, min(cols - 1, nc))
            other = words[nr * cols + nc] if 0 <= nr < rows and 0 <= nc < cols else 0
            if kind == "rich":
                summed = (value + other) & 0xffffffff
                squared = summed * summed & 0xffffffff
                expected.append(int(((max(squared, value) + 7) & 0xffffffff) >= 1000))
            else:
                expected.append((max(value, other) + bias) & 0xffffffff)
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.absolute()
    if target.exists() or target.is_symlink() or not target.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("output must be a fresh directory inside artifacts")
    sources = ("raveil/grid_kernel.py", "raveil/project_tiling.py", "raveil/project.py",
               "raveil/project_graph.py", "raveil/project_composition.py", "raveil/graph_device_dag.py",
               "raveil/graph_device_dynamic.py", "scripts/demo_project_grid.py")
    identities = {name: digest((ROOT / name).read_bytes()) for name in sources}
    target.parent.mkdir(parents=True, exist_ok=True)
    root = init_project(target)
    project = Project(root)
    os.environ.setdefault("RAVEIL_SIMULATOR_REUSE", "1")
    cases = []
    def execute(label, rows, columns, kind, mode, bias=5):
        grid = {"schema": k.INPUT, "rows": rows, "columns": columns,
                "words": [(r * 19 + c * 7) % 64 for r in range(rows) for c in range(columns)]}
        grid["words"][0] = 0xffffffff
        if len(grid["words"]) > 10: grid["words"][9] = 0x80000000
        kernel = rich() if kind == "rich" else neighbor(bias)
        (root / "inputs/grid.json").write_bytes(encoded(grid))
        (root / "inputs/kernel.json").write_bytes(encoded(kernel))
        preview = t.check(project, "grid.json", kernel_file="kernel.json", boundary=mode)
        print(f"{label}: {rows}x{columns} {kind} {mode}; {preview['tiles']} actual RTL children", flush=True)
        record = t.run(project, "grid.json", kernel_file="kernel.json", boundary=mode)
        if record["status"] != "succeeded": raise RuntimeError(record["error"])
        expected = scalar(grid, kind, mode, bias)
        assert record["output"]["words"] == expected
        assert t.load(project, record["tiling_id"]) == record
        cases.append({"label": label, "rows": rows, "columns": columns, "kind": kind, "boundary": mode,
                      "bias": bias, "tiling_id": record["tiling_id"], "scalar_cells_checked": len(expected),
                      "children": record["children"]})
        print(f"{label}: all {len(expected)} cells PASS {record['tiling_id']}", flush=True)
        return record
    execute("partial-periodic", 17, 19, "rich", "wrap")
    before = execute("partial-clamped", 3, 17, "neighbor", "clamp")
    snapshot = tree(root / "tilings" / before["tiling_id"])
    execute("singleton-zero", 1, 1, "rich", "zero")
    after = execute("edited-kernel", 3, 17, "neighbor", "clamp", bias=7)
    difference = t.compare(project, before["tiling_id"], after["tiling_id"])
    assert difference["kernel_changed"] and difference["input_cells_changed"] == 0
    assert difference["output_cells_changed"] == 51
    assert tree(root / "tilings" / before["tiling_id"]) == snapshot
    calls = 0
    def cancelled():
        nonlocal calls
        calls += 1
        return calls == 2
    print("cancellation: one actual child then host-boundary stop", flush=True)
    incomplete = t.run(project, "grid.json", kernel_file="kernel.json", boundary="clamp", cancelled=cancelled)
    assert incomplete["status"] == "incomplete" and incomplete["output"] is None and len(incomplete["children"]) == 1
    assert t.load(project, incomplete["tiling_id"]) == incomplete
    children = [child for case in cases for child in case["children"]] + incomplete["children"]
    assert len(children) == 10
    assert all(all(child[key] == children[0][key] for key in t.BUILD_KEYS) for child in children)
    assert identities == {name: digest((ROOT / name).read_bytes()) for name in sources}
    receipt = {"schema": "raveil.general-grid-demo/v1", "status": "passed", "candidate_only": True,
               "evidence_class": "rtl-simulation-functional", "performance": "not-measured",
               "implementation": identities, "cases": cases, "scalar_cells_checked": sum(c["scalar_cells_checked"] for c in cases),
               "difference": difference, "original_snapshot_preserved": True,
               "incomplete": incomplete["tiling_id"], "cancelled_children": incomplete["children"],
               "cancellation": "host boundary, not in-flight device cancellation"}
    write_new(root / "demo-receipt.json", encoded(receipt))
    print("PASS: 426 scalar cells, three shapes, three boundaries, all seven opcodes, kernel edit and cancellation", flush=True)


if __name__ == "__main__": main()
