"""Editable project Graphs using the existing bounded dynamic RTL executor."""
from __future__ import annotations

import json
import struct
from typing import Any
import hashlib

from .graph_device_dag import compile_descriptor
from .graph_device_dynamic import _profile_for, run_snapshot

INPUT_SCHEMA = "raveil.graph-input/v1"
INPUT_WORDS = 324


def _input_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate Graph input field")
        result[key] = value
    return result


def input_bytes(payload: bytes) -> bytes:
    """Validate the fixed editable JSON input and return its wire image."""
    if len(payload) > 64 * 1024:
        raise ValueError("Graph input exceeds 64 KiB")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_input_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Graph input is not valid JSON") from error
    if type(value) is not dict or set(value) != {"schema", "words"} or value["schema"] != INPUT_SCHEMA:
        raise ValueError("Graph input must be an exact raveil.graph-input/v1 object")
    words = value["words"]
    if type(words) is not list or len(words) != INPUT_WORDS:
        raise ValueError("Graph input needs exactly 324 uint32 words")
    if any(type(word) is not int or not 0 <= word <= 0xffffffff for word in words):
        raise ValueError("Graph input words must be uint32 integers")
    return struct.pack("<324I", *words)


def describe_input(payload: bytes) -> str:
    packed = input_bytes(payload)
    return f"inputs: snapshot JSON (324 uint32 words, sha256={hashlib.sha256(packed).hexdigest()})"


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


def describe(descriptor: dict[str, Any], seed: int | None = None, input_payload: bytes | None = None) -> str:
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
    provenance = (f"inputs: deterministic uint32 grid generated from seed={seed}" if input_payload is None
                  else describe_input(input_payload))
    lines.extend((provenance,
                  "outputs: output.bin (256 little-endian uint32 words), output.txt (active rows)",
                  "backend: rtl-sim (offline Docker + Verilator; not Sonatine/QEMU)",
                  "Edit ADD_U32 to MAX_U32, a load coordinate within [-1,1], or the snapshot words, then rerun."))
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
