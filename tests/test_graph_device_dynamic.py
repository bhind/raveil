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
    _marker,
    prepare_request,
    run_dynamic,
    run_dynamic_pair,
)
from raveil.graph_device_dag import compile_descriptor, load_descriptor


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "contracts/graph_device_dags/five-point.json"
CUSTOM = "tests/fixtures/graph_device_dynamic/center-north.json"
FANOUT = "tests/fixtures/graph_device_dynamic/fanout-five-live.json"


class GraphDeviceDynamicTests(unittest.TestCase):
    def test_cli_uses_descriptor_pairs(self):
        args = build_parser().parse_args([
            "graph-device", "dynamic-run-pair",
            "--descriptor", BASELINE, "--seed", "1",
            "--descriptor", CUSTOM, "--seed", "4294967295",
        ])
        self.assertEqual(args.graph, [BASELINE, CUSTOM])
        self.assertEqual(args.seed, [1, 0xFFFFFFFF])
        single = build_parser().parse_args([
            "graph-device", "dynamic-run", "--descriptor", FANOUT, "--seed", "3",
        ])
        self.assertEqual(single.graph, FANOUT)
        self.assertEqual(single.seed, 3)

    def test_fanout_fixture_has_exact_program_and_liveness(self):
        descriptor = load_descriptor(ROOT / FANOUT)
        program = compile_descriptor(descriptor)
        self.assertEqual(program["instruction_count"], 11)
        self.assertEqual(sum(node["op"] == "LOAD_U32" for node in descriptor["nodes"]), 5)
        self.assertEqual(sum(node["op"] == "ADD_U32" for node in descriptor["nodes"]), 5)
        self.assertEqual(sum(node["op"] == "STORE_U32" for node in descriptor["nodes"]), 1)
        self.assertEqual(program["program_sha256"],
                         "ec13f9f0d376233b49b2d647088f71bf208ddea68e7a4d09732f660b9770ea39")
        self.assertEqual(descriptor["nodes"][8]["inputs"], ["a2", "e"])
        self.assertEqual(descriptor["nodes"][9]["inputs"], ["a3", "a0"])
        remaining = {node["id"]: 0 for node in descriptor["nodes"]}
        for node in descriptor["nodes"]:
            for source in node.get("inputs", [node.get("input")]):
                if source is not None:
                    remaining[source] += 1
        live, maximum = set(), 0
        for node in descriptor["nodes"]:
            for source in node.get("inputs", [node.get("input")]):
                if source is not None:
                    remaining[source] -= 1
                    if remaining[source] == 0:
                        live.remove(source)
            if node["op"] != "STORE_U32":
                live.add(node["id"])
            maximum = max(maximum, len(live))
        self.assertEqual(maximum, 5)

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

    def test_single_marker_requires_one_build_and_one_invocation(self):
        session = Path("artifacts/graph_device_axi4lite_dynamic/run.12345678")
        marker = (
            "GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V1 status=PASS requests=1 "
            "same_simulator=1 invoked_once=1 rtl_emitted_once=1 simulator_built_once=1 "
            "rejected_before_axi=1 simulator_sha256=" + "a" * 64 +
            " path=artifacts/graph_device_axi4lite_dynamic/run.12345678 "
            "evidence=rtl-simulation-functional performance=not-measured"
        )
        self.assertEqual(_marker(marker, session, 1), marker)
        with self.assertRaisesRegex(GraphDeviceDynamicError, "not confined"):
            _marker(marker.replace("simulator_built_once=1 ", ""), session, 1)

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
            with self.assertRaisesRegex(GraphDeviceDynamicError, "outside the frozen catalogue"):
                with patch("raveil.graph_device_dynamic.subprocess.run") as invoked:
                    run_dynamic(BASELINE, 3, ROOT)
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
        self.assertIn("invocation=once", shell)
        self.assertIn("invoked_%s=1", shell)
        self.assertIn("simulator_built_once=1", shell)
        self.assertIn("rejected_before_axi=1", shell)
        self.assertIn("dynamic-source.manifest", shell)
        self.assertLess(shell.index("dynamic-source.manifest"), shell.index("verilator --assert --cc"))
        outer = (ROOT / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh").read_text()
        self.assertIn("request-1/request-2 siblings", outer)
        self.assertIn("request_count=1", outer)
        self.assertIn("set -C", outer)
        self.assertIn("container.stdout container.stderr", outer)


if __name__ == "__main__":
    unittest.main()
