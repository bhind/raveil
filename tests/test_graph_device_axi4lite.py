import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from raveil.graph_device_axi4lite import ABI_HASHES, SOURCE_FILES, GraphDeviceAxi4LiteError, finalize, prepare

ROOT = Path(__file__).resolve().parents[1]

class GraphDeviceAxi4LiteTests(unittest.TestCase):
    def _complete_evidence(self, root):
        source_lines = []
        for name in sorted(SOURCE_FILES):
            location = root / name if name in {"abi.sha256", "graph_device_axi4lite_aperture_generated.h"} else ROOT / name
            source_lines.append(f"{name} {hashlib.sha256(location.read_bytes()).hexdigest()}")
        (root / "source.manifest").write_text("\n".join(source_lines) + "\n")
        for manifest, directory in (("rtl-first.manifest", "rtl-first"), ("rtl-second.manifest", "rtl-second")):
            target = root / directory; target.mkdir(); (target / "GraphDeviceAxi4LiteTop.sv").write_text("module x; endmodule\n")
            digest = hashlib.sha256((target / "GraphDeviceAxi4LiteTop.sv").read_bytes()).hexdigest()
            (root / manifest).write_text(f"GraphDeviceAxi4LiteTop.sv {digest}\n")
        (root / "simulator.bin").write_bytes(b"simulator")
        (root / "simulator.sha256").write_text(hashlib.sha256(b"simulator").hexdigest() + "\n")
        (root / "environment.txt").write_text("schema=raveil.graph-device-axi4lite-environment/v1\nplatform=linux/amd64\nimage_id=sha256:" + "a" * 64 + "\n")
        (root / "toolchain.txt").write_text("Scala CLI version: test\nVerilator test\n")
        (root / "device.log").write_text("GraphDevice-AXI4LITE-CONTROL-V1 status=OK evidence=rtl-simulation-functional performance=not-measured\n")

    def test_map_is_relative_nonoverlapping_and_bounded(self):
        value = json.loads((ROOT / "contracts/graph_device_axi4lite_aperture_v1.json").read_text())
        self.assertEqual(value["absolute_base"], "unassigned")
        self.assertEqual([(x["base"], x["limit"]) for x in value["apertures"].values()], [(0, 8192), (8192, 12288), (12288, 16384)])
        self.assertEqual(value["responses"], {"okay": 0, "slverr": 2, "decerr": 3})

    def test_prepare_binds_exact_abis_and_finalizes_once(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root)
            self.assertIn("RAVEIL_AXI_EXEC_BASE", (root / "graph_device_axi4lite_aperture_generated.h").read_text())
            for name, digest in ABI_HASHES.items():
                self.assertEqual(hashlib.sha256((ROOT / "contracts" / name).read_bytes()).hexdigest(), digest)
            self._complete_evidence(root)
            receipt = finalize(root)
            self.assertEqual(receipt["abi"], ABI_HASHES)
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "append-once"):
                finalize(root)

    def test_finalizer_rejects_absolute_and_substituted_inputs(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root)
            self._complete_evidence(root)
            lines = (root / "source.manifest").read_text().splitlines()
            lines[0] = "/absolute " + "a" * 64
            (root / "source.manifest").write_text("\n".join(lines) + "\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "invalid manifest"):
                finalize(root)

    def test_finalizer_rejects_source_and_rtl_digest_substitution(self):
        for manifest, expected in (("source.manifest", "source digest mismatch"), ("rtl-first.manifest", "digest mismatch")):
            with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
                root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
                lines = (root / manifest).read_text().splitlines(); fields = lines[0].split(" "); fields[1] = "0" * 64
                (root / manifest).write_text(" ".join(fields) + "\n" + "\n".join(lines[1:]) + "\n")
                with self.assertRaisesRegex(GraphDeviceAxi4LiteError, expected): finalize(root)

    def test_finalizer_rejects_symlink_nonregular_and_header_substitution(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            link = Path(tmp) / "evidence-link"; link.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "evidence symlink"):
                finalize(link)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            (root / "device.log").unlink(); (root / "device.log").mkdir()
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "unsafe file"):
                finalize(root)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            (root / "graph_device_axi4lite_aperture_generated.h").write_text("substituted\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "header drifted"):
                finalize(root)

    def test_finalizer_rejects_path_escape_manifest_and_rtl_mismatch(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            (root / "rtl-first.manifest").write_text("../escape " + "0" * 64 + "\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "invalid manifest"):
                finalize(root)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            second = root / "rtl-second" / "GraphDeviceAxi4LiteTop.sv"
            second.write_text("module y; endmodule\n")
            digest = hashlib.sha256(second.read_bytes()).hexdigest()
            (root / "rtl-second.manifest").write_text(f"GraphDeviceAxi4LiteTop.sv {digest}\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "RTL manifests differ"):
                finalize(root)

    def test_finalizer_rejects_simulator_substitution(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            root = Path(tmp) / "evidence"; prepare(root); self._complete_evidence(root)
            (root / "simulator.bin").write_bytes(b"substituted")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteError, "simulator hash mismatch"):
                finalize(root)

    def test_top_has_independent_aw_w_and_fail_closed_classes(self):
        source = (ROOT / "hardware/chisel/GraphDeviceAxi4LiteTop.scala").read_text()
        self.assertIn("extends RawModule", source)
        self.assertIn("3.U", source)  # DECERR
        self.assertIn("2.U", source)  # SLVERR
        self.assertIn("resetBarrier", source)
        self.assertIn("pendingReset", source)
        self.assertIn("!awvalid && !wvalid", source)
        self.assertIn("0.U(29.W)", source)
        self.assertIn("withClockAndReset", source)

if __name__ == "__main__": unittest.main()
