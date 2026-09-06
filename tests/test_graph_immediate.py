"""T-0173 host checks; synthetic parser inputs are not RTL evidence."""
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
from raveil.graph_device_dynamic_sealed import _valid_program_words
from raveil.garden import GardenDynamicExplanation, GardenProjectView
from raveil.project_graph import describe, describe_changes

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = "tests/fixtures/graph_device_dynamic/add-immediate-u32.json"


class GraphImmediateTests(unittest.TestCase):
    def descriptor(self, immediate=5):
        graph = load_descriptor(ROOT / SAMPLE)
        graph["nodes"][1]["immediate"] = immediate
        return graph

    def test_boundaries_wrap_and_trace_identity(self):
        for immediate in (0, 1, 5, 4194303):
            for operand in (0, 1, 0xffffffff):
                with self.subTest(immediate=immediate, operand=operand):
                    graph = self.descriptor(immediate)
                    program = compile_descriptor(graph)
                    output = graph_oracle(graph, [operand] * 324)
                    self.assertEqual(output[:64], [(operand + immediate) & 0xffffffff] * 64)
                    self.assertEqual(output[64:], [0] * 192)
                    self.assertEqual(output, software_fallback(program, [operand] * 324))
                    self.assertEqual(program["payload"][:4], [0x52504731, 5, 3, 8])
                    self.assertEqual(program["instructions"][1], (6 << 28) | immediate)
                    validate_lowering_trace(graph, program["lowering_trace"], program["instructions"])
                    self.assertFalse(_valid_program_words(program["payload"]))
        for immediate in (-1, 4194304, True, False, None, 1.0, "5"):
            with self.subTest(invalid=immediate), self.assertRaises(GraphDeviceDagError):
                compile_descriptor(self.descriptor(immediate))

    def test_versions_dependencies_and_rehashed_fallback_rejected(self):
        graph = self.descriptor()
        program = compile_descriptor(graph)
        for version in (1, 2, 3, 4):
            invalid = copy.deepcopy(program)
            invalid["payload"][1] = version
            with self.assertRaises(GraphDeviceDagError):
                software_fallback(invalid, [0] * 324)
        for schema in (1, 2, 3):
            invalid = copy.deepcopy(graph)
            invalid["schema"] = f"raveil.graph-device-dag/v{schema}"
            with self.assertRaises(GraphDeviceDagError):
                compile_descriptor(invalid)
        for source in ("missing", "store", "bias"):
            invalid = copy.deepcopy(graph)
            invalid["nodes"][1]["input"] = source
            with self.assertRaises(GraphDeviceDagError):
                compile_descriptor(invalid)
        invalid = copy.deepcopy(program)
        invalid["instructions"][1] |= 7 << 22
        invalid["payload"][13] = invalid["instructions"][1]
        digest = hashlib.sha256(struct.pack("<4I", 3, *invalid["instructions"])).digest()
        invalid["program_sha256"] = digest.hex()
        invalid["payload"][4:12] = struct.unpack("<8I", digest)
        with self.assertRaises(GraphDeviceDagError):
            software_fallback(invalid, [0] * 324)

    def test_old_v4_payload_bytes_are_preserved(self):
        # Recorded from pre-increment main 4476918, not recomputed as expectation.
        old = compile_descriptor(load_descriptor(ROOT / "tests/fixtures/graph_device_dynamic/product-neighbors-u32.json"))
        self.assertEqual(hashlib.sha256(struct.pack("<32I", *old["payload"])).hexdigest(),
                         "f0332280b378a7d88a3728ce6f0316a9253158997ab962dd33b77f38f9cf531f")
        self.assertEqual(old["lowering_trace"]["schema"], "raveil.graph-device-lowering-trace/v1")
        self.assertNotIn("immediate", old["lowering_trace"]["instructions"][0])

    def test_garden_and_project_explain_constant_without_execution(self):
        graph = self.descriptor()
        program = compile_descriptor(graph)
        receipt = {"graph_id": graph["graph_id"], "program_sha256": program["program_sha256"],
                   "affine": "compact", "status": "complete", "evidence_class": "rtl-simulation-functional",
                   "performance": "not-measured",
                   **{key: "a" * 64 for key in ("output_sha256", "oracle_sha256", "fallback_sha256",
                       "simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256")}}
        view = GardenProjectView.from_saved("synthetic-host-only", program, receipt)
        from raveil.garden import render_key_session
        shown = render_key_session(view, "jq", 100)
        self.assertIn("unsigned immediate: 5", shown)
        self.assertIn("modulo 2^32", shown)
        self.assertIn("immediate=5", describe(graph, 0))
        changed = self.descriptor(7)
        self.assertIn('"immediate": 7', "\n".join(describe_changes(graph, changed, bytes(1024), bytes(1024))))
        for bad in (True, -1, 4194304, 6):
            trace = copy.deepcopy(program["lowering_trace"])
            trace["instructions"][1]["immediate"] = bad
            with self.assertRaises(GraphDeviceDagError):
                validate_lowering_trace(graph, trace, program["instructions"])
            raw = {"lowering": trace, "program_payload": program["payload"],
                   "lowering_trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.parse_lowering(raw)

    def test_v6_cpp_admission_and_legacy_snapshot_rejection(self):
        compiler = shutil.which("c++")
        if compiler is None:
            self.skipTest("no C++ compiler")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request"
            result = prepare_request(request, SAMPLE, 0, ROOT, input_bytes=bytes(1296))
            self.assertEqual(result["metadata"]["schema"], "raveil.graph-device-dynamic-request/v6")
            harness = root / "admission"
            build = subprocess.run([compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "linux/include"), "-I", str(request),
                str(ROOT / "tests/graph_device_dynamic_request_host_test.cpp"),
                str(ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp"),
                "-o", str(harness)], capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            def admitted(*args):
                return subprocess.run([str(harness), str(request), *args], capture_output=True, text=True)
            self.assertEqual(admitted().returncode, 0)
            self.assertEqual(admitted("--projected").returncode, 1)
            original = (request / "request.bin").read_bytes()
            for immediate in (0, 4194303):
                raw = bytearray(original)
                struct.pack_into("<32I", raw, 96, *compile_descriptor(self.descriptor(immediate))["payload"])
                (request / "request.bin").write_bytes(raw)
                self.assertEqual(admitted().returncode, 0)
            for offset, value in ((16, 1), (100, 4)):
                raw = bytearray(original)
                struct.pack_into("<I", raw, offset, value)
                (request / "request.bin").write_bytes(raw)
                self.assertEqual(admitted().returncode, 1)
            for version in (1, 2, 3, 4, 5, 7):
                raw = bytearray(original)
                struct.pack_into("<I", raw, 4, version)
                (request / "request.bin").write_bytes(raw)
                self.assertEqual(admitted().returncode, 1, version)
            raw = bytearray(original)
            words = list(struct.unpack_from("<32I", raw, 96))
            words[13] |= 7 << 22
            words[4:12] = struct.unpack("<8I", hashlib.sha256(struct.pack("<4I", 3, *words[12:15])).digest())
            struct.pack_into("<32I", raw, 96, *words)
            (request / "request.bin").write_bytes(raw)
            self.assertEqual(admitted().returncode, 1)
            with self.assertRaises(GraphDeviceDynamicError):
                prepare_request(root / "seeded", SAMPLE, 1, ROOT)
