import json
import pathlib
import re
import subprocess
import tempfile
import unittest

from raveil import t0044_physical


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PhysicalProxyToolchainTests(unittest.TestCase):
    def test_frozen_stage_b_manifest_is_exact(self) -> None:
        path = ROOT / "benchmarks/manifests/t0044-static-physical-screen-v1.json"
        manifest = t0044_physical.load_manifest(path)
        self.assertRegex(manifest["implementation_authority"], r"^[0-9a-f]{40}$")
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                manifest["implementation_authority"],
                "HEAD",
            ],
            cwd=ROOT,
            check=True,
        )
        self.assertEqual(manifest["variants"]["rocket-in-order"]["top"], "Rocket")
        self.assertEqual(
            manifest["variants"]["static-graph"]["blackboxes"],
            ["OwnedFixedLatencyScratchpad", "RaveilFixtureInputProvider"],
        )
        self.assertFalse(manifest["partition_policy"]["whole_system_claim"])

        recovery_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v1.json"
        )
        recovery = t0044_physical.load_manifest(recovery_path)
        self.assertEqual(
            recovery["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(path),
        )
        self.assertEqual(
            recovery["operational_change"],
            "allow-only-empty-host-owned-container-log-before-container-launch",
        )
        recovery_v2_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v2.json"
        )
        recovery_v2 = t0044_physical.load_manifest(recovery_v2_path)
        self.assertEqual(
            recovery_v2["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(recovery_path),
        )
        self.assertEqual(
            recovery_v2["variants"]["static-graph"]["lowering_options"],
            ["disallowLocalVariables", "disallowPackedArrays"],
        )
        recovery_v3_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v3.json"
        )
        recovery_v3 = t0044_physical.load_manifest(recovery_v3_path)
        self.assertEqual(
            recovery_v3["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(recovery_v2_path),
        )
        self.assertEqual(
            recovery_v3["operational_change"],
            "assert-and-blackbox-common-partitions-before-checked-hierarchy",
        )
        recovery_v4_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v4.json"
        )
        recovery_v4 = t0044_physical.load_manifest(recovery_v4_path)
        self.assertEqual(
            recovery_v4["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(recovery_v3_path),
        )
        self.assertEqual(
            recovery_v4["operational_change"],
            "verify-named-module-single-instance-blackbox-attributes",
        )
        self.assertEqual(
            recovery_v4["collector_policy"],
            {
                "blackbox_selection_mode": "yosys-module-name-single-instance-v1",
                "blackbox_before_checked_hierarchy": True,
            },
        )
        recovery_v5_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v5.json"
        )
        recovery_v5 = t0044_physical.load_manifest(recovery_v5_path)
        self.assertEqual(
            recovery_v5["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(recovery_v4_path),
        )
        self.assertEqual(
            recovery_v5["operational_change"],
            "load-mapped-cell-liberty-and-use-supported-opensta-tcl",
        )
        self.assertEqual(recovery_v5["collector_policy"]["mapped_check_mode"], "liberty-aware-v1")
        self.assertEqual(
            recovery_v5["collector_policy"]["sta_constraint_mode"],
            "foreach-non-clock-inputs-v1",
        )
        recovery_v6_path = (
            ROOT / "benchmarks/manifests/t0044-static-physical-screen-recovery-v6.json"
        )
        recovery_v6 = t0044_physical.load_manifest(recovery_v6_path)
        self.assertEqual(
            recovery_v6["recovery_of_manifest_sha256"],
            t0044_physical.sha256_file(recovery_v5_path),
        )
        self.assertEqual(
            recovery_v6["operational_change"],
            "emit-and-verify-explicit-common-blackbox-declarations",
        )
        self.assertEqual(
            recovery_v6["collector_policy"]["mapped_blackbox_declarations"],
            "explicit-yosys-stubs-v1",
        )

    def test_toolchain_is_pinned_and_commissioning_only(self) -> None:
        dockerfile = (ROOT / "hardware/chisel/Dockerfile.physical-proxy").read_text()
        self.assertIn("mambaorg/micromamba:1.4.2", dockerfile)
        self.assertIn("yosys=0.27_4_gb58664d44", dockerfile)
        self.assertIn("openroad=2.0_7070_g0264023b6", dockerfile)
        self.assertIn("open_pdks.sky130a=1.0.457_0_g32e8f23", dockerfile)
        self.assertIn("libgomp=15.2.0", dockerfile)
        self.assertIn("libgl1=1.3.2-1", dockerfile)
        self.assertNotRegex(dockerfile, re.compile(r"\b(latest|master|main)\b"))

        inner = (
            ROOT / "hardware/chisel/run-physical-proxy-smoke-in-container.sh"
        ).read_text()
        self.assertIn("evidence=synthesis-toolchain-commissioning", inner)
        self.assertIn("performance=not-measured", inner)
        self.assertIn("sky130_fd_sc_hd__tt_025C_1v80.lib", inner)
        self.assertIn("stat -liberty", inner)
        self.assertIn("report_checks", inner)
        self.assertIn("sta -exit", inner)
        self.assertIn("conda_environment_sha256", inner)
        self.assertIn("system_packages_sha256", inner)

    def test_outer_wrapper_is_offline_and_hash_binds_inputs(self) -> None:
        wrapper = (
            ROOT / "hardware/chisel/run-physical-proxy-toolchain-smoke.sh"
        ).read_text()
        self.assertIn("--network none", wrapper)
        self.assertIn("--security-opt no-new-privileges=true", wrapper)
        self.assertIn("docker image inspect", wrapper)
        self.assertIn("--provenance=false", wrapper)
        self.assertIn("Dockerfile.physical-proxy", wrapper)
        self.assertIn("physical_proxy_smoke.sv", wrapper)
        self.assertIn("physical_proxy_smoke.sdc", wrapper)
        self.assertIn("run-physical-proxy-smoke-in-container.sh", wrapper)
        self.assertIn("performance=not-measured", wrapper)

    def test_smoke_is_not_a_candidate(self) -> None:
        smoke = (ROOT / "hardware/chisel/physical_proxy_smoke.sv").read_text()
        self.assertIn("module PhysicalProxySmoke", smoke)
        self.assertNotIn("StaticStencilRegion", smoke)
        self.assertNotIn("Rocket", smoke)
        self.assertNotIn("Boom", smoke)

    def test_candidate_runner_is_manifest_driven_and_separates_evidence(self) -> None:
        graph_source = (ROOT / "hardware/chisel/StaticStencilRegion.scala").read_text()
        graph_export = (ROOT / "hardware/chisel/export-physical-graph-rtl.sh").read_text()
        self.assertIn("object EmitPhysicalStaticStencilRegion", graph_source)
        self.assertIn("disallowLocalVariables,disallowPackedArrays", graph_source)
        self.assertIn("--main-class EmitPhysicalStaticStencilRegion", graph_export)
        self.assertIn("generated_physical_static", graph_export)
        rocket_export = (
            ROOT / "hardware/chisel/export-physical-rocket-rtl.sh"
        ).read_text()
        self.assertNotIn("+[ -d", rocket_export)
        self.assertIn("[ -d \"$source_dir\" ]", rocket_export)
        self.assertIn(".top.f", rocket_export)
        self.assertIn('filelist="$source_dir/', rocket_export)
        self.assertIn("generator_rootfs_sha256", rocket_export)
        self.assertIn("rtl_filelist_sha256", rocket_export)
        self.assertIn("raveil-chipyard-physical-yosys-rocket-v1", rocket_export)
        self.assertIn("RAVEIL-PHYSICAL-ROCKET-BUILD-V1", rocket_export)
        self.assertIn("shared-elaboration-identical", rocket_export)
        self.assertIn("physical lowering changed normalized $suffix", rocket_export)
        self.assertIn("physical lowering changed module hierarchy", rocket_export)
        self.assertIn("lowering-provenance.txt", rocket_export)
        self.assertIn("compatibility_lowering=disallowPackedArrays", rocket_export)
        self.assertNotIn('cp -a "$source_dir"', rocket_export)
        physical_build = (
            ROOT / "hardware/chisel/run-physical-yosys-rocket-build.sh"
        ).read_text()
        self.assertIn("RAVEIL_PHYSICAL_YOSYS_FLOW=1", physical_build)
        self.assertIn("RAVEIL_BUILD_ONLY=1", physical_build)
        self.assertIn("raveil-chipyard-physical-yosys-rocket-v1", physical_build)
        owned_runner = (
            ROOT / "hardware/chisel/run-owned-cpu-memory-smoke.sh"
        ).read_text()
        self.assertIn('if [ "$RAVEIL_PHYSICAL_YOSYS_FLOW" = 1 ]; then', owned_runner)
        self.assertIn("ENABLE_YOSYS_FLOW=1", owned_runner)
        self.assertNotIn('ENABLE_YOSYS_FLOW="$RAVEIL_PHYSICAL_YOSYS_FLOW"', owned_runner)
        self.assertIn("RAVEIL_CHIPYARD_COMMON_MK_SHA256", owned_runner)
        self.assertIn("RAVEIL-PHYSICAL-ROCKET-BUILD-V1", owned_runner)
        wrapper = (
            ROOT / "hardware/chisel/run-physical-proxy-synthesis.sh"
        ).read_text()
        self.assertIn("variant-field", wrapper)
        self.assertIn("seal-raw", wrapper)
        self.assertIn("--raw-dir", wrapper)
        self.assertIn("--derived-dir", wrapper)
        self.assertIn("target=/runner.sh,readonly", wrapper)
        self.assertNotIn("/work/run-physical-proxy-synthesis-in-container.sh", wrapper)

        inner = (
            ROOT / "hardware/chisel/run-physical-proxy-synthesis-in-container.sh"
        ).read_text()
        self.assertLess(inner.index("blackbox N:%s"), inner.index("hierarchy -check"))
        self.assertNotIn("hierarchy -top %s", inner)
        self.assertIn("select -assert-any N:%s", inner)
        self.assertIn("select -assert-count 1 t:%s", inner)
        self.assertNotIn("select -assert-count 1 m:%s", inner)
        self.assertIn("select -assert-any =N:%s =A:blackbox=1", inner)
        self.assertIn("select -clear", inner)
        self.assertIn("blackbox_selection_mode=yosys-module-name-single-instance-v1", inner)
        self.assertLess(inner.index("read_liberty -lib"), inner.index("check -assert"))
        self.assertIn("get_property -object_type port", inner)
        self.assertIn("foreach port [all_inputs]", inner)
        self.assertNotIn("remove_from_collection", inner)
        self.assertIn("report_clock_properties", inner)
        self.assertNotIn("report_clocks\n", inner)
        self.assertIn("mapped_check_mode=liberty-aware-v1", inner)
        self.assertIn("sta_constraint_mode=foreach-non-clock-inputs-v1", inner)
        self.assertLess(
            inner.index("write_verilog -noattr -blackboxes"),
            inner.index("read_liberty -lib"),
        )
        self.assertIn("cat /tmp/partition-blackboxes.v /tmp/mapped-core.v", inner)
        self.assertIn("mapped_blackbox_declarations=explicit-yosys-stubs-v1", inner)
        self.assertIn("stat -json", inner)
        self.assertIn("tool-identity.txt", inner)
        self.assertIn("set_input_delay 1.000", inner)
        self.assertIn("set_output_delay 1.000", inner)
        self.assertIn("[ -f /evidence/container.log ]", inner)
        self.assertIn("[ ! -s /evidence/container.log ]", inner)
        self.assertIn("! -name container.log", inner)


class PhysicalProxyEvidenceTests(unittest.TestCase):
    def _manifest(self, rtl_sha256: str) -> dict[str, object]:
        authority = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True
        ).stdout.strip()
        toolchain = {
            "image_id": "sha256:" + "1" * 64,
            "yosys_sha256": "2" * 64,
            "opensta_sha256": "3" * 64,
            "liberty_sha256": "4" * 64,
            "conda_environment_sha256": "5" * 64,
            "system_packages_sha256": "6" * 64,
        }
        variants = {}
        for variant, role in (
            ("static-graph", "graph-candidate-local-incremental"),
            ("rocket-in-order", "rocket-fallback-denominator"),
        ):
            variants[variant] = {
                "top": "Top" if variant == "static-graph" else "RocketTop",
                "blackboxes": ["CommonMemory"],
                "rtl_sha256": rtl_sha256,
                "partition_role": role,
                "configuration_id": variant + "-fixture-v1",
                "source_sha256": "7" * 64,
                "generator_image_id": "sha256:" + "8" * 64,
                "clock_port": "clock",
                "missing_components": ["placed-routing", "clock-tree"],
            }
        return {
            "schema": t0044_physical.SCHEMA,
            "status": "frozen",
            "experiment_id": "EXP-0009",
            "task_id": "T-0044",
            "implementation_authority": authority,
            "matrix": ["static-graph", "rocket-in-order"],
            "clock_period_ns": 20.0,
            "constraints": {
                "clock_port": "clock",
                "input_delay_ns": 1.0,
                "output_delay_ns": 1.0,
            },
            "corner": "sky130_fd_sc_hd__tt_025C_1v80",
            "partition_policy": {
                "common_fixture": "excluded-at-explicit-candidate-boundary",
                "common_memory": "excluded-at-explicit-candidate-boundary",
                "fallback_composition": "rocket-fallback-plus-graph-incremental",
                "whole_system_claim": False,
            },
            "collector_policy": {
                "blackbox_selection_mode": "yosys-module-name-single-instance-v1",
                "blackbox_before_checked_hierarchy": True,
                "mapped_check_mode": "liberty-aware-v1",
                "sta_constraint_mode": "foreach-non-clock-inputs-v1",
                "mapped_blackbox_declarations": "explicit-yosys-stubs-v1",
            },
            "toolchain": toolchain,
            "variants": variants,
            "decision_rules": {
                "incremental_area_ratio_no_go_above": 0.25,
                "graph_timing_miss_only_if_rocket_meets": True,
                "pass_label": "advance-to-integrated-physical",
                "incomplete_label": "pause-boundary",
            },
            "report_contract": {
                "raw_schema": "raveil.t0044-physical-run/v1",
                "result_schema": "raveil.t0044-physical-result/v1",
                "matrix_schema": "raveil.t0044-physical-matrix/v1",
                "deterministic_reruns_are_samples": False,
                "evidence_class": "synthesis-estimate",
            },
        }

    def _fixture(self, root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
        rtl = root / "rtl"
        raw = root / "raw"
        rtl.mkdir()
        raw.mkdir()
        (rtl / "top.v").write_text("module Top(input clock); endmodule\n")
        manifest = root / "manifest.json"
        manifest.write_text(
            json.dumps(self._manifest(t0044_physical.tree_sha256(rtl)), sort_keys=True) + "\n"
        )
        (raw / "yosys.log").write_text("Chip area for module '\\Top': 12.500000\n")
        (raw / "opensta.log").write_text(
            "Startpoint: a\nEndpoint: b\nPath Group: clock\n0.250000 slack (MET)\n"
        )
        (raw / "mapped.v").write_text(
            "module CommonMemory(input clock); endmodule\n"
            "module Top(input clock); CommonMemory memory(clock); endmodule\n"
        )
        (raw / "stat.json").write_text(
            json.dumps({"modules": {"\\Top": {"area": 12.5, "num_cells": 5}}}) + "\n"
        )
        for name in ("constraint.sdc", "synthesis.ys", "timing.tcl"):
            (raw / name).write_text(name + "\n")
        (raw / "rtl-files.txt").write_text("/rtl/top.v\n")
        (raw / "blackboxes.txt").write_text("CommonMemory\n")
        (raw / "container.log").write_text(
            "RAVEIL-PHYSICAL-SYNTHESIS-V1 status=OK performance=candidate-data\n"
        )
        (raw / "tool-identity.txt").write_text(
            "yosys_sha256=" + "2" * 64 + "\n"
            "opensta_sha256=" + "3" * 64 + "\n"
            "liberty_sha256=" + "4" * 64 + "\n"
            "clock_port=clock\nclock_period_ns=20.000\n"
            "input_delay_ns=1.000\noutput_delay_ns=1.000\n"
            "blackbox_selection_mode=yosys-module-name-single-instance-v1\n"
            "mapped_check_mode=liberty-aware-v1\n"
            "sta_constraint_mode=foreach-non-clock-inputs-v1\n"
            "mapped_blackbox_declarations=explicit-yosys-stubs-v1\n"
        )
        t0044_physical.write_run_metadata(
            manifest, "static-graph", "Top", "CommonMemory", rtl, raw
        )
        return manifest, rtl, raw

    def test_sealed_raw_derives_complete_partition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            manifest, rtl, raw = self._fixture(root)
            t0044_physical.seal_raw(manifest, "static-graph", raw)
            result = t0044_physical.derive_one(
                manifest, "static-graph", rtl, raw, root / "derived"
            )
            self.assertEqual(result["mapped_cells"], 5)
            self.assertEqual(result["eligibility"], "partition-complete")
            self.assertFalse(result["whole_system_claim"])
            self.assertTrue((root / "derived/result.json").is_file())
            self.assertFalse((raw / "result.json").exists())

    def test_raw_mutation_after_seal_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            manifest, rtl, raw = self._fixture(root)
            t0044_physical.seal_raw(manifest, "static-graph", raw)
            (raw / "yosys.log").write_text("Chip area for module '\\Top': 1.0\n")
            with self.assertRaisesRegex(ValueError, "sealed raw evidence changed"):
                t0044_physical.derive_one(
                    manifest, "static-graph", rtl, raw, root / "derived"
                )

    def test_top_and_blackbox_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            manifest, rtl, raw = self._fixture(root)
            with self.assertRaisesRegex(ValueError, "top drift"):
                t0044_physical.write_run_metadata(
                    manifest, "static-graph", "Wrong", "CommonMemory", rtl, raw
                )
            with self.assertRaisesRegex(ValueError, "blackbox drift"):
                t0044_physical.write_run_metadata(
                    manifest, "static-graph", "Top", "HiddenLogic", rtl, raw
                )

    def test_contradictory_timing_status_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            manifest, rtl, raw = self._fixture(root)
            (raw / "opensta.log").write_text(
                "Startpoint: a\nEndpoint: b\nPath Group: clock\n-0.25 slack (MET)\n"
            )
            t0044_physical.seal_raw(manifest, "static-graph", raw)
            with self.assertRaisesRegex(ValueError, "contradicts"):
                t0044_physical.derive_one(
                    manifest, "static-graph", rtl, raw, root / "derived"
                )

    def test_matrix_composes_fallback_without_whole_system_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            rtl = root / "rtl"
            rtl.mkdir()
            (rtl / "top.v").write_text("module Top; endmodule\n")
            rtl_sha256 = t0044_physical.tree_sha256(rtl)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(self._manifest(rtl_sha256), sort_keys=True) + "\n")
            manifest_sha256 = t0044_physical.sha256_file(manifest)
            results = {}
            for variant, area, timing in (
                ("static-graph", 20.0, True),
                ("rocket-in-order", 100.0, True),
            ):
                contract = self._manifest(rtl_sha256)["variants"][variant]
                result = {
                    "schema": "raveil.t0044-physical-result/v1",
                    "variant": variant,
                    "eligibility": "partition-complete",
                    "manifest_sha256": manifest_sha256,
                    "partition_role": contract["partition_role"],
                    "rtl_sha256": rtl_sha256,
                    "whole_system_claim": False,
                    "mapped_area_um2": area,
                    "timing_met": timing,
                    "missing_components": contract["missing_components"],
                }
                path = root / f"{variant}.json"
                path.write_text(json.dumps(result, sort_keys=True) + "\n")
                results[variant] = path
            matrix = t0044_physical.derive_matrix(
                manifest,
                results["static-graph"],
                results["rocket-in-order"],
                root / "matrix",
            )
            self.assertEqual(matrix["outcome"], "advance-to-integrated-physical")
            self.assertAlmostEqual(matrix["incremental_area_ratio"], 0.2)
            self.assertEqual(matrix["analytical_logic_composition_area_um2"], 120.0)
            self.assertFalse(matrix["whole_system_claim"])
            self.assertIn("common-memory-area", matrix["missing_components"])


if __name__ == "__main__":
    unittest.main()
