from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

from raveil.project import Project


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "project-workloads"


class ProjectWorkloadExampleTests(unittest.TestCase):
    def fixture(self, name: str) -> tuple[Path, Project]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / name
        shutil.copytree(FIXTURES / name, root)
        (root / "runs").mkdir()
        return root, Project(root)

    def test_log_summary_matches_manual_expected_output_and_retains_edits(self) -> None:
        root, project = self.fixture("log-summary")
        first = project.run("log-summary", "native", kernel=Path("missing"),
                            qemu="missing", compiler="cc")
        self.assertEqual(first["status"], "succeeded")
        expected = (root / "expected" / "errors.txt").read_bytes()
        first_output = root / "runs" / first["run_id"] / "workspace" / "errors.txt"
        self.assertEqual(first_output.read_bytes(), expected)

        with (root / "inputs" / "events.log").open("a", encoding="utf-8") as stream:
            stream.write("ERROR capacity\n")
        second = project.run("log-summary", "native", kernel=Path("missing"),
                             qemu="missing", compiler="cc")
        self.assertEqual(second["status"], "succeeded")
        self.assertEqual(first_output.read_bytes(), expected)
        self.assertEqual(project.load_run(first["run_id"]), first)
        difference = project.diff(first["run_id"], second["run_id"])
        self.assertIn("/events.log", difference)
        self.assertIn("/errors.txt", difference)

    def test_duplicate_inventory_matches_manual_expected_output(self) -> None:
        root, project = self.fixture("duplicate-inventory")
        record = project.run("duplicate-inventory", "native", kernel=Path("missing"),
                             qemu="missing", compiler="cc")
        self.assertEqual(record["status"], "succeeded")
        output = root / "runs" / record["run_id"] / "workspace" / "unique.txt"
        self.assertEqual(output.read_bytes(), (root / "expected" / "unique.txt").read_bytes())

    def test_missing_input_is_retained_as_failure_without_published_output(self) -> None:
        root, project = self.fixture("log-summary")
        record = project.run("missing-input", "native", kernel=Path("missing"),
                             qemu="missing", compiler="cc")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["outputs"], {})
        self.assertFalse((root / "runs" / record["run_id"] / "workspace" /
                          "missing-copy.txt").exists())
        self.assertIn("missing-input native failed", project.runs())


if __name__ == "__main__":
    unittest.main()
