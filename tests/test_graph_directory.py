from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.graph_directory import materialize


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/graph_directory"


class GraphDirectoryTests(unittest.TestCase):
    def test_materializes_deterministic_ordinal_only_tree(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = materialize(FIXTURES / "program.json", FIXTURES / "result.json", Path(first))
            two = materialize(FIXTURES / "program.json", FIXTURES / "result.json", Path(second))
            self.assertEqual(one, two)
            first_files = sorted(path.relative_to(first) for path in Path(first).rglob("*") if path.is_file())
            second_files = sorted(path.relative_to(second) for path in Path(second).rglob("*") if path.is_file())
            self.assertEqual(first_files, second_files)
            self.assertEqual(
                [str(path) for path in first_files],
                [
                    "contract.json", "manifest.json", "memory-plans/000.json", "memory-plans/001.json",
                    "memory-plans/002.json", "memory-plans/003.json", "memory-plans/004.json", "nodes/000.json",
                    "nodes/001.json", "nodes/002.json", "program.json", "proposal.json", "result.json",
                    "selection.txt", "tree.txt", "variants/000.json", "variants/001.json", "variants/002.json",
                    "variants/003.json", "variants/004.json",
                ],
            )
            for relative in first_files:
                self.assertEqual((Path(first) / relative).read_bytes(), (Path(second) / relative).read_bytes())
            manifest = json.loads((Path(first) / "manifest.json").read_text())
            self.assertEqual(manifest["authority"], "observe-only")
            self.assertEqual(manifest["files_sha256"]["program.json"], hashlib.sha256((Path(first) / "program.json").read_bytes()).hexdigest())
            self.assertIn("manifest.json", (Path(first) / "tree.txt").read_text().splitlines())

    def test_rejects_duplicate_unknown_and_stale_input_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = root / "program.json"
            program.write_text('{"schema":"raveil.graph-program/v1","schema":"raveil.graph-program/v1"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON field"):
                materialize(program, FIXTURES / "result.json", root / "empty")
            target = root / "target"; target.mkdir()
            stale = json.loads((FIXTURES / "result.json").read_text())
            stale["program_sha256"] = "0" * 64
            result = root / "result.json"; result.write_text(json.dumps(stale))
            with self.assertRaisesRegex(ValueError, "lineage"):
                materialize(FIXTURES / "program.json", result, target)
            self.assertEqual(list(target.iterdir()), [])

    def test_rejects_inconsistent_result_and_claims_before_publish(self) -> None:
        mutations = (
            ("selection", lambda result: result.update(selected_variant="baseline-ijk")),
            ("observations", lambda result: result["observations"].append(result["observations"][0])),
            ("schema or lineage", lambda result: result.update(claim_status="measured-hardware")),
            (
                "candidate fields",
                lambda result: result["variants"][1]["candidate"].update(
                    cold_priority=True
                ),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target = root / "target"
                target.mkdir()
                result = json.loads((FIXTURES / "result.json").read_text())
                mutate(result)
                result_path = root / "result.json"
                result_path.write_text(json.dumps(result))
                with self.assertRaisesRegex(ValueError, label):
                    materialize(FIXTURES / "program.json", result_path, target)
                self.assertEqual(list(target.iterdir()), [])

    def test_refuses_nonempty_or_symlink_output_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            occupied = root / "occupied"; occupied.mkdir(); (occupied / "keep").write_text("keep")
            with self.assertRaisesRegex(ValueError, "must be empty"):
                materialize(FIXTURES / "program.json", FIXTURES / "result.json", occupied)
            link = root / "link"; link.symlink_to(occupied, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "non-symlink"):
                materialize(FIXTURES / "program.json", FIXTURES / "result.json", link)

    def test_cli_reports_publication_digest_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            captured = []
            with mock.patch("sys.stdout", new_callable=__import__("io").StringIO) as stdout:
                self.assertEqual(main(["graph-directory", "--program", str(FIXTURES / "program.json"), "--result", str(FIXTURES / "result.json"), "--output", str(output)]), 0)
                captured.append(stdout.getvalue())
            with mock.patch("sys.stderr", new_callable=__import__("io").StringIO) as stderr:
                self.assertEqual(main(["graph-directory", "--program", str(FIXTURES / "program.json"), "--result", str(FIXTURES / "result.json"), "--output", str(output)]), 2)
                self.assertIn("refusing overwrite", stderr.getvalue())
            self.assertIn("manifest_sha256=", captured[0])


if __name__ == "__main__":
    unittest.main()
