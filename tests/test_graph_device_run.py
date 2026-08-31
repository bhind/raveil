import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import build_parser
from raveil.graph_device_run import GraphDeviceRunError, _axi_evidence_path, _evidence_path, run
from raveil.graph_device_dag import compile_descriptor, load_descriptor, expected_transactions
from raveil.riscv_stencil_signature import input_words
from tests.test_graph_device_selected import ROOT, VERTICAL


class GraphDeviceRunTests(unittest.TestCase):
    marker = "GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/run.Abc123 private=1 publication=0"

    def _receipt(self, **changes):
        receipt = {
            "submission": {
                "graph_id": "vertical-three-point", "graph_path": VERTICAL,
                "descriptor_sha256": hashlib.sha256((ROOT / VERTICAL).read_bytes()).hexdigest(),
                "seed": 7,
            },
            "evidence_class": "rtl-simulation-functional", "performance": "not-measured",
            "invalid_programs_rejected": 8, "output_published_on_rejection": False,
            "non_claims": ["performance", "fpga"],
        }
        receipt.update(changes)
        return receipt

    def _selected_trace(self):
        program = compile_descriptor(load_descriptor(ROOT / VERTICAL))
        return expected_transactions(program, input_words(7))

    def _selected_parse(self, trace=None, segments=None, events=None):
        return (
            events or ["reset"] * 8 + ["start", "cancel", "reset", "reset", "start"],
            segments if segments is not None else [[], trace or self._selected_trace()],
        )

    def test_run_revalidates_marker_receipt_and_renders_boundaries(self) -> None:
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed) as invoked, \
             patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()), \
             patch("raveil.graph_device_run._parse_trace", return_value=self._selected_parse()):
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
        self.assertIn("Installed program order (canonical; ADD internals not directly observed):", output)
        self.assertIn("id=center op=LOAD_U32 address=center", output)
        self.assertIn("id=sum0 op=ADD_U32 inputs=center,north", output)
        self.assertIn("id=store op=STORE_U32 input=sum1", output)
        self.assertIn("Selected segment totals: transactions=1024 reads=768 writes=256", output)
        self.assertIn("READ address=", output)
        self.assertIn("receipt-bound input; not RTL-observed", output)
        self.assertIn("WRITE address=", output)
        self.assertIn("data=0x", output)

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
             patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()), \
             patch("raveil.graph_device_run._parse_trace", return_value=self._selected_parse()):
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

    def test_receipt_validation_precedes_trace_parse(self) -> None:
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed), \
             patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_run.validate_receipt", side_effect=GraphDeviceRunError("invalid")), \
             patch("raveil.graph_device_run._parse_trace") as parse_trace:
            with self.assertRaises(GraphDeviceRunError):
                run(VERTICAL, 7, ROOT)
        parse_trace.assert_not_called()

    def test_descriptor_mutation_after_receipt_validation_fails_before_trace_render(self) -> None:
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        receipt = self._receipt()
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            descriptor = repository / VERTICAL
            descriptor.parent.mkdir(parents=True)
            descriptor.write_bytes((ROOT / VERTICAL).read_bytes())

            def mutate_after_validation(*_args):
                descriptor.write_bytes(descriptor.read_bytes() + b"\n")
                return receipt

            with patch("raveil.graph_device_run.subprocess.run", return_value=completed), \
                 patch("raveil.graph_device_run._evidence_path", return_value=repository), \
                 patch("raveil.graph_device_run.validate_receipt", side_effect=mutate_after_validation), \
                 patch("raveil.graph_device_run.admit", return_value=receipt["submission"]), \
                 patch("raveil.graph_device_run._parse_trace") as parse_trace:
                with self.assertRaisesRegex(GraphDeviceRunError, "descriptor bytes changed"):
                    run(VERTICAL, 7, repository)
            parse_trace.assert_not_called()

    def test_samples_are_first_middle_last_and_write_values_are_observed(self) -> None:
        trace = self._selected_trace()
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed), \
             patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()), \
             patch("raveil.graph_device_run._parse_trace", return_value=self._selected_parse(trace)):
            output = run(VERTICAL, 7, ROOT)
        self.assertIn("sample=first output_cell=0", output)
        self.assertIn("sample=middle output_cell=128", output)
        self.assertIn("sample=last output_cell=255", output)
        self.assertIn("WRITE address=324 data=0x", output)
        self.assertIn("(RTL-observed)", output)

    def test_second_trace_read_rejects_lifecycle_segment_and_transaction_drift(self) -> None:
        completed = subprocess.CompletedProcess([], 0, self.marker + "\n", "")
        expected = self._selected_trace()
        changed = [*expected]
        changed[-1] = {**changed[-1], "address": changed[-1]["address"] - 1}
        failures = (
            self._selected_parse(events=["reset"]),
            self._selected_parse(segments=[[], expected, []]),
            self._selected_parse(changed),
        )
        for parsed in failures:
            with self.subTest(parsed=parsed), \
                 patch("raveil.graph_device_run.subprocess.run", return_value=completed), \
                 patch("raveil.graph_device_run._evidence_path", return_value=ROOT), \
                 patch("raveil.graph_device_run.validate_receipt", return_value=self._receipt()), \
                 patch("raveil.graph_device_run._parse_trace", return_value=parsed):
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

    def test_cli_accepts_explicit_axi4lite_sim_transport(self) -> None:
        args = build_parser().parse_args(
            ["graph-device", "run", "--graph", VERTICAL, "--seed", "7",
             "--transport", "axi4lite-sim"]
        )
        self.assertEqual(args.transport, "axi4lite-sim")

    def test_axi4lite_transport_is_explicit_about_catalogue_scope(self) -> None:
        marker = (
            "GraphDevice-AXI4LITE-SELECTED-EVIDENCE-V1 "
            "path=artifacts/graph_device_axi4lite_selected/run.Abc123 "
            "private=1 publication=0"
        )
        completed = subprocess.CompletedProcess([], 0, marker + "\n", "")
        receipt = {
            "evidence_class": "rtl-simulation-functional",
            "performance": "not-measured",
        }
        with patch("raveil.graph_device_run.subprocess.run", return_value=completed) as invoked, \
             patch("raveil.graph_device_run._axi_evidence_path", return_value=ROOT), \
             patch("raveil.graph_device_axi4lite_selected.finalize", return_value=receipt):
            output = run(VERTICAL, 7, ROOT, transport="axi4lite-sim")
        self.assertEqual(
            invoked.call_args.args[0],
            [str(ROOT / "hardware/chisel/run-graph-device-axi4lite-selected.sh")],
        )
        self.assertIn("Admission graph=vertical-three-point seed=7", output)
        self.assertIn("Execution scope=frozen-catalogue (not one selected invocation)", output)
        self.assertIn("Factory restart=PASS", output)

    def test_axi4lite_marker_path_is_repository_confined(self) -> None:
        marker = (
            "GraphDevice-AXI4LITE-SELECTED-EVIDENCE-V1 "
            "path=artifacts/graph_device_axi4lite_selected/run.Abc123 "
            "private=1 publication=0"
        )
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            evidence = repository / "artifacts/graph_device_axi4lite_selected/run.Abc123"
            evidence.mkdir(parents=True)
            self.assertEqual(_axi_evidence_path(marker, repository), evidence.resolve())
            with self.assertRaises(GraphDeviceRunError):
                _axi_evidence_path(marker.replace("private=1", "private=0"), repository)


if __name__ == "__main__":
    unittest.main()
