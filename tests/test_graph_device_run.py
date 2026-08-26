from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from raveil.graph_device_run import GraphDeviceRunError, _evidence_path, run
from tests.test_graph_device_selected import ROOT, VERTICAL


class GraphDeviceRunTests(unittest.TestCase):
    marker = "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/run.Abc123 private=1 publication=0"

    def _receipt(self, **changes):
        receipt = {
            "submission": {"graph_id": "vertical-three-point", "graph_path": VERTICAL, "seed": 7},
            "evidence_class": "rtl-simulation-functional", "performance": "not-measured",
            "invalid_programs_rejected": 8, "output_published_on_rejection": False,
            "non_claims": ["performance", "fpga"],
        }
        receipt.update(changes)
        return receipt

    def test_run_revalidates_marker_receipt_and_renders_boundaries(self) -> None:
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed) as invoked, \
             patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()):
            output = run(VERTICAL, 7, ROOT)
        self.assertEqual(
            invoked.call_args.args[0],
            [str(ROOT / "hardware/chisel/run-graph-device-selected.sh"), "--graph", VERTICAL, "--seed", "7"],
        )
        self.assertEqual(invoked.call_args.kwargs["cwd"], ROOT)
        self.assertTrue(invoked.call_args.kwargs["capture_output"])
        self.assertIn("Graph=vertical-three-point seed=7", output)
        self.assertIn("RTL=PASS", output)
        self.assertIn("Boundary busy=FAULT", output)
        self.assertIn("Rejected publication=0", output)
        self.assertIn("Performance=not-measured", output)

    def test_marker_counts_and_nonzero_runner_fail_closed(self) -> None:
        outputs = (
            "",
            "unexpected\n",
            self.marker + "\n" + self.marker + "\n",
            "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/run.Abc123 private=0 publication=0\n",
        )
        for stdout in outputs:
            with self.subTest(stdout=stdout), patch("raveil.graph_device_run.subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout, "")):
                with self.assertRaises(GraphDeviceRunError):
                    run(VERTICAL, 7, ROOT)
        with patch("raveil.graph_device_run.subprocess.run", return_value=subprocess.CompletedProcess([], 9, self.marker + "\n", "")):
            with self.assertRaises(GraphDeviceRunError):
                run(VERTICAL, 7, ROOT)

    def test_diagnostics_around_one_marker_are_not_rendered(self) -> None:
        completed = subprocess.CompletedProcess(
            [], 0, "Scala build warning\n" + self.marker + "\nVerilator note\n", ""
        )
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed), \
             patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()):
            output = run(VERTICAL, 7, ROOT)
        self.assertTrue(output.startswith("GraphDevice-RTL-RUN-V1 status=PASS\n"))
        self.assertNotIn("Scala build warning", output)
        self.assertNotIn("Verilator note", output)

    def test_real_repository_confined_path_and_symlinks_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            evidence = repository / "artifacts/graph_device_selected/run.Abc123"
            evidence.mkdir(parents=True)
            self.assertEqual(_evidence_path(self.marker, repository), evidence.resolve())
            for malformed in (
                "GraphDevice-SELECTED-EVIDENCE-V1 path=/tmp/x private=1 publication=0",
                "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/../run.Abc123 private=1 publication=0",
                "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/run.Abc123 private=0 publication=0",
            ):
                with self.subTest(marker=malformed), self.assertRaises(GraphDeviceRunError):
                    _evidence_path(malformed, repository)
            linked = repository / "artifacts/graph_device_selected/run.Abc123"
            linked.rmdir()
            try:
                linked.symlink_to(repository)
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            with self.assertRaises(GraphDeviceRunError):
                _evidence_path(self.marker, repository)

    def test_receipt_failure_is_no_traceback_at_cli_boundary(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/run.NoSuch private=1 publication=0\n", "")
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed):
            with self.assertRaises(GraphDeviceRunError):
                run(VERTICAL, 7, ROOT)

    def test_receipt_identity_drifts_fail_closed(self) -> None:
        drifts = (
            {"submission": {"graph_id": "other", "graph_path": VERTICAL, "seed": 7}},
            {"submission": {"graph_id": "vertical-three-point", "graph_path": VERTICAL, "seed": 8}},
            {"evidence_class": "emulation-functional"}, {"performance": "measured"},
            {"invalid_programs_rejected": 7}, {"output_published_on_rejection": True},
        )
        for changed in drifts:
            with self.subTest(changed=changed), \
                 patch("raveil.graph_device_run.subprocess.run", return_value=subprocess.CompletedProcess([], 0, self.marker + "\n", "")), \
                 patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
                 patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt(**changed)):
                with self.assertRaises(GraphDeviceRunError):
                    run(VERTICAL, 7, ROOT)

    def test_cli_runner_failure_is_exit_two_without_traceback(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "raveil", "graph-device", "run", "--graph", "unknown.json", "--seed", "7"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
