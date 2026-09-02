import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from raveil.graph_device_axi4lite_export import (
    GraphDeviceAxi4LiteExportError,
    finalize,
    prepare,
    publish,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


class GraphDeviceAxi4LiteExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARTIFACTS.mkdir(exist_ok=True)

    def _emitted(self, staging: Path) -> None:
        rtl = staging / "generated-src"
        rtl.mkdir()
        (rtl / "GraphDeviceAxi4LiteTop.sv").write_text("module GraphDeviceAxi4LiteTop; endmodule\n")
        digest = hashlib.sha256((rtl / "GraphDeviceAxi4LiteTop.sv").read_bytes()).hexdigest()
        manifest = f"GraphDeviceAxi4LiteTop.sv {digest}\n"
        (staging / "rtl.manifest").write_text(manifest)
        (staging / "rtl-repeat.manifest").write_text(manifest)
        (staging / "toolchain.txt").write_text("Scala CLI version: test\njava version test\n")

    def test_finalize_publish_and_verify_exact_bundle(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"
            prepare(staging); self._emitted(staging)
            receipt = finalize(staging, "sha256:" + "a" * 64)
            self.assertEqual(receipt["absolute_base"], "unassigned")
            self.assertEqual(receipt["board"], "unassigned")
            output = Path(parent) / "bundle"
            publish(staging, output)
            self.assertEqual(verify(output), receipt)

    def test_rejects_repeat_drift_and_missing_top(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
            (staging / "rtl-repeat.manifest").write_text("Other.sv " + "0" * 64 + "\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "repeat RTL"):
                finalize(staging, "sha256:" + "a" * 64)
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
            manifest = (staging / "rtl.manifest").read_text().replace("GraphDeviceAxi4LiteTop", "Other")
            (staging / "rtl.manifest").write_text(manifest); (staging / "rtl-repeat.manifest").write_text(manifest)
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "top-level"):
                finalize(staging, "sha256:" + "a" * 64)

    def test_rejects_bundle_mutation_symlink_and_replacement(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
            finalize(staging, "sha256:" + "a" * 64)
            output = Path(parent) / "bundle"; publish(staging, output)
            (output / "toolchain.txt").write_text("changed\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "tree or digest"):
                verify(output)
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "already exists"):
                publish(staging, output)
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
            (staging / "unsafe").symlink_to(staging / "toolchain.txt")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "unsafe tree"):
                finalize(staging, "sha256:" + "a" * 64)

    def test_rejects_invalid_image_and_source_drift(self):
        with tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
            staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "image identity"):
                finalize(staging, "latest")
            finalize(staging, "sha256:" + "a" * 64)
            output = Path(parent) / "bundle"; publish(staging, output)
            receipt_path = output / "receipt.json"
            receipt = json.loads(receipt_path.read_text()); receipt["source_sha256"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
            manifest_path = output / "manifest.json"; manifest = json.loads(manifest_path.read_text())
            manifest["receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            manifest["files"]["receipt.json"]["sha256"] = manifest["receipt_sha256"]
            manifest["files"]["receipt.json"]["bytes"] = len(receipt_path.read_bytes())
            manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
            with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, "source or ABI"):
                verify(output)

    def test_rejects_bundled_abi_or_aperture_substitution(self):
        for name, expected in (("abi.sha256", "bundled ABI"), ("graph_device_axi4lite_aperture_generated.h", "bundled aperture")):
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=ARTIFACTS) as parent:
                staging = Path(parent) / "staging"; prepare(staging); self._emitted(staging)
                (staging / name).write_text("substituted\n")
                with self.assertRaisesRegex(GraphDeviceAxi4LiteExportError, expected):
                    finalize(staging, "sha256:" + "a" * 64)


if __name__ == "__main__": unittest.main()
