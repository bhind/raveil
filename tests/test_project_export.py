import base64
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import main
from raveil.project import Project, init_project
from raveil import project_export as export


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = Project(init_project(self.base / "project"))
        self.record = self.project.run("logs", "native", kernel=Path("unused"), qemu="unused", compiler="cc")
        self.run_id = self.record["run_id"]
        self.root = self.project.root / "runs" / self.run_id
        self.members = ["workspace/errors.txt"]
        self.dest = self.base / "selected.json"

    def view(self):
        return export.preview(self.project, self.run_id, self.members)

    def write(self, **kwargs):
        return export.export_selected(self.project, self.run_id, self.members, self.dest,
                                      kwargs.pop("expected", self.view()["preview_sha256"]),
                                      **dict({"acknowledge": True}, **kwargs))

    def test_actual_preview_and_selected_export(self):
        view = self.view()
        self.assertEqual(view["selected_count"], 1)
        self.assertGreater(view["omitted_count"], 0)
        self.assertEqual(view["selected_bytes"], 2)
        with patch.object(self.project, "run", side_effect=AssertionError("must not execute")):
            result = self.write()
        bundle = json.loads(self.dest.read_text())
        self.assertEqual(base64.b64decode(bundle["files"][0]["base64"]), b"2\n")
        self.assertEqual(bundle["source_preview_sha256"], view["preview_sha256"])
        self.assertFalse(bundle["authenticated"])
        self.assertFalse(bundle["replayable_full_run"])
        self.assertEqual([f["path"] for f in bundle["files"]], self.members)
        self.assertNotIn("inputs/left.txt", self.dest.read_text())
        self.assertNotIn("recipe", bundle)
        self.assertNotIn("inventory", bundle)
        self.assertEqual(stat.S_IMODE(self.dest.stat().st_mode), 0o600)
        self.assertEqual(result["sha256"], export.digest(self.dest.read_bytes()))
        inspection = export.inspect_export(self.dest)
        self.assertEqual(inspection["selected_bytes"], 2)
        self.assertEqual(inspection["bundle_sha256"], result["sha256"])

    def test_explicit_ack_selection_and_preview_required(self):
        for kwargs in ({"acknowledge": False}, {"expected": "0" * 64}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.write(**kwargs)
        with self.assertRaises(ValueError):
            export.export_selected(self.project, self.run_id, [], self.dest, "x", True)
        self.assertFalse(self.dest.exists())
        self.assertEqual(export.preview(self.project, self.run_id)["selected_count"], 0)

    def test_selection_validation(self):
        for selection in (["../outside"], ["/record.json"], ["a\\b"], ["missing"],
                          ["inputs"], self.members * 2, ["a\x1bb"], ["C:evil"]):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                export.preview(self.project, self.run_id, selection)

    def test_original_record_and_missing_nofollow_rejected(self):
        for member in ("record.json", "record.sha256"):
            with self.subTest(member=member), self.assertRaises(ValueError):
                export.preview(self.project, self.run_id, [member])
            with self.assertRaises(ValueError):
                export.export_selected(self.project, self.run_id, [member], self.dest, "x", True)
        with patch.object(export.os, "O_NOFOLLOW", 0), self.assertRaises(ValueError):
            self.view()
        self.assertFalse(self.dest.exists())

    def test_existing_output_and_project_output_rejected(self):
        self.dest.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            self.write()
        self.assertEqual(self.dest.read_bytes(), b"keep")
        self.dest = self.project.root / "new.json"
        with self.assertRaises(ValueError):
            self.write()
        self.assertFalse(self.dest.exists())

    def test_output_symlink_ancestor(self):
        (self.base / "linked").symlink_to(self.base, target_is_directory=True)
        self.dest = self.base / "linked" / "new.json"
        with self.assertRaises(ValueError):
            self.write()
        self.assertFalse((self.base / "new.json").exists())

    def test_symlink_and_hardlink_source(self):
        file = self.root / "workspace/errors.txt"
        (self.base / "link").hardlink_to(file)
        with self.assertRaises(ValueError):
            self.view()

    def test_unselected_tampering_rejected(self):
        prior = self.view()["preview_sha256"]
        (self.root / "inputs/left.txt").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.write(expected=prior)
        self.assertFalse(self.dest.exists())

    def test_changed_during_capture_and_symlink_source(self):
        original = export.os.read
        changed = False
        def read(fd, size):
            nonlocal changed
            data = original(fd, size)
            if not changed:
                changed = True
                (self.root / "inputs/left.txt").write_bytes(b"changed")
            return data
        with patch.object(export.os, "read", side_effect=read), self.assertRaises(ValueError):
            self.view()

    def test_source_link_and_resource_limits(self):
        with patch.object(export, "MAX_BYTES", 1), self.assertRaises(ValueError):
            self.view()
        with patch.object(export, "MAX_ENTRIES", 1), self.assertRaises(ValueError):
            self.view()
        target = self.root / "workspace/errors.txt"
        target.unlink()
        target.symlink_to(self.root / "inputs/events.txt")
        with self.assertRaises(ValueError):
            self.view()

    def test_encoded_size_limit_and_link_failure_leave_no_output(self):
        with patch.object(export, "MAX_EXPORT_BYTES", 1), self.assertRaises(ValueError):
            self.write()
        with patch.object(export.os, "link", side_effect=OSError("publication failed")), self.assertRaises(OSError):
            self.write()
        self.assertFalse(self.dest.exists())
        self.assertEqual(list(self.base.glob(".raveil-export-*")), [])

    def test_cli_preview_export(self):
        common = [self.run_id, "--project", str(self.project.root), "--member", self.members[0]]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["project", "export-preview", *common]), 0)
        token = json.loads(out.getvalue())["preview_sha256"]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["project", "export", *common, str(self.dest),
                                   "--expect-preview", token, "--acknowledge-sensitive-data"]), 0)
        self.assertTrue(self.dest.exists())


class InspectExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "selected.json"
        self.bundle = {"schema": export.SCHEMA, "kind": "selected-file-derivative",
                       "authenticated": False, "replayable_full_run": False,
                       "source_run_id": "example", "source_record_sha256": "a" * 64,
                       "source_preview_sha256": "b" * 64, "omitted_count": 2,
                       "warnings": export.WARNINGS,
                       "files": [{"path": "workspace/errors.txt", "bytes": 2,
                                  "sha256": export.digest(b"2\n"), "base64": "Mgo="}]}

    def inspect(self, bundle=None):
        self.source.write_bytes(export.encoded(self.bundle if bundle is None else bundle))
        return export.inspect_export(self.source)

    def test_valid_inspection_is_read_only_without_source_project(self):
        self.inspect()
        before = self.source.read_bytes()
        stdout = io.StringIO()
        with patch("raveil.project.Project", side_effect=AssertionError("no project read")), \
                contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["project", "inspect-export", str(self.source)]), 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["internal_integrity"], "consistent")
        for field in ("authenticated", "replayable_full_run", "source_verified"):
            self.assertIs(result[field], False)
        self.assertEqual(result["files"], [{k: v for k, v in self.bundle["files"][0].items()
                                          if k != "base64"}])
        self.assertNotIn("Mgo=", stdout.getvalue())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [self.source])

    def test_malformed_json_duplicate_keys_and_constants(self):
        for raw in (b"{", b"[]", b"null", b"\xff", b'{"x":1,"x":2}',
                    b'{"x":NaN}', b'{"x":Infinity}', b"[" * 2000 + b"]" * 2000):
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                self.source.write_bytes(raw)
                export.inspect_export(self.source)
        raw = export.encoded(self.bundle).replace(b'"bytes": 2', b'"bytes": 2, "bytes": 2')
        self.source.write_bytes(raw)
        with self.assertRaises(ValueError):
            export.inspect_export(self.source)

    def test_wrong_schema_claims_types_and_extra_fields(self):
        for key, value in (("schema", "unknown"), ("kind", "run"), ("authenticated", True),
                           ("authenticated", 0), ("replayable_full_run", True), ("warnings", []),
                           ("source_run_id", []), ("source_run_id", "../run"),
                           ("source_record_sha256", "g" * 64), ("source_preview_sha256", None),
                           ("omitted_count", True), ("omitted_count", -1),
                           ("omitted_count", 1024), ("files", []), ("extra", "no")):
            bundle = copy.deepcopy(self.bundle)
            bundle[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.inspect(bundle)
        del self.bundle["warnings"]
        with self.assertRaises(ValueError):
            self.inspect()

    def test_paths_duplicates_and_prefix_conflicts(self):
        for path in ("../x", "/x", "a\\b", "a\x1bb", "record.json", "record.sha256", ""):
            bundle = copy.deepcopy(self.bundle)
            bundle["files"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.inspect(bundle)
        for path in ("workspace/errors.txt", "WORKSPACE/errors.txt", "workspace"):
            bundle = copy.deepcopy(self.bundle)
            second = copy.deepcopy(bundle["files"][0])
            second["path"] = path
            bundle["files"].append(second)
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.inspect(bundle)

    def test_payload_validation(self):
        for key, value in (("bytes", True), ("bytes", -1), ("bytes", 3),
                           ("bytes", export.MAX_BYTES + 1), ("sha256", "0" * 64),
                           ("base64", "!!!!"), ("base64", "Mgp="), ("base64", "Mgo=\n"),
                           ("base64", 1), ("base64", "あいうえ"), ("extra", "x")):
            bundle = copy.deepcopy(self.bundle)
            bundle["files"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.inspect(bundle)

    def test_empty_payload_and_multiple_members(self):
        self.bundle["files"].append({"path": "empty.txt", "bytes": 0,
                                    "sha256": export.digest(b""), "base64": ""})
        result = self.inspect()
        self.assertEqual(result["selected_count"], 2)
        self.assertEqual(result["selected_bytes"], 2)

    def test_byte_and_entry_budgets(self):
        self.inspect()
        with patch.object(export, "MAX_EXPORT_BYTES", 10), self.assertRaises(ValueError):
            export.inspect_export(self.source)
        with patch.object(export, "MAX_BYTES", 1), self.assertRaises(ValueError):
            export.inspect_export(self.source)
        with patch.object(export, "MAX_ENTRIES", 3), self.assertRaises(ValueError):
            export.inspect_export(self.source)

    def test_links_special_files_and_missing_nofollow(self):
        self.inspect()
        link = self.root / "link"
        link.symlink_to(self.source)
        with self.assertRaises(OSError):
            export.inspect_export(link)
        link.unlink()
        link.hardlink_to(self.source)
        with self.assertRaises(ValueError):
            export.inspect_export(self.source)
        link.unlink()
        with patch.object(export.os, "O_NOFOLLOW", 0), self.assertRaises(ValueError):
            export.inspect_export(self.source)
        os.mkfifo(self.root / "fifo")
        with self.assertRaises(ValueError):
            export.inspect_export(self.root / "fifo")

    def test_changed_file_rejected(self):
        self.inspect()
        original = export.os.read
        changed = False
        def read(fd, size):
            nonlocal changed
            chunk = original(fd, size)
            if not changed:
                changed = True
                self.source.write_bytes(b"{}")
            return chunk
        with patch.object(export.os, "read", side_effect=read), self.assertRaises(ValueError):
            export.inspect_export(self.source)


if __name__ == "__main__":
    unittest.main()
