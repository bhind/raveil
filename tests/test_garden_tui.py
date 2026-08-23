from __future__ import annotations

import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.garden import GardenBrowser, GardenSnapshot, render_key_session


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
        self.assertIn("python3 -m raveil garden --fixture", rendered)

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

    def test_garden_module_has_no_execution_backend(self) -> None:
        source = (ROOT / "raveil/garden.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("NativeCBackend", source)
        self.assertNotIn("SonatineQEMUBackend", source)
        self.assertNotIn("GraphExecutor", source)


if __name__ == "__main__":
    unittest.main()
