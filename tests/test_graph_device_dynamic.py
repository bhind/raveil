import json
from pathlib import Path
import shutil
import struct
import subprocess
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
MAX_U32 = "tests/fixtures/graph_device_dynamic/cross-dilation-u32.json"


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

    def test_max_u32_cross_dilation_uses_explicit_v2_and_unsigned_oracle(self):
        descriptor = load_descriptor(ROOT / MAX_U32)
        program = compile_descriptor(descriptor)
        self.assertEqual(program["payload"][1], 2)
        self.assertEqual(program["instruction_count"], 10)
        self.assertEqual(sum(node["op"] == "LOAD_U32" for node in descriptor["nodes"]), 5)
        self.assertEqual(sum(node["op"] == "MAX_U32" for node in descriptor["nodes"]), 4)
        self.assertEqual(sum(node["op"] == "STORE_U32" for node in descriptor["nodes"]), 1)
        from raveil.graph_device_dag import graph_oracle, software_fallback
        words = [0] * 324
        center = 19
        words[center], words[center - 18] = 0x80000000, 0x7fffffff
        words[center + 18], words[center - 1], words[center + 1] = 0, 1, 0xffffffff
        self.assertEqual(graph_oracle(descriptor, words)[0], 0xffffffff)
        self.assertEqual(software_fallback(program, words)[0], 0xffffffff)
        words[center], words[center - 18] = 0x80000000, 0x7fffffff
        words[center + 18], words[center - 1], words[center + 1] = 0, 0, 0
        self.assertEqual(graph_oracle(descriptor, words)[0], 0x80000000)
        self.assertEqual(software_fallback(program, words)[0], 0x80000000)
        words[center], words[center - 18] = 7, 7
        self.assertEqual(graph_oracle(descriptor, words)[0], 7)
        words[center], words[center - 18] = 0, 0
        self.assertEqual(graph_oracle(descriptor, words)[0], 0)

    def test_v1_payload_rejects_max_and_v2_request_pair_is_exact(self):
        from raveil.graph_device_dynamic_sealed import _valid_program_words
        legacy = compile_descriptor(load_descriptor(ROOT / FANOUT))["payload"]
        self.assertTrue(_valid_program_words(legacy))
        self.assertEqual(legacy[:4], [0x52504731, 1, 11, 8])
        self.assertEqual(compile_descriptor(load_descriptor(ROOT / FANOUT))["program_sha256"],
                         "ec13f9f0d376233b49b2d647088f71bf208ddea68e7a4d09732f660b9770ea39")
        legacy[12] = (4 << 28) | (legacy[12] & 0x0fffffff)
        self.assertFalse(_valid_program_words(legacy))
        with tempfile.TemporaryDirectory() as directory:
            result = prepare_request(Path(directory) / "request", MAX_U32, 3, ROOT)
            self.assertEqual(struct.unpack_from("<I", result["request"], 4)[0], 2)
            self.assertEqual(result["program"]["payload"][1], 2)

    def test_program_wire_negative_paths_fail_closed(self):
        from raveil.graph_device_dynamic_sealed import _valid_program_words
        v2 = compile_descriptor(load_descriptor(ROOT / MAX_U32))["payload"]
        for label, change in (
            ("unknown", lambda words: words.__setitem__(17, 5 << 28)),
            ("padding", lambda words: words.__setitem__(22, 1)),
            ("reserved", lambda words: words.__setitem__(17, words[17] | 1)),
            ("undefined", lambda words: words.__setitem__(17, (4 << 28) | (7 << 25) | (7 << 22) | (6 << 19))),
            ("store-placement", lambda words: words.__setitem__(17, 3 << 28)),
        ):
            with self.subTest(label=label):
                mutated = list(v2); change(mutated)
                self.assertFalse(_valid_program_words(mutated))
        cross = list(v2); cross[1] = 1
        self.assertFalse(_valid_program_words(cross))
        self.assertFalse(_valid_program_words(v2[:1] + [3] + v2[2:]))

    def test_standalone_fallback_revalidates_version_and_digest(self):
        from raveil.graph_device_dag import GraphDeviceDagError, graph_oracle, software_fallback
        for descriptor_path in (FANOUT, MAX_U32):
            program = compile_descriptor(load_descriptor(ROOT / descriptor_path))
            self.assertEqual(software_fallback(program, [0] * 324), graph_oracle(load_descriptor(ROOT / descriptor_path), [0] * 324))
            if program["payload"][1] == 2:
                version_mutation = {**program, "payload": list(program["payload"])}
                version_mutation["payload"][1] = 1
                with self.assertRaises(GraphDeviceDagError):
                    software_fallback(version_mutation, [0] * 324)
            digest_mutation = {**program, "payload": list(program["payload"])}
            digest_mutation["payload"][4] ^= 1
            with self.assertRaises(GraphDeviceDagError):
                software_fallback(digest_mutation, [0] * 324)

    def test_descriptor_identifier_admission_is_bounded_ascii(self):
        descriptor = load_descriptor(ROOT / MAX_U32)
        for graph_id in ("", "a" * 32, "ümlaut"):
            with self.subTest(graph_id=graph_id):
                changed = {**descriptor, "graph_id": graph_id}
                from raveil.graph_device_dag import GraphDeviceDagError, validate_descriptor
                with self.assertRaises(GraphDeviceDagError): validate_descriptor(changed)

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
        self.assertIn("contracts/graph_device_dynamic_request_v2.json", shell)
        self.assertIn("contracts/graph_device_program_v2.json", shell)
        self.assertLess(shell.index("dynamic-source.manifest"), shell.index("verilator --assert --cc"))
        outer = (ROOT / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh").read_text()
        self.assertIn("request-1/request-2 siblings", outer)
        self.assertIn("request_count=1", outer)
        self.assertIn("set -C", outer)
        self.assertIn("container.stdout container.stderr", outer)

    def test_cxx_admission_precedes_model_and_chisel_gates_v2_max(self):
        parser = (ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp").read_text()
        bridge = (ROOT / "hardware/chisel/graph_device_axi4lite_dynamic_verilator.cpp").read_text()
        installer = (ROOT / "hardware/chisel/GraphDeviceProgramInstaller.scala").read_text()
        self.assertIn("request_version == kVersionV2", parser)
        self.assertIn("opcode == 4U", parser)
        self.assertIn("dynamic program digest is invalid", parser)
        self.assertLess(bridge.index("read_dynamic_graph_device_request"), bridge.index("VGraphDeviceAxi4LiteTop top"))
        self.assertIn("MaxU32Opcode", installer)
        self.assertIn("payloadVersion === 2.U", installer)
        fallback = (ROOT / "hardware/chisel/graph_device_dag_runtime.cpp").read_text()
        self.assertIn("bool valid_fallback_program", fallback)
        self.assertIn("opcode == 4U && payload[1] == 2U", fallback)
        self.assertLess(fallback.index("if (!valid_fallback_program(graph.payload)) return false;"),
                        fallback.index("output.fill(0U);"))
        from raveil.graph_device_dynamic_sealed import SOURCE_PATHS, _expected_runner_source_manifest, seal, verify
        self.assertIn("contracts/graph_device_dynamic_request_v2.json", SOURCE_PATHS)
        self.assertIn("contracts/graph_device_program_v2.json", SOURCE_PATHS)
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
            sealed = Path(seal(MAX_U32, 3, ROOT)["path"])
            expected = _expected_runner_source_manifest(verify(sealed, ROOT)).decode("ascii")
        self.assertIn("orchestration/contracts/graph_device_dynamic_request_v2.json ", expected)
        self.assertIn("orchestration/contracts/graph_device_program_v2.json ", expected)

    def test_cxx_host_admission_rejects_digest_before_model(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if compiler is None:
            self.skipTest("no C++ compiler is available for host admission regression")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request"
            prepare_request(request, MAX_U32, 3, ROOT)
            harness = root / "dynamic-request-host"
            compile_result = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-I", str(ROOT / "linux/include"), "-I", str(request),
                 str(ROOT / "tests/graph_device_dynamic_request_host_test.cpp"),
                 str(ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp"),
                 "-o", str(harness)], capture_output=True, text=True, check=False,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            self.assertEqual(subprocess.run([str(harness), str(request)], check=False).returncode, 0)
            raw = bytearray((request / "request.bin").read_bytes())
            raw[96 + 4 * 4] ^= 1
            (request / "request.bin").write_bytes(raw)
            self.assertEqual(subprocess.run([str(harness), str(request)], check=False).returncode, 1)
            self.assertFalse((request / "axi-transcript.log").exists())
            self.assertFalse(any(request.glob("simulator*")))


if __name__ == "__main__":
    unittest.main()
