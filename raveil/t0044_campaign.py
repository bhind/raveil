"""Fail-closed EXP-0008 nested-prefix RTL latency/traffic campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time
from typing import Any

from .controlled_run import ControlledRunError, fixture_owned_resource_tuple_id
from .t0044_fixture import (
    RESOURCE_FIELDS,
    fixture_contract_id,
    parse_variant_log,
)
from .t0044_repeated import (
    PHASES,
    VARIANTS,
    _canonical_bytes,
    _sha256,
    seal_raw,
)


MANIFEST_SCHEMA = "raveil.t0044-fixture-campaign-manifest/v1"
REPORT_SCHEMA = "raveil.t0044-fixture-campaign-report/v1"
PREFIXES = (1, 4, 16, 64, 256)
FULL_ACCOUNT = 256
BOOTSTRAP_RESAMPLES = 100000


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != MANIFEST_SCHEMA:
        raise ControlledRunError("EXP-0008 manifest schema changed")
    if value.get("experiment_id") != "EXP-0008":
        raise ControlledRunError("EXP-0008 manifest identity changed")
    if value.get("status") != "frozen-before-data":
        raise ControlledRunError("EXP-0008 manifest is not frozen")
    expected_top = {
        "schema", "experiment_id", "status", "authority", "scope", "matrix",
        "resource", "workload", "session", "phases", "metrics", "sampling",
        "estimator", "decision_rules", "environment", "identity_policy",
        "operations", "stop_conditions", "evidence",
    }
    if set(value) != expected_top:
        raise ControlledRunError("EXP-0008 manifest top-level schema changed")
    authority = value["authority"]
    if set(authority) != {
        "implementation_commit", "governance_ancestor", "t0042_commit",
        "architecture_decision", "commissioning_experiment",
    }:
        raise ControlledRunError("EXP-0008 authority schema changed")
    implementation_commit = authority["implementation_commit"]
    if (type(implementation_commit) is not str
            or len(implementation_commit) != 40
            or any(character not in "0123456789abcdef"
                   for character in implementation_commit)):
        raise ControlledRunError(
            "implementation_commit must be a lowercase Git SHA-1")
    if authority != {
        "implementation_commit": implementation_commit,
        "governance_ancestor": "ae606dea3f74d6694eecbe91fc368b097f03758c",
        "t0042_commit": "528fbe28a0dcdfbab65d4ae2995c0876857e053a",
        "architecture_decision": "ADR-0047",
        "commissioning_experiment": "EXP-0007",
    }:
        raise ControlledRunError("EXP-0008 authority changed")
    run_id = value.get("sampling", {}).get("run_id")
    if (type(run_id) is not str or not run_id
            or not run_id.endswith("-campaign256")):
        raise ControlledRunError("EXP-0008 frozen RUN-ID changed")

    exact = {
        "scope": {
            "stage": "nested-prefix-1-4-16-64-256",
            "primary": list(VARIANTS[:3]),
            "diagnostic_only": [VARIANTS[3]],
            "secondary_ablation": "not-activated",
            "performance_scope": "latency-traffic-only",
            "rfc0005_go": False,
        },
        "matrix": {
            "complete": list(VARIANTS),
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
            "provider_window_cycles": 648,
            "release_edge": "response-consume-for-word-323",
            "rearm_edge": "validation-response-consume-for-word-255",
        },
        "workload": {
            "name": "rfc-0005-five-point-stencil-u32",
            "input_shape": [18, 18], "output_shape": [16, 16],
            "input_words": 324, "output_words": 256,
            "formula": "u32(((index+1)*u32(seed*2654435761))^u32(index<<(seed&7))^u32(seed*17))",
            "seed_schedule": "seed-equals-invocation-index-1-through-256",
            "oracle": "independent-host-static-stencil-oracle-v1",
            "result_reuse": False, "intermediate_reuse": False,
        },
        "session": {
            "processes_per_candidate": 1, "resets_per_candidate": 1,
            "installation_count": 1, "artifact_reloads": 0,
            "re_elaboration_or_reboot_between_invocations": False,
            "full_account": FULL_ACCOUNT,
        },
        "phases": {
            "order": list(PHASES),
            "installation": "reset-through-first-fixture-trigger-once",
            "staging": "initial-trigger-or-previous-rearm-through-word-323-response-consume",
            "provider_window": "fixture-trigger-through-word-323-response-consume-exact-648",
            "execution": "common-release-through-final-candidate-memory-response",
            "completion": "execution-quiescence-through-validation-admission",
            "validation": "256-ordered-output-read-responses",
            "publication": "zero-cycle-marker-publication",
            "total": "sum-of-six-disjoint-phases",
        },
        "metrics": {
            "cycles": list(PHASES) + ["session-total", "amortized-total",
                                      "execution-window", "fixture-provider-window"],
            "traffic": ["accepted-read", "accepted-write", "completed-read",
                        "completed-write", "bytes", "stall", "backpressure"],
            "useful_operations": ["load", "add", "store", "output"],
            "activity": ["fetch-decode-register", "rename-rob-issue-lsu",
                         "graph-schedule-control"],
            "missing_activity_policy": "unavailable-is-not-zero",
            "simulator_wall_clock_role": "operations-only",
        },
        "sampling": {
            "inference_unit": "fresh-input-version",
            "prefix_relationship": "nested-prefixes-of-one-256-input-session",
            "prefixes": list(PREFIXES),
            "new_inputs_by_prefix": {"1": 1, "4": 3, "16": 12,
                                     "64": 48, "256": 192},
            "deterministic_rerun_is_not_sample": True,
            "minimum_for_rfc0005_numerical_no_go": 64,
            "run_id": run_id,
        },
        "estimator": {
            "candidate_point": "median-across-fresh-input-versions",
            "candidate_interval_95": "exact-if-observed-input-invariant-else-percentile-bootstrap-median",
            "paired_execution_point": "median-of-same-input-graph-over-cpu-ratios",
            "paired_execution_interval_95": "percentile-bootstrap-paired-median",
            "correct_latency_point": "ratio-of-prefix-cumulative-six-phase-cycles",
            "correct_latency_interval_95": "paired-bootstrap-ratio-with-installation-fixed-once",
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "candidate_seed_base": 27007,
            "paired_seed_base": 37007,
            "interval_claim_bearing_prefixes": [64, 256],
            "finite-seed-schedule_scope": "empirical-prefix-not-unbounded-workload-population",
        },
        "decision_rules": {
            "functional_or_fairness_failure": "fail-closed-no-claim",
            "rfc0005_correct_latency_ratio": "static-graph-over-rocket",
            "latency_no_go_at_64": "upper-95-percent-bound-greater-than-1.05",
            "configuration_break_even": "cumulative-six-phase-graph-no-greater-than-rocket-by-64",
            "numeric_decision_prefix": 64,
            "continue_to_256_after_latency_result": True,
            "go_from_latency_traffic_only": False,
            "energy_timing_area_rules": "not-evaluated",
            "other_organizations": "not-evaluated",
        },
        "environment": {
            "path": "pinned-linux-amd64-docker-verilator",
            "host": "apple-silicon-non-authoritative",
            "chipyard_revision": "ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1",
            "rocket_chip_revision": "749a3eae9678bc70b029c5b9091fae33fad539c4",
            "toolchain_identity": "version-and-recipe-hash",
            "toolchain_byte_identity_limitation": "floating-apt-and-unchecksummed-scala-cli-inherited",
        },
        "operations": {
            "minimum_free_bytes_before_collection": 5368709120,
            "maximum_raw_log_bytes_per_candidate": 2147483648,
            "terminal_marker_drain_timeout_seconds": 120,
            "partial_failure_evidence": "append-once-failure-record-and-failed-raw-seal",
            "host_wall_clock_use": "operations-only",
        },
        "evidence": {
            "raw": "one-256-input-command-log-per-variant-plus-frozen-manifest",
            "derived": "one-report-with-five-nested-prefix-summaries",
            "seal": "sha256-manifest-after-derived-report",
            "evidence_class": "rtl-simulation-latency-traffic-campaign",
            "clean_checkout_replay": True,
        },
    }
    for section, expected in exact.items():
        if value[section] != expected:
            raise ControlledRunError(f"EXP-0008 {section} changed")
    required_stops = [
        "oracle-mismatch", "resource-equality-failure", "unexplained-traffic",
        "required-accounting-missing", "source-config-toolchain-drift",
        "artifact-or-session-drift", "incomplete-matrix",
        "execution-window-meaning-differs", "restart-reset-reload-observed",
        "fixture-overlap-or-early-candidate-acceptance",
        "fixture-order-count-pending-or-release-failure",
        "fixture-rearm-failure", "input-byte-or-order-mismatch",
        "prefix-relationship-failure", "raw-log-limit-exceeded",
        "insufficient-free-space",
    ]
    if value["stop_conditions"] != required_stops:
        raise ControlledRunError("EXP-0008 stop conditions changed")
    identities = value["identity_policy"]
    if set(identities) != {
        "required_per_session", "stable_expected_by_variant",
        "stable_across_full_session", "artifact_difference_policy",
        "commissioning_evidence",
    }:
        raise ControlledRunError("EXP-0008 identity policy schema changed")
    if identities["required_per_session"] != [
        "configuration_sha256", "source_sha256", "artifact_sha256",
        "toolchain_sha256", "resource_sha256", "contract_sha256",
        "input_sha256", "oracle_output_sha256", "observed_output_sha256",
    ]:
        raise ControlledRunError("EXP-0008 required identities changed")
    expected_identity_fields = {
        "implementation", "implementation_configuration", "source_sha256",
        "configuration_sha256", "toolchain_sha256", "resource_sha256",
        "contract_sha256",
    }
    stable = identities["stable_expected_by_variant"]
    if set(stable) != set(VARIANTS):
        raise ControlledRunError("EXP-0008 variant identities changed")
    for variant in VARIANTS:
        if set(stable[variant]) != expected_identity_fields:
            raise ControlledRunError("EXP-0008 stable identity fields changed")
        for field in expected_identity_fields - {
                "implementation", "implementation_configuration"}:
            digest = stable[variant][field]
            if (type(digest) is not str or len(digest) != 64
                    or any(character not in "0123456789abcdef"
                           for character in digest)):
                raise ControlledRunError("EXP-0008 stable identity is not SHA-256")
    if identities["stable_across_full_session"] is not True:
        raise ControlledRunError("EXP-0008 session identity rule changed")
    if identities["artifact_difference_policy"] != (
            "account-256-artifact-bound-per-session-no-cross-account-equality"):
        raise ControlledRunError("EXP-0008 artifact policy changed")
    if identities["commissioning_evidence"] != (
            "EXP-0007-hashes-used-for-identity-only-not-performance-values"):
        raise ControlledRunError("EXP-0008 predecessor policy changed")
    return value


def _percentile_interval(values: list[float], seed: int,
                         claim_bearing: bool) -> dict[str, Any]:
    if len(set(values)) == 1:
        return {
            "method": "exact-observed-input-invariant",
            "low": values[0], "high": values[0],
            "fresh_input_count": len(values),
            "coverage": "finite-observed-prefix",
            "claim_bearing": claim_bearing,
        }
    generator = random.Random(seed)
    count = len(values)
    estimates = sorted(statistics.median(
        generator.choices(values, k=count)) for _ in range(BOOTSTRAP_RESAMPLES))
    return {
        "method": "percentile-bootstrap-median-fresh-input",
        "resamples": BOOTSTRAP_RESAMPLES, "seed": seed,
        "low": estimates[int(BOOTSTRAP_RESAMPLES * 0.025)],
        "high": estimates[int(BOOTSTRAP_RESAMPLES * 0.975) - 1],
        "fresh_input_count": count, "coverage": "finite-seed-schedule",
        "claim_bearing": claim_bearing,
    }


def _candidate_summary(observations: list[dict[str, Any]], prefix: int,
                       seed: int) -> dict[str, Any]:
    selected = observations[:prefix]
    execution = [item["window_cycles"] for item in selected]
    interval = _percentile_interval(
        [float(item) for item in execution], seed, prefix >= 64)
    if all(float(value).is_integer() for value in interval.values()
           if type(value) is float):
        interval = {
            key: int(value) if type(value) is float else value
            for key, value in interval.items()
        }
    phase_totals = {
        phase: sum(item["phase_cycles"][phase] for item in selected)
        for phase in PHASES
    }
    session_total = sum(phase_totals.values())
    return {
        "execution_cycles": {
            "exact": execution, "minimum": min(execution),
            "median": statistics.median(execution), "maximum": max(execution),
            "interval_95": interval,
        },
        "phase_totals": phase_totals,
        "session_total_cycles": session_total,
        "amortized_total_cycles_per_invocation": session_total / prefix,
        "execution_transactions": {
            "exact": [item["execution_traffic_accepted"] for item in selected],
            "accepted_equals_completed": True, "pending": 0,
        },
        "staging_transactions": {
            "exact": [item["staging_traffic_accepted"] for item in selected],
            "accepted_equals_completed": True,
        },
        "fixture_provider_cycles": {
            "exact": [item["fixture_provider_cycles"] for item in selected],
        },
    }


def _paired_execution_ratio(graph: list[dict[str, Any]],
                            peer: list[dict[str, Any]], prefix: int,
                            seed: int) -> dict[str, Any]:
    ratios = [
        graph[index]["window_cycles"] / peer[index]["window_cycles"]
        for index in range(prefix)
    ]
    return {
        "orientation": "static-graph-over-peer-lower-is-better",
        "unit": "same-fresh-input-invocation",
        "exact": ratios,
        "median": statistics.median(ratios),
        "interval_95": _percentile_interval(ratios, seed, prefix >= 64),
    }


def _correct_latency_ratio(graph: list[dict[str, Any]],
                           peer: list[dict[str, Any]], prefix: int,
                           seed: int) -> dict[str, Any]:
    graph_selected = graph[:prefix]
    peer_selected = peer[:prefix]
    graph_install = graph_selected[0]["phase_cycles"]["installation"]
    peer_install = peer_selected[0]["phase_cycles"]["installation"]
    graph_variable = [
        item["total_cycles"] - item["phase_cycles"]["installation"]
        for item in graph_selected
    ]
    peer_variable = [
        item["total_cycles"] - item["phase_cycles"]["installation"]
        for item in peer_selected
    ]
    numerator = graph_install + sum(graph_variable)
    denominator = peer_install + sum(peer_variable)
    point = numerator / denominator
    if prefix == 1:
        interval = {
            "method": "exact-single-fresh-input",
            "low": point, "high": point, "fresh_input_count": 1,
            "installation_treatment": "fixed-once",
            "claim_bearing": False,
        }
    else:
        generator = random.Random(seed)
        estimates = []
        for _ in range(BOOTSTRAP_RESAMPLES):
            indices = [generator.randrange(prefix) for _ in range(prefix)]
            graph_total = graph_install + sum(graph_variable[i] for i in indices)
            peer_total = peer_install + sum(peer_variable[i] for i in indices)
            estimates.append(graph_total / peer_total)
        estimates.sort()
        interval = {
            "method": "paired-bootstrap-cumulative-ratio-installation-fixed-once",
            "resamples": BOOTSTRAP_RESAMPLES, "seed": seed,
            "low": estimates[int(BOOTSTRAP_RESAMPLES * 0.025)],
            "high": estimates[int(BOOTSTRAP_RESAMPLES * 0.975) - 1],
            "fresh_input_count": prefix,
            "installation_treatment": "fixed-once",
            "claim_bearing": prefix >= 64,
        }
    return {
        "orientation": "static-graph-over-peer-lower-is-better",
        "components": list(PHASES),
        "numerator_cycles": numerator, "denominator_cycles": denominator,
        "point": point, "interval_95": interval,
    }


def _verify_expected_identities(sessions: dict[str, dict[str, Any]],
                                manifest: dict[str, Any]) -> None:
    expected = manifest["identity_policy"]["stable_expected_by_variant"]
    for variant, session in sessions.items():
        identity = session["identity"]
        for field, value in expected[variant].items():
            if identity.get(field) != value:
                raise ControlledRunError(
                    f"EXP-0008 {variant} {field} drifted from freeze")


def build_report(sessions: dict[str, dict[str, Any]],
                 manifest_sha256: str) -> dict[str, Any]:
    if set(sessions) != set(VARIANTS):
        raise ControlledRunError("EXP-0008 matrix is incomplete")
    if any(session["account"] != FULL_ACCOUNT for session in sessions.values()):
        raise ControlledRunError("EXP-0008 session account changed")
    primary = [sessions[name] for name in VARIANTS[:3]]
    for index in range(FULL_ACCOUNT):
        peers = [session["observations"][index] for session in primary]
        for field in ("contract_sha256", "resource_sha256", "input_sha256",
                      "oracle_output_sha256", "observed_output_sha256"):
            if len({peer[field] for peer in peers}) != 1:
                raise ControlledRunError(f"EXP-0008 primary {field} differs")

    prefix_summaries: dict[str, Any] = {}
    graph = sessions["static-graph"]["observations"]
    rocket = sessions["rocket-in-order"]["observations"]
    boom = sessions["boom-ooo"]["observations"]
    for prefix_offset, prefix in enumerate(PREFIXES):
        candidate_rows = {
            variant: {
                "role": "diagnostic-only" if sessions[variant]["diagnostic_only"]
                    else "primary",
                **_candidate_summary(
                    sessions[variant]["observations"], prefix,
                    27007 + prefix_offset * 10 + variant_offset),
            }
            for variant_offset, variant in enumerate(VARIANTS)
        }
        prefix_summaries[str(prefix)] = {
            "fresh_input_versions": list(range(1, prefix + 1)),
            "candidate_rows": candidate_rows,
            "paired_comparisons": {
                "static-graph-vs-rocket-in-order": {
                    "execution_ratio": _paired_execution_ratio(
                        graph, rocket, prefix, 37007 + prefix_offset * 10),
                    "correct_latency_ratio": _correct_latency_ratio(
                        graph, rocket, prefix, 37008 + prefix_offset * 10),
                },
                "static-graph-vs-boom-ooo": {
                    "execution_ratio": _paired_execution_ratio(
                        graph, boom, prefix, 37009 + prefix_offset * 10),
                    "correct_latency_ratio": _correct_latency_ratio(
                        graph, boom, prefix, 37010 + prefix_offset * 10),
                },
            },
            "interval_role": "claim-bearing-latency" if prefix >= 64
                else "descriptive-only",
        }

    cumulative_graph = 0
    cumulative_rocket = 0
    break_even_invocation = None
    for index in range(64):
        cumulative_graph += graph[index]["total_cycles"]
        cumulative_rocket += rocket[index]["total_cycles"]
        if break_even_invocation is None and cumulative_graph <= cumulative_rocket:
            break_even_invocation = index + 1
    latency_64 = prefix_summaries["64"]["paired_comparisons"][
        "static-graph-vs-rocket-in-order"]["correct_latency_ratio"]
    latency_no_go = latency_64["interval_95"]["high"] > 1.05
    break_even_failure = break_even_invocation is None
    early_no_go = latency_no_go or break_even_failure
    session_summaries = {}
    for variant, session in sessions.items():
        observations = session["observations"]
        session_summaries[variant] = {
            "schema": session["schema"],
            "session_sha256": session["session_sha256"],
            "account": session["account"],
            "simulator_processes": session["simulator_processes"],
            "resets": session["resets"],
            "artifact_reloads": session["artifact_reloads"],
            "installation_count": session["installation_count"],
            "diagnostic_only": session["diagnostic_only"],
            "identity": session["identity"],
            "input_output_sequence_sha256": hashlib.sha256(_canonical_bytes([
                {
                    "invocation": item["invocation"],
                    "input_sha256": item["input_sha256"],
                    "oracle_output_sha256": item["oracle_output_sha256"],
                    "observed_output_sha256": item["observed_output_sha256"],
                }
                for item in observations
            ])).hexdigest(),
            "accounting_complete": session["accounting_complete"],
        }
    return {
        "schema": REPORT_SCHEMA,
        "experiment_id": "EXP-0008", "stage": "full-nested-prefix-campaign",
        "account": FULL_ACCOUNT, "prefixes": list(PREFIXES),
        "manifest_sha256": manifest_sha256,
        "matrix_complete": True, "semantic_valid": True,
        "resource_equality_verified": True, "staging_initiator_equal": True,
        "execution_window_meaning_equal": True,
        "single_process_reset_installation_verified": True,
        "prefix_relationship_verified": True,
        "session_summaries": session_summaries,
        "prefix_summaries": prefix_summaries,
        "traffic_finding": (
            "Graph fixed schedule exposes 1536 execution transactions per input; "
            "Rocket and BOOM lawfully reuse loads and expose 1056"
        ),
        "secondary_ablation": "not-activated",
        "rfc0005_latency_decision": {
            "evaluated_at_prefix": 64,
            "threshold_upper_95": 1.05,
            "observed_upper_95": latency_64["interval_95"]["high"],
            "latency_no_go_triggered": latency_no_go,
            "configuration_break_even_invocation": break_even_invocation,
            "configuration_break_even_failure_by_64": break_even_failure,
        },
        "claim_eligibility": {
            "execution_latency_traffic": True,
            "end_to_end_reuse_amortization": True,
            "rfc0005_latency_no_go_evaluated": True,
            "rfc0005_numerical_no_go": early_no_go,
            "rfc0005_go": False,
            "energy": False, "synthesis_timing": False, "area": False,
        },
        "decision": "early-no-go" if early_no_go
            else "advance-partial-latency-traffic",
        "evidence_class": "rtl-simulation-latency-traffic-campaign",
        "limitations": [
            "simulator wall clock is operations-only",
            "Graph toolchain identity is recipe/version rather than complete byte identity",
            "no energy, synthesis timing, or area",
            "no VLIW/CGRA, elastic, stream, or hybrid candidates",
            "finite deterministic seed schedule is not an unbounded workload population",
        ],
    }


def derive(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    derived_dir = run_dir / "derived"
    derived_dir.mkdir(exist_ok=False)
    sessions = {
        variant: parse_variant_log(
            run_dir / "raw" / f"{variant}.log", variant, FULL_ACCOUNT)
        for variant in VARIANTS
    }
    _verify_expected_identities(sessions, manifest)
    report = build_report(sessions, _sha256(manifest_path))
    (derived_dir / "report.json").write_bytes(_canonical_bytes(report) + b"\n")
    return report


def _tail_has_prefix(path: Path, prefix: str) -> bool:
    if not path.exists():
        return False
    with path.open("rb") as source:
        size = source.seek(0, 2)
        source.seek(max(0, size - 131072))
        tail = source.read().decode("utf-8", errors="replace")
    return any(line.startswith(prefix) for line in tail.splitlines())


def _marker_counts(path: Path, prefixes: dict[str, int]) -> dict[str, int]:
    observed = {prefix: 0 for prefix in prefixes}
    with path.open("r", encoding="utf-8") as source:
        for line in source:
            for prefix in prefixes:
                if line.startswith(prefix):
                    observed[prefix] += 1
    return observed


def _append_command_record(command_file: Path, command: list[str],
                           env: dict[str, str], start: int, end: int,
                           returncode: int, log_path: Path) -> None:
    record = {
        "argv": command,
        "environment": {
            key: env[key] for key in sorted(env)
            if key.startswith("RAVEIL_")
            and key not in {"RAVEIL_CHIPYARD_SOURCE", "RAVEIL_ROCKET_CHIP_SOURCE"}
        },
        "start_unix_ns": start, "end_unix_ns": end,
        "simulator_wall_clock_ns_operations_only": end - start,
        "exit_code": returncode, "log": log_path.name,
        "log_bytes": log_path.stat().st_size,
        "log_sha256": _sha256(log_path),
    }
    with command_file.open("ab") as target:
        target.write(_canonical_bytes(record) + b"\n")


def _run_campaign_command(command: list[str], env: dict[str, str],
                          log_path: Path, command_file: Path,
                          required: dict[str, int], terminal_prefix: str,
                          manifest: dict[str, Any]) -> None:
    start = time.time_ns()
    with log_path.open("wb") as output:
        result = subprocess.run(command, env=env, stdout=output,
                                stderr=subprocess.STDOUT)
    end = time.time_ns()
    if result.returncode != 0:
        _append_command_record(
            command_file, command, env, start, end, result.returncode, log_path)
        raise ControlledRunError(f"campaign command failed with {result.returncode}")
    deadline = time.monotonic() + manifest["operations"][
        "terminal_marker_drain_timeout_seconds"]
    while not _tail_has_prefix(log_path, terminal_prefix):
        if time.monotonic() >= deadline:
            _append_command_record(
                command_file, command, env, start, end, result.returncode, log_path)
            raise ControlledRunError("campaign terminal marker did not drain")
        time.sleep(0.25)
    limit = manifest["operations"]["maximum_raw_log_bytes_per_candidate"]
    if log_path.stat().st_size > limit:
        _append_command_record(
            command_file, command, env, start, end, result.returncode, log_path)
        raise ControlledRunError("campaign raw log exceeded frozen limit")
    observed = _marker_counts(log_path, required)
    _append_command_record(
        command_file, command, env, start, end, result.returncode, log_path)
    if observed != required:
        raise ControlledRunError(
            f"campaign marker counts changed: observed={observed}, expected={required}")


def _seal_failed_raw(run_dir: Path, error: str) -> None:
    raw = run_dir / "raw"
    failure = {"schema": "raveil.research-failure/v1", "error": error}
    (raw / "failure.json").write_bytes(_canonical_bytes(failure) + b"\n")
    files = sorted(path for path in raw.iterdir() if path.is_file())
    seal = {
        "schema": "raveil.research-failed-raw-seal/v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size,
             "sha256": _sha256(path)} for path in files
        ],
    }
    (run_dir / "failed-raw-seal.json").write_bytes(
        _canonical_bytes(seal) + b"\n")


def collect(repo: Path, run_dir: Path, manifest_path: Path,
            chipyard: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if run_dir.exists():
        raise ControlledRunError("RUN-ID directory already exists")
    if run_dir.name != manifest["sampling"]["run_id"]:
        raise ControlledRunError("run directory does not match frozen RUN-ID")
    if subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo, text=True,
    ):
        raise ControlledRunError("collection requires a clean worktree")
    if shutil.disk_usage(repo).free < manifest["operations"][
            "minimum_free_bytes_before_collection"]:
        raise ControlledRunError("insufficient free space for EXP-0008")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    implementation_commit = manifest["authority"]["implementation_commit"]
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", implementation_commit, commit],
        cwd=repo,
    ).returncode:
        raise ControlledRunError("campaign implementation is not an ancestor")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{implementation_commit}..{commit}"],
        cwd=repo, text=True,
    ).splitlines()
    allowed = {
        "benchmarks/manifests/t0044-fixture-campaign-v1.json",
        "docs/STATUS.md", "TODO.md", "docs/ROADMAP.md",
        "docs/OPEN_QUESTIONS.md", "docs/experiments/README.md",
        "docs/experiments/EXP-0008-static-full-campaign.md",
        "docs/log/2026-08-14.md",
    }
    if not set(changed).issubset(allowed):
        raise ControlledRunError("source/config changed after EXP-0008 freeze authority")

    raw = run_dir / "raw"
    raw.mkdir(parents=True)
    (raw / "frozen-manifest.json").write_bytes(manifest_path.read_bytes())
    metadata = {
        "schema": "raveil.t0044-fixture-campaign-run-metadata/v1",
        "experiment_id": "EXP-0008", "stage": "full-nested-prefix-campaign",
        "account": FULL_ACCOUNT, "prefixes": list(PREFIXES),
        "git_commit": commit, "manifest_sha256": _sha256(manifest_path),
        "platform": subprocess.check_output(["uname", "-s"], text=True).strip(),
        "architecture": subprocess.check_output(["uname", "-m"], text=True).strip(),
        "chipyard_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=chipyard, text=True).strip(),
        "rocket_chip_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=chipyard.parent / "rocket-chip",
            text=True).strip(),
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
    env["RAVEIL_ROCKET_CHIP_SOURCE"] = str(chipyard.parent / "rocket-chip")
    env["RAVEIL_REPEAT_ACCOUNT"] = str(FULL_ACCOUNT)
    command_file = raw / "commands.jsonl"
    try:
        for variant in VARIANTS:
            required = {
                "RAVEIL-CONTROLLED-OUTPUT-V1": 256 * FULL_ACCOUNT,
                "RAVEIL-FIXTURE-INPUT-V1": 324 * FULL_ACCOUNT,
                "RAVEIL-FIXTURE-PHASE-V1": 2 * FULL_ACCOUNT,
                "RAVEIL-FIXTURE-REARM-V1": FULL_ACCOUNT,
                "RAVEIL-FIXTURE-STAGING-V1": FULL_ACCOUNT,
                "RAVEIL-FIXTURE-RESOURCE-V1": FULL_ACCOUNT,
            }
            variant_env = dict(env)
            if variant == "static-graph":
                variant_env.pop("RAVEIL_REPEAT_ACCOUNT")
                variant_env["RAVEIL_FIXTURE_REPEAT_ACCOUNT"] = str(FULL_ACCOUNT)
                required.update({
                    "RAVEIL-FIXTURE-GRAPH-COMPLETE-V1": FULL_ACCOUNT,
                    "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1": 1,
                })
                terminal = "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1"
            else:
                required.update({
                    "RAVEIL-REPEATED-CPU-COMPLETE-V1": FULL_ACCOUNT,
                    "RAVEIL-FIXTURE-CPU-HOST-V1": 1,
                })
                terminal = "RAVEIL-FIXTURE-CPU-HOST-V1"
            _run_campaign_command(
                [str(scripts[variant])], variant_env,
                raw / f"{variant}.log", command_file,
                required, terminal, manifest,
            )
        report = derive(run_dir, manifest_path)
        seal_raw(run_dir)
        return report
    except (ControlledRunError, OSError, ValueError, KeyError) as error:
        if raw.is_dir() and not (run_dir / "raw-seal.json").exists():
            _seal_failed_raw(run_dir, str(error))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run EXP-0008 fixture campaign")
    commands = parser.add_subparsers(dest="command", required=True)
    collect_parser = commands.add_parser("collect")
    collect_parser.add_argument("--repo", type=Path, required=True)
    collect_parser.add_argument("--run-dir", type=Path, required=True)
    collect_parser.add_argument("--manifest", type=Path, required=True)
    collect_parser.add_argument("--chipyard-source", type=Path, required=True)
    derive_parser = commands.add_parser("derive")
    derive_parser.add_argument("--run-dir", type=Path, required=True)
    derive_parser.add_argument("--manifest", type=Path, required=True)
    seal_parser = commands.add_parser("seal")
    seal_parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            result = collect(
                args.repo.resolve(), args.run_dir.resolve(),
                args.manifest.resolve(), args.chipyard_source.resolve())
        elif args.command == "derive":
            result = derive(args.run_dir.resolve(), args.manifest.resolve())
        else:
            result = seal_raw(args.run_dir.resolve())
    except (ControlledRunError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
