"""Versioned bounded grid execution over unchanged16x16 RTL children."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import struct
import subprocess
from uuid import uuid4

from . import project as p, project_graph as g, project_composition as c, grid_kernel as k

INPUT = "raveil.grid-input/v1"
PLAN = "raveil.project-tiling-plan/v1"
RESULT = "raveil.project-tiling-result/v1"
PLAN_V2 = "raveil.project-tiling-plan/v2"
RESULT_V2 = "raveil.project-tiling-result/v2"
ORIGINS = ((0, 0), (0, 16), (16, 0), (16, 16))
BUILD_KEYS = ("simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256")


def input_words(raw):
    if len(raw) > 64 * 1024:
        raise ValueError("grid input exceeds64 KiB")
    value = c._json(raw)
    if set(value) != {"schema", "rows", "columns", "words"} or value["schema"] != INPUT:
        raise ValueError("expected exact grid input schema")
    if any(type(value[k]) is not int or value[k] != 32 for k in ("rows", "columns")):
        raise ValueError("tiling requires exactly32x32")
    words = value["words"]
    if type(words) is not list or len(words) != 1024 or any(type(w) is not int or not 0 <= w <= 0xffffffff for w in words):
        raise ValueError("grid requires1024 uint32 words")
    return words


def descriptor():
    nodes = []
    previous = "center"
    for index, (label, dr, dc) in enumerate((("center", 0, 0), ("north", -1, 0),
                                           ("south", 1, 0), ("west", 0, -1), ("east", 0, 1))):
        nodes.append({"id": label, "op": "LOAD_U32", "address": {"row_delta": dr, "column_delta": dc}})
        if index:
            target = f"sum{index}"
            nodes.append({"id": target, "op": "ADD_U32", "inputs": [previous, label]})
            previous = target
    nodes.append({"id": "store", "op": "STORE_U32", "input": previous})
    return {"schema": "raveil.graph-device-dag/v2", "graph_id": "tiled-five-point",
            "affine": {"rows": 16, "columns": 16, "input_stride": 18, "output_stride": 16}, "nodes": nodes}


def tile_words(words, slot):
    row, col = ORIGINS[slot]
    return [words[r * 32 + k] if 0 <= r < 32 and 0 <= k < 32 else 0
            for r in range(row - 1, row + 17) for k in range(col - 1, col + 17)]


def global_reference(words):
    result = []
    for row in range(32):
        for col in range(32):
            index = row * 32 + col
            total = words[index]
            if row: total += words[index - 32]
            if row < 31: total += words[index + 32]
            if col: total += words[index - 1]
            if col < 31: total += words[index + 1]
            result.append(total & 0xffffffff)
    return result


def _filename(value):
    if type(value) is not str or not value.endswith(".json"):
        raise ValueError("tiling input must be a JSON filename inside inputs/")
    p.name(value[:-5])
    return value


def _planned(identity, filename, raw, kernel_raw=None, kernel_file=None, boundary="zero"):
    k.boundary(boundary)
    if kernel_raw is not None:
        grid = k.read_input(raw)
        desc = p.encoded(k.compile_kernel(kernel_raw))
        layout = k.layout(grid)
        tiles = [p.encoded({"schema": g.INPUT_SCHEMA, "words": k.halo(grid, tile, boundary)}) for tile in layout]
        plan = {"schema": PLAN_V2, "tiling_id": identity, "input_file": _filename(filename),
                "input_json_sha256": p.digest(raw),
                "input_sha256": p.digest(struct.pack(f"<{len(grid['words'])}I", *grid["words"])),
                "kernel_file": _filename(kernel_file), "kernel_json_sha256": p.digest(kernel_raw),
                "descriptor_sha256": p.digest(desc), "rows": grid["rows"], "columns": grid["columns"],
                "boundary": boundary,
                "tiles": [{**tile, "input_json_sha256": p.digest(tiles[slot]),
                           "input_sha256": p.digest(g.input_bytes(tiles[slot]))}
                          for slot, tile in enumerate(layout)]}
        return plan, grid["words"], desc, tiles
    if boundary != "zero" or kernel_file is not None:
        raise ValueError("legacy fixed grid requires zero boundary and no kernel")
    words = input_words(raw)
    tiles = [p.encoded({"schema": g.INPUT_SCHEMA, "words": tile_words(words, slot)}) for slot in range(4)]
    desc = p.encoded(descriptor())
    g.compile_graph(descriptor())
    plan = {"schema": PLAN, "tiling_id": identity, "input_file": _filename(filename),
            "input_json_sha256": p.digest(raw), "input_sha256": p.digest(struct.pack("<1024I", *words)),
            "descriptor_sha256": p.digest(desc),
            "tiles": [{"slot": slot, "row": row, "column": col,
                       "input_json_sha256": p.digest(tiles[slot]),
                       "input_sha256": p.digest(g.input_bytes(tiles[slot]))}
                      for slot, (row, col) in enumerate(ORIGINS)]}
    return plan, words, desc, tiles


def _plan(root):
    saved = c._json(c._read(root, "plan.json"))
    raw = c._read(root, "input.json")
    if saved.get("schema") == PLAN_V2:
        plan, words, desc, tiles = _planned(root.name, saved.get("input_file"), raw,
                                           c._read(root, "kernel.json"), saved.get("kernel_file"), saved.get("boundary"))
    elif saved.get("schema") == PLAN:
        plan, words, desc, tiles = _planned(root.name, saved.get("input_file"), raw)
    else:
        raise ValueError("unsupported tiling plan schema")
    if p.encoded(saved) != p.encoded(plan):
        raise ValueError("tiling plan differs from frozen full input")
    if c._read(root, "descriptor.json") != desc:
        raise ValueError("tiling descriptor differs")
    if any(c._read(root, f"input-{slot}.json") != tile for slot, tile in enumerate(tiles)):
        raise ValueError("saved halo differs from frozen full input")
    return plan, words, desc, tiles


def _child(root, slot, run_id, plan, desc, tiles):
    # Reuse only existing private validation; composition's public contract stays1/2.
    proxy = {"input_sha256": plan["tiles"][slot]["input_sha256"],
             "outputs": [{"name": f"tile-{i}"} for i in range(len(plan["tiles"]))]}
    entry, text = c._child(root, slot, run_id, proxy, tiles[slot], g.input_bytes(tiles[slot]), desc)
    values = [int(word) for word in text.split()]
    if len(values) != 256:
        raise ValueError("tile output size differs")
    return entry, values


def _assembled(root, children, plan, words, desc, tiles):
    if len(children) != len(tiles):
        raise ValueError("assembly requires all complete children")
    rows, columns = plan.get("rows", 32), plan.get("columns", 32)
    result = [None] * (rows * columns)
    for slot, entry in enumerate(children):
        expected, values = _child(root, slot, entry["run_id"], plan, desc, tiles)
        if p.encoded(entry) != p.encoded(expected):
            raise ValueError("tile child reference differs")
        if any(entry[k] != children[0][k] for k in BUILD_KEYS):
            raise ValueError("tiles used different RTL builds")
        tile = plan["tiles"][slot]
        row, col = tile["row"], tile["column"]
        for r in range(tile.get("rows", 16)):
            for column in range(tile.get("columns", 16)):
                index = (row + r) * columns + col + column
                if result[index] is not None:
                    raise ValueError("tile outputs overlap")
                result[index] = values[r * 16 + column]
    expected = global_reference(words) if plan["schema"] == PLAN else k.reference(
        {"rows": rows, "columns": columns, "words": words}, c._json(desc), plan["boundary"])
    if result != expected:
        raise ValueError("assembled output differs from full-grid reference")
    output = {"words": result, "sha256": p.digest(struct.pack(f"<{len(result)}I", *result))}
    if plan["schema"] == PLAN_V2:
        output.update(rows=rows, columns=columns)
    return output


def run(project, input_file, *, kernel_file=None, boundary="zero", cancelled=lambda: False):
    raw = c._read(project.root / "inputs", _filename(input_file))
    identity = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:12]
    kernel_raw = c._read(project.root / "inputs", _filename(kernel_file)) if kernel_file is not None else None
    plan, words, desc, tiles = _planned(identity, input_file, raw, kernel_raw, kernel_file, boundary)
    if "tilings" not in project.workspace.ls("/"):
        project.workspace.mkdir("tilings", mode=0o700)
    project.workspace.mkdir(f"tilings/{identity}", mode=0o700)
    root = project.root / "tilings" / identity
    for filename, data in [("plan.json", p.encoded(plan)), ("input.json", raw), ("descriptor.json", desc)]:
        p.write_new(root / filename, data)
    if kernel_raw is not None:
        p.write_new(root / "kernel.json", kernel_raw)
    for slot, data in enumerate(tiles):
        p.write_new(root / f"input-{slot}.json", data)
    (root / "children").mkdir(mode=0o700)
    record = {"schema": RESULT if plan["schema"] == PLAN else RESULT_V2, "tiling_id": identity, "plan_sha256": p.digest(p.encoded(plan)),
              "status": "incomplete", "error": "", "children": [], "output": None,
              "evidence_class": "rtl-simulation-functional"}

    def checkpoint():
        if cancelled():
            raise KeyboardInterrupt("tiling cancelled")

    try:
        for slot in range(len(tiles)):
            checkpoint()
            if _plan(root)[0] != plan:
                raise ValueError("tiling plan changed during execution")
            child_root = root / "children" / str(slot)
            child_root.mkdir(mode=0o700)
            for directory in ("inputs", "recipes", "runs"):
                (child_root / directory).mkdir(mode=0o700)
            p.write_new(child_root / "project.json", p.encoded(p.CONFIG))
            p.write_new(child_root / "recipes/child.json", p.encoded(c.CHILD_RECIPE))
            p.write_new(child_root / "inputs/input.json", tiles[slot])
            p.write_new(child_root / "inputs/descriptor.json", desc)
            child = p.Project(child_root).run("child", "rtl-sim", kernel=Path("unused"), qemu="unused", compiler="unused")
            if child["status"] != "succeeded":
                raise ValueError(f"tile {slot} failed: {child['error']}")
            entry, _ = _child(root, slot, child["run_id"], plan, desc, tiles)
            record["children"].append(entry)
        checkpoint()
        if _plan(root)[0] != plan:
            raise ValueError("tiling plan changed before assembly")
        output = _assembled(root, record["children"], plan, words, desc, tiles)
        checkpoint()
        record.update(status="succeeded", output=output)
    except KeyboardInterrupt:
        record["error"] = "cancelled; grid incomplete"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        record["error"] = str(error)
    record["artifacts"] = c._manifest(root)
    payload = p.encoded(record)
    p.write_new(root / ".record.pending", payload)
    p.write_new(root / "record.sha256", (p.digest(payload) + "\n").encode())
    try:
        if record["status"] == "succeeded":
            checkpoint()
        os.link(root / ".record.pending", root / "record.json")
        (root / ".record.pending").unlink()
    except KeyboardInterrupt:
        if not (root / "record.json").exists():
            record.update(status="incomplete", output=None, error="cancelled before publication; unsealed grid")
    return record


def load(project, identity):
    p.name(identity)
    project.workspace.stat(f"tilings/{identity}")
    root = project.root / "tilings" / identity
    plan, words, desc, tiles = _plan(root)
    payload = c._read(root, "record.json")
    if p.digest(payload) != c._read(root, "record.sha256").decode().strip():
        raise ValueError("tiling record checksum differs")
    record = c._json(payload)
    if set(record) != {"schema", "tiling_id", "plan_sha256", "status", "error", "children", "output", "evidence_class", "artifacts"} or record["schema"] != (RESULT if plan["schema"] == PLAN else RESULT_V2) or record["tiling_id"] != identity:
        raise ValueError("invalid tiling record")
    if record["plan_sha256"] != p.digest(c._read(root, "plan.json")) or record["artifacts"] != c._manifest(root):
        raise ValueError("saved tiling artifacts differ")
    if record["status"] not in ("succeeded", "incomplete") or type(record["children"]) is not list or len(record["children"]) > len(tiles):
        raise ValueError("invalid tiling status or children")
    if record["evidence_class"] != "rtl-simulation-functional" or type(record["error"]) is not str:
        raise ValueError("invalid tiling evidence or error")
    if any(type(e) is not dict or type(e.get("run_id")) is not str for e in record["children"]):
        raise ValueError("invalid tile reference")
    if record["status"] == "succeeded":
        if record["error"] or p.encoded(record["output"]) != p.encoded(_assembled(root, record["children"], plan, words, desc, tiles)):
            raise ValueError("published grid differs from checked assembly")
    else:
        if record["output"] is not None or not record["error"]:
            raise ValueError("incomplete grid must have no output and a cause")
        for slot, entry in enumerate(record["children"]):
            if p.encoded(entry) != p.encoded(_child(root, slot, entry["run_id"], plan, desc, tiles)[0]):
                raise ValueError("retained tile reference differs")
    if c._read(root, "record.json") != payload or c._manifest(root) != record["artifacts"]:
        raise ValueError("tiling changed during capture")
    return record


def inspect(project, identity):
    record = load(project, identity)
    lines = [f"tiling={identity} status={record['status']} evidence={record['evidence_class']}"]
    if record["status"] != "succeeded":
        return "\n".join(lines + ["No complete grid. " + record["error"]]) + "\n"
    output = record["output"]
    rows, columns = output.get("rows", 32), output.get("columns", 32)
    lines.append(f"output={rows}x{columns} uint32; validated saved grid")
    words = output["words"]
    return "\n".join(lines + [" ".join(map(str, words[r:r + columns])) for r in range(0, len(words), columns)]) + "\n"


def history(project):
    if "tilings" not in project.workspace.ls("/"):
        return "No tiling attempts."
    lines = []
    for identity in project.workspace.ls("tilings"):
        try:
            record = load(project, identity)
            lines.append(f"{identity} {record['status']} tiles={len(record['children'])}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            lines.append(f"{identity} incomplete/unverified: {error}")
    return "\n".join(lines)


def check(project, input_file, *, kernel_file=None, boundary="zero"):
    """Admission only: no directories, snapshots or executions are created."""
    raw = c._read(project.root / "inputs", _filename(input_file))
    kernel_raw = c._read(project.root / "inputs", _filename(kernel_file)) if kernel_file is not None else None
    plan, _, desc, _ = _planned("preview", input_file, raw, kernel_raw, kernel_file, boundary)
    program = g.compile_graph(c._json(desc))
    return {"rows": plan.get("rows", 32), "columns": plan.get("columns", 32),
            "boundary": boundary, "tiles": len(plan["tiles"]),
            "instructions": program["instruction_count"], "graph_id": program["graph_id"]}


def compare(project, first, second):
    """Compare saved, compatible complete grids without execution or writes."""
    before, after = load(project, first), load(project, second)
    if any(r["status"] != "succeeded" for r in (before, after)):
        raise ValueError("grid comparison requires two complete results")
    a, b = before["output"], after["output"]
    shape = lambda output: (output.get("rows", 32), output.get("columns", 32))
    if shape(a) != shape(b) or any(before["children"][0][key] != after["children"][0][key] for key in BUILD_KEYS):
        raise ValueError("grid comparison requires matching shape and RTL build")
    pa, wa, da, _ = _plan(project.root / "tilings" / first)
    pb, wb, db, _ = _plan(project.root / "tilings" / second)
    changes = [i for i, (x, y) in enumerate(zip(a["words"], b["words"])) if x != y]
    result = {"rows": shape(a)[0], "columns": shape(a)[1],
              "input_cells_changed": sum(x != y for x, y in zip(wa, wb)),
              "kernel_changed": da != db,
              "boundary_before": pa.get("boundary", "zero"), "boundary_after": pb.get("boundary", "zero"),
              "output_cells_changed": len(changes),
              "changed_cells": [list(divmod(i, shape(a)[1])) for i in changes]}
    if load(project, first) != before or load(project, second) != after:
        raise ValueError("grids changed during comparison")
    return result
