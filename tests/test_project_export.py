import base64
import contextlib
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


if __name__ == "__main__":
    unittest.main()
