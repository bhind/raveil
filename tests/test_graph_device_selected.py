import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from raveil.graph_device_selected import GraphDeviceSelectedError, finalize, prepare, validate_receipt
from raveil.graph_device_selected import _cache_manifest, _manifest
from raveil.graph_device_dag import expected_transactions
from raveil.riscv_stencil_signature import input_words


ROOT = Path(__file__).resolve().parents[1]
VERTICAL = "contracts/graph_device_dags/vertical-three-point.json"


class GraphDeviceSelectedTests(unittest.TestCase):
    def _complete(self, root: Path) -> None:
        prepared = prepare(VERTICAL, 7, root)
        submission = prepared["submission"]
        oracle = (root / "direct-oracle.bin").read_bytes()
        graph = submission["graph_id"]
        seed = submission["seed"]
        (root / f"fallback-output-{graph}-seed-{seed}.bin").write_bytes(oracle)
        (root / f"private-output-{graph}-seed-{seed}.bin").write_bytes(oracle)
        (root / "rtl-first.hashes").write_text("a" * 64 + "\n", encoding="ascii")
        (root / "rtl-second.hashes").write_text("a" * 64 + "\n", encoding="ascii")
        import hashlib
        (root / "rtl-export.sha256").write_text(
            hashlib.sha256((root / "rtl-first.hashes").read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )
        simulator = b"synthetic selected simulator"
        (root / "simulator.bin").write_bytes(simulator)
        (root / "simulator.sha256").write_text(hashlib.sha256(simulator).hexdigest() + "\n", encoding="ascii")
        docker = hashlib.sha256((ROOT / "hardware/chisel/Dockerfile").read_bytes()).hexdigest()
        (root / "environment.txt").write_text(
            "schema=raveil.graph-device-selected-environment/v1\nplatform=linux/amd64\n"
            "dockerfile_sha256=" + docker + "\nimage_id=sha256:" + "d" * 64 + "\n",
            encoding="ascii",
        )
        (root / "toolchain.txt").write_text("Scala CLI 1.10.1\nopenjdk 17\nVerilator 5\n", encoding="ascii")
        (root / "toolchain.sha256").write_text(
            hashlib.sha256((root / "toolchain.txt").read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )
        artifact = json.loads((root / "selected-artifact.json").read_text(encoding="ascii"))
        programs = {item["graph_id"]: item for item in artifact["graphs"]}
        def trace(items):
            return "".join(
                "GraphDevice-TRACE-V1 event=transaction "
                f"write={int(item['write'])} address={item['address']} data={item['data']:08x}\n"
                for item in items
            )
        (root / "transaction-trace.txt").write_text(
            "GraphDevice-TRACE-V1 event=reset\n" * 8
            + "GraphDevice-TRACE-V1 event=start\n"
            + trace(expected_transactions(programs["five-point"], input_words(1))[:1])
            + "GraphDevice-TRACE-V1 event=cancel\nGraphDevice-TRACE-V1 event=reset\n"
            + "GraphDevice-TRACE-V1 event=reset\nGraphDevice-TRACE-V1 event=start\n"
            + trace(expected_transactions(programs[graph], input_words(seed))), encoding="ascii"
        )
        manifest = "StaticStencilRegion.sv 1 " + "a" * 64 + "\n"
        (root / "rtl-first.manifest").write_text(manifest, encoding="ascii")
        (root / "rtl-second.manifest").write_text(manifest, encoding="ascii")
        (root / "dependency-cache.manifest").write_text("scala/cache.bin 0 " + "e" * 64 + "\n", encoding="ascii")
        (root / "device.log").write_text(
            "GraphDevice-DAG-NEGATIVE-V1 partial=FAULT order=FAULT duplicate=FAULT opcode=FAULT undefined=FAULT reserved=FAULT missing_store=FAULT busy=FAULT cases=8 output_published=0\n"
            f"GraphDevice-DAG-RUN-V1 graph={graph} seed={seed} mode=complete status=COMPLETED output_published=1 polls=1\n"
            f"GraphDevice-DAG-SELECTED-RUNTIME-V1 status=OK graph={graph} seed={seed} completed=1 invalid_cases=8 same_rtl=1 rtl_regeneration=0 evidence=rtl-simulation-functional performance=not-measured\n",
            encoding="ascii",
        )

    def test_prepare_and_finalize_bind_selected_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            self._complete(root)
            receipt = finalize(root)
            self.assertEqual(receipt["evidence_class"], "rtl-simulation-functional")
            self.assertEqual(receipt["submission"]["graph_id"], "vertical-three-point")
            self.assertEqual(receipt["invalid_programs_rejected"], 8)
            self.assertEqual(
                receipt["dependency_cache_sha256"],
                hashlib.sha256((root / "dependency-cache.manifest").read_bytes()).hexdigest(),
            )
            self.assertEqual(validate_receipt(root), receipt)
            with self.assertRaises(GraphDeviceSelectedError):
                finalize(root)
            (root / "selected-receipt.json").write_text("{}\n", encoding="ascii")
            with self.assertRaises(GraphDeviceSelectedError):
                validate_receipt(root)

    def test_prepare_accepts_empty_mktemp_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "run.abc123"
            root.mkdir()
            result = prepare(VERTICAL, 7, root)
            self.assertEqual(result["submission"]["graph_id"], "vertical-three-point")
            for name in (
                "graph_device_abi_generated.h", "graph_device_affine_generated.h",
                "graph_device_dag_generated.h",
            ):
                self.assertTrue((root / name).is_file())
            self.assertEqual((root / "input.bin").read_bytes(), (root / "inputs/seed-7.bin").read_bytes())

    def test_rejects_each_bound_evidence_mutation(self) -> None:
        mutations = (
            ("device.log", lambda path: path.write_text(path.read_text() + "extra\n")),
            ("transaction-trace.txt", lambda path: path.write_text("GraphDevice-TRACE-V1 event=reset\n")),
            ("selected-sources.json", lambda path: path.write_text("{}\n")),
            ("environment.txt", lambda path: path.write_text("bad\n")),
            ("toolchain.txt", lambda path: path.write_text("changed\n")),
            ("simulator.sha256", lambda path: path.write_text("bad\n")),
            ("simulator.bin", lambda path: path.write_bytes(b"bad")),
            ("selected-artifact.json", lambda path: path.write_text("{}\n")),
            ("submission.json", lambda path: path.write_text("{}\n")),
            ("input.bin", lambda path: path.write_bytes(b"bad")),
            ("direct-oracle.bin", lambda path: path.write_bytes(b"bad")),
            ("graph_device_abi_generated.h", lambda path: path.write_bytes(b"bad")),
            ("graph_device_affine_generated.h", lambda path: path.write_bytes(b"bad")),
            ("graph_device_dag_generated.h", lambda path: path.write_bytes(b"bad")),
            ("rtl-first.manifest", lambda path: path.write_text("../bad 1 " + "a" * 64 + "\n")),
        )
        for name, mutate in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "evidence"
                self._complete(root)
                mutate(root / name)
                with self.assertRaises(GraphDeviceSelectedError):
                    finalize(root)

    def test_rtl_manifest_uses_ascii_c_locale_order(self) -> None:
        ordered = (
            b"verification/assert/Owned.sv 1 " + b"a" * 64 + b"\n"
            + b"verification/assert/layers.sv 1 " + b"b" * 64 + b"\n"
        )
        _manifest(ordered)
        unordered = (
            b"verification/assert/layers.sv 1 " + b"b" * 64 + b"\n"
            + b"verification/assert/Owned.sv 1 " + b"a" * 64 + b"\n"
        )
        with self.assertRaises(GraphDeviceSelectedError):
            _manifest(unordered)

    def test_dependency_cache_manifest_is_strict_and_runner_is_readonly(self) -> None:
        valid = b"A 0 " + b"a" * 64 + b"\nz 1 " + b"b" * 64 + b"\n"
        _cache_manifest(valid)
        for payload in (b"", b"../x 0 " + b"a" * 64 + b"\n", b"z -1 " + b"a" * 64 + b"\n", b"z 0 bad\n", b"z 0 " + b"a" * 64 + b"\nA 0 " + b"b" * 64 + b"\n"):
            with self.subTest(payload=payload), self.assertRaises(GraphDeviceSelectedError):
                _cache_manifest(payload)
        runner = (ROOT / "hardware/chisel/run-graph-device-selected.sh").read_text()
        self.assertIn("target=/root/.cache,readonly", runner)
        inner = (ROOT / "hardware/chisel/run-graph-device-dag-in-container.sh").read_text()
        self.assertIn("-type l", inner)
        self.assertIn("! -type d -a ! -type f", inner)
        self.assertIn("dependency cache contains a symbolic link or non-regular entry", inner)

    def test_rejects_tampered_output_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            self._complete(root)
            target = root / "private-output-vertical-three-point-seed-7.bin"
            target.write_bytes(b"changed")
            with self.assertRaises(GraphDeviceSelectedError):
                finalize(root)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            self._complete(root)
            try:
                (root / "unexpected").symlink_to(root / "device.log")
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            with self.assertRaises(GraphDeviceSelectedError):
                finalize(root)

    def test_rejects_bad_submission_seed_and_shell_before_docker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(GraphDeviceSelectedError):
                prepare("contracts/graph_device_dags/unknown.json", 7, Path(temporary) / "evidence")
            with self.assertRaises(GraphDeviceSelectedError):
                prepare(VERTICAL, -1, Path(temporary) / "evidence")
        result = subprocess.run(
            ["sh", "hardware/chisel/run-graph-device-selected.sh", "--graph", "unknown.json", "--seed", "7"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)

    def test_sources_preserve_selected_only_and_abi_boundaries(self) -> None:
        runtime = (ROOT / "hardware/chisel/graph_device_dag_runtime.cpp").read_text()
        verilator = (ROOT / "hardware/chisel/graph_device_verilator.cpp").read_text()
        runner = (ROOT / "hardware/chisel/run-graph-device-selected.sh").read_text()
        self.assertIn("run_selected_dag", runtime)
        self.assertIn("selected->affine", runtime)
        self.assertIn("--dag-selected", verilator)
        self.assertIn("--network none", runner)
        self.assertIn("no-new-privileges=true", runner)
        self.assertNotIn("vivado", runner.lower())
        inner = (ROOT / "hardware/chisel/run-graph-device-dag-in-container.sh").read_text()
        self.assertIn('[ "$#" -ne 1 ] && [ "$#" -ne 3 ]', inner)
        self.assertIn('--dag "$evidence_root"', inner)
        static = (ROOT / "hardware/chisel/StaticStencilRegion.scala").read_text()
        for source in (
            "GraphDeviceAffineConfigInstaller.scala",
            "GraphDeviceProgramInstaller.scala",
        ):
            self.assertIn(f"//> using file {source}", static)
            self.assertIn(source, inner)
            self.assertIn(f"hardware/chisel/{source}", __import__("raveil.graph_device_selected", fromlist=["SOURCE_PATHS"]).SOURCE_PATHS)


if __name__ == "__main__":
    unittest.main()
