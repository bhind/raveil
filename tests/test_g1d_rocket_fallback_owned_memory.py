from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from raveil.riscv_stencil_signature import input_words
from raveil.static_region import static_stencil_oracle


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
MEMORY = ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
RUNNER = ROOT / "hardware/chisel/run-g1d-rocket-fallback-owned-memory.sh"
VERIFY = ROOT / "hardware/chisel/verify_g1d_rocket_fallback_owned_memory.py"


class G1dFallbackTests(unittest.TestCase):
    @staticmethod
    def _evidence() -> str:
        output = static_stencil_oracle(input_words(1))
        validation = "\n".join(
            "RAVEIL-G1D-VALIDATION-V1 "
            f"address={324 + index:4d} index={index:3d} "
            f"data=0x{word:08x} error=0"
            for index, word in enumerate(output)
        )
        log = "\n".join((
            "RAVEIL-FIXTURE-STAGING-V1 invocation=         1 seed=         1 "
            "accepted=324 completed=324 writes=324 first_word=0 last_word=323 "
            "pending=0 candidate_accepted_before_release=         0 release_count=1",
            "RAVEIL-G1D-EXECUTION-COMPLETE-V1 dcache_reads=       800 "
            "dcache_writes=       256 dcache_origin_accepted=      1056 "
            "dcache_origin_completed=      1056 graph_origin_accepted=         0 "
            "graph_origin_completed=         0 pending=0 performance=not-measured",
            validation,
            "RAVEIL-G1D-COMPLETE-V1 fixture_writes=324 "
            "dcache_execution_reads=       800 dcache_execution_writes=       256 "
            "validation_reads=       256 dcache_origin_accepted=      1312 "
            "dcache_origin_completed=      1312 graph_origin_accepted=         0 "
            "graph_origin_completed=         0 publication=private pending=0 "
            "performance=not-measured",
            "*** PASSED *** Completed after 326896 simulation cycles",
        ))
        return log

    def _verify(self, log: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            log_path = evidence / "sim.log"
            log_path.write_text(log, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    "--log",
                    str(log_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_selected_candidate_and_topology(self):
        config = CONFIG.read_text()
        memory = MEMORY.read_text()
        self.assertIn("RaveilFallbackIntegratedGraphRocketConfig", config)
        self.assertIn("WithRaveilFallbackIntegratedGraphMemorySourceRange", config)
        self.assertIn("graphSelected = false", memory)
        self.assertIn("graphSelected = true", memory)
        self.assertIn("require(!params.graphSelected || params.integratedGraph)", memory)
        self.assertIn("dcacheOriginRequest && rocketExpectedClientRequest", memory)
        self.assertIn("if (params.graphSelected) 1280.U else 800.U", memory)
        self.assertIn("if (params.graphSelected) 1536.U else 1056.U", memory)
        self.assertIn("RAVEIL-G1D-EXECUTION-COMPLETE-V1", memory)
        self.assertIn("RAVEIL-G1D-VALIDATION-V1", memory)
        self.assertIn("RAVEIL-G1D-COMPLETE-V1", memory)

    def test_runner_is_pinned_replay_not_stub(self):
        runner = RUNNER.read_text()
        self.assertTrue(RUNNER.stat().st_mode & 0o111)
        self.assertIn("RaveilFallbackIntegratedGraphRocketConfig", runner)
        self.assertIn("raveil-boom-functional-sim:v1", runner)
        self.assertNotIn(":latest", runner)
        self.assertIn("--network none", runner)
        self.assertIn("5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d", runner)
        for patch in (
            "t-0042-rocket-dcache-origin-hook.patch",
            "t-0042-tlxbar-request-defaults.patch",
            "t-0042-tl-token-metadata.patch",
        ):
            self.assertIn(patch, runner)
        self.assertNotIn("*.patch", runner)
        self.assertIn("riscv64-unknown-elf-gcc", runner)
        self.assertIn("RAVEIL_REPEAT_ACCOUNT=1", runner)
        self.assertIn("riscv_stencil_fixture_repeated.c", runner)
        self.assertNotIn("+signature=", runner)
        self.assertIn("printf 'chipyard_revision=%s", runner)
        self.assertIn('"$chipyard_revision" "$rocket_revision"', runner)
        self.assertIn("git -C /build/chipyard rev-parse HEAD", runner)
        self.assertIn("G1D-INTEGRATED-TOPOLOGY-V1 status=OK", runner)
        self.assertIn("G1D-CLEAN-REPLAY-V1 status=OK", runner)
        self.assertIn("performance=not-measured", runner)

    def test_verifier_accepts_padded_markers_and_private_validation(self):
        log = self._evidence()
        result = self._verify(log)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status=OK", result.stdout)

    def test_verifier_rejects_missing_or_duplicate_completion(self):
        log = self._evidence()
        completion = next(
            line for line in log.splitlines()
            if line.startswith("RAVEIL-G1D-COMPLETE-V1")
        )
        for invalid in (
            log.replace("RAVEIL-G1D-COMPLETE-V1", "REMOVED"),
            log + "\n" + completion,
        ):
            with self.subTest():
                result = self._verify(invalid)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("completion", result.stderr)

    def test_verifier_rejects_origin_or_traffic_drift(self):
        log = self._evidence()
        for invalid in (
            log.replace(
                "graph_origin_accepted=         0",
                "graph_origin_accepted=         1",
                1,
            ),
            log.replace(
                "dcache_origin_accepted=      1056",
                "dcache_origin_accepted=      1055",
                1,
            ),
        ):
            with self.subTest():
                result = self._verify(invalid)
                self.assertNotEqual(result.returncode, 0)

    def test_verifier_rejects_validation_drift(self):
        log = self._evidence()
        first_word = static_stencil_oracle(input_words(1))[0]
        changed_log = log.replace(
            f"data=0x{first_word:08x}",
            f"data=0x{first_word ^ 1:08x}",
            1,
        )
        result = self._verify(changed_log)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
