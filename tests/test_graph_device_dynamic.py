import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import build_parser
from raveil.graph_device_dynamic import (
    GraphDeviceDynamicError,
    HEADER_BYTES,
    MAGIC,
    REQUEST_BYTES,
    prepare_request,
    run_dynamic_pair,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "contracts/graph_device_dags/five-point.json"
CUSTOM = "tests/fixtures/graph_device_dynamic/center-north.json"


class GraphDeviceDynamicTests(unittest.TestCase):
    def test_cli_uses_descriptor_pairs(self):
        args = build_parser().parse_args([
            "graph-device", "dynamic-run-pair",
            "--descriptor", BASELINE, "--seed", "1",
            "--descriptor", CUSTOM, "--seed", "4294967295",
        ])
        self.assertEqual(args.graph, [BASELINE, CUSTOM])
        self.assertEqual(args.seed, [1, 0xFFFFFFFF])

    def test_prepare_is_pointer_free_and_compiles_custom_graph(self):
        with tempfile.TemporaryDirectory() as directory:
            result = prepare_request(Path(directory) / "request", CUSTOM, 7, ROOT)
            raw = (Path(directory) / "request/request.bin").read_bytes()
            self.assertEqual(len(raw), REQUEST_BYTES)
            self.assertEqual(REQUEST_BYTES, 1584)
            contract = json.loads((ROOT / "contracts/graph_device_dynamic_request_v1.json").read_text())
            self.assertEqual(contract["magic"], MAGIC)
            self.assertEqual(contract["request_bytes"], REQUEST_BYTES)
            self.assertEqual(struct.unpack_from("<8I", raw),
                             (0x52445731, 1, HEADER_BYTES, 1, 7, 32, 16, 324))
            self.assertEqual(result["metadata"]["graph_id"], "center-north")
            self.assertEqual(result["profile"]["name"], "compact")
            self.assertEqual(
                json.loads((Path(directory) / "request/request.json").read_text()),
                result["metadata"],
            )
            self.assertEqual(
                (Path(directory) / "request/request-input.bin").read_bytes(),
                (Path(directory) / "request/inputs/seed-7.bin").read_bytes(),
            )
            self.assertTrue((Path(directory) / "request/graph_device_abi_generated.h").is_file())

    def test_second_request_must_be_non_catalogue_and_count_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(GraphDeviceDynamicError, "outside the frozen catalogue"):
                with patch("raveil.graph_device_dynamic.subprocess.run") as invoked:
                    run_dynamic_pair([BASELINE, BASELINE], [1, 2], ROOT)
                    invoked.assert_not_called()
            with patch("raveil.graph_device_dynamic.subprocess.run") as invoked:
                with self.assertRaisesRegex(GraphDeviceDynamicError, "exactly two"):
                    run_dynamic_pair([BASELINE], [1], ROOT)
                invoked.assert_not_called()

    def test_runner_marker_and_outputs_are_fully_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "hardware/chisel").mkdir(parents=True)
            runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
            runner.write_text("#!/bin/sh\nexit 0\n")
            runner.chmod(0o755)
            # This test exercises pre-run admission only; an external runner is
            # intentionally not faked into a claim-bearing success.
            with self.assertRaises(GraphDeviceDynamicError):
                run_dynamic_pair([BASELINE, CUSTOM], [1, 2], repo)

    def test_runtime_files_preserve_dynamic_boundary(self):
        source = (ROOT / "hardware/chisel/graph_device_axi4lite_dynamic_verilator.cpp").read_text()
        parser = (ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp").read_text()
        shell = (ROOT / "hardware/chisel/run-graph-device-axi4lite-dynamic-in-container.sh").read_text()
        self.assertIn("run_dynamic_dag", source)
        self.assertNotIn("write_words", source)
        self.assertIn("std::ostringstream trace", source)
        self.assertIn("O_EXCL", source)
        self.assertIn("transcript output already exists", source)
        self.assertIn("validate_program", parser)
        self.assertIn("read_input_file", parser)
        self.assertIn("verilator --assert --cc", shell)
        self.assertEqual(shell.count("verilator --assert --cc"), 1)
        self.assertIn("invoked_twice=1", shell)
        self.assertIn("rejected_before_axi=1", shell)
        self.assertIn("dynamic-source.manifest", shell)
        self.assertLess(shell.index("dynamic-source.manifest"), shell.index("verilator --assert --cc"))
        outer = (ROOT / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh").read_text()
        self.assertIn("request-1/request-2 siblings", outer)
        self.assertIn("set -C", outer)
        self.assertIn("container.stdout container.stderr", outer)


if __name__ == "__main__":
    unittest.main()
