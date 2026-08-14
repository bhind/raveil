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
import os
from pathlib import Path
import subprocess
import sys
import time
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
MANIFEST_SCHEMA = "raveil.t0044-repeated-manifest/v1"
REPORT_SCHEMA = "raveil.t0044-repeated-report/v1"
VARIANTS = (
    "static-graph", "rocket-in-order", "boom-ooo",
    "boom-serialize-dispatch",
)
IMPLEMENTATIONS = {"static-graph", "rocket-in-order", "boom-ooo"}
PHASES = (
    "installation", "staging", "execution", "completion", "validation",
    "publication",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != MANIFEST_SCHEMA or value.get("experiment_id") != "EXP-0006":
        raise ControlledRunError("EXP-0006 manifest identity changed")
    if value.get("status") != "frozen-before-data":
        raise ControlledRunError("EXP-0006 manifest is not frozen")
    if value["authority"]["boundary_implementation_commit"] != (
        "10b4f0fc2efe1e0b7f3d6a8722c5c766a23a6c2d"
    ):
        raise ControlledRunError("EXP-0006 implementation authority changed")
    if value["authority"]["collector_implementation_commit"] != (
        "7575602e6651cc1e755e8d2f7b255aa8872db856"
    ):
        raise ControlledRunError("EXP-0006 collector authority changed")
    if value["authority"]["runtime_fix_commit"] != (
        "80a35e61881393ba9790b19719eb1f6dcb4ee415"
    ):
        raise ControlledRunError("EXP-0006 runtime-fix authority changed")
    if value["authority"]["installation_accounting_commit"] != (
        "cf454e4cd847d43d223fe7166b20d75dae0c2ffe"
    ):
        raise ControlledRunError("EXP-0006 installation-accounting authority changed")
    if value["authority"]["log_synchronization_commit"] != (
        "988c25e615feaf711cb4d91f121d551bf88420ea"
    ):
        raise ControlledRunError("EXP-0006 log-synchronization authority changed")
    if value["workload"]["fresh_input_versions"] != list(range(1, 257)):
        raise ControlledRunError("EXP-0006 fresh-input order changed")
    if value["matrix"]["complete_for_commissioning"] != list(VARIANTS):
        raise ControlledRunError("EXP-0006 commissioning matrix changed")
    if value["sampling"]["commissioning_accounts"] != [1, 4] or value[
        "sampling"
    ]["campaign_prefix_accounts"] != [1, 4, 16, 64, 256]:
        raise ControlledRunError("EXP-0006 accounts changed")
    session = value["session_contract"]
    if any(session[key] != expected for key, expected in {
        "simulator_processes": 1, "resets": 1, "installation_count": 1,
        "artifact_reloads": 0,
    }.items()):
        raise ControlledRunError("EXP-0006 install-once session changed")
    required_stops = {
        "oracle-mismatch", "resource-equality-failure", "unexplained-traffic",
        "required-accounting-missing", "source-config-toolchain-drift",
        "artifact-or-session-drift", "incomplete-matrix",
        "execution-window-meaning-differs", "restart-reset-reload-observed",
    }
    if not required_stops.issubset(value["stop_conditions"]):
        raise ControlledRunError("EXP-0006 stop conditions are incomplete")
    return value


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
        raise ControlledRunError(
            "repeated output marker cardinality changed: "
            f"observed {len(records)}, expected {256 * account}"
        )
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
        expected_lifecycle_traffic = "2216" if invocation == 1 else "1636"
        for field, expected in {
            "publication_cycles": "0", "accepted": expected_lifecycle_traffic,
            "completed": expected_lifecycle_traffic,
            "installation_reads": "0",
            "installation_writes": "580" if invocation == 1 else "0",
            "staging_writes": "324",
            "execution_reads": "800", "execution_writes": "256",
            "validation_reads": "256",
        }.items():
            if complete.get(field) != expected:
                raise ControlledRunError(f"repeated CPU complete {field} changed")
        expected_complete_fields = {
            "invocation", *{f"{phase}_cycles" for phase in PHASES},
            "total_cycles", "accepted", "completed", "staging_writes",
            "installation_reads", "installation_writes", "execution_reads",
            "execution_writes", "validation_reads",
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


def _one_marker(lines: list[str], prefix: str) -> dict[str, str]:
    matches = _markers(lines, prefix)
    if len(matches) != 1:
        raise ControlledRunError(f"expected exactly one {prefix} marker")
    return matches[0]


def parse_variant_log(path: Path, variant: str, account: int) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise ControlledRunError("repeated variant changed")
    if variant == "static-graph":
        return verify_graph_log(path, account)
    lines = path.read_text(encoding="utf-8").splitlines()
    host = _one_marker(lines, "RAVEIL-REPEATED-CPU-HOST-V1")
    expected_label = {
        "rocket-in-order": "rocket",
        "boom-ooo": "boom",
        "boom-serialize-dispatch": "boom-serialize",
    }[variant]
    if host.get("status") != "OK" or host.get("cpu") != expected_label:
        raise ControlledRunError(f"{variant} host identity changed")
    for field, expected in {
        "account": str(account), "simulator_processes": "1", "resets": "1",
        "artifact_reloads": "0", "resource_sha256": owned_resource_tuple_id(),
        "workload": "frozen-rfc-0005", "oracle": "independent-host",
        "accounting": "pending-completed-outer-raw-verification",
        "evidence": "rtl-simulation-functional",
        "performance": "not-measured",
    }.items():
        if host.get(field) != expected:
            raise ControlledRunError(f"{variant} host {field} changed")
    implementation = "rocket-in-order" if variant == "rocket-in-order" else "boom-ooo"
    return verify_cpu_log(
        path, implementation, account, host["source_sha256"],
        host["artifact_sha256"], host["toolchain_sha256"], host["config"],
        diagnostic=variant == "boom-serialize-dispatch",
    )


def derive(run_dir: Path, manifest_path: Path, account: int) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    _positive_account(account)
    allowed = {4, 256}
    if account not in allowed:
        raise ControlledRunError("collection account must be commissioning 4 or campaign 256")
    raw_dir = run_dir / "raw"
    derived_dir = run_dir / "derived"
    derived_dir.mkdir(exist_ok=False)
    sessions = {
        variant: parse_variant_log(raw_dir / f"{variant}.log", variant, account)
        for variant in VARIANTS
    }
    if set(sessions) != set(VARIANTS):
        raise ControlledRunError("repeated matrix is incomplete")
    primary = [sessions[name] for name in VARIANTS[:3]]
    for invocation in range(account):
        peers = [session["observations"][invocation] for session in primary]
        for field in (
            "contract_sha256", "resource_sha256", "input_sha256",
            "oracle_output_sha256", "observed_output_sha256",
        ):
            if len({peer[field] for peer in peers}) != 1:
                raise ControlledRunError(
                    f"invocation {invocation + 1} primary {field} differs"
                )
    if len({session["identity"]["resource_sha256"] for session in primary}) != 1:
        raise ControlledRunError("repeated primary resource equality failed")
    prefixes = [
        prefix for prefix in manifest["sampling"]["campaign_prefix_accounts"]
        if prefix <= account
    ]
    accounts: dict[str, Any] = {}
    for prefix in prefixes:
        variants: dict[str, Any] = {}
        for variant, session in sessions.items():
            chosen = session["observations"][:prefix]
            variants[variant] = {
                "execution_cycles": [item["window_cycles"] for item in chosen],
                "execution_transactions": [
                    item["execution_traffic_accepted"] for item in chosen
                ],
                "phase_cycles": [item["phase_cycles"] for item in chosen],
                "cumulative_total_cycles": sum(
                    item["total_cycles"] for item in chosen
                ),
                "installation_count": 1,
            }
        accounts[str(prefix)] = variants
    report = {
        "schema": REPORT_SCHEMA,
        "experiment_id": "EXP-0006",
        "stage": "commissioning" if account == 4 else "campaign",
        "account": account,
        "manifest_sha256": _sha256(manifest_path),
        "matrix_complete": True,
        "semantic_valid": True,
        "resource_equality_verified": True,
        "execution_window_meaning_equal": True,
        "single_process_reset_installation_verified": True,
        "fresh_input_versions": list(range(1, account + 1)),
        "accounts": accounts,
        "sessions": sessions,
        "primary_fairness_finding": (
            "execution preserves lawful CPU load reuse and visible Graph extra "
            "traffic; staging/end-to-end remains claim-ineligible because CPU "
            "input generation is candidate-local while Graph input generation "
            "is testbench-side"
        ),
        "secondary_ablation": "not-activated",
        "claim_eligibility": {
            "execution_latency_traffic": True,
            "end_to_end_reuse_amortization": False,
            "rfc0005_go": False,
            "rfc0005_numerical_no_go": False,
        },
        "decision": "pause",
        "pause_point": "same-meaning-input-staging-initiator-boundary",
        "evidence_class": "rtl-simulation-pilot",
        "limitations": [
            "staging initiator differs between Graph and CPU",
            "simulator wall clock is operations-only",
            "no energy, synthesis timing, or area",
            "no VLIW/CGRA, elastic, stream, or hybrid candidates",
        ],
    }
    (derived_dir / "report.json").write_bytes(_canonical_bytes(report) + b"\n")
    return report


def seal_raw(run_dir: Path) -> dict[str, Any]:
    raw_dir = run_dir / "raw"
    report_path = run_dir / "derived/report.json"
    seal_path = run_dir / "raw-seal.json"
    if not raw_dir.is_dir() or not report_path.is_file():
        raise ControlledRunError("raw evidence and derived report are required")
    if seal_path.exists():
        raise ControlledRunError("raw evidence is already sealed")
    raw_files = sorted(path for path in raw_dir.iterdir() if path.is_file())
    if not raw_files:
        raise ControlledRunError("raw evidence is empty")
    seal = {
        "schema": "raveil.research-raw-seal/v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in raw_files
        ],
        "derived_report_sha256": _sha256(report_path),
    }
    seal_path.write_bytes(_canonical_bytes(seal) + b"\n")
    return seal


def _run_command(
    command: list[str], env: dict[str, str], log_path: Path, command_file: Path
) -> None:
    start = time.time_ns()
    with log_path.open("wb") as output:
        result = subprocess.run(
            command, env=env, stdout=output, stderr=subprocess.STDOUT
        )
    end = time.time_ns()
    record = {
        "argv": command,
        "environment": {
            key: env[key] for key in sorted(env)
            if key.startswith("RAVEIL_") and key != "RAVEIL_CHIPYARD_SOURCE"
        },
        "start_unix_ns": start,
        "end_unix_ns": end,
        "simulator_wall_clock_ns_operations_only": end - start,
        "exit_code": result.returncode,
        "log": log_path.name,
        "log_bytes": log_path.stat().st_size,
        "log_sha256": _sha256(log_path),
    }
    with command_file.open("ab") as target:
        target.write(_canonical_bytes(record) + b"\n")
    if result.returncode != 0:
        raise ControlledRunError(
            f"command failed with exit {result.returncode}: {command}"
        )


def collect(
    repo: Path, run_dir: Path, manifest_path: Path, chipyard: Path, account: int,
) -> dict[str, Any]:
    load_manifest(manifest_path)
    if account not in {4, 256}:
        raise ControlledRunError("collection account must be 4 or 256")
    if run_dir.exists():
        raise ControlledRunError("RUN-ID directory already exists")
    if subprocess.run(["git", "diff", "--quiet"], cwd=repo).returncode != 0 or subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo
    ).returncode != 0:
        raise ControlledRunError("collection requires a clean tracked worktree")
    if not chipyard.is_dir():
        raise ControlledRunError("pinned Chipyard source directory is missing")
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "frozen-manifest.json").write_bytes(manifest_path.read_bytes())
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    metadata = {
        "schema": "raveil.t0044-repeated-run-metadata/v1",
        "experiment_id": "EXP-0006",
        "stage": "commissioning" if account == 4 else "campaign",
        "account": account,
        "git_commit": git_commit,
        "manifest_sha256": _sha256(manifest_path),
        "platform": subprocess.check_output(["uname", "-s"], text=True).strip(),
        "architecture": subprocess.check_output(["uname", "-m"], text=True).strip(),
        "host_wall_clock_role": "operations-only-not-cpu-performance-evidence",
    }
    (raw_dir / "run-metadata.json").write_bytes(_canonical_bytes(metadata) + b"\n")
    scripts = {
        "static-graph": repo / "hardware/chisel/run-static-stencil-rtl.sh",
        "rocket-in-order": repo / "hardware/chisel/run-repeated-rocket-stencil.sh",
        "boom-ooo": repo / "hardware/chisel/run-repeated-boom-stencil.sh",
        "boom-serialize-dispatch": (
            repo / "hardware/chisel/run-repeated-boom-serialize-stencil.sh"
        ),
    }
    base_env = dict(os.environ)
    base_env["RAVEIL_CHIPYARD_SOURCE"] = str(chipyard)
    base_env["RAVEIL_REPEAT_ACCOUNT"] = str(account)
    command_file = raw_dir / "commands.jsonl"
    for variant in VARIANTS:
        _run_command(
            [str(scripts[variant])], dict(base_env),
            raw_dir / f"{variant}.log", command_file,
        )
    report = derive(run_dir, manifest_path, account)
    seal_raw(run_dir)
    return report


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
    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--repo", type=Path, required=True)
    collect_parser.add_argument("--run-dir", type=Path, required=True)
    collect_parser.add_argument("--manifest", type=Path, required=True)
    collect_parser.add_argument("--chipyard-source", type=Path, required=True)
    collect_parser.add_argument("--account", type=int, choices=(4, 256), required=True)
    derive_parser = subparsers.add_parser("derive")
    derive_parser.add_argument("--run-dir", type=Path, required=True)
    derive_parser.add_argument("--manifest", type=Path, required=True)
    derive_parser.add_argument("--account", type=int, choices=(4, 256), required=True)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify-graph":
            result = verify_graph_log(args.log, args.account)
        elif args.command == "verify-cpu":
            result = verify_cpu_log(
                args.log, args.implementation, args.account,
                args.source_sha256, args.artifact_sha256,
                args.toolchain_sha256, args.implementation_configuration,
                diagnostic=args.diagnostic_only,
            )
        elif args.command == "collect":
            result = collect(
                args.repo.resolve(), args.run_dir.resolve(),
                args.manifest.resolve(), args.chipyard_source.resolve(),
                args.account,
            )
        elif args.command == "derive":
            result = derive(
                args.run_dir.resolve(), args.manifest.resolve(), args.account
            )
        else:
            result = seal_raw(args.run_dir.resolve())
    except (ControlledRunError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
