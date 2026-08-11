from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock

from raveil.experiment_schema import BenchmarkCandidate, WorkloadSpec
from raveil.native_backend import NativeCBackend


class NativeBackendBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = NativeCBackend(Path("benchmark.c"), Path("benchmark"))
        self.context = WorkloadSpec(
            "g", "gemm", 8, 8, 8, "x", "x", "x", "matmul", 1
        )
        self.candidate = BenchmarkCandidate(
            "baseline-ijk", "ijk", 0, "materialized", 0, True
        )

    def measure_json(self, value: dict[str, object]):
        completed = subprocess.CompletedProcess([], 0, stdout=json.dumps(value), stderr="")
        with mock.patch("subprocess.run", return_value=completed):
            return self.backend.measure(self.context, self.candidate)

    def test_exact_native_result_schema_is_accepted(self) -> None:
        measured = self.measure_json(
            {
                "latency_ns": 1,
                "checksum": "0123456789abcdef",
                "reference_checksum": "0123456789abcdef",
                "semantic_valid": True,
                "failure": "",
            }
        )
        self.assertTrue(measured.semantic_valid)

    def test_wrong_types_missing_fields_and_negative_latency_fail_closed(self) -> None:
        base: dict[str, object] = {
            "latency_ns": 1,
            "checksum": "0123456789abcdef",
            "reference_checksum": "0123456789abcdef",
            "semantic_valid": True,
            "failure": "",
        }
        malformed = []
        for key, value in (
            ("semantic_valid", "false"),
            ("latency_ns", -1),
            ("latency_ns", 1.0),
            ("checksum", "not-hex"),
        ):
            item = dict(base)
            item[key] = value
            malformed.append(item)
        missing = dict(base)
        del missing["failure"]
        malformed.append(missing)
        for item in malformed:
            measured = self.measure_json(item)
            self.assertFalse(measured.semantic_valid)
            self.assertIn("invalid native benchmark", measured.failure)


if __name__ == "__main__":
    unittest.main()
