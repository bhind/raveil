from pathlib import Path
import tempfile
import unittest
import inspect
from unittest.mock import patch

from raveil.graph_device_dynamic_sealed import GraphDeviceDynamicSealError, seal
from raveil.graph_device_uio_dry_run import plan
import raveil.graph_device_uio_dry_run as dry_run_module


ROOT = Path(__file__).resolve().parents[1]
GRAPH = "tests/fixtures/graph_device_dynamic/fanout-five-live.json"


class GraphDeviceUioDryRunTests(unittest.TestCase):
    def test_verified_plan_stops_before_open_mmap_or_mmio(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "sealed"
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                result = plan(bundle, "/dev/uio17", ROOT)
            self.assertEqual(result["device_opened"], 0)
            self.assertEqual(result["mmap"], 0)
            self.assertEqual(result["mmio"], 0)
            self.assertEqual(result["aperture_bytes"], 0x4000)
            self.assertEqual(result["performance"], "not-measured")

    def test_invalid_device_or_unverified_payload_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "sealed"
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/mem", ROOT)
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/uio00", ROOT)
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/uio0/x", ROOT)
            (bundle / "program.bin").write_bytes(b"x")
            with self.assertRaises(GraphDeviceDynamicSealError):
                plan(bundle, "/dev/uio0", ROOT)

    def test_plan_module_has_no_transport_syscall_or_mapping_import(self):
        source = inspect.getsource(dry_run_module)
        self.assertNotIn("import mmap", source)
        self.assertNotIn("os.open", source)
        self.assertNotIn("/dev/mem", source)


if __name__ == "__main__":
    unittest.main()
