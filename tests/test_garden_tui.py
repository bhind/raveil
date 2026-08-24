from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.garden import GardenBrowser, GardenSnapshot, render_error, render_key_session


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/garden/minimal.json"


class GardenTUITests(unittest.TestCase):
    def test_fixture_loads_through_owned_program_and_canonical_variants(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        self.assertEqual(snapshot.program.program_id, "gemm_bias_relu-8x8x8")
        self.assertEqual(len(snapshot.program.nodes), 3)
        self.assertEqual(len(snapshot.variants), 5)
        self.assertEqual(snapshot.variants[0].variant_id, "baseline-ijk")
        rendered = GardenBrowser(snapshot).render()
        self.assertIn("Raveil Garden | read-only graph browser", rendered)
        self.assertIn("authority: observe-only execute=no mutate=no approve=no promote=no", rendered)
        self.assertIn("> 1. matmul", rendered)
        self.assertIn("evidence: host-functional claim=development-non-claim", rendered)
        self.assertIn("Graph Navigator", rendered)
        self.assertIn("Node Inspector", rendered)
        self.assertIn("Variants / Evidence", rendered)
        self.assertIn("Commands / Status", rendered)

    def test_navigation_transcript_is_bounded_and_deterministic(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        first = render_key_session(snapshot, "jjq")
        second = render_key_session(snapshot, "jjq")
        self.assertEqual(first, second)
        self.assertIn("> 3. relu", first)
        self.assertTrue(first.endswith("Raveil Garden | closed"))
        with self.assertRaisesRegex(ValueError, "bounded step limit"):
            render_key_session(snapshot, "j" * 65)

    def test_cli_renders_one_noninteractive_screen(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO()), mock.patch("sys.stdout", output):
            exit_code = main(["garden", "--fixture", str(FIXTURE)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().count("Raveil Garden | read-only graph browser"), 1)
        self.assertIn("Navigation: j next", output.getvalue())

    def test_wide_layout_uses_three_panes_with_bounded_lines(self) -> None:
        rendered = GardenBrowser(GardenSnapshot.load(FIXTURE), width=150).render()
        first_pane_line = next(line for line in rendered.splitlines() if "Graph Navigator" in line)
        self.assertIn("Node Inspector", first_pane_line)
        self.assertIn("Variants / Evidence", first_pane_line)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 150)
        three_pane_borders = [
            line for line in rendered.splitlines()
            if line.startswith("+-") and line.count("+") == 6
        ]
        self.assertEqual(len(three_pane_borders), 1)

    def test_narrow_layout_stacks_all_panes(self) -> None:
        rendered = GardenBrowser(GardenSnapshot.load(FIXTURE), width=100).render()
        self.assertIn("[stacked layout]", rendered)
        self.assertIn("Graph Navigator", rendered)
        self.assertIn("Node Inspector", rendered)
        self.assertIn("Variants / Evidence", rendered)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 100)

    def test_width_boundaries_and_determinism(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        for width in (72, 119, 120, 240):
            rendered = GardenBrowser(snapshot, width).render()
            self.assertLessEqual(max(map(len, rendered.splitlines())), width)
            self.assertEqual(rendered, GardenBrowser(snapshot, width).render())
            self.assertEqual(render_key_session(snapshot, "jg", width), render_key_session(snapshot, "jg", width))
        for width in (71, 241):
            with self.assertRaisesRegex(ValueError, "width must be"):
                GardenBrowser(snapshot, width)

    def test_long_content_is_wrapped_printably(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        long_snapshot = snapshot.__class__(
            "X" * 256, snapshot.program, snapshot.variants, snapshot.evidence,
            ("python3 -m raveil " + "x" * 300,),
        )
        rendered = GardenBrowser(long_snapshot, 72).render()
        self.assertTrue(all(line.isprintable() for line in rendered.splitlines()))
        self.assertNotIn("\x1b", rendered)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 72)

    def test_cli_width_is_applied_and_invalid_width_fails_closed(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO()), mock.patch("sys.stdout", output):
            self.assertEqual(main(["garden", "--fixture", str(FIXTURE), "--width", "100"]), 0)
        self.assertIn("[stacked layout]", output.getvalue())
        for width in ("71", "241"):
            error = io.StringIO()
            with mock.patch("sys.stderr", error):
                self.assertEqual(main(["garden", "--fixture", str(FIXTURE), "--width", width]), 2)
            self.assertIn("garden width must be", error.getvalue())

    def test_cli_exposes_explicit_empty_state(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            self.assertEqual(main(["garden", "--empty"]), 0)
        self.assertEqual(
            output.getvalue(),
            "Raveil Garden | empty\n"
            "No validated graph snapshot is loaded.\n"
            "authority: observe-only execute=no mutate=no approve=no promote=no\n",
        )

    def test_cli_reports_fail_closed_error_state(self) -> None:
        malformed = json.loads(FIXTURE.read_text(encoding="utf-8"))
        malformed["unknown"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malformed.json"
            path.write_text(json.dumps(malformed), encoding="utf-8")
            error = io.StringIO()
            with mock.patch("sys.stderr", error):
                self.assertEqual(main(["garden", "--fixture", str(path)]), 2)
        self.assertIn("Raveil Garden | error", error.getvalue())
        self.assertIn("No graph state was accepted", error.getvalue())

    def test_noncanonical_variant_and_promoted_claim_are_rejected(self) -> None:
        for mutation, message in (
            (lambda value: value["variants"].reverse(), "canonical compiler slate"),
            (lambda value: value["evidence"].update({"claim_status": "measured"}),
             "development-non-claim"),
        ):
            malformed = json.loads(FIXTURE.read_text(encoding="utf-8"))
            mutation(malformed)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "malformed.json"
                path.write_text(json.dumps(malformed), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    GardenSnapshot.load(path)

    def test_malformed_program_and_variant_types_are_rejected_cleanly(self) -> None:
        for mutation, message in (
            (lambda value: value["program"].update({"m": "8"}), "m must be an integer"),
            (lambda value: value["program"].update({"family": []}), "family must be"),
            (lambda value: value.update({"variants": ["not-an-object"]}), "contain objects"),
        ):
            malformed = json.loads(FIXTURE.read_text(encoding="utf-8"))
            mutation(malformed)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "malformed.json"
                path.write_text(json.dumps(malformed), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    GardenSnapshot.load(path)

    def test_terminal_control_characters_are_rejected(self) -> None:
        for field, value in (
            ("title", "trusted\x1b[2Jforged"),
            ("demo_commands", ["python3 -m raveil garden\x07"]),
            ("program_id", "graph\u202epng"),
        ):
            malformed = json.loads(FIXTURE.read_text(encoding="utf-8"))
            if field == "program_id":
                malformed["program"][field] = value
            else:
                malformed[field] = value
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "malformed.json"
                path.write_text(json.dumps(malformed), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "printable single-line"):
                    GardenSnapshot.load(path)

    def test_duplicate_json_fields_are_rejected(self) -> None:
        source = FIXTURE.read_text(encoding="utf-8")
        duplicates = (
            source.replace('"title": ', '"title": "forged", "title": ', 1),
            source.replace('"family": ', '"family": "gemm", "family": ', 1),
        )
        for duplicate in duplicates:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "duplicate.json"
                path.write_text(duplicate, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "duplicate field"):
                    GardenSnapshot.load(path)

    def test_error_rendering_removes_terminal_controls(self) -> None:
        rendered = render_error("bad\x1b[2J\x07\u202evalue")
        self.assertNotIn("\x1b", rendered)
        self.assertNotIn("\x07", rendered)
        self.assertNotIn("\u202e", rendered)
        self.assertIn("bad [2J value", rendered)

    def test_garden_module_has_no_execution_backend(self) -> None:
        source = (ROOT / "raveil/garden.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("NativeCBackend", source)
        self.assertNotIn("SonatineQEMUBackend", source)
        self.assertNotIn("GraphExecutor", source)


if __name__ == "__main__":
    unittest.main()
