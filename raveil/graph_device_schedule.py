"""Generated-schedule and transaction-trace evidence for T-0123/S01.

S01 keeps the existing bounded stencil and hand-written executor unchanged. It
emits a canonical schedule from the validated graph descriptor and proves that
the accepted RTL memory-transaction sequence is equivalent.  This is
simulation-functional evidence, not a generality or performance result.
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
    canonical_descriptor_bytes,
    compile_static_stencil_descriptor,
    configuration_id,
    static_stencil_oracle,
    validate_static_stencil_descriptor,
)
from .graph_device_mvp import (
    EVIDENCE_CLASS,
    GraphDeviceMvpError,
    device_abi_id,
    load_device_abi,
    prepare as prepare_graph_device,
    validate_artifact,
)


SCHEDULE_SCHEMA = "raveil.graph-device-generated-schedule/v1"
RECEIPT_SCHEMA = "raveil.graph-device-schedule-receipt/v1"
SOURCE_PATHS = (
    "raveil/graph_device_schedule.py",
    "raveil/graph_device_mvp.py",
    "raveil/static_region.py",
    "raveil/riscv_stencil_signature.py",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp",
    "hardware/chisel/graph_device_verilator.cpp",
    "hardware/chisel/run-graph-device-generated-schedule.sh",
    "hardware/chisel/run-graph-device-generated-schedule-in-container.sh",
    "hardware/chisel/Dockerfile",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)$")
U32_HEX_RE = re.compile(r"^[0-9a-f]{8}$")
GRAPH_DEVICE_RECEIPT_FIELDS = {
    "schema", "status", "task", "evidence_class", "performance",
    "source_sha256", "artifact_sha256", "abi_sha256", "descriptor_sha256",
    "configuration_sha256", "implementation_sha256", "oracle_identity",
    "simulator_sha256", "environment_sha256", "runs", "cancel",
    "reset_restart",
}
RUN_FIELDS = {
    "seed", "input_sha256", "oracle_sha256", "private_output_sha256",
    "output_words", "checksum", "oracle_match", "published",
}
CANCEL_FIELDS = {
    "seed", "input_sha256", "oracle_sha256", "cancelled", "output_valid",
    "output_words", "published",
}


class T0123ScheduleError(ValueError):
    """The generated schedule or observed transaction trace failed closed."""


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


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise T0123ScheduleError(f"{label} cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise T0123ScheduleError(f"{label} must be an object")
    return value


def _read_words(path: Path, count: int, label: str) -> list[int]:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise T0123ScheduleError(f"{label} cannot be read: {error}") from error
    if len(payload) != count * 4:
        raise T0123ScheduleError(f"{label} must contain exactly {count} u32 words")
    return list(struct.unpack(f"<{count}I", payload))


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise T0123ScheduleError(f"{label} is not a lowercase SHA-256")
    return value


def source_id(root: Path | None = None) -> str:
    repo = root if root is not None else _root()
    digest = hashlib.sha256()
    for relative in SOURCE_PATHS:
        path = repo / relative
        if not path.is_file():
            raise T0123ScheduleError(f"source path is missing: {relative}")
        digest.update(relative.encode("ascii") + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def compile_generated_schedule() -> dict[str, Any]:
    descriptor = compile_static_stencil_descriptor()
    validate_static_stencil_descriptor(descriptor)
    abi = load_device_abi()
    by_node = {node["id"]: node for node in descriptor["nodes"]}
    entries: list[dict[str, Any]] = []
    transactions: list[dict[str, Any]] = []
    for scheduled_cycle in descriptor["schedule"]:
        for slot, node_id in enumerate(scheduled_cycle["nodes"]):
            node = by_node[node_id]
            entry: dict[str, Any] = {
                "cycle": scheduled_cycle["cycle"],
                "slot": slot,
                "node": node_id,
                "op": node["op"],
            }
            if "effect" in node:
                entry["effect"] = node["effect"]
                transactions.append({
                    "sequence": len(transactions),
                    "node": node_id,
                    "op": node["op"],
                    "object": node["effect"]["object"],
                    "affine": node["effect"]["affine"],
                })
            entries.append(entry)
    return {
        "schema": SCHEDULE_SCHEMA,
        "task": "T-0123",
        "slice": "S01",
        "descriptor_sha256": _sha256(canonical_descriptor_bytes(descriptor)),
        "configuration_sha256": configuration_id(descriptor),
        "abi_sha256": device_abi_id(),
        "source_sha256": source_id(),
        "executor_target": descriptor["target_signature"],
        "schedule": entries,
        "transaction_template": transactions,
        "address_spaces": {
            "A": {"base_word": 0, "count_words": 324},
            "B": {"base_word": 324, "count_words": 256},
        },
        "internal_scratchpad_mapping": {
            "input_words": {"base_word": 0, "count_words": 324},
            "output_words": {"base_word": 324, "count_words": 256},
            "host_abi_input_offset": abi["input_window"]["base_word"],
            "host_abi_output_offset": abi["output_window"]["base_word"],
        },
        "outputs_per_invocation": 256,
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
    }


def validate_generated_schedule(schedule: dict[str, Any]) -> None:
    if schedule != compile_generated_schedule():
        raise T0123ScheduleError("generated schedule content or identity changed")


def _logical_address(expression: str, y: int, x: int) -> int:
    if expression == "18*y+x":
        return 18 * y + x
    if expression == "18*(y-1)+x":
        return 18 * (y - 1) + x
    if expression == "18*(y+1)+x":
        return 18 * (y + 1) + x
    if expression == "18*y+x-1":
        return 18 * y + x - 1
    if expression == "18*y+x+1":
        return 18 * y + x + 1
    if expression == "16*(y-1)+(x-1)":
        return 16 * (y - 1) + (x - 1)
    raise T0123ScheduleError(f"unsupported S01 affine expression: {expression}")


def expected_transactions(schedule: dict[str, Any], seed: int) -> list[dict[str, Any]]:
    validate_generated_schedule(schedule)
    oracle = static_stencil_oracle(input_words(seed))
    result: list[dict[str, Any]] = []
    for output_index in range(schedule["outputs_per_invocation"]):
        y = output_index // 16 + 1
        x = output_index % 16 + 1
        for operation in schedule["transaction_template"]:
            logical = _logical_address(operation["affine"], y, x)
            address_space = schedule["address_spaces"][operation["object"]]
            physical = address_space["base_word"] + logical
            if not address_space["base_word"] <= physical < (
                address_space["base_word"] + address_space["count_words"]
            ):
                raise T0123ScheduleError("generated transaction escaped its object")
            write = operation["op"] == "STORE_U32"
            result.append({
                "write": write,
                "address": physical,
                "data": oracle[output_index] if write else None,
            })
    return result


def prepare(output: Path) -> dict[str, Any]:
    prepare_graph_device(output)
    schedule = compile_generated_schedule()
    validate_generated_schedule(schedule)
    (output / "generated-schedule.json").write_bytes(
        _canonical_bytes(schedule) + b"\n"
    )
    return schedule


def _parse_trace(path: Path) -> tuple[list[str], list[list[dict[str, Any]]]]:
    events: list[str] = []
    segments: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] | None = None
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        fields = line.split()
        if not fields or fields[0] != "GraphDevice-TRACE-V1":
            raise T0123ScheduleError(f"trace line {line_number} has an invalid schema")
        values: dict[str, str] = {}
        for field in fields[1:]:
            if "=" not in field:
                raise T0123ScheduleError("trace field is malformed")
            key, value = field.split("=", 1)
            if key in values:
                raise T0123ScheduleError("trace field is duplicated")
            values[key] = value
        event = values.pop("event", None)
        if event == "transaction":
            if current is None or set(values) != {"write", "address", "data"}:
                raise T0123ScheduleError("transaction occurred outside an invocation")
            if (
                values["write"] not in {"0", "1"}
                or DECIMAL_RE.fullmatch(values["address"]) is None
                or U32_HEX_RE.fullmatch(values["data"]) is None
            ):
                raise T0123ScheduleError("transaction field is not canonical numeric text")
            write = int(values["write"])
            address = int(values["address"])
            data = int(values["data"], 16)
            if not 0 <= address < 580:
                raise T0123ScheduleError("transaction field is out of range")
            current.append({"write": bool(write), "address": address, "data": data})
            continue
        if values or event not in {"reset", "start", "cancel"}:
            raise T0123ScheduleError("trace event changed")
        events.append(event)
        if event == "start":
            if current is not None:
                segments.append(current)
            current = []
        elif event == "cancel":
            if current is None:
                raise T0123ScheduleError("cancel occurred outside an invocation")
            segments.append(current)
            current = None
        elif current is not None:
            segments.append(current)
            current = None
    if current is not None:
        segments.append(current)
    return events, segments


def _require_equivalent(
    actual: list[dict[str, Any]], expected: list[dict[str, Any]], *, prefix: bool
) -> None:
    if prefix:
        if not 0 < len(actual) < len(expected):
            raise T0123ScheduleError("cancel trace must be a non-empty strict prefix")
        selected = expected[:len(actual)]
    else:
        if len(actual) != len(expected):
            raise T0123ScheduleError("completed transaction count changed")
        selected = expected
    for index, (observed, planned) in enumerate(zip(actual, selected)):
        if observed["write"] != planned["write"] or observed["address"] != planned["address"]:
            raise T0123ScheduleError(f"transaction schedule mismatch at index {index}")
        if planned["write"] and observed["data"] != planned["data"]:
            raise T0123ScheduleError(f"transaction store data mismatch at index {index}")


def _validate_graph_device_receipt(
    evidence: Path, receipt: dict[str, Any], schedule: dict[str, Any]
) -> dict[str, Any]:
    if set(receipt) != GRAPH_DEVICE_RECEIPT_FIELDS:
        raise T0123ScheduleError("T-0122 prerequisite receipt fields changed")
    artifact_path = evidence / "artifact.json"
    artifact = _read_json(artifact_path, "graph device artifact")
    try:
        validate_artifact(artifact)
    except GraphDeviceMvpError as error:
        raise T0123ScheduleError(f"graph device artifact is invalid: {error}") from error
    if (
        schedule["descriptor_sha256"] != artifact["descriptor_sha256"]
        or schedule["configuration_sha256"] != artifact["configuration_sha256"]
        or schedule["abi_sha256"] != artifact["abi_sha256"]
    ):
        raise T0123ScheduleError("schedule and graph device artifact identities diverged")

    try:
        simulator_text = (evidence / "simulator.sha256").read_text(
            encoding="ascii"
        ).strip()
    except (OSError, UnicodeError) as error:
        raise T0123ScheduleError(f"simulator identity cannot be read: {error}") from error
    simulator_sha256 = _require_sha256(simulator_text, "simulator identity")
    environment_sha256 = _file_sha256(evidence / "environment.txt")
    expected_top = {
        "schema": "raveil.graph-device-simulation-receipt/v1",
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
    }
    for field, expected in expected_top.items():
        if receipt.get(field) != expected:
            raise T0123ScheduleError(
                f"T-0122 prerequisite receipt {field} identity changed"
            )

    runs = receipt.get("runs")
    if not isinstance(runs, list) or len(runs) != 2:
        raise T0123ScheduleError("T-0122 prerequisite receipt run matrix changed")
    for index, seed in enumerate((1, 2)):
        run = runs[index]
        if not isinstance(run, dict) or set(run) != RUN_FIELDS:
            raise T0123ScheduleError("T-0122 prerequisite run fields changed")
        input_path = evidence / "inputs" / f"seed-{seed}.bin"
        oracle_path = evidence / "oracles" / f"seed-{seed}.bin"
        output_path = evidence / f"private-output-seed-{seed}.bin"
        _read_words(input_path, 324, f"seed {seed} input")
        oracle_words = _read_words(oracle_path, 256, f"seed {seed} oracle")
        output_words = _read_words(output_path, 256, f"seed {seed} private output")
        if output_words != oracle_words:
            raise T0123ScheduleError(f"seed {seed} private output does not match Pavane")
        expected_run = {
            "seed": seed,
            "input_sha256": _file_sha256(input_path),
            "oracle_sha256": _file_sha256(oracle_path),
            "private_output_sha256": _file_sha256(output_path),
            "output_words": 256,
            "checksum": f"{sum(oracle_words) & 0xFFFFFFFFFFFFFFFF:016x}",
            "oracle_match": True,
            "published": False,
        }
        if run != expected_run:
            raise T0123ScheduleError(
                f"T-0122 prerequisite receipt seed {seed} identity changed"
            )

    cancel = receipt.get("cancel")
    if not isinstance(cancel, dict) or set(cancel) != CANCEL_FIELDS:
        raise T0123ScheduleError("T-0122 prerequisite cancel fields changed")
    cancel_input = evidence / "inputs" / "seed-3.bin"
    cancel_oracle = evidence / "oracles" / "seed-3.bin"
    _read_words(cancel_input, 324, "cancel input")
    _read_words(cancel_oracle, 256, "cancel oracle")
    if (evidence / "private-output-seed-3.bin").exists():
        raise T0123ScheduleError("cancelled output was materialized")
    expected_cancel = {
        "seed": 3,
        "input_sha256": _file_sha256(cancel_input),
        "oracle_sha256": _file_sha256(cancel_oracle),
        "cancelled": True,
        "output_valid": False,
        "output_words": 0,
        "published": False,
    }
    if cancel != expected_cancel:
        raise T0123ScheduleError("T-0122 prerequisite cancel identity changed")
    if receipt.get("reset_restart") != {
        "reset_count": 2,
        "restart_seed": 2,
        "passed": True,
    }:
        raise T0123ScheduleError("T-0122 prerequisite reset/restart identity changed")
    return artifact


def finalize(evidence: Path) -> dict[str, Any]:
    schedule = _read_json(evidence / "generated-schedule.json", "generated schedule")
    graph_device_receipt = _read_json(
        evidence / "receipt.json", "graph device receipt"
    )
    validate_generated_schedule(schedule)
    artifact = _validate_graph_device_receipt(evidence, graph_device_receipt, schedule)
    events, segments = _parse_trace(evidence / "transaction-trace.txt")
    if events != ["reset", "start", "start", "cancel", "reset", "start"]:
        raise T0123ScheduleError("runtime trace lifecycle changed")
    if len(segments) != 3:
        raise T0123ScheduleError("runtime trace must contain three invocations")
    expected_1 = expected_transactions(schedule, 1)
    expected_3 = expected_transactions(schedule, 3)
    expected_2 = expected_transactions(schedule, 2)
    _require_equivalent(segments[0], expected_1, prefix=False)
    _require_equivalent(segments[1], expected_3, prefix=True)
    _require_equivalent(segments[2], expected_2, prefix=False)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "complete",
        "task": "T-0123",
        "slice": "S01",
        "evidence_class": EVIDENCE_CLASS,
        "performance": "not-measured",
        "source_sha256": schedule["source_sha256"],
        "schedule_sha256": _file_sha256(evidence / "generated-schedule.json"),
        "artifact_sha256": graph_device_receipt["artifact_sha256"],
        "descriptor_sha256": schedule["descriptor_sha256"],
        "configuration_sha256": schedule["configuration_sha256"],
        "abi_sha256": graph_device_receipt["abi_sha256"],
        "graph_device_source_sha256": graph_device_receipt["source_sha256"],
        "implementation_sha256": graph_device_receipt["implementation_sha256"],
        "oracle_identity": artifact["oracle_identity"],
        "simulator_sha256": graph_device_receipt["simulator_sha256"],
        "environment_sha256": graph_device_receipt["environment_sha256"],
        "run_input_sha256": [run["input_sha256"] for run in graph_device_receipt["runs"]],
        "run_oracle_sha256": [run["oracle_sha256"] for run in graph_device_receipt["runs"]],
        "run_output_sha256": [
            run["private_output_sha256"] for run in graph_device_receipt["runs"]
        ],
        "cancel_input_sha256": graph_device_receipt["cancel"]["input_sha256"],
        "cancel_oracle_sha256": graph_device_receipt["cancel"]["oracle_sha256"],
        "graph_device_receipt_sha256": _file_sha256(evidence / "receipt.json"),
        "transaction_trace_sha256": _file_sha256(evidence / "transaction-trace.txt"),
        "completed_transaction_counts": [len(segments[0]), len(segments[2])],
        "cancelled_transaction_count": len(segments[1]),
        "transaction_trace_equivalent": True,
        "store_data_oracle_match": True,
        "schedule_consumed_by_executor": False,
    }
    receipt_path = evidence / "schedule-receipt.json"
    if receipt_path.exists():
        raise T0123ScheduleError("schedule receipt is append-once and already exists")
    receipt_path.write_bytes(_canonical_bytes(receipt) + b"\n")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Graph device generated schedule")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--output", type=Path, required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--evidence", type=Path, required=True)
    subparsers.add_parser("source-id")
    try:
        args = parser.parse_args(argv)
        if args.command == "prepare":
            schedule = prepare(args.output)
            print(
                "GraphDevice-SCHEDULE-V1 status=OK "
                f"schedule_sha256={_file_sha256(args.output / 'generated-schedule.json')} "
                f"entries={len(schedule['schedule'])} "
                f"transactions_per_output={len(schedule['transaction_template'])}"
            )
        elif args.command == "finalize":
            receipt = finalize(args.evidence)
            print(
                "GraphDevice-SCHEDULE-RECEIPT-V1 status=OK "
                f"receipt_sha256={_file_sha256(args.evidence / 'schedule-receipt.json')} "
                f"completed={receipt['completed_transaction_counts']} "
                f"cancelled_prefix={receipt['cancelled_transaction_count']} "
                f"evidence={EVIDENCE_CLASS} performance=not-measured"
            )
        else:
            print(source_id())
    except (OSError, UnicodeError, json.JSONDecodeError, T0123ScheduleError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
