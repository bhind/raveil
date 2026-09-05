from __future__ import annotations

from dataclasses import replace
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.garden import (
    GardenBrowser,
    GardenDynamicBrowser,
    GardenDynamicExplanation,
    GardenSnapshot,
    _materialized_fused_plan_pair,
    render_error,
    render_key_session,
    run_interactive,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/garden/minimal.json"
DYNAMIC_FIXTURE = ROOT / "tests/fixtures/garden/dynamic-explanation.json"


class GardenTUITests(unittest.TestCase):
    def _details(self, snapshot, width=150):
        browser = GardenBrowser(snapshot, width)
        browser.navigate("d")
        return browser

    def _dynamic_document(self) -> dict[str, object]:
        return json.loads(DYNAMIC_FIXTURE.read_text(encoding="ascii"))

    def _write_dynamic(self, value: object) -> tuple[str, Path]:
        descriptor, name = tempfile.mkstemp(
            prefix="dynamic-explanation-test-", suffix=".json", dir=DYNAMIC_FIXTURE.parent,
        )
        os.close(descriptor)
        path = Path(name)
        path.write_text(json.dumps(value), encoding="ascii")
        return path.relative_to(ROOT).as_posix(), path

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
        self.assertIn("Materialized:", rendered)
        self.assertIn("Fused:", rendered)
        rendered = self._details(snapshot).render()
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

    def test_compact_fusion_screen_marks_selected_stage_and_removed_io(self) -> None:
        browser = GardenBrowser(GardenSnapshot.load(FIXTURE), 150)
        initial = browser.render()
        self.assertLessEqual(len(initial.splitlines()), 24)
        header = next(line for line in initial.splitlines() if "Materialized:" in line)
        self.assertIn("Fused:", header)
        self.assertIn("WRITE intermediate [512B]", initial)
        self.assertIn("intermediate WRITE removed", initial)
        self.assertIn("intermediate READ removed", initial)
        self.assertIn("Intermediate plan memory: 512B -> 0B; not total Graph memory.", initial)
        browser.navigate("j")
        bias = browser.render()
        self.assertIn("> bias_add", bias)
        self.assertIn("> bias_add + relu", bias)
        self.assertIn("its intermediate WRITE disappears", bias)
        browser.navigate("j")
        relu = browser.render()
        self.assertIn("> relu", relu)
        self.assertIn("> bias_add + relu", relu)
        self.assertIn("its intermediate READ disappears", relu)
        browser.navigate("d")
        self.assertIn("program sha256=", browser.render())
        browser.navigate("d")
        self.assertEqual(browser.render(), relu)

    def test_interactive_redraw_requires_both_streams_to_be_ttys(self) -> None:
        class Tty(io.StringIO):
            def isatty(self):
                return True
        snapshot = GardenSnapshot.load(FIXTURE)
        output = Tty()
        self.assertEqual(run_interactive(snapshot, Tty("j\nj\nq\n"), output), 0)
        frames = output.getvalue().split("\x1b[H\x1b[2J")
        self.assertEqual(len(frames), 4)
        self.assertIn("Selected matmul:", frames[1])
        self.assertIn("Selected bias:", frames[2])
        self.assertIn("Selected relu:", frames[3])
        self.assertTrue(output.getvalue().endswith("Raveil Garden | closed\n"))
        for input_stream in (Tty("j\nq\n"), io.StringIO("j\nq\n")):
            plain_output = io.StringIO()
            self.assertEqual(run_interactive(snapshot, input_stream, plain_output), 0)
            self.assertNotIn("\x1b", plain_output.getvalue())

    def test_validated_fusion_comparison_is_data_bound_and_non_claiming(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        pair = _materialized_fused_plan_pair(snapshot.variants)
        self.assertIsNotNone(pair)
        materialized, fused = pair
        self.assertEqual(
            (materialized.variant_id, fused.variant_id),
            ("loop-ikj", "loop-ikj-fused"),
        )
        self.assertEqual(materialized.program_sha256, fused.program_sha256)
        self.assertEqual(materialized.contract_sha256, fused.contract_sha256)
        self.assertEqual(materialized.memory_plan.maximum_intermediate_bytes, 512)
        self.assertEqual(fused.memory_plan.maximum_intermediate_bytes, 0)
        for width in (72, 100, 150, 240):
            rendered = self._details(snapshot, width).render()
            normalized = " ".join(rendered.replace("|", "").split())
            compact = "".join(rendered.replace("|", "").split())
            self.assertIn(
                "Matched plan pair: loop-ikj vs loop-ikj-fused "
                "(deterministic comparison; not a measured best-plan selection)",
                normalized,
            )
            self.assertIn(
                "semanticgraph:unchanged;programsha256=" + materialized.program_sha256,
                compact,
            )
            self.assertIn(
                "resultcontract:unchanged;contractsha256=" + materialized.contract_sha256,
                compact,
            )
            self.assertIn(
                "materialized [loop-ikj]: matmul -> bias_add -> "
                "intermediate[512B] -> relu -> output",
                normalized,
            )
            self.assertIn(
                "fused [loop-ikj-fused]: matmul -> bias_add + relu -> output; "
                "intermediate[0B]",
                normalized,
            )
            self.assertIn(
                "scope: intermediate buffer only; not total Graph memory (512B vs 0B)",
                normalized,
            )
            self.assertLess(
                rendered.index("Matched plan pair:"),
                rendered.index("baseline-ijk baseline;"),
            )
            self.assertNotIn("speedup", rendered)
            self.assertNotIn("latency", rendered)
            self.assertNotIn("energy", rendered)

    def test_fusion_comparison_is_omitted_without_a_validated_pair(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        without_fused = tuple(
            variant for variant in snapshot.variants
            if variant.memory_plan.materialization != "fused"
        )
        no_pair_snapshot = snapshot.__class__(
            snapshot.title, snapshot.program, without_fused, snapshot.evidence,
            snapshot.demo_commands,
        )
        self.assertIsNone(_materialized_fused_plan_pair(without_fused))
        self.assertNotIn("Matched plan pair:", GardenBrowser(no_pair_snapshot).render())

    def test_fusion_comparison_rejects_near_match_lineage_and_schedule(self) -> None:
        snapshot = GardenSnapshot.load(FIXTURE)
        materialized = next(
            variant for variant in snapshot.variants if variant.variant_id == "loop-ikj"
        )
        fused = next(
            variant for variant in snapshot.variants if variant.variant_id == "loop-ikj-fused"
        )
        near_matches = (
            replace(fused, program_sha256="0" * 64),
            replace(fused, contract_sha256="0" * 64),
            replace(fused, candidate=replace(fused.candidate, loop_order="ijk")),
            replace(fused, transforms=("loop-tiling:32", "fuse:bias_add+relu")),
        )
        for near_match in near_matches:
            with self.subTest(near_match=near_match):
                self.assertIsNone(_materialized_fused_plan_pair((materialized, near_match)))

        tiled_materialized = next(
            variant for variant in snapshot.variants if variant.variant_id == "tile32"
        )
        tiled_fused = next(
            variant for variant in snapshot.variants if variant.variant_id == "tile32-fused"
        )
        wrong_tile = replace(tiled_fused, candidate=replace(tiled_fused.candidate, tile=16))
        self.assertIsNone(_materialized_fused_plan_pair((tiled_materialized, wrong_tile)))

    def test_cli_renders_one_noninteractive_screen(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO()), mock.patch("sys.stdout", output):
            exit_code = main(["garden", "--fixture", str(FIXTURE)])
        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().count("Raveil Garden | read-only graph browser"), 1)
        self.assertIn("Navigation: j next", output.getvalue())

    def test_wide_layout_uses_three_panes_with_bounded_lines(self) -> None:
        rendered = self._details(GardenSnapshot.load(FIXTURE), width=150).render()
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
        rendered = self._details(GardenSnapshot.load(FIXTURE), width=100).render()
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
        rendered = self._details(long_snapshot, 72).render()
        self.assertTrue(all(line.isprintable() for line in rendered.splitlines()))
        self.assertNotIn("\x1b", rendered)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 72)

    def test_cli_width_is_applied_and_invalid_width_fails_closed(self) -> None:
        output = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO()), mock.patch("sys.stdout", output):
            self.assertEqual(main(["garden", "--fixture", str(FIXTURE), "--width", "100"]), 0)
        self.assertIn("Materialized:", output.getvalue())
        self.assertLessEqual(max(map(len, output.getvalue().splitlines())), 100)
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

    def test_dynamic_explanation_is_strict_read_only_and_complete(self) -> None:
        explanation = GardenDynamicExplanation.load(
            "tests/fixtures/garden/dynamic-explanation.json"
        )
        self.assertEqual(explanation.graph_id, "cross-dilation-u32")
        self.assertEqual(explanation.program_version, 2)
        self.assertEqual(len(explanation.instructions), 10)
        with self.assertRaises(TypeError):
            explanation.identities["program_sha256"] = "0" * 64
        rendered = GardenDynamicBrowser(explanation).render()
        for expected in (
            "read-only dynamic execution explanation",
            "op=MAX_U32",
            "encoded word: 0x10000000",
            "assigned register: r0",
            "zero-based program-order indices",
            "descriptor_sha256:",
            "program_sha256:",
            "request_sha256:",
            "compiler_source_sha256:",
            "abi_sha256:",
            "rtl_sha256:",
            "toolchain_sha256:",
            "simulator_sha256:",
            "axi_trace_sha256:",
            "agreement: oracle=fallback=RTL exact",
            "performance=not-measured",
            "execute=no mutate=no approve=no promote=no",
        ):
            self.assertIn(expected, rendered)
        normalized = " ".join(rendered.replace("|", "").split())
        self.assertIn("evidence class (this Garden view): host-functional", normalized)
        self.assertIn(
            "retained execution evidence class: rtl-simulation-functional", normalized,
        )
        self.assertIn(
            "polls= is a termination diagnostic, not cycles, elapsed time, throughput, or performance",
            normalized,
        )
        self.assertIn("conformance", rendered)
        self.assertIn("transactions/output=6", rendered)
        self.assertLessEqual(max(map(len, rendered.splitlines())), 150)

    def test_dynamic_cli_demo_is_bounded_deterministic_and_keeps_navigation(self) -> None:
        arguments = [
            "garden", "--fixture", "tests/fixtures/garden/dynamic-explanation.json",
            "--keys", "jjq",
        ]
        outputs = []
        for _ in range(2):
            output = io.StringIO()
            with mock.patch("sys.stdout", output):
                self.assertEqual(main(arguments), 0)
            outputs.append(output.getvalue())
        self.assertEqual(outputs[0], outputs[1])
        self.assertIn("> [2] s op=LOAD_U32", outputs[0])
        self.assertTrue(outputs[0].rstrip().endswith("Raveil Garden | closed"))
        error = io.StringIO()
        with mock.patch("sys.stderr", error):
            self.assertEqual(main(arguments[:-1] + ["l"]), 2)
        self.assertIn("accepts only j, k, g, G, or q", error.getvalue())

    def test_dynamic_explanation_respects_all_terminal_width_boundaries(self) -> None:
        explanation = GardenDynamicExplanation.load(
            "tests/fixtures/garden/dynamic-explanation.json"
        )
        for width in (72, 119, 120, 150, 240):
            rendered = GardenDynamicBrowser(explanation, width).render()
            self.assertLessEqual(max(map(len, rendered.splitlines())), width)
            self.assertEqual(rendered, GardenDynamicBrowser(explanation, width).render())
        with self.assertRaisesRegex(ValueError, "width must be"):
            GardenDynamicBrowser(explanation, 71)

    def test_dynamic_trace_each_field_tamper_fails_before_render(self) -> None:
        mutations = {
            "index": lambda item: item.update(index=6),
            "node_id": lambda item: item.update(node_id="forged"),
            "op": lambda item: item.update(op="ADD_U32"),
            "dependencies": lambda item: item.update(dependencies=["n", "c"]),
            "selector": lambda item: item.update(selector="center"),
            "fan_out": lambda item: item.update(fan_out=2),
            "consumers": lambda item: item.update(consumers=["m3"]),
            "encoded_word": lambda item: item.update(encoded_word=item["encoded_word"] ^ 1),
            "source_registers": lambda item: item.update(source_registers=[1, 0]),
            "destination_register": lambda item: item.update(destination_register=2),
            "definition_index": lambda item: item.update(definition_index=4),
            "last_use_index": lambda item: item.update(last_use_index=8),
            "live_range": lambda item: item.update(live_range=[5, 8]),
            "release_after_index": lambda item: item.update(release_after_index=8),
        }
        for field, mutation in mutations.items():
            with self.subTest(field=field):
                malformed = self._dynamic_document()
                mutation(malformed["lowering"]["instructions"][5])
                with self.assertRaises(ValueError):
                    GardenDynamicExplanation.from_dict(malformed)

    def test_dynamic_schema_payload_identity_and_claim_tampering_fail(self) -> None:
        mutations = (
            lambda value: value.update(schema="raveil.garden-dynamic-explanation/v2"),
            lambda value: value.update(unknown=True),
            lambda value: value.pop("affine"),
            lambda value: value["lowering"].update(unknown=True),
            lambda value: value["lowering"]["instructions"][0].update(unknown=True),
            lambda value: value["identities"].pop("abi_sha256"),
            lambda value: value["lowering"].update(program_version=1),
            lambda value: value["program_payload"].__setitem__(0, 0),
            lambda value: value["program_payload"].__setitem__(4, 0),
            lambda value: value["program_payload"].__setitem__(12, value["program_payload"][12] ^ 1),
            lambda value: value["program_payload"].__setitem__(22, 1),
            lambda value: value["program_payload"].__setitem__(31, 1),
            lambda value: value["identities"].update(request_sha256="0" * 64),
            lambda value: value["agreement"].update(fallback_sha256="0" * 64),
            lambda value: value["evidence"].update(garden_class="rtl-simulation-functional"),
            lambda value: value.update(performance="measured"),
            lambda value: value["polls"].update(is_cycle_measurement=True),
            lambda value: value.update(lowering_trace_sha256="0" * 64),
            lambda value: value.update(retained_evidence_sha256="0" * 64),
        )
        for mutation in mutations:
            malformed = self._dynamic_document()
            mutation(malformed)
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.from_dict(malformed)
        for identity in self._dynamic_document()["identities"]:
            with self.subTest(identity=identity):
                malformed = self._dynamic_document()
                malformed["identities"][identity] = "0" * 64
                with self.assertRaises(ValueError):
                    GardenDynamicExplanation.from_dict(malformed)

    def test_dynamic_duplicate_fields_and_wrong_optional_types_fail(self) -> None:
        source = DYNAMIC_FIXTURE.read_text(encoding="ascii")
        duplicate = source.replace('"schema": ', '"schema": "forged", "schema": ', 1)
        descriptor, name = tempfile.mkstemp(
            prefix="dynamic-explanation-duplicate-", suffix=".json",
            dir=DYNAMIC_FIXTURE.parent,
        )
        os.close(descriptor)
        path = Path(name)
        try:
            path.write_text(duplicate, encoding="ascii")
            relative = path.relative_to(ROOT).as_posix()
            with self.assertRaisesRegex(ValueError, "duplicate field"):
                GardenDynamicExplanation.load(relative)
        finally:
            path.unlink(missing_ok=True)
        for field, invalid in (
            ("definition_index", "5"),
            ("last_use_index", False),
            ("live_range", [5, "7"]),
            ("release_after_index", []),
        ):
            malformed = self._dynamic_document()
            malformed["lowering"]["instructions"][5][field] = invalid
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.from_dict(malformed)

    def test_dynamic_path_and_file_admission_fail_closed(self) -> None:
        for path in (
            "", ".", "./tests/fixtures/garden/dynamic-explanation.json",
            "tests/fixtures/garden/../garden/dynamic-explanation.json",
            "README.md", str(DYNAMIC_FIXTURE),
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                GardenDynamicExplanation.load(path)
        document = self._dynamic_document()
        relative, leaf = self._write_dynamic(document)
        link = leaf.with_name(leaf.name + "-link.json")
        directory = leaf.with_name(leaf.name + "-directory.json")
        fifo = leaf.with_name(leaf.name + "-fifo.json")
        hardlink = leaf.with_name(leaf.name + "-hardlink.json")
        empty = leaf.with_name(leaf.name + "-empty.json")
        oversized = leaf.with_name(leaf.name + "-oversized.json")
        try:
            link.symlink_to(leaf)
            directory.mkdir()
            os.mkfifo(fifo)
            os.link(leaf, hardlink)
            empty.touch()
            oversized.write_bytes(b"x" * (64 * 1024 + 1))
            for candidate in (link, directory, fifo, hardlink, empty, oversized):
                with self.subTest(candidate=candidate.name), self.assertRaises(ValueError):
                    GardenDynamicExplanation.load(candidate.relative_to(ROOT).as_posix())
            # The original is also rejected while it has a second hard link.
            with self.assertRaises(ValueError):
                GardenDynamicExplanation.load(relative)
        finally:
            for path in (link, fifo, hardlink, empty, oversized, leaf):
                path.unlink(missing_ok=True)
            if directory.exists():
                directory.rmdir()

    def test_dynamic_parent_symlink_and_read_race_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            repository = temporary_root / "repository"
            outside = temporary_root / "outside"
            (outside / "fixtures/garden").mkdir(parents=True)
            repository.mkdir()
            (repository / "tests").symlink_to(outside, target_is_directory=True)
            with mock.patch("raveil.garden._repository_root", return_value=repository):
                with self.assertRaises(ValueError):
                    GardenDynamicExplanation.load(
                        "tests/fixtures/garden/dynamic-explanation.json"
                    )
        relative, leaf = self._write_dynamic(self._dynamic_document())
        real_read = os.read
        changed = False

        def raced(descriptor: int, size: int) -> bytes:
            nonlocal changed
            payload = real_read(descriptor, size)
            if not changed:
                changed = True
                os.utime(leaf, ns=(leaf.stat().st_atime_ns, leaf.stat().st_mtime_ns + 1_000_000))
            return payload

        try:
            with mock.patch("raveil.garden.os.read", side_effect=raced):
                with self.assertRaisesRegex(ValueError, "changed while read"):
                    GardenDynamicExplanation.load(relative)
        finally:
            leaf.unlink(missing_ok=True)
        relative, leaf = self._write_dynamic(self._dynamic_document())
        replacement = leaf.with_name(leaf.name + "-opened")
        original = leaf.read_bytes()
        changed = False

        def replaced(descriptor: int, size: int) -> bytes:
            nonlocal changed
            payload = real_read(descriptor, size)
            if not changed:
                changed = True
                leaf.rename(replacement)
                leaf.write_bytes(original)
            return payload

        try:
            with mock.patch("raveil.garden.os.read", side_effect=replaced):
                with self.assertRaisesRegex(ValueError, "changed while read"):
                    GardenDynamicExplanation.load(relative)
        finally:
            leaf.unlink(missing_ok=True)
            replacement.unlink(missing_ok=True)

    def test_dynamic_missing_no_follow_capabilities_fail_before_open(self) -> None:
        for capability in ("O_NOFOLLOW", "O_DIRECTORY"):
            with self.subTest(capability=capability), \
                    mock.patch.object(os, capability, None), \
                    mock.patch("raveil.garden.os.open",
                               side_effect=AssertionError("path touched")) as opened:
                with self.assertRaisesRegex(
                    ValueError, "requires O_NOFOLLOW and O_DIRECTORY",
                ):
                    GardenDynamicExplanation.load(
                        "tests/fixtures/garden/dynamic-explanation.json"
                    )
                opened.assert_not_called()

    def test_dynamic_view_never_calls_execution_or_compiler_paths(self) -> None:
        import subprocess
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("execution")), \
                mock.patch("raveil.garden.GraphCompiler.compile",
                           side_effect=AssertionError("legacy compiler")), \
                mock.patch("raveil.graph_device_dag.compile_descriptor",
                           side_effect=AssertionError("compiler")):
            explanation = GardenDynamicExplanation.load(
                "tests/fixtures/garden/dynamic-explanation.json"
            )
            self.assertIn("read-only", GardenDynamicBrowser(explanation).render())


if __name__ == "__main__":
    unittest.main()
