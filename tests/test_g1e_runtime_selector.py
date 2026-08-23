from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "hardware/chisel/chipyard-overlay/RaveilStaticStencilTLClient.scala"
CONFIG = ROOT / "hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
MEMORY = ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
RUNNER = ROOT / "hardware/chisel/run-g1e-runtime-selector.sh"
VERIFY = ROOT / "hardware/chisel/verify_g1e_runtime_selector.py"


class G1eRuntimeSelectorTests(unittest.TestCase):
    @staticmethod
    def _log(mode: str) -> str:
        graph = "1" if mode == "graph" else "0"
        dcache = "0" if mode == "graph" else "1"
        completion = "G1C" if mode == "graph" else "G1D"
        return "\n".join((
            f"RAVEIL-G1E-SELECT-V1 mode={mode} locked=1 "
            f"graph_origin={graph} dcache_origin={dcache} performance=not-measured",
            "RAVEIL-FIXTURE-STAGING-V1 invocation=1 seed=1 accepted=324",
            f"RAVEIL-{completion}-COMPLETE-V1 publication=private",
            "*** PASSED *** Completed after 123 simulation cycles",
        ))

    def _verify(self, graph: str, rocket: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            graph_log = path / "graph.log"
            rocket_log = path / "rocket.log"
            graph_log.write_text(graph, encoding="utf-8")
            rocket_log.write_text(rocket, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    "--graph-log",
                    str(graph_log),
                    "--rocket-log",
                    str(rocket_log),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_one_runtime_config_contains_control_and_both_origins(self):
        client = CLIENT.read_text()
        config = CONFIG.read_text()
        memory = MEMORY.read_text()
        self.assertIn("RaveilRuntimeIntegratedGraphRocketConfig", config)
        self.assertIn("WithRaveilRuntimeStaticStencilAttachment", config)
        self.assertIn("WithRaveilRuntimeIntegratedGraphMemorySourceRange", config)
        self.assertIn("runtimeControl: Boolean = false", client)
        self.assertIn("controlBeatBytes: Int = 8", client)
        self.assertIn("beatBytes = params.controlBeatBytes", client)
        self.assertIn("RAVEIL_GRAPH_CONTROL", (ROOT / "hardware/chisel/riscv_integrated_graph_launch.c").read_text())
        self.assertIn("runtimeSelectionLocked", memory)
        self.assertIn("runtimeGraphSelected", memory)
        self.assertIn("RAVEIL-G1E-SELECT-V1 mode=graph", memory)
        self.assertIn("RAVEIL-G1E-SELECT-V1 mode=rocket", memory)
        self.assertIn("selectedExpectedCandidateRequest", memory)

    def test_runner_uses_one_rtl_image_for_two_runtime_modes(self):
        runner = RUNNER.read_text()
        self.assertTrue(RUNNER.stat().st_mode & 0o111)
        self.assertEqual(runner.count("make -j2 CONFIG=\"$config\""), 1)
        self.assertIn("RaveilRuntimeIntegratedGraphRocketConfig", runner)
        self.assertIn('"$graph_elf"', runner)
        self.assertIn('"$rocket_elf"', runner)
        self.assertIn("runtime_selector=present", runner)
        self.assertIn("--network none", runner)
        self.assertNotIn(":latest", runner)
        self.assertIn("performance=not-measured", runner)

    def test_verifier_accepts_exact_two_mode_selection(self):
        result = self._verify(self._log("graph"), self._log("rocket"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("status=OK", result.stdout)

    def test_verifier_rejects_mode_drift_duplicate_and_failure(self):
        graph = self._log("graph")
        rocket = self._log("rocket")
        invalid_pairs = (
            (graph.replace("mode=graph", "mode=rocket"), rocket),
            (graph + "\n" + graph.splitlines()[0], rocket),
            (graph, rocket + "\nAssertion failed"),
            (graph.replace("graph_origin=1", "graph_origin=0"), rocket),
        )
        for invalid_graph, invalid_rocket in invalid_pairs:
            with self.subTest():
                result = self._verify(invalid_graph, invalid_rocket)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
