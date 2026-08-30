import hashlib
import tempfile
import unittest
from pathlib import Path

from raveil.graph_device_axi4lite_install import (
    ABI_HASHES,
    GENERATED_FILES,
    IMAGE_ID,
    SOURCE_FILES,
    GraphDeviceAxi4LiteInstallError,
    finalize,
    prepare,
)

ROOT = Path(__file__).resolve().parents[1]


class GraphDeviceAxi4LiteInstallTests(unittest.TestCase):
    def _complete_evidence(self, root: Path) -> None:
        lines = []
        for name in sorted(SOURCE_FILES):
            location = root / name if name in GENERATED_FILES else ROOT / name
            lines.append(f"{name} {hashlib.sha256(location.read_bytes()).hexdigest()}")
        (root / "source.manifest").write_text("\n".join(lines) + "\n")
        for manifest, directory in (
            ("rtl-first.manifest", "rtl-first"),
            ("rtl-second.manifest", "rtl-second"),
        ):
            target = root / directory
            target.mkdir()
            rtl = target / "GraphDeviceAxi4LiteTop.sv"
            rtl.write_text("module x; endmodule\n")
            digest = hashlib.sha256(rtl.read_bytes()).hexdigest()
            (root / manifest).write_text(f"GraphDeviceAxi4LiteTop.sv {digest}\n")
        (root / "simulator.bin").write_bytes(b"simulator")
        (root / "simulator.sha256").write_text(
            hashlib.sha256(b"simulator").hexdigest() + "\n"
        )
        (root / "environment.txt").write_text(
            "schema=raveil.graph-device-axi4lite-install-environment/v1\n"
            f"platform=linux/amd64\nimage_id={IMAGE_ID}\n"
        )
        (root / "toolchain.txt").write_text(
            "Scala CLI version: test\nVerilator test\n"
        )
        (root / "device.log").write_text(
            "GraphDevice-AXI4LITE-INSTALL-V1 status=OK "
            "evidence=rtl-simulation-functional performance=not-measured\n"
        )
        (root / "device.stderr").write_bytes(b"")
        (root / "container.stderr").write_bytes(b"")

    def test_prepare_generates_all_bounded_inputs_and_finalizes_once(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            evidence = Path(temporary) / "evidence"
            prepare(evidence)
            for name in GENERATED_FILES:
                self.assertTrue((evidence / name).is_file(), name)
            for name, digest in ABI_HASHES.items():
                self.assertEqual(
                    hashlib.sha256((ROOT / "contracts" / name).read_bytes()).hexdigest(),
                    digest,
                )
            self._complete_evidence(evidence)
            receipt = finalize(evidence)
            self.assertEqual(
                receipt["schema"],
                "raveil.graph-device-axi4lite-install-receipt/v1",
            )
            self.assertEqual(finalize(evidence, verify_existing=True), receipt)
            with self.assertRaisesRegex(
                GraphDeviceAxi4LiteInstallError, "append-once"
            ):
                finalize(evidence)

    def test_finalizer_rejects_generated_source_and_simulator_substitution(self):
        for target, expected in (
            ("graph_device_affine_generated.h", "generated input drifted"),
            ("source.manifest", "source digest mismatch"),
            ("simulator.bin", "simulator hash mismatch"),
        ):
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                evidence = Path(temporary) / "evidence"
                prepare(evidence)
                self._complete_evidence(evidence)
                path = evidence / target
                if target == "source.manifest":
                    lines = path.read_text().splitlines()
                    name, _ = lines[0].split(" ", 1)
                    lines[0] = f"{name} {'0' * 64}"
                    path.write_text("\n".join(lines) + "\n")
                else:
                    path.write_bytes(b"substituted")
                with self.assertRaisesRegex(GraphDeviceAxi4LiteInstallError, expected):
                    finalize(evidence)

    def test_harness_exercises_both_installers_and_factory_reset(self):
        source = (
            ROOT / "hardware/chisel/graph_device_axi4lite_install_verilator.cpp"
        ).read_text()
        self.assertIn("ConfigPayload", source)
        self.assertIn("ProgramPayload", source)
        self.assertIn("wrong-order program", source)
        self.assertIn("config reset restore", source)
        self.assertIn("evidence=rtl-simulation-functional", source)


if __name__ == "__main__":
    unittest.main()
