"""Fail-closed structural checks for the EXP-0011 ChipTop RTL exports.

The module deliberately stops before synthesis, timing, area, or any candidate
decision.  Its inputs are Yosys JSON representations of the exported RTL plus
the immutable export metadata and copied source closure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable

from raveil.t0044_physical import tree_sha256


TOP = "ChipTop"
VARIANTS = {
    "integrated-static-graph-rocket":
        "chipyard.raveil.RaveilRuntimeIntegratedGraphRocketConfig",
    "matched-rocket-system":
        "chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig",
}
CLOCK_ROOTS = frozenset({"clock_uncore", "jtag_TCK", "serial_tl_0_clock_in"})
REQUIRED_PORTS = CLOCK_ROOTS | {
    "reset_io",
    "custom_boot",
    "axi4_mem_0_clock",
    "clock_tap",
}
MEMORY_MACRO_CONTRACT = {
    "cc_dir_ext": "name cc_dir_ext depth 1024 width 128 ports mrw mask_gran 16",
    "cc_banks_0_ext": "name cc_banks_0_ext depth 16384 width 64 ports rw",
    "data_arrays_0_ext": "name data_arrays_0_ext depth 512 width 256 ports mrw mask_gran 8",
    "tag_array_ext": "name tag_array_ext depth 64 width 88 ports mrw mask_gran 22",
    "tag_array_0_ext": "name tag_array_0_ext depth 64 width 84 ports mrw mask_gran 21",
    "data_arrays_0_0_ext": "name data_arrays_0_0_ext depth 512 width 128 ports mrw mask_gran 32",
    "memory_ext": "name memory_ext depth 1024 width 32 ports mwrite,read mask_gran 8",
}
MEMORY_MACRO_COUNTS = {
    "cc_banks_0_ext": 4,
    "cc_dir_ext": 1,
    "data_arrays_0_0_ext": 2,
    "data_arrays_0_ext": 1,
    "memory_ext": 1,
    "tag_array_0_ext": 1,
    "tag_array_ext": 1,
}
MEMORY_MACRO_PORTS = {
    "cc_banks_0_ext": {
        "RW0_addr": ("input", 14), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 64), "RW0_rdata": ("output", 64),
    },
    "cc_dir_ext": {
        "RW0_addr": ("input", 10), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 128), "RW0_rdata": ("output", 128),
        "RW0_wmask": ("input", 8),
    },
    "data_arrays_0_ext": {
        "RW0_addr": ("input", 9), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 256), "RW0_rdata": ("output", 256),
        "RW0_wmask": ("input", 32),
    },
    "tag_array_ext": {
        "RW0_addr": ("input", 6), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 88), "RW0_rdata": ("output", 88),
        "RW0_wmask": ("input", 4),
    },
    "tag_array_0_ext": {
        "RW0_addr": ("input", 6), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 84), "RW0_rdata": ("output", 84),
        "RW0_wmask": ("input", 4),
    },
    "data_arrays_0_0_ext": {
        "RW0_addr": ("input", 9), "RW0_en": ("input", 1),
        "RW0_clk": ("input", 1), "RW0_wmode": ("input", 1),
        "RW0_wdata": ("input", 128), "RW0_rdata": ("output", 128),
        "RW0_wmask": ("input", 4),
    },
    "memory_ext": {
        "R0_addr": ("input", 10), "R0_en": ("input", 1),
        "R0_clk": ("input", 1), "R0_data": ("output", 32),
        "W0_addr": ("input", 10), "W0_en": ("input", 1),
        "W0_clk": ("input", 1), "W0_data": ("input", 32),
        "W0_mask": ("input", 4),
    },
}
MEMORY_MACRO_CLOCK_PORTS = {
    name: ({"R0_clk", "W0_clk"} if name == "memory_ext" else {"RW0_clk"})
    for name in MEMORY_MACRO_CONTRACT
}

# S10 is deliberately a document-only gate.  Keeping this validator here (next
# to the S08 structural checks) makes the boundary explicit: it consumes a
# proposed contract, never an export or physical result.
_READINESS_KEYS = frozenset({
    "schema", "experiment_id", "freeze_state", "estimand_overhead",
    "connectivity", "clock_reset", "memory_macro_views", "repetitions",
    "append_only_controls",
})
_REQUIRED_READINESS_KEYS = _READINESS_KEYS - {"experiment_id"}
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_REQUIRED_STOP_RULES = frozenset({
    "oracle_mismatch",
    "resource_inequality",
    "unexplained_traffic",
    "accounting_missing",
    "source_config_drift",
    "incomplete_matrix",
    "execution_window_mismatch",
})
_ALLOWED_PAUSE_RULES = frozenset({
    "fairness_unresolved",
    "measurement_boundary_unresolved",
    "toolchain_unavailable",
})
_REQUIRED_NO_GO_RULES = frozenset({
    "fair_common_conditions_impossible",
    "integrated_hierarchy_not_closed",
    "candidate_only_condition_required",
    "evidence_integrity_failure",
})
_ALLOWED_ADVANCE_RULES = frozenset({"contract_review_passed"})
_RAW_SEAL_STEPS = [
    "write_raw_once",
    "hash_raw_sha256",
    "seal_raw",
    "verify_raw_immutable",
]
_DERIVED_SEAL_STEPS = [
    "read_sealed_raw",
    "write_derived_once",
    "hash_derived_sha256",
    "seal_derived",
    "verify_derived_immutable",
]


def validate_readiness_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Validate the fail-closed, pre-data integrated-physical readiness contract."""
    require(isinstance(document, dict), "readiness contract must be an object")
    require(
        _REQUIRED_READINESS_KEYS <= set(document) <= _READINESS_KEYS,
        "missing or unknown readiness contract field",
    )
    require(document.get("schema") == "raveil.t0044-integrated-physical-readiness/v1", "invalid readiness schema")
    require("experiment_id" not in document or document["experiment_id"] is None, "experiment_id must be absent or null")
    require(document.get("freeze_state") == "unfrozen", "freeze_state must be unfrozen")
    for forbidden in ("results", "measurements", "thresholds", "data", "claims"):
        require(forbidden not in document, f"claim-bearing field prohibited: {forbidden}")

    def obj(name: str) -> dict[str, Any]:
        value = document.get(name)
        require(isinstance(value, dict), f"missing or invalid readiness category: {name}")
        return value

    def fields(value: dict[str, Any], allowed: set[str], name: str) -> None:
        require(set(value) == allowed, f"missing or unknown field in {name}")

    overhead = obj("estimand_overhead")
    fields(overhead, {"estimand", "components", "dynamic_traffic_difference"}, "estimand_overhead")
    require(isinstance(overhead.get("estimand"), str) and overhead["estimand"].strip(), "complete estimand required")
    components = overhead.get("components")
    require(isinstance(components, dict), "overhead components required")
    require(
        set(components) == {"graph_candidate", "rocket_candidate", "common"},
        "missing or unknown overhead component bucket",
    )
    ledger_names: list[str] = []
    for key, value in components.items():
        require(
            isinstance(value, list)
            and value
            and all(isinstance(item, str) and item.strip() for item in value),
            f"overhead ledger component incomplete: {key}",
        )
        ledger_names.extend(value)
    require(
        len(ledger_names) == len(set(ledger_names)),
        "overhead component must have one accounting owner",
    )
    traffic = overhead.get("dynamic_traffic_difference")
    require(isinstance(traffic, dict), "dynamic traffic difference required")
    fields(traffic, {"represented", "asserted_equal"}, "dynamic_traffic_difference")
    require(traffic.get("represented") is True and traffic.get("asserted_equal") is False, "dynamic traffic must be represented and not asserted equal")

    connectivity = obj("connectivity")
    fields(connectivity, {"common_modules", "deltas", "ownership"}, "connectivity")
    for key in ("common_modules", "deltas"):
        require(isinstance(connectivity.get(key), list) and connectivity[key], f"{key} connectivity required")
        names = [x.get("name") if isinstance(x, dict) else None for x in connectivity[key]]
        require(
            all(
                isinstance(item, dict)
                and set(item) == {"name"}
                and isinstance(name, str)
                and name.strip()
                for item, name in zip(connectivity[key], names)
            ),
            f"named {key} components required",
        )
        require(len(names) == len(set(names)), f"duplicate {key} component")
    ownership = connectivity.get("ownership")
    require(isinstance(ownership, dict), "component ownership required")
    all_names = [x["name"] for key in ("common_modules", "deltas") for x in connectivity[key]]
    require(len(all_names) == len(set(all_names)), "duplicate connectivity component")
    require(
        set(ownership) == set(all_names)
        and all(v in {"common", "graph", "rocket"} for v in ownership.values()),
        "component ownership is missing or invalid",
    )
    common_names = {item["name"] for item in connectivity["common_modules"]}
    require(
        all(ownership[name] == "common" for name in common_names),
        "common component ownership is invalid",
    )

    clock = obj("clock_reset")
    fields(clock, {"clock_endpoints", "period", "waveform", "reset"}, "clock_reset")
    require(isinstance(clock.get("clock_endpoints"), list) and clock["clock_endpoints"] and all(isinstance(x, str) and x.strip() for x in clock["clock_endpoints"]) and len(set(clock["clock_endpoints"])) == len(clock["clock_endpoints"]), "normalized clock endpoints required")
    require(
        isinstance(clock.get("period"), (int, float))
        and not isinstance(clock["period"], bool)
        and math.isfinite(clock["period"])
        and clock["period"] > 0,
        "normalized clock period required",
    )
    waveform = clock.get("waveform")
    require(
        isinstance(waveform, dict)
        and set(waveform) == {"rising_edge", "duty_cycle"}
        and all(
            isinstance(waveform[key], (int, float))
            and not isinstance(waveform[key], bool)
            and math.isfinite(waveform[key])
            for key in waveform
        )
        and 0 <= waveform["rising_edge"] < clock["period"]
        and 0 < waveform["duty_cycle"] < 1,
        "normalized waveform required",
    )
    reset = clock.get("reset")
    require(
        isinstance(reset, dict)
        and set(reset) == {"polarity", "synchrony", "coverage"}
        and reset["polarity"] in {"active_high", "active_low"}
        and reset["synchrony"] in {"synchronous", "asynchronous"}
        and reset["coverage"] == "all_sequential_state",
        "reset polarity, synchrony, and coverage required",
    )

    views = obj("memory_macro_views")
    fields(views, {"macros"}, "memory_macro_views")
    require(isinstance(views["macros"], list) and views["macros"], "memory macro views required")
    required_view = {"name", "liberty_sha256", "lef_sha256", "pvt", "rc_corner"}
    names = set()
    for view in views["macros"]:
        require(isinstance(view, dict) and required_view <= set(view), "incomplete memory macro view")
        fields(view, required_view, "memory macro view")
        require(
            all(
                isinstance(view[k], str)
                and view[k].strip()
                and view[k].lower() not in {"tbd", "todo", "placeholder", "unknown"}
                for k in required_view
            )
            and _HEX_SHA256.fullmatch(view["liberty_sha256"]) is not None
            and _HEX_SHA256.fullmatch(view["lef_sha256"]) is not None,
            "missing or placeholder memory macro identity",
        )
        require(view["name"] not in names, "duplicate memory macro view")
        names.add(view["name"])
    require(
        names == set(MEMORY_MACRO_CONTRACT),
        "memory macro view set does not cover the integrated hierarchy",
    )

    reps = obj("repetitions")
    fields(reps, {"count", "seeds", "inference_unit", "uncertainty_policy", "interval_95_policy", "campaign_policy"}, "repetitions")
    require(isinstance(reps.get("count"), int) and reps["count"] > 0 and isinstance(reps.get("seeds"), list) and len(reps["seeds"]) == reps["count"] and len(set(reps["seeds"])) == reps["count"] and all(isinstance(x, int) and not isinstance(x, bool) for x in reps["seeds"]), "repetitions and seeds required")
    require(isinstance(reps.get("inference_unit"), str) and reps["inference_unit"].strip(), "inference unit required")
    require(isinstance(reps.get("uncertainty_policy"), str) and reps["uncertainty_policy"].strip() and isinstance(reps.get("interval_95_policy"), str) and reps["interval_95_policy"].strip(), "uncertainty and 95% interval policy required")
    require(isinstance(reps.get("campaign_policy"), str) and reps["campaign_policy"].strip() and reps["campaign_policy"] != "EXP-0008", "explicit non-EXP-0008 campaign policy required")

    controls = obj("append_only_controls")
    fields(controls, {"raw_derived_separation", "hashes", "append_before_seal", "immutable_after_seal", "raw_seal_steps", "derived_seal_steps", "stop", "pause", "no_go", "advance"}, "append_only_controls")
    require(
        controls.get("raw_derived_separation") is True
        and controls.get("hashes") == ["sha256"],
        "hash algorithm identities required",
    )
    require(
        controls.get("append_before_seal") is True
        and controls.get("immutable_after_seal") is True
        and controls.get("raw_seal_steps") == _RAW_SEAL_STEPS
        and controls.get("derived_seal_steps") == _DERIVED_SEAL_STEPS,
        "mutable or incomplete append-once seal",
    )

    def rules(name: str, allowed: frozenset[str], required: frozenset[str]) -> None:
        values = controls.get(name)
        require(
            isinstance(values, list)
            and values
            and len(values) == len(set(values))
            and all(isinstance(value, str) and value in allowed for value in values)
            and required <= set(values),
            f"incomplete or unknown {name} rule",
        )

    rules("stop", _REQUIRED_STOP_RULES, _REQUIRED_STOP_RULES)
    rules("pause", _ALLOWED_PAUSE_RULES, frozenset())
    rules("no_go", _REQUIRED_NO_GO_RULES, _REQUIRED_NO_GO_RULES)
    rules("advance", _ALLOWED_ADVANCE_RULES, _ALLOWED_ADVANCE_RULES)
    return {"schema": document["schema"], "status": "ready-for-review", "experiment_id": None, "freeze_state": "unfrozen"}


validate_integrated_physical_readiness = validate_readiness_contract


_PREFREEZE_KEYS = frozenset({
    "schema", "experiment_id", "freeze_state", "readiness", "identity",
    "component_ledger", "workload_oracle", "budget_policy",
    "physical_conditions", "evidence_scope",
})
_PREFREEZE_COMPONENTS = {
    "fixture_provider": "common", "owned_memory": "common",
    "cache_interconnect": "common", "clock_reset": "common",
    "private_output_validation": "common", "rocket_fallback": "rocket_fallback",
    "graph_core": "graph_delta", "graph_tl_client": "graph_delta",
    "selector_adapter": "graph_delta",
}


def validate_prefreeze_identity_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Validate S11's repository-only, unallocated pre-freeze identity contract.

    This is deliberately a second validator: S10 remains its own accepted
    readiness boundary and is nested here unchanged.
    """
    require(isinstance(document, dict), "pre-freeze contract must be an object")
    require(set(document) in {_PREFREEZE_KEYS, _PREFREEZE_KEYS - {"experiment_id"}}, "missing or unknown pre-freeze field")
    require(document["schema"] == "raveil.t0044-integrated-physical-prefreeze/v2", "invalid pre-freeze schema")
    require(document.get("experiment_id") is None, "experiment_id must be absent or null")
    require(document["freeze_state"] == "unfrozen", "freeze_state must be unfrozen")
    validate_readiness_contract(document["readiness"])

    def exact(value: Any, keys: set[str], name: str) -> dict[str, Any]:
        require(isinstance(value, dict) and set(value) == keys, f"missing or unknown field in {name}")
        return value

    def digest(value: Any, name: str, *, image: bool = False) -> None:
        prefix = "sha256:" if image else ""
        require(isinstance(value, str) and re.fullmatch(prefix + r"[0-9a-f]{64}", value) is not None, f"invalid {name} identity")

    identity = exact(document["identity"], {"implementation_authority_commit", "top", "variants", "preflight", "toolchain"}, "identity")
    require(isinstance(identity["implementation_authority_commit"], str) and re.fullmatch(r"[0-9a-f]{40}", identity["implementation_authority_commit"]) is not None, "invalid implementation authority")
    require(identity["top"] == TOP, "top identity must be ChipTop")
    variants = identity["variants"]
    require(isinstance(variants, dict) and set(variants) == set(VARIANTS), "variant identity set mismatch")
    variant_keys = {"config", "rtl_tree_sha256", "rtl_filelist_sha256", "firrtl_sha256", "lowering_provenance_sha256", "source_sha256", "input_sha256", "rocket_canonical_module_sha256", "memory_macro_contract_sha256"}
    peer_values: dict[str, list[str]] = {"rocket_canonical_module_sha256": [], "memory_macro_contract_sha256": []}
    for name, config in VARIANTS.items():
        item = exact(variants[name], variant_keys, f"identity variant {name}")
        require(item["config"] == config, "variant config mismatch")
        for key in variant_keys - {"config"}:
            digest(item[key], key)
        for key in peer_values:
            peer_values[key].append(item[key])
    require(all(len(set(values)) == 1 for values in peer_values.values()), "peer canonical identities mismatch")
    preflight = exact(identity["preflight"], {"comparison_sha256", "raw_manifest_sha256", "derived_manifest_sha256"}, "preflight")
    for key, value in preflight.items(): digest(value, key)
    toolchain = exact(identity["toolchain"], {"generator_image", "generator_rootfs_sha256", "physical_image", "physical_rootfs_sha256", "lock_sha256", "yosys_sha256", "opensta_sha256", "standard_cell_liberty_sha256", "tech_lef_sha256", "sdc_sha256"}, "toolchain")
    for key, value in toolchain.items(): digest(value, key, image=key in {"generator_image", "physical_image"})

    ledger = document["component_ledger"]
    require(isinstance(ledger, list) and len(ledger) == len(_PREFREEZE_COMPONENTS), "component ledger must be exhaustive")
    seen = set()
    component_keys = {"name", "role", "inclusion", "instance_paths", "module_sha256", "accounting_owner", "activity_scope"}
    for item in ledger:
        exact(item, component_keys, "component ledger entry")
        name, role = item["name"], item["role"]
        require(name in _PREFREEZE_COMPONENTS and name not in seen and role == _PREFREEZE_COMPONENTS.get(name), "invalid or duplicate component")
        seen.add(name)
        inclusion = exact(item["inclusion"], set(VARIANTS), "component inclusion")
        paths = exact(item["instance_paths"], set(VARIANTS), "component paths")
        hashes = exact(item["module_sha256"], set(VARIANTS), "component hashes")
        activity = {"common": "included_both_candidates", "rocket_fallback": "idle_when_graph_active_and_active_when_selected", "graph_delta": "active_when_graph_selected"}
        require(item["accounting_owner"] == role, "invalid component accounting owner")
        require(item["activity_scope"] == activity[role], "invalid component activity scope")
        for variant in VARIANTS:
            require(isinstance(inclusion[variant], bool) and isinstance(paths[variant], list) and all(isinstance(path, str) and path.strip() and path.lower() not in {"tbd", "unknown", "placeholder"} for path in paths[variant]), "invalid component inclusion/path")
            require(hashes[variant] is None or (isinstance(hashes[variant], str) and _HEX_SHA256.fullmatch(hashes[variant]) is not None), "invalid component hash")
        if role in {"common", "rocket_fallback"}:
            require(all(inclusion.values()) and all(paths.values()) and hashes["integrated-static-graph-rocket"] == hashes["matched-rocket-system"] and hashes["integrated-static-graph-rocket"] is not None, "common/fallback must match peers")
        else:
            require(inclusion["integrated-static-graph-rocket"] and not inclusion["matched-rocket-system"] and paths["integrated-static-graph-rocket"] and not paths["matched-rocket-system"] and hashes["integrated-static-graph-rocket"] is not None and hashes["matched-rocket-system"] is None, "graph delta must be integrated-only")
    require(seen == set(_PREFREEZE_COMPONENTS), "component ledger set mismatch")

    oracle = exact(document["workload_oracle"], {"operation", "input_words", "output_words", "comparison", "artifact_sha256", "input_generator_sha256", "oracle_sha256", "simulator_sha256", "input_schedule", "oracle_access", "lifecycle"}, "workload_oracle")
    require(oracle["operation"] == "uint32_stencil_5_point_bounded" and oracle["input_words"] == 324 and oracle["output_words"] == 256 and oracle["comparison"] == "all_words_plus_checksum", "fixed workload shape/comparison required")
    for key in ("artifact_sha256", "input_generator_sha256", "oracle_sha256", "simulator_sha256"): digest(oracle[key], key)
    require(oracle["artifact_sha256"] != oracle["oracle_sha256"], "candidate and oracle identities must differ")
    require(oracle["input_schedule"] == "candidate_blind_deterministic" and oracle["oracle_access"] == "inaccessible_to_candidates", "candidate-blind oracle required")
    require(oracle["lifecycle"] == ["installation", "staging", "execution", "drain_completion", "validation", "publication"], "workload lifecycle mismatch")

    budget = exact(document["budget_policy"], {"traffic_equal", "unequal_traffic_disclosed", "lawful_candidate_optimization", "cpu_load_reuse_explicit", "common_resource_equality_required", "execution_window", "accounting_fields"}, "budget_policy")
    require(budget["traffic_equal"] is False and all(budget[key] is True for key in ("unequal_traffic_disclosed", "lawful_candidate_optimization", "cpu_load_reuse_explicit", "common_resource_equality_required")), "traffic/reuse policy mismatch")
    require(budget["execution_window"] == "installation_through_drain_completion_excluding_validation_publication", "execution window mismatch")
    require(budget["accounting_fields"] == ["useful_load", "useful_add", "useful_store", "useful_output", "admitted_read", "completed_read", "admitted_write", "completed_write", "bytes", "stall", "backpressure"], "accounting fields mismatch")

    physical = exact(document["physical_conditions"], {"common_to_variants", "clock", "input_delay", "output_delay", "standard_cell_pvt", "rc_corner", "load_model_sha256", "drive_model_sha256", "generated_clocks", "false_paths", "multicycle_paths", "sdc_sha256"}, "physical_conditions")
    require(physical["common_to_variants"] is True and physical["sdc_sha256"] == toolchain["sdc_sha256"], "physical conditions or SDC drift")
    clock = exact(physical["clock"], {"port", "period", "waveform"}, "physical clock")
    require(isinstance(clock["port"], str) and clock["port"].strip() and isinstance(clock["period"], (int, float)) and not isinstance(clock["period"], bool) and math.isfinite(clock["period"]) and clock["period"] > 0, "invalid clock")
    require(clock["waveform"] == [0.0, clock["period"] / 2], "clock waveform mismatch")
    for key in ("input_delay", "output_delay"):
        require(isinstance(physical[key], (int, float)) and not isinstance(physical[key], bool) and math.isfinite(physical[key]) and physical[key] >= 0, "invalid IO delay")
    require(all(isinstance(physical[key], str) and physical[key].strip() and physical[key].lower() not in {"tbd", "placeholder", "unknown"} for key in ("standard_cell_pvt", "rc_corner")), "invalid PVT/RC")
    for key in ("load_model_sha256", "drive_model_sha256", "sdc_sha256"): digest(physical[key], key)
    for key in ("generated_clocks", "false_paths", "multicycle_paths"):
        require(isinstance(physical[key], list) and all(isinstance(value, str) and value.strip() for value in physical[key]), "constraint declaration list required")
    require(
        all(
            macro["pvt"] == physical["standard_cell_pvt"]
            and macro["rc_corner"] == physical["rc_corner"]
            for macro in document["readiness"]["memory_macro_views"]["macros"]
        ),
        "common PVT/RC mismatch between macro views and physical conditions",
    )

    scope = exact(document["evidence_scope"], {"current_evidence", "target", "p_and_r_required_before_area_timing_claim", "physical_disclosures", "energy_claim", "thermal", "performance_claim", "fpga_claim", "asic_claim", "silicon_claim"}, "evidence_scope")
    require(scope["current_evidence"] == "host-contract-validation-only" and scope["target"] == "integrated-place-and-route-area-timing" and scope["p_and_r_required_before_area_timing_claim"] is True, "evidence boundary mismatch")
    require(scope["physical_disclosures"] == ["floorplan", "die", "core", "utilization", "placement_seed", "routing", "parasitic_identity"], "P&R disclosure mismatch")
    require(scope["energy_claim"] == {"enabled": False, "status": "not-measured"} and scope["thermal"] == {"applicable": False, "prohibits_energy_device_inference": True}, "energy/thermal boundary mismatch")
    require(all(scope[key] is False for key in ("performance_claim", "fpga_claim", "asic_claim", "silicon_claim")), "hardware/performance claims prohibited")
    return {"schema": document["schema"], "status": "ready-for-review", "experiment_id": None, "freeze_state": "unfrozen"}


def validate_measurement_readiness_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Validate S12's pre-data physical measurement contract, without freezing it."""
    keys = {"schema", "experiment_id", "freeze_state", "prefreeze", "measurement_design", "estimator_policy", "decision_policy", "evidence_protocol"}
    require(isinstance(document, dict) and (set(document) == keys or set(document) == keys - {"experiment_id"}), "missing or unknown measurement readiness field")
    require(document["schema"] == "raveil.t0044-integrated-physical-measurement-readiness/v3", "invalid measurement readiness schema")
    require(document.get("experiment_id") is None and document["freeze_state"] == "unfrozen", "experiment must be unallocated and unfrozen")
    validate_prefreeze_identity_contract(document["prefreeze"])
    def exact(value: Any, expected: set[str], name: str) -> dict[str, Any]:
        require(isinstance(value, dict) and set(value) == expected, f"missing or unknown field in {name}")
        return value
    design = exact(document["measurement_design"], {"matrix", "physical_flow_seeds", "run_order", "pairing", "stages", "scope", "repetition_policy"}, "measurement design")
    require(design["matrix"] == list(VARIANTS) and design["physical_flow_seeds"] == [101, 202] and design["run_order"] == [[101, "integrated-static-graph-rocket"], [101, "matched-rocket-system"], [202, "matched-rocket-system"], [202, "integrated-static-graph-rocket"]], "matrix, seeds, or balanced seed-major order mismatch")
    require(design["pairing"] == {"same_seed_constraints_toolchain": True, "fresh_synthesis_and_pnr_per_pair": True, "raw_result_import": False, "deterministic_reruns_reproducibility_only": True, "reruns_are_samples": False}, "pairing/reproducibility policy mismatch")
    require(design["stages"] == ["synthesis", "floorplan", "placement", "clock_tree", "routing", "parasitic_extraction", "sta"], "physical stage sequence mismatch")
    require(design["scope"] == {"dynamic_latency_traffic_campaign": "not_in_scope_not_reopened", "energy": "not_in_scope", "boom": "not_in_scope", "cgra": "not_in_scope"}, "physical scope mixing")
    reps = exact(design["repetition_policy"], {"runs_per_variant", "inference_unit", "uncertainty", "ci_95", "reruns"}, "repetition policy")
    nested = document["prefreeze"]["readiness"]["repetitions"]
    require(reps == {"runs_per_variant": 2, "inference_unit": "paired_physical_flow_seed", "uncertainty": "controlled_paired_seed_sensitivity_only", "ci_95": "unavailable_not_imputed", "reruns": "reproducibility_only_not_samples"} and nested["count"] == 2 and nested["seeds"] == [101, 202] and nested["inference_unit"] == reps["inference_unit"] and nested["uncertainty_policy"] == reps["uncertainty"] and nested["interval_95_policy"] == reps["ci_95"], "nested repetition/CI policy mismatch")
    estimator = exact(document["estimator_policy"], {"area", "timing", "uncertainty"}, "estimator policy")
    require(estimator["area"] == {"required_fields": ["integrated_total_area", "matched_total_area", "graph_delta_component_area", "matched_rocket_component_area"], "ratio_formula": "graph_delta_component_area/matched_rocket_component_area", "absolute_totals_reported": True, "summary": "per_seed_ratio_and_median_of_paired_seed_ratios_descriptive"}, "area estimator mismatch")
    require(estimator["timing"] == {"metric": "worst_setup_slack_ns", "period_ns": 40.0, "same_sdc_pvt_rc": True, "report_each_candidate_seed": True, "meet_iff": "slack>=0"}, "timing estimator mismatch")
    require(estimator["uncertainty"] == {"kind": "controlled_paired_seed_sensitivity_only", "ci_95": "unavailable_not_imputed", "deterministic_reruns_independent_samples": False}, "uncertainty estimator mismatch")
    decision = exact(document["decision_policy"], {"stop", "no_go", "pause", "advance", "prohibitions", "energy"}, "decision policy")
    require(decision["stop"] == ["oracle_mismatch", "resource_inequality", "unexplained_traffic", "accounting_missing", "identity_config_tool_drift", "incomplete_matrix", "window_mismatch", "physical_stage_closure_missing", "seal_failure"], "stop policy mismatch")
    require(decision["no_go"] == ["any_area_ratio_gt_0.25", "integrated_misses_40ns_matched_meets", "candidate_only_condition_needed", "rtl_regeneration_configurability_reinvention_dependency_needed"], "no-go policy mismatch")
    require(decision["pause"] == ["matched_misses_or_both_miss", "required_physical_input_component_unavailable", "pnr_closure_ambiguous", "fairness_boundary_unresolved"], "pause policy mismatch")
    require(decision["advance"] == {"name": "advance_partial_integrated_physical", "requires": ["every_pair_stage_seal_complete", "both_meet_40ns", "every_area_ratio_lte_0.25", "equality_fairness_pass", "missing_dimensions_explicit"]}, "advance policy mismatch")
    require(decision["prohibitions"] == ["generic_go", "t0044_close", "product_hardware_claim", "adaptive_threshold_target_sweep_change"] and decision["energy"] == {"status": "not_evaluable_in_s12", "threshold_0.90_active": False}, "decision prohibition/energy mismatch")
    evidence = exact(document["evidence_protocol"], {"run", "raw", "raw_seal", "derived", "result_seal", "failed_attempt", "recovery", "promotion", "prohibitions", "scientific_field_change"}, "evidence protocol")
    require(evidence["run"] == "immutable_new_run_id_per_attempt" and evidence["raw"] == ["frozen_manifest", "command_environment_exit", "identity_snapshot", "physical_stage_reports", "component_area_ledger", "timing_paths_constraints", "file_map"], "RUN/raw protocol mismatch")
    require(evidence["raw_seal"] == ["relative_path", "bytes", "sha256", "manifest", "run_id"] and evidence["derived"] == "reads_only_sealed_raw_writes_once" and evidence["result_seal"] == ["raw_seal", "report", "derived_file_map"], "seal protocol mismatch")
    require(evidence["failed_attempt"] == "retain_failed_raw_seal_no_eligible_derived_claim" and evidence["recovery"] == "new_run_id_binds_failed_seal_imported_hashes_exact_rerun_imports_not_samples", "failure/recovery mismatch")
    require(evidence["promotion"] == "immutable_remote_copy_one_way_download_verify_marker_last_tracked_non_sensitive_receipt" and evidence["prohibitions"] == ["credentials", "absolute_paths"] and evidence["scientific_field_change"] == "requires_new_predata_freeze", "promotion/prohibition mismatch")
    return {"schema": document["schema"], "status": "ready-for-review", "experiment_id": None, "freeze_state": "unfrozen"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


YOSYS_AUTO_ID = re.compile(
    r"(?<=\$)[0-9]+(?=_[A-Za-z0-9]|[ \t\[]|$)"
)
YOSYS_CANDIDATE_MOUNT = re.compile(r"/(?:integrated|baseline)/generated-src/")


def canonical_rtlil_module_sha256(
    module_lines: list[str], module_attributes: dict[str, str]
) -> str:
    """Hash RTLIL semantics while excluding Yosys process-global numeric IDs.

    Yosys assigns the final ``$<number>`` component of generated identifiers
    from a process-global counter.  Adding an unrelated module can therefore
    renumber an otherwise byte-identical Rocket module and reorder its RTLIL
    declarations.  The canonical form changes only those numeric components,
    keeps attributes, source locations, types, parameters, and connections,
    sorts complete top-level RTLIL units, and canonicalizes only proven-
    independent statements inside process runs whose order has no semantics.
    """
    require(
        len(module_lines) >= 2
        and module_lines[0].startswith("module \\")
        and module_lines[-1] == "end",
        "malformed RTLIL module boundary",
    )

    def normalize(line: str) -> str:
        candidate_relative = YOSYS_CANDIDATE_MOUNT.sub(
            "/candidate/generated-src/", line
        )
        return YOSYS_AUTO_ID.sub("<yosys-auto-id>", candidate_relative)

    def signal_base(token: str) -> str | None:
        if not token.startswith(("\\", "$")):
            return None
        return token.split("[", 1)[0]

    def process_statement_access(
        line: str, operation: str
    ) -> tuple[set[str], set[str]] | None:
        """Return conservative signal accesses for one flat RTLIL statement."""
        statement = line.strip()
        if operation == "assign" and statement == "assign { } { }":
            return set(), set()
        fields = statement.split(maxsplit=2)
        if len(fields) != 3 or fields[0] != operation:
            return None
        target = signal_base(fields[1])
        if target is None:
            return None
        reads = {
            base
            for token in re.findall(r"(?:\\|\$)[^\s{}]+", fields[2])
            if (base := signal_base(token)) is not None
        }
        return {target}, reads

    def normalize_partial_order_run(
        run: list[str], operation: str, *, reads_conflict: bool
    ) -> list[str]:
        """Sort independent statements while preserving every dependency edge."""
        accesses = [process_statement_access(line, operation) for line in run]
        if any(access is None for access in accesses):
            return run
        concrete = [access for access in accesses if access is not None]
        edges = [set() for _ in run]
        indegree = [0 for _ in run]
        for index, (writes, reads) in enumerate(concrete):
            for other_index in range(index + 1, len(concrete)):
                other_writes, other_reads = concrete[other_index]
                conflict = bool(writes & other_writes)
                if reads_conflict:
                    conflict = conflict or bool(
                        writes & other_reads or other_writes & reads
                    )
                if conflict:
                    edges[index].add(other_index)
                    indegree[other_index] += 1
        ready = {index for index, degree in enumerate(indegree) if degree == 0}
        ordered: list[str] = []
        while ready:
            index = min(ready, key=lambda item: (run[item], item))
            ready.remove(index)
            ordered.append(run[index])
            for successor in edges[index]:
                indegree[successor] -= 1
                if indegree[successor] == 0:
                    ready.add(successor)
        return ordered if len(ordered) == len(run) else run

    def normalize_process(block: list[str]) -> list[str]:
        lines = list(block)
        # Defaults before a switch are priority-sensitive, so never move an
        # assign across a control boundary.  Only sort one contiguous flat run
        # after proving that its reads and writes are independent.
        index = 1
        while index < len(lines) - 1:
            if lines[index].startswith("    assign "):
                end = index + 1
                while end < len(lines) - 1 and lines[end].startswith("    assign "):
                    end += 1
                lines[index:end] = normalize_partial_order_run(
                    lines[index:end], "assign", reads_conflict=True
                )
                index = end
                continue
            if lines[index].startswith("    sync "):
                update_index = index + 1
                update_end = update_index
                while (
                    update_end < len(lines) - 1
                    and lines[update_end].startswith("      update ")
                ):
                    update_end += 1
                lines[update_index:update_end] = normalize_partial_order_run(
                    lines[update_index:update_end],
                    "update",
                    reads_conflict=False,
                )
                index = update_end
                continue
            index += 1
        return lines

    units: list[tuple[str, ...]] = []
    pending_attributes: list[str] = []
    index = 1
    while index < len(module_lines) - 1:
        line = module_lines[index]
        require(line.startswith("  "), f"unexpected RTLIL module line: {line}")
        if line.startswith("  attribute "):
            pending_attributes.append(normalize(line))
            index += 1
            continue
        if line.startswith(("  wire ", "  memory ", "  connect ")):
            units.append(tuple(pending_attributes + [normalize(line)]))
            pending_attributes = []
            index += 1
            continue
        if line.startswith(("  cell ", "  process ")):
            block = pending_attributes + [normalize(line)]
            pending_attributes = []
            index += 1
            while index < len(module_lines) - 1:
                nested = module_lines[index]
                block.append(normalize(nested))
                index += 1
                if nested == "  end":
                    break
            else:
                raise ValueError("unterminated RTLIL cell or process")
            process_index = next(
                (
                    position
                    for position, block_line in enumerate(block)
                    if block_line.startswith("  process ")
                ),
                None,
            )
            if process_index is not None:
                block[process_index:] = normalize_process(block[process_index:])
            units.append(tuple(block))
            continue
        raise ValueError(f"unsupported RTLIL top-level unit: {line}")
    require(not pending_attributes, "orphan RTLIL module attributes")
    payload = {
        "module": normalize(module_lines[0]),
        "attributes": {
            key: normalize(value) for key, value in sorted(module_attributes.items())
        },
        "units": sorted(units),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_rtlil_hierarchy(path: Path) -> dict[str, Any]:
    """Load only module, port, cell, and module-attribute structure from RTLIL."""
    parsed: dict[str, Any] = {"modules": {}}
    pending_attributes: dict[str, str] = {}
    current: dict[str, Any] | None = None
    current_name = ""
    module_lines: list[str] = []
    with path.open() as source:
        for raw in source:
            line = raw.rstrip("\n")
            if current is None:
                attribute = re.fullmatch(r"attribute \\([^ ]+) (.+)", line)
                if attribute:
                    pending_attributes[attribute.group(1)] = attribute.group(2)
                    continue
                module = re.fullmatch(r"module \\(.+)", line)
                if module:
                    current_name = module.group(1)
                    current = {
                        "attributes": pending_attributes,
                        "ports": {},
                        "cells": {},
                    }
                    pending_attributes = {}
                    module_lines = [line]
                continue
            module_lines.append(line)
            if line == "end":
                current["rtlil_raw_sha256"] = hashlib.sha256(
                    ("\n".join(module_lines) + "\n").encode()
                ).hexdigest()
                current["rtlil_canonical_sha256"] = canonical_rtlil_module_sha256(
                    module_lines, current["attributes"]
                )
                parsed["modules"][current_name] = current
                current = None
                current_name = ""
                module_lines = []
                continue
            port = re.fullmatch(
                r"  wire(?: width ([0-9]+))? (input|output|inout) [0-9]+ \\(.+)",
                line,
            )
            if port:
                width = int(port.group(1) or "1")
                current["ports"][port.group(3)] = {
                    "direction": port.group(2),
                    "bits": list(range(width)),
                }
                continue
            cell = re.fullmatch(r"  cell (?:\\([^ ]+)|(\$[^ ]+)) (.+)", line)
            if cell:
                cell_type = cell.group(1) or cell.group(2)
                current["cells"][cell.group(3)] = {"type": cell_type}
    require(current is None, f"unterminated RTLIL module: {current_name}")
    require(parsed["modules"], f"RTLIL lacks modules: {path}")
    return parsed


def modules(document: dict[str, Any]) -> dict[str, Any]:
    value = document.get("modules")
    require(isinstance(value, dict), "Yosys JSON lacks modules")
    require(TOP in value, f"Yosys JSON lacks {TOP}")
    return value


def attribute_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value not in {"", "0", "false", "False", "00000000000000000000000000000000"}
    return bool(value)


def port_signature(module: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    return {
        name: (
            port.get("direction"),
            len(port.get("bits", [])),
            port.get("offset", 0),
            bool(port.get("upto", 0)),
            bool(port.get("signed", False)),
        )
        for name, port in sorted(module.get("ports", {}).items())
    }


def walk_hierarchy(
    all_modules: dict[str, Any],
    module_name: str = TOP,
    prefix: str = "",
    stack: tuple[str, ...] = (),
) -> Iterable[tuple[str, str, dict[str, Any]]]:
    require(module_name not in stack, f"recursive module hierarchy at {module_name}")
    module = all_modules[module_name]
    for instance_name, cell in sorted(module.get("cells", {}).items()):
        cell_type = cell.get("type", "")
        path = f"{prefix}/{instance_name}" if prefix else instance_name
        yield path, cell_type, cell
        if cell_type in all_modules:
            yield from walk_hierarchy(
                all_modules, cell_type, path, stack + (module_name,)
            )


def reachable_module_names(
    all_modules: dict[str, Any], instances: Iterable[tuple[str, str, dict[str, Any]]]
) -> set[str]:
    return {TOP} | {cell_type for _, cell_type, _ in instances if cell_type in all_modules}


def module_json_sha256(module: dict[str, Any]) -> str:
    encoded = json.dumps(module, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def module_structural_sha256(module: dict[str, Any]) -> str:
    canonical = module.get("rtlil_canonical_sha256")
    if canonical is None:
        return module_json_sha256(module)
    require(
        isinstance(canonical, str) and _HEX_SHA256.fullmatch(canonical) is not None,
        "malformed canonical RTLIL module SHA-256",
    )
    return canonical


def analyze_hierarchy(document: dict[str, Any], variant: str) -> dict[str, Any]:
    require(variant in VARIANTS, f"unknown variant: {variant}")
    all_modules = modules(document)
    instances = list(walk_hierarchy(all_modules))
    reachable = reachable_module_names(all_modules, instances)
    reachable_blackboxes: set[str] = set()
    for module_name in sorted(reachable):
        attrs = all_modules[module_name].get("attributes", {})
        if attribute_true(attrs.get("blackbox", False)):
            require(
                module_name in MEMORY_MACRO_CONTRACT,
                f"unapproved reachable blackbox module: {module_name}",
            )
            reachable_blackboxes.add(module_name)

    typed_paths: dict[str, list[str]] = {}
    for path, cell_type, _ in instances:
        typed_paths.setdefault(cell_type, []).append(path)
    require(
        reachable_blackboxes == set(MEMORY_MACRO_CONTRACT),
        "reachable memory-macro blackbox set is incomplete or drifted",
    )
    memory_macro_paths = {
        name: typed_paths.get(name, []) for name in sorted(MEMORY_MACRO_CONTRACT)
    }
    for name, expected_count in MEMORY_MACRO_COUNTS.items():
        require(
            len(memory_macro_paths[name]) == expected_count,
            f"memory-macro instance count drift for {name}",
        )
        actual_ports = {
            port: (value[0], value[1])
            for port, value in port_signature(all_modules[name]).items()
        }
        require(
            actual_ports == MEMORY_MACRO_PORTS[name],
            f"memory-macro port contract drift for {name}",
        )

    rockets = typed_paths.get("Rocket", [])
    require(len(rockets) == 1, "hierarchy must contain exactly one Rocket instance")
    managers = typed_paths.get("RaveilOwnedTLMemory", [])
    fixtures = typed_paths.get("RaveilFixtureInputProvider", [])
    require(len(managers) == 1, "hierarchy must contain exactly one owned memory manager")
    require(len(fixtures) == 1, "hierarchy must contain exactly one fixture provider")
    require(
        any(name == "DCache" or name.endswith("DCache") for name in reachable),
        "hierarchy lacks a Rocket data cache",
    )
    require(
        any(name.startswith("TLXbar") or name.startswith("TLInterconnectCoupler")
            for name in reachable),
        "hierarchy lacks a TileLink interconnect",
    )

    graph_types = {
        "RaveilIntegratedGraphDigitalTop",
        "RaveilStaticStencilCore",
        "RaveilStaticStencilTLClient",
    }
    graph_paths = {
        name: typed_paths.get(name, [])
        for name in sorted(graph_types)
    }
    if variant == "integrated-static-graph-rocket":
        for name, paths in graph_paths.items():
            require(len(paths) == 1, f"integrated hierarchy requires one {name} instance")
    else:
        require(
            not any(graph_paths.values()),
            "matched Rocket baseline contains integrated Graph logic",
        )

    signature = port_signature(all_modules[TOP])
    missing_ports = sorted(REQUIRED_PORTS - signature.keys())
    require(not missing_ports, f"ChipTop lacks required ports: {missing_ports}")
    require(signature["axi4_mem_0_clock"][0] == "output", "AXI clock must be output")
    require(signature["clock_tap"][0] == "output", "clock tap must be output")
    for name in CLOCK_ROOTS | {"reset_io", "custom_boot"}:
        require(signature[name][0] == "input", f"{name} must be input")

    return {
        "top": TOP,
        "variant": variant,
        "config": VARIANTS[variant],
        "rocket_instance_path": rockets[0],
        "rocket_module_canonical_sha256": all_modules["Rocket"].get(
            "rtlil_canonical_sha256", module_json_sha256(all_modules["Rocket"])
        ),
        "rocket_module_raw_sha256": all_modules["Rocket"].get(
            "rtlil_raw_sha256", module_json_sha256(all_modules["Rocket"])
        ),
        "rocket_module_canonicalization":
            "rtlil-top-level-unit-sort-and-yosys-auto-id-elision-v1",
        "owned_memory_path": managers[0],
        "fixture_provider_path": fixtures[0],
        "graph_paths": graph_paths,
        "reachable_module_count": len(reachable),
        "port_signature": signature,
        "blackboxes": len(reachable_blackboxes),
        "blackbox_policy": "matched-memory-macros-only",
        "memory_macro_paths": memory_macro_paths,
        "memory_macro_port_signatures": {
            name: port_signature(all_modules[name])
            for name in sorted(MEMORY_MACRO_CONTRACT)
        },
    }


def analyze_common_concrete_hierarchy(
    document: dict[str, Any],
    variant: str,
    *,
    source_sha256: str,
    flat_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Strict Option-B pre-data check for a concrete (non-blackbox) export."""
    require(variant in VARIANTS, f"unknown variant: {variant}")
    require(
        _HEX_SHA256.fullmatch(source_sha256) is not None,
        "common memory source SHA-256 is required",
    )
    all_modules = modules(document)
    instances = list(walk_hierarchy(all_modules))
    reachable = reachable_module_names(all_modules, instances)
    blackboxes = {name for name in reachable if attribute_true(all_modules[name].get("attributes", {}).get("blackbox", False))}
    require(not blackboxes, "common-concrete policy requires zero reachable blackboxes")
    typed_paths: dict[str, list[str]] = {}
    for path, cell_type, _ in instances:
        typed_paths.setdefault(cell_type, []).append(path)
    macro_paths = {name: sorted(typed_paths.get(name, [])) for name in sorted(MEMORY_MACRO_CONTRACT)}
    require(set(typed_paths) >= set(MEMORY_MACRO_CONTRACT), "common concrete macro type missing")
    for name, expected in MEMORY_MACRO_COUNTS.items():
        require(len(macro_paths[name]) == expected, f"common concrete instance count drift for {name}")
        module = all_modules[name]
        require(not attribute_true(module.get("attributes", {}).get("blackbox", False)), f"concrete macro remains blackbox: {name}")
        actual_ports = {p: (v[0], v[1]) for p, v in port_signature(module).items()}
        require(actual_ports == MEMORY_MACRO_PORTS[name], f"common concrete port contract drift for {name}")
        mems = [cell for cell in module.get("cells", {}).values() if cell.get("type") == "$mem_v2"]
        require(len(mems) == 1, f"common concrete module must contain exactly one $mem_v2: {name}")
    rockets = typed_paths.get("Rocket", [])
    require(len(rockets) == 1, "hierarchy must contain exactly one Rocket instance")
    managers = typed_paths.get("RaveilOwnedTLMemory", [])
    fixtures = typed_paths.get("RaveilFixtureInputProvider", [])
    require(len(managers) == 1, "hierarchy must contain exactly one owned memory manager")
    require(len(fixtures) == 1, "hierarchy must contain exactly one fixture provider")
    require(
        any(name == "DCache" or name.endswith("DCache") for name in reachable),
        "hierarchy lacks a Rocket data cache",
    )
    require(
        any(
            name.startswith("TLXbar") or name.startswith("TLInterconnectCoupler")
            for name in reachable
        ),
        "hierarchy lacks a TileLink interconnect",
    )
    graph_types = {
        "RaveilIntegratedGraphDigitalTop",
        "RaveilStaticStencilCore",
        "RaveilStaticStencilTLClient",
    }
    graph_paths = {name: typed_paths.get(name, []) for name in sorted(graph_types)}
    if variant == "integrated-static-graph-rocket":
        for name, paths in graph_paths.items():
            require(len(paths) == 1, f"integrated hierarchy requires one {name} instance")
    else:
        require(
            not any(graph_paths.values()),
            "matched Rocket baseline contains integrated Graph logic",
        )
    signature = port_signature(all_modules[TOP])
    missing_ports = sorted(REQUIRED_PORTS - signature.keys())
    require(not missing_ports, f"ChipTop lacks required ports: {missing_ports}")
    require(signature["axi4_mem_0_clock"][0] == "output", "AXI clock must be output")
    require(signature["clock_tap"][0] == "output", "clock tap must be output")
    for name in CLOCK_ROOTS | {"reset_io", "custom_boot"}:
        require(signature[name][0] == "input", f"{name} must be input")
    clock_inventory = (
        analyze_clock_inventory(flat_document) if flat_document is not None else None
    )
    return {
        "top": TOP, "variant": variant, "config": VARIANTS[variant],
        "rocket_instance_path": rockets[0],
        "rocket_module_canonical_sha256": module_structural_sha256(all_modules["Rocket"]),
        "rocket_module_raw_sha256": all_modules["Rocket"].get("rtlil_raw_sha256", module_json_sha256(all_modules["Rocket"])),
        "owned_memory_path": managers[0],
        "fixture_provider_path": fixtures[0],
        "graph_paths": graph_paths,
        "port_signature": signature, "memory_macro_paths": macro_paths,
        "memory_macro_port_signatures": {n: port_signature(all_modules[n]) for n in sorted(MEMORY_MACRO_CONTRACT)},
        "memory_macro_module_sha256": {
            name: module_structural_sha256(all_modules[name])
            for name in sorted(MEMORY_MACRO_CONTRACT)
        },
        "reachable_blackboxes": [], "blackbox_policy": "common-concrete-zero-reachable-blackboxes",
        "source_sha256": source_sha256,
        "clock_inventory": clock_inventory,
        "status": "structural-preflight-only",
    }


def compare_common_concrete_reports(
    integrated: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, Any]:
    """Compare the two concrete-memory hierarchy reports without candidate data."""
    require(
        integrated.get("variant") == "integrated-static-graph-rocket",
        "wrong integrated concrete report",
    )
    require(
        baseline.get("variant") == "matched-rocket-system",
        "wrong matched-Rocket concrete report",
    )
    for field in (
        "port_signature",
        "rocket_module_canonical_sha256",
        "owned_memory_path",
        "fixture_provider_path",
        "memory_macro_paths",
        "memory_macro_port_signatures",
        "memory_macro_module_sha256",
        "source_sha256",
    ):
        require(
            integrated.get(field) == baseline.get(field),
            f"common concrete identity mismatch: {field}",
        )
    require(
        integrated.get("reachable_blackboxes") == baseline.get("reachable_blackboxes") == [],
        "common concrete hierarchy contains a reachable blackbox",
    )
    for label, report in (("integrated", integrated), ("baseline", baseline)):
        clocks = report.get("clock_inventory")
        require(isinstance(clocks, dict), f"{label} concrete clock inventory missing")
        require(
            clocks.get("allowed_roots") == sorted(CLOCK_ROOTS),
            f"{label} concrete clock-root policy drift",
        )
        require(
            clocks.get("unconstrained_clock_endpoints") == 0,
            f"{label} concrete hierarchy has unconstrained clock endpoints",
        )
    return {
        "schema": "raveil.exp-0011-common-memory-concrete/v1",
        "status": "structural-only",
        "source_sha256": integrated["source_sha256"],
        "memory_macro_instances": sum(MEMORY_MACRO_COUNTS.values()),
        "memory_macro_types": len(MEMORY_MACRO_CONTRACT),
        "rocket_module_canonical_sha256": integrated["rocket_module_canonical_sha256"],
        "common_clock_roots": integrated["clock_inventory"]["allowed_roots"],
        "reachable_blackboxes": 0,
        "nonclaims": [
            "no synthesis or memory mapping",
            "no placement or routing",
            "no timing, area, energy, performance, FPGA, ASIC, or silicon result",
        ],
    }


def is_constant(bit: Any) -> bool:
    return isinstance(bit, str) and bit.lower() in {"0", "1", "x", "z"}


def sequential_clock_ports(cell_type: str, cell: dict[str, Any]) -> set[str]:
    connections = cell.get("connections", {})
    if cell_type in MEMORY_MACRO_CLOCK_PORTS:
        pins = MEMORY_MACRO_CLOCK_PORTS[cell_type]
        require(pins <= connections.keys(), f"memory macro lacks clock pin: {cell_type}")
        return pins
    if cell_type == "$mem_v2":
        parameters = cell.get("parameters", {})
        active_pins: set[str] = set()
        for prefix in ("RD", "WR"):
            ports_value = parameters.get(f"{prefix}_PORTS")
            require(
                isinstance(ports_value, str)
                and ports_value
                and set(ports_value) <= {"0", "1"},
                f"$mem_v2 has malformed {prefix}_PORTS",
            )
            port_count = int(ports_value, 2)
            enable_value = parameters.get(f"{prefix}_CLK_ENABLE")
            require(
                isinstance(enable_value, str)
                and enable_value
                and set(enable_value) <= {"0", "1"},
                f"$mem_v2 has malformed {prefix}_CLK_ENABLE",
            )
            pin = f"{prefix}_CLK"
            require(pin in connections, f"$mem_v2 lacks {pin}")
            clock_bits = connections[pin]
            require(isinstance(clock_bits, list), f"$mem_v2 has malformed {pin}")
            if port_count == 0:
                require(int(enable_value, 2) == 0, f"$mem_v2 enables absent {prefix} port")
                require(not clock_bits, f"$mem_v2 has clock bits for absent {prefix} port")
                continue
            require(
                len(enable_value) == port_count,
                f"$mem_v2 {prefix}_CLK_ENABLE width disagrees with {prefix}_PORTS",
            )
            require(
                len(clock_bits) == port_count,
                f"$mem_v2 {pin} width disagrees with {prefix}_PORTS",
            )
            if set(enable_value) == {"0"}:
                require(
                    all(is_constant(bit) for bit in clock_bits),
                    f"$mem_v2 disabled {pin} is not constant",
                )
                continue
            require(
                set(enable_value) == {"1"},
                f"$mem_v2 mixed {prefix}_CLK_ENABLE is unsupported",
            )
            active_pins.add(pin)
        return active_pins
    if cell_type.startswith(("$memrd", "$memwr")):
        pins = {name for name in connections if "CLK" in name.upper()}
        require(pins, f"clocked memory cell lacks a clock pin: {cell_type}")
        return pins
    if cell_type.startswith("$_DFF") or cell_type.startswith("$_SDFF"):
        require("C" in connections, f"sequential cell lacks C clock pin: {cell_type}")
        return {"C"}
    if cell_type.startswith(("$dff", "$adff", "$sdff", "$aldff")):
        require("CLK" in connections, f"sequential cell lacks CLK clock pin: {cell_type}")
        return {"CLK"}
    if cell_type.startswith(("$dlatch", "$_DLATCH")):
        pins = {"EN", "E"} & connections.keys()
        require(pins, f"latch cell lacks enable clock pin: {cell_type}")
        return pins
    require(
        not cell_type.startswith("$ff"),
        f"clockless sequential cell is unsupported: {cell_type}",
    )
    return set()


def is_sequential(cell_type: str, cell: dict[str, Any]) -> bool:
    return bool(sequential_clock_ports(cell_type, cell))


def analyze_clock_inventory(document: dict[str, Any]) -> dict[str, Any]:
    top = modules(document)[TOP]
    ports = top.get("ports", {})
    bit_sources: dict[str, list[tuple[str, ...]]] = {}
    for port_name, port in ports.items():
        if port.get("direction") == "input":
            for bit in port.get("bits", []):
                if not is_constant(bit):
                    bit_sources.setdefault(str(bit), []).append(("port", port_name))
    cells = top.get("cells", {})
    for cell_name, cell in cells.items():
        directions = cell.get("port_directions", {})
        for pin, bits in cell.get("connections", {}).items():
            if directions.get(pin) == "output":
                for bit in bits:
                    if not is_constant(bit):
                        bit_sources.setdefault(str(bit), []).append(
                            ("cell", cell_name, pin)
                        )

    memo: dict[str, frozenset[str]] = {}
    derived_clock_bits: set[str] = set()
    derived_clock_driver_cells: set[str] = set()
    eicg_clock_gate_cells: set[str] = set()
    eicg_control_latch_cells: set[str] = set()

    def parameter_int(cell: dict[str, Any], name: str) -> int | None:
        value = cell.get("parameters", {}).get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value and set(value) <= {"0", "1"}:
            return int(value, 2)
        return None

    def eicg_raw_clock_bit(cell_name: str, cell: dict[str, Any]) -> Any | None:
        """Recognize only the exact low-phase-latch EICG emitted by Chipyard."""
        if cell.get("type") not in {"$and", "$logic_and"}:
            return None
        gate_source = str(cell.get("attributes", {}).get("src", ""))
        gate_source_parts = gate_source.split("|")
        gate_leaf = "generated-src/EICG_wrapper.v:18.16-18.32"
        if (
            len(gate_source_parts) != 2
            or gate_source_parts[1]
            not in {gate_leaf, f"/integrated/{gate_leaf}", f"/baseline/{gate_leaf}"}
        ):
            return None
        if cell.get("port_directions") != {"A": "input", "B": "input", "Y": "output"}:
            return None
        connections = cell.get("connections", {})
        if set(connections) != {"A", "B", "Y"}:
            return None
        if any(len(connections[pin]) != 1 for pin in ("A", "B", "Y")):
            return None
        wrapper_source = gate_source_parts[0]
        for latched_pin, raw_pin in (("A", "B"), ("B", "A")):
            latched_bit = connections[latched_pin][0]
            raw_bit = connections[raw_pin][0]
            sources = bit_sources.get(str(latched_bit), [])
            if len(sources) != 1 or sources[0][0] != "cell" or sources[0][2] != "Q":
                continue
            latch_name = sources[0][1]
            latch = cells[latch_name]
            if latch.get("type") != "$dlatch":
                continue
            latch_source = str(latch.get("attributes", {}).get("src", ""))
            latch_source_parts = latch_source.split("|")
            latch_leaf = "generated-src/EICG_wrapper.v:12.3-16.6"
            if (
                len(latch_source_parts) != 2
                or latch_source_parts[0] != wrapper_source
                or latch_source_parts[1]
                not in {
                    latch_leaf,
                    f"/integrated/{latch_leaf}",
                    f"/baseline/{latch_leaf}",
                }
            ):
                continue
            if latch.get("port_directions") != {"D": "input", "EN": "input", "Q": "output"}:
                continue
            latch_connections = latch.get("connections", {})
            if set(latch_connections) != {"D", "EN", "Q"}:
                continue
            if any(len(latch_connections[pin]) != 1 for pin in ("D", "EN", "Q")):
                continue
            if latch_connections["Q"][0] != latched_bit:
                continue
            if latch_connections["EN"][0] != raw_bit:
                continue
            if parameter_int(latch, "WIDTH") != 1:
                continue
            if parameter_int(latch, "EN_POLARITY") != 0:
                continue
            eicg_clock_gate_cells.add(cell_name)
            eicg_control_latch_cells.add(latch_name)
            return raw_bit
        return None

    def roots_for(bit: Any, visiting: frozenset[str] = frozenset()) -> frozenset[str]:
        if is_constant(bit):
            return frozenset()
        key = str(bit)
        if key in memo:
            return memo[key]
        require(key not in visiting, f"combinational clock-driver cycle at bit {key}")
        sources = bit_sources.get(key, [])
        require(sources, f"clock ancestry has no driver for bit {key}")
        require(len(sources) == 1, f"clock ancestry has multiple drivers for bit {key}")
        source = sources[0]
        if source[0] == "port":
            result = (
                frozenset({source[1]})
                if source[1] in CLOCK_ROOTS
                else frozenset()
            )
        else:
            cell_name = source[1]
            cell = cells[cell_name]
            cell_type = cell.get("type", "")
            derived_clock_bits.add(key)
            derived_clock_driver_cells.add(cell_name)
            eicg_clock = eicg_raw_clock_bit(cell_name, cell)
            if eicg_clock is not None:
                result = roots_for(eicg_clock, visiting | {key})
                memo[key] = result
                return result
            require(
                not is_sequential(cell_type, cell),
                f"clock for an endpoint is generated by sequential cell {cell_name}",
            )
            require(
                cell_type.startswith("$"),
                f"unresolved non-primitive clock driver {cell_name}:{cell_type}",
            )
            input_bits = [
                candidate
                for pin, bits in cell.get("connections", {}).items()
                if cell.get("port_directions", {}).get(pin) == "input"
                for candidate in bits
            ]
            require(input_bits, f"derived clock driver has no inputs: {cell_name}")
            roots: set[str] = set()
            for candidate in input_bits:
                roots.update(roots_for(candidate, visiting | {key}))
            result = frozenset(roots)
        memo[key] = result
        return result

    root_counts = {name: 0 for name in CLOCK_ROOTS}
    endpoints: list[dict[str, str]] = []
    for cell_name, cell in sorted(cells.items()):
        cell_type = cell.get("type", "")
        for pin in sorted(sequential_clock_ports(cell_type, cell)):
            require(
                cell.get("port_directions", {}).get(pin) == "input",
                f"sequential clock pin is not an input: {cell_name}.{pin}",
            )
            clock_bits = cell["connections"][pin]
            require(clock_bits, f"sequential clock pin is empty: {cell_name}.{pin}")
            for index, bit in enumerate(clock_bits):
                if is_constant(bit):
                    continue
                roots = roots_for(bit)
                require(
                    len(roots) == 1,
                    f"sequential clock lacks one unique external root: {cell_name}.{pin}[{index}]={sorted(roots)}",
                )
                root = next(iter(roots))
                require(root in CLOCK_ROOTS, f"unapproved clock root: {root}")
                root_counts[root] += 1
                endpoints.append({
                    "cell": cell_name,
                    "type": cell_type,
                    "pin": pin,
                    "root": root,
                })
    require(endpoints, "flattened RTL has no sequential or memory clock endpoints")
    missing_roots = sorted(name for name, count in root_counts.items() if count == 0)
    require(not missing_roots, f"declared clocks lack sequential endpoints: {missing_roots}")
    return {
        "allowed_roots": sorted(CLOCK_ROOTS),
        "root_endpoint_counts": dict(sorted(root_counts.items())),
        "sequential_endpoint_count": len(endpoints),
        "unconstrained_clock_endpoints": 0,
        "derived_clock_bits": sorted(derived_clock_bits),
        "derived_clock_driver_cells": sorted(derived_clock_driver_cells),
        "eicg_clock_gate_cells": sorted(eicg_clock_gate_cells),
        "eicg_control_latch_cells": sorted(eicg_control_latch_cells),
        "endpoints": endpoints,
    }


def validate_export(export_dir: Path, variant: str) -> dict[str, Any]:
    metadata = load_json(export_dir / "export-metadata.json")
    require(metadata.get("schema") == "raveil.exp-0011-rtl-export/v1", "bad export schema")
    require(metadata.get("variant") == variant, "export variant mismatch")
    require(metadata.get("config") == VARIANTS[variant], "export config mismatch")
    require(metadata.get("top") == TOP, "export top mismatch")
    require(metadata.get("performance") == "not-measured", "export contains a performance claim")
    for field in (
        "source_sha256", "input_sha256", "runner_sha256", "lock_sha256",
        "image_rootfs_sha256", "rtl_sha256", "rtl_filelist_sha256",
        "firrtl_sha256", "hierarchy_sha256", "lowering_provenance_sha256",
        "rocket_rtl_sha256", "memory_macro_contract_sha256",
    ):
        value = metadata.get(field, "")
        require(isinstance(value, str) and len(value) == 64, f"invalid export identity: {field}")
    require(
        re.fullmatch(r"sha256:[0-9a-f]{64}", metadata.get("image_id", "")) is not None,
        "invalid export image identity",
    )
    required_files = (
        "ChipTop.top.f", "rtl-files.txt", "pre-firtool.fir",
        "top-module-hierarchy.json", "lowering-provenance.txt",
        "memory-macro-contract.txt",
        "generated-src/ChipTop.sv", "generated-src/Rocket.sv",
    )
    for relative in required_files:
        require((export_dir / relative).is_file(), f"missing export file: {relative}")
    identity_files = {
        "rtl_filelist_sha256": "rtl-files.txt",
        "firrtl_sha256": "pre-firtool.fir",
        "hierarchy_sha256": "top-module-hierarchy.json",
        "lowering_provenance_sha256": "lowering-provenance.txt",
    }
    for field, relative in identity_files.items():
        require(
            sha256_file(export_dir / relative) == metadata[field],
            f"export artifact hash mismatch: {relative}",
        )
    require(
        tree_sha256(export_dir / "generated-src") == metadata["rtl_sha256"],
        "exported RTL tree hash mismatch",
    )
    require(
        sha256_file(export_dir / "generated-src/Rocket.sv") == metadata["rocket_rtl_sha256"],
        "Rocket RTL hash does not match export metadata",
    )
    macro_contract = {
        line.split()[1]: line.strip()
        for line in (export_dir / "memory-macro-contract.txt").read_text().splitlines()
        if line.strip()
    }
    require(macro_contract == MEMORY_MACRO_CONTRACT, "memory macro contract drift")
    require(
        sha256_file(export_dir / "memory-macro-contract.txt") ==
        metadata["memory_macro_contract_sha256"],
        "memory macro contract hash mismatch",
    )
    filelist = (export_dir / "ChipTop.top.f").read_text().splitlines()
    recorded_files = (export_dir / "rtl-files.txt").read_text().splitlines()
    require(filelist, "empty ChipTop RTL file list")
    require(len(filelist) == len(set(filelist)), "duplicate ChipTop RTL file-list entry")
    require(
        sorted(filelist) == sorted(recorded_files),
        "ChipTop and recorded RTL file lists differ",
    )
    safe_entry = re.compile(r"generated-src/[A-Za-z0-9_.-]+\.(?:sv|v)")
    for relative in filelist:
        require(safe_entry.fullmatch(relative) is not None, "unsafe RTL file-list entry")
        require((export_dir / relative).is_file(), f"missing copied RTL: {relative}")
    return metadata


def analyze_export(
    export_dir: Path,
    hierarchy_path: Path,
    flat_path: Path,
    variant: str,
) -> dict[str, Any]:
    metadata = validate_export(export_dir, variant)
    hierarchy_document = (
        load_rtlil_hierarchy(hierarchy_path)
        if hierarchy_path.suffix == ".rtlil"
        else load_json(hierarchy_path)
    )
    hierarchy = analyze_hierarchy(hierarchy_document, variant)
    clocks = analyze_clock_inventory(load_json(flat_path))
    return {
        "schema": "raveil.exp-0011-rtl-structural-report/v1",
        "variant": variant,
        "export": metadata,
        "hierarchy": hierarchy,
        "clock_inventory": clocks,
        "status": "structural-preflight-only",
        "performance": "not-measured",
    }


def compare_reports(integrated: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    require(integrated["variant"] == "integrated-static-graph-rocket", "wrong integrated report")
    require(baseline["variant"] == "matched-rocket-system", "wrong baseline report")
    a_hierarchy = integrated["hierarchy"]
    b_hierarchy = baseline["hierarchy"]
    require(
        a_hierarchy["port_signature"] == b_hierarchy["port_signature"],
        "external ChipTop port signatures differ",
    )
    require(
        a_hierarchy["rocket_module_canonical_sha256"] ==
        b_hierarchy["rocket_module_canonical_sha256"],
        "canonical Yosys-parsed Rocket module differs",
    )
    require(
        integrated["export"]["rocket_rtl_sha256"] == baseline["export"]["rocket_rtl_sha256"],
        "copied Rocket.sv differs",
    )
    require(
        integrated["export"]["rocket_revision"] == baseline["export"]["rocket_revision"],
        "Rocket source revisions differ",
    )
    require(
        integrated["export"]["image_rootfs_sha256"] == baseline["export"]["image_rootfs_sha256"],
        "generator toolchain root filesystems differ",
    )
    for field in (
        "image_id", "lock_sha256", "runner_sha256", "chipyard_revision",
        "normal_lowering", "physical_lowering",
    ):
        require(
            integrated["export"].get(field) == baseline["export"].get(field),
            f"export provenance differs: {field}",
        )
    require(
        integrated["export"]["memory_macro_contract_sha256"] ==
        baseline["export"]["memory_macro_contract_sha256"],
        "memory macro contracts differ",
    )
    require(
        a_hierarchy["memory_macro_paths"] == b_hierarchy["memory_macro_paths"],
        "memory macro instance paths differ",
    )
    require(
        a_hierarchy["memory_macro_port_signatures"] ==
        b_hierarchy["memory_macro_port_signatures"],
        "memory macro port signatures differ",
    )
    require(
        integrated["clock_inventory"]["allowed_roots"] ==
        baseline["clock_inventory"]["allowed_roots"] == sorted(CLOCK_ROOTS),
        "clock-root policies differ",
    )
    return {
        "schema": "raveil.exp-0011-rtl-preflight-comparison/v1",
        "top": TOP,
        "integrated_config": integrated["hierarchy"]["config"],
        "baseline_config": baseline["hierarchy"]["config"],
        "external_port_signature_equal": True,
        "rocket_instance_count": {"integrated": 1, "baseline": 1},
        "rocket_module_identity_equal": True,
        "rocket_module_canonical_sha256":
            a_hierarchy["rocket_module_canonical_sha256"],
        "rocket_module_raw_rtlil_equal":
            a_hierarchy["rocket_module_raw_sha256"] ==
            b_hierarchy["rocket_module_raw_sha256"],
        "rocket_module_raw_sha256": {
            "integrated": a_hierarchy["rocket_module_raw_sha256"],
            "baseline": b_hierarchy["rocket_module_raw_sha256"],
        },
        "rocket_rtl_sha256": integrated["export"]["rocket_rtl_sha256"],
        "common_clock_roots": sorted(CLOCK_ROOTS),
        "blackbox_policy": "matched-memory-macros-only",
        "memory_macro_contract_sha256":
            integrated["export"]["memory_macro_contract_sha256"],
        "memory_macro_paths": a_hierarchy["memory_macro_paths"],
        "blackbox_module_types": {
            "integrated": len(MEMORY_MACRO_CONTRACT),
            "baseline": len(MEMORY_MACRO_CONTRACT),
        },
        "blackbox_instances": {
            "integrated": sum(MEMORY_MACRO_COUNTS.values()),
            "baseline": sum(MEMORY_MACRO_COUNTS.values()),
        },
        "status": "eligible-for-pre-data-freeze-review",
        "performance": "not-measured",
        "nonclaim": "no synthesis, timing, area, energy, FPGA, ASIC, or silicon result",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--export-dir", type=Path, required=True)
    analyze.add_argument("--hierarchy", type=Path, required=True)
    analyze.add_argument("--flat", type=Path, required=True)
    analyze.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    concrete = subparsers.add_parser("analyze-concrete")
    concrete.add_argument("--hierarchy", type=Path, required=True)
    concrete.add_argument("--flat", type=Path, required=True)
    concrete.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    concrete.add_argument("--source-sha256", required=True)
    compare_concrete = subparsers.add_parser("compare-concrete")
    compare_concrete.add_argument("--integrated-report", type=Path, required=True)
    compare_concrete.add_argument("--baseline-report", type=Path, required=True)
    validate = subparsers.add_parser("validate-export")
    validate.add_argument("--export-dir", type=Path, required=True)
    validate.add_argument("--variant", choices=sorted(VARIANTS), required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--integrated-report", type=Path, required=True)
    compare.add_argument("--baseline-report", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "analyze":
        result = analyze_export(args.export_dir, args.hierarchy, args.flat, args.variant)
    elif args.command == "analyze-concrete":
        result = analyze_common_concrete_hierarchy(
            load_rtlil_hierarchy(args.hierarchy),
            args.variant,
            source_sha256=args.source_sha256,
            flat_document=load_json(args.flat),
        )
    elif args.command == "compare-concrete":
        result = compare_common_concrete_reports(
            load_json(args.integrated_report), load_json(args.baseline_report)
        )
    elif args.command == "validate-export":
        result = validate_export(args.export_dir, args.variant)
    else:
        result = compare_reports(
            load_json(args.integrated_report), load_json(args.baseline_report)
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
