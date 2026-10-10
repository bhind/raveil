"""Host fault injection/staging tests; actual RTL evidence is the separate demo."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from raveil import project_tiling as t
from raveil.cli import main
from raveil.project import Project, init_project, encoded, digest, tree
from tests.test_project_graph import host_fixture_runner


class TilingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = init_project(Path(self.temp.name) / "project")
        self.project = Project(self.root)
        self.words = [row * 32 + col + 1 for row in range(32) for col in range(32)]
        self.save(self.words)

    def save(self, words):
        (self.root / "inputs/grid.json").write_bytes(encoded({"schema": t.INPUT, "rows": 32, "columns": 32, "words": words}))

    def run_grid(self, runner=host_fixture_runner, **kwargs):
        with patch("raveil.project_graph.run_snapshot", side_effect=runner):
            return t.run(self.project, "grid.json", **kwargs)

    def parent(self, record):
        return self.root / "tilings" / record["tiling_id"]

    def test_halos_use_global_neighbors_and_zero_only_outside_grid(self):
        for slot, (row, col) in enumerate(t.ORIGINS):
            data = t.tile_words(self.words, slot)
            self.assertEqual(len(data), 324)
            for lr in range(18):
                for lc in range(18):
                    r, c = row + lr - 1, col + lc - 1
                    expected = self.words[r * 32 + c] if 0 <= r < 32 and 0 <= c < 32 else 0
                    self.assertEqual(data[lr * 18 + lc], expected)
        # Right halo of tile0 must be original column16, not zero.
        self.assertEqual(t.tile_words(self.words, 0)[18 + 17], self.words[16])
        self.assertEqual(t.tile_words(self.words, 1)[18], self.words[15])

    def test_seam_corner_impulses_and_uint32_wrap(self):
        words = [0] * 1024
        expected = [0] * 1024
        for row, col, value in ((0, 0, 1), (31, 31, 2), (15, 15, 0xffffffff),
                                 (15, 16, 17), (16, 15, 31), (16, 16, 0x80000000)):
            words[row * 32 + col] = value
            for r, c in ((row, col), (row-1, col), (row+1, col), (row, col-1), (row, col+1)):
                if 0 <= r < 32 and 0 <= c < 32:
                    expected[r * 32 + c] = (expected[r * 32 + c] + value) & 0xffffffff
        self.save(words)
        result = self.run_grid()
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["output"]["words"], expected)

    def test_complete_inspection_and_history_never_reexecute(self):
        result = self.run_grid()
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(len(result["children"]), 4)
        self.assertEqual(len({c["input_sha256"] for c in result["children"]}), 4)
        with patch("raveil.project_graph.run_snapshot", side_effect=AssertionError("must not run")):
            loaded = t.load(self.project, result["tiling_id"])
            shown = t.inspect(self.project, result["tiling_id"])
            self.assertEqual(loaded, result)
            self.assertIn("output=32x32", shown)
            self.assertIn("succeeded tiles=4", t.history(self.project))
        self.assertNotIn(result["tiling_id"], self.project.runs())
        self.assertFalse((self.parent(result) / "output.bin").exists())

    def test_input_schema_types_bounds_and_paths_fail_before_execution(self):
        valid = json.loads((self.root / "inputs/grid.json").read_text())
        changes = [{"rows": 16}, {"columns": True}, {"schema": "unknown"},
                   {"words": [0] * 1023}, {"words": [False] * 1024},
                   {"words": [-1] * 1024}, {"words": [1 << 32] * 1024}, {"extra": 0}]
        for change in changes:
            with self.subTest(change=list(change)):
                (self.root / "inputs/grid.json").write_bytes(encoded({**valid, **change}))
                with patch("raveil.project_graph.run_snapshot") as runner:
                    with self.assertRaises(ValueError):
                        t.run(self.project, "grid.json")
                    runner.assert_not_called()
        self.assertFalse((self.root / "tilings").exists())
        for filename in ("../grid.json", "grid", "a/b.json", "a\\b.json", None):
            with self.assertRaises(ValueError):
                t.run(self.project, filename)
        with self.assertRaises(ValueError): t.input_words(b" " * (65537))
        with self.assertRaises(ValueError): t.input_words(b'{"schema":1,"schema":2}')

    def test_live_input_edit_does_not_change_frozen_run(self):
        def runner(*args, **kwargs):
            (self.root / "inputs/grid.json").write_text("changed live source")
            return host_fixture_runner(*args, **kwargs)
        result = self.run_grid(runner)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["output"]["words"], t.global_reference(self.words))
        t.load(self.project, result["tiling_id"])

    def test_failed_tile_has_no_assembled_output_and_retry_is_fresh(self):
        calls = 0
        def runner(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3: raise ValueError("injected third tile failure")
            return host_fixture_runner(*args, **kwargs)
        failed = self.run_grid(runner)
        self.assertEqual(failed["status"], "incomplete")
        self.assertEqual(len(failed["children"]), 2)
        self.assertIsNone(failed["output"])
        self.assertIn("No complete grid", t.inspect(self.project, failed["tiling_id"]))
        old = tree(self.parent(failed))
        retry = self.run_grid()
        self.assertNotEqual(retry["tiling_id"], failed["tiling_id"])
        self.assertEqual(retry["status"], "succeeded")
        self.assertEqual(tree(self.parent(failed)), old)

    def test_cancel_every_boundary_including_atomic_seal(self):
        for stop in range(1, 8):
            calls = 0
            def cancelled():
                nonlocal calls
                calls += 1
                return calls == stop
            result = self.run_grid(cancelled=cancelled)
            self.assertEqual(result["status"], "incomplete", stop)
            self.assertIsNone(result["output"])
            if stop == 7:
                self.assertFalse((self.parent(result) / "record.json").exists())
                self.assertIn("incomplete/unverified", t.history(self.project))
            else:
                self.assertIsNone(t.load(self.project, result["tiling_id"])["output"])

    def test_interrupt_during_child_retains_private_evidence(self):
        calls = 0
        def runner(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2: raise KeyboardInterrupt()
            return host_fixture_runner(*args, **kwargs)
        result = self.run_grid(runner)
        self.assertEqual(len(result["children"]), 1)
        self.assertIsNone(t.load(self.project, result["tiling_id"])["output"])

    def test_build_drift_blocks_complete_grid(self):
        calls = 0
        def runner(*args, **kwargs):
            nonlocal calls
            calls += 1
            result = host_fixture_runner(*args, **kwargs)
            if calls == 4: result["receipt"]["simulator_sha256"] = "f" * 64
            return result
        result = self.run_grid(runner)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("different RTL builds", result["error"])
        self.assertIsNone(t.load(self.project, result["tiling_id"])["output"])

    def test_tampered_snapshots_halos_descriptor_and_records_rejected(self):
        for filename in ("input.json", "input-0.json", "descriptor.json", "plan.json", "record.json"):
            result = self.run_grid()
            (self.parent(result) / filename).write_text("{}")
            with self.assertRaises((ValueError, KeyError)):
                t.load(self.project, result["tiling_id"])
        result = self.run_grid()
        entry = result["children"][0]
        (self.parent(result) / "children/0/runs" / entry["run_id"] / "workspace/output.bin").write_bytes(b"bad")
        with self.assertRaises(ValueError): t.load(self.project, result["tiling_id"])

    def test_forged_resealed_output_and_partial_success_are_rejected(self):
        result = self.run_grid()
        root = self.parent(result)
        for change in ("word", "bool", "shape", "hash", "partial", "incomplete"):
            forged = json.loads(json.dumps(result))
            if change == "word": forged["output"]["words"][0] ^= 1
            if change == "bool": forged["output"]["words"][0] = True
            if change == "shape": forged["output"]["words"].pop()
            if change == "hash": forged["output"]["sha256"] = "0" * 64
            if change == "partial": forged["children"].pop()
            if change == "incomplete": forged.update(status="incomplete", error="cause")
            raw = encoded(forged)
            (root / "record.json").write_bytes(raw)
            (root / "record.sha256").write_text(digest(raw) + "\n")
            with self.subTest(change=change), self.assertRaises(ValueError):
                t.load(self.project, result["tiling_id"])

    def test_symlink_input_and_parent_rejected(self):
        source = self.root / "inputs/grid.json"
        data = source.read_bytes(); source.unlink()
        other = Path(self.temp.name) / "data.json"; other.write_bytes(data)
        source.symlink_to(other)
        with self.assertRaises(ValueError): self.run_grid()
        source.unlink(); source.write_bytes(data)
        (self.root / "tilings").symlink_to(self.root / "runs", target_is_directory=True)
        with self.assertRaises(ValueError): self.run_grid()

    def test_publish_failure_cannot_return_or_expose_success(self):
        original_link = t.os.link
        def fail(src, dst, *args, **kwargs):
            if Path(dst).parent.parent.name == "tilings":
                raise OSError("publication failed")
            return original_link(src, dst, *args, **kwargs)
        with patch.object(t.os, "link", side_effect=fail), self.assertRaises(OSError):
            self.run_grid()
        self.assertIn("incomplete/unverified", t.history(self.project))

    def test_cli_run_inspect_history_and_failure_status(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["project", "tile-run", "--project", str(self.root), "--input", "grid.json"]), 0)
        identity = out.getvalue().split("tiling=", 1)[1].split()[0]
        with patch("raveil.project_graph.run_snapshot", side_effect=AssertionError("no rerun")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["project", "tile", identity, "--project", str(self.root)]), 0)
            self.assertEqual(main(["project", "tiles", "--project", str(self.root)]), 0)
        with patch("raveil.project_graph.run_snapshot", side_effect=ValueError("failure")), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["project", "tile-run", "--project", str(self.root), "--input", "grid.json"]), 2)


if __name__ == "__main__":
    unittest.main()
