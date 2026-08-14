"""Fail-closed verifier for the T-0044 install-once repeated-input boundary.

This module is deliberately separate from :mod:`raveil.t0044_pilot`: EXP-0005
is immutable evidence for fresh-process runs.  The records here describe one
simulator process, one reset, one installed artifact, and ordered fresh inputs.
They are functional/accounting evidence until an experiment manifest promotes
them to a measurement campaign.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from .controlled_run import (
    ControlledRunError,
    _input_words,
    _parse_marker,
    _require_sha256,
    _word_digest,
    owned_resource_tuple_id,
    static_graph_source_id,
)
from .static_region import static_stencil_oracle


SCHEMA = "raveil.t0044-repeated-observation/v1"
SESSION_SCHEMA = "raveil.t0044-repeated-session/v1"
IMPLEMENTATIONS = {"static-graph", "rocket-in-order", "boom-ooo"}
PHASES = (
    "installation", "staging", "execution", "completion", "validation",
    "publication",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def repeated_contract() -> dict[str, Any]:
    return {
        "schema": SESSION_SCHEMA,
        "resource_sha256": owned_resource_tuple_id(),
        "workload": "five-point-stencil-u32-rfc-0005",
        "input_versions": list(range(1, 257)),
        "account_prefixes": [1, 4, 16, 64, 256],
        "processes_per_candidate_session": 1,
        "resets_per_candidate_session": 1,
        "artifact_reloads_per_candidate_session": 0,
        "installation_count": 1,
        "inter_invocation_boundary": (
            "previous-validation-response-to-next-staging-first-request"
        ),
        "publication_cycles": 0,
        "performance_claim": False,
    }


def repeated_contract_id() -> str:
    return hashlib.sha256(_canonical_bytes(repeated_contract())).hexdigest()


def _configuration_id(
    implementation: str,
    implementation_configuration: str,
    source_sha256: str,
    toolchain_sha256: str,
) -> str:
    return hashlib.sha256(_canonical_bytes({
        "implementation": implementation,
        "implementation_configuration": implementation_configuration,
        "repeated_contract_sha256": repeated_contract_id(),
        "resource_sha256": owned_resource_tuple_id(),
        "source_sha256": source_sha256,
        "toolchain_sha256": toolchain_sha256,
    })).hexdigest()


def _markers(lines: list[str], prefix: str) -> list[dict[str, str]]:
    return [_parse_marker(line) for line in lines if line.startswith(prefix)]


def _positive_account(account: int) -> None:
    if type(account) is not int or not 1 <= account <= 256:
        raise ControlledRunError("account must be in [1,256]")


def _observed_output_hashes(
    lines: list[str], account: int
) -> dict[int, str]:
    records = _markers(lines, "RAVEIL-CONTROLLED-OUTPUT-V1")
    if len(records) != 256 * account:
        raise ControlledRunError("repeated output marker cardinality changed")
    words: dict[int, list[int | None]] = {
        invocation: [None] * 256 for invocation in range(1, account + 1)
    }
    for fields in records:
        if set(fields) != {"invocation", "index", "value"}:
            raise ControlledRunError("repeated output marker schema changed")
        invocation = int(fields["invocation"])
        index = int(fields["index"])
        if invocation not in words or not 0 <= index < 256:
            raise ControlledRunError("repeated output coordinate is out of range")
        if words[invocation][index] is not None:
            raise ControlledRunError("repeated output coordinate is duplicated")
        try:
            value = int(fields["value"], 16)
        except ValueError as error:
            raise ControlledRunError("repeated output value is not hex") from error
        if not 0 <= value <= 0xFFFFFFFF:
            raise ControlledRunError("repeated output value is not uint32")
        words[invocation][index] = value

    result: dict[int, str] = {}
    for invocation, optional_words in words.items():
        if any(word is None for word in optional_words):
            raise ControlledRunError("repeated output is incomplete")
        actual = [int(word) for word in optional_words]
        oracle = static_stencil_oracle(_input_words(invocation))
        if actual != oracle:
            raise ControlledRunError(
                f"repeated output differs from oracle at invocation {invocation}"
            )
        result[invocation] = _word_digest(actual)
    return result


def _base_observation(
    implementation: str,
    implementation_configuration: str,
    invocation: int,
    source_sha256: str,
    artifact_sha256: str,
    toolchain_sha256: str,
    phase_cycles: dict[str, int],
    output_sha256: str,
    execution_traffic: int,
) -> dict[str, Any]:
    inputs = _input_words(invocation)
    oracle = static_stencil_oracle(inputs)
    return {
        "schema": SCHEMA,
        "contract_sha256": repeated_contract_id(),
        "resource_sha256": owned_resource_tuple_id(),
        "source_sha256": source_sha256,
        "artifact_sha256": artifact_sha256,
        "toolchain_sha256": toolchain_sha256,
        "configuration_sha256": _configuration_id(
            implementation, implementation_configuration,
            source_sha256, toolchain_sha256,
        ),
        "implementation_configuration": implementation_configuration,
        "implementation": implementation,
        "invocation": invocation,
        "seed": invocation,
        "input_sha256": _word_digest(inputs),
        "oracle_output_sha256": _word_digest(oracle),
        "observed_output_sha256": output_sha256,
        "semantic_valid": output_sha256 == _word_digest(oracle),
        "phase_cycles": phase_cycles,
        "total_cycles": sum(phase_cycles.values()),
        "window_cycles": phase_cycles["execution"],
        "execution_traffic_accepted": execution_traffic,
        "execution_traffic_completed": execution_traffic,
        "execution_traffic_pending": 0,
        "accounting_complete": True,
        "quiescence_before": True,
        "quiescence_after": True,
        "evidence_class": "rtl-simulation-functional",
        "performance_claim": False,
    }


def _session(
    observations: list[dict[str, Any]], account: int,
    *, diagnostic: bool = False,
) -> dict[str, Any]:
    if len(observations) != account:
        raise ControlledRunError("repeated observation cardinality changed")
    stable_fields = (
        "implementation", "implementation_configuration", "source_sha256",
        "artifact_sha256", "toolchain_sha256", "configuration_sha256",
        "contract_sha256", "resource_sha256",
    )
    for field in stable_fields:
        if len({observation[field] for observation in observations}) != 1:
            raise ControlledRunError(f"repeated session {field} drifted")
    if [record["invocation"] for record in observations] != list(
        range(1, account + 1)
    ):
        raise ControlledRunError("repeated invocation order changed")
    if len({record["input_sha256"] for record in observations}) != account:
        raise ControlledRunError("repeated inputs are not fresh")
    if any(not record["semantic_valid"] for record in observations):
        raise ControlledRunError("repeated semantic validation failed")
    identity = {field: observations[0][field] for field in stable_fields}
    session_id = hashlib.sha256(_canonical_bytes({
        **identity, "account": account, "diagnostic": diagnostic,
    })).hexdigest()
    return {
        "schema": SESSION_SCHEMA,
        "session_sha256": session_id,
        "account": account,
        "simulator_processes": 1,
        "resets": 1,
        "artifact_reloads": 0,
        "installation_count": 1,
        "diagnostic_only": diagnostic,
        "identity": identity,
        "observations": observations,
        "prefix_total_cycles": [
            sum(record["total_cycles"] for record in observations[:prefix])
            for prefix in range(1, account + 1)
        ],
        "accounting_complete": True,
        "performance_claim": False,
    }


def verify_graph_log(path: Path, account: int) -> dict[str, Any]:
    _positive_account(account)
    lines = path.read_text(encoding="utf-8").splitlines()
    identities = _markers(lines, "CONTROLLED-GRAPH-IDENTITY-V1")
    if len(identities) != 1 or set(identities[0]) != {
        "artifact_sha256", "toolchain_sha256",
    }:
        raise ControlledRunError("expected one repeated Graph identity")
    identity = identities[0]
    _require_sha256("artifact_sha256", identity["artifact_sha256"])
    _require_sha256("toolchain_sha256", identity["toolchain_sha256"])
    outputs = _observed_output_hashes(lines, account)
    completes = _markers(lines, "RAVEIL-REPEATED-GRAPH-COMPLETE-V1")
    activities = _markers(lines, "T0044-REPEATED-GRAPH-ACTIVITY-V1")
    accounts = _markers(lines, "RAVEIL-REPEATED-GRAPH-ACCOUNT-V1")
    if len(completes) != account or len(activities) != account or len(accounts) != 1:
        raise ControlledRunError("repeated Graph marker cardinality changed")
    source_sha256 = static_graph_source_id()
    configuration = "StaticStencilRegion:d4bf9395a510385f:repeated-v1"
    observations: list[dict[str, Any]] = []
    for invocation, fields in enumerate(completes, 1):
        expected = {
            "status", "invocation", "seed", *{
                f"{phase}_cycles" for phase in PHASES
            }, "total_cycles", "quiescence_before", "quiescence_after",
            "traffic_accepted", "traffic_completed", "traffic_pending",
            "graph_traffic", "unaccounted_window_traffic", "resource_sha256",
            "resource_contract_verified", "resource_equality_verified",
            "comparison_eligible", "performance",
        }
        if set(fields) != expected:
            raise ControlledRunError("repeated Graph complete schema changed")
        phase_cycles = {phase: int(fields[f"{phase}_cycles"]) for phase in PHASES}
        checks = {
            "status": "OK", "invocation": str(invocation),
            "seed": str(invocation), "installation_cycles": "0",
            "staging_cycles": "648", "execution_cycles": "3073",
            "completion_cycles": "1", "validation_cycles": "512",
            "publication_cycles": "0", "total_cycles": "4234",
            "quiescence_before": "1", "quiescence_after": "1",
            "traffic_accepted": "1536", "traffic_completed": "1536",
            "traffic_pending": "0", "graph_traffic": "1536",
            "unaccounted_window_traffic": "0",
            "resource_sha256": owned_resource_tuple_id(),
            "resource_contract_verified": "1",
            "resource_equality_verified": "0", "comparison_eligible": "0",
            "performance": "not-measured",
        }
        if fields != checks:
            raise ControlledRunError("repeated Graph complete values changed")
        observations.append(_base_observation(
            "static-graph", configuration, invocation, source_sha256,
            identity["artifact_sha256"], identity["toolchain_sha256"],
            phase_cycles, outputs[invocation], 1536,
        ))
    activity_invocations = [int(fields.get("invocation", "0")) for fields in activities]
    if activity_invocations != list(range(1, account + 1)):
        raise ControlledRunError("repeated Graph activity order changed")
    account_marker = accounts[0]
    if account_marker != {
        "status": "OK", "account": str(account), "installation_count": "1",
        "simulator_processes": "1", "resets": "1", "artifact_reloads": "0",
        "total_cycles": str(4234 * account), "performance": "not-measured",
    }:
        raise ControlledRunError("repeated Graph account marker changed")
    return _session(observations, account)


def verify_cpu_log(
    path: Path, implementation: str, account: int, source_sha256: str,
    artifact_sha256: str, toolchain_sha256: str,
    implementation_configuration: str, *, diagnostic: bool = False,
) -> dict[str, Any]:
    _positive_account(account)
    if implementation not in {"rocket-in-order", "boom-ooo"}:
        raise ControlledRunError("repeated CPU implementation changed")
    for name, value in (
        ("source_sha256", source_sha256), ("artifact_sha256", artifact_sha256),
        ("toolchain_sha256", toolchain_sha256),
    ):
        _require_sha256(name, value)
    expected_configuration = {
        "rocket-in-order": "chipyard.raveil.RaveilRepeatedMatchedRocketConfig",
        "boom-ooo": "chipyard.raveil.RaveilRepeatedMatchedSmallBoomConfig",
    }[implementation]
    if implementation_configuration != expected_configuration:
        raise ControlledRunError("repeated CPU configuration changed")
    lines = path.read_text(encoding="utf-8").splitlines()
    forbidden = (
        "RAVEIL-CONTROLLED-MIXED-TRAFFIC-V1",
        "RAVEIL-CONTROLLED-VALIDATION-TRAFFIC-V1",
    )
    if any(line.startswith(forbidden) for line in lines):
        raise ControlledRunError("repeated CPU admitted unexplained traffic")
    phases = _markers(lines, "RAVEIL-REPEATED-PHASE-V1")
    expected_phase_order = [(1, "0", "1")]
    for invocation in range(1, account + 1):
        expected_phase_order.extend((
            (invocation, "1", "2"), (invocation, "2", "3"),
            (invocation, "3", "4"), (invocation, "4", "1"),
        ))
    if len(phases) != len(expected_phase_order):
        raise ControlledRunError("repeated CPU phase cardinality changed")
    phase_fields = {
        "invocation", "from", "to", "cycle", "accepted", "completed",
        "busy_before", "publication_cycles",
    }
    for fields, expected in zip(phases, expected_phase_order, strict=True):
        invocation, source, destination = expected
        if set(fields) != phase_fields or (
            fields["invocation"], fields["from"], fields["to"],
            fields["publication_cycles"],
        ) != (str(invocation), source, destination, "0"):
            raise ControlledRunError("repeated CPU phase order changed")
    outputs = _observed_output_hashes(lines, account)
    windows = _markers(lines, "RAVEIL-REPEATED-WINDOW-V1")
    resources = _markers(lines, "RAVEIL-REPEATED-RESOURCE-V1")
    completes = _markers(lines, "RAVEIL-REPEATED-CPU-COMPLETE-V1")
    activities = _markers(lines, "T0044-REPEATED-CPU-ACTIVITY-V1")
    if not all(len(records) == account for records in (
        windows, resources, completes, activities,
    )):
        raise ControlledRunError("repeated CPU marker cardinality changed")
    observations: list[dict[str, Any]] = []
    for invocation in range(1, account + 1):
        window = windows[invocation - 1]
        complete = completes[invocation - 1]
        resource = resources[invocation - 1]
        activity = activities[invocation - 1]
        if any(record.get("invocation") != str(invocation) for record in (
            window, complete, resource, activity,
        )):
            raise ControlledRunError("repeated CPU invocation order changed")
        expected_window_fields = {
            "invocation", "start_cycle", "end_cycle", "cycles", "accepted",
            "completed", "reads", "writes", "expected_accepted",
            "expected_completed", "unexpected_accepted",
            "unexpected_completed", "origin_accepted", "origin_completed",
            "nonorigin_accepted", "nonorigin_completed", "pending",
            "quiescence_before", "quiescence_after",
        }
        if set(window) != expected_window_fields:
            raise ControlledRunError("repeated CPU window schema changed")
        for field, expected in {
            "accepted": "1056", "completed": "1056", "reads": "800",
            "writes": "256", "expected_accepted": "1056",
            "expected_completed": "1056", "unexpected_accepted": "0",
            "unexpected_completed": "0", "origin_accepted": "1056",
            "origin_completed": "1056", "nonorigin_accepted": "0",
            "nonorigin_completed": "0", "pending": "0",
            "quiescence_before": "1", "quiescence_after": "1",
        }.items():
            if window.get(field) != expected:
                raise ControlledRunError(f"repeated CPU window {field} changed")
        if int(window["end_cycle"]) - int(window["start_cycle"]) != int(window["cycles"]):
            raise ControlledRunError("repeated CPU window boundary mismatch")
        for field, expected in {
            "publication_cycles": "0", "accepted": "1636",
            "completed": "1636", "staging_writes": "324",
            "execution_reads": "800", "execution_writes": "256",
            "validation_reads": "256",
        }.items():
            if complete.get(field) != expected:
                raise ControlledRunError(f"repeated CPU complete {field} changed")
        expected_complete_fields = {
            "invocation", *{f"{phase}_cycles" for phase in PHASES},
            "total_cycles", "accepted", "completed", "staging_writes",
            "execution_reads", "execution_writes", "validation_reads",
        }
        if set(complete) != expected_complete_fields:
            raise ControlledRunError("repeated CPU complete schema changed")
        phase_cycles = {phase: int(complete[f"{phase}_cycles"]) for phase in PHASES}
        if phase_cycles["execution"] != int(window["cycles"]):
            raise ControlledRunError("repeated CPU execution boundary differs")
        if sum(phase_cycles.values()) != int(complete["total_cycles"]):
            raise ControlledRunError("repeated CPU lifecycle total changed")
        if invocation > 1 and phase_cycles["installation"] != 0:
            raise ControlledRunError("repeated CPU installation was not one-time")
        expected_resource = {
            "invocation": str(invocation),
            "resource_sha256": owned_resource_tuple_id(),
            "data_width_bits": "32", "operation_width_bytes": "4",
            "request_ports": "1", "response_ports": "1",
            "maximum_outstanding_requests": "1", "request_buffer_depth": "0",
            "response_buffer_depth": "1", "physical_banks": "1",
            "physical_words": "1024", "valid_words": "580",
            "arbitration": "none-at-owned-contract-ingress",
            "accepted_operations": "read,write-byte-mask",
            "response_rule": "one-module-local-cycle-after-acceptance",
            "response_hold": "stable-until-consumed",
        }
        if resource != expected_resource:
            raise ControlledRunError("repeated CPU resource identity changed")
        expected_activity_fields = {
            "invocation", "request_stall_cycles",
            "response_backpressure_cycles", "read_transactions",
            "write_transactions", "read_bytes", "write_bytes",
            "useful_loads", "useful_adds", "useful_stores", "outputs",
            "frontend_activity", "rename_rob_issue_lsu",
        }
        if set(activity) != expected_activity_fields:
            raise ControlledRunError("repeated CPU activity schema changed")
        for field, expected in {
            "read_transactions": "800", "write_transactions": "256",
            "read_bytes": "3200", "write_bytes": "1024",
            "useful_loads": "1280", "useful_adds": "1024",
            "useful_stores": "256", "outputs": "256",
            "frontend_activity": "unavailable",
            "rename_rob_issue_lsu": "unavailable",
        }.items():
            if activity[field] != expected:
                raise ControlledRunError(f"repeated CPU activity {field} changed")
        observations.append(_base_observation(
            implementation, implementation_configuration, invocation,
            source_sha256, artifact_sha256, toolchain_sha256, phase_cycles,
            outputs[invocation], 1056,
        ))
    return _session(
        observations, account,
        diagnostic=diagnostic,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify T-0044 repeated RTL logs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    graph = subparsers.add_parser("verify-graph")
    graph.add_argument("--log", type=Path, required=True)
    graph.add_argument("--account", type=int, required=True)
    cpu = subparsers.add_parser("verify-cpu")
    cpu.add_argument("--log", type=Path, required=True)
    cpu.add_argument("--implementation", required=True)
    cpu.add_argument("--account", type=int, required=True)
    cpu.add_argument("--source-sha256", required=True)
    cpu.add_argument("--artifact-sha256", required=True)
    cpu.add_argument("--toolchain-sha256", required=True)
    cpu.add_argument("--implementation-configuration", required=True)
    cpu.add_argument("--diagnostic-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify-graph":
            result = verify_graph_log(args.log, args.account)
        else:
            result = verify_cpu_log(
                args.log, args.implementation, args.account,
                args.source_sha256, args.artifact_sha256,
                args.toolchain_sha256, args.implementation_configuration,
                diagnostic=args.diagnostic_only,
            )
    except (ControlledRunError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
