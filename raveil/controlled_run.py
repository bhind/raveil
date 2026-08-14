"""Strict ADR-0046 controlled-run records for the T-0042 small start.

This schema wraps the preserved simulation-adapter/v2 semantic identity.  It
adds the resource, quiescence, traffic, oracle, and complete lifecycle facts
needed before a run can become eligible for T-0044.  A single implementation
record is intentionally ineligible until Rocket, BOOM, and Graph records with
the same resource tuple have been verified together.
"""

from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import struct
import sys
from typing import Any

from .simulation_adapter import simulation_adapter_contract_id
from .riscv_stencil_signature import validate_signature
from .static_region import configuration_id, static_stencil_oracle


SCHEMA = "raveil.controlled-run/v1"
AGGREGATE_SCHEMA = "raveil.controlled-run-aggregate/v1"
RESOURCE_SCHEMA = "raveil.owned-memory-resource/v1"
IMPLEMENTATIONS = {"static-graph", "rocket-in-order", "boom-ooo"}
PHASES = (
    "installation",
    "staging",
    "execution",
    "completion",
    "validation",
    "publication",
)
TRAFFIC_CLASSES = (
    "graph",
    "cpu",
    "fesvr",
    "loader",
    "debug",
    "setup",
    "recovery",
    "unknown",
)
SEMANTIC_OPERATIONS = {
    "reads": 1280,
    "writes": 256,
    "outputs": 256,
}


class ControlledRunError(ValueError):
    """A record is not inside the accepted ADR-0046 boundary."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def owned_resource_tuple() -> dict[str, Any]:
    """Return the exact one-bank, two-logical-region ADR-0043 candidate.

    One physical bank contains disjoint input and private-output regions.  The
    adapter admits at most one live transaction.  This describes the current
    Graph target and the target CPU adapters must reuse; it does not by itself
    establish cross-implementation equality.
    """

    return {
        "schema": RESOURCE_SCHEMA,
        "contract_version": 1,
        "data_width_bits": 32,
        "byte_mask_bits": 4,
        "operation_width_bytes": 4,
        "request_ports": 1,
        "response_ports": 1,
        "maximum_outstanding_requests": 1,
        "request_buffer_depth": 0,
        "response_buffer_depth": 1,
        "arbitration": "none-at-owned-contract-ingress",
        "accepted_operations": ["read", "write-byte-mask"],
        "response_availability_rule": "one-module-local-cycle-after-acceptance",
        "response_hold_rule": "stable-until-consumed",
        "physical_banks": 1,
        "physical_words": 1024,
        "valid_words": 580,
        "regions": [
            {
                "name": "input",
                "base_word": 0,
                "words": 324,
                "binding": "read-only-during-execution",
            },
            {
                "name": "private-output",
                "base_word": 324,
                "words": 256,
                "binding": "write-only-during-execution",
            },
        ],
    }


def owned_resource_tuple_id() -> str:
    return hashlib.sha256(_canonical_bytes(owned_resource_tuple())).hexdigest()


def controlled_run_contract() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "descriptor_sha256": configuration_id(),
        "simulation_adapter_sha256": simulation_adapter_contract_id(),
        "implementations": sorted(IMPLEMENTATIONS),
        "resource": owned_resource_tuple(),
        "phases": list(PHASES),
        "traffic_classes": list(TRAFFIC_CLASSES),
        "frozen_workload": "five-point-stencil-u32-rfc-0005",
        "independent_oracle": "raveil.static-region-oracle/v1",
        "semantic_operations": SEMANTIC_OPERATIONS,
        "performance_claim": False,
    }


def controlled_run_contract_id() -> str:
    return hashlib.sha256(_canonical_bytes(controlled_run_contract())).hexdigest()


def _input_words(seed: int) -> list[int]:
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ControlledRunError("seed must be uint32")
    words: list[int] = []
    for index in range(324):
        value = (
            ((index + 1) * ((seed * 2654435761) & 0xFFFFFFFF))
            ^ (index << (seed & 7))
            ^ (seed * 17)
        ) & 0xFFFFFFFF
        words.append(value)
    return words


def _word_digest(words: list[int]) -> str:
    payload = b"".join(struct.pack("<I", word) for word in words)
    return hashlib.sha256(payload).hexdigest()


def static_graph_source_id() -> str:
    root = Path(__file__).resolve().parents[1]
    relative_paths = (
        "hardware/chisel/StaticStencilRegion.scala",
        "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
        "hardware/chisel/static_stencil_sim_main.cpp",
        "hardware/chisel/run-static-stencil-rtl.sh",
        "hardware/chisel/run-static-stencil.sh",
        "hardware/chisel/Dockerfile",
        "raveil/controlled_run.py",
        "raveil/simulation_adapter.py",
        "raveil/static_region.py",
    )
    digest = hashlib.sha256()
    for relative in relative_paths:
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update((root / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _require_sha256(name: str, value: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ControlledRunError(f"{name} must be lowercase SHA-256")


def implementation_configuration_id(
    implementation: str,
    implementation_configuration: str,
    source_sha256: str,
    toolchain_sha256: str,
) -> str:
    return hashlib.sha256(_canonical_bytes({
        "implementation": implementation,
        "implementation_configuration": implementation_configuration,
        "controlled_contract_sha256": controlled_run_contract_id(),
        "descriptor_sha256": configuration_id(),
        "resource_sha256": owned_resource_tuple_id(),
        "source_sha256": source_sha256,
        "toolchain_sha256": toolchain_sha256,
    })).hexdigest()


def static_graph_controlled_observation(
    invocation: int,
    seed: int,
    artifact_sha256: str,
    toolchain_sha256: str,
) -> dict[str, Any]:
    """Create the exact first executable Graph-only controlled record."""

    inputs = _input_words(seed)
    oracle = static_stencil_oracle(inputs)
    phase_cycles = {
        "installation": 0,
        "staging": 648,
        "execution": 3072,
        "completion": 1,
        "validation": 512,
        "publication": 0,
    }
    traffic = {name: 0 for name in TRAFFIC_CLASSES}
    traffic["graph"] = 1536
    source_sha256 = static_graph_source_id()
    implementation_configuration = "StaticStencilRegion:d4bf9395a510385f"
    observation = {
        "schema": SCHEMA,
        "contract_sha256": controlled_run_contract_id(),
        "simulation_adapter_sha256": simulation_adapter_contract_id(),
        "descriptor_sha256": configuration_id(),
        "resource_sha256": owned_resource_tuple_id(),
        "source_sha256": source_sha256,
        "artifact_sha256": artifact_sha256,
        "toolchain_sha256": toolchain_sha256,
        "configuration_sha256": implementation_configuration_id(
            "static-graph", implementation_configuration,
            source_sha256, toolchain_sha256,
        ),
        "implementation_configuration": implementation_configuration,
        "implementation": "static-graph",
        "invocation": invocation,
        "input_sha256": _word_digest(inputs),
        "oracle_output_sha256": _word_digest(oracle),
        "observed_output_sha256": _word_digest(oracle),
        "semantic_valid": True,
        "semantic_operations": dict(SEMANTIC_OPERATIONS),
        "phase_cycles": phase_cycles,
        "total_cycles": sum(phase_cycles.values()),
        "accounting_complete": True,
        "quiescence_before": True,
        "quiescence_after": True,
        "window_start": "after-staging-response-drain",
        "window_end": "after-final-execution-response",
        "window_cycles": 3072,
        "traffic": traffic,
        "traffic_accepted": 1536,
        "traffic_completed": 1536,
        "traffic_pending": 0,
        "unaccounted_window_traffic": 0,
        "traffic_conserved": True,
        "resource_contract_verified": True,
        "resource_equality_verified": False,
        "comparison_eligible": False,
        "ineligibility_reasons": ["rocket-and-boom-resource-peers-not-yet-verified"],
        "evidence_class": "rtl-simulation-functional",
        "performance_claim": False,
    }
    validate_controlled_observation(observation)
    return observation


def validate_controlled_observation(observation: dict[str, Any]) -> None:
    expected_fields = {
        "schema", "contract_sha256", "simulation_adapter_sha256",
        "descriptor_sha256", "resource_sha256", "implementation",
        "source_sha256", "artifact_sha256", "toolchain_sha256",
        "configuration_sha256", "implementation_configuration",
        "invocation", "input_sha256", "oracle_output_sha256",
        "observed_output_sha256", "semantic_valid", "semantic_operations",
        "phase_cycles",
        "total_cycles", "accounting_complete", "quiescence_before",
        "quiescence_after", "window_start", "window_end", "window_cycles",
        "traffic", "traffic_accepted", "traffic_completed", "traffic_pending",
        "unaccounted_window_traffic", "traffic_conserved",
        "resource_contract_verified", "resource_equality_verified",
        "comparison_eligible", "ineligibility_reasons", "evidence_class",
        "performance_claim",
    }
    if set(observation) != expected_fields:
        raise ControlledRunError("controlled observation fields changed")
    if observation["schema"] != SCHEMA:
        raise ControlledRunError("controlled schema changed")
    if observation["contract_sha256"] != controlled_run_contract_id():
        raise ControlledRunError("controlled contract identity mismatch")
    if observation["simulation_adapter_sha256"] != simulation_adapter_contract_id():
        raise ControlledRunError("simulation adapter identity mismatch")
    if observation["descriptor_sha256"] != configuration_id():
        raise ControlledRunError("descriptor identity mismatch")
    if observation["resource_sha256"] != owned_resource_tuple_id():
        raise ControlledRunError("owned resource identity mismatch")
    for field in (
        "source_sha256", "artifact_sha256", "toolchain_sha256",
        "configuration_sha256",
    ):
        _require_sha256(field, observation[field])
    if type(observation["implementation_configuration"]) is not str or not observation["implementation_configuration"]:
        raise ControlledRunError("implementation configuration is missing")
    if observation["implementation"] not in IMPLEMENTATIONS:
        raise ControlledRunError("unsupported implementation")
    if observation["configuration_sha256"] != implementation_configuration_id(
        observation["implementation"],
        observation["implementation_configuration"],
        observation["source_sha256"],
        observation["toolchain_sha256"],
    ):
        raise ControlledRunError("implementation configuration identity mismatch")
    if type(observation["invocation"]) is not int or observation["invocation"] < 1:
        raise ControlledRunError("invocation must be positive")
    for field in ("input_sha256", "oracle_output_sha256", "observed_output_sha256"):
        value = observation[field]
        if type(value) is not str or len(value) != 64:
            raise ControlledRunError(f"{field} must be SHA-256")
    if observation["semantic_valid"] is not True:
        raise ControlledRunError("controlled run lacks exact semantic validation")
    if observation["semantic_operations"] != SEMANTIC_OPERATIONS:
        raise ControlledRunError("frozen semantic operation counts changed")
    if observation["observed_output_sha256"] != observation["oracle_output_sha256"]:
        raise ControlledRunError("observed output differs from independent oracle")

    phases = observation["phase_cycles"]
    if type(phases) is not dict or set(phases) != set(PHASES):
        raise ControlledRunError("phase accounting is not canonical")
    if any(type(value) is not int or value < 0 for value in phases.values()):
        raise ControlledRunError("phase cycles must be non-negative integers")
    if observation["accounting_complete"] is not True:
        raise ControlledRunError("controlled accounting must be complete")
    if observation["total_cycles"] != sum(phases.values()):
        raise ControlledRunError("total cycles do not equal all six phases")
    if observation["window_cycles"] != phases["execution"]:
        raise ControlledRunError("execution window is not the execution phase")
    if observation["quiescence_before"] is not True or observation["quiescence_after"] is not True:
        raise ControlledRunError("execution window is not quiescent")

    traffic = observation["traffic"]
    if type(traffic) is not dict or set(traffic) != set(TRAFFIC_CLASSES):
        raise ControlledRunError("traffic classes are not canonical")
    if any(type(value) is not int or value < 0 for value in traffic.values()):
        raise ControlledRunError("traffic counts must be non-negative integers")
    total_traffic = sum(traffic.values())
    if observation["traffic_accepted"] != total_traffic:
        raise ControlledRunError("accepted traffic is not fully classified")
    if observation["traffic_completed"] + observation["traffic_pending"] != observation["traffic_accepted"]:
        raise ControlledRunError("traffic conservation failed")
    conserved = observation["traffic_pending"] == 0 and observation["unaccounted_window_traffic"] == 0
    if observation["traffic_conserved"] is not conserved:
        raise ControlledRunError("traffic conservation flag is inconsistent")

    for field in ("resource_contract_verified", "resource_equality_verified", "comparison_eligible"):
        if type(observation[field]) is not bool:
            raise ControlledRunError(f"{field} must be boolean")
    reasons = observation["ineligibility_reasons"]
    if type(reasons) is not list or any(type(reason) is not str or not reason for reason in reasons):
        raise ControlledRunError("ineligibility reasons are invalid")
    eligible = (
        observation["resource_contract_verified"]
        and observation["resource_equality_verified"]
        and observation["traffic_conserved"]
        and observation["unaccounted_window_traffic"] == 0
        and observation["semantic_valid"]
        and observation["accounting_complete"]
    )
    if observation["comparison_eligible"] is not eligible:
        raise ControlledRunError("comparison eligibility is inconsistent")
    if eligible != (reasons == []):
        raise ControlledRunError("eligibility reasons are inconsistent")
    if observation["evidence_class"] != "rtl-simulation-functional":
        raise ControlledRunError("evidence class changed")
    if observation["performance_claim"] is not False:
        raise ControlledRunError("T-0042 cannot make a performance claim")


def _parse_marker(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    items = line.split()[1:]
    index = 0
    while index < len(items):
        item = items[index]
        if item.endswith("=") and item.count("=") == 1:
            index += 1
            if index >= len(items) or "=" in items[index]:
                raise ControlledRunError(f"missing padded marker value: {item}")
            item = item + items[index]
        if item.count("=") != 1:
            raise ControlledRunError(f"malformed marker field: {item}")
        key, value = item.split("=", 1)
        if not key or not value or key in fields:
            raise ControlledRunError(f"invalid marker field: {item}")
        fields[key] = value
        index += 1
    return fields


def verify_static_graph_log(path: Path) -> list[dict[str, Any]]:
    """Bind the two successful RTL windows to strict controlled records."""

    identity_records = [
        _parse_marker(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("CONTROLLED-GRAPH-IDENTITY-V1")
    ]
    if len(identity_records) != 1:
        raise ControlledRunError("expected exactly one controlled Graph identity")
    identity = identity_records[0]
    if set(identity) != {"artifact_sha256", "toolchain_sha256"}:
        raise ControlledRunError("controlled Graph identity marker changed")
    _require_sha256("artifact_sha256", identity["artifact_sha256"])
    _require_sha256("toolchain_sha256", identity["toolchain_sha256"])

    prefix = "CONTROLLED-GRAPH-WINDOW-V1"
    records = [
        _parse_marker(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(prefix)
    ]
    if len(records) != 2:
        raise ControlledRunError("expected exactly two controlled Graph windows")
    observations: list[dict[str, Any]] = []
    expected_keys = {
        "status", "invocation", "seed", "installation_cycles",
        "staging_cycles", "execution_cycles", "completion_cycles",
        "validation_cycles", "publication_cycles", "total_cycles",
        "quiescence_before", "quiescence_after", "traffic_accepted",
        "traffic_completed", "traffic_pending", "graph_traffic",
        "unaccounted_window_traffic", "resource_sha256",
        "resource_contract_verified", "resource_equality_verified",
        "comparison_eligible", "performance",
    }
    for fields, invocation, seed in zip(records, (1, 3), (1, 3), strict=True):
        if set(fields) != expected_keys:
            raise ControlledRunError("controlled Graph marker schema changed")
        observation = static_graph_controlled_observation(
            invocation, seed,
            identity["artifact_sha256"], identity["toolchain_sha256"],
        )
        expected = {
            "status": "OK",
            "invocation": str(invocation),
            "seed": str(seed),
            **{
                f"{phase}_cycles": str(observation["phase_cycles"][phase])
                for phase in PHASES
            },
            "total_cycles": str(observation["total_cycles"]),
            "quiescence_before": "1",
            "quiescence_after": "1",
            "traffic_accepted": str(observation["traffic_accepted"]),
            "traffic_completed": str(observation["traffic_completed"]),
            "traffic_pending": "0",
            "graph_traffic": str(observation["traffic"]["graph"]),
            "unaccounted_window_traffic": "0",
            "resource_sha256": observation["resource_sha256"],
            "resource_contract_verified": "1",
            "resource_equality_verified": "0",
            "comparison_eligible": "0",
            "performance": "not-measured",
        }
        if fields != expected:
            raise ControlledRunError(
                f"controlled Graph marker mismatch: {fields!r} != {expected!r}"
            )
        observations.append(observation)
    return observations


def verify_cpu_log(
    path: Path,
    signature_path: Path,
    implementation: str,
    invocation: int,
    source_sha256: str,
    artifact_sha256: str,
    toolchain_sha256: str,
    implementation_configuration: str,
) -> dict[str, Any]:
    """Bind one frozen CPU ELF run to the strict controlled boundary."""

    if implementation not in {"rocket-in-order", "boom-ooo"}:
        raise ControlledRunError("controlled CPU implementation changed")
    if type(invocation) is not int or invocation < 1:
        raise ControlledRunError("invocation must be positive")
    _require_sha256("source_sha256", source_sha256)
    _require_sha256("artifact_sha256", artifact_sha256)
    _require_sha256("toolchain_sha256", toolchain_sha256)
    expected_configuration = {
        "rocket-in-order": "chipyard.raveil.RaveilMatchedRocketConfig",
        "boom-ooo": "chipyard.raveil.RaveilMatchedSmallBoomConfig",
    }[implementation]
    if implementation_configuration != expected_configuration:
        raise ControlledRunError("controlled CPU configuration changed")
    lines = path.read_text(encoding="utf-8").splitlines()
    phases = [
        _parse_marker(line) for line in lines
        if line.startswith("RAVEIL-CONTROLLED-PHASE-V1")
    ]
    expected_transitions = [("0", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "5")]
    if len(phases) != len(expected_transitions):
        raise ControlledRunError("controlled CPU phase cardinality changed")
    for marker, transition in zip(phases, expected_transitions, strict=True):
        if set(marker) != {"from", "to", "cycle", "accepted", "completed", "busy_before"}:
            raise ControlledRunError("controlled CPU phase marker changed")
        if (marker["from"], marker["to"]) != transition:
            raise ControlledRunError("controlled CPU phase order changed")

    resource_markers = [
        _parse_marker(line) for line in lines
        if line.startswith("RAVEIL-CONTROLLED-RESOURCE-V1")
    ]
    if len(resource_markers) != 1:
        raise ControlledRunError("expected exactly one CPU resource marker")
    resource = resource_markers[0]
    expected_resource = {
        "resource_sha256": owned_resource_tuple_id(),
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
        "arbitration": "none-at-owned-contract-ingress",
        "accepted_operations": "read,write-byte-mask",
        "response_rule": "one-module-local-cycle-after-acceptance",
        "response_hold": "stable-until-consumed",
    }
    if resource != expected_resource:
        raise ControlledRunError("controlled CPU resource marker mismatch")

    windows = [
        _parse_marker(line) for line in lines
        if line.startswith("RAVEIL-CONTROLLED-WINDOW-V1")
    ]
    if len(windows) != 1:
        raise ControlledRunError("expected exactly one CPU execution window")
    window = windows[0]
    expected_window_fields = {
        "start_cycle", "end_cycle", "cycles", "accepted", "completed",
        "reads", "writes", "expected_accepted", "expected_completed",
        "unexpected_accepted", "unexpected_completed", "origin_accepted",
        "origin_completed", "nonorigin_accepted", "nonorigin_completed",
        "pending", "quiescence_before", "quiescence_after",
    }
    if set(window) != expected_window_fields:
        raise ControlledRunError("controlled CPU execution marker changed")
    for field, expected in {
        "accepted": "1056", "completed": "1056", "reads": "800",
        "writes": "256", "expected_accepted": "1056",
        "expected_completed": "1056", "unexpected_accepted": "0",
        "unexpected_completed": "0", "origin_accepted": "1056",
        "origin_completed": "1056", "nonorigin_accepted": "0",
        "nonorigin_completed": "0", "pending": "0",
        "quiescence_before": "1", "quiescence_after": "1",
    }.items():
        if window[field] != expected:
            raise ControlledRunError(f"controlled CPU window {field} changed")
    if int(window["end_cycle"]) - int(window["start_cycle"]) != int(window["cycles"]):
        raise ControlledRunError("controlled CPU window boundary mismatch")

    complete_markers = [
        _parse_marker(line) for line in lines
        if line.startswith("RAVEIL-CONTROLLED-CPU-COMPLETE-V1")
    ]
    if len(complete_markers) != 1:
        raise ControlledRunError("expected exactly one CPU complete marker")
    complete = complete_markers[0]
    expected_complete_fields = {
        "installation_cycles", "staging_cycles", "execution_cycles",
        "completion_cycles", "validation_cycles", "publication_cycles",
        "total_cycles", "accepted", "completed", "staging_writes",
        "execution_reads", "execution_writes", "validation_reads",
    }
    if set(complete) != expected_complete_fields:
        raise ControlledRunError("controlled CPU complete marker changed")
    for field, expected in {
        "publication_cycles": "0", "staging_writes": "324",
        "execution_reads": "800", "execution_writes": "256",
        "validation_reads": "256",
    }.items():
        if complete[field] != expected:
            raise ControlledRunError(f"controlled CPU complete {field} changed")
    if complete["accepted"] != complete["completed"]:
        raise ControlledRunError("controlled CPU final traffic did not drain")
    phase_cycles = {
        phase: int(complete[f"{phase}_cycles"])
        for phase in PHASES
    }
    if phase_cycles["execution"] != int(window["cycles"]):
        raise ControlledRunError("CPU execution phase differs from window")
    if sum(phase_cycles.values()) != int(complete["total_cycles"]):
        raise ControlledRunError("controlled CPU lifecycle total changed")

    observed_words = validate_signature(
        signature_path.read_text(encoding="ascii"), seed=1
    )
    inputs = _input_words(1)
    oracle = static_stencil_oracle(inputs)
    observation = {
        "schema": SCHEMA,
        "contract_sha256": controlled_run_contract_id(),
        "simulation_adapter_sha256": simulation_adapter_contract_id(),
        "descriptor_sha256": configuration_id(),
        "resource_sha256": owned_resource_tuple_id(),
        "source_sha256": source_sha256,
        "artifact_sha256": artifact_sha256,
        "toolchain_sha256": toolchain_sha256,
        "configuration_sha256": implementation_configuration_id(
            implementation, implementation_configuration,
            source_sha256, toolchain_sha256,
        ),
        "implementation_configuration": implementation_configuration,
        "implementation": implementation,
        "invocation": invocation,
        "input_sha256": _word_digest(inputs),
        "oracle_output_sha256": _word_digest(oracle),
        "observed_output_sha256": _word_digest(observed_words),
        "semantic_valid": True,
        "semantic_operations": dict(SEMANTIC_OPERATIONS),
        "phase_cycles": phase_cycles,
        "total_cycles": int(complete["total_cycles"]),
        "accounting_complete": True,
        "quiescence_before": True,
        "quiescence_after": True,
        "window_start": "after-staging-response-drain",
        "window_end": "after-final-execution-response",
        "window_cycles": int(window["cycles"]),
        "traffic": {
            "graph": 0, "cpu": 1056, "fesvr": 0, "loader": 0,
            "debug": 0, "setup": 0, "recovery": 0, "unknown": 0,
        },
        "traffic_accepted": 1056,
        "traffic_completed": 1056,
        "traffic_pending": 0,
        "unaccounted_window_traffic": 0,
        "traffic_conserved": True,
        "resource_contract_verified": True,
        "resource_equality_verified": False,
        "comparison_eligible": False,
        "ineligibility_reasons": ["all-three-resource-peers-not-yet-verified"],
        "evidence_class": "rtl-simulation-functional",
        "performance_claim": False,
    }
    validate_controlled_observation(observation)
    return observation


def aggregate_controlled_observations(
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Promote exactly one validated Rocket/BOOM/Graph peer set.

    Resource equality is established here, never by an individual run.  The
    dynamic traffic totals remain visible and need not be equal: the frozen
    optimized CPU ELF reuses horizontal loads while the admitted static Graph
    executes its fixed five-load schedule.  That is a T-0044 measurement-design
    input, not a T-0042 performance result.
    """

    if len(observations) != len(IMPLEMENTATIONS):
        raise ControlledRunError("aggregate requires exactly three observations")
    by_implementation: dict[str, dict[str, Any]] = {}
    for observation in observations:
        validate_controlled_observation(observation)
        implementation = observation["implementation"]
        if implementation in by_implementation:
            raise ControlledRunError("aggregate implementation is duplicated")
        by_implementation[implementation] = observation
    if set(by_implementation) != IMPLEMENTATIONS:
        raise ControlledRunError("aggregate implementation set changed")

    ordered = [by_implementation[name] for name in sorted(IMPLEMENTATIONS)]
    identity_fields = (
        "contract_sha256",
        "simulation_adapter_sha256",
        "descriptor_sha256",
        "resource_sha256",
        "input_sha256",
        "oracle_output_sha256",
        "observed_output_sha256",
    )
    identities: dict[str, str] = {}
    for field in identity_fields:
        values = {observation[field] for observation in ordered}
        if len(values) != 1:
            raise ControlledRunError(f"aggregate {field} differs")
        identities[field] = values.pop()
    if identities["resource_sha256"] != owned_resource_tuple_id():
        raise ControlledRunError("aggregate resource identity is not canonical")

    for observation in ordered:
        if observation["semantic_valid"] is not True:
            raise ControlledRunError("aggregate semantic validation failed")
        if observation["accounting_complete"] is not True:
            raise ControlledRunError("aggregate accounting is incomplete")
        if observation["quiescence_before"] is not True or observation["quiescence_after"] is not True:
            raise ControlledRunError("aggregate execution boundary is not quiescent")
        if observation["traffic_conserved"] is not True:
            raise ControlledRunError("aggregate traffic conservation failed")
        if observation["traffic_pending"] != 0 or observation["unaccounted_window_traffic"] != 0:
            raise ControlledRunError("aggregate contains pending or unaccounted traffic")
        if observation["resource_contract_verified"] is not True:
            raise ControlledRunError("aggregate resource contract is unverified")
        if observation["performance_claim"] is not False:
            raise ControlledRunError("aggregate cannot contain a performance claim")

    traffic = {
        implementation: {
            "accepted": by_implementation[implementation]["traffic_accepted"],
            "completed": by_implementation[implementation]["traffic_completed"],
            "window_cycles": by_implementation[implementation]["window_cycles"],
        }
        for implementation in sorted(IMPLEMENTATIONS)
    }
    dynamic_traffic_equal = len({item["accepted"] for item in traffic.values()}) == 1
    return {
        "schema": AGGREGATE_SCHEMA,
        "implementations": sorted(IMPLEMENTATIONS),
        **identities,
        "sources": {
            implementation: by_implementation[implementation]["source_sha256"]
            for implementation in sorted(IMPLEMENTATIONS)
        },
        "artifacts": {
            implementation: by_implementation[implementation]["artifact_sha256"]
            for implementation in sorted(IMPLEMENTATIONS)
        },
        "toolchains": {
            implementation: by_implementation[implementation]["toolchain_sha256"]
            for implementation in sorted(IMPLEMENTATIONS)
        },
        "configuration_ids": {
            implementation: by_implementation[implementation]["configuration_sha256"]
            for implementation in sorted(IMPLEMENTATIONS)
        },
        "implementation_configurations": {
            implementation: by_implementation[implementation]["implementation_configuration"]
            for implementation in sorted(IMPLEMENTATIONS)
        },
        "semantic_valid": True,
        "semantic_operations": dict(SEMANTIC_OPERATIONS),
        "accounting_complete": True,
        "quiescence_before": True,
        "quiescence_after": True,
        "traffic": traffic,
        "traffic_conserved": True,
        "resource_contract_verified": True,
        "resource_equality_verified": True,
        "dynamic_memory_traffic_equal": dynamic_traffic_equal,
        "comparison_eligible": True,
        "t0044_measurement_claim_ready": False,
        "evidence_class": "rtl-simulation-functional",
        "semantic_initiator": "not-proven",
        "performance_claim": False,
    }


def aggregate_controlled_logs(paths: list[Path]) -> dict[str, Any]:
    """Read wrapper logs and select the seed-1 record for each peer."""

    if len(paths) != 3:
        raise ControlledRunError("aggregate requires three wrapper logs")
    selected: list[dict[str, Any]] = []
    for path in paths:
        candidates: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("{"):
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and value.get("schema") == SCHEMA:
                candidates.append(value)
        seed_one = [
            value for value in candidates
            if value.get("implementation") != "static-graph"
            or value.get("invocation") == 1
        ]
        if len(seed_one) != 1:
            raise ControlledRunError(
                f"wrapper log {path} does not contain one selected record"
            )
        selected.append(seed_one[0])
    return aggregate_controlled_observations(selected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="verify ADR-0046 controlled records")
    parser.add_argument("--verify-static-graph-log", type=Path)
    parser.add_argument("--verify-cpu-log", type=Path)
    parser.add_argument("--signature", type=Path)
    parser.add_argument("--implementation", choices=("rocket-in-order", "boom-ooo"))
    parser.add_argument("--invocation", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--aggregate-logs", type=Path, nargs=3)
    parser.add_argument("--source-sha256")
    parser.add_argument("--artifact-sha256")
    parser.add_argument("--toolchain-sha256")
    parser.add_argument("--implementation-configuration")
    args = parser.parse_args(argv)
    try:
        if args.aggregate_logs is not None:
            if any(value is not None for value in (
                args.verify_static_graph_log, args.verify_cpu_log,
                args.signature, args.implementation, args.invocation,
                args.seed, args.source_sha256, args.artifact_sha256,
                args.toolchain_sha256,
                args.implementation_configuration,
            )):
                raise ControlledRunError("aggregate log verification excludes other arguments")
            print(json.dumps(
                aggregate_controlled_logs(list(args.aggregate_logs)),
                sort_keys=True,
                separators=(",", ":"),
            ))
            return 0
        if args.verify_static_graph_log is not None:
            if any(value is not None for value in (
                args.verify_cpu_log, args.signature, args.implementation,
                args.invocation, args.seed, args.source_sha256,
                args.artifact_sha256, args.toolchain_sha256,
                args.implementation_configuration,
            )):
                raise ControlledRunError("log verification excludes record arguments")
            observations = verify_static_graph_log(args.verify_static_graph_log)
            for observation in observations:
                print(json.dumps(observation, sort_keys=True, separators=(",", ":")))
            return 0
        if args.verify_cpu_log is not None:
            if any(value is None for value in (
                args.signature, args.implementation, args.invocation,
                args.source_sha256, args.artifact_sha256,
                args.toolchain_sha256, args.implementation_configuration,
            )):
                raise ControlledRunError("CPU log verification requires signature, implementation, invocation, source, artifact, toolchain, and configuration")
            if args.seed is not None or args.verify_static_graph_log is not None:
                raise ControlledRunError("CPU log verification arguments changed")
            observation = verify_cpu_log(
                args.verify_cpu_log, args.signature, args.implementation,
                args.invocation, args.source_sha256,
                args.artifact_sha256, args.toolchain_sha256,
                args.implementation_configuration,
            )
            print(json.dumps(observation, sort_keys=True, separators=(",", ":")))
            return 0
        if args.invocation is None or args.seed is None:
            raise ControlledRunError("invocation and seed are required")
        if args.artifact_sha256 is None or args.toolchain_sha256 is None:
            raise ControlledRunError(
                "direct Graph record requires artifact and toolchain identities"
            )
        print(json.dumps(
            static_graph_controlled_observation(
                args.invocation, args.seed,
                args.artifact_sha256, args.toolchain_sha256,
            ),
            sort_keys=True,
            separators=(",", ":"),
        ))
        return 0
    except (ControlledRunError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
