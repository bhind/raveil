"""Strict common observation boundary for the bounded CPU/Graph simulation.

The adapter normalizes semantics and accounting fields without pretending that
different implementations share an RTL type.  Functional records with missing
lifecycle phases are valid evidence, but they are never measurement-ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any

from .static_region import configuration_id


SCHEMA = "raveil.simulation-adapter/v2"
ADAPTER_IDENTITY = "raveil.bounded-region-simulation-adapter/v2"
EVIDENCE_CLASS = "rtl-simulation-functional"
IMPLEMENTATIONS = {
    "static-graph",
    "rocket-in-order",
    "boom-ooo",
    "boom-ooo-disabled-diagnostic",
}
ACCOUNTING_PHASES = (
    "installation_cycles",
    "staging_cycles",
    "execution_cycles",
    "completion_cycles",
    "validation_cycles",
    "publication_cycles",
)
MEMORY_MODELS = {
    "owned-private-scratchpads",
    "cache-backed-variable-latency",
    "shared-tilelink-banked-scratchpad-unverified-latency",
    "matched-fixed-latency-banked-scratchpad",
}


class SimulationAdapterError(ValueError):
    """A contract or observation is outside the common adapter boundary."""


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def compile_simulation_adapter_contract() -> dict[str, Any]:
    """Return the implementation-neutral RFC-0005 functional boundary."""

    return {
        "schema": SCHEMA,
        "adapter_identity": ADAPTER_IDENTITY,
        "descriptor_sha256": configuration_id(),
        "workload": {
            "name": "five-point-stencil-u32",
            "input_words": 324,
            "output_words": 256,
            "word_bits": 32,
            "arithmetic": "uint32-modulo-2^32",
            "useful_operations": {
                "loads": 1280,
                "adds": 1024,
                "stores": 256,
            },
        },
        "memory": {
            "required_comparison_model": "matched-fixed-latency-banked-scratchpad",
            "input_binding": "read-only",
            "output_binding": "exclusive-private-output",
            "input_read_ports": 1,
            "output_write_ports": 1,
            "output_publication": "after-independent-validation",
        },
        "lifecycle": [
            "installation",
            "staging",
            "execution",
            "completion",
            "validation",
            "publication-or-invalidation",
        ],
        "accounting_phases": list(ACCOUNTING_PHASES),
        "implementations": sorted(IMPLEMENTATIONS),
        "evidence_class": EVIDENCE_CLASS,
        "performance_claim": False,
    }


def validate_simulation_adapter_contract(contract: dict[str, Any]) -> None:
    """Reject any drift from the accepted common functional boundary."""

    expected = compile_simulation_adapter_contract()
    if contract != expected:
        raise SimulationAdapterError("simulation adapter contract changed")


def simulation_adapter_contract_id() -> str:
    contract = compile_simulation_adapter_contract()
    validate_simulation_adapter_contract(contract)
    return hashlib.sha256(_canonical_bytes(contract)).hexdigest()


def validate_simulation_observation(observation: dict[str, Any]) -> None:
    """Validate one functional result without upgrading it to measurement."""

    expected_fields = {
        "schema",
        "adapter_contract_sha256",
        "descriptor_sha256",
        "implementation",
        "invocation",
        "status",
        "semantic_valid",
        "output_private",
        "output_published",
        "input_words_staged",
        "output_words_validated",
        "useful_loads",
        "useful_adds",
        "useful_stores",
        *ACCOUNTING_PHASES,
        "total_cycles",
        "accounting_complete",
        "missing_accounting",
        "evidence_class",
        "performance_claim",
        "memory_model",
        "resource_match_verified",
        "matched_comparison_ready",
    }
    if set(observation) != expected_fields:
        raise SimulationAdapterError("observation fields changed")
    if observation["schema"] != SCHEMA:
        raise SimulationAdapterError("observation schema changed")
    if observation["adapter_contract_sha256"] != simulation_adapter_contract_id():
        raise SimulationAdapterError("adapter identity mismatch")
    if observation["descriptor_sha256"] != configuration_id():
        raise SimulationAdapterError("descriptor identity mismatch")
    if observation["implementation"] not in IMPLEMENTATIONS:
        raise SimulationAdapterError("unsupported implementation")
    if type(observation["invocation"]) is not int or observation["invocation"] < 1:
        raise SimulationAdapterError("invocation must be a positive integer")
    if observation["evidence_class"] != EVIDENCE_CLASS:
        raise SimulationAdapterError("evidence class changed")
    if observation["performance_claim"] is not False:
        raise SimulationAdapterError("functional adapter cannot make a performance claim")
    if observation["memory_model"] not in MEMORY_MODELS:
        raise SimulationAdapterError("unsupported memory model")
    if type(observation["resource_match_verified"]) is not bool:
        raise SimulationAdapterError("resource_match_verified must be boolean")
    if type(observation["matched_comparison_ready"]) is not bool:
        raise SimulationAdapterError("matched_comparison_ready must be boolean")
    if observation["resource_match_verified"] and observation["memory_model"] != (
        "matched-fixed-latency-banked-scratchpad"
    ):
        raise SimulationAdapterError("resource match requires the RFC-0005 memory model")

    status = observation["status"]
    if status not in {"completed", "cancelled"}:
        raise SimulationAdapterError("unsupported completion status")
    if type(observation["output_private"]) is not bool:
        raise SimulationAdapterError("output_private must be boolean")
    if type(observation["output_published"]) is not bool:
        raise SimulationAdapterError("output_published must be boolean")
    if observation["output_published"]:
        raise SimulationAdapterError("functional adapter may not publish output")

    integer_fields = {
        "input_words_staged",
        "output_words_validated",
        "useful_loads",
        "useful_adds",
        "useful_stores",
    }
    for field in integer_fields:
        value = observation[field]
        if type(value) is not int or value < 0:
            raise SimulationAdapterError(f"{field} must be a non-negative integer")

    if observation["input_words_staged"] != 324:
        raise SimulationAdapterError("input staging is not matched")
    maximum_useful = {"useful_loads": 1280, "useful_adds": 1024, "useful_stores": 256}
    for field, maximum in maximum_useful.items():
        if observation[field] > maximum:
            raise SimulationAdapterError(f"{field} exceeds the workload semantics")

    if status == "completed":
        if observation["semantic_valid"] is not True:
            raise SimulationAdapterError("completed output lacks semantic validation")
        if observation["output_private"] is not True:
            raise SimulationAdapterError("completed output must remain private")
        if observation["output_words_validated"] != 256:
            raise SimulationAdapterError("completed output was not fully validated")
        if any(observation[field] != maximum for field, maximum in maximum_useful.items()):
            raise SimulationAdapterError("completed useful-operation counts changed")
    else:
        if observation["semantic_valid"] is not False:
            raise SimulationAdapterError("cancelled output cannot be semantically approved")
        if observation["output_private"] is not False:
            raise SimulationAdapterError("cancelled output must be invalid")
        if observation["output_words_validated"] != 0:
            raise SimulationAdapterError("cancelled output cannot be validated")

    missing: list[str] = []
    total = 0
    for phase in ACCOUNTING_PHASES:
        value = observation[phase]
        if value is None:
            missing.append(phase)
        elif type(value) is not int or value < 0:
            raise SimulationAdapterError(f"{phase} must be null or a non-negative integer")
        else:
            total += value
    if observation["missing_accounting"] != missing:
        raise SimulationAdapterError("missing accounting list is not canonical")

    complete = not missing
    if observation["accounting_complete"] is not complete:
        raise SimulationAdapterError("accounting completeness is inconsistent")
    if complete:
        if observation["total_cycles"] != total:
            raise SimulationAdapterError("total cycles do not equal lifecycle phases")
    elif observation["total_cycles"] is not None:
        raise SimulationAdapterError("incomplete accounting cannot report total cycles")
    ready = complete and observation["resource_match_verified"]
    if observation["matched_comparison_ready"] is not ready:
        raise SimulationAdapterError("matched comparison readiness is inconsistent")


def static_graph_functional_observation(invocation: int) -> dict[str, Any]:
    """Describe the current RTL smoke without claiming complete accounting."""

    observation = {
        "schema": SCHEMA,
        "adapter_contract_sha256": simulation_adapter_contract_id(),
        "descriptor_sha256": configuration_id(),
        "implementation": "static-graph",
        "invocation": invocation,
        "status": "completed",
        "semantic_valid": True,
        "output_private": True,
        "output_published": False,
        "input_words_staged": 324,
        "output_words_validated": 256,
        "useful_loads": 1280,
        "useful_adds": 1024,
        "useful_stores": 256,
        "installation_cycles": None,
        "staging_cycles": 324,
        "execution_cycles": 1536,
        "completion_cycles": None,
        "validation_cycles": None,
        "publication_cycles": None,
        "total_cycles": None,
        "accounting_complete": False,
        "missing_accounting": [
            "installation_cycles",
            "completion_cycles",
            "validation_cycles",
            "publication_cycles",
        ],
        "evidence_class": EVIDENCE_CLASS,
        "performance_claim": False,
        "memory_model": "owned-private-scratchpads",
        "resource_match_verified": False,
        "matched_comparison_ready": False,
    }
    validate_simulation_observation(observation)
    return observation


def static_graph_cancelled_observation(invocation: int) -> dict[str, Any]:
    """Describe the smoke cancellation after 17 execution cycles."""

    observation = static_graph_functional_observation(invocation)
    observation.update(
        {
            "status": "cancelled",
            "semantic_valid": False,
            "output_private": False,
            "output_words_validated": 0,
            "useful_loads": 15,
            "useful_adds": 12,
            "useful_stores": 2,
            "execution_cycles": 17,
        }
    )
    validate_simulation_observation(observation)
    return observation


def cpu_functional_observation(
    implementation: str,
    invocation: int,
    memory_model: str = "cache-backed-variable-latency",
) -> dict[str, Any]:
    """Describe a CPU semantic smoke without claiming resource matching."""

    if implementation not in {
        "rocket-in-order",
        "boom-ooo",
        "boom-ooo-disabled-diagnostic",
    }:
        raise SimulationAdapterError("unsupported CPU implementation")
    if memory_model not in {
        "cache-backed-variable-latency",
        "shared-tilelink-banked-scratchpad-unverified-latency",
    }:
        raise SimulationAdapterError("unsupported CPU functional memory model")
    observation = static_graph_functional_observation(invocation)
    observation.update(
        {
            "implementation": implementation,
            "memory_model": memory_model,
            "missing_accounting": list(ACCOUNTING_PHASES),
            **{phase: None for phase in ACCOUNTING_PHASES},
        }
    )
    validate_simulation_observation(observation)
    return observation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="emit one validated functional-only simulation observation"
    )
    parser.add_argument("--invocation", type=int, required=True)
    parser.add_argument(
        "--implementation", choices=sorted(IMPLEMENTATIONS), default="static-graph"
    )
    parser.add_argument(
        "--memory-model",
        choices=sorted(MEMORY_MODELS),
        default="cache-backed-variable-latency",
    )
    parser.add_argument(
        "--status", choices=("completed", "cancelled"), required=True
    )
    args = parser.parse_args(argv)
    try:
        if args.implementation != "static-graph" and args.status == "cancelled":
            raise SimulationAdapterError("CPU cancellation observation is not implemented")
        if args.implementation != "static-graph":
            observation = cpu_functional_observation(
                args.implementation, args.invocation, args.memory_model
            )
        elif args.status == "completed":
            observation = static_graph_functional_observation(args.invocation)
        else:
            observation = static_graph_cancelled_observation(args.invocation)
    except SimulationAdapterError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(observation, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
