from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPIKE = ROOT / "experiments" / "openasip"


def load_module(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class OpenAsipFeasibilityTest(unittest.TestCase):
    def test_cancellation_observer_requires_pid_and_reports_api_errors(self):
        witness = load_module("t0191_observer", SPIKE / "check_cancellation.py")
        with mock.patch.object(witness.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "PID COMMAND\n123 /opt/openasip/bin/oacc -O3\n", "")
            self.assertTrue(witness.observe("a" * 64, "oacc"))
            self.assertEqual(run.call_args.args[0][-2:], ["-eo", "pid,args"])
            run.return_value = subprocess.CompletedProcess([], 1, "", "Couldn't find PID field in ps output")
            with self.assertRaisesRegex(RuntimeError, "observation failed"):
                witness.observe("a" * 64, "oacc")
            run.return_value = subprocess.CompletedProcess([], 1, "", "container is not running")
            self.assertFalse(witness.observe("a" * 64, "oacc"))

    def test_cancellation_observer_excludes_load_only_probe(self):
        witness = load_module("t0191_observer_stage", SPIKE / "check_cancellation.py")
        command = ["/opt/openasip/bin/ttasim", "-e"]
        self.assertFalse(witness.target_stage(command + [witness.simulate.LOAD_SCRIPT], "ttasim"))
        self.assertTrue(witness.target_stage(command + [witness.simulate.SIM_SCRIPT], "ttasim"))

    def test_source_receipt_matches_manifest_and_is_non_claiming(self) -> None:
        manifest = json.loads((SPIKE / "manifest.json").read_text())
        receipt = json.loads((SPIKE / "source-receipt.json").read_text())
        self.assertEqual(receipt["openasip_revision"], manifest["upstream"]["revision"])
        self.assertEqual(receipt["llvm_revision"], manifest["llvm"]["revision"])
        self.assertEqual(receipt["machine_sha256"], manifest["machine"]["sha256"])
        self.assertEqual(receipt["base_image"], manifest["container"]["base_image"])
        self.assertEqual(receipt["build_exit"], 0)
        self.assertFalse(receipt["toolchain_built"])
        self.assertFalse(receipt["simulator_run"])
        self.assertFalse(receipt["publication"])

    def test_container_source_and_archive_identities_are_exact(self) -> None:
        dockerfile = (SPIKE / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "ubuntu@sha256:1e0a86e57d247923571b75e0aaf48a1449cf8c543d51fb3e07a4a7d7bfa79316",
            dockerfile,
        )
        self.assertIn("UBUNTU_SNAPSHOT=20260908T000000Z", dockerfile)
        self.assertIn("ca-certificates=20260601~24.04.1", dockerfile)
        self.assertIn("f2282048f4c78d18190a9b77e7497e29a164721d", dockerfile)
        self.assertIn("b47e651cc052ba9e097701efa8840e8f3081c84d", dockerfile)
        self.assertNotIn("--branch openasip-llvm-22-patched", dockerfile)

    def test_manifest_preserves_exact_inputs_and_authority(self) -> None:
        verifier = load_module("t0191_manifest", SPIKE / "verify_manifest.py")
        receipt = verifier.validate(require_container=False)
        self.assertEqual(len(receipt["program_sha256"]), 3)
        self.assertEqual(
            verifier.validate(require_container=True)["manifest_sha256"],
            receipt["manifest_sha256"],
        )

    def test_independent_oracles_are_exact_unsigned_words(self) -> None:
        oracle = load_module("t0191_oracle", SPIKE / "oracle.py")
        self.assertEqual(oracle.neighborhood(), 170)
        self.assertEqual(oracle.elementwise(), 740)
        self.assertEqual(oracle.reduction(), 374)

    def test_programs_require_runtime_observable_inputs_and_feature_receipts(self) -> None:
        manifest = json.loads((SPIKE / "manifest.json").read_text())
        for relative in manifest["programs"]:
            source = (SPIKE / relative).read_text(encoding="utf-8")
            self.assertIn("volatile const uint32_t input", source)
            receipt = manifest["program_receipts"][relative]
            self.assertGreater(receipt["input_bytes"], 0)
            self.assertEqual(receipt["result_bytes"], 4)
            self.assertTrue(receipt["topology"])
            self.assertTrue(receipt["dependence"])
            self.assertTrue(receipt["access_footprint"])

    def test_preflight_is_explicitly_non_executing(self) -> None:
        result = subprocess.run(
            [str(SPIKE / "run_three_programs.sh"), "--preflight"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
        self.assertEqual(json.loads(lines[1]), {
            "elementwise": 740,
            "neighborhood": 170,
            "reduction": 374,
        })
        self.assertEqual(
            lines[2],
            "T-0191 status=preflight-only build=no simulation=no publication=no",
        )

    def test_explicit_host_check_matches_oracle(self) -> None:
        result = subprocess.run(
            [str(SPIKE / "run_three_programs.sh"), "--host-check"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
        host = json.loads(lines[2])
        self.assertEqual(host["backend"], "native-cpu")
        self.assertFalse(host["published"])
        self.assertEqual(
            lines[3],
            "T-0191 status=host-check-only build=no simulation=no publication=no",
        )

    def test_program_path_traversal_is_rejected(self) -> None:
        verifier = load_module("t0191_manifest_paths", SPIKE / "verify_manifest.py")
        value = verifier.load_manifest()
        receipt = value["program_receipts"].pop(value["programs"][0])
        value["programs"][0] = "programs/../../../AGENTS.md"
        value["program_receipts"][value["programs"][0]] = receipt
        original = verifier.load_manifest
        verifier.load_manifest = lambda: value
        try:
            with self.assertRaisesRegex(ValueError, "outside the allowlist"):
                verifier.validate(require_container=True)
        finally:
            verifier.load_manifest = original

    def test_default_execution_fails_closed(self) -> None:
        result = subprocess.run(
            [str(SPIKE / "run_three_programs.sh")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("choose --preflight", result.stderr)

    def test_simulator_parser_requires_one_complete_exact_envelope(self) -> None:
        simulator = load_module("t0191_simulator", SPIKE / "simulate.py")
        output = "\n".join([
            "RAVEIL_RESULT=0x000000aa",
            "RAVEIL_CYCLES=123",
            "RAVEIL_REGISTER_READS=9.0",
            "RAVEIL_REGISTER_WRITES=4",
            "RAVEIL_DONE",
        ])
        self.assertEqual(simulator.parse_simulator_output(output), {
            "result_hex": 170,
            "cycles": 123,
            "register_reads": 9,
            "register_writes": 4,
        })
        for invalid in (
            output.replace("RAVEIL_DONE", ""),
            output + "\nRAVEIL_DONE",
            output.replace("0x000000aa", "170"),
            output.replace("9.0", "9.5"),
            output + "\ntrailing",
        ):
            with self.assertRaises(RuntimeError):
                simulator.parse_simulator_output(invalid)

    def test_simulator_container_boundary_is_hardened_and_fixed(self) -> None:
        simulator = load_module("t0191_simulator_args", SPIKE / "simulate.py")
        args = simulator.common_container_args(
            work=Path("/tmp/t0191-evidence"),
            source=Path("/tmp/t0191-input.c"),
        )
        for pair in (
            ["--network", "none"], ["--cap-drop", "ALL"],
            ["--security-opt", "no-new-privileges=true"],
            ["--read-only"], ["--user", "65534:65534"],
        ):
            joined = "\0".join(args)
            self.assertIn("\0".join(pair), joined)
        self.assertNotIn("/bin/sh", args)
        self.assertNotIn("-c", args)

    def test_raveil_owns_candidate_publication_and_oracle_rejection(self) -> None:
        lifecycle = load_module("t0191_lifecycle", SPIKE / "lifecycle.py")
        private = {
            "published": False,
            "programs": {
                name: {"result_u32": value}
                for name, value in lifecycle.EXPECTED.items()
            },
        }
        accepted = lifecycle.admit(private)
        self.assertTrue(accepted["published"])
        self.assertEqual(accepted["publication_authority"], "raveil")
        self.assertEqual(accepted["results"], lifecycle.EXPECTED)
        self.assertNotIn("programs", accepted)
        private["programs"]["reduction"]["result_u32"] ^= 1
        rejected = lifecycle.admit(private)
        self.assertEqual(rejected["status"], "fallback")
        self.assertEqual(rejected["backend"], "cpu-oracle")

    def test_publication_projects_only_reviewed_fields_and_private_identity(self) -> None:
        lifecycle = load_module("t0191_lifecycle_projection", SPIKE / "lifecycle.py")
        private_path = "/private/tmp/raveil-t0191-private-work"
        private = {
            "published": False,
            "programs": {
                name: {
                    "result_u32": value,
                    "compile_argv": [f"type=bind,src={private_path},dst=/evidence"],
                }
                for name, value in lifecycle.EXPECTED.items()
            },
            "host_platform": "private-host-fingerprint",
            "candidate_controlled_claim": "unreviewed",
        }
        accepted = lifecycle.admit(private)
        rendered = json.dumps(accepted, sort_keys=True)
        self.assertEqual(set(accepted), {
            "task", "status", "backend", "results",
            "private_candidate_receipt_sha256", "publication_authority", "published",
        })
        self.assertEqual(accepted["results"], lifecycle.EXPECTED)
        self.assertNotIn(private_path, rendered)
        self.assertNotIn("private-host-fingerprint", rendered)
        self.assertNotIn("unreviewed", rendered)

    def test_cpu_fallback_projects_only_results_and_private_identity(self) -> None:
        lifecycle = load_module("t0191_lifecycle_cpu_projection", SPIKE / "lifecycle.py")
        cpu = {
            "backend": "native-cpu",
            "programs": {
                name: {"observed_u32": value} for name, value in lifecycle.EXPECTED.items()
            },
            "private_host_path": "/private/tmp/raveil-cpu-private",
        }
        accepted = lifecycle.actual_cpu_fallback("candidate-failed", lambda: cpu)
        self.assertTrue(accepted["published"])
        self.assertEqual(accepted["results"], lifecycle.EXPECTED)
        self.assertNotIn("cpu_receipt", accepted)
        self.assertNotIn("/private/tmp", json.dumps(accepted, sort_keys=True))

    def test_cancel_and_failure_do_not_leak_candidate_output(self) -> None:
        lifecycle = load_module("t0191_lifecycle_fail", SPIKE / "lifecycle.py")
        calls = 0

        def candidate():  # type: ignore[no-untyped-def]
            nonlocal calls
            calls += 1
            raise RuntimeError("candidate failed")

        cancelled = lifecycle.execute(candidate, cancelled=True)
        self.assertEqual(calls, 0)
        self.assertFalse(cancelled["published"])
        failed = lifecycle.execute(candidate)
        self.assertEqual(calls, 1)
        self.assertEqual(failed["status"], "fallback")
        self.assertNotIn("candidate failed", json.dumps(failed))

    def test_inflight_cancel_wins_before_candidate_publication(self) -> None:
        lifecycle = load_module("t0191_lifecycle_inflight", SPIKE / "lifecycle.py")
        cancelling = False
        calls = 0

        def candidate():  # type: ignore[no-untyped-def]
            nonlocal cancelling, calls
            calls += 1
            cancelling = True
            return {
                "published": False,
                "programs": {
                    name: {"result_u32": value}
                    for name, value in lifecycle.EXPECTED.items()
                },
            }

        receipt = lifecycle.execute(
            candidate,
            cancel_requested=lambda: cancelling,
        )
        self.assertEqual(calls, 1)
        self.assertEqual(receipt["status"], "cancelled")
        self.assertTrue(receipt["candidate_started"])
        self.assertFalse(receipt["published"])
        self.assertNotIn("programs", receipt)

    def test_inflight_cancel_also_wins_over_candidate_failure(self) -> None:
        lifecycle = load_module("t0191_lifecycle_cancel_failure", SPIKE / "lifecycle.py")
        cancelling = False
        fallback_calls = 0

        def candidate():  # type: ignore[no-untyped-def]
            nonlocal cancelling
            cancelling = True
            raise RuntimeError("private candidate detail")

        def fallback():  # type: ignore[no-untyped-def]
            nonlocal fallback_calls
            fallback_calls += 1
            return {"backend": "native-cpu", "programs": {}}

        receipt = lifecycle.execute(
            candidate,
            cancel_requested=lambda: cancelling,
            cpu_fallback=fallback,
        )
        self.assertEqual(receipt["status"], "cancelled")
        self.assertTrue(receipt["candidate_started"])
        self.assertFalse(receipt["published"])
        self.assertEqual(fallback_calls, 0)
        self.assertNotIn("private candidate detail", json.dumps(receipt))

    def test_real_runner_cancels_before_start_without_docker(self) -> None:
        result = subprocess.run(
            [str(SPIKE / "run_three_programs.sh"), "--simulate", "--cancel-before-start"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        )
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["status"], "cancelled")
        self.assertFalse(receipt["candidate_started"])
        self.assertFalse(receipt["published"])

    def test_owned_external_process_is_terminated_and_reaped_on_cancel(self) -> None:
        simulator = load_module("t0191_external_cancel", SPIKE / "simulate.py")
        with tempfile.TemporaryDirectory() as value:
            marker = Path(value) / "completed"
            started = time.monotonic()
            checks = 0

            def cancel_requested() -> bool:
                nonlocal checks
                checks += 1
                return checks >= 3

            with self.assertRaisesRegex(
                simulator.ExternalProcessCancelled, "cancelled and reaped"
            ):
                simulator.run(
                    [
                        sys.executable, "-c",
                        "import pathlib,time; time.sleep(5); "
                        f"pathlib.Path({str(marker)!r}).write_text('late')",
                    ],
                    timeout=10,
                    cancel_requested=cancel_requested,
                )
            self.assertLess(time.monotonic() - started, 2)
            time.sleep(0.1)
            self.assertFalse(marker.exists())

    def test_cancel_probe_failure_reaps_child_and_fails_closed(self) -> None:
        simulator = load_module("t0191_probe_failure", SPIKE / "simulate.py")
        with tempfile.TemporaryDirectory() as value:
            marker = Path(value) / "completed"
            with self.assertRaisesRegex(
                simulator.ExternalProcessCleanupError, "probe failed"
            ):
                simulator.run(
                    [
                        sys.executable, "-c",
                        "import pathlib,time; time.sleep(5); "
                        f"pathlib.Path({str(marker)!r}).write_text('late')",
                    ],
                    timeout=10,
                    cancel_requested=lambda: (_ for _ in ()).throw(OSError("gone")),
                )
            time.sleep(0.1)
            self.assertFalse(marker.exists())

    def test_owned_container_cancel_stops_and_removes_only_created_id(self) -> None:
        simulator = load_module("t0191_container_lifecycle", SPIKE / "simulate.py")
        container_id = "a" * 64
        create = subprocess.CompletedProcess([simulator.DOCKER], 0, container_id + "\n", "")
        cancelled = simulator.ExternalProcessCancelled("external process cancelled and reaped")
        states = [
            subprocess.CompletedProcess([], 0, "true\n", ""),
            subprocess.CompletedProcess([], 0, container_id + "\n", ""),
            subprocess.CompletedProcess([], 0, "false\n", ""),
            subprocess.CompletedProcess([], 0, container_id + "\n", ""),
        ]
        with mock.patch.object(simulator, "run", side_effect=[create, cancelled]) as runner, \
             mock.patch.object(simulator.subprocess, "run", side_effect=states) as cleanup:
            with self.assertRaises(simulator.ExternalProcessCancelled):
                simulator.run_container(
                    [simulator.DOCKER, "run", "--rm", simulator.IMAGE, "sleep", "10"],
                    cancel_requested=lambda: True,
                )
        self.assertEqual(
            runner.call_args_list[0].args[0][0:5],
            [simulator.DOCKER, "create", "--name", runner.call_args_list[0].args[0][3], "--label"],
        )
        self.assertRegex(runner.call_args_list[0].args[0][3], r"^raveil-t0191-[0-9a-f]{32}$")
        self.assertEqual(runner.call_args_list[0].args[0][5:], ["raveil.task=T-0191", simulator.IMAGE, "sleep", "10"])
        self.assertEqual(
            runner.call_args_list[1].args[0],
            [simulator.DOCKER, "start", "--attach", container_id],
        )
        self.assertEqual(
            [call.args[0] for call in cleanup.call_args_list],
            [
                [simulator.DOCKER, "inspect", "--format", "{{.State.Running}}", container_id],
                [simulator.DOCKER, "stop", "--time", "2", container_id],
                [simulator.DOCKER, "inspect", "--format", "{{.State.Running}}", container_id],
                [simulator.DOCKER, "rm", container_id],
            ],
        )

    def test_owned_container_requires_verified_zero_exit(self) -> None:
        simulator = load_module("t0191_container_exit", SPIKE / "simulate.py")
        container_id = "b" * 64
        created = subprocess.CompletedProcess([simulator.DOCKER], 0, container_id + "\n", "")
        started = subprocess.CompletedProcess([simulator.DOCKER], 0, "output", "")
        states = [
            subprocess.CompletedProcess([], 0, "false 7\n", ""),
            subprocess.CompletedProcess([], 0, "false\n", ""),
            subprocess.CompletedProcess([], 0, container_id + "\n", ""),
        ]
        with mock.patch.object(simulator, "run", side_effect=[created, started]), \
             mock.patch.object(simulator.subprocess, "run", side_effect=states):
            with self.assertRaises(subprocess.CalledProcessError) as error:
                simulator.run_container([simulator.DOCKER, "run", simulator.IMAGE, "false"])
        self.assertEqual(error.exception.returncode, 7)

    def test_cleanup_uncertainty_neither_falls_back_nor_publishes(self) -> None:
        lifecycle = load_module("t0191_cleanup_uncertain", SPIKE / "lifecycle.py")
        fallback_calls = 0

        def fallback():  # type: ignore[no-untyped-def]
            nonlocal fallback_calls
            fallback_calls += 1
            return {"backend": "native-cpu", "programs": {}}

        receipt = lifecycle.execute(
            lambda: (_ for _ in ()).throw(lifecycle.ExternalProcessCleanupError("unknown")),
            cpu_fallback=fallback,
        )
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse(receipt["published"])
        self.assertEqual(fallback_calls, 0)

    def test_external_timeout_neither_falls_back_nor_publishes(self) -> None:
        lifecycle = load_module("t0191_timeout_boundary", SPIKE / "lifecycle.py")
        fallback = mock.Mock()
        receipt = lifecycle.execute(
            lambda: (_ for _ in ()).throw(subprocess.TimeoutExpired("owned", 1)),
            cpu_fallback=fallback,
        )
        self.assertEqual(receipt["status"], "failed")
        self.assertFalse(receipt["published"])
        fallback.assert_not_called()

    def test_create_failure_never_cleans_an_unproven_container(self) -> None:
        simulator = load_module("t0191_create_conflict", SPIKE / "simulate.py")
        for error in (subprocess.CalledProcessError(1, ["docker", "create"]),
                      subprocess.TimeoutExpired(["docker", "create"], 5)):
            with self.subTest(error=type(error).__name__), \
                 mock.patch.object(simulator, "run", side_effect=error), \
                 mock.patch.object(simulator, "_cleanup_container") as cleanup:
                with self.assertRaises(simulator.ExternalProcessCleanupError):
                    simulator.run_container([simulator.DOCKER, "run", simulator.IMAGE, "true"])
                cleanup.assert_not_called()

    def test_cancel_file_latches_after_removal(self) -> None:
        runner = load_module("t0191_authorized_cancel_latch", SPIKE / "run_authorized.py")
        with tempfile.TemporaryDirectory() as value:
            path = Path(value) / "cancel"
            path.write_text("cancel", encoding="utf-8")
            requested = runner.CancelFile(path)
            self.assertTrue(requested())
            path.unlink()
            self.assertTrue(requested())

    def test_real_runner_uses_native_cpu_fallback_on_candidate_failure(self) -> None:
        result = subprocess.run(
            [
                str(SPIKE / "run_three_programs.sh"), "--simulate",
                "--force-candidate-failure-for-test",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        )
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["status"], "fallback")
        self.assertEqual(receipt["backend"], "native-cpu")
        self.assertEqual(receipt["publication_authority"], "raveil")
        self.assertTrue(receipt["published"])

    def test_rtl_identity_normalizes_only_known_generator_timestamp(self) -> None:
        generator = load_module("t0191_rtl_generator", SPIKE / "generate_rtl.py")
        with tempfile.TemporaryDirectory() as value:
            first = Path(value) / "rf_bool.vhd"
            second = Path(value) / "rf_rf.vhd"
            first.write_text("-- Generated on first\nentity x is\n", encoding="utf-8")
            second.write_text("-- Generated on second\nentity x is\n", encoding="utf-8")
            self.assertNotEqual(generator.digest(first), generator.digest(second))
            self.assertEqual(
                generator.normalized_digest(first), generator.normalized_digest(second)
            )

    def test_run_evidence_verifier_rejects_raw_log_tamper(self) -> None:
        verifier = load_module("t0191_evidence_run", SPIKE / "verify_evidence.py")
        manifest = json.loads((SPIKE / "manifest.json").read_text())
        toolchain = json.loads((SPIKE / "toolchain-receipt.json").read_text())
        empty_hash = hashlib.sha256(b"").hexdigest()
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            programs = {}
            for relative in manifest["programs"]:
                name = Path(relative).stem
                directory = root / name
                directory.mkdir()
                tpef = directory / f"{name}.tpef"
                tpef.write_bytes(name.encode())
                for filename in (
                    "compile.stdout", "compile.stderr", "tpef.disassembly",
                    "load-probe.stdout", "load-probe.stderr",
                    "simulator.stdout", "simulator.stderr",
                ):
                    (directory / filename).write_text("", encoding="utf-8")
                source = manifest["program_receipts"][relative]
                programs[name] = {
                    "result_u32": {"neighborhood": 170, "elementwise": 740, "reduction": 374}[name],
                    "source_sha256": source["sha256"],
                    "staged_source_sha256": source["sha256"],
                    "staged_source_bytes": source["bytes"],
                    "tpef_sha256": hashlib.sha256(name.encode()).hexdigest(),
                    "tpef_bytes": len(name),
                    "compile_exit_code": 0, "disasm_exit_code": 0,
                    "load_probe_exit_code": 0, "simulator_exit_code": 0,
                    "compile_stdout_sha256": empty_hash, "compile_stderr_sha256": empty_hash,
                    "disassembly_sha256": empty_hash, "load_probe_stdout_sha256": empty_hash,
                    "load_probe_stderr_sha256": empty_hash, "simulator_stdout_sha256": empty_hash,
                    "simulator_stderr_sha256": empty_hash,
                }
            private = {
                "schema": "raveil.t0191-openasip-run/v1", "task": "T-0191",
                "evidence_class": "host-functional-external-simulator",
                "manifest_sha256": verifier.digest(SPIKE / "manifest.json"),
                "machine_sha256": manifest["machine"]["sha256"],
                "local_image_id": toolchain["local_image_id"], "published": False,
                "implementation_sha256": {
                    name: verifier.digest(SPIKE / name)
                    for name in ("simulate.py", "verify_manifest.py", "lifecycle.py", "run_authorized.py")
                },
                "programs": programs,
            }
            authorized = {
                "task": "T-0191", "status": "accepted",
                "backend": "openasip-ttasim",
                "results": {
                    name: programs[name]["result_u32"] for name in verifier.EXPECTED
                },
                "private_candidate_receipt_sha256": verifier.receipt_sha256(private),
                "publication_authority": "raveil", "published": True,
            }
            (root / "run-receipt.json").write_text(json.dumps(private), encoding="utf-8")
            (root / "authorized-receipt.json").write_text(json.dumps(authorized), encoding="utf-8")
            self.assertTrue(verifier.verify_run(root)["verified"])
            (root / "reduction" / "simulator.stdout").write_text("tamper", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "raw log mismatch"):
                verifier.verify_run(root)


if __name__ == "__main__":
    unittest.main()
