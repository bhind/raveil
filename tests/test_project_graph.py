"""Host-functional adapter tests; mocked runners are not RTL evidence."""
import json
import contextlib
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from raveil.cli import main
from raveil.graph_device_dag import compile_descriptor, graph_oracle
from raveil.graph_device_dynamic import run_snapshot
from raveil.project import Project, digest, init_project
from raveil.project_graph import compile_graph, output_text, sample_descriptor
from raveil.riscv_stencil_signature import input_words


def host_fixture_runner(descriptor_bytes, seed, *, input_bytes=None):
    """Supply known bytes at the runner boundary, never launch a simulator."""
    descriptor = json.loads(descriptor_bytes)
    input_payload = input_bytes if input_bytes is not None else struct.pack("<324I", *input_words(seed))
    input_data = struct.unpack("<324I", input_payload)
    words = graph_oracle(descriptor, input_data)
    output = struct.pack(f"<{len(words)}I", *words)
    result = {
        "output": output, "input": input_payload,
        "summary": "host fixture only", "evidence_directory": "/test-only",
        "receipt": {
            "descriptor_sha256": digest(descriptor_bytes),
            "program_sha256": compile_descriptor(descriptor)["program_sha256"],
            "output_sha256": digest(output), "simulator_sha256": "a" * 64,
            "rtl_manifest_sha256": "b" * 64, "source_manifest_sha256": "c" * 64,
        },
    }
    if input_bytes is not None:
        result["receipt"].update({"input_mode": "snapshot", "input_sha256": digest(input_bytes)})
    return result


class ProjectGraphTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        init_project(self.root)
        self.project = Project(self.root)
        self.descriptor_path = self.root / "inputs/neighborhood.json"

    def run_graph(self):
        return self.project.run("neighborhood", "rtl-sim", kernel=Path("unused"),
                                qemu="unused", compiler="unused")

    def run_graph_data(self):
        return self.project.run("neighborhood-data", "rtl-sim", kernel=Path("unused"),
                                qemu="unused", compiler="unused")

    def test_output_displays_saved_rows_after_edit_without_execution(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            record = self.run_graph_data()
        run_id = record["run_id"]
        saved = self.root / "runs" / run_id / "workspace/output.txt"
        original = saved.read_text()
        self.descriptor_path.write_text("invalid current descriptor")
        (self.root / "inputs/neighborhood-data.json").write_text("invalid current input")
        out = io.StringIO()
        with patch("raveil.project_graph.run_snapshot") as runner, \
                patch("raveil.project_graph.compile_graph") as compiler, \
                contextlib.redirect_stdout(out):
            self.assertEqual(main(["project", "output", run_id, "--project", str(self.root)]), 0)
            runner.assert_not_called()
            compiler.assert_not_called()
        self.assertIn(f"run={run_id}", out.getvalue())
        self.assertIn("simulation not rerun", out.getvalue())
        self.assertTrue(out.getvalue().endswith(original))
        self.assertEqual(saved.read_text(), original)
        self.assertEqual(len(list((self.root / "runs").iterdir())), 1)

    def test_output_rejects_changed_artifact_without_printing_rows(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            record = self.run_graph()
        run_id = record["run_id"]
        (self.root / "runs" / run_id / "workspace/output.txt").write_text("changed output\n")
        out, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(error):
            self.assertEqual(main(["project", "output", run_id, "--project", str(self.root)]), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("saved artifacts changed", error.getvalue())

    def test_output_rechecks_bytes_after_record_validation(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            record = self.run_graph()
        run_id = record["run_id"]
        verified = self.project.load_run(run_id)
        (self.root / "runs" / run_id / "workspace/output.txt").write_text("changed after admission\n")
        with patch.object(self.project, "load_run", return_value=verified):
            with self.assertRaisesRegex(ValueError, "saved Graph output changed"):
                self.project.output(run_id)

    def test_output_rejects_failed_non_graph_and_missing_runs(self):
        native = self.project.run("logs", "native", kernel=Path("unused"), qemu="unused", compiler="unused")
        self.descriptor_path.write_text("{}")
        failed = self.run_graph()
        for run_id in (native["run_id"], failed["run_id"], "missing", "../outside"):
            with self.subTest(run_id=run_id):
                out, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(error):
                    self.assertEqual(main(["project", "output", run_id, "--project", str(self.root)]), 2)
                self.assertEqual(out.getvalue(), "")
                self.assertNotIn("Traceback", error.getvalue())

    def test_show_explains_editable_dependencies_and_coordinates(self):
        shown = self.project.show("neighborhood")
        self.assertIn("nodes=4 edges=3 instructions=4/16", shown)
        self.assertIn("combine: ADD_U32 <- center, north", shown)
        self.assertIn('"row_delta": -1', shown)
        self.assertIn("seed=1", shown)
        self.assertIn("rtl-sim", shown)
        self.assertIn("descriptor file: inputs/neighborhood.json", shown)

    def test_show_names_actual_descriptor_instead_of_inferring_from_graph_id(self):
        renamed = self.root / "inputs/my-edited-graph.json"
        renamed.write_bytes(self.descriptor_path.read_bytes())
        for source in ("neighborhood", "neighborhood-data"):
            with self.subTest(source=source):
                recipe = json.loads((self.root / f"recipes/{source}.json").read_text())
                recipe["descriptor"] = renamed.name
                (self.root / "recipes/recipe-alias.json").write_text(json.dumps(recipe))
                out = io.StringIO()
                with patch("raveil.project_graph.run_snapshot") as runner, contextlib.redirect_stdout(out):
                    result = main(["project", "show", "recipe-alias", "--project", str(self.root)])
                    runner.assert_not_called()
                self.assertEqual(result, 0)
                shown = out.getvalue()
                self.assertIn("graph=neighborhood", shown)
                self.assertIn("descriptor file: inputs/my-edited-graph.json", shown)
                self.assertNotIn(str(self.root), shown)
                if "input" in recipe:
                    self.assertIn("input file: inputs/neighborhood-data.json", shown)
                else:
                    self.assertNotIn("input file:", shown)

    def test_edit_changes_program_and_output_but_preserves_old_snapshot(self):
        original = self.descriptor_path.read_bytes()
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner) as runner:
            first = self.run_graph()
            self.assertEqual(first["status"], "succeeded", first["error"])
            self.assertEqual(runner.call_args.args[0], original)
            changed = json.loads(original)
            changed["nodes"][2]["op"] = "MAX_U32"
            self.descriptor_path.write_text(json.dumps(changed))
            second = self.run_graph()
        self.assertEqual(second["status"], "succeeded", second["error"])
        self.assertNotEqual(first["outputs"], second["outputs"])
        saved = self.root / "runs" / first["run_id"]
        self.assertEqual((saved / "inputs/neighborhood.json").read_bytes(), original)
        self.assertEqual((saved / "generated-input.bin").stat().st_size, 324 * 4)
        self.assertEqual(self.project.load_run(first["run_id"]), first)
        diff = self.project.diff(first["run_id"], second["run_id"])
        self.assertIn("simulator_sha256: same", diff)
        self.assertIn("rtl_manifest_sha256: same", diff)
        self.assertIn("program_sha256:", diff)
        self.assertIn("/output.txt", diff)
        self.assertIn("node combine:", diff)
        self.assertIn("ADD_U32", diff)
        self.assertIn("MAX_U32", diff)
        self.assertIn("output: 64/64 active cells changed", diff)
        self.assertIn("first changed cell (0, 0): 2802362300 -> 1788458059", diff)

    def test_edit_to_v4_mul_reaches_runner_and_keeps_previous_run(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            first = self.run_graph()
            graph = json.loads(self.descriptor_path.read_text())
            graph["schema"] = "raveil.graph-device-dag/v3"
            graph["nodes"][2]["op"] = "MUL_U32"
            self.descriptor_path.write_text(json.dumps(graph))
            self.assertIn("MUL_U32", self.project.show("neighborhood"))
            second = self.run_graph()
        self.assertEqual(second["status"], "succeeded", second["error"])
        self.assertEqual(compile_descriptor(graph)["payload"][1], 4)
        self.assertEqual(self.project.load_run(first["run_id"]), first)
        self.assertIn("MUL_U32", self.project.diff(first["run_id"], second["run_id"]))

    def test_seed_edit_changes_generated_input_without_overwriting_user_file(self):
        (self.root / "inputs/generated-input.bin").write_bytes(b"user input")
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            first = self.run_graph()
            recipe_path = self.root / "recipes/neighborhood.json"
            recipe = json.loads(recipe_path.read_text())
            recipe["seed"] = 2
            recipe_path.write_text(json.dumps(recipe))
            second = self.run_graph()
        self.assertEqual(second["status"], "succeeded", second["error"])
        self.assertNotEqual(first["inputs"]["generated_input_sha256"], second["inputs"]["generated_input_sha256"])
        self.assertEqual((self.root / "inputs/generated-input.bin").read_bytes(), b"user input")

    def test_snapshot_record_missing_input_name_fails_cleanly_in_cli_diff(self):
        from raveil.project import encoded
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            valid = self.run_graph_data()
        directory = self.root / "runs" / valid["run_id"]
        for value in (None, [], 1, ""):
            with self.subTest(value=value):
                record = json.loads(json.dumps(valid))
                if value is None:
                    del record["recipe"]["input"]
                else:
                    record["recipe"]["input"] = value
                record["recipe_sha256"] = digest(encoded(record["recipe"]))
                payload = encoded(record)
                (directory / "record.json").write_bytes(payload)
                (directory / "record.sha256").write_text(digest(payload) + "\n")
                with self.assertRaisesRegex(ValueError, "snapshot input"):
                    self.project.load_run(valid["run_id"])
                with contextlib.redirect_stdout(io.StringIO()), patch("sys.stderr", new_callable=io.StringIO) as error:
                    self.assertEqual(main(["project", "diff", valid["run_id"], valid["run_id"],
                                           "--project", str(self.root)]), 2)
                self.assertNotIn("Traceback", error.getvalue())

    def test_editable_input_snapshot_changes_output_and_preserves_old_run(self):
        input_path = self.root / "inputs/neighborhood-data.json"
        original = input_path.read_bytes()
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner) as runner:
            first = self.run_graph_data()
            changed = json.loads(original)
            changed["words"][18] = 0xffffffff
            input_path.write_text(json.dumps(changed))
            second = self.run_graph_data()
        self.assertEqual(first["status"], "succeeded", first["error"])
        self.assertEqual(second["status"], "succeeded", second["error"])
        self.assertNotEqual(first["outputs"], second["outputs"])
        self.assertEqual((self.root / "runs" / first["run_id"] / "inputs/neighborhood-data.json").read_bytes(), original)
        self.assertEqual(runner.call_args.kwargs["input_bytes"], struct.pack("<324I", *changed["words"]))
        self.assertEqual(first["inputs"]["input_mode"], "snapshot")
        self.assertIn("/neighborhood-data.json", self.project.diff(first["run_id"], second["run_id"]))
        shown = self.project.diff(first["run_id"], second["run_id"])
        self.assertIn("input: 1/324 words changed", shown)
        self.assertIn(f"first changed input word [18] (zero-based): {json.loads(original)['words'][18]} -> 4294967295", shown)

    def test_input_diff_is_saved_semantic_and_does_not_execute(self):
        path = self.root / "inputs/neighborhood-data.json"
        original = json.loads(path.read_text())
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            first = self.run_graph_data()
            path.write_text(json.dumps(original, indent=4))
            formatted = self.run_graph_data()
            changed = json.loads(path.read_text())
            for index in (20, 3):
                changed["words"][index] ^= 1
            path.write_text(json.dumps(changed))
            second = self.run_graph_data()
        path.write_text("current workspace is deliberately invalid")
        with patch("raveil.project_graph.run_snapshot") as runner, patch("raveil.project_graph.compile_graph") as compiler:
            same = self.project.diff(first["run_id"], formatted["run_id"])
            shown = self.project.diff(first["run_id"], second["run_id"])
            runner.assert_not_called()
            compiler.assert_not_called()
        self.assertIn("input: 0/324 words changed", same)
        self.assertNotIn("first changed input word", same)
        self.assertIn("/neighborhood-data.json", same)
        self.assertIn("input: 2/324 words changed", shown)
        self.assertIn(f"first changed input word [3] (zero-based): {original['words'][3]} -> {changed['words'][3]}", shown)
        self.assertEqual(shown, self.project.diff(first["run_id"], second["run_id"]))

    def test_input_diff_preserves_legacy_and_rejects_corrupt_history(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            seed = self.run_graph()
            explicit = self.run_graph_data()
        self.assertNotIn("words changed", self.project.diff(seed["run_id"], explicit["run_id"]))
        self.assertNotIn("words changed", self.project.diff(seed["run_id"], seed["run_id"]))
        with patch("raveil.project_graph.run_snapshot", side_effect=ValueError("failed fixture")):
            failed = self.run_graph_data()
        self.assertNotIn("words changed", self.project.diff(explicit["run_id"], failed["run_id"]))
        saved = self.root / "runs" / explicit["run_id"] / "input.bin"
        saved.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "saved artifacts changed"):
            self.project.diff(explicit["run_id"], explicit["run_id"])

    def test_explicit_input_symlink_rejected_by_show_and_run(self):
        path = self.root / "inputs/neighborhood-data.json"
        outside = Path(self.temporary.name) / "outside-input.json"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises((OSError, ValueError)):
            self.project.show("neighborhood-data")
        with patch("raveil.project_graph.run_snapshot") as runner:
            result = self.run_graph_data()
        self.assertEqual(result["status"], "failed")
        runner.assert_not_called()

    def test_explicit_input_receipt_or_returned_bytes_mismatch_fails_closed(self):
        for changed in ("receipt", "returned"):
            with self.subTest(changed=changed):
                def incorrect(*args, **kwargs):
                    result = host_fixture_runner(*args, **kwargs)
                    if changed == "receipt": result["receipt"]["input_sha256"] = "f" * 64
                    else: result["input"] = b"x" * (324 * 4)
                    return result
                with patch("raveil.project_graph.run_snapshot", side_effect=incorrect):
                    result = self.run_graph_data()
                self.assertEqual(result["status"], "failed")
                self.assertIn("saved Graph input", result["error"])

    def test_snapshot_input_malformed_or_oversized_fails_before_runner(self):
        path = self.root / "inputs/neighborhood-data.json"
        invalid = [
            b'{"schema":"raveil.graph-input/v1","words":[true]}' ,
            json.dumps({"schema": "raveil.graph-input/v1", "words": [0] * 323}).encode(),
            b'{"schema":"raveil.graph-input/v1","words":[],"words":[]}',
            b" " * (64 * 1024 + 1),
        ]
        for bad in (True, 0.5, -1, 0x100000000):
            invalid.append(json.dumps({"schema": "raveil.graph-input/v1",
                                       "words": [bad] + [0] * 323}).encode())
        invalid.append(json.dumps({"schema": "raveil.graph-input/v1",
                                   "words": [0] * 324, "extra": 1}).encode())
        with patch("raveil.project_graph.run_snapshot") as runner:
            for payload in invalid:
                with self.subTest(size=len(payload)):
                    path.write_bytes(payload)
                    result = self.run_graph_data()
                    self.assertEqual(result["status"], "failed")
            runner.assert_not_called()

    def test_malformed_graphs_fail_before_runner_and_retain_failed_history(self):
        invalid = []
        graph = sample_descriptor()
        graph["nodes"][0]["address"]["row_delta"] = 2
        invalid.append(graph)
        graph = sample_descriptor()
        graph["nodes"][2]["inputs"] = ["missing", "north"]
        invalid.append(graph)
        graph = sample_descriptor()
        graph["nodes"][2]["inputs"] = [{}, "north"]
        invalid.append(graph)
        graph = sample_descriptor()
        graph["affine"]["rows"] = 7
        invalid.append(graph)
        graph = sample_descriptor()
        graph["nodes"] = graph["nodes"] * 5
        invalid.append(graph)
        with patch("raveil.project_graph.run_snapshot") as runner:
            for graph in invalid:
                with self.subTest(graph=graph):
                    self.descriptor_path.write_text(json.dumps(graph))
                    result = self.run_graph()
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["outputs"], {})
                    self.assertEqual(self.project.load_run(result["run_id"]), result)
            runner.assert_not_called()

    def test_invalid_backend_and_descriptor_path_fail_before_launch(self):
        with self.assertRaisesRegex(ValueError, "require --backend rtl-sim"):
            self.project.run("neighborhood", "native", kernel=Path("unused"), qemu="unused", compiler="unused")
        recipe_path = self.root / "recipes/neighborhood.json"
        recipe = json.loads(recipe_path.read_text())
        recipe["descriptor"] = "../external.json"
        recipe_path.write_text(json.dumps(recipe))
        with self.assertRaises(ValueError):
            self.run_graph()

    def test_descriptor_symlink_rejected_before_runner(self):
        outside = Path(self.temporary.name) / "outside.json"
        self.descriptor_path.rename(outside)
        self.descriptor_path.symlink_to(outside)
        with patch("raveil.project_graph.run_snapshot") as runner:
            result = self.run_graph()
            self.assertEqual(result["status"], "failed")
            runner.assert_not_called()

    def test_receipt_mismatch_cannot_publish_outputs(self):
        def incorrect(*args):
            result = host_fixture_runner(*args)
            result["receipt"]["program_sha256"] = "f" * 64
            return result
        with patch("raveil.project_graph.run_snapshot", side_effect=incorrect):
            result = self.run_graph()
        self.assertEqual(result["status"], "failed")
        self.assertIn("receipt differs", result["error"])
        self.assertEqual(result["outputs"], {})

    def test_snapshot_mutation_during_execution_fails_closed(self):
        def mutate_snapshot(descriptor_bytes, seed):
            result = host_fixture_runner(descriptor_bytes, seed)
            saved = next((self.root / "runs").glob("*/inputs/neighborhood.json"))
            changed = json.loads(descriptor_bytes)
            changed["nodes"][2]["op"] = "MAX_U32"
            saved.write_text(json.dumps(changed))
            return result
        with patch("raveil.project_graph.run_snapshot", side_effect=mutate_snapshot):
            result = self.run_graph()
        self.assertEqual(result["status"], "failed")
        self.assertIn("snapshot changed during execution", result["error"])
        self.assertEqual(result["outputs"], {})

    def test_changed_output_history_is_rejected(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner):
            result = self.run_graph()
        (self.root / "runs" / result["run_id"] / "workspace/output.txt").write_text("forged")
        with self.assertRaisesRegex(ValueError, "saved artifacts changed"):
            self.project.load_run(result["run_id"])

    def test_output_text_rejects_wrong_size(self):
        with self.assertRaisesRegex(ValueError, "output size"):
            output_text(b"bad", compile_graph(sample_descriptor()))

    def test_compact_text_projects_active_rows_from_full_transport_window(self):
        program = compile_graph(sample_descriptor())
        payload = struct.pack("<256I", *range(256))
        rows = output_text(payload, program).decode().splitlines()
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0], "0 1 2 3 4 5 6 7")
        self.assertEqual(rows[-1], "56 57 58 59 60 61 62 63")

    def test_cli_reports_actual_backend_and_validation(self):
        with patch("raveil.project_graph.run_snapshot", side_effect=host_fixture_runner), patch("builtins.print") as printed:
            self.assertEqual(main(["project", "run", "neighborhood", "--backend", "rtl-sim", "--project", str(self.root)]), 0)
        rendered = "\n".join(call.args[0] for call in printed.call_args_list)
        self.assertIn("descriptor oracle, C++ fallback and RTL output are byte-equal", rendered)
        self.assertNotIn("trusted GEMM", rendered)

    def test_snapshot_runner_passes_data_to_existing_admission_and_rechecks_output(self):
        repo = Path(self.temporary.name) / "repo"
        repo.mkdir()
        payload = b"  " + json.dumps(sample_descriptor()).encode() + b"\n"
        def complete(graphs, seeds, repository, command, *, details):
            self.assertEqual((repository / graphs[0]).read_bytes(), payload)
            self.assertEqual(seeds, [1])
            request = repository / "request"
            request.mkdir()
            (request / "private-output-neighborhood-seed-1.bin").write_bytes(b"output")
            details.update(request_roots=[request], receipts=[{
                "graph_id": "neighborhood", "output_sha256": digest(b"output")
            }], summary="host fixture")
        with patch("raveil.graph_device_dynamic._run_dynamic", side_effect=complete):
            result = run_snapshot(payload, 1, repo)
        self.assertEqual(result["output"], b"output")
        self.assertEqual(result["input"], struct.pack("<324I", *input_words(1)))


if __name__ == "__main__":
    unittest.main()
