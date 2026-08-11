from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from raveil.experiment_schema import BenchmarkCandidate, WorkloadSpec
from raveil.sonatine_backend import RESULT_PREFIX, SonatineQEMUBackend


def result_line(request: int, **changes: str) -> str:
    fields = {
        "request": f"{request:016x}", "status": "1", "detail": "0",
        "job": str(request), "epoch": "1", "sequence": "1",
        "cookie": "01" * 16, "checksum": "0123456789abcdef",
        "reference": "0123456789abcdef", "approved": "1",
    }
    fields.update(changes)
    return RESULT_PREFIX + " ".join(f"{key}={value}" for key, value in fields.items()) + "\n"


class SonatineBackendTests(unittest.TestCase):
    def test_strict_result_binding_and_approval(self) -> None:
        parsed = SonatineQEMUBackend.parse_result(result_line(7), 7)
        self.assertTrue(parsed.semantic_valid)
        self.assertIsNone(parsed.latency_ns)
        self.assertEqual(parsed.checksum, parsed.reference_checksum)
        for output in (
            result_line(7) + result_line(7),
            result_line(8),
            result_line(7, status="99"),
            result_line(7, approved="0"),
            result_line(7).replace(" approved=1", " extra=1 approved=1"),
        ):
            self.assertFalse(SonatineQEMUBackend.parse_result(output, 7).semantic_valid)

    def test_request_is_exact_bounded_and_rejects_unsupported_graph(self) -> None:
        backend = SonatineQEMUBackend(Path("missing"))
        context = WorkloadSpec("g", "gemm", 8, 8, 8, "x", "x", "x", "matmul", 1)
        candidate = BenchmarkCandidate("baseline-ijk", "ijk", 0, "materialized", 0, True)
        request_id, request = backend._request(context, candidate)
        self.assertNotEqual(request_id, 0)
        self.assertEqual(len(request), 128)
        unsupported = WorkloadSpec("g", "gemm_bias_relu", 8, 8, 8, "x", "x", "x", "x", 1)
        measured = backend.measure(unsupported, candidate)
        self.assertFalse(measured.semantic_valid)
        self.assertIn("only GEMM", measured.failure)

    def test_timeout_and_parse_failure_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            kernel = Path(directory) / "sonatine.elf"
            kernel.write_bytes(b"elf")
            backend = SonatineQEMUBackend(kernel)
            context = WorkloadSpec("g", "gemm", 8, 8, 8, "x", "x", "x", "matmul", 1)
            candidate = BenchmarkCandidate("baseline-ijk", "ijk", 0, "materialized", 0, True)
            with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("qemu", 1)):
                self.assertEqual(backend.measure(context, candidate).failure, "sonatine-qemu timeout")
            completed = subprocess.CompletedProcess([], 0, stdout="no frame", stderr="")
            with mock.patch("subprocess.run", return_value=completed):
                self.assertIn("missing", backend.measure(context, candidate).failure)


if __name__ == "__main__":
    unittest.main()
