import copy
import hashlib
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from raveil.t0044_integrated_rtl import MEMORY_MACRO_PORTS
from raveil.t0044_stdcell_memory import (
    CELL_LEF_SHA256,
    EVIDENCE_CLASS,
    EXPECTED_MACROS,
    FUNCTIONAL_CONFIG_VIEW_SHA256,
    FUNCTIONAL_CHECKS,
    FUNCTIONAL_LOCK_SHA256,
    FUNCTIONAL_MODULES,
    FUNCTIONAL_NONCLAIMS,
    FUNCTIONAL_PAYLOAD_MANIFEST,
    FUNCTIONAL_ROOTFS_SHA256,
    FUNCTIONAL_TOOLCHAIN_VOLUME,
    FUNCTIONAL_VERIFIER_SHA256,
    FUTURE_MAPPING_PASSES,
    LIBERTY_SHA256,
    NONCLAIMS,
    OPENRCX_SHA256,
    PHYSICAL_IMAGE_ID,
    PHYSICAL_ROOTFS_SHA256,
    POSTCONDITIONS,
    READINESS_RECEIPT_SHA256,
    SCHEMA,
    SEMANTICS,
    TECH_LEF_SHA256,
    TOTAL_STORAGE_BITS,
    YOSYS_SHA256,
    parse_runtime_receipt,
    validate_evidence_bundle,
    validate_option_b_contract,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware/chisel/exp0011_common_stdcell_memories.sv"
PREFLIGHT = ROOT / "hardware/chisel/run-exp0011-stdcell-memory-preflight.sh"
SIMULATION = ROOT / "hardware/chisel/run-exp0011-stdcell-memory-sim.sh"
CLOSURE = ROOT / "hardware/chisel/run-exp0011-common-memory-closure.sh"
TESTBENCH = ROOT / "hardware/chisel/exp0011_common_stdcell_memory_tb.sv"
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64
H5 = "5" * 64
H6 = "6" * 64
H7 = "7" * 64
RUNTIME_IMAGE_ID = "sha256:" + "9" * 64
RUNTIME_RECEIPT = (
    "SCHEMA=raveil.boom-functional-sim-image/v2\n"
    f"RUNTIME_IMAGE_ID={RUNTIME_IMAGE_ID}\n"
    f"RUNTIME_DESCRIPTOR_DIGEST={RUNTIME_IMAGE_ID}\n"
    "RUNTIME_DESCRIPTOR_MEDIA_TYPE=application/vnd.oci.image.index.v1+json\n"
    "RUNTIME_DESCRIPTOR_SIZE=856\n"
    f"PAYLOAD_MANIFEST={FUNCTIONAL_PAYLOAD_MANIFEST}\n"
    "PAYLOAD_MEDIA_TYPE=application/vnd.oci.image.manifest.v1+json\n"
    f"CONFIG_VIEW_SHA256={FUNCTIONAL_CONFIG_VIEW_SHA256}\n"
    f"ROOTFS_LAYERS_SHA256={FUNCTIONAL_ROOTFS_SHA256}\n"
    "PLATFORM=linux/amd64\n"
    "BUILD_REF=abcdefghijklmnopqrstuvwxy\n"
).encode()
RAW_MANIFEST = b"1" * 64 + b"  simulation-transcript.txt\n"


def valid_contract():
    return {
        "schema": SCHEMA,
        "task_id": "T-0044",
        "authority_commit": "a" * 40,
        "freeze_state": "unfrozen",
        "experiment_id": None,
        "manifest_frozen": False,
        "claim_bearing_candidate_data_collected": False,
        "candidate_synthesis": False,
        "pnr": False,
        "evidence_class": EVIDENCE_CLASS,
        "nonclaims": copy.deepcopy(NONCLAIMS),
        "candidates": {"integrated": H1, "matched_rocket": H1},
        "macros": [copy.deepcopy(m) for m in EXPECTED_MACROS.values()],
        "total_storage_bits": TOTAL_STORAGE_BITS,
        "semantics": copy.deepcopy(SEMANTICS),
        "identities": {
            "source_sha256": H2,
            "preflight_runner_sha256": H3,
            "simulation_runner_sha256": H4,
            "testbench_sha256": H5,
            "verifier_sha256": FUNCTIONAL_VERIFIER_SHA256,
            "readiness_receipt_sha256": READINESS_RECEIPT_SHA256,
            "preflight_receipt": {"sha256": H6, "source_sha256": H2, "runner_sha256": H3},
            "simulation_receipt": {"sha256": H7, "source_sha256": H2, "runner_sha256": H4, "testbench_sha256": H5},
            "toolchain": {
                "physical_image": "raveil-physical-proxy-toolchain:v1",
                "physical_image_id": PHYSICAL_IMAGE_ID,
                "physical_rootfs_sha256": PHYSICAL_ROOTFS_SHA256,
                "functional_runtime_oci_index": RUNTIME_IMAGE_ID,
                "functional_payload_manifest": FUNCTIONAL_PAYLOAD_MANIFEST,
                "functional_config_view_sha256": FUNCTIONAL_CONFIG_VIEW_SHA256,
                "functional_rootfs_sha256": FUNCTIONAL_ROOTFS_SHA256,
                "functional_verifier_sha256": FUNCTIONAL_VERIFIER_SHA256,
                "functional_runtime_receipt_sha256": hashlib.sha256(RUNTIME_RECEIPT).hexdigest(),
                "functional_runtime_descriptor_digest": RUNTIME_IMAGE_ID,
                "functional_runtime_descriptor_media_type": "application/vnd.oci.image.index.v1+json",
                "functional_runtime_descriptor_size": 856,
                "functional_payload_media_type": "application/vnd.oci.image.manifest.v1+json",
                "functional_runtime_build_ref": "abcdefghijklmnopqrstuvwxy",
                "platform": "linux/amd64",
                "yosys_sha256": YOSYS_SHA256,
                "yosys_version": "0.27+3",
                "verilator_sha256": "8" * 64,
                "verilator_version": "5.020",
                "standard_cell_liberty_sha256": LIBERTY_SHA256,
                "standard_cell_lef_sha256": CELL_LEF_SHA256,
                "technology_lef_sha256": TECH_LEF_SHA256,
                "openrcx_rule_sha256": OPENRCX_SHA256,
            },
        },
        "future_mapping_passes": copy.deepcopy(FUTURE_MAPPING_PASSES),
        "postconditions": copy.deepcopy(POSTCONDITIONS),
    }


class TestT0044OptionBContract(unittest.TestCase):
    def reject(self, mutation):
        document = valid_contract()
        mutation(document)
        with self.assertRaises(ValueError):
            validate_option_b_contract(document)

    def test_valid_contract_reports_exact_denominator(self):
        result = validate_option_b_contract(valid_contract())
        self.assertEqual(result["status"], "valid-unfrozen-pre-data")
        self.assertEqual(result["macro_types"], 7)
        self.assertEqual(result["macro_instances"], 11)
        self.assertEqual(result["total_storage_bits"], 4_631_296)

    def test_missing_top_level_field_rejected(self):
        self.reject(lambda d: d.pop("semantics"))

    def test_unknown_top_level_field_rejected(self):
        self.reject(lambda d: d.__setitem__("surprise", False))

    def test_unknown_nested_field_rejected(self):
        self.reject(lambda d: d["identities"].__setitem__("surprise", H1))

    def test_absent_candidate_key_rejected(self):
        self.reject(lambda d: d["candidates"].pop("matched_rocket"))

    def test_malformed_candidate_hash_rejected(self):
        self.reject(lambda d: d["candidates"].__setitem__("integrated", "abc"))

    def test_placeholder_candidate_hash_rejected(self):
        self.reject(lambda d: d["candidates"].update(integrated="0" * 64, matched_rocket="0" * 64))

    def test_asymmetric_candidate_hash_rejected(self):
        self.reject(lambda d: d["candidates"].__setitem__("matched_rocket", H2))

    def test_macro_set_drift_rejected(self):
        self.reject(lambda d: d["macros"].pop())

    def test_macro_depth_drift_rejected(self):
        self.reject(lambda d: d["macros"][0].__setitem__("depth", d["macros"][0]["depth"] + 1))

    def test_macro_width_drift_rejected(self):
        self.reject(lambda d: d["macros"][1].__setitem__("width", 63))

    def test_macro_count_drift_rejected(self):
        self.reject(lambda d: d["macros"][1].__setitem__("count", 3))

    def test_macro_ports_drift_rejected(self):
        self.reject(lambda d: d["macros"][0].__setitem__("ports", "blackbox"))

    def test_macro_mask_granularity_drift_rejected(self):
        self.reject(lambda d: d["macros"][0].__setitem__("mask_granularity", 8))

    def test_recomputed_total_storage_bits_rejected(self):
        self.reject(lambda d: d.__setitem__("total_storage_bits", TOTAL_STORAGE_BITS - 1))

    def test_read_hold_semantics_drift_rejected(self):
        self.reject(lambda d: d["semantics"].__setitem__("one_rw_output_hold", ["disabled"]))

    def test_cross_clock_collision_semantics_drift_rejected(self):
        self.reject(lambda d: d["semantics"].__setitem__("memory_ext_collision", "write-first"))

    def test_physical_input_identity_drift_rejected(self):
        self.reject(lambda d: d["identities"]["toolchain"].__setitem__("standard_cell_lef_sha256", H1))

    def test_tool_binary_identity_drift_rejected(self):
        self.reject(lambda d: d["identities"]["toolchain"].__setitem__("yosys_sha256", H1))

    def test_source_receipt_binding_drift_rejected(self):
        self.reject(lambda d: d["identities"]["preflight_receipt"].__setitem__("source_sha256", H1))

    def test_simulation_receipt_binding_drift_rejected(self):
        self.reject(lambda d: d["identities"]["simulation_receipt"].__setitem__("runner_sha256", H1))

    def test_readiness_receipt_hash_drift_rejected(self):
        self.reject(lambda d: d["identities"].__setitem__("readiness_receipt_sha256", H1))

    def test_future_mapping_pass_drift_rejected(self):
        self.reject(lambda d: d.__setitem__("future_mapping_passes", ["memory_map", "abc"]))

    def test_future_postcondition_drift_rejected(self):
        self.reject(lambda d: d["postconditions"].pop())

    def test_blackbox_postcondition_rejection(self):
        self.reject(lambda d: d["postconditions"].__setitem__(1, "blackboxes allowed"))

    def test_data_collection_rejected(self):
        self.reject(lambda d: d.__setitem__("claim_bearing_candidate_data_collected", True))

    def test_runtime_oci_index_sentinel_rejected(self):
        self.reject(
            lambda d: d["identities"]["toolchain"].__setitem__(
                "functional_runtime_oci_index", "resolved-by-verified-receipt"
            )
        )

    def test_runtime_oci_index_placeholder_rejected(self):
        self.reject(
            lambda d: d["identities"]["toolchain"].__setitem__(
                "functional_runtime_oci_index", "sha256:" + "0" * 64
            )
        )

    def test_freeze_rejected(self):
        self.reject(lambda d: d.__setitem__("manifest_frozen", True))

    def test_experiment_allocation_rejected(self):
        self.reject(lambda d: d.__setitem__("experiment_id", "EXP-0011"))

    def test_candidate_synthesis_rejected(self):
        self.reject(lambda d: d.__setitem__("candidate_synthesis", True))

    def test_pnr_rejected(self):
        self.reject(lambda d: d.__setitem__("pnr", True))

    def test_claim_rejected(self):
        self.reject(lambda d: d.__setitem__("nonclaims", ["area is better"]))

    def test_authority_commit_format_rejected(self):
        self.reject(lambda d: d.__setitem__("authority_commit", "acd2db99"))

    def test_runtime_receipt_exact_parser_rejects_mutations(self):
        self.assertEqual(
            parse_runtime_receipt(RUNTIME_RECEIPT)["RUNTIME_IMAGE_ID"],
            RUNTIME_IMAGE_ID,
        )
        mutations = (
            RUNTIME_RECEIPT + b"UNKNOWN=value\n",
            RUNTIME_RECEIPT.replace(b"PLATFORM=linux/amd64", b"PLATFORM=linux/arm64"),
            RUNTIME_RECEIPT.replace(b"RUNTIME_DESCRIPTOR_SIZE=856", b"RUNTIME_DESCRIPTOR_SIZE=0"),
            RUNTIME_RECEIPT.replace(b"BUILD_REF=", b"SCHEMA=duplicate\nBUILD_REF="),
        )
        for receipt in mutations:
            with self.subTest(receipt=receipt):
                with self.assertRaises(ValueError):
                    parse_runtime_receipt(receipt)

    def bundle_fixture(self, root):
        authority = "a" * 40
        relative_files = {
            "source_sha256": "hardware/chisel/exp0011_common_stdcell_memories.sv",
            "testbench_sha256": "hardware/chisel/exp0011_common_stdcell_memory_tb.sv",
            "runner_sha256": "hardware/chisel/run-exp0011-stdcell-memory-sim.sh",
            "verifier_sha256": "hardware/chisel/verify-boom-functional-sim-image.sh",
        }
        hashes = {}
        for key, relative in relative_files.items():
            data = (ROOT / relative).read_bytes()
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            hashes[key] = hashlib.sha256(data).hexdigest()
        self.assertEqual(hashes["verifier_sha256"], FUNCTIONAL_VERIFIER_SHA256)
        receipt_sha256 = hashlib.sha256(RUNTIME_RECEIPT).hexdigest()
        receipt_path = (
            root / "artifacts/boom-functional-sim-images" /
            RUNTIME_IMAGE_ID.removeprefix("sha256:") / "receipt"
        )
        receipt_path.parent.mkdir(parents=True)
        receipt_path.write_bytes(RUNTIME_RECEIPT)
        metadata = {
            "schema": "raveil.exp-0011-common-stdcell-memory-functional/v3",
            "task_id": "T-0044",
            "authority_commit": authority,
            "runtime_oci_index": RUNTIME_IMAGE_ID,
            "descriptor_digest": RUNTIME_IMAGE_ID,
            "descriptor_media_type": "application/vnd.oci.image.index.v1+json",
            "descriptor_size": 856,
            "payload_manifest": FUNCTIONAL_PAYLOAD_MANIFEST,
            "payload_media_type": "application/vnd.oci.image.manifest.v1+json",
            "config_view_sha256": FUNCTIONAL_CONFIG_VIEW_SHA256,
            "rootfs_layers_sha256": FUNCTIONAL_ROOTFS_SHA256,
            "platform": "linux/amd64",
            "build_ref": "abcdefghijklmnopqrstuvwxy",
            "receipt_sha256": receipt_sha256,
            "receipt_path": (
                "artifacts/boom-functional-sim-images/" +
                RUNTIME_IMAGE_ID.removeprefix("sha256:") + "/receipt"
            ),
            "receipt_copy_sha256": receipt_sha256,
            "toolchain_volume": FUNCTIONAL_TOOLCHAIN_VOLUME,
            "lock_sha256": FUNCTIONAL_LOCK_SHA256,
            "verilator_version": "Verilator 5.020 2024-01-01 rev test",
            "verilator_sha256": "8" * 64,
            "source_sha256": hashes["source_sha256"],
            "testbench_sha256": hashes["testbench_sha256"],
            "runner_sha256": hashes["runner_sha256"],
            "raw_manifest_sha256": hashlib.sha256(RAW_MANIFEST).hexdigest(),
            "verifier_sha256": hashes["verifier_sha256"],
            "modules": FUNCTIONAL_MODULES,
            "checks": FUNCTIONAL_CHECKS,
            "evidence_class": "rtl-simulation-functional",
            "functional_evidence_collected": True,
            "claim_bearing_candidate_data_collected": False,
            "experiment_id": None,
            "manifest_frozen": False,
            "candidate_synthesis": False,
            "pnr": False,
            "nonclaims": FUNCTIONAL_NONCLAIMS,
        }
        metadata_bytes = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode()
        contract = valid_contract()
        contract["authority_commit"] = authority
        identities = contract["identities"]
        identities["source_sha256"] = hashes["source_sha256"]
        identities["testbench_sha256"] = hashes["testbench_sha256"]
        identities["simulation_runner_sha256"] = hashes["runner_sha256"]
        identities["verifier_sha256"] = hashes["verifier_sha256"]
        identities["preflight_receipt"]["source_sha256"] = hashes["source_sha256"]
        identities["simulation_receipt"] = {
            "sha256": hashlib.sha256(metadata_bytes).hexdigest(),
            "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["runner_sha256"],
            "testbench_sha256": hashes["testbench_sha256"],
        }
        return contract, metadata_bytes

    def test_v3_bundle_binds_receipt_metadata_contract_head_and_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            contract, metadata_bytes = self.bundle_fixture(root)
            completed = mock.Mock(stdout="a" * 40 + "\n")
            with mock.patch("raveil.t0044_stdcell_memory.subprocess.run", return_value=completed):
                result = validate_evidence_bundle(
                    contract, metadata_bytes, RUNTIME_RECEIPT, RAW_MANIFEST,
                    repo_root=root,
                )
            self.assertEqual(result["status"], "valid-unfrozen-pre-data")

            tampered = RUNTIME_RECEIPT.replace(
                b"PLATFORM=linux/amd64", b"PLATFORM=linux/arm64"
            )
            with mock.patch("raveil.t0044_stdcell_memory.subprocess.run", return_value=completed):
                with self.assertRaises(ValueError):
                    validate_evidence_bundle(
                        contract, metadata_bytes, tampered, RAW_MANIFEST,
                        repo_root=root,
                    )

    def test_source_has_exact_modules_interfaces_and_guard(self):
        source = SOURCE.read_text(encoding="utf-8")
        modules = re.findall(r"(?m)^module\s+([A-Za-z0-9_]+)\s*\(", source)
        self.assertEqual(set(modules), set(MEMORY_MACRO_PORTS))
        self.assertEqual(len(modules), 7)
        self.assertIn("`default_nettype none", source)
        self.assertTrue(source.rstrip().endswith("`default_nettype wire"))
        for name, ports in MEMORY_MACRO_PORTS.items():
            header = source.split(f"module {name} (", 1)[1].split(");", 1)[0]
            for port, (direction, width) in ports.items():
                width_text = "" if width == 1 else rf"\s+\[{width - 1}:0\]"
                self.assertRegex(
                    header,
                    rf"\b{direction}\s+logic{width_text}\s+{re.escape(port)}\b",
                )

    def test_source_has_no_forbidden_constructs(self):
        source = SOURCE.read_text(encoding="utf-8")
        code = re.sub(r"//.*", "", source)
        for forbidden in (r"\binitial\b", r"\$random\b", r"\bDPI\b", r"\bblackbox\b", r"\breset\b"):
            self.assertNotRegex(code, forbidden)
        self.assertNotIn("vendor", code.lower())
        self.assertNotIn("candidate", code.lower())

    def test_preflight_runner_pins_offline_append_only_fresh_tops(self):
        runner = PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn("APPEND_ONLY_OUTPUT_DIR", runner)
        self.assertIn('[ ! -e "$output_dir" ]', runner)
        self.assertNotIn("mkdir -p", runner)
        self.assertIn("--network none", runner)
        self.assertIn(PHYSICAL_IMAGE_ID, runner)
        self.assertIn(PHYSICAL_ROOTFS_SHA256, runner)
        self.assertIn("for top in $tops", runner)
        self.assertIn('yosys -Q -T -l "/out/$top-yosys.log"', runner)
        self.assertIn("select -assert-count 1", runner)
        self.assertIn("select -assert-none a:blackbox=1", runner)
        self.assertNotIn("memory_map", runner)

    def test_preflight_runner_binds_physical_and_hash_identities(self):
        runner = PREFLIGHT.read_text(encoding="utf-8")
        for digest in (READINESS_RECEIPT_SHA256, LIBERTY_SHA256, CELL_LEF_SHA256, TECH_LEF_SHA256, OPENRCX_SHA256, YOSYS_SHA256):
            self.assertIn(digest, runner)
        for token in ("source_sha256", "runner_sha256", "raw_manifest_sha256", "physical-input-identities.txt"):
            self.assertIn(token, runner)

    def test_simulation_runner_uses_pinned_verilator_and_all_modules(self):
        runner = SIMULATION.read_text(encoding="utf-8")
        self.assertIn("APPEND_ONLY_OUTPUT_DIR", runner)
        self.assertIn('[ ! -e "$output_dir" ]', runner)
        self.assertIn("--network none", runner)
        self.assertIn("verify-boom-functional-sim-image.sh", runner)
        self.assertIn(FUNCTIONAL_PAYLOAD_MANIFEST, runner)
        self.assertIn(FUNCTIONAL_CONFIG_VIEW_SHA256, runner)
        self.assertIn(FUNCTIONAL_ROOTFS_SHA256, runner)
        self.assertNotIn("raveil-boom-functional-sim:v1", runner)
        self.assertIn("runtime_oci_index", runner)
        self.assertIn("runtime-image-receipt.txt", runner)
        self.assertIn("receipt_sha256", runner)
        self.assertIn("receipt_path", runner)
        self.assertIn("functional/v3", runner)
        self.assertIn('"$repo_root/$verifier_rel" "$receipt_source"', runner)
        self.assertIn("Verilator 5.020", runner)
        self.assertIn("verilator --binary --timing", runner)
        self.assertNotIn("iverilog", runner)
        self.assertNotIn("vvp", runner)
        testbench = TESTBENCH.read_text(encoding="utf-8")
        for module in MEMORY_MACRO_PORTS:
            self.assertRegex(testbench, rf"\b{module}\b")
        self.assertEqual(testbench.count("check_value("), 29)
        self.assertIn('if (checks != 28) $fatal', testbench)
        self.assertIn("checks=%0d modules=7", testbench)

    def test_closure_runner_binds_all_three_prerequisites_without_candidate_flow(self):
        runner = CLOSURE.read_text(encoding="utf-8")
        self.assertIn("APPEND_ONLY_OUTPUT_DIR", runner)
        self.assertIn("run-exp0011-common-memory-hierarchy-preflight.sh", runner)
        self.assertIn("run-exp0011-stdcell-memory-preflight.sh", runner)
        self.assertIn("run-exp0011-stdcell-memory-sim.sh", runner)
        self.assertIn("option-b-contract.json", runner)
        self.assertIn("--bundle-metadata", runner)
        self.assertIn("--bundle-receipt", runner)
        self.assertIn("--bundle-raw-manifest", runner)
        self.assertNotIn("memory_map", runner)
        self.assertNotIn("openroad", runner.lower())
        self.assertNotIn("candidate_synthesis\": True", runner)


if __name__ == "__main__":
    unittest.main()
