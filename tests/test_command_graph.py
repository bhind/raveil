from __future__ import annotations

from dataclasses import replace
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.command_graph import (
    CommandComparison,
    CommandGraphCompiler,
    CommandGraphProgram,
    ToolRegistry,
    ExecutionPolicy,
    benchmark,
)
from raveil.interactive_shell import NativeInteractiveSession, dispatch
from raveil.command_workloads import preregistered_workloads
from raveil.workspace import NativeWorkspace, WorkspaceError


ROOT = Path(__file__).resolve().parents[1]


class CommandGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = NativeWorkspace(self.root)
        self.registry = ToolRegistry()
        self.compiler = CommandGraphCompiler(self.workspace, self.registry)
        (self.root / "input.txt").write_text("INFO start\nERROR failed\nERROR retry\n")
        (self.root / "words.txt").write_text("pear\napple\npear\nbanana\n")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_pipeline_quoting_and_deterministic_identity(self) -> None:
        source = 'cat "/input.txt" | grep "ERROR" | wc -l'
        first = self.compiler.compile(source)
        second = CommandGraphCompiler(self.workspace, ToolRegistry()).compile(source)
        self.assertEqual(first.graph_id, second.graph_id)
        self.assertEqual(len(first.nodes), 3)
        self.assertEqual([(edge.source, edge.target, edge.kind) for edge in first.edges], [
            ("node-001-cat", "node-002-grep", "stream"),
            ("node-002-grep", "node-003-wc", "stream"),
        ])
        self.assertEqual(first.declared_inputs, ("/input.txt",))

    def test_strict_schema_round_trip_and_unknown_field_rejection(self) -> None:
        program = self.compiler.compile("cat /words.txt | sort | uniq -c")
        self.assertEqual(CommandGraphProgram.from_dict(program.to_dict()), program)
        malformed = program.to_dict()
        malformed["unknown"] = True
        with self.assertRaisesRegex(ValueError, "fields do not match"):
            CommandGraphProgram.from_dict(malformed)
        nested = program.to_dict()
        nested["nodes"][0]["unknown"] = True
        with self.assertRaisesRegex(ValueError, "fields do not match"):
            CommandGraphProgram.from_dict(nested)

    def test_direct_and_graph_outputs_agree_exactly(self) -> None:
        program = self.compiler.compile("cat /input.txt | grep ERROR | wc -l")
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=True)
        self.assertTrue(result.semantic_valid)
        self.assertTrue(result.committed)
        self.assertEqual(result.direct.stdout, b"2\n")
        self.assertEqual(result.direct.stdout, result.graph.stdout)
        self.assertEqual(result.direct.exit_status, result.graph.exit_status)

    def test_binary_stdout_is_lossless_and_private_paths_are_absent(self) -> None:
        payload = b"\x00\xffcommand-graph\n"
        (self.root / "binary.dat").write_bytes(payload)
        program = self.compiler.compile("cat /binary.dat")
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=False)
        encoded = result.to_dict()
        self.assertEqual(base64.b64decode(encoded["direct"]["stdout_base64"]), payload)
        self.assertEqual(encoded["direct"]["stdout_encoding"], "base64")
        self.assertNotIn(str(self.root), json.dumps(encoded))

    def test_redirection_is_exclusive_and_published_after_agreement(self) -> None:
        program = self.compiler.compile("cat /words.txt | sort | uniq -c > /counts.txt")
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=True)
        self.assertTrue(result.semantic_valid)
        self.assertTrue((self.root / "counts.txt").is_file())
        self.assertEqual(result.direct.outputs, result.graph.outputs)
        with self.assertRaisesRegex(WorkspaceError, "output already exists"):
            self.compiler.compile("cat /words.txt > /counts.txt")

    def test_multi_output_and_directory_mutations_are_declared(self) -> None:
        program = self.compiler.compile("cp /input.txt /copy.txt ||| cp /words.txt /words-copy.txt")
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=True)
        self.assertTrue(result.semantic_valid)
        self.assertEqual((self.root / "copy.txt").read_bytes(), (self.root / "input.txt").read_bytes())
        self.assertEqual((self.root / "words-copy.txt").read_bytes(), (self.root / "words.txt").read_bytes())
        directory = self.compiler.compile("mkdir /created")
        made = CommandComparison(self.workspace, self.registry).execute(directory, publish=True)
        self.assertTrue(made.semantic_valid)
        self.assertTrue((self.root / "created").is_dir())

    def test_success_dependency_and_failure_propagation(self) -> None:
        program = self.compiler.compile("grep NEVER /input.txt && wc -l")
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=True)
        self.assertFalse(result.semantic_valid)
        self.assertFalse(result.committed)
        self.assertEqual(result.direct.nodes[1].status, "skipped")
        self.assertEqual(result.graph.nodes[1].status, "skipped")

    def test_owned_join_fanout_is_independent_and_equal_concurrency(self) -> None:
        program = self.compiler.compile("sha256sum /input.txt ||| sha256sum /words.txt")
        self.assertFalse(program.nodes[0].dependencies)
        self.assertFalse(program.nodes[1].dependencies)
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=False)
        self.assertTrue(result.semantic_valid)
        self.assertGreaterEqual(result.direct.maximum_concurrency, 2)
        self.assertEqual(result.direct.maximum_concurrency, result.graph.maximum_concurrency)
        self.assertNotIn(str(self.root), json.dumps(result.to_dict()))

    def test_parser_rejects_unsupported_or_ambient_execution(self) -> None:
        for source in (
            "python3 script.py", "/bin/cat /input.txt", "cat /input.txt >> /out",
            "cat $HOME", "cat *.txt", "cat /input.txt || wc -l", "cat /input.txt &",
            "grep -f /input.txt /words.txt", "tee -a /out",
        ):
            with self.assertRaises((ValueError, WorkspaceError), msg=source):
                self.compiler.compile(source)
        program = self.compiler.compile("cat /input.txt")
        self.assertTrue(program.nodes[0].tool.locator.startswith("system://"))
        self.assertNotIn(str(self.root), json.dumps(program.to_dict()))

    def test_traversal_and_symlink_inputs_are_rejected(self) -> None:
        outside = self.root.parent / "outside-command-graph"
        outside.write_text("outside")
        (self.root / "link").symlink_to(outside)
        with self.assertRaises(WorkspaceError):
            self.compiler.compile("cat ../outside-command-graph")
        with self.assertRaises(WorkspaceError):
            self.compiler.compile("cat /link")
        outside.unlink()

    def test_stale_tool_identity_is_rejected(self) -> None:
        program = self.compiler.compile("cat /input.txt")
        stale_tool = replace(program.nodes[0].tool, binary_sha256="0" * 64)
        stale_node = replace(program.nodes[0], tool=stale_tool)
        provisional = replace(program, graph_id="pending", nodes=(stale_node,))
        stale = replace(provisional, graph_id=f"command-{provisional.identity[:16]}")
        with self.assertRaisesRegex(ValueError, "tool identity"):
            CommandComparison(self.workspace, self.registry).execute(stale, publish=False)

    def test_timeout_and_undeclared_mutation_fail_closed(self) -> None:
        program = self.compiler.compile("cat /input.txt")
        timeout = subprocess_timeout()
        with mock.patch("raveil.command_graph.subprocess.Popen") as popen:
            popen.return_value.pid = 999999
            popen.return_value.communicate.side_effect = timeout
            result = CommandComparison(self.workspace, self.registry).execute(program, publish=False)
        self.assertFalse(result.semantic_valid)
        self.assertEqual(result.direct.status, "timeout")

        from raveil.command_graph import _ExecutorBase
        real_run_node = _ExecutorBase._run_node
        def mutate(executor, node, stage, stdin):  # type: ignore[no-untyped-def]
            outcome = real_run_node(executor, node, stage, stdin)
            Path(stage, "surprise.txt").write_text("unexpected")
            return outcome
        with mock.patch.object(_ExecutorBase, "_run_node", mutate):
            result = CommandComparison(self.workspace, self.registry).execute(program, publish=False)
        self.assertFalse(result.semantic_valid)
        self.assertEqual(result.direct.status, "invalid-mutation")

    def test_benchmark_fields_are_balanced_and_non_claim(self) -> None:
        program = self.compiler.compile("cat /input.txt | grep ERROR | wc -l")
        value = benchmark(program, self.workspace, self.registry, warmups=0, repetitions=4,
                          parse_ns=self.compiler.last_parse_ns,
                          construction_ns=self.compiler.last_construction_ns).to_dict()
        self.assertEqual(value["schema"], "raveil.command-benchmark-result/v1")
        self.assertEqual(value["order"].count("direct-first"), 2)
        self.assertEqual(value["order"].count("graph-first"), 2)
        self.assertEqual(len(value["direct_execution"]["samples_ns"]), 4)
        self.assertIn("paired_bootstrap_95_ns", value)
        self.assertTrue(value["equal_concurrency_baseline"])
        self.assertEqual(value["claim_status"], "development-non-claim")
        self.assertFalse(value["crossover_evaluated"])
        self.assertIsNone(value["crossover"])
        self.assertEqual(len(value["actual_direct_concurrency"]), 4)
        self.assertEqual(len(value["direct_node_samples"]), 4)
        self.assertIn("stdout_sha256", value["direct_node_samples"][0][0])
        self.assertFalse(value["ordinary_pipeline_baseline"])
        self.assertFalse(value["scheduling_claim_eligible"])

    def test_benchmark_rejects_invalid_pairs_from_statistics(self) -> None:
        program = self.compiler.compile("cat /input.txt")
        valid = CommandComparison(self.workspace, self.registry).execute(program, publish=False)
        invalid = replace(valid, semantic_valid=False, differences=("stdout",))
        with mock.patch.object(CommandComparison, "execute", return_value=invalid):
            value = benchmark(program, self.workspace, self.registry, warmups=0, repetitions=2,
                              parse_ns=1, construction_ns=2).to_dict()
        self.assertFalse(value["comparison_valid"])
        self.assertEqual(value["accepted_pairs"], 0)
        self.assertEqual(value["rejected_pairs"], 2)
        self.assertIsNone(value["paired_bootstrap_95_ns"])
        self.assertEqual(value["direct_execution"]["samples_ns"], [])

    def test_read_after_write_and_nested_outputs_publish(self) -> None:
        program = self.compiler.compile("cp /input.txt /mid ; cat /mid")
        self.assertEqual(program.declared_outputs, ("/mid",))
        result = CommandComparison(self.workspace, self.registry).execute(program, publish=True)
        self.assertTrue(result.semantic_valid)
        self.assertEqual((self.root / "mid").read_bytes(), (self.root / "input.txt").read_bytes())
        nested = self.compiler.compile("mkdir /out ; cp /words.txt /out/words")
        nested_result = CommandComparison(self.workspace, self.registry).execute(nested, publish=True)
        self.assertTrue(nested_result.semantic_valid)
        self.assertEqual((self.root / "out/words").read_bytes(), (self.root / "words.txt").read_bytes())

    def test_deserialized_node_cannot_reclassify_tool_or_policy(self) -> None:
        program = self.compiler.compile("cat /input.txt")
        malformed = program.to_dict()
        malformed["nodes"][0]["declared_writes"] = ["/forged"]
        identity = dict(malformed); identity.pop("graph_id")
        from raveil.command_graph import _canonical, _digest
        malformed["graph_id"] = f"command-{_digest(_canonical(identity))[:16]}"
        rebuilt = CommandGraphProgram.from_dict(malformed)
        with self.assertRaisesRegex(ValueError, "writes do not match"):
            CommandComparison(self.workspace, self.registry).execute(rebuilt, publish=False)

        missing_input = program.to_dict()
        missing_input["declared_inputs"] = []
        identity = dict(missing_input); identity.pop("graph_id")
        missing_input["graph_id"] = f"command-{_digest(_canonical(identity))[:16]}"
        rebuilt_input = CommandGraphProgram.from_dict(missing_input)
        with self.assertRaisesRegex(ValueError, "inputs do not match"):
            CommandComparison(self.workspace, self.registry).execute(rebuilt_input, publish=False)

        policy = ExecutionPolicy(timeout_ms=321, max_capture_bytes=1024)
        bounded = CommandGraphCompiler(self.workspace, self.registry, policy).compile("cat /input.txt")
        with mock.patch("raveil.command_graph.subprocess.Popen") as popen:
            popen.return_value.pid = 999999
            popen.return_value.communicate.side_effect = subprocess_timeout()
            CommandComparison(self.workspace, self.registry).execute(bounded, publish=False)
        self.assertEqual(popen.return_value.communicate.call_args.kwargs["timeout"], 0.321)

    def test_preregistered_workload_families_have_real_oracles(self) -> None:
        ids = {item.workload_id for item in preregistered_workloads(12)}
        self.assertTrue({"sequential-text", "sort-deduplicate", "transform-head",
                         "hash-fanout", "multi-input-filter", "missing-input",
                         "grep-no-match", "output-collision", "injected-timeout",
                         "injected-stale-tool"}.issubset(ids))
        for workload in preregistered_workloads(12):
            with self.subTest(workload=workload.workload_id), tempfile.TemporaryDirectory() as directory:
                workspace = NativeWorkspace(Path(directory)); workload.generate(workspace)
                registry = ToolRegistry(); compiler = CommandGraphCompiler(workspace, registry)
                if workload.expected_status == "compile-failed":
                    with self.assertRaises(WorkspaceError): compiler.compile(workload.source)
                    continue
                program = compiler.compile(workload.source)
                if workload.expected_status == "injected-timeout":
                    with mock.patch("raveil.command_graph.subprocess.Popen") as popen:
                        popen.return_value.pid = 999999
                        popen.return_value.communicate.side_effect = subprocess_timeout()
                        result = CommandComparison(workspace, registry).execute(program, publish=False)
                    self.assertFalse(result.semantic_valid)
                    self.assertEqual(result.direct.status, "timeout")
                    continue
                if workload.expected_status == "injected-stale-tool":
                    stale_tool = replace(program.nodes[0].tool, binary_sha256="f" * 64)
                    provisional = replace(program, graph_id="pending", nodes=(replace(program.nodes[0], tool=stale_tool),))
                    stale = replace(provisional, graph_id=f"command-{provisional.identity[:16]}")
                    with self.assertRaisesRegex(ValueError, "tool identity"):
                        CommandComparison(workspace, registry).execute(stale, publish=False)
                    continue
                result = CommandComparison(workspace, registry).execute(program, publish=False)
                if workload.expected_status == "executed":
                    self.assertTrue(result.semantic_valid)
                    if workload.expected_stdout_sha256 is not None:
                        self.assertEqual(result.direct.to_dict()["stdout_sha256"], workload.expected_stdout_sha256)
                else:
                    self.assertFalse(result.semantic_valid)

    def test_source_contains_no_shell_true_or_shell_command_runner(self) -> None:
        source = (ROOT / "raveil/command_graph.py").read_text()
        self.assertNotIn("shell=True", source)
        self.assertNotIn("sh -c", source)


def subprocess_timeout() -> Exception:
    import subprocess
    return subprocess.TimeoutExpired(["cat"], 1)


class CommandGraphInteractiveTests(unittest.TestCase):
    def test_manual_transcript_uses_real_tools_and_exclusive_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session = NativeInteractiveSession(
                source=ROOT / "benchmarks/native/benchmark.c", workspace=NativeWorkspace(root)
            )
            dispatch(session, 'write /input.txt "INFO start\\nERROR failed\\nERROR retry\\n"')
            self.assertEqual(dispatch(session, "run cat /input.txt | grep ERROR | wc -l")[1], "2")
            compiled = dispatch(session, "graph compile cat /input.txt | grep ERROR | wc -l")[1]
            self.assertIn("nodes=3 edges=2", compiled)
            shown = json.loads(dispatch(session, "graph show")[1])
            self.assertEqual(shown["schema"], "raveil.command-graph-program/v1")
            compared = dispatch(session, "graph execute --compare")[1]
            self.assertIn("semantic=valid", compared)
            benchmark_text = dispatch(session, "graph benchmark --warmups 0 --repetitions 2")[1]
            self.assertIn("benchmark=development-non-claim", benchmark_text)
            dispatch(session, "graph result /command-result.json")
            result = json.loads((root / "command-result.json").read_text())
            self.assertEqual(result["schema"], "raveil.command-graph-result/v1")
            self.assertTrue(result["semantic_valid"])
            with self.assertRaises(WorkspaceError):
                dispatch(session, "graph result /command-result.json")


if __name__ == "__main__":
    unittest.main()
