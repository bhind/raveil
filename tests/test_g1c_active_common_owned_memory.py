from pathlib import Path
import subprocess
import sys
import unittest

from raveil.riscv_stencil_signature import input_words
from raveil.static_region import static_stencil_oracle

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "hardware/chisel/chipyard-overlay/RaveilStaticStencilTLClient.scala"
MEMORY = ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
RUNNER = ROOT / "hardware/chisel/run-g1c-active-common-owned-memory.sh"
VERIFY = ROOT / "hardware/chisel/verify_g1c_active_common_owned_memory.py"

class G1cActiveStructureTests(unittest.TestCase):
    @staticmethod
    def _smoke_log() -> str:
        output = static_stencil_oracle(input_words(1))
        validation = "\n".join(
            "RAVEIL-G1C-VALIDATION-V1 "
            f"address={324 + index:4d} index={index:3d} "
            f"data=0x{word:08x} error=0"
            for index, word in enumerate(output)
        )
        return "\n".join((
            "RAVEIL-FIXTURE-STAGING-V1 invocation=         1 seed=         1 "
            "accepted=324 completed=324 writes=324 first_word=0 last_word=323 "
            "pending=0 candidate_accepted_before_release=         0 release_count=1",
            "RAVEIL-G1C-EXECUTION-COMPLETE-V1 graph_reads=      1280 "
            "graph_writes=       256 dcache_origin_accepted=         0 "
            "dcache_origin_completed=         0 pending=0 performance=not-measured",
            validation,
            "RAVEIL-G1C-COMPLETE-V1 fixture_writes=324 "
            "graph_execution_reads=      1280 graph_execution_writes=       256 "
            "validation_reads=       256 graph_origin_accepted=      1792 "
            "graph_origin_completed=      1792 dcache_origin_accepted=         0 "
            "dcache_origin_completed=         0 publication=private pending=0 "
            "performance=not-measured",
            "*** PASSED *** Completed after 326896 simulation cycles",
        ))

    def test_one_shot_private_validation_controller(self):
        source = CLIENT.read_text()
        self.assertIn(
            "(params.activeOneShot.B || launchRequested) && !startIssued",
            source,
        )
        self.assertIn("require(!(params.activeOneShot && params.runtimeControl))", source)
        self.assertIn("validationIndex", source)
        self.assertIn("324.U(10.W) + validationIndex.pad(10)", source)
        self.assertIn("tl.a.bits.address === requestByteAddress", source)
        self.assertNotIn("324.U + validationIndex", source)
        self.assertIn("validationIndex === 255.U", source)
        self.assertIn("RAVEIL-G1C-VALIDATION-V1", source)
        self.assertIn("core.io.graphInputReadsAccepted === 1280.U", source)
        self.assertIn("core.io.graphOutputWritesAccepted === 256.U", source)
        self.assertNotIn("StaticStencilRegion", source)
        self.assertNotIn("new SyncReadMem", source)

    def test_shared_fixture_and_dcache_zero_contract(self):
        memory = MEMORY.read_text()
        self.assertIn("fixtureOwnedInputStaging = true", memory)
        self.assertIn("controlledRun = true", memory)
        self.assertIn("graphOriginAcceptedCount", memory)
        self.assertIn("dcacheOriginAcceptedCount", memory)

    def test_runner_and_verifier_are_non_claiming(self):
        runner = RUNNER.read_text()
        verifier = VERIFY.read_text()
        self.assertTrue(RUNNER.stat().st_mode & 0o111)
        self.assertIn("RaveilActiveIntegratedGraphRocketConfig", runner)
        self.assertIn("RaveilFixtureInputProvider.scala", runner)
        self.assertIn("one manager", runner)
        self.assertNotIn("raveil-boom-functional-sim:v1", runner)
        self.assertIn("verify-boom-functional-sim-image.sh", runner)
        self.assertNotIn(":latest", runner)
        self.assertIn("--network none", runner)
        self.assertIn('build_volume="raveil-chipyard-g1c-active-$input_prefix"', runner)
        self.assertIn("printf 'chipyard_revision=%s", runner)
        self.assertIn('"$chipyard_revision" "$rocket_revision"', runner)
        self.assertIn("git -C /build/chipyard rev-parse HEAD", runner)
        self.assertIn("G1C-CLEAN-REPLAY-V1 status=OK", runner)
        self.assertIn("static_stencil_oracle", verifier)
        self.assertIn("graph_reads=1280", verifier)
        self.assertIn("performance=not-measured", verifier)

    def test_verifier_accepts_padded_chisel_markers(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY)], input=self._smoke_log(), text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status=OK", result.stdout)

    def test_verifier_fails_closed_on_missing_completion(self):
        log = self._smoke_log().replace("RAVEIL-G1C-COMPLETE-V1", "REMOVED")
        result = subprocess.run(
            [sys.executable, str(VERIFY)], input=log, text=True,
            capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("completion", result.stderr)

if __name__ == "__main__":
    unittest.main()
