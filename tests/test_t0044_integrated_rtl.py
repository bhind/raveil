import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from raveil.t0044_integrated_rtl import (
    CLOCK_ROOTS,
    MEMORY_MACRO_CONTRACT,
    MEMORY_MACRO_COUNTS,
    MEMORY_MACRO_PORTS,
    VARIANTS,
    analyze_clock_inventory,
    analyze_export,
    analyze_hierarchy,
    compare_reports,
    load_rtlil_hierarchy,
    validate_export,
    validate_prefreeze_identity_contract,
    validate_measurement_readiness_contract,
    validate_readiness_contract,
)
from raveil.t0044_physical import tree_sha256


ROOT = Path(__file__).parents[1]
HEX = "a" * 64


def hierarchy_document(*, graph: bool, rocket_count: int = 1):
    ports = {
        "clock_uncore": {"direction": "input", "bits": [1]},
        "jtag_TCK": {"direction": "input", "bits": [2]},
        "serial_tl_0_clock_in": {"direction": "input", "bits": [3]},
        "reset_io": {"direction": "input", "bits": [4]},
        "custom_boot": {"direction": "input", "bits": [5]},
        "axi4_mem_0_clock": {"direction": "output", "bits": [6]},
        "clock_tap": {"direction": "output", "bits": [7]},
    }
    system_type = "RaveilIntegratedGraphDigitalTop" if graph else "DigitalTop"
    top_cells = {"system": {"type": system_type}}
    system_cells = {
        "rocket": {"type": "Rocket"},
        "dcache": {"type": "DCache"},
        "xbar": {"type": "TLXbar"},
        "owned": {"type": "RaveilOwnedTLMemory"},
    }
    if rocket_count == 0:
        system_cells.pop("rocket")
    for index in range(1, rocket_count):
        system_cells[f"rocket_{index}"] = {"type": "Rocket"}
    if graph:
        system_cells["core"] = {"type": "RaveilStaticStencilCore"}
        system_cells["client"] = {"type": "RaveilStaticStencilTLClient"}
    for macro_name, count in MEMORY_MACRO_COUNTS.items():
        for index in range(count):
            system_cells[f"macro_{macro_name}_{index}"] = {"type": macro_name}
    modules = {
        "ChipTop": {"ports": ports, "cells": top_cells},
        system_type: {"cells": system_cells},
        "Rocket": {"ports": {"clock": {"direction": "input", "bits": [1]}}},
        "DCache": {"cells": {}},
        "TLXbar": {"cells": {}},
        "RaveilOwnedTLMemory": {
            "cells": {"fixture": {"type": "RaveilFixtureInputProvider"}}
        },
        "RaveilFixtureInputProvider": {"cells": {}},
    }
    if graph:
        modules["RaveilStaticStencilCore"] = {"cells": {}}
        modules["RaveilStaticStencilTLClient"] = {"cells": {}}
    for module_index, (macro_name, signature) in enumerate(MEMORY_MACRO_PORTS.items()):
        next_bit = 1000 + module_index * 1000
        ports = {}
        for port_name, (direction, width) in signature.items():
            ports[port_name] = {
                "direction": direction,
                "bits": list(range(next_bit, next_bit + width)),
            }
            next_bit += width
        modules[macro_name] = {"attributes": {"blackbox": "1"}, "ports": ports}
    return {"modules": modules}


def flat_document():
    ports = hierarchy_document(graph=True)["modules"]["ChipTop"]["ports"]
    return {
        "modules": {
            "ChipTop": {
                "ports": ports,
                "cells": {
                    "main_ff": {
                        "type": "$dff",
                        "port_directions": {"CLK": "input", "D": "input", "Q": "output"},
                        "connections": {"CLK": [1], "D": ["0"], "Q": [10]},
                    },
                    "jtag_ff": {
                        "type": "$adff",
                        "port_directions": {"CLK": "input", "ARST": "input", "D": "input", "Q": "output"},
                        "connections": {"CLK": [2], "ARST": [4], "D": ["0"], "Q": [11]},
                    },
                    "serial_memory": {
                        "type": "$mem_v2",
                        "port_directions": {"RD_CLK": "input", "WR_CLK": "input"},
                        "connections": {"RD_CLK": [3], "WR_CLK": ["0"]},
                    },
                },
            }
        }
    }


def write_export(root: Path, variant: str, *, rocket_text: str = "module Rocket; endmodule\n"):
    (root / "generated-src").mkdir(parents=True)
    (root / "generated-src/ChipTop.sv").write_text("module ChipTop; endmodule\n")
    (root / "generated-src/Rocket.sv").write_text(rocket_text)
    (root / "ChipTop.top.f").write_text("generated-src/ChipTop.sv\ngenerated-src/Rocket.sv\n")
    (root / "rtl-files.txt").write_text("generated-src/ChipTop.sv\ngenerated-src/Rocket.sv\n")
    (root / "pre-firtool.fir").write_text("circuit ChipTop:\n")
    (root / "top-module-hierarchy.json").write_text("{}\n")
    (root / "lowering-provenance.txt").write_text("status=shared-elaboration-identical\n")
    macro_contract = "\n".join(MEMORY_MACRO_CONTRACT.values()) + "\n"
    (root / "memory-macro-contract.txt").write_text(macro_contract)
    rocket_hash = hashlib.sha256(rocket_text.encode()).hexdigest()
    metadata = {
        "schema": "raveil.exp-0011-rtl-export/v1",
        "variant": variant,
        "config": VARIANTS[variant],
        "top": "ChipTop",
        "performance": "not-measured",
        "chipyard_revision": "chipyard-revision",
        "rocket_revision": "rocket-revision",
        "image_id": "sha256:" + HEX,
        "normal_lowering": "normal",
        "physical_lowering": "physical",
        "rocket_rtl_sha256": rocket_hash,
        "memory_macro_contract_sha256": hashlib.sha256(macro_contract.encode()).hexdigest(),
    }
    for field in ("source_sha256", "input_sha256", "runner_sha256", "lock_sha256", "image_rootfs_sha256"):
        metadata[field] = HEX
    metadata.update({
        "rtl_sha256": tree_sha256(root / "generated-src"),
        "rtl_filelist_sha256": hashlib.sha256((root / "rtl-files.txt").read_bytes()).hexdigest(),
        "firrtl_sha256": hashlib.sha256((root / "pre-firtool.fir").read_bytes()).hexdigest(),
        "hierarchy_sha256": hashlib.sha256((root / "top-module-hierarchy.json").read_bytes()).hexdigest(),
        "lowering_provenance_sha256": hashlib.sha256((root / "lowering-provenance.txt").read_bytes()).hexdigest(),
    })
    (root / "export-metadata.json").write_text(json.dumps(metadata))


def readiness_contract():
    macro_views = [
        {
            "name": name,
            "liberty_sha256": HEX,
            "lef_sha256": "b" * 64,
            "pvt": "ss_0p72v_125c",
            "rc_corner": "rcworst",
        }
        for name in sorted(MEMORY_MACRO_CONTRACT)
    ]
    return {
        "schema": "raveil.t0044-integrated-physical-readiness/v1",
        "experiment_id": None,
        "freeze_state": "unfrozen",
        "estimand_overhead": {
            "estimand": "area and slack under one normalized boundary",
            "components": {
                "graph_candidate": ["graph_core"],
                "rocket_candidate": ["rocket_core"],
                "common": ["clock_reset", "owned_memory", "interconnect"],
            },
            "dynamic_traffic_difference": {
                "represented": True,
                "asserted_equal": False,
            },
        },
        "connectivity": {
            "common_modules": [
                {"name": "clock_reset"},
                {"name": "owned_memory"},
                {"name": "interconnect"},
            ],
            "deltas": [{"name": "graph_core"}, {"name": "rocket_core"}],
            "ownership": {
                "clock_reset": "common",
                "owned_memory": "common",
                "interconnect": "common",
                "graph_core": "graph",
                "rocket_core": "rocket",
            },
        },
        "clock_reset": {
            "clock_endpoints": ["integrated.clock_uncore", "matched.clock_uncore"],
            "period": 40.0,
            "waveform": {"rising_edge": 0.0, "duty_cycle": 0.5},
            "reset": {
                "polarity": "active_high",
                "synchrony": "synchronous",
                "coverage": "all_sequential_state",
            },
        },
        "memory_macro_views": {"macros": macro_views},
        "repetitions": {
            "count": 2,
            "seeds": [101, 202],
            "inference_unit": "fresh implementation seed",
            "uncertainty_policy": "report all observations and estimator",
            "interval_95_policy": "predeclared percentile interval",
            "campaign_policy": "new integrated physical campaign",
        },
        "append_only_controls": {
            "raw_derived_separation": True,
            "hashes": ["sha256"],
            "append_before_seal": True,
            "immutable_after_seal": True,
            "raw_seal_steps": [
                "write_raw_once",
                "hash_raw_sha256",
                "seal_raw",
                "verify_raw_immutable",
            ],
            "derived_seal_steps": [
                "read_sealed_raw",
                "write_derived_once",
                "hash_derived_sha256",
                "seal_derived",
                "verify_derived_immutable",
            ],
            "stop": [
                "oracle_mismatch",
                "resource_inequality",
                "unexplained_traffic",
                "accounting_missing",
                "source_config_drift",
                "incomplete_matrix",
                "execution_window_mismatch",
            ],
            "pause": ["fairness_unresolved"],
            "no_go": [
                "fair_common_conditions_impossible",
                "integrated_hierarchy_not_closed",
                "candidate_only_condition_required",
                "evidence_integrity_failure",
            ],
            "advance": ["contract_review_passed"],
        },
    }


def prefixed_hex(character):
    return character * 64


def prefreeze_contract():
    variant_identities = {
        variant: {
            "config": config, "rtl_tree_sha256": prefixed_hex("a"),
            "rtl_filelist_sha256": prefixed_hex("b"), "firrtl_sha256": prefixed_hex("c"),
            "lowering_provenance_sha256": prefixed_hex("d"), "source_sha256": prefixed_hex("e"),
            "input_sha256": prefixed_hex("f"), "rocket_canonical_module_sha256": prefixed_hex("1"),
            "memory_macro_contract_sha256": prefixed_hex("2"),
        } for variant, config in VARIANTS.items()
    }
    roles = {
        "fixture_provider": "common", "owned_memory": "common",
        "cache_interconnect": "common", "clock_reset": "common",
        "private_output_validation": "common", "rocket_fallback": "rocket_fallback",
        "graph_core": "graph_delta", "graph_tl_client": "graph_delta",
        "selector_adapter": "graph_delta",
    }
    integrated, matched = VARIANTS
    ledger = []
    for number, (name, role) in enumerate(roles.items()):
        graph = role == "graph_delta"
        ledger.append({
            "name": name, "role": role,
            "inclusion": {integrated: True, matched: not graph},
            "instance_paths": {integrated: ["system/" + name], matched: [] if graph else ["system/" + name]},
            "module_sha256": {integrated: prefixed_hex(format(number, "x")), matched: None if graph else prefixed_hex(format(number, "x"))},
            "accounting_owner": role,
            "activity_scope": "idle_when_graph_active_and_active_when_selected" if name == "rocket_fallback" else "active_when_graph_selected" if graph else "included_both_candidates",
        })
    return {
        "schema": "raveil.t0044-integrated-physical-prefreeze/v2",
        "experiment_id": None, "freeze_state": "unfrozen",
        "readiness": readiness_contract(),
        "identity": {
            "implementation_authority_commit": "3" * 40, "top": "ChipTop",
            "variants": variant_identities,
            "preflight": {"comparison_sha256": prefixed_hex("4"), "raw_manifest_sha256": prefixed_hex("5"), "derived_manifest_sha256": prefixed_hex("6")},
            "toolchain": {"generator_image": "sha256:" + prefixed_hex("7"), "generator_rootfs_sha256": prefixed_hex("8"), "physical_image": "sha256:" + prefixed_hex("9"), "physical_rootfs_sha256": prefixed_hex("a"), "lock_sha256": prefixed_hex("b"), "yosys_sha256": prefixed_hex("c"), "opensta_sha256": prefixed_hex("d"), "standard_cell_liberty_sha256": prefixed_hex("e"), "tech_lef_sha256": prefixed_hex("f"), "sdc_sha256": prefixed_hex("1")},
        },
        "component_ledger": ledger,
        "workload_oracle": {"operation": "uint32_stencil_5_point_bounded", "input_words": 324, "output_words": 256, "comparison": "all_words_plus_checksum", "artifact_sha256": prefixed_hex("a"), "input_generator_sha256": prefixed_hex("b"), "oracle_sha256": prefixed_hex("c"), "simulator_sha256": prefixed_hex("d"), "input_schedule": "candidate_blind_deterministic", "oracle_access": "inaccessible_to_candidates", "lifecycle": ["installation", "staging", "execution", "drain_completion", "validation", "publication"]},
        "budget_policy": {"traffic_equal": False, "unequal_traffic_disclosed": True, "lawful_candidate_optimization": True, "cpu_load_reuse_explicit": True, "common_resource_equality_required": True, "execution_window": "installation_through_drain_completion_excluding_validation_publication", "accounting_fields": ["useful_load", "useful_add", "useful_store", "useful_output", "admitted_read", "completed_read", "admitted_write", "completed_write", "bytes", "stall", "backpressure"]},
        "physical_conditions": {"common_to_variants": True, "clock": {"port": "clock_uncore", "period": 40.0, "waveform": [0.0, 20.0]}, "input_delay": 1.0, "output_delay": 1.0, "standard_cell_pvt": "ss_0p72v_125c", "rc_corner": "rcworst", "load_model_sha256": prefixed_hex("a"), "drive_model_sha256": prefixed_hex("b"), "generated_clocks": [], "false_paths": [], "multicycle_paths": [], "sdc_sha256": prefixed_hex("1")},
        "evidence_scope": {"current_evidence": "host-contract-validation-only", "target": "integrated-place-and-route-area-timing", "p_and_r_required_before_area_timing_claim": True, "physical_disclosures": ["floorplan", "die", "core", "utilization", "placement_seed", "routing", "parasitic_identity"], "energy_claim": {"enabled": False, "status": "not-measured"}, "thermal": {"applicable": False, "prohibits_energy_device_inference": True}, "performance_claim": False, "fpga_claim": False, "asic_claim": False, "silicon_claim": False},
    }


def measurement_contract():
    prefreeze = prefreeze_contract()
    prefreeze["readiness"]["repetitions"].update({"inference_unit": "paired_physical_flow_seed", "uncertainty_policy": "controlled_paired_seed_sensitivity_only", "interval_95_policy": "unavailable_not_imputed"})
    return {"schema": "raveil.t0044-integrated-physical-measurement-readiness/v3", "experiment_id": None, "freeze_state": "unfrozen", "prefreeze": prefreeze,
        "measurement_design": {"matrix": list(VARIANTS), "physical_flow_seeds": [101, 202], "run_order": [[101, "integrated-static-graph-rocket"], [101, "matched-rocket-system"], [202, "matched-rocket-system"], [202, "integrated-static-graph-rocket"]], "pairing": {"same_seed_constraints_toolchain": True, "fresh_synthesis_and_pnr_per_pair": True, "raw_result_import": False, "deterministic_reruns_reproducibility_only": True, "reruns_are_samples": False}, "stages": ["synthesis", "floorplan", "placement", "clock_tree", "routing", "parasitic_extraction", "sta"], "scope": {"dynamic_latency_traffic_campaign": "not_in_scope_not_reopened", "energy": "not_in_scope", "boom": "not_in_scope", "cgra": "not_in_scope"}, "repetition_policy": {"runs_per_variant": 2, "inference_unit": "paired_physical_flow_seed", "uncertainty": "controlled_paired_seed_sensitivity_only", "ci_95": "unavailable_not_imputed", "reruns": "reproducibility_only_not_samples"}},
        "estimator_policy": {"area": {"required_fields": ["integrated_total_area", "matched_total_area", "graph_delta_component_area", "matched_rocket_component_area"], "ratio_formula": "graph_delta_component_area/matched_rocket_component_area", "absolute_totals_reported": True, "summary": "per_seed_ratio_and_median_of_paired_seed_ratios_descriptive"}, "timing": {"metric": "worst_setup_slack_ns", "period_ns": 40.0, "same_sdc_pvt_rc": True, "report_each_candidate_seed": True, "meet_iff": "slack>=0"}, "uncertainty": {"kind": "controlled_paired_seed_sensitivity_only", "ci_95": "unavailable_not_imputed", "deterministic_reruns_independent_samples": False}},
        "decision_policy": {"stop": ["oracle_mismatch", "resource_inequality", "unexplained_traffic", "accounting_missing", "identity_config_tool_drift", "incomplete_matrix", "window_mismatch", "physical_stage_closure_missing", "seal_failure"], "no_go": ["any_area_ratio_gt_0.25", "integrated_misses_40ns_matched_meets", "candidate_only_condition_needed", "rtl_regeneration_configurability_reinvention_dependency_needed"], "pause": ["matched_misses_or_both_miss", "required_physical_input_component_unavailable", "pnr_closure_ambiguous", "fairness_boundary_unresolved"], "advance": {"name": "advance_partial_integrated_physical", "requires": ["every_pair_stage_seal_complete", "both_meet_40ns", "every_area_ratio_lte_0.25", "equality_fairness_pass", "missing_dimensions_explicit"]}, "prohibitions": ["generic_go", "t0044_close", "product_hardware_claim", "adaptive_threshold_target_sweep_change"], "energy": {"status": "not_evaluable_in_s12", "threshold_0.90_active": False}},
        "evidence_protocol": {"run": "immutable_new_run_id_per_attempt", "raw": ["frozen_manifest", "command_environment_exit", "identity_snapshot", "physical_stage_reports", "component_area_ledger", "timing_paths_constraints", "file_map"], "raw_seal": ["relative_path", "bytes", "sha256", "manifest", "run_id"], "derived": "reads_only_sealed_raw_writes_once", "result_seal": ["raw_seal", "report", "derived_file_map"], "failed_attempt": "retain_failed_raw_seal_no_eligible_derived_claim", "recovery": "new_run_id_binds_failed_seal_imported_hashes_exact_rerun_imports_not_samples", "promotion": "immutable_remote_copy_one_way_download_verify_marker_last_tracked_non_sensitive_receipt", "prohibitions": ["credentials", "absolute_paths"], "scientific_field_change": "requires_new_predata_freeze"}}


class TestIntegratedRTL(unittest.TestCase):
    def test_s12_measurement_readiness_contract_valid(self):
        document = measurement_contract()
        self.assertEqual(validate_measurement_readiness_contract(document)["status"], "ready-for-review")
        document.pop("experiment_id")
        self.assertEqual(validate_measurement_readiness_contract(document)["experiment_id"], None)
        for key, value in (("experiment_id", "EXP-0011"), ("freeze_state", "frozen"), ("results", {})):
            document = measurement_contract(); document[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate_measurement_readiness_contract(document)

    def test_s12_rejects_design_estimator_and_scope_drift(self):
        mutations = (
            lambda d: d["measurement_design"].__setitem__("matrix", ["matched-rocket-system"]),
            lambda d: d["measurement_design"].__setitem__("physical_flow_seeds", [101, 303]),
            lambda d: d["measurement_design"]["run_order"].reverse(),
            lambda d: d["measurement_design"]["pairing"].__setitem__("reruns_are_samples", True),
            lambda d: d["measurement_design"]["stages"].pop(),
            lambda d: d["measurement_design"]["scope"].__setitem__("energy", "in_scope"),
            lambda d: d["measurement_design"]["repetition_policy"].__setitem__("ci_95", "percentile_bootstrap"),
            lambda d: d["prefreeze"]["readiness"]["repetitions"].__setitem__("interval_95_policy", "percentile_bootstrap"),
            lambda d: d["estimator_policy"]["area"].__setitem__("ratio_formula", "total_area_ratio"),
            lambda d: d["estimator_policy"]["timing"].__setitem__("period_ns", 20.0),
        )
        for mutation in mutations:
            document = measurement_contract(); mutation(document)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): validate_measurement_readiness_contract(document)

    def test_s12_rejects_decision_and_evidence_protocol_drift(self):
        mutations = (
            lambda d: d["decision_policy"]["stop"].pop(),
            lambda d: d["decision_policy"]["stop"].append("seal_failure"),
            lambda d: d["decision_policy"]["no_go"].append("adaptive_threshold"),
            lambda d: d["decision_policy"]["advance"]["requires"].pop(),
            lambda d: d["decision_policy"]["energy"].__setitem__("threshold_0.90_active", True),
            lambda d: d["evidence_protocol"]["raw"].pop(),
            lambda d: d["evidence_protocol"].__setitem__("failed_attempt", "discard_failed_run"),
            lambda d: d["evidence_protocol"].__setitem__("recovery", "reuse_run_id"),
            lambda d: d["evidence_protocol"]["prohibitions"].pop(),
        )
        for mutation in mutations:
            document = measurement_contract(); mutation(document)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): validate_measurement_readiness_contract(document)

    def test_s11_prefreeze_identity_contract_valid(self):
        document = prefreeze_contract()
        self.assertEqual(validate_prefreeze_identity_contract(document)["status"], "ready-for-review")
        document.pop("experiment_id")
        self.assertEqual(validate_prefreeze_identity_contract(document)["experiment_id"], None)

    def test_s11_rejects_top_level_and_identity_drift(self):
        cases = []
        for mutation in (
            lambda d: d.__setitem__("results", {}),
            lambda d: d.__setitem__("unknown", True),
            lambda d: d.__setitem__("experiment_id", ""),
            lambda d: d.__setitem__("freeze_state", "frozen"),
            lambda d: d["identity"].__setitem__("unknown", True),
            lambda d: d["identity"].__setitem__("top", "OtherTop"),
            lambda d: d["identity"].__setitem__("implementation_authority_commit", "TBD"),
            lambda d: d["identity"]["variants"].pop("matched-rocket-system"),
            lambda d: d["identity"]["variants"]["integrated-static-graph-rocket"].__setitem__("config", "wrong"),
            lambda d: d["identity"]["variants"]["matched-rocket-system"].__setitem__("rocket_canonical_module_sha256", "0" * 64),
            lambda d: d["identity"]["toolchain"].pop("generator_rootfs_sha256"),
            lambda d: d["identity"]["toolchain"].__setitem__("generator_image", "sha256:" + "z" * 64),
            lambda d: d["identity"]["toolchain"].__setitem__("physical_rootfs_sha256", "0" * 63),
            lambda d: d["identity"]["toolchain"].__setitem__("physical_image", "not-a-hash"),
            lambda d: d["readiness"]["clock_reset"].__setitem__("unknown", True),
        ):
            document = prefreeze_contract(); mutation(document); cases.append(document)
        for document in cases:
            with self.subTest(document=document), self.assertRaises(ValueError):
                validate_prefreeze_identity_contract(document)

    def test_s11_rejects_ledger_or_workload_drift(self):
        cases = []
        for mutation in (
            lambda d: d.__setitem__("component_ledger", d["component_ledger"][:-1]),
            lambda d: d["component_ledger"][0].__setitem__("extra", True),
            lambda d: d["component_ledger"][0]["inclusion"].__setitem__("matched-rocket-system", False),
            lambda d: d["component_ledger"][0]["module_sha256"].__setitem__("matched-rocket-system", "f" * 64),
            lambda d: d["component_ledger"][0]["instance_paths"].__setitem__("integrated-static-graph-rocket", ["TBD"]),
            lambda d: d["component_ledger"][0].__setitem__("accounting_owner", "graph_delta"),
            lambda d: d["component_ledger"][6]["instance_paths"].__setitem__("matched-rocket-system", ["bad"]),
            lambda d: d["component_ledger"][5].__setitem__("activity_scope", "bounded_execution"),
            lambda d: d["workload_oracle"].__setitem__("input_words", 323),
            lambda d: d["workload_oracle"].__setitem__("oracle_sha256", "a" * 64),
            lambda d: d["workload_oracle"].__setitem__("oracle_access", "candidate_visible"),
            lambda d: d["workload_oracle"]["lifecycle"].pop(),
        ):
            document = prefreeze_contract(); mutation(document); cases.append(document)
        for document in cases:
            with self.subTest(document=document), self.assertRaises(ValueError):
                validate_prefreeze_identity_contract(document)

    def test_s11_rejects_budget_physical_and_claim_drift(self):
        cases = []
        for mutation in (
            lambda d: d["budget_policy"].__setitem__("traffic_equal", True),
            lambda d: d["budget_policy"].pop("cpu_load_reuse_explicit"),
            lambda d: d["budget_policy"]["accounting_fields"].pop(),
            lambda d: d["physical_conditions"].__setitem__("sdc_sha256", "0" * 64),
            lambda d: d["physical_conditions"]["clock"].__setitem__("period", True),
            lambda d: d["physical_conditions"].__setitem__("common_to_variants", False),
            lambda d: d["physical_conditions"].__setitem__("false_paths", [True]),
            lambda d: d["readiness"]["memory_macro_views"]["macros"][0].__setitem__("pvt", "ff_0p88v_0c"),
            lambda d: d["readiness"]["memory_macro_views"]["macros"][0].__setitem__("rc_corner", "rcbest"),
            lambda d: d["evidence_scope"].__setitem__("performance_claim", True),
            lambda d: d["evidence_scope"].__setitem__("energy_claim", {"enabled": True, "status": "measured"}),
            lambda d: d["evidence_scope"]["physical_disclosures"].pop(),
        ):
            document = prefreeze_contract(); mutation(document); cases.append(document)
        for document in cases:
            with self.subTest(document=document), self.assertRaises(ValueError):
                validate_prefreeze_identity_contract(document)

    def test_s10_readiness_contract_valid(self):
        contract = readiness_contract()
        self.assertEqual(validate_readiness_contract(contract)["status"], "ready-for-review")
        contract.pop("experiment_id")
        self.assertEqual(validate_readiness_contract(contract)["experiment_id"], None)

    def test_s10_readiness_rejects_top_level_drift_and_claim_data(self):
        mutations = []
        for field in ("clock_reset", "repetitions"):
            document = readiness_contract()
            document.pop(field)
            mutations.append((f"missing-{field}", document))
        for field in ("unknown", "results", "measurements", "claims"):
            document = readiness_contract()
            document[field] = {}
            mutations.append((f"forbidden-{field}", document))
        document = readiness_contract()
        document["experiment_id"] = ""
        mutations.append(("empty-experiment-id", document))
        document = readiness_contract()
        document["freeze_state"] = "frozen"
        mutations.append(("premature-freeze", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_overhead_and_traffic_drift(self):
        mutations = []
        document = readiness_contract()
        document["estimand_overhead"].pop("estimand")
        mutations.append(("missing-estimand", document))
        document = readiness_contract()
        document["estimand_overhead"]["extra"] = True
        mutations.append(("unknown-overhead-field", document))
        document = readiness_contract()
        document["estimand_overhead"]["components"].pop("common")
        mutations.append(("missing-common-ledger", document))
        document = readiness_contract()
        document["estimand_overhead"]["components"]["common"].append("graph_core")
        mutations.append(("duplicate-ledger-owner", document))
        for field, value in (("represented", False), ("asserted_equal", True)):
            document = readiness_contract()
            document["estimand_overhead"]["dynamic_traffic_difference"][field] = value
            mutations.append((f"traffic-{field}", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_connectivity_drift(self):
        mutations = []
        document = readiness_contract()
        document["connectivity"]["deltas"].append({"name": "graph_core"})
        mutations.append(("duplicate-within-delta", document))
        document = readiness_contract()
        document["connectivity"]["deltas"].append({"name": "owned_memory"})
        mutations.append(("duplicate-across-boundaries", document))
        document = readiness_contract()
        document["connectivity"]["common_modules"][0]["kind"] = "clock"
        mutations.append(("unknown-component-field", document))
        document = readiness_contract()
        document["connectivity"]["ownership"].pop("graph_core")
        mutations.append(("missing-owner", document))
        document = readiness_contract()
        document["connectivity"]["ownership"]["owned_memory"] = "graph"
        mutations.append(("common-owned-by-candidate", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_clock_and_reset_drift(self):
        mutations = []
        document = readiness_contract()
        document["clock_reset"]["period"] = True
        mutations.append(("boolean-period", document))
        document = readiness_contract()
        document["clock_reset"]["period"] = float("inf")
        mutations.append(("infinite-period", document))
        document = readiness_contract()
        document["clock_reset"]["clock_endpoints"].append("integrated.clock_uncore")
        mutations.append(("duplicate-endpoint", document))
        document = readiness_contract()
        document["clock_reset"]["waveform"]["falling_edge"] = 20.0
        mutations.append(("unknown-waveform-field", document))
        document = readiness_contract()
        document["clock_reset"]["reset"]["coverage"] = "unknown"
        mutations.append(("unknown-reset-coverage", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_incomplete_macro_identity(self):
        mutations = []
        document = readiness_contract()
        document["memory_macro_views"]["macros"].pop()
        mutations.append(("missing-macro", document))
        document = readiness_contract()
        document["memory_macro_views"]["macros"][0]["liberty_sha256"] = "TBD"
        mutations.append(("placeholder-liberty", document))
        document = readiness_contract()
        document["memory_macro_views"]["macros"][0].pop("lef_sha256")
        mutations.append(("missing-lef", document))
        document = readiness_contract()
        document["memory_macro_views"]["macros"][1]["name"] = document["memory_macro_views"]["macros"][0]["name"]
        mutations.append(("duplicate-macro", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_weak_repetition_policy(self):
        mutations = []
        document = readiness_contract()
        document["repetitions"]["seeds"] = [101, 101]
        mutations.append(("duplicate-seed", document))
        document = readiness_contract()
        document["repetitions"]["seeds"] = [101, "202"]
        mutations.append(("non-integer-seed", document))
        document = readiness_contract()
        document["repetitions"]["campaign_policy"] = "EXP-0008"
        mutations.append(("reused-exp-0008", document))
        document = readiness_contract()
        document["repetitions"].pop("interval_95_policy")
        mutations.append(("missing-interval", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_mutable_or_incomplete_seals(self):
        mutations = []
        document = readiness_contract()
        document["append_only_controls"]["immutable_after_seal"] = False
        mutations.append(("mutable-after-seal", document))
        document = readiness_contract()
        document["append_only_controls"]["raw_seal_steps"].append("append_after_seal")
        mutations.append(("post-seal-append", document))
        document = readiness_contract()
        document["append_only_controls"]["derived_seal_steps"].reverse()
        mutations.append(("reordered-derived-seal", document))
        document = readiness_contract()
        document["append_only_controls"]["hashes"] = ["sha512"]
        mutations.append(("wrong-hash", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_s10_readiness_rejects_incomplete_or_unknown_decision_rules(self):
        mutations = []
        document = readiness_contract()
        document["append_only_controls"]["stop"].remove("oracle_mismatch")
        mutations.append(("incomplete-stop", document))
        document = readiness_contract()
        document["append_only_controls"]["stop"].append("ignore_oracle")
        mutations.append(("unknown-stop", document))
        document = readiness_contract()
        document["append_only_controls"]["pause"] = []
        mutations.append(("empty-pause", document))
        document = readiness_contract()
        document["append_only_controls"]["no_go"].pop()
        mutations.append(("incomplete-no-go", document))
        document = readiness_contract()
        document["append_only_controls"]["advance"].append("contract_review_passed")
        mutations.append(("duplicate-advance", document))
        for label, document in mutations:
            with self.subTest(label=label), self.assertRaises(ValueError):
                validate_readiness_contract(document)

    def test_recursive_integrated_hierarchy(self):
        report = analyze_hierarchy(hierarchy_document(graph=True), "integrated-static-graph-rocket")
        self.assertEqual(report["rocket_instance_path"], "system/rocket")
        self.assertEqual(report["blackboxes"], len(MEMORY_MACRO_CONTRACT))

    def test_matched_baseline_excludes_graph(self):
        report = analyze_hierarchy(hierarchy_document(graph=False), "matched-rocket-system")
        self.assertFalse(any(report["graph_paths"].values()))

    def test_rocket_must_be_exactly_one(self):
        for count in (0, 2):
            with self.subTest(count=count), self.assertRaises(ValueError):
                analyze_hierarchy(
                    hierarchy_document(graph=True, rocket_count=count),
                    "integrated-static-graph-rocket",
                )

    def test_graph_presence_is_variant_specific(self):
        with self.assertRaises(ValueError):
            analyze_hierarchy(hierarchy_document(graph=False), "integrated-static-graph-rocket")
        with self.assertRaises(ValueError):
            analyze_hierarchy(hierarchy_document(graph=True), "matched-rocket-system")

    def test_reachable_blackbox_fails(self):
        document = hierarchy_document(graph=True)
        document["modules"]["Rocket"]["attributes"] = {"blackbox": "1"}
        with self.assertRaisesRegex(ValueError, "blackbox"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_memory_macro_boundary_requires_exact_count_and_ports(self):
        document = hierarchy_document(graph=True)
        document["modules"]["RaveilIntegratedGraphDigitalTop"]["cells"].pop(
            "macro_cc_dir_ext_0"
        )
        with self.assertRaisesRegex(ValueError, "memory-macro"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")
        document = hierarchy_document(graph=True)
        document["modules"]["cc_dir_ext"]["ports"]["RW0_addr"]["bits"].append(99999)
        with self.assertRaisesRegex(ValueError, "port contract drift"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_required_component_and_port_fail_closed(self):
        document = hierarchy_document(graph=True)
        document["modules"]["RaveilIntegratedGraphDigitalTop"]["cells"].pop("xbar")
        with self.assertRaisesRegex(ValueError, "interconnect"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")
        document = hierarchy_document(graph=True)
        document["modules"]["ChipTop"]["ports"].pop("custom_boot")
        with self.assertRaisesRegex(ValueError, "required ports"):
            analyze_hierarchy(document, "integrated-static-graph-rocket")

    def test_three_clock_roots_cover_sequential_and_memory_endpoints(self):
        report = analyze_clock_inventory(flat_document())
        self.assertEqual(report["allowed_roots"], sorted(CLOCK_ROOTS))
        self.assertEqual(report["sequential_endpoint_count"], 3)

    def test_rtlil_hierarchy_loader_keeps_only_structural_identity(self):
        text = """attribute \\top 1
module \\ChipTop
  wire input 1 \\clock_uncore
  wire width 2 output 2 \\out
  cell \\Rocket \\rocket
    connect \\clock \\clock_uncore
  end
  process $proc$ignored
  end
end
attribute \\blackbox 1
module \\Rocket
  wire input 1 \\clock
end
"""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "hierarchy.rtlil"
            path.write_text(text)
            document = load_rtlil_hierarchy(path)
        self.assertEqual(document["modules"]["ChipTop"]["cells"]["\\rocket"]["type"], "Rocket")
        self.assertEqual(len(document["modules"]["ChipTop"]["ports"]["out"]["bits"]), 2)

    def test_rtlil_canonical_hash_elides_only_yosys_auto_ids_and_unit_order(self):
        def rocket_rtlil(
            first_id: int,
            *,
            reverse: bool,
            width: int = 1,
            source_line: int = 10,
            cell_type: str = "$and",
            input_name: str = "named_input",
        ) -> str:
            units = [
                (
                    f'  attribute \\src "generated-src/Rocket.sv:{source_line}.1-{source_line}.8"\n'
                    f"  wire $and$generated-src/Rocket.sv:{source_line}${first_id}_Y"
                ),
                (
                    f'  attribute \\src "generated-src/Rocket.sv:{source_line}.1-{source_line}.8"\n'
                    f"  cell {cell_type} $and$generated-src/Rocket.sv:{source_line}${first_id}\n"
                    f"    parameter \\Y_WIDTH {width}\n"
                    f"    connect \\A \\{input_name}\n"
                    f"    connect \\Y $and$generated-src/Rocket.sv:{source_line}${first_id}_Y\n"
                    "  end"
                ),
            ]
            if reverse:
                units.reverse()
            return "module \\Rocket\n" + "\n".join(units) + "\nend\n"

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a_path, b_path = root / "a.rtlil", root / "b.rtlil"
            a_path.write_text(rocket_rtlil(101, reverse=False))
            b_path.write_text(rocket_rtlil(9021, reverse=True))
            a = load_rtlil_hierarchy(a_path)["modules"]["Rocket"]
            b = load_rtlil_hierarchy(b_path)["modules"]["Rocket"]
            drifts = []
            for index, kwargs in enumerate((
                {"width": 2},
                {"source_line": 11},
                {"cell_type": "$or"},
                {"input_name": "other_input"},
            )):
                drift_path = root / f"drift-{index}.rtlil"
                drift_path.write_text(rocket_rtlil(9021, reverse=True, **kwargs))
                drifts.append(
                    load_rtlil_hierarchy(drift_path)["modules"]["Rocket"]
                )
        self.assertNotEqual(a["rtlil_raw_sha256"], b["rtlil_raw_sha256"])
        self.assertEqual(a["rtlil_canonical_sha256"], b["rtlil_canonical_sha256"])
        for drift in drifts:
            self.assertNotEqual(
                a["rtlil_canonical_sha256"], drift["rtlil_canonical_sha256"]
            )

    def test_rtlil_canonical_hash_reorders_only_safe_process_runs(self):
        def process_rtlil(*, reverse: bool = False, clock: str = r"\clock") -> str:
            assigns = [
                "    assign $0\\a[0:0] \\a\n",
                "    assign $0\\b[0:0] \\b\n",
            ]
            updates = [
                "      update \\a $0\\a[0:0]\n",
                "      update \\b $0\\b[0:0]\n",
            ]
            if reverse:
                assigns.reverse()
                updates.reverse()
            return (
                "module \\Rocket\n  wire \\a\n  wire \\b\n"
                "  attribute \\src \"generated-src/Rocket.sv:1\"\n"
                "  process $proc\n"
                + "".join(assigns)
                + "    switch \\sel\n      case 1'1\n"
                + "        assign $0\\guard \\guarded\n      end\n    end\n"
                + f"    sync posedge {clock}\n"
                + "".join(updates)
                + "  end\nend\n"
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            same_a = root / "same-a.rtlil"
            same_b = root / "same-b.rtlil"
            same_a.write_text(process_rtlil())
            same_b.write_text(process_rtlil(reverse=True))
            base = load_rtlil_hierarchy(same_a)["modules"]["Rocket"]
            reordered = load_rtlil_hierarchy(same_b)["modules"]["Rocket"]
            self.assertEqual(
                base["rtlil_canonical_sha256"], reordered["rtlil_canonical_sha256"]
            )
            clock_drift = root / "clock-drift.rtlil"
            clock_drift.write_text(process_rtlil(clock=r"\other_clock"))
            self.assertNotEqual(
                base["rtlil_canonical_sha256"],
                load_rtlil_hierarchy(clock_drift)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
            )

            duplicate_a = root / "duplicate-a.rtlil"
            duplicate_b = root / "duplicate-b.rtlil"
            duplicate_prefix = "module \\Rocket\n  process $proc\n"
            duplicate_suffix = "  end\nend\n"
            first = "    assign $0\\a[0:0] \\x\n"
            second = "    assign $0\\a[0:0] \\y\n"
            duplicate_a.write_text(
                duplicate_prefix + first + second + duplicate_suffix
            )
            duplicate_b.write_text(
                duplicate_prefix + second + first + duplicate_suffix
            )
            self.assertNotEqual(
                load_rtlil_hierarchy(duplicate_a)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
                load_rtlil_hierarchy(duplicate_b)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
            )

            dependent_a = root / "dependent-a.rtlil"
            dependent_b = root / "dependent-b.rtlil"
            dependent = "    assign $0\\b[0:0] $0\\a[0:0]\n"
            dependent_a.write_text(
                duplicate_prefix + first + dependent + duplicate_suffix
            )
            dependent_b.write_text(
                duplicate_prefix + dependent + first + duplicate_suffix
            )
            self.assertNotEqual(
                load_rtlil_hierarchy(dependent_a)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
                load_rtlil_hierarchy(dependent_b)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
            )

            update_a = root / "update-a.rtlil"
            update_b = root / "update-b.rtlil"
            update_prefix = duplicate_prefix + "    sync posedge \\clock\n"
            update_first = "      update \\a \\x\n"
            update_second = "      update \\a \\y\n"
            update_a.write_text(
                update_prefix + update_first + update_second + duplicate_suffix
            )
            update_b.write_text(
                update_prefix + update_second + update_first + duplicate_suffix
            )
            self.assertNotEqual(
                load_rtlil_hierarchy(update_a)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
                load_rtlil_hierarchy(update_b)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
            )

            boundary_a = root / "boundary-a.rtlil"
            boundary_b = root / "boundary-b.rtlil"
            boundary = "    switch \\sel\n      case 1'1\n      end\n    end\n"
            boundary_a.write_text(
                duplicate_prefix + "    assign $0\\a \\x\n" + boundary
                + "    assign $0\\b \\y\n" + duplicate_suffix
            )
            boundary_b.write_text(
                duplicate_prefix + "    assign $0\\b \\y\n" + boundary
                + "    assign $0\\a \\x\n" + duplicate_suffix
            )
            self.assertNotEqual(
                load_rtlil_hierarchy(boundary_a)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
                load_rtlil_hierarchy(boundary_b)["modules"]["Rocket"][
                    "rtlil_canonical_sha256"
                ],
            )

            def switch_rtlil(selector: str, case_value: str) -> str:
                return (
                    "module \\Rocket\n  wire \\q\n  process $proc\n"
                    f"    switch {selector}\n      case {case_value}\n"
                    "        assign $0\\q \\d\n      end\n    end\n  end\nend\n"
                )

            switch_a = root / "switch-a.rtlil"
            switch_a.write_text(switch_rtlil(r"\sel", "1'1"))
            switch_base = load_rtlil_hierarchy(switch_a)["modules"]["Rocket"]
            for index, args in enumerate(((r"\other", "1'1"), (r"\sel", "1'0"))):
                switch_drift = root / f"switch-drift-{index}.rtlil"
                switch_drift.write_text(switch_rtlil(*args))
                self.assertNotEqual(
                    switch_base["rtlil_canonical_sha256"],
                    load_rtlil_hierarchy(switch_drift)["modules"]["Rocket"][
                        "rtlil_canonical_sha256"
                    ],
                )

    def test_gated_clock_traces_only_approved_clock_root(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["gate"] = {
            "type": "$and",
            "port_directions": {"A": "input", "B": "input", "Y": "output"},
            "connections": {"A": [1], "B": [5], "Y": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        report = analyze_clock_inventory(document)
        self.assertEqual(report["root_endpoint_counts"]["clock_uncore"], 1)
        self.assertEqual(report["derived_clock_bits"], ["20"])
        self.assertEqual(report["derived_clock_driver_cells"], ["gate"])

    @staticmethod
    def eicg_document():
        document = flat_document()
        document["modules"]["ChipTop"]["cells"].update({
            "eicg_latch": {
                "type": "$dlatch",
                "attributes": {
                    "src": "generated-src/ChipTop.sv:1.1-2.2|generated-src/EICG_wrapper.v:12.3-16.6",
                },
                "parameters": {
                    "WIDTH": "00000000000000000000000000000001",
                    "EN_POLARITY": "00000000000000000000000000000000",
                },
                "port_directions": {"D": "input", "EN": "input", "Q": "output"},
                "connections": {"D": [5], "EN": [1], "Q": [21]},
            },
            "eicg_gate": {
                "type": "$logic_and",
                "attributes": {
                    "src": "generated-src/ChipTop.sv:1.1-2.2|generated-src/EICG_wrapper.v:18.16-18.32",
                },
                "port_directions": {"A": "input", "B": "input", "Y": "output"},
                "connections": {"A": [21], "B": [1], "Y": [20]},
            },
        })
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        return document

    def test_exact_eicg_traces_raw_clock_not_control_latch(self):
        report = analyze_clock_inventory(self.eicg_document())
        self.assertEqual(report["eicg_clock_gate_cells"], ["eicg_gate"])
        self.assertEqual(report["eicg_control_latch_cells"], ["eicg_latch"])
        self.assertEqual(report["root_endpoint_counts"]["clock_uncore"], 2)

    def test_eicg_pattern_drift_fails_closed(self):
        mutations = (
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_latch"]["connections"].__setitem__("EN", [2]),
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_latch"]["parameters"].__setitem__(
                "EN_POLARITY", "00000000000000000000000000000001"
            ),
            lambda d: d["modules"]["ChipTop"]["cells"]["eicg_gate"]["attributes"].__setitem__(
                "src", "generated-src/NotEICG.v:18.16-18.32"
            ),
        )
        for mutate in mutations:
            document = self.eicg_document()
            mutate(document)
            with self.subTest(mutation=mutate), self.assertRaisesRegex(
                ValueError, "generated by sequential cell"
            ):
                analyze_clock_inventory(document)

    def test_malformed_sequential_clock_pin_fails_closed(self):
        document = flat_document()
        cell = document["modules"]["ChipTop"]["cells"]["main_ff"]
        cell["connections"].pop("CLK")
        with self.assertRaisesRegex(ValueError, "lacks CLK"):
            analyze_clock_inventory(document)
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["main_ff"]["port_directions"]["CLK"] = "output"
        with self.assertRaisesRegex(ValueError, "not an input"):
            analyze_clock_inventory(document)

    def test_unapproved_or_ambiguous_clock_fails(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [4]
        with self.assertRaisesRegex(ValueError, "unique external root"):
            analyze_clock_inventory(document)
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["gate"] = {
            "type": "$or",
            "port_directions": {"A": "input", "B": "input", "Y": "output"},
            "connections": {"A": [1], "B": [2], "Y": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        with self.assertRaisesRegex(ValueError, "unique external root"):
            analyze_clock_inventory(document)

    def test_unresolved_nonprimitive_clock_driver_fails(self):
        document = flat_document()
        document["modules"]["ChipTop"]["cells"]["mystery"] = {
            "type": "ClockMystery",
            "port_directions": {"in": "input", "out": "output"},
            "connections": {"in": [1], "out": [20]},
        }
        document["modules"]["ChipTop"]["cells"]["main_ff"]["connections"]["CLK"] = [20]
        with self.assertRaisesRegex(ValueError, "non-primitive"):
            analyze_clock_inventory(document)

    def test_export_is_self_contained_and_hash_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            export = Path(temporary)
            write_export(export, "integrated-static-graph-rocket")
            self.assertEqual(
                validate_export(export, "integrated-static-graph-rocket")["top"],
                "ChipTop",
            )
            (export / "generated-src/ChipTop.sv").write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "RTL tree hash"):
                validate_export(export, "integrated-static-graph-rocket")

    def test_export_rejects_nonlocal_or_duplicate_filelist(self):
        with tempfile.TemporaryDirectory() as temporary:
            export = Path(temporary)
            write_export(export, "integrated-static-graph-rocket")
            (export / "ChipTop.top.f").write_text("/absolute/ChipTop.sv\n")
            with self.assertRaisesRegex(ValueError, "file lists differ"):
                validate_export(export, "integrated-static-graph-rocket")
            unsafe = "generated-src/../generated-src/ChipTop.sv\n"
            (export / "ChipTop.top.f").write_text(unsafe)
            (export / "rtl-files.txt").write_text(unsafe)
            metadata = json.loads((export / "export-metadata.json").read_text())
            metadata["rtl_filelist_sha256"] = hashlib.sha256(unsafe.encode()).hexdigest()
            (export / "export-metadata.json").write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError, "unsafe"):
                validate_export(export, "integrated-static-graph-rocket")
            (export / "ChipTop.top.f").write_text(
                "generated-src/ChipTop.sv\ngenerated-src/ChipTop.sv\n"
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                validate_export(export, "integrated-static-graph-rocket")

    def test_analysis_and_comparison_bind_rocket_and_ports(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            a_export, b_export = root / "a", root / "b"
            write_export(a_export, "integrated-static-graph-rocket")
            write_export(b_export, "matched-rocket-system")
            a_hier, b_hier, flat = root / "a.json", root / "b.json", root / "flat.json"
            a_hier.write_text(json.dumps(hierarchy_document(graph=True)))
            b_hier.write_text(json.dumps(hierarchy_document(graph=False)))
            flat.write_text(json.dumps(flat_document()))
            a = analyze_export(a_export, a_hier, flat, "integrated-static-graph-rocket")
            b = analyze_export(b_export, b_hier, flat, "matched-rocket-system")
            self.assertTrue(compare_reports(a, b)["rocket_module_identity_equal"])
            b["hierarchy"]["port_signature"]["custom_boot"] = ("input", 2, 0, False, False)
            with self.assertRaisesRegex(ValueError, "port signatures"):
                compare_reports(a, b)

    def test_rocket_revision_and_byte_mismatch_fail(self):
        a = {
            "variant": "integrated-static-graph-rocket",
            "hierarchy": {
                "port_signature": {},
                "rocket_module_canonical_sha256": HEX,
                "rocket_module_raw_sha256": HEX,
                "config": "a",
            },
            "clock_inventory": {"allowed_roots": sorted(CLOCK_ROOTS)},
            "export": {"rocket_rtl_sha256": HEX, "rocket_revision": "x", "image_rootfs_sha256": HEX},
        }
        b = copy.deepcopy(a)
        b["variant"] = "matched-rocket-system"
        b["hierarchy"]["config"] = "b"
        b["export"]["rocket_revision"] = "y"
        with self.assertRaisesRegex(ValueError, "revisions"):
            compare_reports(a, b)
        b["export"]["rocket_revision"] = "x"
        b["export"]["rocket_rtl_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "Rocket.sv"):
            compare_reports(a, b)

    def test_scripts_copy_closure_and_never_run_candidate_flow(self):
        export = (ROOT / "hardware/chisel/run-exp0011-rtl-export.sh").read_text()
        preflight = (ROOT / "hardware/chisel/run-exp0011-rtl-preflight.sh").read_text()
        for token in (
            "ENABLE_YOSYS_FLOW=1",
            "generated-src/$base",
            "ChipTop.top.f",
            "shared-elaboration-identical",
            "memory-macro-contract.txt",
            "RaveilRuntimeIntegratedGraphRocketConfig",
            "RaveilFixtureRepeatedMatchedRocketConfig",
            "--network none",
            'image=$("$repo_root/hardware/chisel/verify-boom-functional-sim-image.sh")',
            '[ "$image_id" = "$image" ]',
            "expected_rootfs_sha256=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c",
            "umask 077",
            "unsafe physical RTL basename",
        ):
            self.assertIn(token, export)
        self.assertNotIn("docker build", export)
        for token in (
            'printf "read_verilog -sv %s\\n"',
            "hierarchy -generate memory_ext",
            "hierarchy -check -top ChipTop",
            "write_rtlil /out/%s-hierarchy.rtlil",
            "flatten\\nproc\\nopt_clean\\ncheck\\nwrite_json",
            "yosys -q -l",
            "--network none",
            "expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169",
            "expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5",
            "validate-export",
            "unsafe RTL entry during preflight",
            'mkdir "$output_dir/raw" "$output_dir/derived"',
            'raw_manifest_sha256=$(shasum -a 256 "$raw_dir/sha256s.txt"',
            "umask 077",
        ):
            self.assertIn(token, preflight)
        self.assertNotIn("docker build", preflight)
        self.assertNotIn("bash -lc", preflight)
        for forbidden in ("synth -top", "abc -liberty", "stat -liberty", "sta "):
            self.assertNotIn(forbidden, preflight)
        self.assertNotIn('awk "{print \\\\$1}"', export)


if __name__ == "__main__":
    unittest.main()
