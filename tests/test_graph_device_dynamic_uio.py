from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from raveil.graph_device_dynamic_sealed import seal

ROOT = Path(__file__).resolve().parents[1]
GRAPH = "tests/fixtures/graph_device_dynamic/cross-dilation-u32.json"


class DynamicUioHostTests(unittest.TestCase):
    def test_sealed_v2_runs_full_fake_transport_and_rejects_drift_before_it(self):
        compiler = shutil.which("c++") or shutil.which("g++")
        if compiler is None:
            self.skipTest("no C++ compiler")
        with tempfile.TemporaryDirectory() as directory, patch(
            "raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()
        ):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            binary = Path(directory) / "dynamic-uio-host"
            command = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "linux/include"),
                       "-I", str(ROOT / "hardware/chisel"), "-I", str(bundle),
                       str(ROOT / "tests/graph_device_dynamic_uio_host_test.cpp"),
                       str(ROOT / "linux/src/raveil_graph_device_dynamic_request.cpp"),
                       str(ROOT / "hardware/chisel/graph_device_runtime.cpp"),
                       str(ROOT / "hardware/chisel/graph_device_affine_runtime.cpp"),
                       str(ROOT / "hardware/chisel/graph_device_dag_runtime.cpp"), "-o", str(binary)]
            built = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertEqual(subprocess.run([str(binary), str(bundle)], check=False).returncode, 0)
            raw = bytearray((bundle / "input.bin").read_bytes()); raw[0] ^= 1; (bundle / "input.bin").write_bytes(raw)
            self.assertNotEqual(subprocess.run([str(binary), str(bundle)], check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
