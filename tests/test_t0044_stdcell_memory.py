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
    validate_mapped_netlist_postconditions,
    validate_option_b_contract,
    verify_evidence_manifest,
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
RAW_MANIFEST = b"1" * 64 + b"  1  simulation-transcript.txt\n"


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
            "preflight_receipt": {
                "sha256": H6, "source_sha256": H2, "runner_sha256": H3,
                "raw_manifest_sha256": H4, "derived_manifest_sha256": H5,
            },
            "simulation_receipt": {
                "sha256": H7, "source_sha256": H2, "runner_sha256": H4,
                "testbench_sha256": H5, "raw_manifest_sha256": H6,
                "derived_manifest_sha256": H7,
            },
            "hierarchy_receipt": {
                "metadata_sha256": H1, "comparison_sha256": H2,
                "raw_manifest_sha256": H3, "derived_manifest_sha256": H4,
                "source_sha256": H2, "runner_sha256": H5,
                "analyzer_sha256": H6,
            },
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
            "preflight_runner_sha256": "hardware/chisel/run-exp0011-stdcell-memory-preflight.sh",
            "hierarchy_runner_sha256": "hardware/chisel/run-exp0011-common-memory-hierarchy-preflight.sh",
            "analyzer_sha256": "raveil/t0044_integrated_rtl.py",
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
        def write_manifest(directory):
            entries = []
            for path in sorted(directory.iterdir(), key=lambda item: item.name):
                if path.name == "sha256s.txt":
                    continue
                payload = path.read_bytes()
                entries.append(
                    f"{hashlib.sha256(payload).hexdigest()}  {len(payload)}  {path.name}\n"
                )
            value = "".join(entries).encode()
            (directory / "sha256s.txt").write_bytes(value)
            return value

        simulation_raw = root / "simulation/raw"
        simulation_raw.mkdir(parents=True)
        (simulation_raw / "runtime-image-receipt.txt").write_bytes(RUNTIME_RECEIPT)
        (simulation_raw / "simulation-transcript.txt").write_bytes(b"x")
        simulation_raw_manifest = write_manifest(simulation_raw)
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
            "raw_manifest_sha256": hashlib.sha256(simulation_raw_manifest).hexdigest(),
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
        simulation_derived = root / "simulation/derived"
        simulation_derived.mkdir()
        (simulation_derived / "simulation-metadata.json").write_bytes(metadata_bytes)
        simulation_derived_manifest = write_manifest(simulation_derived)

        hierarchy_raw = root / "hierarchy/raw"
        hierarchy_raw.mkdir(parents=True)
        (hierarchy_raw / "yosys-version.txt").write_bytes(b"Yosys 0.27+3\n")
        hierarchy_raw_manifest = write_manifest(hierarchy_raw)
        hierarchy_comparison = {
            "schema": "raveil.exp-0011-common-memory-concrete/v1",
            "status": "structural-only", "source_sha256": hashes["source_sha256"],
            "memory_macro_instances": 11, "memory_macro_types": 7,
            "rocket_module_canonical_sha256": H1,
            "common_clock_roots": ["clock_uncore", "jtag_TCK", "serial_tl_0_clock_in"],
            "reachable_blackboxes": 0,
            "nonclaims": ["no synthesis or memory mapping", "no placement or routing", "no timing, area, energy, performance, FPGA, ASIC, or silicon result"],
        }
        hierarchy_metadata = {
            "schema": "raveil.exp-0011-common-memory-hierarchy-preflight/v1",
            "task_id": "T-0044", "authority_commit": authority,
            "image": "raveil-physical-proxy-toolchain:v1",
            "image_id": PHYSICAL_IMAGE_ID, "image_rootfs_sha256": PHYSICAL_ROOTFS_SHA256,
            "platform": "linux/amd64", "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["hierarchy_runner_sha256"],
            "analyzer_sha256": hashes["analyzer_sha256"],
            "integrated_export_metadata_sha256": H1,
            "baseline_export_metadata_sha256": H2,
            "raw_manifest_sha256": hashlib.sha256(hierarchy_raw_manifest).hexdigest(),
            "memory_macro_types": 7, "memory_macro_instances": 11,
            "reachable_blackboxes": 0, "evidence_class": "rtl-structural-preflight",
            "candidate_synthesis": False, "memory_mapping": False, "pnr": False,
            "nonclaims": ["no synthesis or memory mapping", "no placement or routing", "no timing, area, energy, performance, FPGA, ASIC, or silicon result"],
        }
        hierarchy_derived = root / "hierarchy/derived"
        hierarchy_derived.mkdir()
        comparison_bytes = (json.dumps(hierarchy_comparison, indent=2, sort_keys=True) + "\n").encode()
        hierarchy_metadata_bytes = (json.dumps(hierarchy_metadata, indent=2, sort_keys=True) + "\n").encode()
        (hierarchy_derived / "comparison-report.json").write_bytes(comparison_bytes)
        (hierarchy_derived / "preflight-metadata.json").write_bytes(hierarchy_metadata_bytes)
        hierarchy_derived_manifest = write_manifest(hierarchy_derived)

        preflight_raw = root / "source-preflight/raw"
        preflight_raw.mkdir(parents=True)
        (preflight_raw / "yosys-version.txt").write_bytes(b"Yosys 0.27+3\n")
        preflight_raw_manifest = write_manifest(preflight_raw)
        preflight_metadata = {
            "schema": "raveil.exp-0011-common-stdcell-memory-preflight/v2",
            "task_id": "T-0044", "authority_commit": authority,
            "image": "raveil-physical-proxy-toolchain:v1", "image_id": PHYSICAL_IMAGE_ID,
            "image_rootfs_sha256": PHYSICAL_ROOTFS_SHA256, "platform": "linux/amd64",
            "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["preflight_runner_sha256"],
            "readiness_receipt_sha256": READINESS_RECEIPT_SHA256,
            "inventory_runner_sha256": H1, "yosys_sha256": YOSYS_SHA256,
            "yosys_version": "0.27+3", "yosys_revision": "b58664d44",
            "raw_manifest_sha256": hashlib.sha256(preflight_raw_manifest).hexdigest(),
            "tops": FUNCTIONAL_MODULES, "fresh_yosys_processes": 7,
            "total_storage_bits": TOTAL_STORAGE_BITS, "commands": ["read_verilog -sv"],
            "evidence_class": EVIDENCE_CLASS, "experiment_id": None,
            "manifest_frozen": False, "preflight_evidence_collected": True,
            "claim_bearing_candidate_data_collected": False,
            "candidate_synthesis": False, "pnr": False,
            "nonclaims": ["no synthesis mapping", "no placement or routing", "no area, timing, energy, FPGA, ASIC, or silicon claim"],
        }
        preflight_metadata_bytes = (json.dumps(preflight_metadata, indent=2, sort_keys=True) + "\n").encode()
        preflight_derived = root / "source-preflight/derived"
        preflight_derived.mkdir()
        (preflight_derived / "preflight-metadata.json").write_bytes(preflight_metadata_bytes)
        preflight_derived_manifest = write_manifest(preflight_derived)
        contract = valid_contract()
        contract["authority_commit"] = authority
        identities = contract["identities"]
        identities["source_sha256"] = hashes["source_sha256"]
        identities["testbench_sha256"] = hashes["testbench_sha256"]
        identities["simulation_runner_sha256"] = hashes["runner_sha256"]
        identities["verifier_sha256"] = hashes["verifier_sha256"]
        identities["preflight_runner_sha256"] = hashes["preflight_runner_sha256"]
        identities["preflight_receipt"] = {
            "sha256": hashlib.sha256(preflight_metadata_bytes).hexdigest(),
            "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["preflight_runner_sha256"],
            "raw_manifest_sha256": hashlib.sha256(preflight_raw_manifest).hexdigest(),
            "derived_manifest_sha256": hashlib.sha256(preflight_derived_manifest).hexdigest(),
        }
        identities["simulation_receipt"] = {
            "sha256": hashlib.sha256(metadata_bytes).hexdigest(),
            "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["runner_sha256"],
            "testbench_sha256": hashes["testbench_sha256"],
            "raw_manifest_sha256": hashlib.sha256(simulation_raw_manifest).hexdigest(),
            "derived_manifest_sha256": hashlib.sha256(simulation_derived_manifest).hexdigest(),
        }
        identities["hierarchy_receipt"] = {
            "metadata_sha256": hashlib.sha256(hierarchy_metadata_bytes).hexdigest(),
            "comparison_sha256": hashlib.sha256(comparison_bytes).hexdigest(),
            "raw_manifest_sha256": hashlib.sha256(hierarchy_raw_manifest).hexdigest(),
            "derived_manifest_sha256": hashlib.sha256(hierarchy_derived_manifest).hexdigest(),
            "source_sha256": hashes["source_sha256"],
            "runner_sha256": hashes["hierarchy_runner_sha256"],
            "analyzer_sha256": hashes["analyzer_sha256"],
        }
        return contract, metadata_bytes, simulation_raw_manifest

    def test_v4_bundle_binds_all_leg_payloads_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            contract, metadata_bytes, raw_manifest = self.bundle_fixture(root)
            completed = mock.Mock(stdout="a" * 40 + "\n")
            with mock.patch("raveil.t0044_stdcell_memory.subprocess.run", return_value=completed):
                result = validate_evidence_bundle(
                    contract, metadata_bytes, RUNTIME_RECEIPT, raw_manifest,
                    repo_root=root, evidence_root=root,
                )
            self.assertEqual(result["status"], "valid-unfrozen-pre-data")

            tampered = RUNTIME_RECEIPT.replace(
                b"PLATFORM=linux/amd64", b"PLATFORM=linux/arm64"
            )
            with mock.patch("raveil.t0044_stdcell_memory.subprocess.run", return_value=completed):
                with self.assertRaises(ValueError):
                    validate_evidence_bundle(
                        contract, metadata_bytes, tampered, raw_manifest,
                        repo_root=root, evidence_root=root,
                    )

            transcript = root / "simulation/raw/simulation-transcript.txt"
            transcript.write_bytes(b"y")
            with mock.patch("raveil.t0044_stdcell_memory.subprocess.run", return_value=completed):
                with self.assertRaisesRegex(ValueError, "size or hash mismatch"):
                    validate_evidence_bundle(
                        contract, metadata_bytes, RUNTIME_RECEIPT, raw_manifest,
                        repo_root=root, evidence_root=root,
                    )

    def test_manifest_parser_rejects_malformed_duplicate_and_unlisted_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = pathlib.Path(temp)
            (directory / "payload.txt").write_bytes(b"x")
            valid = (
                f"{hashlib.sha256(b'x').hexdigest()}  1  payload.txt\n".encode()
            )
            self.assertEqual(verify_evidence_manifest(valid, directory)["entries"], 1)
            for bad in (
                valid.replace(b"  1  ", b"  "),
                valid + valid,
                valid.replace(b"payload.txt", b"../payload.txt"),
            ):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    verify_evidence_manifest(bad, directory)
            (directory / "unlisted.txt").write_bytes(b"z")
            with self.assertRaisesRegex(ValueError, "file set mismatch"):
                verify_evidence_manifest(valid, directory)

    def test_future_mapped_netlist_postcondition_rejects_abstract_memory(self):
        clean = {"modules": {"top": {"cells": {"gate": {"type": "AND2_X1"}}}}}
        self.assertEqual(
            validate_mapped_netlist_postconditions(clean)["pnr"], False
        )
        dirty = copy.deepcopy(clean)
        dirty["modules"]["top"]["cells"]["memory"] = {"type": "$mem_v2"}
        with self.assertRaisesRegex(ValueError, "abstract memory"):
            validate_mapped_netlist_postconditions(dirty)

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
        self.assertIn("--bundle-root", runner)
        self.assertIn('"hierarchy_receipt"', runner)
        self.assertIn('find "$output_dir" -type f -exec chmod 0444', runner)
        self.assertIn('find "$output_dir" -depth -type d -exec chmod 0555', runner)
        self.assertIn("aggregate_manifest_sha256", runner)
        self.assertIn("verify_evidence_manifest", runner)
        self.assertNotIn("memory_map", runner)
        self.assertNotIn("openroad", runner.lower())
        self.assertNotIn("candidate_synthesis\": True", runner)


if __name__ == "__main__":
    unittest.main()
