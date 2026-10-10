"""Host fault injection only; actual RTL acceptance uses the separate demo."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from raveil import project_composition as c
from raveil.project import Project, init_project, encoded, digest
from raveil.cli import main
from tests.test_project_graph import host_fixture_runner


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = init_project(Path(self.temp.name) / "project")
        self.project = Project(self.root)
        self.outputs = [("raw", "bias-grid"), ("biased", "bias-grid")]

    def run_pair(self, runner=host_fixture_runner, **kw):
        with patch("raveil.project_graph.run_snapshot", side_effect=runner):
            return c.compose(self.project, "bias-grid-data.json", self.outputs, **kw)

    def test_complete_and_read_without_execution(self):
        record = self.run_pair()
        self.assertEqual(record["status"], "succeeded")
        self.assertEqual(len(record["children"]), 2)
        self.assertEqual(record["children"][0]["input_sha256"], record["children"][1]["input_sha256"])
        with patch("raveil.project_graph.run_snapshot", side_effect=AssertionError("no rerun")):
            text = c.inspect(self.project, record["composition_id"])
        self.assertIn("output=raw", text)
        self.assertIn("output=biased", text)
        self.assertIn("succeeded children=2", c.history(self.project))
        self.assertNotIn(record["composition_id"], self.project.runs())

    def test_bad_names_count_recipe_and_input_fail_before_execution(self):
        for outputs in ([], [("a", "bias-grid")] * 3, [("a", "bias-grid")] * 2,
                        [("../x", "bias-grid")], [("é", "bias-grid")], [("a\n", "bias-grid")],
                        [("A", "bias-grid")], [("a" * 32, "bias-grid")], [("x", "logs")]):
            with self.subTest(outputs=outputs), patch("raveil.project_graph.run_snapshot") as runner:
                with self.assertRaises(ValueError):
                    c.compose(self.project, "bias-grid-data.json", outputs)
                runner.assert_not_called()
        self.assertFalse((self.root / "compositions").exists())
        for value in ("../project.json", "a/b.json", "bias-grid-data", ""):
            with self.assertRaises(ValueError):
                c.compose(self.project, value, self.outputs)

    def test_one_output_and_field_like_names(self):
        self.outputs = [("schema", "bias-grid")]
        self.assertEqual(self.run_pair()["status"], "succeeded")
        self.outputs = [("outputs", "bias-grid"), ("schema", "bias-grid")]
        self.assertEqual(self.run_pair()["status"], "succeeded")

    def test_live_edits_cannot_change_frozen_children(self):
        seen = []
        def runner(descriptor, seed, **kw):
            seen.append((descriptor, kw["input_bytes"]))
            (self.root / "inputs/bias-grid.json").write_text("broken live descriptor")
            (self.root / "inputs/bias-grid-data.json").write_text("broken live data")
            (self.root / "recipes/bias-grid.json").write_text("broken live recipe")
            return host_fixture_runner(descriptor, seed, **kw)
        record = self.run_pair(runner)
        self.assertEqual(record["status"], "succeeded")
        self.assertEqual(seen[0], seen[1])
        c.load(self.project, record["composition_id"])

    def test_second_failure_retains_first_without_parent_success_and_retry_is_new(self):
        calls = 0
        def runner(*args, **kw):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise ValueError("injected failure")
            return host_fixture_runner(*args, **kw)
        failed = self.run_pair(runner)
        self.assertEqual(failed["status"], "incomplete")
        self.assertEqual(len(failed["children"]), 1)
        self.assertIn("No complete result set", c.inspect(self.project, failed["composition_id"]))
        first = self.root / "compositions" / failed["composition_id"] / "children/0"
        self.assertEqual(Project(first).load_run(failed["children"][0]["run_id"])["status"], "succeeded")
        retried = self.run_pair()
        self.assertNotEqual(failed["composition_id"], retried["composition_id"])
        self.assertEqual(retried["status"], "succeeded")

    def test_cancellation_each_boundary_including_seal(self):
        for stop in range(1, 6):
            calls = 0
            def cancelled():
                nonlocal calls
                calls += 1
                return calls == stop
            record = self.run_pair(cancelled=cancelled)
            self.assertEqual(record["status"], "incomplete", stop)
            root = self.root / "compositions" / record["composition_id"]
            if stop == 5:
                self.assertFalse((root / "record.json").exists())
                self.assertIn("incomplete/unverified", c.history(self.project))
            else:
                self.assertEqual(c.load(self.project, record["composition_id"])[0]["status"], "incomplete")

    def test_keyboard_interrupt_during_second_child(self):
        calls = 0
        def runner(*args, **kw):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return host_fixture_runner(*args, **kw)
        record = self.run_pair(runner)
        self.assertEqual(record["status"], "incomplete")
        self.assertEqual(len(record["children"]), 1)
        c.load(self.project, record["composition_id"])

    def test_saved_input_child_output_plan_record_tamper_rejected(self):
        for relative in ("input.json", "descriptor-0.json", "plan.json", "record.json"):
            record = self.run_pair()
            path = self.root / "compositions" / record["composition_id"] / relative
            path.write_text("{}")
            with self.assertRaises((ValueError, KeyError)):
                c.inspect(self.project, record["composition_id"])
        record = self.run_pair()
        path = self.root / "compositions" / record["composition_id"] / "children/0/runs" / record["children"][0]["run_id"] / "workspace/output.bin"
        path.write_bytes(b"bad")
        with self.assertRaises(ValueError):
            c.inspect(self.project, record["composition_id"])

    def test_plan_mutation_or_build_drift_blocks_success(self):
        for mutation in ("plan", "build"):
            calls = 0
            def runner(*args, **kw):
                nonlocal calls
                calls += 1
                result = host_fixture_runner(*args, **kw)
                if calls == 2:
                    if mutation == "build":
                        result["receipt"]["simulator_sha256"] = "d" * 64
                    else:
                        root = sorted((self.root / "compositions").iterdir())[-1]
                        plan = json.loads((root / "plan.json").read_text())
                        plan["input_file"] = "changed.json"
                        (root / "plan.json").write_bytes(encoded(plan))
                return result
            self.assertEqual(self.run_pair(runner)["status"], "incomplete")

    def test_symlink_saved_child_and_parent_rejected(self):
        record = self.run_pair()
        root = self.root / "compositions" / record["composition_id"]
        path = root / "input.json"
        path.unlink(); path.symlink_to(self.root / "inputs/bias-grid-data.json")
        with self.assertRaises(ValueError):
            c.load(self.project, record["composition_id"])
        other = Path(self.temp.name) / "other"; other.mkdir()
        root2 = init_project(Path(self.temp.name) / "second")
        (root2 / "compositions").symlink_to(other, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.compose(Project(root2), "bias-grid-data.json", self.outputs)
        self.assertEqual(list(other.iterdir()), [])

    def test_false_child_output_never_publishes_parent(self):
        def runner(*args, **kw):
            result = host_fixture_runner(*args, **kw)
            result["output"] = b"\x00" * 1024
            result["receipt"]["output_sha256"] = digest(result["output"])
            return result
        record = self.run_pair(runner)
        self.assertEqual(record["status"], "incomplete")
        self.assertEqual(record["children"], [])
        self.assertIn("oracle", record["error"])

    def test_atomic_publication_failure_and_checksum_tamper(self):
        with patch("raveil.project_composition.os.link", side_effect=OSError("injected link failure")):
            with self.assertRaises(OSError):
                self.run_pair()
        root = next((self.root / "compositions").iterdir())
        self.assertFalse((root / "record.json").exists())
        self.assertIn("incomplete/unverified", c.history(self.project))
        record = self.run_pair()
        root = self.root / "compositions" / record["composition_id"]
        (root / "record.sha256").write_text("0" * 64)
        with self.assertRaisesRegex(ValueError, "checksum"):
            c.load(self.project, record["composition_id"])

    def test_snapshot_budget_rejects_before_children(self):
        with patch("raveil.project_composition.p.MAX_BYTES", 10000), patch("raveil.project_graph.run_snapshot") as runner:
            # Individual reads fit; the combined duplicated capture budget does not.
            with self.assertRaisesRegex(ValueError, "byte budget"):
                c.compose(self.project, "bias-grid-data.json", self.outputs)
            runner.assert_not_called()
        self.assertFalse((self.root / "compositions").exists())

    def test_malformed_sealed_record_is_rejected_without_traceback(self):
        record = self.run_pair()
        root = self.root / "compositions" / record["composition_id"]
        for field, value in (("children", [None, {}]), ("children", [[], 1]),
                             ("children", [{"run_id": 1}, {}]), ("status", [])):
            changed = dict(record, **{field: value})
            payload = encoded(changed)
            (root / "record.json").write_bytes(payload)
            (root / "record.sha256").write_text(digest(payload) + "\n")
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    c.load(self.project, record["composition_id"])
                self.assertIn("incomplete/unverified", c.history(self.project))

    def test_malformed_child_result_is_rejected(self):
        record = self.run_pair()
        root = self.root / "compositions" / record["composition_id"]
        child_path = root / "children/0/runs" / record["children"][0]["run_id"]
        child = json.loads((child_path / "record.json").read_text())
        for result in (None, "invalid", {}, {"receipt": []}):
            changed = dict(child, result=result)
            payload = encoded(changed)
            (child_path / "record.json").write_bytes(payload)
            (child_path / "record.sha256").write_text(digest(payload) + "\n")
            parent = dict(record, artifacts=c._manifest(root))
            payload = encoded(parent)
            (root / "record.json").write_bytes(payload)
            (root / "record.sha256").write_text(digest(payload) + "\n")
            with self.subTest(result=result), self.assertRaisesRegex(ValueError, "child result"):
                c.load(self.project, record["composition_id"])

    def test_cli_compose_inspect_and_history(self):
        out = io.StringIO()
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner), contextlib.redirect_stdout(out):
            self.assertEqual(main(["project", "compose", "--project", str(self.root), "--input", "bias-grid-data.json", "--output", "raw=bias-grid", "--output", "biased=bias-grid"]), 0)
        identity = out.getvalue().split("composition=", 1)[1].split()[0]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["project", "composition", identity, "--project", str(self.root)]), 0)
            self.assertEqual(main(["project", "compositions", "--project", str(self.root)]), 0)


if __name__ == "__main__":
    unittest.main()
