from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import tomllib
import unittest
from unittest import mock

from raveil.analysis import analyze_policy_outcomes, headroom_capture
from raveil.cli import main as cli_main
from raveil.experiment_runner import analyze_bundle, measurement_order, run_experiment, seal_bundle
from raveil.experiment_schema import (
    BenchmarkCandidate,
    BenchmarkManifest,
    PolicyOutcome,
    WorkloadSpec,
    validate_backend_evidence,
)
from raveil.native_backend import NativeCBackend
from raveil.power import PowermetricsSampler, parse_powermetrics
from raveil.research_bundle import ResearchBundle, make_run_id, sha256_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/manifests/gate1-fixed-c-v1.json"
SOURCE = ROOT / "benchmarks/native/benchmark.c"


class ManifestTests(unittest.TestCase):
    def test_gate1_manifest_preregisters_holdout_dimensions(self) -> None:
        manifest = BenchmarkManifest.load(MANIFEST)
        self.assertEqual(manifest.experiment_id, "EXP-0003")
        self.assertGreaterEqual(len(manifest.workloads), 20)
        self.assertEqual(manifest.repetitions, 15)
        self.assertTrue(manifest.energy.required)
        self.assertEqual(manifest.candidates[0].trusted_baseline, True)
        self.assertGreater(len({w.lineage for w in manifest.workloads}), 1)
        self.assertGreater(len({w.shape_class for w in manifest.workloads}), 1)
        self.assertGreater(len({w.working_set for w in manifest.workloads}), 1)
        self.assertEqual(
            {w.operator_composition for w in manifest.workloads},
            {"gemm-only", "gemm-bias-relu", "two-stage-mlp"},
        )

    def test_measurement_order_is_baseline_first_randomized_and_equal(self) -> None:
        manifest = BenchmarkManifest.load(MANIFEST)
        order = measurement_order(manifest.candidates, manifest.repetitions, 7)
        self.assertTrue(order[0][0].trusted_baseline)
        self.assertEqual(order[0][2], "trusted-baseline")
        self.assertEqual(order, measurement_order(manifest.candidates, manifest.repetitions, 7))
        counts = {candidate.candidate_id: 0 for candidate in manifest.candidates}
        for candidate, _, _ in order:
            counts[candidate.candidate_id] += 1
        self.assertEqual(set(counts.values()), {manifest.repetitions})

    def test_invalid_candidate_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a tile"):
            BenchmarkCandidate("bad", "tiled", 0, "materialized", 0)

    def test_qemu_telemetry_can_only_be_emulation_evidence(self) -> None:
        validate_backend_evidence("qemu-telemetry", "emulation")
        with self.assertRaisesRegex(ValueError, "classified as emulation"):
            validate_backend_evidence("qemu-telemetry", "silicon")

    def test_cli_reports_preflight_failure_without_traceback(self) -> None:
        error = io.StringIO()
        with mock.patch(
            "raveil.cli.run_experiment", side_effect=RuntimeError("powermetrics unavailable")
        ), contextlib.redirect_stderr(error):
            result = cli_main(
                ["experiment", "run", "--manifest", "benchmarks/manifests/gate1-fixed-c-v1.json"]
            )
        self.assertEqual(result, 2)
        self.assertEqual(error.getvalue(), "error: powermetrics unavailable\n")


class NativeBackendTests(unittest.TestCase):
    def test_all_candidate_families_match_int64_reference_checksum(self) -> None:
        manifest = BenchmarkManifest.load(MANIFEST)
        with tempfile.TemporaryDirectory() as directory:
            backend = NativeCBackend(
                SOURCE,
                Path(directory) / "benchmark",
                compiler_flags=(
                    "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-D_POSIX_C_SOURCE=200809L",
                ),
                warmups=1,
            )
            backend.compile()
            for family in ("gemm", "gemm_bias_relu", "mlp2"):
                workload = WorkloadSpec(
                    f"test-{family}", family, 9, 11, 7, "test", "odd",
                    "test-fit", family, 1,
                )
                for candidate in manifest.candidates:
                    with self.subTest(family=family, candidate=candidate.candidate_id):
                        result = backend.measure(workload, candidate)
                        self.assertTrue(result.semantic_valid, result.failure)
                        self.assertEqual(result.checksum, result.reference_checksum)
                        self.assertGreater(result.latency_ns or 0, 0)

    def test_timeout_and_dimension_guard_are_fail_closed(self) -> None:
        candidate = BenchmarkCandidate("baseline", "ijk", 0, "materialized", 0, True)
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "slow-benchmark"
            binary.write_text("#!/bin/sh\nsleep 1\n", encoding="utf-8")
            binary.chmod(0o755)
            backend = NativeCBackend(SOURCE, binary, timeout_seconds=0.01, warmups=1)
            workload = WorkloadSpec("timeout", "gemm", 8, 8, 8, "t", "t", "t", "t")
            result = backend.measure(workload, candidate)
            self.assertEqual(result.failure, "timeout")

            compiled = Path(directory) / "compiled"
            backend = NativeCBackend(
                SOURCE,
                compiled,
                compiler_flags=("-O2", "-std=c11", "-D_POSIX_C_SOURCE=200809L"),
                warmups=1,
            )
            backend.compile()
            too_large = WorkloadSpec("overflow", "gemm", 513, 8, 8, "t", "t", "t", "t")
            result = backend.measure(too_large, candidate)
            self.assertFalse(result.semantic_valid)
            self.assertIn("invalid arguments", result.failure)


class PowerTests(unittest.TestCase):
    def test_powermetrics_energy_and_thermal_contract(self) -> None:
        valid = parse_powermetrics(
            "CPU Power: 750 mW\nCurrent pressure level: Nominal\n"
            "CPU Power: 1.25 W\nCurrent pressure level: Nominal\n",
            ("Nominal",),
        )
        self.assertTrue(valid.valid)
        self.assertEqual(valid.cpu_power_mw, 1000.0)
        missing = parse_powermetrics("Current pressure level: Nominal\n", ("Nominal",))
        self.assertFalse(missing.valid)
        changed = parse_powermetrics(
            "CPU Power: 1 W\nCurrent pressure level: Nominal\n"
            "Current pressure level: Heavy\n",
            ("Nominal",),
        )
        self.assertFalse(changed.valid)
        self.assertIn("changed", changed.failure)

    def test_powermetrics_preflight_requires_cached_noninteractive_privilege(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "fake-sudo"
            fake.write_text(
                "#!/bin/sh\n"
                "echo 'sudo: a password is required' >&2\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            sampler = PowermetricsSampler(20, ("Nominal",), (str(fake),))
            result = sampler.preflight()
            self.assertFalse(result.valid)
            self.assertIn("sudo -v", result.failure)

    def test_powermetrics_preflight_accepts_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "fake-powermetrics"
            fake.write_text(
                "#!/bin/sh\n"
                "echo 'CPU Power: 800 mW'\n"
                "echo 'Current pressure level: Nominal'\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            sampler = PowermetricsSampler(20, ("Nominal",), (str(fake),))
            result = sampler.preflight()
            self.assertTrue(result.valid, result.failure)
            self.assertEqual(result.cpu_power_mw, 800.0)


class AnalysisTests(unittest.TestCase):
    @staticmethod
    def outcome(workload: str, policy: str) -> PolicyOutcome:
        selected_latency = {"cold": 100.0, "bounded": 90.0, "full-history": 89.0}[policy]
        selected_energy = {"cold": 10.0, "bounded": 9.0, "full-history": 8.9}[policy]
        retrieval = {"cold": 10, "bounded": 100, "full-history": 1000}[policy]
        return PolicyOutcome(
            run_id="20260808T000000Z-abcdef123-12345678",
            workload_id=workload,
            policy=policy,
            selected_candidate_id=f"selected-{policy}",
            baseline_latency_ns=110.0,
            selected_latency_ns=selected_latency,
            oracle_latency_ns=85.0,
            baseline_energy_mj=11.0,
            selected_energy_mj=selected_energy,
            oracle_energy_mj=8.5,
            measurement_budget=3,
            retrieval_latency_ns=retrieval,
            active_memory_records=128 if policy == "bounded" else 1000,
            cold_evidence_records=2000,
        )

    def test_gate_metrics_cover_energy_hcr_bootstrap_ntr_and_retrieval(self) -> None:
        outcomes = [
            self.outcome(f"holdout-{index}", policy)
            for index in range(20)
            for policy in ("cold", "bounded", "full-history")
        ]
        result = analyze_policy_outcomes(outcomes, active_limit=256, bootstrap_samples=500)
        self.assertTrue(result["gate_ready"], result["unmet"])
        metrics = result["metrics"]
        self.assertAlmostEqual(metrics["latency_median_improvement"], 0.1)
        self.assertAlmostEqual(metrics["energy_median_improvement"], 0.1)
        self.assertEqual(metrics["joint_negative_transfer_rate"], 0.0)
        self.assertLess(
            metrics["bounded_retrieval_p95_ns"], metrics["full_history_retrieval_p95_ns"]
        )
        self.assertGreater(headroom_capture(100, 90, 80), 0)

    def test_joint_negative_transfer_is_fail_closed(self) -> None:
        outcomes = [
            self.outcome(f"holdout-{index}", policy)
            for index in range(20)
            for policy in ("cold", "bounded", "full-history")
        ]
        for workload in ("holdout-0", "holdout-1"):
            bad = self.outcome(workload, "bounded")
            outcomes[outcomes.index(bad)] = replace(bad, selected_energy_mj=10.3)
        result = analyze_policy_outcomes(outcomes, active_limit=256, bootstrap_samples=200)
        self.assertFalse(result["gate_ready"])
        self.assertIn("joint NTR exceeds 5%", result["unmet"])


class BundleTests(unittest.TestCase):
    def test_run_analyze_seal_lifecycle_without_energy_does_not_claim_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            value["energy"]["required"] = False
            value["candidates"] = value["candidates"][:2]
            value["workloads"] = [
                {
                    **workload,
                    "m": 4 + index % 2,
                    "n": 5 + index % 3,
                    "k": 6 + index % 2,
                    "inner_iterations": 1,
                }
                for index, workload in enumerate(value["workloads"][:20])
            ]
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch("raveil.experiment_runner.require_clean_worktree"):
                bundle, valid = run_experiment(manifest_path, root / "artifacts")
            self.assertTrue(valid)
            analysis = analyze_bundle(bundle, bootstrap_samples=100)
            self.assertEqual(analysis["gate_conclusion"], "incomplete")
            self.assertFalse(analysis["policy"]["gate_ready"])
            sealed = seal_bundle(bundle)
            self.assertEqual(bundle.verify()["bundle_hash"], sealed["bundle_hash"])
            os.chmod(bundle.path, stat.S_IRWXU)

    def test_seal_records_hashes_and_refuses_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_id = make_run_id("abcdef1234567", "1234567890abcdef", datetime(2026, 8, 8, tzinfo=timezone.utc))
            bundle = ResearchBundle(root, "EXP-0003", run_id)
            bundle.create()
            bundle.append_jsonl("measurement.jsonl", {"valid": True})
            bundle.write_json("analysis.json", {"gate": "incomplete"})
            value = bundle.seal(("raveil", "experiment", "seal"), {"test": "1"}, {"machine": "arm64"})
            self.assertEqual(bundle.verify()["bundle_hash"], value["bundle_hash"])
            self.assertTrue((bundle.path / "completion-marker.json").is_file())
            with self.assertRaisesRegex(RuntimeError, "sealed bundle"):
                bundle.write_json("late.json", {})
            os.chmod(bundle.path, stat.S_IRWXU)
            (bundle.path / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "file set changed"):
                bundle.verify()
            (bundle.path / "unexpected.txt").unlink()

    def test_seal_rejects_machine_local_paths_and_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_id = make_run_id("abcdef1234567", "1234567890abcdef", datetime(2026, 8, 8, tzinfo=timezone.utc))
            bundle = ResearchBundle(Path(directory), "EXP-0003", run_id)
            bundle.create()
            bundle.append_jsonl("measurement.jsonl", {"path": "/Users/example/raw"})
            with self.assertRaisesRegex(ValueError, "machine-local"):
                bundle.seal(("seal",), {}, {})

    def test_sync_uses_immutable_copy_download_check_and_marker_last(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_id = make_run_id("abcdef1234567", "1234567890abcdef", datetime(2026, 8, 8, tzinfo=timezone.utc))
            bundle = ResearchBundle(root / "artifacts", "EXP-0003", run_id)
            bundle.create()
            bundle.append_jsonl("measurement.jsonl", {"valid": True})
            bundle.write_json("analysis.json", {"gate": "incomplete"})
            bundle.seal(("seal",), {}, {})
            log = root / "rclone.log"
            fail = root / "fail-check"
            partial = root / "partial-remote"
            completed = root / "completed-remote"
            fake = root / "rclone"
            fake.write_text(
                "#!/bin/sh\n"
                f"printf '%s\\n' \"$*\" >> '{log}'\n"
                f"if [ \"$1\" = lsf ] && [ -f '{completed}' ]; then echo completion-marker.json; exit 0; fi\n"
                f"if [ \"$1\" = lsf ] && [ -f '{partial}' ]; then echo bundle-manifest.json; exit 0; fi\n"
                "if [ \"$1\" = lsf ]; then exit 3; fi\n"
                f"if [ \"$1\" = check ] && [ -f '{fail}' ]; then exit 1; fi\n"
                f"if [ \"$1\" = cat ]; then cat '{bundle.path / 'completion-marker.json'}'; fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            remote = bundle.sync("fake:Raveil/research-data", rclone=str(fake))
            self.assertEqual(remote, f"fake:Raveil/research-data/EXP-0003/{run_id}")
            commands = log.read_text(encoding="utf-8").splitlines()
            self.assertIn("--immutable", commands[1])
            self.assertIn("--download", commands[2])
            self.assertTrue(commands[-2].startswith("copyto "))
            self.assertTrue(commands[-1].startswith("cat "))
            partial.write_text("partial", encoding="utf-8")
            self.assertEqual(
                bundle.sync("fake:Raveil/research-data", rclone=str(fake)), remote
            )
            fail.write_text("fail", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "remote hash/size"):
                bundle.sync("fake:Raveil/research-data", rclone=str(fake))
            fail.unlink()
            completed.write_text("complete", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "completed remote"):
                bundle.sync("fake:Raveil/research-data", rclone=str(fake))
            os.chmod(bundle.path, stat.S_IRWXU)


class AgentBoundaryTests(unittest.TestCase):
    def test_librarian_is_read_only_and_skill_metadata_is_valid(self) -> None:
        agent = tomllib.loads(
            (ROOT / ".codex/agents/raveil-librarian.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(agent["sandbox_mode"], "read-only")
        skill = (ROOT / ".agents/skills/raveil-context-librarian/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(skill.startswith("---\nname: raveil-context-librarian\n"))
        self.assertIn("description:", skill.split("---", 2)[1])
        self.assertNotIn("[TODO", skill)

    def test_role_write_boundaries_are_explicit(self) -> None:
        agents = {
            path.stem: tomllib.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / ".codex/agents").glob("*.toml")
        }
        expected = {
            "raveil-project-manager", "raveil-experience-implementer",
            "raveil-systems-implementer", "raveil-measurement-implementer",
            "raveil-performance-reviewer", "raveil-security-reviewer",
            "raveil-tester", "raveil-researcher", "raveil-librarian",
        }
        self.assertEqual(set(agents), expected)
        for name in ("raveil-performance-reviewer", "raveil-security-reviewer", "raveil-librarian"):
            self.assertEqual(agents[name]["sandbox_mode"], "read-only")
        self.assertIn(
            "Write only docs/research/reviews/",
            agents["raveil-researcher"]["developer_instructions"],
        )
        self.assertIn(
            "Do not edit tracked files",
            agents["raveil-tester"]["developer_instructions"],
        )
        for name in (
            "raveil-experience-implementer",
            "raveil-systems-implementer",
            "raveil-measurement-implementer",
        ):
            self.assertIn("Do not edit", agents[name]["developer_instructions"])


if __name__ == "__main__":
    unittest.main()
