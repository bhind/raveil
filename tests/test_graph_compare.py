"""T-0182 host functional tests; these are not RTL execution evidence."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from raveil.graph_device_dag import (
    GraphDeviceDagError, compile_descriptor, graph_oracle, load_descriptor,
    software_fallback, validate_lowering_trace,
)
from raveil.graph_device_dynamic import prepare_request, GraphDeviceDynamicError
from raveil.graph_device_dynamic_sealed import _valid_program_words, seal
from raveil.garden import GardenDynamicExplanation, GardenProjectView, render_key_session
from raveil.project_graph import describe

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = "tests/fixtures/graph_device_dynamic/compare-immediate-u32.json"


class GraphCompareTests(unittest.TestCase):
    def descriptor(self, threshold=100):
        graph = load_descriptor(ROOT / SAMPLE)
        graph["nodes"][1]["immediate"] = threshold
        return graph

    def test_unsigned_boundaries_and_canonical_results(self):
        for threshold in (0, 1, 100, 4194303):
            for operand in (0, 1, 99, 100, 101, 4194302, 4194303, 0x80000000, 0xffffffff):
                with self.subTest(threshold=threshold, operand=operand):
                    graph = self.descriptor(threshold)
                    program = compile_descriptor(graph)
                    expected = [int(operand >= threshold)] * 64 + [0] * 192
                    self.assertEqual(graph_oracle(graph, [operand] * 324), expected)
                    self.assertEqual(software_fallback(program, [operand] * 324), expected)
                    self.assertEqual(program["payload"][:4], [0x52504731, 6, 3, 8])
                    self.assertEqual(program["instructions"][1], (7 << 28) | threshold)
                    self.assertFalse(_valid_program_words(program["payload"]))
        for invalid in (-1, 4194304, True, False, None, 1.0, "100"):
            with self.assertRaises(GraphDeviceDagError):
                compile_descriptor(self.descriptor(invalid))

    def test_old_versions_and_undefined_dependencies_reject(self):
        with self.assertRaises(GraphDeviceDynamicError):
            seal(SAMPLE, 1, ROOT)
        for version in range(1, 6):
            program = compile_descriptor(self.descriptor())
            program["payload"][1] = version
            with self.assertRaises(GraphDeviceDagError):
                software_fallback(program, [0] * 324)
        for version in range(1, 5):
            graph = self.descriptor()
            graph["schema"] = f"raveil.graph-device-dag/v{version}"
            with self.assertRaises(GraphDeviceDagError):
                compile_descriptor(graph)
        for source in ("missing", "store", "threshold"):
            graph = self.descriptor()
            graph["nodes"][1]["input"] = source
            with self.assertRaises(GraphDeviceDagError):
                compile_descriptor(graph)

    def test_old_addition_retained_in_new_version(self):
        graph = load_descriptor(ROOT / "tests/fixtures/graph_device_dynamic/add-immediate-u32.json")
        old = compile_descriptor(graph)
        self.assertEqual(hashlib.sha256(struct.pack("<32I", *old["payload"])).hexdigest(),
                         "0f89997c7bdba5a5735ef14e0fa322f428d512dc44225cbaba5162299a0bb846")
        graph["schema"] = "raveil.graph-device-dag/v5"
        new = compile_descriptor(graph)
        self.assertEqual(old["instructions"], new["instructions"])
        self.assertEqual(software_fallback(new, [0xffffffff] * 324)[:64], [4] * 64)

    def test_garden_explains_unsigned_value_not_branch(self):
        graph = self.descriptor()
        program = compile_descriptor(graph)
        receipt = {"graph_id": graph["graph_id"], "program_sha256": program["program_sha256"],
                   "affine": "compact", "status": "complete", "evidence_class": "rtl-simulation-functional",
                   "performance": "not-measured",
                   **{key: "a" * 64 for key in ("output_sha256", "oracle_sha256", "fallback_sha256",
                       "simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256")}}
        view = GardenProjectView.from_saved("synthetic-host-only", program, receipt)
        shown = render_key_session(view, "jq", 100)
        self.assertIn("unsigned threshold: 100", shown)
        self.assertIn("otherwise 0", shown)
        self.assertIn("no conditional effects", shown)
        self.assertIn("unsigned source >= threshold", describe(graph, 0))
        for bad in (True, -1, 4194304, 101):
            trace = copy.deepcopy(program["lowering_trace"])
            trace["instructions"][1]["immediate"] = bad
            with self.assertRaises(GraphDeviceDagError):
                validate_lowering_trace(graph, trace, program["instructions"])
            raw = {"lowering": trace, "program_payload": program["payload"],
                   "lowering_trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.parse_lowering(raw)

    def test_cpp_v7_pairing_and_rehashed_invalid_source(self):
        compiler = shutil.which("c++")
        if compiler is None:
            self.skipTest("no C++ compiler")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request"
            prepared = prepare_request(request, SAMPLE, 0, ROOT, input_bytes=bytes(1296))
            self.assertEqual(prepared["metadata"]["schema"], "raveil.graph-device-dynamic-request/v7")
            harness = root / "admission"
            build = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "linux/include"), "-I", str(request),
                str(ROOT / "tests/graph_device_dynamic_request_host_test.cpp"),
                str(ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp"),
                "-o", str(harness)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            original = (request / "request.bin").read_bytes()
            def admitted(*args):
                return subprocess.run([str(harness), str(request), *args], capture_output=True, text=True)
            self.assertEqual(admitted().returncode, 0)
            self.assertEqual(admitted("--projected").returncode, 1)
            for offset, value in [(4, v) for v in range(1, 7)] + [(16, 1), (100, 5), (100, 7), (96 + 28 * 4, 1)]:
                raw = bytearray(original)
                struct.pack_into("<I", raw, offset, value)
                (request / "request.bin").write_bytes(raw)
                self.assertEqual(admitted().returncode, 1, (offset, value))
            # Correct old envelope/program pair, but opcode 7 must still fail.
            raw = bytearray(original)
            struct.pack_into("<I", raw, 4, 6)
            struct.pack_into("<I", raw, 100, 5)
            (request / "request.bin").write_bytes(raw)
            self.assertEqual(admitted().returncode, 1)
            raw = bytearray(original)
            words = list(struct.unpack_from("<32I", raw, 96))
            words[13] |= 7 << 22
            words[4:12] = struct.unpack("<8I", hashlib.sha256(struct.pack("<4I", 3, *words[12:15])).digest())
            struct.pack_into("<32I", raw, 96, *words)
            (request / "request.bin").write_bytes(raw)
            self.assertEqual(admitted().returncode, 1)
            with self.assertRaises(GraphDeviceDynamicError):
                prepare_request(root / "seeded", SAMPLE, 1, ROOT)

    def test_garden_rejects_malformed_version_before_comparison(self):
        program = compile_descriptor(self.descriptor())
        for bad in (None, True, "6", 6.0, 0, 7):
            trace = copy.deepcopy(program["lowering_trace"])
            trace["program_version"] = bad
            raw = {"lowering": trace, "program_payload": program["payload"],
                   "lowering_trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.parse_lowering(raw)

    def test_threshold_then_cross_dilation_matches_scalar_oracle(self):
        graph = load_descriptor(ROOT / "examples/graph-workloads/inputs/threshold-cross-dilate-descriptor.json")
        words = json.loads((ROOT / "examples/graph-workloads/inputs/threshold-cross-dilate-input.json").read_text())["words"]
        counts = []
        for threshold in (100, 150):
            for node in graph["nodes"]:
                if node["op"] == "GE_IMM_U32":
                    node["immediate"] = threshold
            expected = [0] * 256
            for row in range(8):
                for column in range(8):
                    center = (row + 1) * 10 + column + 1
                    expected[row * 8 + column] = int(any(words[center + offset] >= threshold for offset in (0, -10, 10, -1, 1)))
            compiled = compile_descriptor(graph)
            self.assertEqual(compiled["instruction_count"], 15)
            self.assertEqual(graph_oracle(graph, words), expected)
            self.assertEqual(software_fallback(compiled, words), expected)
            counts.append(sum(expected))
        self.assertEqual(counts, [15, 5])
