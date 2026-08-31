import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_axi4lite_request import (
    GENERATED, GraphDeviceAxi4LiteRequestError, SOURCE_FILES,
    _NEGATIVE_PREFIX_LINES, prepare,
)
from raveil.graph_device_submit import admit
from tests.test_graph_device_selected import ROOT, VERTICAL


class GraphDeviceAxi4LiteRequestTests(unittest.TestCase):
    def test_prepare_binds_admitted_request_and_seed_specific_oracle(self) -> None:
        submission = admit(VERTICAL, 0xFFFFFFFF, ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            prepare(evidence, submission)
            self.assertEqual(json.loads((evidence / "request.json").read_text()), submission)
            self.assertEqual((evidence / "request-input.bin").stat().st_size, 324 * 4)
            self.assertEqual((evidence / "request-oracle.bin").stat().st_size, 256 * 4)
            self.assertEqual((evidence / "inputs" / "seed-4294967295.bin").stat().st_size, 324 * 4)

    def test_prepare_rejects_unadmitted_request_mutation(self) -> None:
        submission = dict(admit(VERTICAL, 7, ROOT)); submission["graph_id"] = "five-point"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(GraphDeviceAxi4LiteRequestError):
                prepare(Path(temporary), submission)

    def test_source_set_covers_new_bridge_and_request_artifacts(self) -> None:
        self.assertIn("hardware/chisel/graph_device_axi4lite_request_verilator.cpp", SOURCE_FILES)
        self.assertIn("hardware/chisel/run-graph-device-axi4lite-request.sh", SOURCE_FILES)
        self.assertIn("request.json", GENERATED)
        self.assertIn("graph_device_dag_generated.h", GENERATED)
        self.assertEqual(_NEGATIVE_PREFIX_LINES, 507)


if __name__ == "__main__":
    unittest.main()
