"""Host-functional adapter tests; mocked runners are not RTL evidence."""
import json
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


def host_fixture_runner(descriptor_bytes, seed):
    """Supply known bytes at the runner boundary, never launch a simulator."""
    descriptor = json.loads(descriptor_bytes)
    words = graph_oracle(descriptor, input_words(seed))
    output = struct.pack(f"<{len(words)}I", *words)
    return {
        "output": output, "input": struct.pack("<324I", *input_words(seed)),
        "summary": "host fixture only", "evidence_directory": "/test-only",
        "receipt": {
            "descriptor_sha256": digest(descriptor_bytes),
            "program_sha256": compile_descriptor(descriptor)["program_sha256"],
            "output_sha256": digest(output), "simulator_sha256": "a" * 64,
            "rtl_manifest_sha256": "b" * 64, "source_manifest_sha256": "c" * 64,
        },
    }


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

    def test_show_explains_editable_dependencies_and_coordinates(self):
        shown = self.project.show("neighborhood")
        self.assertIn("nodes=4 edges=3 instructions=4/16", shown)
        self.assertIn("combine: ADD_U32 <- center, north", shown)
        self.assertIn('"row_delta": -1', shown)
        self.assertIn("seed=1", shown)
        self.assertIn("rtl-sim", shown)

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
