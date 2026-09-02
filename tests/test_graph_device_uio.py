from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GraphDeviceUioTests(unittest.TestCase):
    def test_uio_has_no_physical_or_fake_success_path(self) -> None:
        source = (ROOT / "linux/src/raveil_graph_device_uio.cpp").read_text()
        runner = (ROOT / "linux/src/raveil-graph-device-uio-run.cpp").read_text()
        self.assertIn("O_NOFOLLOW", source)
        self.assertIn("S_ISCHR", source)
        self.assertIn('path.compare(0, 8, prefix)', source)
        self.assertIn('minor(after.st_rdev)', source)
        self.assertIn('"/dev"', source)
        self.assertIn('major(device)', source)
        self.assertIn('maps/map0/size', source)
        self.assertIn('size == UioRegisterIo::kBytes', source)
        self.assertIn("kBytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0", source)
        self.assertNotIn("/dev/mem", source + runner)
        self.assertIn("open_checked(argv[1])", runner)
        self.assertIn("argc != 3", runner)
        self.assertNotIn("argv[3]", runner)
        self.assertIn('root / "uio-request.bin"', runner)
        self.assertIn('root / "request.json"', runner)
        self.assertIn('root / "request-input.bin"', runner)
        self.assertIn("uio_request_generated", runner)
        self.assertIn("dag_generated::kGraphs[graph].id", runner)
        self.assertIn("evidence=linux-uio-transport-unverified", runner)
        self.assertIn("same_rtl=not-verified", runner)
        self.assertIn("runtime_log, runtime_errors", runner)

    def test_request_prepare_emits_fixed_uio_binding(self) -> None:
        request = (ROOT / "raveil/graph_device_axi4lite_request.py").read_text()
        runtime = (ROOT / "hardware/chisel/graph_device_dag_runtime.cpp").read_text()
        self.assertIn('"uio-request.bin"', request)
        self.assertIn("0x52555131", request)
        self.assertIn("O_EXCL", runtime)
        self.assertIn("O_NOFOLLOW", runtime)

    def test_relative_transport_is_shared_and_bounded(self) -> None:
        transport = (ROOT / "hardware/chisel/graph_device_axi4lite_transport.h").read_text()
        verilator = (ROOT / "hardware/chisel/graph_device_axi4lite_request_verilator.cpp").read_text()
        self.assertIn("kApertureBytes = 0x4000U", transport)
        self.assertIn("kExecutionBytes = 0x2000U", transport)
        self.assertIn("kConfigBytes = 0x1000U", transport)
        self.assertIn("bytes > span - 4U", transport)
        self.assertIn("word > (std::numeric_limits", transport)
        self.assertIn("Axi4LiteTransport transport", verilator)


if __name__ == "__main__":
    unittest.main()
