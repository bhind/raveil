"""Bounded affine configuration, oracle, and RTL-simulation receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Sequence

from .graph_device_mvp import (
    device_abi_id,
    load_device_abi,
    prepare as prepare_graph_device,
    validate_artifact as validate_graph_device_artifact,
)
from .riscv_stencil_signature import input_words


INSTALL_ABI_PATH = "contracts/graph_device_install_abi_v1.json"
ARTIFACT_SCHEMA = "raveil.graph-device-affine-artifact/v1"
RECEIPT_SCHEMA = "raveil.graph-device-affine-receipt/v1"
EVIDENCE_CLASS = "rtl-simulation-functional"
CONFIG_MAGIC = 0x52414631
CONFIG_VERSION = 1
CONFIG_WORDS = 16
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

SOURCE_PATHS = (
    "contracts/graph_device_abi_v1.json",
    INSTALL_ABI_PATH,
    "raveil/graph_device_affine.py",
    "raveil/graph_device_mvp.py",
    "raveil/riscv_stencil_signature.py",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp",
    "hardware/chisel/graph_device_affine_runtime.h",
    "hardware/chisel/graph_device_affine_runtime.cpp",
    "hardware/chisel/graph_device_verilator.cpp",
    "hardware/chisel/run-graph-device-affine.sh",
    "hardware/chisel/run-graph-device-affine-in-container.sh",
    "hardware/chisel/Dockerfile",
)

PROFILE_FIELDS = (
    "rows",
    "columns",
    "input_stride",
    "output_stride",
    "active_outputs",
    "transactions_per_output",
)
PROFILE_BASES = {
    "baseline": {
        "rows": 16,
        "columns": 16,
        "input_stride": 18,
        "output_stride": 16,
        "active_outputs": 256,
        "transactions_per_output": 6,
    },
    "compact": {
        "rows": 8,
        "columns": 8,
        "input_stride": 10,
        "output_stride": 8,
        "active_outputs": 64,
        "transactions_per_output": 6,
    },
}


class GraphDeviceAffineError(ValueError):
    """An affine artifact, install transaction, or receipt failed closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    try:
        return _sha256(path.read_bytes())
    except OSError as error:
        raise GraphDeviceAffineError(f"cannot hash {path}: {error}") from error


def _word_bytes(words: Sequence[int]) -> bytes:
    return struct.pack(f"<{len(words)}I", *(word & 0xFFFFFFFF for word in words))


def _read_words(path: Path, count: int) -> list[int]:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise GraphDeviceAffineError(f"cannot read {path}: {error}") from error
    if len(payload) != count * 4:
        raise GraphDeviceAffineError(f"{path.name} must contain {count} u32 words")
    return list(struct.unpack(f"<{count}I", payload))


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceAffineError(f"{label} cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise GraphDeviceAffineError(f"{label} must be an object")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise GraphDeviceAffineError(f"{label} is not a lowercase SHA-256")
    return value


def load_install_abi(root: Path | None = None) -> dict[str, Any]:
    path = (root if root is not None else _root()) / INSTALL_ABI_PATH
    abi = _read_json(path, "install ABI")
    expected = {
        "byte_order": "little-endian",
        "control_bits": {"clear": 1, "commit": 2},
        "identity_word": 0x52564901,
        "max_payload_words": 16,
        "max_outstanding_requests": 1,
        "offset_unit": "u32-word",
        "payload_window": {
            "base_word": 256,
            "count_words": 16,
            "write_only": True,
        },
        "pointer_free": True,
        "registers": {
            "control": 4,
            "install_identity": 0,
            "install_version": 1,
            "installed_config_sha256_base": 16,
            "payload_count_words": 6,
            "status": 5,
        },
        "schema": "raveil.graph-device-install-abi/v1",
        "status_bits": {"fault": 4, "installed": 2, "loading": 1},
        "word_bits": 32,
    }
    if abi != expected:
        raise GraphDeviceAffineError("install ABI fields changed")
    return abi


def install_abi_id(root: Path | None = None) -> str:
    return _sha256(_canonical_bytes(load_install_abi(root)))


def source_id(root: Path | None = None) -> str:
    repo = root if root is not None else _root()
    digest = hashlib.sha256()
    for relative in SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise GraphDeviceAffineError(f"source path is missing: {relative}")
        digest.update(relative.encode("ascii") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def profiles() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for name, base in PROFILE_BASES.items():
        value = {"name": name, **base}
        value["configuration_sha256"] = _sha256(_canonical_bytes(value))
        result.append(value)
    return result


def profile(name: str) -> dict[str, Any]:
    for value in profiles():
        if value["name"] == name:
            return value
    raise GraphDeviceAffineError(f"unknown profile: {name}")


def validate_profile(value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise GraphDeviceAffineError("profile must be an object")
    integers = {field: value.get(field) for field in PROFILE_FIELDS}
    if any(type(item) is not int for item in integers.values()):
        raise GraphDeviceAffineError("profile fields must be integers")
    rows = integers["rows"]
    columns = integers["columns"]
    input_stride = integers["input_stride"]
    output_stride = integers["output_stride"]
    active_outputs = integers["active_outputs"]
    assert isinstance(rows, int)
    assert isinstance(columns, int)
    assert isinstance(input_stride, int)
    assert isinstance(output_stride, int)
    assert isinstance(active_outputs, int)
    if not 1 <= rows <= 16 or not 1 <= columns <= 16:
        raise GraphDeviceAffineError("profile shape is outside the bounded domain")
    if active_outputs != rows * columns or active_outputs > 256:
        raise GraphDeviceAffineError("active output count changed")
    if input_stride < columns + 2 or output_stride < columns:
        raise GraphDeviceAffineError("profile stride is too small")
    if integers["transactions_per_output"] != 6:
        raise GraphDeviceAffineError("transaction count changed")
    last_center = rows * input_stride + columns
    last_south = last_center + input_stride
    last_output = (rows - 1) * output_stride + columns - 1
    if last_south >= 324 or last_output >= 256:
        raise GraphDeviceAffineError("profile escapes a fixed physical window")


def config_words(value: dict[str, Any]) -> list[int]:
    validate_profile(value)
    canonical = next(
        (item for item in profiles() if item["name"] == value.get("name")), None
    )
    if canonical is None or any(
        value.get(field) != canonical[field] for field in PROFILE_FIELDS
    ) or value.get("configuration_sha256") != canonical["configuration_sha256"]:
        raise GraphDeviceAffineError("configuration identity mismatch")
    digest = bytes.fromhex(canonical["configuration_sha256"])
    return [
        CONFIG_MAGIC,
        CONFIG_VERSION,
        canonical["rows"],
        canonical["columns"],
        canonical["input_stride"],
        canonical["output_stride"],
        canonical["active_outputs"],
        canonical["transactions_per_output"],
        *[
            int.from_bytes(digest[index:index + 4], "little")
            for index in range(0, 32, 4)
        ],
    ]


def config_bytes(value: dict[str, Any]) -> bytes:
    return _word_bytes(config_words(value))


def validate_config_words(words: Sequence[int]) -> dict[str, Any]:
    if not isinstance(words, (list, tuple)) or len(words) != CONFIG_WORDS:
        raise GraphDeviceAffineError("configuration payload count changed")
    if any(type(word) is not int or not 0 <= word <= 0xFFFFFFFF for word in words):
        raise GraphDeviceAffineError("configuration payload word is invalid")
    for value in profiles():
        if list(words) == config_words(value):
            return value
    raise GraphDeviceAffineError("configuration payload is not admitted")


def affine_oracle(words: Sequence[int], value: dict[str, Any]) -> list[int]:
    validate_profile(value)
    if len(words) != 324:
        raise GraphDeviceAffineError("input must contain exactly 324 words")
    output = [0] * 256
    stride = value["input_stride"]
    for row in range(value["rows"]):
        for column in range(value["columns"]):
            center = (row + 1) * stride + column + 1
            output_index = row * value["output_stride"] + column
            output[output_index] = sum(
                words[center + offset]
                for offset in (0, -stride, stride, -1, 1)
            ) & 0xFFFFFFFF
    return output


def software_fallback(words: Sequence[int], value: dict[str, Any]) -> list[int]:
    validate_profile(value)
    if len(words) != 324:
        raise GraphDeviceAffineError("input must contain exactly 324 words")
    output = [0] * 256
    for row in range(value["rows"]):
        for column in range(value["columns"]):
            stride = value["input_stride"]
            center = (row + 1) * stride + column + 1
            accumulator = 0
            for address in (
                center,
                center - stride,
                center + stride,
                center - 1,
                center + 1,
            ):
                accumulator = (accumulator + int(words[address])) & 0xFFFFFFFF
            output[row * value["output_stride"] + column] = accumulator
    return output


def expected_transactions(value: dict[str, Any], seed: int = 1) -> list[dict[str, Any]]:
    validate_profile(value)
    oracle = affine_oracle(input_words(seed), value)
    result: list[dict[str, Any]] = []
    stride = value["input_stride"]
    for row in range(value["rows"]):
        for column in range(value["columns"]):
            center = (row + 1) * stride + column + 1
            for address in (
                center,
                center - stride,
                center + stride,
                center - 1,
                center + 1,
            ):
                result.append({"write": False, "address": address, "data": None})
            output_index = row * value["output_stride"] + column
            result.append({
                "write": True,
                "address": 324 + output_index,
                "data": oracle[output_index],
            })
    return result


def _generated_header() -> bytes:
    lines = [
        "#ifndef RAVEIL_GRAPH_DEVICE_AFFINE_GENERATED_H",
        "#define RAVEIL_GRAPH_DEVICE_AFFINE_GENERATED_H",
        "#include <array>",
        "#include <cstdint>",
        "namespace raveil::graph_device::affine_generated {",
        "struct Profile {",
        "  const char* name;",
        "  std::uint32_t activeOutputs;",
        "  std::array<std::uint32_t, 16> payload;",
        "  std::array<std::uint32_t, 8> digest;",
        "};",
        "inline constexpr std::array<Profile, 2> kProfiles = {{",
    ]
    for value in profiles():
        words = config_words(value)
        payload = ", ".join(f"0x{word:08x}U" for word in words)
        digest = ", ".join(f"0x{word:08x}U" for word in words[8:])
        lines.append(
            "  Profile{\"%s\", %dU, {%s}, {%s}},"
            % (value["name"], value["active_outputs"], payload, digest)
        )
    lines.extend([
        "}};",
        "}  // namespace raveil::graph_device::affine_generated",
        "#endif",
        "",
    ])
    return "\n".join(lines).encode("ascii")


def compile_artifact(root: Path | None = None) -> dict[str, Any]:
    repo = root if root is not None else _root()
    values = profiles()
    return {
        "schema": ARTIFACT_SCHEMA,
        "execution_abi_sha256": device_abi_id(load_device_abi(repo)),
        "install_abi_sha256": install_abi_id(repo),
        "source_sha256": source_id(repo),
        "profiles": [
            {**value, "payload_words": config_words(value)} for value in values
        ],
        "fixed_windows": {"input_words": 324, "output_words": 256},
        "successful_runs": [
            {"profile": "baseline", "seed": 1},
            {"profile": "compact", "seed": 2},
            {"profile": "compact", "seed": 4, "restart": True},
        ],
        "cancel": {"profile": "compact", "seed": 3},
        "invalid_install_cases": ["partial", "order", "duplicate", "digest", "busy"],
        "oracle_identity": _sha256(_canonical_bytes({
            "algorithm": "independent-u32-five-point-affine",
            "version": 1,
        })),
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
    }


def validate_artifact(artifact: dict[str, Any], root: Path | None = None) -> None:
    if artifact != compile_artifact(root):
        raise GraphDeviceAffineError("affine artifact content or identity changed")


def prepare(output: Path) -> dict[str, Any]:
    base_artifact = prepare_graph_device(output)
    validate_graph_device_artifact(base_artifact)
    words = input_words(4)
    (output / "inputs" / "seed-4.bin").write_bytes(_word_bytes(words))
    artifact = compile_artifact()
    validate_artifact(artifact)
    (output / "affine-artifact.json").write_bytes(_canonical_bytes(artifact) + b"\n")
    (output / "graph_device_affine_generated.h").write_bytes(_generated_header())
    for value in profiles():
        (output / f"config-{value['name']}.bin").write_bytes(config_bytes(value))
        for seed in (1, 2, 3, 4):
            oracle = affine_oracle(input_words(seed), value)
            (output / "oracles" / f"{value['name']}-seed-{seed}.bin").write_bytes(
                _word_bytes(oracle)
            )
    return artifact


def _parse_fields(line: str) -> tuple[str, dict[str, str]]:
    fields = line.split()
    if not fields or not fields[0].startswith("GraphDevice-AFFINE-"):
        raise GraphDeviceAffineError("runtime log schema changed")
    values: dict[str, str] = {}
    for field in fields[1:]:
        if "=" not in field:
            raise GraphDeviceAffineError("runtime log field is malformed")
        key, value = field.split("=", 1)
        if key in values:
            raise GraphDeviceAffineError("runtime log field is duplicated")
        values[key] = value
    return fields[0], values


def _parse_runtime_log(path: Path) -> list[tuple[str, dict[str, str]]]:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise GraphDeviceAffineError(f"runtime log cannot be read: {error}") from error
    return [_parse_fields(line) for line in lines if line]


def _parse_trace(path: Path) -> tuple[list[str], list[list[dict[str, Any]]]]:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise GraphDeviceAffineError(f"transaction trace cannot be read: {error}") from error
    events: list[str] = []
    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] | None = None
    for number, line in enumerate(lines, 1):
        fields = line.split()
        if not fields or fields[0] != "GraphDevice-TRACE-V1":
            raise GraphDeviceAffineError(f"trace line {number} has an invalid schema")
        values: dict[str, str] = {}
        for field in fields[1:]:
            if "=" not in field:
                raise GraphDeviceAffineError("trace field is malformed")
            key, value = field.split("=", 1)
            if key in values:
                raise GraphDeviceAffineError("trace field is duplicated")
            values[key] = value
        event = values.pop("event", None)
        if event == "transaction":
            if current is None or set(values) != {"write", "address", "data"}:
                raise GraphDeviceAffineError("transaction occurred outside an invocation")
            if values["write"] not in {"0", "1"}:
                raise GraphDeviceAffineError("trace write bit changed")
            try:
                address = int(values["address"])
                data = int(values["data"], 16)
            except ValueError as error:
                raise GraphDeviceAffineError("trace number is malformed") from error
            if not 0 <= address < 580 or not 0 <= data <= 0xFFFFFFFF:
                raise GraphDeviceAffineError("trace number is out of range")
            current.append({
                "write": values["write"] == "1",
                "address": address,
                "data": data,
            })
            continue
        if values or event not in {"reset", "start", "cancel"}:
            raise GraphDeviceAffineError("trace lifecycle event changed")
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
    prefix: bool,
) -> None:
    if prefix:
        if not 0 < len(actual) < len(expected):
            raise GraphDeviceAffineError("cancelled trace is not a strict nonempty prefix")
        expected = expected[:len(actual)]
    elif len(actual) != len(expected):
        raise GraphDeviceAffineError("completed transaction count changed")
    for index, (observed, planned) in enumerate(zip(actual, expected)):
        if observed["write"] != planned["write"] or observed["address"] != planned["address"]:
            raise GraphDeviceAffineError(f"transaction schedule mismatch at {index}")
        if planned["write"] and observed["data"] != planned["data"]:
            raise GraphDeviceAffineError(f"transaction store data mismatch at {index}")


def _validate_environment(path: Path) -> str:
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise GraphDeviceAffineError(f"environment cannot be read: {error}") from error
    if len(lines) < 7 or lines[:2] != [
        "schema=raveil.graph-device-affine-environment/v1",
        "platform=linux/amd64",
    ]:
        raise GraphDeviceAffineError("environment schema or platform changed")
    if not lines[2].startswith("dockerfile_sha256=") or SHA256_RE.fullmatch(
        lines[2].removeprefix("dockerfile_sha256=")
    ) is None:
        raise GraphDeviceAffineError("Dockerfile identity is invalid")
    if not lines[3].startswith("image_id=sha256:") or SHA256_RE.fullmatch(
        lines[3].removeprefix("image_id=sha256:")
    ) is None:
        raise GraphDeviceAffineError("container image identity is invalid")
    tool_lines = lines[4:]
    if not any(line.startswith("Scala CLI version: ") for line in tool_lines):
        raise GraphDeviceAffineError("Scala CLI version is missing")
    if not any(line.startswith("openjdk version ") for line in tool_lines):
        raise GraphDeviceAffineError("Java version is missing")
    if not any(line.startswith("Verilator ") for line in tool_lines):
        raise GraphDeviceAffineError("Verilator version is missing")
    return _file_sha256(path)


def finalize(evidence: Path) -> dict[str, Any]:
    receipt_path = evidence / "affine-receipt.json"
    if receipt_path.exists():
        raise GraphDeviceAffineError("affine receipt is append-once and already exists")
    artifact_path = evidence / "affine-artifact.json"
    artifact = _read_json(artifact_path, "affine artifact")
    validate_artifact(artifact)
    if _file_sha256(evidence / "graph_device_affine_generated.h") != _sha256(
        _generated_header()
    ):
        raise GraphDeviceAffineError("generated C++ configuration header drifted")
    for value in profiles():
        if (evidence / f"config-{value['name']}.bin").read_bytes() != config_bytes(value):
            raise GraphDeviceAffineError("configuration payload receipt drifted")

    records = _parse_runtime_log(evidence / "device.log")
    negatives = [values for tag, values in records if tag == "GraphDevice-AFFINE-NEGATIVE-V1"]
    runs = [values for tag, values in records if tag == "GraphDevice-AFFINE-RUN-V1"]
    cancels = [values for tag, values in records if tag == "GraphDevice-AFFINE-CANCEL-V1"]
    finals = [values for tag, values in records if tag == "GraphDevice-AFFINE-RUNTIME-V1"]
    if negatives != [{
        "partial": "FAULT",
        "order": "FAULT",
        "duplicate": "FAULT",
        "digest": "FAULT",
        "busy": "FAULT",
        "mutation": "0",
        "cases": "5",
    }]:
        raise GraphDeviceAffineError("invalid installation matrix is incomplete")
    if cancels != [{
        "profile": "compact",
        "seed": "3",
        "status": "CANCELLED",
        "output_valid": "0",
        "output_words": "0",
        "blocked_read": "1",
        "published": "0",
    }]:
        raise GraphDeviceAffineError("cancelled invocation exposed output")
    if finals != [{
        "status": "OK",
        "completed": "3",
        "cancelled": "1",
        "resets": "10",
        "profiles": "2",
        "invalid_cases": "5",
        "evidence": EVIDENCE_CLASS,
        "performance": "not-measured",
    }]:
        raise GraphDeviceAffineError("runtime final accounting changed")

    run_receipts: list[dict[str, Any]] = []
    expected_runs = artifact["successful_runs"]
    if len(runs) != len(expected_runs):
        raise GraphDeviceAffineError("completed run count changed")
    for record, expected_run in zip(runs, expected_runs):
        name = expected_run["profile"]
        seed = expected_run["seed"]
        value = profile(name)
        expected_record = {
            "profile": name,
            "seed": str(seed),
            "status": "COMPLETED",
            "staged_words": "324",
            "output_valid": "1",
            "output_words": "256",
            "active_outputs": str(value["active_outputs"]),
            "restart": "1" if expected_run.get("restart") else "0",
        }
        if any(record.get(key) != item for key, item in expected_record.items()):
            raise GraphDeviceAffineError(f"runtime record changed for {name} seed {seed}")
        polls_text = record.get("polls", "")
        if not polls_text.isdecimal() or not 1 <= int(polls_text) <= load_device_abi()["max_status_polls"]:
            raise GraphDeviceAffineError("runtime polling was not finite")
        output_path = evidence / f"private-output-{name}-seed-{seed}.bin"
        oracle_path = evidence / "oracles" / f"{name}-seed-{seed}.bin"
        output = _read_words(output_path, 256)
        oracle = _read_words(oracle_path, 256)
        fallback = software_fallback(input_words(seed), value)
        if output != oracle or oracle != fallback:
            raise GraphDeviceAffineError(f"oracle/fallback mismatch for {name} seed {seed}")
        if any(output[value["active_outputs"]:]):
            raise GraphDeviceAffineError("inactive private output tail is not zero")
        checksum = sum(output[:value["active_outputs"]]) & 0xFFFFFFFFFFFFFFFF
        if record.get("checksum") != f"{checksum:016x}":
            raise GraphDeviceAffineError("runtime checksum changed")
        run_receipts.append({
            "profile": name,
            "seed": seed,
            "configuration_sha256": value["configuration_sha256"],
            "input_sha256": _file_sha256(evidence / "inputs" / f"seed-{seed}.bin"),
            "oracle_sha256": _file_sha256(oracle_path),
            "private_output_sha256": _file_sha256(output_path),
            "active_outputs": value["active_outputs"],
            "output_words": 256,
            "inactive_tail_zero": True,
            "oracle_match": True,
            "fallback_match": True,
            "published": False,
        })

    if (evidence / "private-output-compact-seed-3.bin").exists():
        raise GraphDeviceAffineError("cancelled private output was materialized")
    events, segments = _parse_trace(evidence / "transaction-trace.txt")
    if len(segments) != 5 or events.count("start") != 5 or events.count("cancel") != 2:
        raise GraphDeviceAffineError("trace lifecycle or invocation count changed")
    expected_segments = (
        (profile("baseline"), 3, True),
        (profile("baseline"), 1, False),
        (profile("compact"), 2, False),
        (profile("compact"), 3, True),
        (profile("compact"), 4, False),
    )
    for actual, (value, seed, prefix) in zip(segments, expected_segments):
        _require_transactions(actual, expected_transactions(value, seed), prefix=prefix)

    simulator_sha256 = _require_sha256(
        (evidence / "simulator.sha256").read_text(encoding="ascii").strip(),
        "simulator identity",
    )
    environment_sha256 = _validate_environment(evidence / "environment.txt")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "complete",
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
        "source_sha256": artifact["source_sha256"],
        "artifact_sha256": _file_sha256(artifact_path),
        "execution_abi_sha256": artifact["execution_abi_sha256"],
        "install_abi_sha256": artifact["install_abi_sha256"],
        "oracle_identity": artifact["oracle_identity"],
        "simulator_sha256": simulator_sha256,
        "environment_sha256": environment_sha256,
        "runs": run_receipts,
        "cancel": {
            "profile": "compact",
            "seed": 3,
            "cancelled": True,
            "output_valid": False,
            "output_words": 0,
            "published": False,
        },
        "invalid_install_cases": artifact["invalid_install_cases"],
        "reset_restart": {"profile": "compact", "seed": 4, "passed": True},
        "completed_transaction_counts": [len(item) for item in segments[1:3]]
            + [len(segments[4])],
        "cancelled_transaction_counts": [len(segments[0]), len(segments[3])],
        "trace_equivalent": True,
        "store_data_oracle_match": True,
        "inactive_tail_zero": True,
        "execution_abi_unchanged": True,
        "rtl_regenerated_per_profile": False,
        "simulation_reset_zeroes_scratchpad": True,
    }
    receipt_path.write_bytes(_canonical_bytes(receipt) + b"\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded affine Graph-device tooling")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    finalize_parser = commands.add_parser("finalize")
    finalize_parser.add_argument("--evidence", type=Path, required=True)
    commands.add_parser("source-id")
    try:
        arguments = parser.parse_args(argv)
        if arguments.command == "prepare":
            prepare(arguments.output)
        elif arguments.command == "finalize":
            finalize(arguments.evidence)
        else:
            print(source_id())
    except GraphDeviceAffineError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
