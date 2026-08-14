"""Fail-closed EXP-0007 fixture-owned staging commissioning verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
from typing import Any

from .controlled_run import (
    ControlledRunError,
    _input_words,
    _parse_marker,
    _word_digest,
    fixture_owned_resource_tuple_id,
    static_graph_fixture_source_id,
)
from .static_region import static_stencil_oracle
from .t0044_repeated import (
    PHASES,
    VARIANTS,
    _canonical_bytes,
    _markers,
    _observed_output_hashes,
    _one_marker,
    _require_sha256,
    _run_command,
    _sha256,
    seal_raw,
)


SCHEMA = "raveil.t0044-fixture-observation/v1"
SESSION_SCHEMA = "raveil.t0044-fixture-session/v1"
MANIFEST_SCHEMA = "raveil.t0044-fixture-manifest/v1"
REPORT_SCHEMA = "raveil.t0044-fixture-report/v1"
RESOURCE_FIELDS = {
    "data_width_bits": "32",
    "operation_width_bytes": "4",
    "request_ports": "1",
    "response_ports": "1",
    "maximum_outstanding_requests": "1",
    "request_buffer_depth": "0",
    "response_buffer_depth": "1",
    "physical_banks": "1",
    "physical_words": "1024",
    "valid_words": "580",
    "arbitration": "phase-exclusive-provider-or-candidate",
    "accepted_operations": "read,write-byte-mask",
    "response_rule": "one-module-local-cycle-after-acceptance",
    "response_hold": "stable-until-consumed",
    "provider": "input-words-324-ascending-full-word",
    "provider_initiator": "fixture",
    "provider_request_buffer_depth": "0",
    "provider_release": "response-consume-word-323",
    "provider_rearm": "validation-response-consume-word-255",
}


def fixture_contract() -> dict[str, Any]:
    return {
        "schema": SESSION_SCHEMA,
        "resource_sha256": fixture_owned_resource_tuple_id(),
        "workload": "five-point-stencil-u32-rfc-0005",
        "input_versions": list(range(1, 257)),
        "account_prefixes": [1, 4, 16, 64, 256],
        "processes_per_candidate_session": 1,
        "resets_per_candidate_session": 1,
        "artifact_reloads_per_candidate_session": 0,
        "installation_count": 1,
        "staging_owner": "common-candidate-external-fixture",
        "staging_writes": 324,
        "release_edge": "response-consume-for-word-323",
        "rearm_edge": "validation-response-consume-for-word-255",
        "lifecycle_staging_start": "initial-trigger-or-previous-rearm",
        "fixture_provider_window_cycles": 648,
        "performance_claim": False,
    }


def fixture_contract_id() -> str:
    return hashlib.sha256(_canonical_bytes(fixture_contract())).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != MANIFEST_SCHEMA or value.get("experiment_id") != "EXP-0007":
        raise ControlledRunError("EXP-0007 manifest identity changed")
    if value.get("status") != "frozen-before-data":
        raise ControlledRunError("EXP-0007 manifest is not frozen")
    if set(value) != {
        "schema", "experiment_id", "status", "authority", "scope",
        "matrix", "resource", "workload", "session", "phases", "metrics",
        "sampling", "estimator", "environment", "identity_policy",
        "stop_conditions", "evidence",
    }:
        raise ControlledRunError("EXP-0007 manifest top-level schema changed")
    authority = value["authority"]
    if set(authority) != {
        "implementation_commit", "governance_ancestor", "t0042_commit",
        "architecture_decision", "predecessor_experiment",
    }:
        raise ControlledRunError("EXP-0007 authority schema changed")
    implementation_commit = authority["implementation_commit"]
    if (type(implementation_commit) is not str
            or len(implementation_commit) != 40
            or any(character not in "0123456789abcdef"
                   for character in implementation_commit)):
        raise ControlledRunError(
            "implementation_commit must be a lowercase Git SHA-1")
    if authority != {
        **authority,
        "governance_ancestor": "ae606dea3f74d6694eecbe91fc368b097f03758c",
        "t0042_commit": "528fbe28a0dcdfbab65d4ae2995c0876857e053a",
        "architecture_decision": "ADR-0047",
        "predecessor_experiment": "EXP-0006",
    }:
        raise ControlledRunError("EXP-0007 authority changed")
    run_ids = value.get("sampling", {}).get("run_ids")
    if (type(run_ids) is not dict or set(run_ids) != {"1", "4"}
            or any(type(item) is not str or not item
                   for item in run_ids.values())
            or run_ids["1"] == run_ids["4"]
            or not run_ids["1"].endswith("-commission1")
            or not run_ids["4"].endswith("-commission4")):
        raise ControlledRunError("EXP-0007 frozen RUN-IDs changed")
    exact_sections = {
        "scope": {
            "stage": "commissioning-1-and-4-fresh-inputs",
            "primary": list(VARIANTS[:3]),
            "diagnostic_only": [VARIANTS[3]],
            "secondary_ablation": "not-activated",
            "performance_claim": False,
            "rfc0005_go_no_go": False,
        },
        "matrix": {
            "complete_for_commissioning": list(VARIANTS),
            "configurations": {
                "static-graph": "StaticStencilRegion:d4bf9395a510385f:fixture-v1",
                "rocket-in-order": "chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig",
                "boom-ooo": "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig",
                "boom-serialize-dispatch": "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig",
            },
        },
        "resource": {
            "resource_sha256": fixture_owned_resource_tuple_id(),
            "fixture_contract_sha256": fixture_contract_id(),
            "single_ingress": True,
            "maximum_outstanding_requests": 1,
            "provider_request_buffer_depth": 0,
            "release_edge": "response-consume-for-word-323",
            "rearm_edge": "validation-response-consume-for-word-255",
        },
        "workload": {
            "name": "rfc-0005-five-point-stencil-u32",
            "input_shape": [18, 18], "output_shape": [16, 16],
            "input_words": 324, "output_words": 256,
            "formula": "u32(((index+1)*u32(seed*2654435761))^u32(index<<(seed&7))^u32(seed*17))",
            "input_order": "seed-equals-invocation-ascending-1-through-256",
            "oracle": "independent-host-static-stencil-oracle-v1",
            "result_reuse": False, "intermediate_reuse": False,
        },
        "session": {
            "processes_per_candidate": 1, "resets_per_candidate": 1,
            "installation_count": 1, "artifact_reloads": 0,
            "re_elaboration_or_reboot_between_invocations": False,
        },
        "phases": {
            "order": list(PHASES),
            "installation": "reset-through-first-fixture-trigger",
            "staging": "initial-trigger-or-previous-rearm-through-word-323-response-consume",
            "provider_window": "fixture-trigger-through-word-323-response-consume-exact-648",
            "execution": "common-release-through-final-candidate-memory-response",
            "completion": "execution-quiescence-through-validation-admission",
            "validation": "256-ordered-output-read-responses",
            "publication": "zero-cycle-marker-publication",
            "total": "sum-of-six-disjoint-phases",
        },
        "metrics": {
            "cycles": list(PHASES) + ["end-to-end-total", "execution-window",
                                      "fixture-provider-window"],
            "traffic": ["accepted-read", "accepted-write", "completed-read",
                        "completed-write", "bytes", "stall", "backpressure"],
            "useful_operations": ["load", "add", "store", "output"],
            "activity": ["fetch-decode-register", "rename-rob-issue-lsu",
                         "graph-schedule-control"],
            "simulator_wall_clock_role": "operations-only",
        },
        "sampling": {
            "inference_unit": "fresh-input-version",
            "commissioning_accounts": [1, 4],
            "campaign_prefixes_after-advance": [1, 4, 16, 64, 256],
            "deterministic_rerun_role": "exact-cycle-reproduction-only",
            "minimum_for_rfc0005_numerical_no_go": 64,
            "run_ids": run_ids,
        },
        "estimator": {
            "point": "median-across-fresh-input-versions",
            "interval_95": "exact-if-observed-input-invariant-else-percentile-bootstrap-median",
            "bootstrap_resamples": 100000, "bootstrap_seed_base": 7007,
            "commissioning_interval_claim_bearing": False,
        },
        "environment": {
            "path": "pinned-linux-amd64-docker-verilator",
            "host": "apple-silicon-non-authoritative",
            "chipyard_revision": "ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1",
            "rocket_chip_revision": "749a3eae9678bc70b029c5b9091fae33fad539c4",
            "toolchain_identity": "version-and-recipe-hash",
            "toolchain_byte_identity_limitation": "floating-apt-and-unchecksummed-scala-cli-inherited",
        },
        "identity_policy": {
            "required_per_session": ["configuration_sha256", "source_sha256",
                "artifact_sha256", "toolchain_sha256", "resource_sha256",
                "contract_sha256", "input_sha256", "oracle_output_sha256",
                "observed_output_sha256"],
            "stable_across-account-1-and-4": ["configuration_sha256",
                "source_sha256", "toolchain_sha256", "resource_sha256",
                "contract_sha256"],
            "artifact_difference_policy": "only-frozen-account-compile-parameter-may-differ",
            "historical_exp0006": "sealed-evidence-immutable-no-byte-identity-claim-for-new-builds",
        },
        "evidence": {
            "raw": "append-once-command-logs-plus-frozen-manifest",
            "derived": "separate-report-json",
            "seal": "sha256-manifest-after-derived-report",
            "evidence_class": "rtl-simulation-pilot",
            "clean_checkout_replay": True,
        },
    }
    for section, expected in exact_sections.items():
        if value[section] != expected:
            raise ControlledRunError(f"EXP-0007 {section} changed")
    required = [
        "oracle-mismatch", "resource-equality-failure", "unexplained-traffic",
        "required-accounting-missing", "source-config-toolchain-drift",
        "artifact-or-session-drift", "incomplete-matrix",
        "execution-window-meaning-differs", "restart-reset-reload-observed",
        "fixture-overlap-or-early-candidate-acceptance",
        "fixture-order-count-pending-or-release-failure",
        "fixture-rearm-failure", "input-byte-or-order-mismatch",
    ]
    if value["stop_conditions"] != required:
        raise ControlledRunError("EXP-0007 stop conditions are incomplete")
    return value


def _configuration_id(implementation: str, configuration: str,
                      source: str, toolchain: str) -> str:
    return hashlib.sha256(_canonical_bytes({
        "implementation": implementation,
        "implementation_configuration": configuration,
        "fixture_contract_sha256": fixture_contract_id(),
        "resource_sha256": fixture_owned_resource_tuple_id(),
        "source_sha256": source,
        "toolchain_sha256": toolchain,
    })).hexdigest()


def _fixture_records(lines: list[str], account: int) -> dict[int, str]:
    input_records = _markers(lines, "RAVEIL-FIXTURE-INPUT-V1")
    staging = _markers(lines, "RAVEIL-FIXTURE-STAGING-V1")
    resources = _markers(lines, "RAVEIL-FIXTURE-RESOURCE-V1")
    phases = _markers(lines, "RAVEIL-FIXTURE-PHASE-V1")
    rearms = _markers(lines, "RAVEIL-FIXTURE-REARM-V1")
    if (len(input_records) != 324 * account or len(staging) != account
            or len(resources) != account or len(phases) != 2 * account
            or len(rearms) != account):
        raise ControlledRunError("fixture staging/resource cardinality changed")

    indexed: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for prefix in (
        "RAVEIL-FIXTURE-PHASE-V1", "RAVEIL-FIXTURE-INPUT-V1",
        "RAVEIL-FIXTURE-STAGING-V1", "RAVEIL-FIXTURE-RESOURCE-V1",
        "RAVEIL-CONTROLLED-OUTPUT-V1", "RAVEIL-FIXTURE-REARM-V1",
    ):
        indexed[prefix] = [
            (line_number, _parse_marker(line))
            for line_number, line in enumerate(lines)
            if line.startswith(prefix + " ")
        ]
    observed_inputs: dict[int, list[int]] = {
        invocation: [] for invocation in range(1, account + 1)
    }
    for record in input_records:
        if set(record) != {"invocation", "seed", "index", "data"}:
            raise ControlledRunError("fixture input trace schema changed")
        invocation = int(record["invocation"])
        if invocation not in observed_inputs or record["seed"] != str(invocation):
            raise ControlledRunError("fixture input invocation changed")
        words = observed_inputs[invocation]
        if record["index"] != str(len(words)) or len(words) >= 324:
            raise ControlledRunError("fixture input trace order changed")
        try:
            value = int(record["data"], 16)
        except ValueError as error:
            raise ControlledRunError("fixture input data is not hex") from error
        if not 0 <= value <= 0xFFFFFFFF:
            raise ControlledRunError("fixture input data is not uint32")
        words.append(value)
    observed_hashes: dict[int, str] = {}
    for invocation, words in observed_inputs.items():
        if words != _input_words(invocation):
            raise ControlledRunError(
                f"fixture input differs from oracle at invocation {invocation}")
        observed_hashes[invocation] = _word_digest(words)
    for invocation, (stage, resource) in enumerate(zip(staging, resources), 1):
        invocation_phases = [
            (line_number, record)
            for line_number, record in indexed["RAVEIL-FIXTURE-PHASE-V1"]
            if record.get("invocation") == str(invocation)
        ]
        invocation_inputs = [
            line_number
            for line_number, record in indexed["RAVEIL-FIXTURE-INPUT-V1"]
            if record.get("invocation") == str(invocation)
        ]
        invocation_outputs = [
            line_number
            for line_number, record in indexed["RAVEIL-CONTROLLED-OUTPUT-V1"]
            if record.get("invocation") == str(invocation)
        ]
        stage_lines = [
            line_number
            for line_number, record in indexed["RAVEIL-FIXTURE-STAGING-V1"]
            if record.get("invocation") == str(invocation)
        ]
        resource_lines = [
            line_number
            for line_number, record in indexed["RAVEIL-FIXTURE-RESOURCE-V1"]
            if record.get("invocation") == str(invocation)
        ]
        rearm_records = [
            (line_number, record)
            for line_number, record in indexed["RAVEIL-FIXTURE-REARM-V1"]
            if record.get("invocation") == str(invocation)
        ]
        if (len(invocation_phases) != 2 or len(invocation_inputs) != 324
                or len(invocation_outputs) != 256 or len(stage_lines) != 1
                or len(resource_lines) != 1 or len(rearm_records) != 1):
            raise ControlledRunError("fixture invocation event cardinality changed")
        (start_line, start), (release_line, release) = invocation_phases
        phase_fields = {"invocation", "from", "to", "cycle",
                        "accepted", "completed", "pending"}
        if set(start) != phase_fields or set(release) != phase_fields:
            raise ControlledRunError("fixture phase marker schema changed")
        expected_from = "0" if invocation == 1 else "1"
        if (start["from"] != expected_from or start["to"] != "1"
                or release["from"] != "1" or release["to"] != "2"
                or start["pending"] != "0" or release["pending"] != "0"):
            raise ControlledRunError("fixture phase transition changed")
        try:
            staging_cycles = int(release["cycle"]) - int(start["cycle"])
        except ValueError as error:
            raise ControlledRunError("fixture phase cycle is not integral") from error
        if staging_cycles != 648:
            raise ControlledRunError("fixture release boundary changed")
        if not (
            start_line < min(invocation_inputs)
            and max(invocation_inputs) < release_line < stage_lines[0]
            and stage_lines[0] < resource_lines[0]
            and release_line < min(invocation_outputs)
        ):
            raise ControlledRunError("fixture event order changed")
        rearm_line, rearm = rearm_records[0]
        if rearm != {
            "invocation": str(invocation), "from": "4", "to": "1",
            "cycle": rearm.get("cycle", ""), "pending": "0",
            "validation_responses": "256", "rearm_count": "1",
        }:
            raise ControlledRunError("fixture rearm contract changed")
        try:
            int(rearm["cycle"])
        except ValueError as error:
            raise ControlledRunError("fixture rearm cycle is not integral") from error
        if max(invocation_outputs) >= rearm_line:
            raise ControlledRunError("fixture rearmed before validation completed")
        if stage != {
            "invocation": str(invocation), "seed": str(invocation),
            "accepted": "324", "completed": "324", "writes": "324",
            "first_word": "0", "last_word": "323", "pending": "0",
            "candidate_accepted_before_release": "0", "release_count": "1",
        }:
            raise ControlledRunError("fixture staging contract failed")
        expected_resource = {
            "invocation": str(invocation),
            "resource_sha256": fixture_owned_resource_tuple_id(),
            **RESOURCE_FIELDS,
        }
        if resource != expected_resource:
            raise ControlledRunError("fixture resource identity changed")
    return observed_hashes


def _observation(implementation: str, configuration: str, invocation: int,
                 source: str, artifact: str, toolchain: str,
                 phase_cycles: dict[str, int], output_sha256: str,
                 input_sha256: str, traffic: int) -> dict[str, Any]:
    inputs = _input_words(invocation)
    oracle = static_stencil_oracle(inputs)
    return {
        "schema": SCHEMA,
        "contract_sha256": fixture_contract_id(),
        "resource_sha256": fixture_owned_resource_tuple_id(),
        "source_sha256": source,
        "artifact_sha256": artifact,
        "toolchain_sha256": toolchain,
        "configuration_sha256": _configuration_id(
            implementation, configuration, source, toolchain),
        "implementation": implementation,
        "implementation_configuration": configuration,
        "invocation": invocation,
        "seed": invocation,
        "input_sha256": input_sha256,
        "oracle_output_sha256": _word_digest(oracle),
        "observed_output_sha256": output_sha256,
        "semantic_valid": output_sha256 == _word_digest(oracle),
        "phase_cycles": phase_cycles,
        "total_cycles": sum(phase_cycles.values()),
        "window_cycles": phase_cycles["execution"],
        "fixture_provider_cycles": 648,
        "execution_traffic_accepted": traffic,
        "execution_traffic_completed": traffic,
        "execution_traffic_pending": 0,
        "staging_traffic_accepted": 324,
        "staging_traffic_completed": 324,
        "accounting_complete": True,
        "evidence_class": "rtl-simulation-functional",
        "performance_claim": False,
    }


def _session(observations: list[dict[str, Any]], account: int,
             diagnostic: bool = False) -> dict[str, Any]:
    if len(observations) != account:
        raise ControlledRunError("fixture observation cardinality changed")
    stable = (
        "implementation", "implementation_configuration", "source_sha256",
        "artifact_sha256", "toolchain_sha256", "configuration_sha256",
        "contract_sha256", "resource_sha256",
    )
    for field in stable:
        if len({record[field] for record in observations}) != 1:
            raise ControlledRunError(f"fixture session {field} drifted")
    if [record["invocation"] for record in observations] != list(range(1, account + 1)):
        raise ControlledRunError("fixture invocation order changed")
    if len({record["input_sha256"] for record in observations}) != account:
        raise ControlledRunError("fixture inputs are not fresh")
    if any(not record["semantic_valid"] for record in observations):
        raise ControlledRunError("fixture semantic validation failed")
    identity = {field: observations[0][field] for field in stable}
    return {
        "schema": SESSION_SCHEMA,
        "session_sha256": hashlib.sha256(_canonical_bytes({
            **identity, "account": account, "diagnostic": diagnostic,
        })).hexdigest(),
        "account": account,
        "simulator_processes": 1,
        "resets": 1,
        "artifact_reloads": 0,
        "installation_count": 1,
        "diagnostic_only": diagnostic,
        "identity": identity,
        "observations": observations,
        "accounting_complete": True,
        "performance_claim": False,
    }


def verify_graph_log(path: Path, account: int) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    identity = _one_marker(lines, "CONTROLLED-GRAPH-IDENTITY-V1")
    for field in ("artifact_sha256", "toolchain_sha256"):
        _require_sha256(field, identity[field])
    input_hashes = _fixture_records(lines, account)
    outputs = _observed_output_hashes(lines, account)
    completes = _markers(lines, "RAVEIL-FIXTURE-GRAPH-COMPLETE-V1")
    activities = _markers(lines, "T0044-FIXTURE-GRAPH-ACTIVITY-V1")
    accounts = _markers(lines, "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1")
    if len(completes) != account or len(activities) != account or len(accounts) != 1:
        raise ControlledRunError("fixture Graph marker cardinality changed")
    source = static_graph_fixture_source_id()
    configuration = "StaticStencilRegion:d4bf9395a510385f:fixture-v1"
    observations = []
    expected_fields = {
        "status", "invocation", "seed", *{f"{phase}_cycles" for phase in PHASES},
        "total_cycles", "quiescence_before", "quiescence_after",
        "traffic_accepted", "traffic_completed", "traffic_pending",
        "graph_traffic", "unaccounted_window_traffic", "resource_sha256",
        "resource_contract_verified", "resource_equality_verified",
        "comparison_eligible", "performance",
    }
    for invocation, complete in enumerate(completes, 1):
        if set(complete) != expected_fields:
            raise ControlledRunError("fixture Graph complete schema changed")
        expected = {
            "status": "OK", "invocation": str(invocation), "seed": str(invocation),
            "installation_cycles": "0", "staging_cycles": "648",
            "execution_cycles": "3072", "completion_cycles": "1",
            "validation_cycles": "512", "publication_cycles": "0",
            "total_cycles": "4233", "quiescence_before": "1",
            "quiescence_after": "1", "traffic_accepted": "1536",
            "traffic_completed": "1536", "traffic_pending": "0",
            "graph_traffic": "1536", "unaccounted_window_traffic": "0",
            "resource_sha256": fixture_owned_resource_tuple_id(),
            "resource_contract_verified": "1", "resource_equality_verified": "0",
            "comparison_eligible": "0", "performance": "not-measured",
        }
        if complete != expected:
            raise ControlledRunError("fixture Graph complete values changed")
        phase = {name: int(complete[f"{name}_cycles"]) for name in PHASES}
        observations.append(_observation(
            "static-graph", configuration, invocation, source,
            identity["artifact_sha256"], identity["toolchain_sha256"],
            phase, outputs[invocation], input_hashes[invocation], 1536,
        ))
        activity = activities[invocation - 1]
        if activity != {
            "invocation": str(invocation), "request_stall_cycles": "0",
            "response_backpressure_cycles": "0", "read_transactions": "1280",
            "write_transactions": "256", "read_bytes": "5120",
            "write_bytes": "1024", "useful_loads": "1280",
            "useful_adds": "1024", "useful_stores": "256", "outputs": "256",
            "schedule_active_cycles": "3072", "launch_cycles": "0",
            "frontend_activity": "unavailable",
            "rename_rob_issue_lsu": "not-applicable",
        }:
            raise ControlledRunError("fixture Graph activity changed")
    if accounts[0] != {
        "status": "OK", "account": str(account), "installation_count": "1",
        "simulator_processes": "1", "resets": "1", "artifact_reloads": "0",
        "total_cycles": str(4233 * account), "performance": "not-measured",
    }:
        raise ControlledRunError("fixture Graph account changed")
    return _session(observations, account)


def verify_cpu_log(path: Path, variant: str, account: int) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if any(line.startswith(("RAVEIL-CONTROLLED-MIXED-TRAFFIC-V1",
                            "RAVEIL-CONTROLLED-VALIDATION-TRAFFIC-V1")) for line in lines):
        raise ControlledRunError("fixture CPU admitted unexplained traffic")
    host = _one_marker(lines, "RAVEIL-FIXTURE-CPU-HOST-V1")
    labels = {
        "rocket-in-order": ("rocket", "rocket-in-order",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig"),
        "boom-ooo": ("boom", "boom-ooo",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig"),
        "boom-serialize-dispatch": ("boom-serialize", "boom-ooo",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig"),
    }
    if variant not in labels:
        raise ControlledRunError("fixture CPU variant changed")
    label, implementation, configuration = labels[variant]
    if set(host) != {
        "status", "cpu", "config", "account", "simulator_processes",
        "resets", "artifact_reloads", "serialize_dispatch", "source_sha256",
        "artifact_sha256", "toolchain_sha256", "cache_source_sha256",
        "build_input_sha256", "resource_sha256", "workload", "oracle",
        "accounting", "evidence", "performance",
    }:
        raise ControlledRunError("fixture CPU host schema changed")
    for field in ("source_sha256", "artifact_sha256", "toolchain_sha256",
                  "cache_source_sha256", "build_input_sha256"):
        _require_sha256(field, host[field])
    for field, expected in {
        "status": "OK", "cpu": label, "config": configuration,
        "account": str(account), "simulator_processes": "1", "resets": "1",
        "artifact_reloads": "0", "resource_sha256": fixture_owned_resource_tuple_id(),
        "workload": "frozen-rfc-0005", "oracle": "independent-host",
        "accounting": "pending-completed-outer-raw-verification",
        "evidence": "rtl-simulation-functional",
        "serialize_dispatch": "1" if variant == "boom-serialize-dispatch" else "0",
        "performance": "not-measured",
    }.items():
        if host.get(field) != expected:
            raise ControlledRunError(f"fixture CPU host {field} changed")
    input_hashes = _fixture_records(lines, account)
    outputs = _observed_output_hashes(lines, account)
    windows = _markers(lines, "RAVEIL-REPEATED-WINDOW-V1")
    completes = _markers(lines, "RAVEIL-REPEATED-CPU-COMPLETE-V1")
    activities = _markers(lines, "T0044-REPEATED-CPU-ACTIVITY-V1")
    if not all(len(records) == account for records in (windows, completes, activities)):
        raise ControlledRunError("fixture CPU marker cardinality changed")
    observations = []
    for invocation, (window, complete, activity) in enumerate(
            zip(windows, completes, activities), 1):
        if any(record.get("invocation") != str(invocation)
               for record in (window, complete, activity)):
            raise ControlledRunError("fixture CPU invocation order changed")
        if set(window) != {
            "invocation", "start_cycle", "end_cycle", "cycles", "accepted",
            "completed", "reads", "writes", "expected_accepted",
            "expected_completed", "unexpected_accepted",
            "unexpected_completed", "origin_accepted", "origin_completed",
            "nonorigin_accepted", "nonorigin_completed", "pending",
            "quiescence_before", "quiescence_after",
        }:
            raise ControlledRunError("fixture CPU window schema changed")
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
                raise ControlledRunError(f"fixture CPU window {field} changed")
        if int(window["end_cycle"]) - int(window["start_cycle"]) != int(window["cycles"]):
            raise ControlledRunError("fixture CPU window boundary changed")
        if set(complete) != {
            "invocation", *{f"{phase}_cycles" for phase in PHASES},
            "total_cycles", "accepted", "completed", "installation_reads",
            "installation_writes", "staging_writes", "execution_reads",
            "execution_writes", "validation_reads",
        }:
            raise ControlledRunError("fixture CPU complete schema changed")
        for field, expected in {
            "accepted": "2216" if invocation == 1 else "1636",
            "completed": "2216" if invocation == 1 else "1636",
            "installation_reads": "0",
            "installation_writes": "580" if invocation == 1 else "0",
            "staging_writes": "324", "execution_reads": "800",
            "execution_writes": "256", "validation_reads": "256",
            "publication_cycles": "0",
        }.items():
            if complete.get(field) != expected:
                raise ControlledRunError(f"fixture CPU complete {field} changed")
        phase = {name: int(complete[f"{name}_cycles"]) for name in PHASES}
        if phase["execution"] != int(window["cycles"]):
            raise ControlledRunError("fixture CPU execution meaning changed")
        if sum(phase.values()) != int(complete["total_cycles"]):
            raise ControlledRunError("fixture CPU total accounting changed")
        if set(activity) != {
            "invocation", "request_stall_cycles",
            "response_backpressure_cycles", "read_transactions",
            "write_transactions", "read_bytes", "write_bytes",
            "useful_loads", "useful_adds", "useful_stores", "outputs",
            "frontend_activity", "rename_rob_issue_lsu",
        }:
            raise ControlledRunError("fixture CPU activity schema changed")
        for field, expected in {
            "read_transactions": "800", "write_transactions": "256",
            "read_bytes": "3200", "write_bytes": "1024",
            "useful_loads": "1280", "useful_adds": "1024",
            "useful_stores": "256", "outputs": "256",
            "frontend_activity": "unavailable", "rename_rob_issue_lsu": "unavailable",
        }.items():
            if activity.get(field) != expected:
                raise ControlledRunError(f"fixture CPU activity {field} changed")
        observations.append(_observation(
            implementation, configuration, invocation, host["source_sha256"],
            host["artifact_sha256"], host["toolchain_sha256"], phase,
            outputs[invocation], input_hashes[invocation], 1056,
        ))
    return _session(observations, account, variant == "boom-serialize-dispatch")


def parse_variant_log(path: Path, variant: str, account: int) -> dict[str, Any]:
    if not 1 <= account <= 256:
        raise ControlledRunError("fixture account must be in [1,256]")
    return (verify_graph_log(path, account) if variant == "static-graph"
            else verify_cpu_log(path, variant, account))


def derive(run_dir: Path, manifest_path: Path, account: int) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if account not in {1, 4}:
        raise ControlledRunError("EXP-0007 commissioning account must be 1 or 4")
    derived_dir = run_dir / "derived"
    derived_dir.mkdir(exist_ok=False)
    sessions = {variant: parse_variant_log(
        run_dir / "raw" / f"{variant}.log", variant, account)
        for variant in VARIANTS}
    primary = [sessions[name] for name in VARIANTS[:3]]
    for index in range(account):
        peers = [session["observations"][index] for session in primary]
        for field in ("contract_sha256", "resource_sha256", "input_sha256",
                      "oracle_output_sha256", "observed_output_sha256"):
            if len({peer[field] for peer in peers}) != 1:
                raise ControlledRunError(f"fixture primary {field} differs")
    cross_account_identity_verified = False
    if account == 4:
        account_one_path = (
            run_dir.parent / manifest["sampling"]["run_ids"]["1"]
            / "derived" / "report.json"
        )
        account_one = json.loads(account_one_path.read_text(encoding="utf-8"))
        if (account_one.get("schema") != REPORT_SCHEMA
                or account_one.get("experiment_id") != "EXP-0007"
                or account_one.get("account") != 1
                or account_one.get("manifest_sha256") != _sha256(manifest_path)):
            raise ControlledRunError("EXP-0007 account-1 peer is not authoritative")
        stable_across_accounts = (
            "implementation", "implementation_configuration", "source_sha256",
            "toolchain_sha256", "configuration_sha256", "contract_sha256",
            "resource_sha256",
        )
        for variant in VARIANTS:
            prior = account_one["sessions"][variant]["observations"][0]
            current = sessions[variant]["observations"][0]
            for field in stable_across_accounts:
                if prior[field] != current[field]:
                    raise ControlledRunError(
                        f"fixture {variant} {field} drifted across accounts")
            for field in ("input_sha256", "oracle_output_sha256",
                          "observed_output_sha256"):
                if prior[field] != current[field]:
                    raise ControlledRunError(
                        f"fixture {variant} input-1 {field} drifted")
        cross_account_identity_verified = True
    def summarize(values: list[int], seed: int) -> dict[str, Any]:
        ordered = sorted(values)
        result: dict[str, Any] = {
            "exact": values,
            "minimum": ordered[0],
            "median": statistics.median(values),
            "maximum": ordered[-1],
        }
        if len(set(values)) == 1:
            result["interval_95"] = {
                "method": "exact-observed-input-invariant",
                "low": values[0], "high": values[0],
                "fresh_input_count": len(values),
                "coverage": "not-population-inference",
                "commissioning_claim_bearing": False,
            }
        else:
            generator = random.Random(seed)
            estimates = sorted(statistics.median(
                generator.choices(values, k=len(values))) for _ in range(100000))
            result["interval_95"] = {
                "method": "percentile-bootstrap-median-fresh-input",
                "resamples": 100000, "seed": seed,
                "low": estimates[2500], "high": estimates[97499],
                "fresh_input_count": len(values),
                "commissioning_claim_bearing": False,
            }
        return result
    comparison_rows: dict[str, Any] = {}
    for offset, (variant, session) in enumerate(sessions.items()):
        observations = session["observations"]
        comparison_rows[variant] = {
            "role": "diagnostic-only" if session["diagnostic_only"] else "primary",
            "execution_cycles": summarize(
                [item["window_cycles"] for item in observations], 7007 + offset),
            "execution_transactions": [
                item["execution_traffic_accepted"] for item in observations],
            "staging_transactions": [
                item["staging_traffic_accepted"] for item in observations],
            "fixture_provider_cycles": [
                item["fixture_provider_cycles"] for item in observations],
            "phase_cycles": [item["phase_cycles"] for item in observations],
            "end_to_end_total_cycles": [item["total_cycles"] for item in observations],
        }
    report = {
        "schema": REPORT_SCHEMA,
        "experiment_id": "EXP-0007",
        "stage": "commissioning",
        "account": account,
        "manifest_sha256": _sha256(manifest_path),
        "matrix_complete": True,
        "semantic_valid": True,
        "resource_equality_verified": True,
        "staging_initiator_equal": True,
        "execution_window_meaning_equal": True,
        "single_process_reset_installation_verified": True,
        "cross_account_identity_verified": cross_account_identity_verified,
        "fresh_input_versions": list(range(1, account + 1)),
        "comparison_rows": comparison_rows,
        "sessions": sessions,
        "primary_fairness_finding": (
            "common fixture-owned staging removes initiator asymmetry; legal CPU "
            "load reuse and Graph execution traffic remain visible design results"
        ),
        "secondary_ablation": "not-activated",
        "claim_eligibility": {
            "commissioning_functional_accounting": True,
            "execution_latency_traffic": True,
            "end_to_end_reuse_amortization": account == 4,
            "rfc0005_go": False,
            "rfc0005_numerical_no_go": False,
        },
        "decision": "advance" if account == 4 else "commissioning-continue",
        "evidence_class": "rtl-simulation-pilot",
        "limitations": [
            "fewer than 64 fresh inputs", "simulator wall clock is operations-only",
            "no energy, synthesis timing, or area",
            "no VLIW/CGRA, elastic, stream, or hybrid candidates",
        ],
    }
    (derived_dir / "report.json").write_bytes(_canonical_bytes(report) + b"\n")
    return report


def collect(repo: Path, run_dir: Path, manifest_path: Path,
            chipyard: Path, account: int) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if account not in {1, 4}:
        raise ControlledRunError("EXP-0007 commissioning account must be 1 or 4")
    if run_dir.exists():
        raise ControlledRunError("RUN-ID directory already exists")
    if run_dir.name != manifest["sampling"]["run_ids"][str(account)]:
        raise ControlledRunError("run directory does not match frozen RUN-ID")
    if subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo, text=True,
    ):
        raise ControlledRunError("collection requires a clean tracked worktree")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    implementation_commit = manifest["authority"]["implementation_commit"]
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", implementation_commit, commit],
        cwd=repo,
    ).returncode:
        raise ControlledRunError("implementation authority is not an ancestor")
    changed_after_implementation = subprocess.check_output(
        ["git", "diff", "--name-only", f"{implementation_commit}..{commit}"],
        cwd=repo, text=True,
    ).splitlines()
    allowed_after_implementation = {
        "benchmarks/manifests/t0044-fixture-owned-staging-v1.json",
        "docs/STATUS.md", "TODO.md", "docs/ROADMAP.md",
        "docs/OPEN_QUESTIONS.md", "docs/experiments/README.md",
        "docs/experiments/EXP-0007-fixture-owned-input-staging.md",
        "docs/log/2026-08-14.md",
    }
    if not set(changed_after_implementation).issubset(allowed_after_implementation):
        raise ControlledRunError("source/config changed after implementation freeze")
    raw = run_dir / "raw"
    raw.mkdir(parents=True)
    (raw / "frozen-manifest.json").write_bytes(manifest_path.read_bytes())
    metadata = {
        "schema": "raveil.t0044-fixture-run-metadata/v1",
        "experiment_id": "EXP-0007", "stage": "commissioning",
        "account": account, "git_commit": commit,
        "manifest_sha256": _sha256(manifest_path),
        "platform": subprocess.check_output(["uname", "-s"], text=True).strip(),
        "architecture": subprocess.check_output(["uname", "-m"], text=True).strip(),
        "chipyard_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=chipyard, text=True).strip(),
        "rocket_chip_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=Path(chipyard).parent / "rocket-chip",
            text=True,
        ).strip(),
        "host_wall_clock_role": "operations-only-not-cpu-performance-evidence",
    }
    if (metadata["chipyard_revision"] != manifest["environment"]["chipyard_revision"]
            or metadata["rocket_chip_revision"]
            != manifest["environment"]["rocket_chip_revision"]):
        raise ControlledRunError("pinned CPU source revision drifted")
    (raw / "run-metadata.json").write_bytes(_canonical_bytes(metadata) + b"\n")
    scripts = {
        "static-graph": repo / "hardware/chisel/run-static-stencil-rtl.sh",
        "rocket-in-order": repo / "hardware/chisel/run-fixture-repeated-rocket-stencil.sh",
        "boom-ooo": repo / "hardware/chisel/run-fixture-repeated-boom-stencil.sh",
        "boom-serialize-dispatch": repo / "hardware/chisel/run-fixture-repeated-boom-serialize-stencil.sh",
    }
    env = dict(os.environ)
    for key in (
        "RAVEIL_PILOT_SEED", "RAVEIL_FIXTURE_REPEAT_ACCOUNT",
        "RAVEIL_REPEAT_ACCOUNT", "RAVEIL_BUILD_ONLY",
        "RAVEIL_CONTROLLED_SEED", "RAVEIL_CONTROLLED_INVOCATION",
        "RAVEIL_CONTROLLED_SERIALIZE_DISPATCH",
    ):
        env.pop(key, None)
    env["RAVEIL_CHIPYARD_SOURCE"] = str(chipyard)
    env["RAVEIL_ROCKET_CHIP_SOURCE"] = str(Path(chipyard).parent / "rocket-chip")
    env["RAVEIL_REPEAT_ACCOUNT"] = str(account)
    command_file = raw / "commands.jsonl"
    for variant in VARIANTS:
        required = {"RAVEIL-CONTROLLED-OUTPUT-V1": 256 * account,
                    "RAVEIL-FIXTURE-INPUT-V1": 324 * account,
                    "RAVEIL-FIXTURE-PHASE-V1": 2 * account,
                    "RAVEIL-FIXTURE-REARM-V1": account,
                    "RAVEIL-FIXTURE-STAGING-V1": account,
                    "RAVEIL-FIXTURE-RESOURCE-V1": account}
        if variant == "static-graph":
            required.update({"RAVEIL-FIXTURE-GRAPH-COMPLETE-V1": account,
                             "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1": 1})
        else:
            required.update({"RAVEIL-REPEATED-CPU-COMPLETE-V1": account,
                             "RAVEIL-FIXTURE-CPU-HOST-V1": 1})
        variant_env = dict(env)
        if variant == "static-graph":
            variant_env.pop("RAVEIL_REPEAT_ACCOUNT")
            variant_env["RAVEIL_FIXTURE_REPEAT_ACCOUNT"] = str(account)
        _run_command([str(scripts[variant])], variant_env,
                     raw / f"{variant}.log", command_file, required)
    report = derive(run_dir, manifest_path, account)
    seal_raw(run_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify EXP-0007 fixture RTL logs")
    commands = parser.add_subparsers(dest="command", required=True)
    collect_p = commands.add_parser("collect")
    for item in (collect_p,):
        item.add_argument("--repo", type=Path, required=True)
        item.add_argument("--run-dir", type=Path, required=True)
        item.add_argument("--manifest", type=Path, required=True)
        item.add_argument("--chipyard-source", type=Path, required=True)
        item.add_argument("--account", type=int, choices=(1, 4), required=True)
    derive_p = commands.add_parser("derive")
    derive_p.add_argument("--run-dir", type=Path, required=True)
    derive_p.add_argument("--manifest", type=Path, required=True)
    derive_p.add_argument("--account", type=int, choices=(1, 4), required=True)
    seal_p = commands.add_parser("seal")
    seal_p.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            result = collect(args.repo.resolve(), args.run_dir.resolve(),
                args.manifest.resolve(), args.chipyard_source.resolve(), args.account)
        elif args.command == "derive":
            result = derive(args.run_dir.resolve(), args.manifest.resolve(), args.account)
        else:
            result = seal_raw(args.run_dir.resolve())
    except (ControlledRunError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
