from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import tempfile
import time
import tomllib
import unittest
from unittest import mock

from raveil.analysis import (
    analyze_policy_outcomes,
    headroom_capture,
    hierarchical_bootstrap_median_improvement_ci,
)
from raveil.cli import build_parser, main as cli_main
from raveil.experiment_runner import (
    analyze_bundle,
    measurement_order,
    run_experiment,
    seal_bundle,
    wait_for_thermal_recovery,
)
from raveil.experiment_schema import (
    BenchmarkCandidate,
    BenchmarkManifest,
    EnergyContract,
    MeasurementRecord,
    PolicyOutcome,
    PolicySelection,
    WorkloadSpec,
    validate_backend_evidence,
)
from raveil.native_backend import NativeCBackend
from raveil.power import PowerSample, PowermetricsSampler, parse_powermetrics
from raveil.policy_comparison import (
    COMPARISON_POLICIES,
    generate_policy_outcomes,
    generate_policy_selections,
)
from raveil.research_bundle import ResearchBundle, make_run_id, manifest_hash, sha256_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/manifests/gate1-fixed-c-v1.json"
HISTORY_MANIFEST = ROOT / "benchmarks/manifests/gate1-fixed-c-history-v1.json"
PILOT_MANIFEST = ROOT / "benchmarks/manifests/gate1-powermetrics-pilot-v1.json"
SOURCE = ROOT / "benchmarks/native/benchmark.c"
HELPER_SOURCE = ROOT / "tools/powermetrics_helper.c"


class ManifestTests(unittest.TestCase):
    def test_gate1_manifest_preregisters_holdout_dimensions(self) -> None:
        manifest = BenchmarkManifest.load(MANIFEST)
        self.assertEqual(manifest.experiment_id, "EXP-0003")
        self.assertEqual(manifest.stage, "full")
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
        self.assertEqual(manifest.energy.minimum_samples, 3)

    def test_gate1_history_manifest_is_disjoint_with_matching_candidates(self) -> None:
        target = BenchmarkManifest.load(MANIFEST)
        history = BenchmarkManifest.load(HISTORY_MANIFEST)
        self.assertEqual(len(history.workloads), len(target.workloads))
        self.assertFalse(
            {workload.workload_id for workload in history.workloads}
            & {workload.workload_id for workload in target.workloads}
        )
        self.assertEqual(
            [candidate.candidate_id for candidate in history.candidates],
            [candidate.candidate_id for candidate in target.candidates],
        )
        self.assertNotEqual(
            {(workload.m, workload.n, workload.k) for workload in history.workloads},
            {(workload.m, workload.n, workload.k) for workload in target.workloads},
        )
        history_summary_records = len(history.workloads) * len(history.candidates)
        self.assertLess(target.active_memory_limit, history_summary_records)
        self.assertEqual(target.active_memory_limit, 64)

    def test_tvm_manifests_pin_official_adapter_and_reuse_fixed_contract(self) -> None:
        fixed_target = BenchmarkManifest.load(MANIFEST)
        fixed_history = BenchmarkManifest.load(HISTORY_MANIFEST)
        tvm_target = BenchmarkManifest.load(
            ROOT / "benchmarks/manifests/gate1-tvm-v1.json"
        )
        tvm_history = BenchmarkManifest.load(
            ROOT / "benchmarks/manifests/gate1-tvm-history-v1.json"
        )
        self.assertEqual(tvm_target.backend, "tvm-meta-schedule")
        self.assertEqual(tvm_target.tvm_version, "0.25.0.post1")
        self.assertEqual(tvm_target.workloads, fixed_target.workloads)
        self.assertEqual(tvm_target.candidates, fixed_target.candidates)
        self.assertEqual(tvm_history.workloads, fixed_history.workloads)
        self.assertEqual(tvm_history.candidates, fixed_history.candidates)

    def test_powermetrics_pilot_is_short_and_not_a_gate_manifest(self) -> None:
        manifest = BenchmarkManifest.load(PILOT_MANIFEST)
        self.assertEqual(manifest.stage, "pilot")
        self.assertEqual(manifest.repetitions, 5)
        self.assertEqual(len(manifest.workloads), 6)
        self.assertEqual({workload.family for workload in manifest.workloads}, {
            "gemm", "gemm_bias_relu", "mlp2"
        })
        self.assertTrue(all(workload.inner_iterations > 512 for workload in manifest.workloads))

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

    def test_legacy_measurement_record_defaults_power_sample_count(self) -> None:
        legacy = {
            "schema": "raveil.measurement-record/v1",
            "run_id": "legacy-run",
            "sequence": 1,
            "measured_at_utc": "2026-08-08T00:00:00Z",
            "workload_id": "legacy-workload",
            "candidate_id": "legacy-candidate",
            "repetition": 0,
            "phase": "trusted-baseline",
            "latency_ns": 100,
            "cpu_power_mw": None,
            "energy_mj": None,
            "checksum": "abc",
            "reference_checksum": "abc",
            "semantic_valid": True,
            "measurement_valid": True,
            "failure": "",
            "thermal_level": None,
            "evidence_class": "silicon",
        }
        self.assertEqual(MeasurementRecord.from_dict(legacy).power_sample_count, 0)

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

    def test_cli_exposes_standalone_preflight(self) -> None:
        output = io.StringIO()
        with mock.patch(
            "raveil.cli.preflight_experiment",
            return_value=PowerSample(850.0, "Nominal", True, sample_count=1),
        ), contextlib.redirect_stdout(output):
            result = cli_main(
                ["experiment", "preflight", "--manifest", str(PILOT_MANIFEST)]
            )
        self.assertEqual(result, 0)
        self.assertIn("thermal=Nominal", output.getvalue())

    def test_cli_exposes_policy_plan_and_run_selection(self) -> None:
        parser = build_parser()
        plan = parser.parse_args(
            [
                "experiment",
                "plan",
                "--manifest",
                "target.json",
                "--source-run",
                "run-id",
                "--output",
                "plan.jsonl",
            ]
        )
        self.assertEqual(plan.source_run, "run-id")
        run = parser.parse_args(
            [
                "experiment",
                "run",
                "--manifest",
                "target.json",
                "--policy-selections",
                "plan.jsonl",
            ]
        )
        self.assertEqual(run.policy_selections, "plan.jsonl")


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
            with self.assertRaisesRegex(ValueError, "exceeds native safety bounds"):
                WorkloadSpec("overflow", "gemm", 513, 8, 8, "t", "t", "t", "t")

            long_window = WorkloadSpec(
                "long-window", "gemm", 8, 8, 8, "t", "t", "t", "t", 600
            )
            result = backend.measure(long_window, candidate)
            self.assertTrue(result.semantic_valid, result.failure)


class PowerTests(unittest.TestCase):
    def test_cooldown_requires_two_consecutive_stable_preflights(self) -> None:
        sampler = mock.Mock()
        sampler.preflight.side_effect = [
            PowerSample(None, "Moderate", False, "unstable thermal level: Moderate"),
            PowerSample(500.0, "Nominal", True),
            PowerSample(450.0, "Nominal", True),
        ]
        sleeper = mock.Mock()
        observations = wait_for_thermal_recovery(
            sampler,
            minimum_seconds=120,
            maximum_seconds=600,
            check_interval_seconds=30,
            sleep=sleeper,
        )
        self.assertEqual([item["valid"] for item in observations], [False, True, True])
        self.assertEqual(sleeper.call_args_list, [mock.call(120), mock.call(30), mock.call(30)])

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
        insufficient = parse_powermetrics(
            "CPU Power: 700 mW\nCurrent pressure level: Nominal\n"
            "CPU Power: 800 mW\nCurrent pressure level: Nominal\n",
            ("Nominal",),
            minimum_samples=3,
        )
        self.assertFalse(insufficient.valid)
        self.assertEqual(insufficient.sample_count, 2)
        self.assertIn("required 3", insufficient.failure)

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
            sampler = PowermetricsSampler(20, ("Nominal",), command_prefix=(str(fake),))
            result = sampler.preflight()
            self.assertFalse(result.valid)
            self.assertIn("not authorized", result.failure)

    def test_powermetrics_preflight_accepts_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / "fake-powermetrics"
            fake.write_text(
                "#!/bin/sh\n"
                "test \"$*\" = '--sample-rate 20 --sample-count 1' || exit 64\n"
                "echo 'CPU Power: 800 mW'\n"
                "echo 'Current pressure level: Nominal'\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            sampler = PowermetricsSampler(20, ("Nominal",), command_prefix=(str(fake),))
            result = sampler.preflight()
            self.assertTrue(result.valid, result.failure)
            self.assertEqual(result.cpu_power_mw, 800.0)

    def test_measure_waits_for_and_excludes_sampler_readiness_sample(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "fake-powermetrics"
            started = root / "measurement-started"
            emitted = root / "measurement-samples"
            fake.write_text(
                "#!/bin/sh\n"
                f"started={shlex.quote(str(started))}\n"
                f"emitted={shlex.quote(str(emitted))}\n"
                "trap ':' INFO\n"
                "trap 'exit 0' TERM\n"
                "echo 'CPU Power: 100 mW'\n"
                "echo 'Current pressure level: Nominal'\n"
                "while test ! -f \"$started\"; do sleep 0.01; done\n"
                "for power in 900 900 900; do\n"
                "  echo \"CPU Power: $power mW\"\n"
                "  echo 'Current pressure level: Nominal'\n"
                "  echo emitted >> \"$emitted\"\n"
                "done\n"
                "while true; do :; done\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            raw = root / "raw.txt"
            sampler = PowermetricsSampler(
                20, ("Nominal",), minimum_samples=3, command_prefix=(str(fake),)
            )
            def wait_for_emitted_samples() -> None:
                started.touch()
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    if emitted.exists() and len(emitted.read_text().splitlines()) >= 3:
                        return
                    time.sleep(0.001)
                self.fail("fake sampler did not emit three measurement samples")

            result, power = sampler.measure(wait_for_emitted_samples, raw)
            self.assertIsNone(result)
            self.assertTrue(power.valid, power.failure)
            self.assertGreaterEqual(power.sample_count, 3)
            self.assertEqual(power.cpu_power_mw, 900.0)
            self.assertIn("RAVEIL MEASUREMENT WINDOW", raw.read_text(encoding="utf-8"))

    def test_measure_preserves_samples_buffered_after_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "fake-powermetrics"
            fake.write_text(
                "#!/bin/sh\n"
                "trap ':' INFO\n"
                "trap 'exit 0' TERM\n"
                "echo 'CPU Power: 100 mW'\n"
                "echo 'Current pressure level: Nominal'\n"
                "for power in 800 900 1000; do\n"
                "  echo \"CPU Power: $power mW\"\n"
                "  echo 'Current pressure level: Nominal'\n"
                "done\n"
                "while true; do sleep 1; done\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            raw = root / "raw.txt"
            sampler = PowermetricsSampler(
                20, ("Nominal",), minimum_samples=3, command_prefix=(str(fake),)
            )
            result, power = sampler.measure(lambda: None, raw)
            self.assertIsNone(result)
            self.assertTrue(power.valid, power.failure)
            self.assertEqual(power.sample_count, 3)
            self.assertEqual(power.cpu_power_mw, 900.0)

    def test_default_helper_fails_closed_before_sudo_when_not_installed(self) -> None:
        sampler = PowermetricsSampler(100, ("Nominal",))
        with mock.patch.object(Path, "lstat", side_effect=FileNotFoundError):
            result = sampler.preflight()
        self.assertFalse(result.valid)
        self.assertIn("not installed", result.failure)

    def test_default_helper_rejects_untrusted_file_metadata_before_sudo(self) -> None:
        sampler = PowermetricsSampler(100, ("Nominal",))
        cases = (
            (stat.S_IFLNK | 0o777, 0, "non-symlink"),
            (stat.S_IFREG | 0o755, os.getuid(), "owned by root"),
            (stat.S_IFREG | 0o775, 0, "group/other writable"),
        )
        for mode, owner, expected in cases:
            with self.subTest(expected=expected), mock.patch.object(
                Path,
                "lstat",
                return_value=os.stat_result((mode, 0, 0, 1, owner, 0, 0, 0, 0, 0)),
            ), mock.patch("raveil.power.subprocess.run") as run:
                result = sampler.preflight()
            self.assertFalse(result.valid)
            self.assertIn(expected, result.failure)
            run.assert_not_called()


class PowermetricsHelperTests(unittest.TestCase):
    def test_manifest_interval_cannot_exceed_helper_boundary(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 20 and 1000"):
            EnergyContract(True, "powermetrics", 1001)

    def test_helper_is_compiled_and_rejects_privilege_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "raveil-powermetrics"
            subprocess.run(
                (
                    "cc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    str(HELPER_SOURCE), "-o", str(helper),
                ),
                check=True,
                capture_output=True,
                text=True,
            )
            version = subprocess.run(
                (str(helper), "--version"), check=True, capture_output=True, text=True
            )
            self.assertEqual(version.stdout.strip(), "raveil-powermetrics-helper/v1")
            for arguments in (
                (),
                ("--sample-rate", "19", "--sample-count", "1"),
                ("--sample-rate", "100", "--sample-count", "2"),
                ("--samplers", "all", "--sample-count", "-1"),
            ):
                with self.subTest(arguments=arguments):
                    rejected = subprocess.run(
                        (str(helper), *arguments), capture_output=True, text=True
                    )
                    self.assertEqual(rejected.returncode, 64)
            unprivileged = subprocess.run(
                (str(helper), "--sample-rate", "100", "--sample-count", "1"),
                capture_output=True,
                text=True,
            )
            self.assertEqual(unprivileged.returncode, 77)
            self.assertIn("authorized sudo", unprivileged.stderr)


class PolicyComparisonTests(unittest.TestCase):
    @staticmethod
    def manifests() -> tuple[BenchmarkManifest, BenchmarkManifest]:
        base = json.loads(MANIFEST.read_text(encoding="utf-8"))
        base["workloads"] = base["workloads"][:20]
        base["candidates"] = base["candidates"][:3]
        base["measurement_budget"] = 2
        base["active_memory_limit"] = 8
        source = json.loads(json.dumps(base))
        target = json.loads(json.dumps(base))
        for workload in source["workloads"]:
            workload["workload_id"] = "source-" + workload["workload_id"]
        for workload in target["workloads"]:
            workload["workload_id"] = "target-" + workload["workload_id"]
        return BenchmarkManifest.from_dict(source), BenchmarkManifest.from_dict(target)

    @staticmethod
    def records(manifest: BenchmarkManifest, run_id: str) -> list[MeasurementRecord]:
        records: list[MeasurementRecord] = []
        sequence = 0
        for workload_index, workload in enumerate(manifest.workloads):
            values = ((100, 10.0), (92 + workload_index % 2, 9.2), (80, 8.0))
            for candidate, (latency, energy) in zip(
                manifest.candidates, values, strict=True
            ):
                for repetition in range(manifest.repetitions):
                    sequence += 1
                    records.append(
                        MeasurementRecord(
                            run_id=run_id,
                            sequence=sequence,
                            measured_at_utc="2026-08-08T00:01:00+00:00",
                            workload_id=workload.workload_id,
                            candidate_id=candidate.candidate_id,
                            repetition=repetition,
                            phase=(
                                "trusted-baseline"
                                if candidate.trusted_baseline and repetition == 0
                                else "randomized"
                            ),
                            latency_ns=latency,
                            cpu_power_mw=100.0,
                            energy_mj=energy,
                            checksum="ok",
                            reference_checksum="ok",
                            semantic_valid=True,
                            measurement_valid=True,
                            failure="",
                            thermal_level="Nominal",
                            power_sample_count=3,
                            evidence_class="silicon",
                        )
                    )
        return records

    def test_generates_equal_budget_six_policy_slates_and_outcomes(self) -> None:
        source, target = self.manifests()
        source_records = self.records(source, "source-run")
        selections = generate_policy_selections(
            target,
            source,
            source_records,
            "0" * 64,
            registered_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
        )
        self.assertEqual(len(selections), len(target.workloads) * len(COMPARISON_POLICIES))
        self.assertEqual({selection.policy for selection in selections}, set(COMPARISON_POLICIES))
        self.assertTrue(
            all(len(selection.candidate_ids) == target.measurement_budget for selection in selections)
        )
        active_sizes = {
            policy: {selection.active_memory_records for selection in selections if selection.policy == policy}
            for policy in COMPARISON_POLICIES
        }
        self.assertEqual(active_sizes["cold"], {0})
        self.assertEqual(active_sizes["full-history"], {len(source.workloads) * len(source.candidates)})
        self.assertEqual(active_sizes["bounded"], {target.active_memory_limit})
        self.assertEqual(active_sizes["fifo"], {target.active_memory_limit})
        self.assertEqual(active_sizes["reservoir"], {target.active_memory_limit})
        self.assertEqual(active_sizes["random"], {target.active_memory_limit})

        target_records = self.records(target, "target-run")
        outcomes = generate_policy_outcomes(target, "target-run", target_records, selections)
        self.assertEqual(len(outcomes), len(selections))
        for outcome, selection in zip(outcomes, selections, strict=True):
            self.assertIn(outcome.selected_candidate_id, selection.candidate_ids)
            self.assertEqual(outcome.measurement_budget, target.measurement_budget)
            self.assertEqual(outcome.retrieval_latency_ns, selection.retrieval_latency_ns)

    def test_source_and_target_workloads_must_be_disjoint(self) -> None:
        source, _ = self.manifests()
        with self.assertRaisesRegex(ValueError, "must be disjoint"):
            generate_policy_selections(
                source, source, self.records(source, "source-run"), "0" * 64
            )


class AnalysisTests(unittest.TestCase):
    RUN_ID = "20260808T000000Z-abcdef123-12345678"

    @staticmethod
    def outcome(workload: str, policy: str) -> PolicyOutcome:
        selected_latency = {
            "cold": 100.0,
            "bounded": 90.0,
            "full-history": 89.0,
            "fifo": 93.0,
            "reservoir": 92.0,
            "random": 94.0,
        }[policy]
        selected_energy = {
            "cold": 10.0,
            "bounded": 9.0,
            "full-history": 8.9,
            "fifo": 9.3,
            "reservoir": 9.2,
            "random": 9.4,
        }[policy]
        retrieval = {
            "cold": 10,
            "bounded": 100,
            "full-history": 1000,
            "fifo": 80,
            "reservoir": 90,
            "random": 85,
        }[policy]
        return PolicyOutcome(
            run_id=AnalysisTests.RUN_ID,
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
            for policy in COMPARISON_POLICIES
        ]
        result = analyze_policy_outcomes(
            outcomes,
            active_limit=256,
            expected_workloads=(f"holdout-{index}" for index in range(20)),
            expected_run_id=self.RUN_ID,
            expected_measurement_budget=3,
            bootstrap_samples=500,
            repetition_samples={
                f"holdout-{index}": (
                    [110.0] * 15,
                    [99.0] * 15,
                    [11.0] * 15,
                    [9.9] * 15,
                )
                for index in range(20)
            },
        )
        self.assertTrue(result["gate_ready"], result["unmet"])
        metrics = result["metrics"]
        self.assertAlmostEqual(metrics["latency_median_improvement"], 0.1)
        self.assertAlmostEqual(metrics["energy_median_improvement"], 0.1)
        self.assertEqual(metrics["joint_negative_transfer_rate"], 0.0)
        self.assertLess(
            metrics["bounded_retrieval_p95_ns"], metrics["full_history_retrieval_p95_ns"]
        )
        self.assertGreater(headroom_capture(100, 90, 80), 0)
        self.assertEqual(set(metrics["policy_metrics"]), set(COMPARISON_POLICIES))
        self.assertEqual(metrics["policy_metrics"]["cold"]["coverage"], 1.0)
        self.assertGreater(
            metrics["latency_improvement_hierarchical_bootstrap_95"][0], 0
        )

    def test_hierarchical_bootstrap_resamples_holdouts_and_repetitions(self) -> None:
        interval = hierarchical_bootstrap_median_improvement_ci(
            {
                f"holdout-{index}": ([100.0] * 15, [90.0] * 15)
                for index in range(20)
            },
            samples=200,
            seed=7,
        )
        self.assertAlmostEqual(interval[0], 0.1)
        self.assertAlmostEqual(interval[1], 0.1)

    def test_joint_negative_transfer_is_fail_closed(self) -> None:
        outcomes = [
            self.outcome(f"holdout-{index}", policy)
            for index in range(20)
            for policy in ("cold", "bounded", "full-history")
        ]
        for workload in ("holdout-0", "holdout-1"):
            bad = self.outcome(workload, "bounded")
            outcomes[outcomes.index(bad)] = replace(bad, selected_energy_mj=10.3)
        result = analyze_policy_outcomes(
            outcomes,
            active_limit=256,
            expected_workloads=(f"holdout-{index}" for index in range(20)),
            expected_run_id=self.RUN_ID,
            expected_measurement_budget=3,
            bootstrap_samples=200,
        )
        self.assertFalse(result["gate_ready"])
        self.assertIn("joint NTR exceeds 5%", result["unmet"])

    def test_policy_outcomes_require_complete_unique_registered_matrix(self) -> None:
        expected = [f"holdout-{index}" for index in range(20)]
        complete = [
            self.outcome(workload, policy)
            for workload in expected
            for policy in ("cold", "bounded", "full-history")
        ]
        cases = {
            "missing": complete[:-1],
            "duplicate": [*complete, complete[0]],
            "unknown-workload": [
                *complete,
                replace(complete[0], workload_id="not-registered"),
            ],
            "wrong-run": [replace(complete[0], run_id="wrong"), *complete[1:]],
            "wrong-budget": [replace(complete[0], measurement_budget=4), *complete[1:]],
        }
        for name, outcomes in cases.items():
            with self.subTest(name=name):
                result = analyze_policy_outcomes(
                    outcomes,
                    active_limit=256,
                    expected_workloads=expected,
                    expected_run_id=self.RUN_ID,
                    expected_measurement_budget=3,
                    bootstrap_samples=20,
                )
                self.assertFalse(result["gate_ready"])
                self.assertTrue(result["unmet"])


class BundleTests(unittest.TestCase):
    def test_mutable_bundle_writes_cannot_escape_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_id = "20260810T000000Z-abcdef123-12345678"
            sibling_run_id = "20260810T000001Z-abcdef123-12345678"
            linked_run_id = "20260810T000002Z-abcdef123-12345678"
            bundle = ResearchBundle(root, "EXP-0003", run_id)
            bundle.create()
            sibling = root / "EXP-0003" / sibling_run_id
            sibling.mkdir()
            outside = root.parent / f"{root.name}-outside.json"
            (bundle.path / "sibling-link").symlink_to(sibling, target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "RUN-ID-local filename"):
                bundle.write_json(f"../{sibling_run_id}/probe.json", {})
            with self.assertRaisesRegex(ValueError, "RUN-ID-local filename"):
                bundle.append_jsonl(f"../{sibling_run_id}/probe.jsonl", {})
            with self.assertRaisesRegex(ValueError, "RUN-ID-local filename"):
                bundle.write_json("sibling-link/probe-via-link.json", {})
            with self.assertRaisesRegex(ValueError, "RUN-ID-local filename"):
                bundle.write_json(str(outside), {})

            self.assertFalse((sibling / "probe.json").exists())
            self.assertFalse((sibling / "probe.jsonl").exists())
            self.assertFalse((sibling / "probe-via-link.json").exists())
            self.assertFalse(outside.exists())

            sibling_target = sibling / "target.json"
            sibling_target.write_text("unchanged\n", encoding="utf-8")
            (bundle.path / "target-link.json").symlink_to(sibling_target)
            with self.assertRaises(OSError):
                bundle.write_json("target-link.json", {})
            self.assertEqual(
                sibling_target.read_text(encoding="utf-8"), "unchanged\n"
            )

            hard_link = bundle.path / "target-hard-link.json"
            os.link(sibling_target, hard_link)
            with self.assertRaisesRegex(ValueError, "single-link regular file"):
                bundle.write_json(hard_link.name, {})
            with self.assertRaisesRegex(ValueError, "single-link regular file"):
                bundle.append_jsonl(hard_link.name, {})
            self.assertEqual(
                sibling_target.read_text(encoding="utf-8"), "unchanged\n"
            )

            (root / "EXP-0003" / linked_run_id).symlink_to(
                sibling, target_is_directory=True
            )
            with self.assertRaisesRegex(ValueError, "must not contain symbolic links"):
                ResearchBundle(root, "EXP-0003", linked_run_id)

            swapped_run_id = "20260810T000003Z-abcdef123-12345678"
            swapped = ResearchBundle(root, "EXP-0003", swapped_run_id)
            swapped.create()
            swapped.path.rmdir()
            swapped.path.symlink_to(sibling, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                swapped.write_json("probe-after-swap.json", {})
            self.assertFalse((sibling / "probe-after-swap.json").exists())

            chain_root = root / "chain-artifacts"
            chain = ResearchBundle(chain_root, "EXP-0003", run_id)
            chain.create()
            experiment_path = chain_root / "EXP-0003"
            saved_experiment = chain_root / "saved-experiment"
            experiment_path.rename(saved_experiment)
            redirected = chain_root / "redirected"
            (redirected / run_id).mkdir(parents=True)
            experiment_path.symlink_to(redirected, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                chain.write_json("probe-after-parent-swap.json", {})
            self.assertFalse(
                (redirected / run_id / "probe-after-parent-swap.json").exists()
            )

    def test_policy_evidence_is_bound_to_preregistration_and_measurements(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            value["candidates"] = value["candidates"][:3]
            value["measurement_budget"] = 2
            manifest = BenchmarkManifest.from_dict(value)
            run_id = make_run_id(
                "abcdef1234567",
                manifest_hash(manifest.to_dict()),
                datetime(2026, 8, 8, tzinfo=timezone.utc),
            )
            bundle = ResearchBundle(root, manifest.experiment_id, run_id)
            bundle.create()
            bundle.write_json("manifest.json", manifest.to_dict())
            baseline_id = manifest.candidates[0].candidate_id
            cold_id = manifest.candidates[1].candidate_id
            selected_id = manifest.candidates[2].candidate_id
            sequence = 0
            for workload in manifest.workloads:
                for candidate_id, latency, energy in (
                    (baseline_id, 100, 10.0),
                    (cold_id, 105, 10.5),
                    (selected_id, 80, 8.0),
                ):
                    for repetition in range(manifest.repetitions):
                        sequence += 1
                        bundle.append_jsonl(
                            "measurement.jsonl",
                            MeasurementRecord(
                                run_id=run_id,
                                sequence=sequence,
                                measured_at_utc="2026-08-08T00:01:00+00:00",
                                workload_id=workload.workload_id,
                                candidate_id=candidate_id,
                                repetition=repetition,
                                phase=(
                                    "trusted-baseline"
                                    if candidate_id == baseline_id and repetition == 0
                                    else "randomized"
                                ),
                                latency_ns=latency,
                                cpu_power_mw=100.0,
                                energy_mj=energy,
                                checksum="ok",
                                reference_checksum="ok",
                                semantic_valid=True,
                                measurement_valid=True,
                                failure="",
                                thermal_level="Nominal",
                                power_sample_count=3,
                                evidence_class="silicon",
                            ).to_dict(),
                        )
                for policy in ("cold", "bounded", "full-history"):
                    candidate_id = baseline_id if policy == "cold" else selected_id
                    slate = (
                        (baseline_id, cold_id)
                        if policy == "cold"
                        else (baseline_id, selected_id)
                    )
                    bundle.append_jsonl(
                        "policy-selections.jsonl",
                        PolicySelection(
                            experiment_id=manifest.experiment_id,
                            manifest_sha256=manifest_hash(manifest.to_dict()),
                            registered_at_utc="2026-08-08T00:00:00+00:00",
                            workload_id=workload.workload_id,
                            policy=policy,
                            candidate_ids=slate,
                            measurement_budget=manifest.measurement_budget,
                            source_run_id="source-run",
                            source_bundle_sha256="0" * 64,
                            source_evidence_max_sequence=0,
                            retrieval_latency_ns={
                                "cold": 10,
                                "bounded": 100,
                                "full-history": 1000,
                            }[policy],
                            active_memory_records={
                                "cold": 0,
                                "bounded": manifest.active_memory_limit,
                                "full-history": 128,
                            }[policy],
                            cold_evidence_records=1000,
                            predicted_latency_ratio=1.0 if policy == "cold" else 0.8,
                            predicted_energy_ratio=1.0 if policy == "cold" else 0.8,
                            abstained=policy == "cold",
                        ).to_dict(),
                    )
                    bundle.append_jsonl(
                        "policy-outcomes.jsonl",
                        PolicyOutcome(
                            run_id=run_id,
                            workload_id=workload.workload_id,
                            policy=policy,
                            selected_candidate_id=candidate_id,
                            baseline_latency_ns=100.0,
                            selected_latency_ns=100.0 if policy == "cold" else 80.0,
                            oracle_latency_ns=80.0,
                            baseline_energy_mj=10.0,
                            selected_energy_mj=10.0 if policy == "cold" else 8.0,
                            oracle_energy_mj=8.0,
                            measurement_budget=manifest.measurement_budget,
                            retrieval_latency_ns={
                                "cold": 10,
                                "bounded": 100,
                                "full-history": 1000,
                            }[policy],
                            active_memory_records={
                                "cold": 0,
                                "bounded": manifest.active_memory_limit,
                                "full-history": 128,
                            }[policy],
                            cold_evidence_records=1000,
                            predicted_latency_ratio=1.0 if policy == "cold" else 0.8,
                            predicted_energy_ratio=1.0 if policy == "cold" else 0.8,
                            abstained=policy == "cold",
                        ).to_dict(),
                    )

            analysis = analyze_bundle(bundle, bootstrap_samples=100)
            self.assertTrue(analysis["policy"]["gate_ready"], analysis["policy"])

            policy_path = bundle.path / "policy-outcomes.jsonl"
            original_policy_text = policy_path.read_text(encoding="utf-8")
            lines = original_policy_text.splitlines()
            tampered = json.loads(lines[0])
            tampered["selected_latency_ns"] = 79.0
            lines[0] = json.dumps(tampered, sort_keys=True)
            policy_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            analysis = analyze_bundle(bundle, bootstrap_samples=20)
            self.assertFalse(analysis["policy"]["gate_ready"])
            self.assertTrue(
                any("do not match measurements" in item for item in analysis["policy"]["unmet"])
            )

            policy_path.write_text(original_policy_text, encoding="utf-8")
            selection_path = bundle.path / "policy-selections.jsonl"
            original_selection_text = selection_path.read_text(encoding="utf-8")
            first_selection = original_selection_text.splitlines()[0]
            with selection_path.open("a", encoding="utf-8") as target:
                target.write(first_selection + "\n")
            analysis = analyze_bundle(bundle, bootstrap_samples=20)
            self.assertFalse(analysis["policy"]["gate_ready"])
            self.assertTrue(
                any("duplicate PolicySelection" in item for item in analysis["policy"]["unmet"])
            )

            selection_lines = original_selection_text.splitlines()
            late = json.loads(selection_lines[0])
            late["registered_at_utc"] = "2026-08-08T00:01:00+00:00"
            selection_lines[0] = json.dumps(late, sort_keys=True)
            selection_path.write_text("\n".join(selection_lines) + "\n", encoding="utf-8")
            analysis = analyze_bundle(bundle, bootstrap_samples=20)
            self.assertFalse(analysis["policy"]["gate_ready"])
            self.assertTrue(
                any("not registered before measurement" in item for item in analysis["policy"]["unmet"])
            )

            selection_path.write_text(original_selection_text, encoding="utf-8")
            measurement_path = bundle.path / "measurement.jsonl"
            measurement_lines = measurement_path.read_text(encoding="utf-8").splitlines()
            wrong_run = json.loads(measurement_lines[0])
            wrong_run["run_id"] = "different-run"
            measurement_lines[0] = json.dumps(wrong_run, sort_keys=True)
            measurement_path.write_text(
                "\n".join(measurement_lines) + "\n", encoding="utf-8"
            )
            analysis = analyze_bundle(bundle, bootstrap_samples=20)
            self.assertFalse(analysis["policy"]["gate_ready"])
            self.assertIn(
                "measurement RUN-ID does not match the analyzed bundle",
                analysis["policy"]["unmet"],
            )

    def test_pilot_analysis_cannot_return_a_gate_conclusion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = json.loads(PILOT_MANIFEST.read_text(encoding="utf-8"))
            value["energy"]["required"] = False
            value["workloads"] = [
                {**workload, "m": 4, "n": 4, "k": 4, "inner_iterations": 1}
                for workload in value["workloads"]
            ]
            manifest_path = root / "pilot.json"
            manifest_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch("raveil.experiment_runner.require_clean_worktree"):
                bundle, valid = run_experiment(manifest_path, root / "artifacts")
            self.assertTrue(valid)
            analysis = analyze_bundle(bundle, bootstrap_samples=100)
            self.assertEqual(analysis["manifest_stage"], "pilot")
            self.assertEqual(analysis["gate_conclusion"], "not-applicable-pilot")
            self.assertFalse(analysis["policy"]["gate_ready"])

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
    def test_every_agent_obeys_project_queue_contract(self) -> None:
        agents = {
            path.stem: tomllib.loads(path.read_text(encoding="utf-8"))
            for path in (ROOT / ".codex/agents").glob("*.toml")
        }
        for name, agent in agents.items():
            with self.subTest(agent=name):
                instructions = " ".join(agent["developer_instructions"].split())
                self.assertIn("ADR-0065", instructions)
                self.assertIn("real `work-item`", instructions)
                self.assertIn("Issue", instructions)
                self.assertIn("Project Manager", instructions)

        implementers = {
            "raveil-chisel-implementer",
            "raveil-experience-implementer",
            "raveil-measurement-implementer",
            "raveil-systems-implementer",
        }
        for name in implementers:
            instructions = " ".join(agents[name]["developer_instructions"].split())
            self.assertIn("currently `In Progress`", instructions)
            self.assertIn("exact file allowlist", instructions)
            self.assertIn("scripts/project_queue.py --apply", instructions)
            self.assertIn("Stop and report", instructions)

        for name in (
            "raveil-librarian",
            "raveil-performance-reviewer",
            "raveil-security-reviewer",
        ):
            instructions = " ".join(agents[name]["developer_instructions"].split())
            self.assertEqual("read-only", agents[name]["sandbox_mode"])
            self.assertIn("do not consume mutation WIP", instructions)
            self.assertIn("scripts/project_queue.py --apply", instructions)
            self.assertIn("Standalone read-only", instructions)

        researcher = " ".join(
            agents["raveil-researcher"]["developer_instructions"].split()
        )
        self.assertIn("Before writing a tracked memo", researcher)
        self.assertIn("exact file allowlist", researcher)
        self.assertIn("does not consume mutation WIP", researcher)

        tester = " ".join(agents["raveil-tester"]["developer_instructions"].split())
        self.assertIn("`In Progress` or `Review`", tester)
        self.assertIn("Do not edit tracked files", tester)
        self.assertIn("scripts/project_queue.py --apply", tester)

        project_manager = " ".join(
            agents["raveil-project-manager"]["developer_instructions"].split()
        )
        self.assertIn("sole Project queue-transition authority", project_manager)
        self.assertIn("including any `/Sxx`", project_manager)
        self.assertIn("python3 scripts/project_queue.py audit", project_manager)
        self.assertIn("Only the Project Manager may use", project_manager)
        self.assertIn("Never activate more than two", project_manager)
        self.assertIn("before `Done`", project_manager)

        governance = (
            ROOT / ".agents/skills/raveil-task-governance/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("apply ADR-0065", governance)
        self.assertIn("real `work-item` Issue", governance)
        self.assertIn("python3 scripts/project_queue.py audit", governance)
        self.assertIn("Only the primary Project Manager", governance)

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
            "raveil-chisel-implementer",
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
        project_manager = agents["raveil-project-manager"]["developer_instructions"]
        self.assertIn("docs/templates/ESTIMATE-TEMPLATE.md", project_manager)
        self.assertIn("warm/cold build state", project_manager)
        self.assertIn("latest named authority commit", project_manager)
        self.assertIn("ADR-0051", project_manager)
        self.assertIn("updates are non-blocking", project_manager)
        self.assertIn("exact approval needed", project_manager)
        workflow = (ROOT / "docs/WORKFLOW.md").read_text(encoding="utf-8")
        repository_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for marker in (
            "HCI-01", "HCI-02", "HCI-03", "HCI-04",
            "HCI-05", "HCI-06", "HCI-07", "HCI-08", "HCI-09",
        ):
            self.assertIn(marker, workflow)
        self.assertIn(
            "Continuous execution and human confirmation", repository_rules
        )
        self.assertIn("A progress update is", repository_rules)
        self.assertIn("informational and does not pause work", repository_rules)

        estimate_template = (
            ROOT / "docs/templates/ESTIMATE-TEMPLATE.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Authority commit:", estimate_template)
        self.assertIn("Warm build/cache state:", estimate_template)
        self.assertIn("Integration/review/records", estimate_template)
        for name in (
            "raveil-experience-implementer",
            "raveil-chisel-implementer",
            "raveil-systems-implementer",
            "raveil-measurement-implementer",
        ):
            self.assertIn("Do not edit", agents[name]["developer_instructions"])

        reasoning_effort = {
            name: agent["model_reasoning_effort"] for name, agent in agents.items()
        }
        for name in (
            "raveil-experience-implementer",
            "raveil-chisel-implementer",
            "raveil-systems-implementer",
            "raveil-measurement-implementer",
            "raveil-tester",
        ):
            self.assertEqual(reasoning_effort[name], "low")
        self.assertEqual(reasoning_effort["raveil-librarian"], "medium")
        for name in (
            "raveil-project-manager",
            "raveil-performance-reviewer",
            "raveil-security-reviewer",
            "raveil-researcher",
        ):
            self.assertEqual(reasoning_effort[name], "high")

    def test_weekly_usage_guard_is_exact_and_fail_closed(self) -> None:
        workflow = (ROOT / "docs/WORKFLOW.md").read_text(encoding="utf-8")
        repository_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        project_manager = tomllib.loads(
            (ROOT / ".codex/agents/raveil-project-manager.toml").read_text(
                encoding="utf-8"
            )
        )["developer_instructions"]
        adr = (
            ROOT
            / "docs/decisions/ADR-0060-weekly-codex-usage-has-a-hard-cost-stop.md"
        ).read_text(encoding="utf-8")
        for text in (workflow, repository_rules, adr):
            self.assertIn("remaining = 100 - usedPercent", text)
            self.assertIn("below five percent", text)
            self.assertIn("Exactly five percent", text)
            self.assertIn("10,080", text)
            self.assertIn("reset credits", text)
        self.assertIn("remaining below five percent", project_manager)
        self.assertIn("telemetry is unavailable or unverifiable", project_manager)
        self.assertIn("fail closed", workflow)
        self.assertIn("stale, malformed", workflow)


if __name__ == "__main__":
    unittest.main()
