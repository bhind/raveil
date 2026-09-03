"""External bounded-DAG compiler, independent oracle, and evidence receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Sequence

from .graph_device_affine import (
    config_bytes,
    install_abi_id,
    prepare as prepare_affine,
    profile,
)
from .graph_device_mvp import device_abi_id, load_device_abi
from .riscv_stencil_signature import input_words


PROGRAM_ABI_PATH = "contracts/graph_device_program_install_abi_v1.json"
GRAPH_DIRECTORY = "contracts/graph_device_dags"
GRAPH_SCHEMA = "raveil.graph-device-dag/v1"
ARTIFACT_SCHEMA = "raveil.graph-device-dag-artifact/v1"
RECEIPT_SCHEMA = "raveil.graph-device-dag-receipt/v1"
LOWERING_TRACE_SCHEMA = "raveil.graph-device-lowering-trace/v1"
EVIDENCE_CLASS = "rtl-simulation-functional"
MAGIC = 0x52504731
VERSION = 1
MAX_U32 = 4
PROGRAM_WORDS = 32
PROGRAM_CAPACITY = 16
VALUE_REGISTERS = 8
LOAD_U32 = 1
ADD_U32 = 2
STORE_U32 = 3
OPS = {"LOAD_U32", "ADD_U32", "MAX_U32", "STORE_U32"}
SELECTORS = {"center": 0, "north": 1, "south": 2, "west": 3, "east": 4}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,30}$")
GRAPH_PATHS = (
    f"{GRAPH_DIRECTORY}/five-point.json",
    f"{GRAPH_DIRECTORY}/compact-horizontal-three-point.json",
    f"{GRAPH_DIRECTORY}/vertical-three-point.json",
)
SOURCE_PATHS = (
    "contracts/graph_device_abi_v1.json",
    "contracts/graph_device_install_abi_v1.json",
    PROGRAM_ABI_PATH,
    "contracts/graph_device_program_v2.json",
    *GRAPH_PATHS,
    "raveil/graph_device_dag.py",
    "raveil/graph_device_affine.py",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_dag_runtime.h",
    "hardware/chisel/graph_device_dag_runtime.cpp",
    "hardware/chisel/graph_device_verilator.cpp",
    "hardware/chisel/run-graph-device-dag.sh",
    "hardware/chisel/run-graph-device-dag-in-container.sh",
)


class GraphDeviceDagError(ValueError):
    """A DAG, program installation, execution, or receipt failed closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _word_bytes(words: Sequence[int]) -> bytes:
    return struct.pack(f"<{len(words)}I", *(word & 0xFFFFFFFF for word in words))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceDagError(f"{label} cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise GraphDeviceDagError(f"{label} must be an object")
    return value


def load_program_abi(root: Path | None = None) -> dict[str, Any]:
    repo = root if root is not None else _root()
    actual = _read_json(repo / PROGRAM_ABI_PATH, "program ABI")
    expected = {
        "byte_order": "little-endian",
        "control_bits": {"clear": 1, "commit": 2},
        "identity_word": 0x52565001,
        "max_outstanding_requests": 1,
        "max_payload_words": 32,
        "offset_unit": "u32-word",
        "payload_window": {"base_word": 256, "count_words": 32,
                           "write_only": True},
        "pointer_free": True,
        "registers": {
            "control": 4, "install_identity": 0, "install_version": 1,
            "installed_program_sha256_base": 16,
            "payload_count_words": 6, "status": 5,
        },
        "schema": "raveil.graph-device-program-install-abi/v1",
        "status_bits": {"fault": 4, "installed": 2, "loading": 1},
        "word_bits": 32,
    }
    if actual != expected:
        raise GraphDeviceDagError("program ABI fields changed")
    return actual


def program_abi_id(root: Path | None = None) -> str:
    return _sha256(_canonical(load_program_abi(root)))


def source_id(root: Path | None = None) -> str:
    repo = root if root is not None else _root()
    digest = hashlib.sha256()
    for relative in SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise GraphDeviceDagError(f"source path is missing: {relative}")
        digest.update(relative.encode("ascii") + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def validate_descriptor(value: dict[str, Any]) -> None:
    if set(value) != {"schema", "graph_id", "affine", "nodes"} or \
            value.get("schema") != GRAPH_SCHEMA:
        raise GraphDeviceDagError("exact descriptor keys and schema are required")
    if not isinstance(value.get("graph_id"), str) or IDENTIFIER_RE.fullmatch(value["graph_id"]) is None:
        raise GraphDeviceDagError("graph_id must be a bounded ASCII identifier")
    affine = value["affine"]
    fields = {"rows", "columns", "input_stride", "output_stride"}
    if not isinstance(affine, dict) or set(affine) != fields or \
            any(type(affine[field]) is not int for field in fields):
        raise GraphDeviceDagError("affine shape is invalid")
    rows, columns = affine["rows"], affine["columns"]
    if not 1 <= rows <= 16 or not 1 <= columns <= 16 or \
            affine["input_stride"] < columns + 2 or \
            affine["output_stride"] < columns or \
            (rows + 1) * affine["input_stride"] + columns >= 324 or \
            (rows - 1) * affine["output_stride"] + columns - 1 >= 256:
        raise GraphDeviceDagError("affine shape escapes the bounded windows")
    nodes = value["nodes"]
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= PROGRAM_CAPACITY:
        raise GraphDeviceDagError("node count is outside the bounded program")
    identifiers: set[str] = set()
    stores = 0
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or IDENTIFIER_RE.fullmatch(node["id"]) is None or \
                node["id"] in identifiers or node.get("op") not in OPS:
            raise GraphDeviceDagError("node identity or opcode is invalid")
        op = node["op"]
        if op == "LOAD_U32":
            if set(node) != {"id", "op", "address"} or \
                    node["address"] not in SELECTORS:
                raise GraphDeviceDagError("LOAD_U32 is invalid")
        elif op in {"ADD_U32", "MAX_U32"}:
            if set(node) != {"id", "op", "inputs"} or \
                    not isinstance(node["inputs"], list) or len(node["inputs"]) != 2 or \
                    any(source not in identifiers for source in node["inputs"]):
                raise GraphDeviceDagError(f"{op} has an undefined operand")
        else:
            if set(node) != {"id", "op", "input"} or \
                    node["input"] not in identifiers or stores:
                raise GraphDeviceDagError("STORE_U32 is invalid")
            stores += 1
        identifiers.add(node["id"])
    if stores != 1 or nodes[-1]["op"] != "STORE_U32":
        raise GraphDeviceDagError("exactly one final STORE_U32 is required")


def load_descriptor(path: Path | str) -> dict[str, Any]:
    value = _read_json(Path(path), "Graph descriptor")
    validate_descriptor(value)
    return value


def encode_load(destination: int, selector: str) -> int:
    return (LOAD_U32 << 28) | (destination << 25) | (SELECTORS[selector] << 22)


def encode_add(destination: int, source_a: int, source_b: int) -> int:
    return (ADD_U32 << 28) | (destination << 25) | (source_a << 22) | (source_b << 19)


def encode_max(destination: int, source_a: int, source_b: int) -> int:
    return (MAX_U32 << 28) | (destination << 25) | (source_a << 22) | (source_b << 19)


def encode_store(source: int) -> int:
    return (STORE_U32 << 28) | (source << 25)


def _lowering_trace(
    value: dict[str, Any],
    instructions: Sequence[int],
    allocations: dict[str, int],
) -> dict[str, Any]:
    """Describe compiler-owned allocation decisions without granting authority."""
    uses: dict[str, list[int]] = {node["id"]: [] for node in value["nodes"]}
    for index, node in enumerate(value["nodes"]):
        for source in node.get("inputs", [node.get("input")]):
            if source is not None:
                uses[source].append(index)
    entries: list[dict[str, Any]] = []
    for index, (node, word) in enumerate(zip(value["nodes"], instructions)):
        dependencies = list(node.get("inputs", [node.get("input")]))
        dependencies = [source for source in dependencies if source is not None]
        produces_value = node["op"] != "STORE_U32"
        last_use = max(uses[node["id"]]) if produces_value and uses[node["id"]] else None
        entries.append({
            "index": index,
            "node_id": node["id"],
            "op": node["op"],
            "dependencies": dependencies,
            "selector": node.get("address"),
            "fan_out": len(uses[node["id"]]),
            "consumers": [value["nodes"][consumer]["id"] for consumer in uses[node["id"]]],
            "encoded_word": int(word),
            "source_registers": [allocations[source] for source in dependencies],
            "destination_register": allocations[node["id"]] if produces_value else None,
            "definition_index": index if produces_value else None,
            "last_use_index": last_use,
            "live_range": (
                [index, last_use if last_use is not None else len(instructions) - 1]
                if produces_value else None
            ),
            "release_after_index": last_use,
        })
    digest = _sha256(_word_bytes([len(instructions), *instructions]))
    return {
        "schema": LOWERING_TRACE_SCHEMA,
        "graph_id": value["graph_id"],
        "descriptor_canonical_sha256": _sha256(_canonical(value)),
        "program_version": 2 if any(node["op"] == "MAX_U32" for node in value["nodes"]) else VERSION,
        "instruction_count": len(instructions),
        "program_sha256": digest,
        "instructions": entries,
    }


def validate_lowering_trace(
    value: dict[str, Any], trace: dict[str, Any], instructions: Sequence[int]
) -> None:
    """Fail closed unless a compiler trace exactly explains the encoded program."""
    validate_descriptor(value)
    expected_keys = {
        "schema", "graph_id", "descriptor_canonical_sha256", "program_version",
        "instruction_count", "program_sha256", "instructions",
    }
    if set(trace) != expected_keys or trace.get("schema") != LOWERING_TRACE_SCHEMA \
            or trace.get("graph_id") != value["graph_id"] \
            or trace.get("descriptor_canonical_sha256") != _sha256(_canonical(value)) \
            or trace.get("program_version") != (
                2 if any(node["op"] == "MAX_U32" for node in value["nodes"]) else VERSION
            ) \
            or trace.get("instruction_count") != len(instructions):
        raise GraphDeviceDagError("lowering trace identity is invalid")
    digest = _sha256(_word_bytes([len(instructions), *instructions]))
    if trace.get("program_sha256") != digest:
        raise GraphDeviceDagError("lowering trace program identity is invalid")
    entries = trace.get("instructions")
    if not isinstance(entries, list) or len(entries) != len(value["nodes"]):
        raise GraphDeviceDagError("lowering trace instruction count is invalid")
    uses: dict[str, list[int]] = {node["id"]: [] for node in value["nodes"]}
    for index, node in enumerate(value["nodes"]):
        for source in node.get("inputs", [node.get("input")]):
            if source is not None:
                uses[source].append(index)
    allocations: dict[str, int] = {}
    entry_keys = {
        "index", "node_id", "op", "dependencies", "selector", "fan_out", "consumers",
        "encoded_word", "source_registers", "destination_register",
        "definition_index", "last_use_index", "live_range", "release_after_index",
    }
    for index, (node, word, entry) in enumerate(zip(value["nodes"], instructions, entries)):
        if not isinstance(entry, dict) or set(entry) != entry_keys:
            raise GraphDeviceDagError("lowering trace instruction fields are invalid")
        dependencies = list(node.get("inputs", [node.get("input")]))
        dependencies = [source for source in dependencies if source is not None]
        if entry["index"] != index or entry["node_id"] != node["id"] \
                or entry["op"] != node["op"] or entry["dependencies"] != dependencies \
                or entry["selector"] != node.get("address") \
                or entry["fan_out"] != len(uses[node["id"]]) \
                or entry["consumers"] != [
                    value["nodes"][consumer]["id"] for consumer in uses[node["id"]]
                ] \
                or entry["encoded_word"] != word \
                or entry["source_registers"] != [allocations[source] for source in dependencies]:
            raise GraphDeviceDagError("lowering trace does not match the descriptor or words")
        produces_value = node["op"] != "STORE_U32"
        destination = (word >> 25) & 0x7 if produces_value else None
        last_use = max(uses[node["id"]]) if produces_value and uses[node["id"]] else None
        if entry["destination_register"] != destination \
                or entry["definition_index"] != (index if produces_value else None) \
                or entry["last_use_index"] != last_use \
                or entry["live_range"] != (
                    [index, last_use if last_use is not None else len(instructions) - 1]
                    if produces_value else None
                ) \
                or entry["release_after_index"] != last_use:
            raise GraphDeviceDagError("lowering trace lifetime or register is invalid")
        if node["op"] == "LOAD_U32":
            expected_word = encode_load(destination, node["address"])
        elif node["op"] == "ADD_U32":
            expected_word = encode_add(destination, *entry["source_registers"])
        elif node["op"] == "MAX_U32":
            expected_word = encode_max(destination, *entry["source_registers"])
        else:
            expected_word = encode_store(entry["source_registers"][0])
        if word != expected_word:
            raise GraphDeviceDagError("lowering trace encoded word is invalid")
        if produces_value:
            allocations[node["id"]] = destination


def compile_descriptor(value: dict[str, Any]) -> dict[str, Any]:
    validate_descriptor(value)
    remaining: dict[str, int] = {node["id"]: 0 for node in value["nodes"]}
    for node in value["nodes"]:
        for source in node.get("inputs", [node.get("input")]):
            if source is not None:
                remaining[source] += 1
    registers: dict[str, int] = {}
    allocations: dict[str, int] = {}
    free = list(range(VALUE_REGISTERS))
    instructions: list[int] = []
    for node in value["nodes"]:
        op = node["op"]
        sources = node.get("inputs", [node.get("input")])
        source_registers = [registers[source] for source in sources if source is not None]
        for source in sources:
            if source is not None:
                remaining[source] -= 1
                if remaining[source] == 0:
                    free.append(registers.pop(source))
        free.sort()
        if op == "STORE_U32":
            instructions.append(encode_store(source_registers[0]))
            continue
        if not free:
            raise GraphDeviceDagError("Graph requires more than eight live values")
        destination = free.pop(0)
        registers[node["id"]] = destination
        allocations[node["id"]] = destination
        if op == "LOAD_U32":
            instructions.append(encode_load(destination, node["address"]))
        elif op == "ADD_U32":
            instructions.append(encode_add(destination, *source_registers))
        else:
            instructions.append(encode_max(destination, *source_registers))
    digest = _sha256(_word_bytes([len(instructions), *instructions]))
    digest_words = list(struct.unpack("<8I", bytes.fromhex(digest)))
    version = 2 if any(node["op"] == "MAX_U32" for node in value["nodes"]) else VERSION
    payload = [MAGIC, version, len(instructions), VALUE_REGISTERS,
               *digest_words, *instructions,
               *([0] * (PROGRAM_CAPACITY - len(instructions))), 0, 0, 0, 0]
    assert len(payload) == PROGRAM_WORDS
    trace = _lowering_trace(value, instructions, allocations)
    validate_lowering_trace(value, trace, instructions)
    return {
        "graph_id": value["graph_id"],
        "affine": value["affine"],
        "instruction_count": len(instructions),
        "instructions": instructions,
        "program_sha256": digest,
        "lowering_trace": trace,
        "payload": payload,
        "transactions_per_output": sum(
            instruction >> 28 == LOAD_U32 for instruction in instructions) + 1,
    }


def descriptors(root: Path | None = None) -> list[dict[str, Any]]:
    repo = root if root is not None else _root()
    return [load_descriptor(repo / relative) for relative in GRAPH_PATHS]


def programs(root: Path | None = None) -> list[dict[str, Any]]:
    return [compile_descriptor(value) for value in descriptors(root)]


def _address(selector: str, center: int, stride: int) -> int:
    return center + {"center": 0, "north": -stride, "south": stride,
                     "west": -1, "east": 1}[selector]


def graph_oracle(value: dict[str, Any], words: Sequence[int]) -> list[int]:
    validate_descriptor(value)
    if len(words) != 324:
        raise GraphDeviceDagError("input must contain exactly 324 words")
    affine = value["affine"]
    output = [0] * 256
    for row in range(affine["rows"]):
        for column in range(affine["columns"]):
            center = (row + 1) * affine["input_stride"] + column + 1
            values: dict[str, int] = {}
            for node in value["nodes"]:
                if node["op"] == "LOAD_U32":
                    values[node["id"]] = int(words[_address(
                        node["address"], center, affine["input_stride"])])
                elif node["op"] == "ADD_U32":
                    values[node["id"]] = sum(values[item] for item in node["inputs"]) & 0xFFFFFFFF
                elif node["op"] == "MAX_U32":
                    values[node["id"]] = max(values[item] for item in node["inputs"])
                else:
                    output[row * affine["output_stride"] + column] = values[node["input"]]
    return output


def _validate_fallback_program(program: dict[str, Any]) -> list[int]:
    """Validate the standalone fallback boundary without trusting admission."""
    payload = program.get("payload")
    instructions = program.get("instructions")
    if not isinstance(payload, list) or len(payload) != PROGRAM_WORDS or \
            any(type(word) is not int or not 0 <= word <= 0xffffffff for word in payload) or \
            not isinstance(instructions, list):
        raise GraphDeviceDagError("fallback program payload is invalid")
    if payload[0] != MAGIC or payload[1] not in {1, 2} or payload[3] != VALUE_REGISTERS:
        raise GraphDeviceDagError("fallback program header is invalid")
    count = payload[2]
    if type(count) is not int or not 2 <= count <= PROGRAM_CAPACITY or \
            program.get("instruction_count") != count or instructions != payload[12:12 + count] or \
            any(payload[index] != 0 for index in range(12 + count, PROGRAM_WORDS)):
        raise GraphDeviceDagError("fallback program count or padding is invalid")
    digest = _sha256(_word_bytes([count, *instructions]))
    if program.get("program_sha256") != digest or payload[4:12] != list(struct.unpack("<8I", bytes.fromhex(digest))):
        raise GraphDeviceDagError("fallback program digest is invalid")
    defined: set[int] = set()
    stores = 0
    for index, word in enumerate(instructions):
        opcode, destination = word >> 28, (word >> 25) & 7
        if opcode == LOAD_U32:
            if index == count - 1 or ((word >> 22) & 7) > 4 or word & ((1 << 22) - 1):
                raise GraphDeviceDagError("fallback load instruction is invalid")
            defined.add(destination)
        elif opcode in {ADD_U32, MAX_U32}:
            left, right = (word >> 22) & 7, (word >> 19) & 7
            if index == count - 1 or word & ((1 << 19) - 1) or left not in defined or right not in defined or \
                    (opcode == MAX_U32 and payload[1] != 2):
                raise GraphDeviceDagError("fallback arithmetic instruction is invalid")
            defined.add(destination)
        elif opcode == STORE_U32:
            if index != count - 1 or word & ((1 << 25) - 1) or destination not in defined:
                raise GraphDeviceDagError("fallback store instruction is invalid")
            stores += 1
        else:
            raise GraphDeviceDagError("fallback program contains an unknown opcode")
    if stores != 1:
        raise GraphDeviceDagError("fallback program must have one final store")
    return instructions


def software_fallback(program: dict[str, Any], words: Sequence[int]) -> list[int]:
    instructions = _validate_fallback_program(program)
    if len(words) != 324:
        raise GraphDeviceDagError("fallback input must contain exactly 324 words")
    affine = program["affine"]
    output = [0] * 256
    for row in range(affine["rows"]):
        for column in range(affine["columns"]):
            center = (row + 1) * affine["input_stride"] + column + 1
            values = [0] * VALUE_REGISTERS
            for instruction in instructions:
                opcode, destination = instruction >> 28, (instruction >> 25) & 7
                if opcode == LOAD_U32:
                    selector = (instruction >> 22) & 7
                    offsets = {0: 0, 1: -affine["input_stride"],
                               2: affine["input_stride"], 3: -1, 4: 1}
                    values[destination] = int(words[center + offsets[selector]])
                elif opcode == ADD_U32:
                    values[destination] = (values[(instruction >> 22) & 7] +
                                           values[(instruction >> 19) & 7]) & 0xFFFFFFFF
                elif opcode == MAX_U32:
                    values[destination] = max(values[(instruction >> 22) & 7],
                                              values[(instruction >> 19) & 7])
                elif opcode == STORE_U32:
                    output[row * affine["output_stride"] + column] = values[destination]
                else:
                    raise GraphDeviceDagError("program contains an unknown opcode")
    return output


def expected_transactions(program: dict[str, Any], words: Sequence[int]) -> list[dict[str, Any]]:
    affine = program["affine"]
    oracle = software_fallback(program, words)
    result: list[dict[str, Any]] = []
    offsets = {0: 0, 1: -affine["input_stride"], 2: affine["input_stride"], 3: -1, 4: 1}
    for row in range(affine["rows"]):
        for column in range(affine["columns"]):
            center = (row + 1) * affine["input_stride"] + column + 1
            output_index = row * affine["output_stride"] + column
            for instruction in program["instructions"]:
                opcode = instruction >> 28
                if opcode == LOAD_U32:
                    result.append({"write": False,
                                   "address": center + offsets[(instruction >> 22) & 7],
                                   "data": 0})
                elif opcode == STORE_U32:
                    result.append({"write": True, "address": 324 + output_index,
                                   "data": oracle[output_index]})
                elif opcode in {ADD_U32, MAX_U32}:
                    pass
                else:
                    raise GraphDeviceDagError("program contains an unknown opcode")
    return result


def compile_artifact(root: Path | None = None) -> dict[str, Any]:
    repo = root if root is not None else _root()
    selected = programs(repo)
    return {
        "schema": ARTIFACT_SCHEMA, "task": "T-0123", "slice": "S03",
        "source_sha256": source_id(repo),
        "execution_abi_sha256": device_abi_id(load_device_abi(repo)),
        "affine_abi_sha256": install_abi_id(repo),
        "program_abi_sha256": program_abi_id(repo),
        "graphs": selected,
        "invocations": [
            {"graph_id": selected[0]["graph_id"], "seed": 1, "mode": "complete"},
            {"graph_id": selected[1]["graph_id"], "seed": 2, "mode": "complete"},
            {"graph_id": selected[1]["graph_id"], "seed": 3, "mode": "cancel"},
            {"graph_id": selected[2]["graph_id"], "seed": 4, "mode": "complete"},
            {"graph_id": selected[0]["graph_id"], "seed": 5, "mode": "factory-restart"},
        ],
        "same_executor_rtl": True, "rtl_regenerated_per_graph": False,
        "generic_fallback": True, "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
    }


def _generated_header(artifact: dict[str, Any]) -> bytes:
    lines = [
        "#ifndef RAVEIL_GRAPH_DEVICE_DAG_GENERATED_H",
        "#define RAVEIL_GRAPH_DEVICE_DAG_GENERATED_H",
        "#include <array>", "#include <cstdint>",
        "namespace raveil::graph_device::dag_generated {",
        "struct Graph { const char* id; const char* affine; std::array<std::uint32_t, 32> payload; };",
        f"inline constexpr std::array<Graph, {len(artifact['graphs'])}> kGraphs = {{{{",
    ]
    for item in artifact["graphs"]:
        affine = "compact" if item["affine"]["rows"] == 8 else "baseline"
        payload = ", ".join(f"0x{word:08x}U" for word in item["payload"])
        lines.append(f'  {{"{item["graph_id"]}", "{affine}", {{{{{payload}}}}}}},')
    lines.extend(["}};", "}  // namespace raveil::graph_device::dag_generated", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def prepare(output: Path) -> dict[str, Any]:
    prepare_affine(output)
    (output / "inputs" / "seed-5.bin").write_bytes(_word_bytes(input_words(5)))
    artifact = compile_artifact()
    (output / "dag-artifact.json").write_bytes(_canonical(artifact) + b"\n")
    (output / "graph_device_dag_generated.h").write_bytes(_generated_header(artifact))
    (output / "dag-programs").mkdir()
    (output / "dag-oracles").mkdir()
    descriptor_by_id = {value["graph_id"]: value for value in descriptors()}
    for item in artifact["graphs"]:
        (output / "dag-programs" / f"{item['graph_id']}.bin").write_bytes(_word_bytes(item["payload"]))
    for invocation in artifact["invocations"]:
        graph_id, seed = invocation["graph_id"], invocation["seed"]
        oracle = graph_oracle(descriptor_by_id[graph_id], input_words(seed))
        (output / "dag-oracles" / f"{graph_id}-seed-{seed}.bin").write_bytes(_word_bytes(oracle))
    return artifact


def _parse_trace(path: Path) -> tuple[list[str], list[list[dict[str, Any]]]]:
    events: list[str] = []
    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] | None = None
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise GraphDeviceDagError(f"transaction trace cannot be read: {error}") from error
    for number, line in enumerate(lines, 1):
        fields = line.split()
        if not fields or fields[0] != "GraphDevice-TRACE-V1":
            raise GraphDeviceDagError(f"trace line {number} has an invalid schema")
        values: dict[str, str] = {}
        for field in fields[1:]:
            if "=" not in field:
                raise GraphDeviceDagError("trace field is malformed")
            key, value = field.split("=", 1)
            if key in values:
                raise GraphDeviceDagError("trace field is duplicated")
            values[key] = value
        event = values.pop("event", "")
        if event == "transaction":
            if current is None or set(values) != {"write", "address", "data"} or \
                    values["write"] not in {"0", "1"}:
                raise GraphDeviceDagError("transaction escaped an invocation")
            try:
                address = int(values["address"])
                data = int(values["data"], 16)
            except ValueError as error:
                raise GraphDeviceDagError("trace number is malformed") from error
            if not 0 <= address < 580 or not 0 <= data <= 0xFFFFFFFF:
                raise GraphDeviceDagError("trace number is outside the owned memory")
            current.append({"write": values["write"] == "1",
                            "address": address, "data": data})
            continue
        if values or event not in {"reset", "start", "cancel"}:
            raise GraphDeviceDagError("trace lifecycle event changed")
        events.append(event)
        if event == "start":
            if current is not None:
                segments.append(current)
            current = []
        elif event in {"reset", "cancel"} and current is not None:
            segments.append(current)
            current = None
    if current is not None:
        segments.append(current)
    return events, segments


def _require_transactions(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    *,
    strict_prefix: bool,
    allow_empty_prefix: bool = False,
) -> None:
    if strict_prefix:
        minimum = 0 if allow_empty_prefix else 1
        if not minimum <= len(actual) < len(expected):
            qualifier = "possibly empty" if allow_empty_prefix else "nonempty"
            raise GraphDeviceDagError(f"trace is not a strict {qualifier} prefix")
        expected = expected[:len(actual)]
    elif len(actual) != len(expected):
        raise GraphDeviceDagError("completed transaction count changed")
    for index, (observed, planned) in enumerate(zip(actual, expected)):
        if observed["write"] != planned["write"] or \
                observed["address"] != planned["address"] or \
                (planned["write"] and observed["data"] != planned["data"]):
            raise GraphDeviceDagError(f"transaction mismatch at index {index}")


def finalize(evidence: Path) -> dict[str, Any]:
    receipt_path = evidence / "dag-receipt.json"
    if receipt_path.exists():
        raise GraphDeviceDagError("DAG receipt is append-once and already exists")
    artifact = _read_json(evidence / "dag-artifact.json", "DAG artifact")
    if artifact != compile_artifact():
        raise GraphDeviceDagError("DAG artifact content or identity changed")
    if (evidence / "graph_device_dag_generated.h").read_bytes() != _generated_header(artifact):
        raise GraphDeviceDagError("generated DAG header changed")
    rtl_first = (evidence / "rtl-first.hashes").read_bytes()
    rtl_second = (evidence / "rtl-second.hashes").read_bytes()
    if rtl_first != rtl_second or not rtl_first:
        raise GraphDeviceDagError("RTL exports are not byte-identical")
    log = (evidence / "device.log").read_text(encoding="ascii")
    if "GraphDevice-DAG-RUNTIME-V1 status=OK graphs=3 completed=4 cancelled=1 invalid_cases=8" not in log:
        raise GraphDeviceDagError("DAG runtime accounting is incomplete")
    by_id = {item["graph_id"]: item for item in artifact["graphs"]}
    events, segments = _parse_trace(evidence / "transaction-trace.txt")
    expected_events = (
        ["reset"] * 8
        + ["start", "cancel", "reset", "reset", "start", "reset", "start",
           "reset", "start", "cancel", "reset", "start", "reset", "start"]
    )
    if events != expected_events or len(segments) != 6:
        raise GraphDeviceDagError("DAG lifecycle trace changed")
    busy_invocation = artifact["invocations"][0]
    busy_expected = expected_transactions(
        by_id[busy_invocation["graph_id"]], input_words(busy_invocation["seed"])
    )
    _require_transactions(
        segments[0], busy_expected, strict_prefix=True, allow_empty_prefix=True
    )
    runs: list[dict[str, Any]] = []
    transaction_counts: list[int] = []
    for segment, invocation in zip(segments[1:], artifact["invocations"]):
        graph_id, seed, mode = invocation["graph_id"], invocation["seed"], invocation["mode"]
        expected = expected_transactions(by_id[graph_id], input_words(seed))
        _require_transactions(segment, expected, strict_prefix=mode == "cancel")
        transaction_counts.append(len(segment))
        oracle_path = evidence / "dag-oracles" / f"{graph_id}-seed-{seed}.bin"
        fallback_path = evidence / f"fallback-output-{graph_id}-seed-{seed}.bin"
        if fallback_path.read_bytes() != oracle_path.read_bytes():
            raise GraphDeviceDagError("generic fallback does not match the independent oracle")
        entry = {"graph_id": graph_id, "seed": seed, "mode": mode,
                 "program_sha256": by_id[graph_id]["program_sha256"],
                 "oracle_sha256": _sha256(oracle_path.read_bytes()),
                 "transaction_count": len(segment)}
        output_path = evidence / f"private-output-{graph_id}-seed-{seed}.bin"
        if mode == "cancel":
            if output_path.exists():
                raise GraphDeviceDagError("cancelled output was published")
        else:
            if output_path.read_bytes() != oracle_path.read_bytes():
                raise GraphDeviceDagError("RTL output does not match the independent oracle")
            entry["private_output_sha256"] = _sha256(output_path.read_bytes())
        runs.append(entry)
    simulator = (evidence / "simulator.sha256").read_text(encoding="ascii").strip()
    if SHA256_RE.fullmatch(simulator) is None:
        raise GraphDeviceDagError("simulator identity is invalid")
    receipt = {
        "schema": RECEIPT_SCHEMA, "status": "complete", "task": "T-0123",
        "slice": "S03", "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured", "source_sha256": artifact["source_sha256"],
        "artifact_sha256": _sha256((evidence / "dag-artifact.json").read_bytes()),
        "execution_abi_sha256": artifact["execution_abi_sha256"],
        "affine_abi_sha256": artifact["affine_abi_sha256"],
        "program_abi_sha256": artifact["program_abi_sha256"],
        "simulator_sha256": simulator,
        "environment_sha256": _sha256((evidence / "environment.txt").read_bytes()),
        "transaction_trace_sha256": _sha256(
            (evidence / "transaction-trace.txt").read_bytes()),
        "busy_mutation_transaction_count": len(segments[0]),
        "transaction_counts": transaction_counts,
        "transaction_addresses_match": True,
        "store_data_oracle_match": True,
        "same_executor_rtl": True, "rtl_regenerated_per_graph": False,
        "generic_fallback": True, "invalid_programs_rejected": True,
        "cancel_output_published": False, "runs": runs,
        "non_claims": ["arbitrary-graph", "performance", "resource-equality",
                       "fpga", "asic", "silicon"],
    }
    receipt_path.write_bytes(_canonical(receipt) + b"\n")
    return receipt


def _main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    finalize_parser = sub.add_parser("finalize")
    finalize_parser.add_argument("--evidence", type=Path, required=True)
    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("descriptor", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare(args.output)
        elif args.command == "finalize":
            finalize(args.evidence)
        else:
            print(json.dumps(compile_descriptor(load_descriptor(args.descriptor)), sort_keys=True))
    except (GraphDeviceDagError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
