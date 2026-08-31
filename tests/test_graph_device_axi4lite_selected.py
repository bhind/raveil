import tempfile
import unittest
from pathlib import Path

from raveil.graph_device_axi4lite_selected import (
    GraphDeviceAxi4LiteSelectedError, SOURCE_FILES, prepare,
)

ROOT = Path(__file__).resolve().parents[1]


class GraphDeviceAxi4LiteSelectedTests(unittest.TestCase):
    def test_prepare_binds_catalogue_and_aperture_without_replacing_dag_headers(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            evidence = Path(temporary) / "evidence"
            artifact = prepare(evidence)
            self.assertEqual([item["graph_id"] for item in artifact["graphs"]], [
                "five-point", "compact-horizontal-three-point", "vertical-three-point",
            ])
            self.assertIn("RAVEIL_AXI_PROGRAM_BASE", (evidence / "graph_device_axi4lite_aperture_generated.h").read_text())
            self.assertTrue((evidence / "graph_device_dag_generated.h").is_file())

    def test_source_set_names_the_transport_bridge_and_offline_runners(self):
        self.assertIn("hardware/chisel/graph_device_axi4lite_selected_verilator.cpp", SOURCE_FILES)
        self.assertIn("hardware/chisel/run-graph-device-axi4lite-selected.sh", SOURCE_FILES)
        self.assertIn("hardware/chisel/run-graph-device-axi4lite-selected-in-container.sh", SOURCE_FILES)
        source = (ROOT / "hardware/chisel/graph_device_axi4lite_selected_verilator.cpp").read_text()
        self.assertIn("run_dag(bridge, bridge, bridge", source)
        self.assertNotIn("graph_id", source)
        runner = (ROOT / "hardware/chisel/run-graph-device-axi4lite-selected.sh").read_text()
        self.assertIn("--network none", runner)
        self.assertIn("required cached offline image is unavailable", runner)

    def test_prepare_refuses_nonempty_evidence(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            evidence = Path(temporary) / "evidence"; evidence.mkdir(); (evidence / "old").write_text("x")
            with self.assertRaises(Exception):
                prepare(evidence)


if __name__ == "__main__":
    unittest.main()
