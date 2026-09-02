from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import build_parser
from raveil.graph_device_runtime_pair import (
    GraphDeviceRuntimePairError,
    _rejected_before_axi,
    _receipt,
    _session_path,
    run_pair,
)
from raveil.graph_device_submit import admit
from tests.test_graph_device_selected import ROOT, VERTICAL


FIVE = "contracts/graph_device_dags/five-point.json"
SHA = "a" * 64
MARKER = (
    "GraphDevice-AXI4LITE-RUNTIME-DEMO-V1 status=PASS requests=2 "
    f"same_simulator=1 rejected_before_axi=1 simulator_sha256={SHA} "
    "path=artifacts/graph_device_axi4lite_runtime_demo/run.Abc123 "
    "private=1 publication=0 evidence=rtl-simulation-functional "
    "performance=not-measured"
)


class GraphDeviceRuntimePairTests(unittest.TestCase):
    def test_cli_collects_exactly_ordered_graphs_and_seeds(self) -> None:
        args = build_parser().parse_args(
            [
                "graph-device", "run-pair",
                "--graph", FIVE, "--seed", "1",
                "--graph", VERTICAL, "--seed", "4294967295",
            ]
        )
        self.assertEqual(args.graph, [FIVE, VERTICAL])
        self.assertEqual(args.seed, [1, 0xFFFFFFFF])

    def test_count_and_admission_fail_before_runner(self) -> None:
        with patch("raveil.graph_device_runtime_pair.subprocess.run") as invoked:
            with self.assertRaises(GraphDeviceRuntimePairError):
                run_pair([FIVE], [1], ROOT)
            with self.assertRaises(ValueError):
                run_pair([FIVE, "unknown.json"], [1, 2], ROOT)
            invoked.assert_not_called()

        result = subprocess.run(
            [
                sys.executable, "-m", "raveil", "graph-device", "run-pair",
                "--graph", FIVE, "--seed", "1",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires exactly two", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_success_revalidates_order_receipts_and_one_simulator(self) -> None:
        submissions = [admit(FIVE, 1, ROOT), admit(VERTICAL, 0xFFFFFFFF, ROOT)]
        completed = subprocess.CompletedProcess([], 0, MARKER + "\n", "")
        receipts = [
            {"submission": submissions[0], "simulator_sha256": SHA},
            {"submission": submissions[1], "simulator_sha256": SHA},
        ]
        with patch("raveil.graph_device_runtime_pair.subprocess.run", return_value=completed) as invoked, \
             patch("raveil.graph_device_runtime_pair._session_path", return_value=(ROOT, SHA)), \
             patch("raveil.graph_device_runtime_pair._receipt", side_effect=receipts) as verified, \
             patch("raveil.graph_device_runtime_pair._rejected_before_axi") as rejected:
            output = run_pair([FIVE, VERTICAL], [1, 0xFFFFFFFF], ROOT)
        self.assertEqual(
            invoked.call_args.args[0],
            [
                str(ROOT / "hardware/chisel/run-graph-device-axi4lite-runtime-demo.sh"),
                "--graph", FIVE, "--seed", "1",
                "--graph", VERTICAL, "--seed", "4294967295",
            ],
        )
        self.assertEqual(verified.call_count, 2)
        rejected.assert_called_once_with(ROOT)
        self.assertIn("Request 1 graph=five-point seed=1 oracle=PASS", output)
        self.assertIn("Request 2 graph=vertical-three-point seed=4294967295 oracle=PASS", output)
        self.assertIn(f"Same simulator=PASS sha256={SHA}", output)

    def test_runner_marker_and_simulator_mismatch_fail_closed(self) -> None:
        failures = (
            subprocess.CompletedProcess([], 1, "", "failed"),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 0, MARKER + "\n" + MARKER + "\n", ""),
        )
        for completed in failures:
            with self.subTest(completed=completed), \
                 patch("raveil.graph_device_runtime_pair.subprocess.run", return_value=completed):
                with self.assertRaises(GraphDeviceRuntimePairError):
                    run_pair([FIVE, VERTICAL], [1, 2], ROOT)
        completed = subprocess.CompletedProcess([], 0, MARKER + "\n", "")
        with patch("raveil.graph_device_runtime_pair.subprocess.run", return_value=completed), \
             patch("raveil.graph_device_runtime_pair._session_path", return_value=(ROOT, SHA)), \
             patch("raveil.graph_device_runtime_pair._receipt", side_effect=[
                 {"simulator_sha256": SHA}, {"simulator_sha256": "b" * 64}
             ]), \
             patch("raveil.graph_device_runtime_pair._rejected_before_axi"):
            with self.assertRaises(GraphDeviceRuntimePairError):
                run_pair([FIVE, VERTICAL], [1, 2], ROOT)

    def test_receipt_must_preserve_request_identity(self) -> None:
        expected = admit(FIVE, 1, ROOT)
        changed = dict(expected)
        changed["seed"] = 2
        with patch(
            "raveil.graph_device_runtime_pair.finalize",
            return_value={"submission": changed, "simulator_sha256": SHA},
        ):
            with self.assertRaises(GraphDeviceRuntimePairError):
                _receipt(ROOT, expected)

    def test_marker_path_and_rejected_evidence_are_confined(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            session = repository / "artifacts/graph_device_axi4lite_runtime_demo/run.Abc123"
            rejected = session / "rejected-request"
            rejected.mkdir(parents=True)
            (rejected / "device.stderr").write_text("rejected\n", encoding="ascii")
            self.assertEqual(_session_path(MARKER, repository), (session.resolve(), SHA))
            _rejected_before_axi(session)
            (rejected / "axi-transcript.log").write_text("traffic\n", encoding="ascii")
            with self.assertRaises(GraphDeviceRuntimePairError):
                _rejected_before_axi(session)


if __name__ == "__main__":
    unittest.main()
