"""Operator-readable, fail-closed presentation of accepted S03 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence

from .graph_device_dag import (
    ARTIFACT_SCHEMA,
    EVIDENCE_CLASS,
    RECEIPT_SCHEMA,
    GraphDeviceDagError,
    compile_artifact,
)


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MARKER_PATH_RE = re.compile(
    r"^artifacts/graph_device_dag/run\.[A-Za-z0-9]{6}$"
)
NON_CLAIMS = [
    "arbitrary-graph",
    "performance",
    "resource-equality",
    "fpga",
    "asic",
    "silicon",
]
RECEIPT_KEYS = {
    "affine_abi_sha256",
    "artifact_sha256",
    "busy_mutation_transaction_count",
    "cancel_output_published",
    "environment_sha256",
    "evidence_class",
    "execution_abi_sha256",
    "generic_fallback",
    "invalid_programs_rejected",
    "non_claims",
    "performance",
    "program_abi_sha256",
    "rtl_regenerated_per_graph",
    "runs",
    "same_executor_rtl",
    "schema",
    "simulator_sha256",
    "slice",
    "source_sha256",
    "status",
    "store_data_oracle_match",
    "task",
    "transaction_addresses_match",
    "transaction_counts",
    "transaction_trace_sha256",
}


def _read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceDagError(f"{label} cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise GraphDeviceDagError(f"{label} must be an object")
    return value, raw


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise GraphDeviceDagError(f"{label} is not a lowercase SHA-256")
    return value


def _rtl_identity(root: Path) -> str:
    try:
        first = (root / "rtl-first.hashes").read_bytes()
        second = (root / "rtl-second.hashes").read_bytes()
    except OSError as error:
        raise GraphDeviceDagError(f"RTL hash export cannot be read: {error}") from error
    if not first or first != second:
        raise GraphDeviceDagError("two-pass RTL hash exports are empty or differ")
    try:
        lines = first.decode("ascii").splitlines()
    except UnicodeError as error:
        raise GraphDeviceDagError("RTL hash export is not ASCII") from error
    if not lines or any(SHA256_RE.fullmatch(line) is None for line in lines):
        raise GraphDeviceDagError("RTL hash export contains a malformed file identity")
    aggregate = hashlib.sha256(first).hexdigest()
    try:
        export_lines = (root / "rtl-export.sha256").read_text(
            encoding="ascii"
        ).splitlines()
    except (OSError, UnicodeError) as error:
        raise GraphDeviceDagError(f"aggregate RTL identity cannot be read: {error}") from error
    if export_lines != [aggregate]:
        raise GraphDeviceDagError("aggregate RTL identity does not bind the hash export")
    return aggregate


def parse_marker(marker: str) -> Path:
    fields = marker.split()
    if len(fields) != 4 or fields[0] != "GraphDevice-DAG-EVIDENCE-V1":
        raise GraphDeviceDagError("evidence marker is malformed")
    values: dict[str, str] = {}
    for field in fields[1:]:
        if field.count("=") != 1:
            raise GraphDeviceDagError("evidence marker field is malformed")
        key, value = field.split("=", 1)
        if key in values:
            raise GraphDeviceDagError("evidence marker field is duplicated")
        values[key] = value
    if set(values) != {"path", "private", "publication"} or \
            values["private"] != "1" or values["publication"] != "0":
        raise GraphDeviceDagError("evidence marker fields changed")
    if MARKER_PATH_RE.fullmatch(values["path"]) is None:
        raise GraphDeviceDagError("evidence marker path escaped the bounded run directory")
    return Path(values["path"])


def validate(evidence: Path | str) -> tuple[dict[str, Any], dict[str, Any], str]:
    root = Path(evidence)
    receipt, _ = _read_json(root / "dag-receipt.json", "DAG receipt")
    artifact, artifact_raw = _read_json(root / "dag-artifact.json", "DAG artifact")
    expected_artifact = compile_artifact()

    if artifact != expected_artifact:
        raise GraphDeviceDagError("DAG artifact differs from the current accepted compiler")
    if artifact.get("schema") != ARTIFACT_SCHEMA or \
            artifact.get("task") != "T-0123" or artifact.get("slice") != "S03":
        raise GraphDeviceDagError("T-0123/S03 artifact identity is required")
    if set(receipt) != RECEIPT_KEYS:
        raise GraphDeviceDagError("DAG receipt fields changed")
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("status") != "complete" or \
            receipt.get("task") != "T-0123" or receipt.get("slice") != "S03":
        raise GraphDeviceDagError("a complete T-0123/S03 receipt is required")
    if receipt.get("evidence_class") != EVIDENCE_CLASS or \
            receipt.get("performance") != "not-measured":
        raise GraphDeviceDagError("evidence class or performance status changed")

    for field in (
        "source_sha256",
        "execution_abi_sha256",
        "affine_abi_sha256",
        "program_abi_sha256",
    ):
        if receipt.get(field) != artifact.get(field):
            raise GraphDeviceDagError(f"receipt does not bind artifact field {field}")
    if receipt.get("artifact_sha256") != hashlib.sha256(artifact_raw).hexdigest():
        raise GraphDeviceDagError("receipt does not bind the exact DAG artifact")
    for field in (
        "artifact_sha256",
        "environment_sha256",
        "simulator_sha256",
        "source_sha256",
        "execution_abi_sha256",
        "affine_abi_sha256",
        "program_abi_sha256",
        "transaction_trace_sha256",
    ):
        _require_sha256(receipt.get(field), field)

    required_true = (
        "generic_fallback",
        "invalid_programs_rejected",
        "same_executor_rtl",
        "store_data_oracle_match",
        "transaction_addresses_match",
    )
    if any(receipt.get(field) is not True for field in required_true):
        raise GraphDeviceDagError("required S03 agreement flag is not true")
    if receipt.get("rtl_regenerated_per_graph") is not False or \
            receipt.get("cancel_output_published") is not False:
        raise GraphDeviceDagError("shared RTL or cancellation policy changed")
    if receipt.get("non_claims") != NON_CLAIMS:
        raise GraphDeviceDagError("S03 non-claims changed")

    graphs = artifact["graphs"]
    graph_ids = [graph["graph_id"] for graph in graphs]
    program_ids = [graph["program_sha256"] for graph in graphs]
    if len(graphs) != 3 or len(set(graph_ids)) != 3 or len(set(program_ids)) != 3:
        raise GraphDeviceDagError("exactly three distinct Graph and program identities are required")
    for program_id in program_ids:
        _require_sha256(program_id, "program_sha256")

    runs = receipt.get("runs")
    invocations = artifact["invocations"]
    if not isinstance(runs, list) or len(runs) != 5 or len(invocations) != 5:
        raise GraphDeviceDagError("four completed runs and one cancelled run are required")
    by_id = {graph["graph_id"]: graph for graph in graphs}
    completed_graphs: set[str] = set()
    counts: list[int] = []
    cancel_count = 0
    for run, invocation in zip(runs, invocations):
        if not isinstance(run, dict) or any(
            run.get(field) != invocation.get(field)
            for field in ("graph_id", "seed", "mode")
        ):
            raise GraphDeviceDagError("receipt run order or invocation identity changed")
        graph = by_id.get(run["graph_id"])
        if graph is None or run.get("program_sha256") != graph["program_sha256"]:
            raise GraphDeviceDagError("run does not bind its installed program")
        _require_sha256(run.get("oracle_sha256"), "oracle_sha256")
        count = run.get("transaction_count")
        if type(count) is not int or count < 0:
            raise GraphDeviceDagError("transaction count is malformed")
        counts.append(count)
        full_count = (
            graph["affine"]["rows"]
            * graph["affine"]["columns"]
            * graph["transactions_per_output"]
        )
        if run["mode"] == "cancel":
            cancel_count += 1
            if "private_output_sha256" in run or not 0 < count < full_count:
                raise GraphDeviceDagError("cancelled run published output or is not a strict prefix")
        else:
            output_id = _require_sha256(
                run.get("private_output_sha256"), "private_output_sha256"
            )
            if output_id != run["oracle_sha256"] or count != full_count:
                raise GraphDeviceDagError("completed RTL output or transaction count differs")
            completed_graphs.add(run["graph_id"])
    if cancel_count != 1 or completed_graphs != set(graph_ids):
        raise GraphDeviceDagError("the complete three-Graph matrix is missing")
    if receipt.get("transaction_counts") != counts:
        raise GraphDeviceDagError("transaction count summary differs from the run matrix")
    busy_count = receipt.get("busy_mutation_transaction_count")
    if type(busy_count) is not int or not 0 <= busy_count < counts[0]:
        raise GraphDeviceDagError("busy-mutation prefix accounting is malformed")

    return receipt, artifact, _rtl_identity(root)


def render(evidence: Path | str) -> str:
    receipt, artifact, rtl_identity = validate(evidence)
    lines = [
        "Raveil bounded Graph-device Playable",
        "graph | shape | stride in/out | instructions | program | validation | transactions",
    ]
    completed = {
        run["graph_id"]: run
        for run in receipt["runs"]
        if run["mode"] == "complete"
    }
    for graph in artifact["graphs"]:
        affine = graph["affine"]
        run = completed.get(graph["graph_id"])
        if run is None:
            run = next(
                item for item in receipt["runs"]
                if item["graph_id"] == graph["graph_id"]
                and item["mode"] == "factory-restart"
            )
        lines.append(
            f"{graph['graph_id']} | {affine['rows']}x{affine['columns']} | "
            f"{affine['input_stride']}/{affine['output_stride']} | "
            f"{graph['instruction_count']} | {graph['program_sha256'][:12]} | "
            f"RTL=PASS oracle=PASS fallback=PASS | {run['transaction_count']}"
        )
    lines.extend((
        f"shared RTL sha256={rtl_identity}",
        f"evidence={EVIDENCE_CLASS} performance=not-measured",
        "capability: fixed baseline=five-point-only; installed executor="
        "3 frozen programs on one RTL image",
        "non-claims: no arbitrary Graph, speedup, latency, resource, FPGA, "
        "ASIC, or silicon result",
    ))
    return "\n".join(lines)


def _main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    marker_parser = subparsers.add_parser("marker")
    marker_parser.add_argument("value")
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("evidence", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "marker":
            print(parse_marker(args.value))
        else:
            print(render(args.evidence))
    except GraphDeviceDagError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
