from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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
        private["programs"]["reduction"]["result_u32"] ^= 1
        rejected = lifecycle.admit(private)
        self.assertEqual(rejected["status"], "fallback")
        self.assertEqual(rejected["backend"], "cpu-oracle")

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
            authorized = dict(private)
            authorized.update({
                "backend": "openasip-ttasim", "status": "accepted",
                "publication_authority": "raveil", "published": True,
            })
            (root / "run-receipt.json").write_text(json.dumps(private), encoding="utf-8")
            (root / "authorized-receipt.json").write_text(json.dumps(authorized), encoding="utf-8")
            self.assertTrue(verifier.verify_run(root)["verified"])
            (root / "reduction" / "simulator.stdout").write_text("tamper", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "raw log mismatch"):
                verifier.verify_run(root)


if __name__ == "__main__":
    unittest.main()
