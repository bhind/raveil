"""Canonical artifact and receipt tooling for the Graph device simulation MVP.

This module owns host-side compilation and independent Pavane validation.  It
does not implement a device transport and does not produce performance or FPGA
evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any

from .riscv_stencil_signature import input_words
from .static_region import (
    COMPILER_IDENTITY,
    ORACLE_IDENTITY,
    TARGET_SIGNATURE,
    canonical_descriptor_bytes,
    compile_static_stencil_descriptor,
    configuration_id,
    static_stencil_oracle,
    validate_static_stencil_descriptor,
)


ARTIFACT_SCHEMA = "raveil.graph-device-static-artifact/v1"
RECEIPT_SCHEMA = "raveil.graph-device-simulation-receipt/v1"
EVIDENCE_CLASS = "rtl-simulation-functional"
IMPLEMENTATION_IDENTITY = "raveil.static-stencil-executor/v1"
ABI_RELATIVE_PATH = "contracts/graph_device_abi_v1.json"
SOURCE_PATHS = (
    ABI_RELATIVE_PATH,
    "raveil/graph_device_mvp.py",
    "raveil/static_region.py",
    "raveil/riscv_stencil_signature.py",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp",
    "hardware/chisel/graph_device_verilator.cpp",
    "hardware/chisel/run-graph-device-sim-mvp.sh",
    "hardware/chisel/run-graph-device-sim-mvp-in-container.sh",
    "hardware/chisel/Dockerfile",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class GraphDeviceMvpError(ValueError):
    """The Graph device artifact, observation, or receipt failed closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _require_sha256(value: Any, label: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise GraphDeviceMvpError(f"{label} must be lowercase SHA-256")
    return value


def load_device_abi(root: Path | None = None) -> dict[str, Any]:
    repo = root if root is not None else _root()
    try:
        abi = json.loads((repo / ABI_RELATIVE_PATH).read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceMvpError(f"device ABI cannot be loaded: {error}") from error
    validate_device_abi(abi)
    return abi


def validate_device_abi(abi: dict[str, Any]) -> None:
    expected = {
        "schema": "raveil.graph-device-abi/v1",
        "byte_order": "little-endian",
        "word_bits": 32,
        "offset_unit": "u32-word",
        "pointer_free": True,
        "max_outstanding_requests": 1,
        "max_status_polls": 8192,
        "identity_word": 0x52560101,
        "digest_word_encoding": "sha256-hex-bytes-packed-little-endian-u32",
        "control_bits": {"start": 1, "cancel": 2, "reset": 4},
        "status_bits": {
            "busy": 1,
            "completed": 2,
            "cancelled": 4,
            "fault": 8,
            "output_valid": 16,
        },
        "registers": {
            "abi_identity": 0,
            "abi_version": 1,
            "control": 4,
            "status": 5,
            "input_count_words": 6,
            "output_count_words": 7,
            "descriptor_sha256_base": 16,
            "config_sha256_base": 24,
            "implementation_sha256_base": 32,
            "checksum_low": 40,
            "checksum_high": 41,
        },
        "input_window": {
            "base_word": 256,
            "count_words": 324,
            "write_only": True,
        },
        "output_window": {
            "base_word": 1024,
            "count_words": 256,
            "private": True,
            "read_requires_output_valid": True,
        },
    }
    if abi != expected:
        raise GraphDeviceMvpError("device ABI fields changed")


def device_abi_id(abi: dict[str, Any] | None = None) -> str:
    selected = abi if abi is not None else load_device_abi()
    validate_device_abi(selected)
    return _sha256(_canonical_bytes(selected))


def source_id(root: Path | None = None) -> str:
    repo = root if root is not None else _root()
    digest = hashlib.sha256()
    for relative in SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise GraphDeviceMvpError(f"source path is missing: {relative}")
        digest.update(relative.encode("ascii") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _digest_words(value: str) -> list[int]:
    raw = bytes.fromhex(_require_sha256(value, "digest"))
    return [int.from_bytes(raw[index:index + 4], "little") for index in range(0, 32, 4)]


def _generated_header(artifact: dict[str, Any], abi: dict[str, Any]) -> bytes:
    def words(name: str, digest: str) -> str:
        values = ", ".join(f"0x{word:08x}U" for word in _digest_words(digest))
        return f"constexpr std::array<std::uint32_t, 8> {name} = {{{values}}};"

    registers = abi["registers"]
    status = abi["status_bits"]
    control = abi["control_bits"]
    lines = [
        "#ifndef RAVEIL_GRAPH_DEVICE_ABI_GENERATED_H",
        "#define RAVEIL_GRAPH_DEVICE_ABI_GENERATED_H",
        "#include <array>",
        "#include <cstdint>",
        "namespace raveil::graph_device::abi {",
        f"constexpr std::uint32_t kIdentity = 0x{abi['identity_word']:08x}U;",
        "constexpr std::uint32_t kVersion = 1U;",
        f"constexpr std::uint32_t kControlStart = {control['start']}U;",
        f"constexpr std::uint32_t kControlCancel = {control['cancel']}U;",
        f"constexpr std::uint32_t kControlReset = {control['reset']}U;",
        f"constexpr std::uint32_t kStatusBusy = {status['busy']}U;",
        f"constexpr std::uint32_t kStatusCompleted = {status['completed']}U;",
        f"constexpr std::uint32_t kStatusCancelled = {status['cancelled']}U;",
        f"constexpr std::uint32_t kStatusFault = {status['fault']}U;",
        f"constexpr std::uint32_t kStatusOutputValid = {status['output_valid']}U;",
        f"constexpr std::uint32_t kRegIdentity = {registers['abi_identity']}U;",
        f"constexpr std::uint32_t kRegVersion = {registers['abi_version']}U;",
        f"constexpr std::uint32_t kRegControl = {registers['control']}U;",
        f"constexpr std::uint32_t kRegStatus = {registers['status']}U;",
        f"constexpr std::uint32_t kRegInputCount = {registers['input_count_words']}U;",
        f"constexpr std::uint32_t kRegOutputCount = {registers['output_count_words']}U;",
        f"constexpr std::uint32_t kRegDescriptorBase = {registers['descriptor_sha256_base']}U;",
        f"constexpr std::uint32_t kRegConfigBase = {registers['config_sha256_base']}U;",
        f"constexpr std::uint32_t kRegImplementationBase = {registers['implementation_sha256_base']}U;",
        f"constexpr std::uint32_t kRegChecksumLow = {registers['checksum_low']}U;",
        f"constexpr std::uint32_t kRegChecksumHigh = {registers['checksum_high']}U;",
        f"constexpr std::uint32_t kInputBase = {abi['input_window']['base_word']}U;",
        f"constexpr std::uint32_t kInputCount = {abi['input_window']['count_words']}U;",
        f"constexpr std::uint32_t kOutputBase = {abi['output_window']['base_word']}U;",
        f"constexpr std::uint32_t kOutputCount = {abi['output_window']['count_words']}U;",
        f"constexpr std::uint32_t kMaxStatusPolls = {abi['max_status_polls']}U;",
        f"constexpr const char* kDescriptorSha256 = \"{artifact['descriptor_sha256']}\";",
        f"constexpr const char* kConfigurationSha256 = \"{artifact['configuration_sha256']}\";",
        f"constexpr const char* kImplementationSha256 = \"{artifact['implementation_sha256']}\";",
        f"constexpr std::uint64_t kRtlConfigurationTag = 0x{artifact['configuration_sha256'][:16]}ULL;",
        words("kDescriptorWords", artifact["descriptor_sha256"]),
        words("kConfigWords", artifact["configuration_sha256"]),
        words("kImplementationWords", artifact["implementation_sha256"]),
        "}",
        "#endif",
        "",
    ]
    return "\n".join(lines).encode("ascii")


def compile_artifact() -> dict[str, Any]:
    descriptor = compile_static_stencil_descriptor()
    validate_static_stencil_descriptor(descriptor)
    descriptor_sha256 = _sha256(canonical_descriptor_bytes(descriptor))
    if descriptor_sha256 != configuration_id(descriptor):
        raise GraphDeviceMvpError("descriptor and configuration identities diverged")
    return {
        "schema": ARTIFACT_SCHEMA,
        "compiler_identity": COMPILER_IDENTITY,
        "oracle_identity": ORACLE_IDENTITY,
        "target_signature": TARGET_SIGNATURE,
        "implementation_identity": IMPLEMENTATION_IDENTITY,
        "implementation_sha256": _sha256(IMPLEMENTATION_IDENTITY.encode("ascii")),
        "abi_sha256": device_abi_id(),
        "descriptor_sha256": descriptor_sha256,
        "configuration_sha256": configuration_id(descriptor),
        "source_sha256": source_id(),
        "descriptor": descriptor,
        "input_seeds": [1, 2, 3],
        "successful_seeds": [1, 2],
        "cancel_seed": 3,
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
    }


def validate_artifact(artifact: dict[str, Any]) -> None:
    if set(artifact) != {
        "schema", "compiler_identity", "oracle_identity", "target_signature",
        "implementation_identity", "implementation_sha256", "abi_sha256",
        "descriptor_sha256", "configuration_sha256", "source_sha256",
        "descriptor", "input_seeds", "successful_seeds", "cancel_seed",
        "evidence_class", "performance",
    }:
        raise GraphDeviceMvpError("artifact fields changed")
    if artifact["schema"] != ARTIFACT_SCHEMA:
        raise GraphDeviceMvpError("artifact schema changed")
    descriptor = artifact["descriptor"]
    validate_static_stencil_descriptor(descriptor)
    expected = compile_artifact()
    if artifact != expected:
        raise GraphDeviceMvpError("artifact content or identity changed")


def _word_bytes(words: list[int]) -> bytes:
    return b"".join(struct.pack("<I", word & 0xFFFFFFFF) for word in words)


def _read_words(path: Path, count: int) -> list[int]:
    data = path.read_bytes()
    if len(data) != count * 4:
        raise GraphDeviceMvpError(f"{path.name} must contain exactly {count} u32 words")
    return list(struct.unpack(f"<{count}I", data))


def prepare(output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()):
        raise GraphDeviceMvpError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    (output / "inputs").mkdir()
    (output / "oracles").mkdir()
    artifact = compile_artifact()
    validate_artifact(artifact)
    abi = load_device_abi()
    (output / "artifact.json").write_bytes(_canonical_bytes(artifact) + b"\n")
    (output / "graph_device_abi_generated.h").write_bytes(
        _generated_header(artifact, abi)
    )
    for seed in artifact["input_seeds"]:
        words = input_words(seed)
        (output / "inputs" / f"seed-{seed}.bin").write_bytes(_word_bytes(words))
        oracle = static_stencil_oracle(words)
        (output / "oracles" / f"seed-{seed}.bin").write_bytes(_word_bytes(oracle))
    return artifact


def _parse_runtime_log(path: Path) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if not fields or not fields[0].startswith("GraphDevice-"):
            continue
        values: dict[str, str] = {}
        for field in fields[1:]:
            if "=" not in field:
                raise GraphDeviceMvpError("runtime log field is malformed")
            key, value = field.split("=", 1)
            if key in values:
                raise GraphDeviceMvpError("runtime log field is duplicated")
            values[key] = value
        records[fields[0]] = values
    return records


def finalize(evidence: Path) -> dict[str, Any]:
    artifact_path = evidence / "artifact.json"
    try:
        artifact = json.loads(artifact_path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceMvpError(f"artifact cannot be read: {error}") from error
    validate_artifact(artifact)
    records = _parse_runtime_log(evidence / "device.log")
    abi_record = records.get("GraphDevice-ABI-V1")
    final_record = records.get("GraphDevice-DEVICE-RUNTIME-V1")
    cancel_record = records.get("GraphDevice-CANCEL-V1")
    restart_record = records.get("GraphDevice-RESET-RESTART-V1")
    if abi_record is None or final_record is None or cancel_record is None or restart_record is None:
        raise GraphDeviceMvpError("runtime log is incomplete")
    if abi_record != {
        "status": "OK",
        "identity": "52560101",
        "descriptor": artifact["descriptor_sha256"],
        "configuration": artifact["configuration_sha256"],
        "implementation": artifact["implementation_sha256"],
    }:
        raise GraphDeviceMvpError("device ABI identity observation changed")
    if cancel_record != {
        "seed": "3", "status": "CANCELLED", "output_valid": "0",
        "output_words": "0", "blocked_read": "1", "published": "0",
    }:
        raise GraphDeviceMvpError("cancelled invocation exposed output")
    if restart_record.get("status") != "OK" or restart_record.get("seed") != "2":
        raise GraphDeviceMvpError("reset/restart evidence is missing")
    if (evidence / "private-output-seed-3.bin").exists():
        raise GraphDeviceMvpError("cancelled output was materialized")

    runs: list[dict[str, Any]] = []
    for seed in artifact["successful_seeds"]:
        output_path = evidence / f"private-output-seed-{seed}.bin"
        actual = _read_words(output_path, 256)
        oracle_path = evidence / "oracles" / f"seed-{seed}.bin"
        expected = _read_words(oracle_path, 256)
        if actual != expected:
            mismatch = next(index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1])
            raise GraphDeviceMvpError(f"Pavane mismatch at seed {seed} output {mismatch}")
        checksum = sum(expected) & 0xFFFFFFFFFFFFFFFF
        record = records.get(f"GraphDevice-RUN-{seed}-V1")
        if record is None or record.get("status") != "COMPLETED":
            raise GraphDeviceMvpError(f"completed record is missing for seed {seed}")
        if record.get("staged_words") != "324" or record.get("output_words") != "256":
            raise GraphDeviceMvpError("runtime word accounting changed")
        if record.get("output_valid") != "1" or record.get("checksum") != f"{checksum:016x}":
            raise GraphDeviceMvpError("runtime publication or checksum changed")
        polls = int(record.get("polls", "0"))
        if polls < 1 or polls > load_device_abi()["max_status_polls"]:
            raise GraphDeviceMvpError("runtime polling was not finite")
        runs.append({
            "seed": seed,
            "input_sha256": _file_sha256(evidence / "inputs" / f"seed-{seed}.bin"),
            "oracle_sha256": _file_sha256(oracle_path),
            "private_output_sha256": _file_sha256(output_path),
            "output_words": 256,
            "checksum": f"{checksum:016x}",
            "oracle_match": True,
            "published": False,
        })

    if final_record != {
        "status": "OK", "completed": "2", "cancelled": "1",
        "resets": "2", "evidence": EVIDENCE_CLASS,
        "performance": "not-measured",
    }:
        raise GraphDeviceMvpError("runtime final record changed")
    simulator_sha256 = _require_sha256(
        (evidence / "simulator.sha256").read_text(encoding="ascii").strip(),
        "simulator identity",
    )
    environment_sha256 = _file_sha256(evidence / "environment.txt")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "complete",
        "task": "Graph device",
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
        "source_sha256": artifact["source_sha256"],
        "artifact_sha256": _file_sha256(artifact_path),
        "abi_sha256": artifact["abi_sha256"],
        "descriptor_sha256": artifact["descriptor_sha256"],
        "configuration_sha256": artifact["configuration_sha256"],
        "implementation_sha256": artifact["implementation_sha256"],
        "oracle_identity": artifact["oracle_identity"],
        "simulator_sha256": simulator_sha256,
        "environment_sha256": environment_sha256,
        "runs": runs,
        "cancel": {
            "seed": 3,
            "input_sha256": _file_sha256(evidence / "inputs" / "seed-3.bin"),
            "oracle_sha256": _file_sha256(evidence / "oracles" / "seed-3.bin"),
            "cancelled": True,
            "output_valid": False,
            "output_words": 0,
            "published": False,
        },
        "reset_restart": {"reset_count": 2, "restart_seed": 2, "passed": True},
    }
    receipt_path = evidence / "receipt.json"
    if receipt_path.exists():
        raise GraphDeviceMvpError("receipt is append-once and already exists")
    receipt_path.write_bytes(_canonical_bytes(receipt) + b"\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Graph device simulation MVP tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--evidence", type=Path, required=True)
    subparsers.add_parser("source-id")
    try:
        args = parser.parse_args(argv)
        if args.command == "prepare":
            artifact = prepare(args.output)
            print(
                "GraphDevice-ARTIFACT-V1 status=OK "
                f"artifact_sha256={_file_sha256(args.output / 'artifact.json')} "
                f"abi_sha256={artifact['abi_sha256']} "
                f"configuration_sha256={artifact['configuration_sha256']}"
            )
        elif args.command == "finalize":
            receipt = finalize(args.evidence)
            print(
                "GraphDevice-MVP-V1 status=OK "
                f"receipt_sha256={_file_sha256(args.evidence / 'receipt.json')} "
                f"runs={len(receipt['runs'])} cancelled=1 reset_restart=1 "
                f"evidence={EVIDENCE_CLASS} performance=not-measured"
            )
        else:
            print(source_id())
    except (OSError, UnicodeError, json.JSONDecodeError, GraphDeviceMvpError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
