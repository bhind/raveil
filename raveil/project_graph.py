"""Editable project Graphs using the existing bounded dynamic RTL executor."""
from __future__ import annotations

import json
import struct
from typing import Any

from .graph_device_dag import compile_descriptor
from .graph_device_dynamic import _profile_for, run_snapshot


def sample_descriptor() -> dict[str, Any]:
    return {
        "schema": "raveil.graph-device-dag/v2", "graph_id": "neighborhood",
        "affine": {"rows": 8, "columns": 8, "input_stride": 10, "output_stride": 8},
        "nodes": [
            {"id": "center", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": 0}},
            {"id": "north", "op": "LOAD_U32", "address": {"row_delta": -1, "column_delta": 0}},
            {"id": "combine", "op": "ADD_U32", "inputs": ["center", "north"]},
            {"id": "store", "op": "STORE_U32", "input": "combine"},
        ],
    }


def compile_graph(descriptor: dict[str, Any]) -> dict[str, Any]:
    try:
        program = compile_descriptor(descriptor)
        _profile_for(program)  # Reject shapes the actual request transport cannot admit.
    except (TypeError, KeyError, IndexError) as error:
        raise ValueError("malformed Graph descriptor") from error
    return program


def describe(descriptor: dict[str, Any], seed: int) -> str:
    program = compile_graph(descriptor)
    edges = sum(len(node.get("inputs", [node["input"]] if "input" in node else []))
                for node in descriptor["nodes"])
    lines = [f"graph={program['graph_id']} program_sha256={program['program_sha256']}",
             f"nodes={len(descriptor['nodes'])} edges={edges} instructions={program['instruction_count']}/16",
             f"output={program['affine']['rows']}x{program['affine']['columns']} uint32"]
    for node in descriptor["nodes"]:
        sources = node.get("inputs", [node["input"]] if "input" in node else [])
        suffix = f" address={json.dumps(node['address'], sort_keys=True)}" if "address" in node else ""
        lines.append(f"  {node['id']}: {node['op']} <- {', '.join(sources) or '(input grid)'}{suffix}")
    lines.extend((f"inputs: deterministic uint32 grid generated from seed={seed}",
                  "outputs: output.bin (256 little-endian uint32 words), output.txt (active rows)",
                  "backend: rtl-sim (offline Docker + Verilator; not Sonatine/QEMU)",
                  "Edit ADD_U32 to MAX_U32, or a load coordinate within [-1,1], then rerun."))
    return "\n".join(lines)


def output_text(output: bytes, program: dict[str, Any]) -> bytes:
    affine = program["affine"]
    if len(output) != 256 * 4:
        raise ValueError("RTL output size differs from the fixed 256-word transport window")
    words = struct.unpack("<256I", output)
    columns = affine["columns"]
    return ("\n".join(" ".join(str(word) for word in words[start:start + columns])
                      for start in range(0, affine["rows"] * affine["output_stride"], affine["output_stride"])) + "\n").encode("ascii")


def describe_changes(before: dict[str, Any], after: dict[str, Any],
                     first_output: bytes, second_output: bytes) -> list[str]:
    lines = []
    left, right = ({node["id"]: node for node in graph["nodes"]} for graph in (before, after))
    for node_id in sorted(left.keys() | right.keys()):
        if left.get(node_id) != right.get(node_id):
            lines.append(f"node {node_id}: {json.dumps(left.get(node_id), sort_keys=True)} -> {json.dumps(right.get(node_id), sort_keys=True)}")
    if before["affine"] != after["affine"]:
        lines.append(f"shape/stride: {before['affine']} -> {after['affine']}")
        return lines
    affine = before["affine"]
    left_words, right_words = (struct.unpack("<256I", payload) for payload in (first_output, second_output))
    changed = [(row, column, row * affine["output_stride"] + column)
               for row in range(affine["rows"]) for column in range(affine["columns"])
               if left_words[row * affine["output_stride"] + column] != right_words[row * affine["output_stride"] + column]]
    lines.append(f"output: {len(changed)}/{affine['rows'] * affine['columns']} active cells changed")
    if changed:
        row, column, index = changed[0]
        lines.append(f"first changed cell ({row}, {column}): {left_words[index]} -> {right_words[index]}")
    return lines
