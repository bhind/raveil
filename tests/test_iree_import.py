from __future__ import annotations

from dataclasses import replace
import json
import hashlib
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from raveil.iree_import import ImportRecord, PinnedIreeImporter
from raveil.cli import main
from raveil.graph_mvp import GraphProgram


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/iree/gemm-8x8x8-i32-i64.import.json"


class FakeIree:
    def __init__(self, *, version: str = "IREE compiler version 3.11.0rc20260316 @ e4a3b0405d7d23554da26403658d0e8c3c5ecf25\n",
                 compile_code: int = 0, artifact: bytes = b"VMFB") -> None:
        self.version = version
        self.compile_code = compile_code
        self.artifact = artifact
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout):  # type: ignore[no-untyped-def]
        self.calls.append(tuple(argv))
        if "--version" in argv:
            return subprocess.CompletedProcess(argv, 0, self.version.encode(), b"")
        output = next(item[3:] for item in argv if item.startswith("-o="))
        if self.compile_code == 0:
            Path(output).write_bytes(self.artifact)
        return subprocess.CompletedProcess(argv, self.compile_code, b"", b"")


class IreeImportTests(unittest.TestCase):
    compiler = Path(__file__).resolve()

    def test_pinned_fixture_emits_only_owned_program_and_record(self) -> None:
        runner = FakeIree()
        imported = PinnedIreeImporter(self.compiler, runner=runner).import_program(
            MANIFEST
        )
        self.assertEqual((imported.program.family, imported.program.m), ("gemm", 8))
        self.assertEqual(imported.record.graph_sha256, imported.program.identity)
        self.assertEqual(imported.record.evidence_class, "compiler-import-correctness")
        self.assertNotIn("path", imported.record.to_dict())
        self.assertEqual(ImportRecord.from_dict(imported.record.to_dict()), imported.record)
        self.assertEqual(runner.calls[0], (str(self.compiler), "--version"))
        self.assertNotIn("shell", " ".join(runner.calls[1]))

    def test_manifest_source_or_tool_drift_fails_before_compile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.mlir"
            source.write_text("changed", encoding="utf-8")
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            value["source"] = source.name
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            runner = FakeIree()
            with self.assertRaisesRegex(ValueError, "source size"):
                PinnedIreeImporter(self.compiler, runner=runner).import_program(manifest)
            self.assertEqual(runner.calls, [])

            source.write_bytes((ROOT / "benchmarks/iree/gemm-8x8x8-i32-i64.mlir").read_bytes())
            value["source_size"] = source.stat().st_size
            value["tool_version"] = "future"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tool pin"):
                PinnedIreeImporter(self.compiler, runner=runner).import_program(manifest)

    def test_self_asserted_source_hash_and_wrong_revision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.mlir"
            source.write_text("module {}\n", encoding="utf-8")
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            value["source"] = source.name
            value["source_size"] = source.stat().st_size
            value["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            runner = FakeIree()
            with self.assertRaisesRegex(ValueError, "source digest"):
                PinnedIreeImporter(self.compiler, runner=runner).import_program(manifest)
            self.assertEqual(runner.calls, [])

        wrong_revision = FakeIree(
            version="IREE compiler version 3.11.0rc20260316 @ " + "0" * 40 + "\n"
        )
        with self.assertRaisesRegex(RuntimeError, "version does not match"):
            PinnedIreeImporter(self.compiler, runner=wrong_revision).import_program(MANIFEST)

    def test_timeout_and_compile_failure_are_bounded(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            PinnedIreeImporter(self.compiler, timeout_seconds=math.nan, runner=FakeIree())
        with self.assertRaisesRegex(RuntimeError, "rejected"):
            PinnedIreeImporter(
                self.compiler, runner=FakeIree(compile_code=1)
            ).import_program(MANIFEST)

    def test_cli_preflights_result_and_sidecar_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            sidecar = Path(str(output) + ".import.json")
            sidecar.write_text("preserve", encoding="utf-8")
            with mock.patch("raveil.cli.PinnedIreeImporter") as importer:
                self.assertEqual(
                    main([
                        "graph-mvp", "--import-manifest", str(MANIFEST),
                        "--iree-compile", str(self.compiler), "--output", str(output),
                    ]),
                    2,
                )
                importer.assert_not_called()
            self.assertFalse(output.exists())
            self.assertEqual(sidecar.read_text(encoding="utf-8"), "preserve")

    def test_wrong_runtime_version_and_missing_artifact_fail_closed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "version does not match"):
            PinnedIreeImporter(
                self.compiler, runner=FakeIree(version="IREE compiler version 4.0\n")
            ).import_program(MANIFEST)
        with self.assertRaisesRegex(RuntimeError, "artifact is outside"):
            PinnedIreeImporter(
                self.compiler, runner=FakeIree(artifact=b"", compile_code=0)
            ).import_program(MANIFEST)

    def test_record_rejects_type_confusion_and_evidence_override(self) -> None:
        record = PinnedIreeImporter(self.compiler, runner=FakeIree()).import_program(
            MANIFEST
        ).record
        with self.assertRaisesRegex(ValueError, "source size"):
            replace(record, source_size=True)
        with self.assertRaisesRegex(ValueError, "evidence class"):
            replace(record, evidence_class="silicon")
        malformed = record.to_dict()
        malformed["external_type"] = "mlir.Operation"
        with self.assertRaisesRegex(ValueError, "fields do not match"):
            ImportRecord.from_dict(malformed)


class SecondIreeWorkloadTests(unittest.TestCase):
    manifest = ROOT / "benchmarks/iree/gemm-bias-relu-8x8x8-i32-i64.import.json"
    compiler = Path(__file__).resolve()

    def test_second_family_retains_exact_owned_graph_and_lineage(self):
        runner = FakeIree()
        imported = PinnedIreeImporter(self.compiler, runner=runner).import_program(self.manifest)
        expected = GraphProgram.create("gemm_bias_relu", 8, 8, 8)
        self.assertEqual(imported.program, expected)
        self.assertEqual(imported.record.graph_sha256, expected.identity)
        self.assertEqual(imported.record.importer_version, "2")
        self.assertEqual(len(runner.calls), 2)
        old = PinnedIreeImporter(self.compiler, runner=FakeIree()).import_program(MANIFEST)
        self.assertNotEqual(imported.record.source_sha256, old.record.source_sha256)
        self.assertNotEqual(imported.record.graph_sha256, old.record.graph_sha256)
        self.assertEqual(imported.record.schema, old.record.schema)

    def rejection(self, source_manifest, change, source_change=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(source_manifest.read_text())
            source = (source_manifest.parent / manifest["source"]).read_text()
            if source_change:
                source = source_change(source)
            source_path = root / "fixture.mlir"
            source_path.write_text(source)
            manifest.update(source=source_path.name,
                            source_size=source_path.stat().st_size,
                            source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest())
            change(manifest)
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest))
            runner = FakeIree()
            with self.assertRaises(ValueError):
                PinnedIreeImporter(self.compiler, runner=runner).import_program(path)
            self.assertEqual(runner.calls, [])

    def test_cross_family_source_substitution_is_rejected(self):
        self.rejection(self.manifest, lambda m: m.update(family="gemm"))
        self.rejection(MANIFEST, lambda m: m.update(family="gemm_bias_relu"))

    def test_edited_source_cannot_self_authorize_its_hash(self):
        for before, after in (("tensor<8xi64>", "tensor<8xi32>"),
                              ("arith.maxsi", "arith.minsi"),
                              ("(m, n) -> (n)", "(m, n) -> (m)")):
            with self.subTest(edit=after):
                self.rejection(self.manifest, lambda m: None,
                               lambda s: s.replace(before, after))

    def test_family_shape_entry_and_tool_rejections_precede_compilation(self):
        for key, value in (("family", "unknown"), ("family", []),
                           ("m", 4), ("n", True), ("entry_point", "other"),
                           ("tool_revision", "0" * 40), ("tool_version", "future")):
            with self.subTest(key=key, value=value):
                self.rejection(self.manifest, lambda m: m.update({key: value}))

    def test_source_pin_includes_size_and_digest(self):
        self.rejection(self.manifest, lambda m: m.update(source_size=1009))
        self.rejection(self.manifest, lambda m: m.update(source_sha256="0" * 64))

    def test_new_workload_does_not_bypass_compiler_failure(self):
        with self.assertRaisesRegex(RuntimeError, "rejected"):
            PinnedIreeImporter(self.compiler, runner=FakeIree(compile_code=1)).import_program(self.manifest)


if __name__ == "__main__":
    unittest.main()
