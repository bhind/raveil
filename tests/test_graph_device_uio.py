from pathlib import Path
import hashlib
import shutil
import struct
import subprocess
import tempfile
import unittest

from raveil.graph_device_axi4lite_request import prepare
from raveil.graph_device_submit import admit


ROOT = Path(__file__).resolve().parents[1]


class GraphDeviceUioTests(unittest.TestCase):
    def test_runtime_admission_reuses_one_binary_and_fails_closed(self) -> None:
        requests = (
            ("contracts/graph_device_dags/five-point.json", 1, "five-point"),
            ("contracts/graph_device_dags/vertical-three-point.json", 0xFFFFFFFF,
             "vertical-three-point"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            roots = []
            for number, (graph, seed, graph_id) in enumerate(requests):
                root = workspace / f"request-{number}"
                prepare(root, admit(graph, seed, ROOT))
                roots.append((root, graph_id))
            self.assertEqual(
                (roots[0][0] / "graph_device_dag_generated.h").read_bytes(),
                (roots[1][0] / "graph_device_dag_generated.h").read_bytes(),
            )
            binary = workspace / "request-admission-test"
            build = subprocess.run(
                [
                    "c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-I", str(ROOT / "linux/include"), "-I", str(roots[0][0]),
                    str(ROOT / "linux/src/raveil_graph_device_request.cpp"),
                    str(ROOT / "tests/graph_device_uio_request_host_test.cpp"),
                    "-o", str(binary),
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            binary_digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            for root, graph_id in roots:
                accepted = subprocess.run(
                    [str(binary), str(root), graph_id], cwd=ROOT,
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(accepted.returncode, 0, accepted.stderr)
                self.assertEqual(hashlib.sha256(binary.read_bytes()).hexdigest(),
                                 binary_digest)

            original = roots[0][0]

            def rejected(label, mutate):
                candidate = workspace / f"bad-{label}"
                shutil.copytree(original, candidate)
                mutate(candidate)
                result = subprocess.run(
                    [str(binary), str(candidate), "five-point"], cwd=ROOT,
                    text=True, capture_output=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0, label)

            def binding_word(offset, value):
                def mutate(root):
                    payload = bytearray((root / "uio-request.bin").read_bytes())
                    struct.pack_into("<I", payload, offset, value)
                    (root / "uio-request.bin").write_bytes(payload)
                return mutate

            for label, mutate in (
                ("magic", binding_word(0, 0)),
                ("version", binding_word(4, 2)),
                ("length-field", binding_word(8, 19)),
                ("catalogue-index", binding_word(12, 3)),
                ("truncated-binding", lambda root: (root / "uio-request.bin").write_bytes(b"x")),
                ("oversized-binding", lambda root: (root / "uio-request.bin").write_bytes(
                    (root / "uio-request.bin").read_bytes() + b"x")),
                ("binding-directory", lambda root: ((root / "uio-request.bin").unlink(),
                                                       (root / "uio-request.bin").mkdir())),
                ("binding-symlink", lambda root: ((root / "uio-request.bin").unlink(),
                    (root / "uio-request.bin").symlink_to(original / "uio-request.bin"))),
                ("request-input-mismatch", lambda root: (root / "request-input.bin").write_bytes(
                    b"\0" + (root / "request-input.bin").read_bytes()[1:])),
                ("request-input-truncated", lambda root: (root / "request-input.bin").write_bytes(
                    (root / "request-input.bin").read_bytes()[:-1])),
                ("request-input-oversized", lambda root: (root / "request-input.bin").write_bytes(
                    (root / "request-input.bin").read_bytes() + b"x")),
                ("selected-input-mismatch", lambda root: (root / "inputs/seed-1.bin").write_bytes(
                    b"\0" + (root / "inputs/seed-1.bin").read_bytes()[1:])),
                ("selected-input-truncated", lambda root: (root / "inputs/seed-1.bin").write_bytes(
                    (root / "inputs/seed-1.bin").read_bytes()[:-1])),
                ("request-input-missing", lambda root: (root / "request-input.bin").unlink()),
                ("request-input-symlink", lambda root: ((root / "request-input.bin").unlink(),
                    (root / "request-input.bin").symlink_to(original / "request-input.bin"))),
                ("inputs-symlink", lambda root: (shutil.rmtree(root / "inputs"),
                    (root / "inputs").symlink_to(original / "inputs", target_is_directory=True))),
            ):
                with self.subTest(label=label):
                    rejected(label, mutate)

            root_link = workspace / "root-link"
            root_link.symlink_to(original, target_is_directory=True)
            linked = subprocess.run(
                [str(binary), str(root_link), "five-point"], cwd=ROOT,
                text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(linked.returncode, 0)
            root_file = workspace / "root-file"
            root_file.write_bytes(b"not a directory")
            non_directory = subprocess.run(
                [str(binary), str(root_file), "five-point"], cwd=ROOT,
                text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(non_directory.returncode, 0)

            for label, mutate in (
                ("mismatch", lambda path: path.write_bytes(
                    b"\0" + path.read_bytes()[1:])),
                ("missing", lambda path: path.unlink()),
                ("symlink", lambda path: (path.unlink(),
                    path.symlink_to(roots[0][0] / "inputs/seed-1.bin"))),
            ):
                with self.subTest(runtime_prerequisite=label):
                    non_one = workspace / f"bad-runtime-prerequisite-{label}"
                    shutil.copytree(roots[1][0], non_one)
                    mutate(non_one / "inputs/seed-1.bin")
                    rejected_prerequisite = subprocess.run(
                        [str(binary), str(non_one), "vertical-three-point"],
                        cwd=ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertNotEqual(rejected_prerequisite.returncode, 0)

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
        admission = (ROOT / "linux/src/raveil_graph_device_request.cpp").read_text()
        self.assertIn('root / "uio-request.bin"', admission)
        self.assertIn('root / "request-input.bin"', admission)
        self.assertIn("admit_graph_device_request", runner)
        self.assertLess(runner.index("admit_graph_device_request"),
                        runner.index("open_checked"))
        self.assertNotIn("graph_device_uio_request_generated", runner)
        self.assertIn("dag_generated::kGraphs[index].id", admission)
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
