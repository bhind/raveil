"""Bounded global-grid semantics, independent of tile scheduling and RTL layout."""
from __future__ import annotations

from . import project as p, project_composition as c, project_graph as g

INPUT = "raveil.grid-input/v2"
KERNEL = "raveil.grid-kernel/v1"
BOUNDARIES = ("zero", "clamp", "wrap")
MAX_DIMENSION = 64


def read_input(raw):
    if len(raw) > 128 * 1024:
        raise ValueError("grid input exceeds 128 KiB")
    value = c._json(raw)
    if set(value) != {"schema", "rows", "columns", "words"} or value["schema"] != INPUT:
        raise ValueError("expected exact grid-input/v2 schema")
    if any(type(value[k]) is not int or not 1 <= value[k] <= MAX_DIMENSION for k in ("rows", "columns")):
        raise ValueError("grid dimensions must be integers in 1..64")
    words = value["words"]
    if type(words) is not list or len(words) != value["rows"] * value["columns"] or any(
            type(w) is not int or not 0 <= w <= 0xffffffff for w in words):
        raise ValueError("grid requires rows*columns uint32 words")
    return value


def compile_kernel(raw):
    if len(raw) > 16 * 1024:
        raise ValueError("kernel exceeds 16 KiB")
    value = c._json(raw)
    if set(value) != {"schema", "graph_id", "nodes"} or value["schema"] != KERNEL:
        raise ValueError("expected exact grid-kernel/v1 schema")
    descriptor = {"schema": "raveil.graph-device-dag/v5", "graph_id": value["graph_id"],
                  "affine": {"rows": 16, "columns": 16, "input_stride": 18, "output_stride": 16},
                  "nodes": value["nodes"]}
    g.compile_graph(descriptor)
    return descriptor


def boundary(value):
    if type(value) is not str or value not in BOUNDARIES:
        raise ValueError("boundary must be zero, clamp or wrap")
    return value


def layout(grid):
    return [{"slot": slot, "row": r, "column": col,
             "rows": min(16, grid["rows"] - r), "columns": min(16, grid["columns"] - col)}
            for slot, (r, col) in enumerate((r, col) for r in range(0, grid["rows"], 16)
                                           for col in range(0, grid["columns"], 16))]


def sample(grid, row, col, mode):
    rows, columns = grid["rows"], grid["columns"]
    if mode == "zero" and not (0 <= row < rows and 0 <= col < columns):
        return 0
    if mode == "clamp":
        row, col = min(rows - 1, max(0, row)), min(columns - 1, max(0, col))
    elif mode == "wrap":
        row, col = row % rows, col % columns
    return grid["words"][row * columns + col]


def halo(grid, tile, mode):
    boundary(mode)
    return [sample(grid, r, col, mode)
            for r in range(tile["row"] - 1, tile["row"] + 17)
            for col in range(tile["column"] - 1, tile["column"] + 17)]


def reference(grid, descriptor, mode):
    """Untiled DAG evaluation; no compiled instructions or halo buffers used."""
    boundary(mode)
    g.compile_graph(descriptor)
    nodes = {n["id"]: n for n in descriptor["nodes"]}
    store = descriptor["nodes"][-1]
    output = []
    for row in range(grid["rows"]):
        for col in range(grid["columns"]):
            memo = {}
            def evaluate(identity):
                if identity in memo:
                    return memo[identity]
                node = nodes[identity]
                op = node["op"]
                if op == "LOAD_U32":
                    # Deliberately separate boundary resolution from halo/sample.
                    r = row + node["address"]["row_delta"]
                    k = col + node["address"]["column_delta"]
                    rows, columns = grid["rows"], grid["columns"]
                    if mode == "zero" and (r < 0 or r >= rows or k < 0 or k >= columns):
                        value = 0
                    else:
                        if mode == "clamp":
                            r, k = max(0, min(r, rows - 1)), max(0, min(k, columns - 1))
                        elif mode == "wrap":
                            r, k = r % rows, k % columns
                        value = grid["words"][r * columns + k]
                elif op in {"ADD_U32", "MUL_U32", "MAX_U32"}:
                    a, b = (evaluate(n) for n in node["inputs"])
                    value = a + b if op == "ADD_U32" else a * b if op == "MUL_U32" else max(a, b)
                else:
                    a = evaluate(node["input"])
                    value = a + node["immediate"] if op == "ADD_IMM_U32" else int(a >= node["immediate"])
                memo[identity] = value & 0xffffffff
                return memo[identity]
            output.append(evaluate(store["input"]))
    return output
