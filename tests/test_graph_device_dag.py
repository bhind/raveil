import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_dag import (
    GraphDeviceDagError,
    _require_transactions,
    compile_artifact,
    compile_descriptor,
    descriptors,
    expected_transactions,
    finalize,
    graph_oracle,
    load_program_abi,
    prepare,
    programs,
    software_fallback,
)
from raveil.riscv_stencil_signature import input_words


ROOT = Path(__file__).resolve().parents[1]
CHISEL = ROOT / "hardware" / "chisel"


class GraphDeviceDagTests(unittest.TestCase):
    def test_busy_mutation_prefix_allows_empty_but_rejects_completion(self) -> None:
        expected = expected_transactions(programs()[0], input_words(1))
        _require_transactions(
            [], expected, strict_prefix=True, allow_empty_prefix=True
        )
        for malformed in (
            [{**expected[0], "address": expected[0]["address"] + 1}],
            [{**expected[0], "write": True}],
        ):
            with self.assertRaisesRegex(GraphDeviceDagError, "mismatch"):
                _require_transactions(
                    malformed, expected, strict_prefix=True, allow_empty_prefix=True
                )
        with self.assertRaisesRegex(GraphDeviceDagError, "possibly empty"):
            _require_transactions(
                expected, expected, strict_prefix=True, allow_empty_prefix=True
            )

    def test_owned_program_abi_is_exact_and_transport_neutral(self) -> None:
        abi = load_program_abi()
        self.assertEqual(abi["identity_word"], 0x52565001)
        self.assertEqual(abi["max_payload_words"], 32)
        self.assertEqual(abi["max_outstanding_requests"], 1)
        self.assertTrue(abi["pointer_free"])
        encoded = (ROOT / "contracts/graph_device_program_install_abi_v1.json").read_bytes()
        self.assertNotIn(b"chisel", encoded.lower())
        self.assertNotIn(b"verilator", encoded.lower())
        self.assertNotIn(b"linux", encoded.lower())

    def test_three_external_graphs_compile_without_identity_dispatch(self) -> None:
        selected = programs()
        self.assertEqual(
            [item["graph_id"] for item in selected],
            ["five-point", "compact-horizontal-three-point",
             "vertical-three-point"],
        )
        self.assertEqual([item["instruction_count"] for item in selected], [10, 6, 6])
        self.assertEqual([item["transactions_per_output"] for item in selected], [6, 4, 4])
        self.assertEqual(len({tuple(item["instructions"]) for item in selected}), 3)
        self.assertTrue(all(len(item["payload"]) == 32 for item in selected))
        self.assertEqual(selected[1]["affine"]["rows"], 8)
        self.assertEqual(selected[1]["affine"]["input_stride"], 10)
        source = (ROOT / "raveil/graph_device_dag.py").read_text()
        self.assertNotIn('if value["graph_id"]', source)
        self.assertNotIn('if graph_id ==', source)

    def test_direct_oracle_and_compiled_fallback_are_independent_and_equal(self) -> None:
        for descriptor, program in zip(descriptors(), programs()):
            for seed in (1, 7):
                words = input_words(seed)
                self.assertEqual(
                    graph_oracle(descriptor, words),
                    software_fallback(program, words),
                )
        five, horizontal, vertical = descriptors()
        words = input_words(1)
        self.assertNotEqual(graph_oracle(five, words), graph_oracle(horizontal, words))
        self.assertNotEqual(graph_oracle(horizontal, words), graph_oracle(vertical, words))

    def test_expected_transaction_counts_follow_shape_and_program(self) -> None:
        five, horizontal, vertical = programs()
        self.assertEqual(len(expected_transactions(five, input_words(1))), 1536)
        self.assertEqual(len(expected_transactions(horizontal, input_words(1))), 256)
        self.assertEqual(len(expected_transactions(vertical, input_words(1))), 1024)

    def test_undefined_operand_and_unbounded_shape_fail_closed(self) -> None:
        descriptor = json.loads(json.dumps(descriptors()[1]))
        descriptor["nodes"][2]["inputs"][1] = "missing"
        with self.assertRaisesRegex(GraphDeviceDagError, "undefined"):
            compile_descriptor(descriptor)
        descriptor = json.loads(json.dumps(descriptors()[1]))
        descriptor["affine"]["rows"] = 17
        with self.assertRaisesRegex(GraphDeviceDagError, "bounded"):
            compile_descriptor(descriptor)

    def test_executor_is_program_driven_without_graph_identity_branch(self) -> None:
        core = (CHISEL / "chipyard-overlay/RaveilStaticStencilCore.scala").read_text()
        installer = (CHISEL / "GraphDeviceProgramInstaller.scala").read_text()
        self.assertIn("io.program(programCounter)", core)
        self.assertIn("val opcode = instruction(31, 28)", core)
        self.assertNotIn("five-point", core.lower())
        self.assertNotIn("horizontal", core.lower())
        self.assertIn("defined(sourceA)", installer)
        self.assertIn("payload(12)(31, 28)", installer)
        self.assertIn("storeCount === 1.U", installer)

    def test_prepare_and_append_once_receipt_bind_three_graphs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            artifact = prepare(evidence)
            self.assertEqual(artifact, compile_artifact())
            self.assertEqual(len(list((evidence / "dag-programs").glob("*.bin"))), 3)
            self.assertEqual(len(list((evidence / "dag-oracles").glob("*.bin"))), 5)
            (evidence / "rtl-first.hashes").write_text("a" * 64 + "\n", encoding="ascii")
            (evidence / "rtl-second.hashes").write_text("a" * 64 + "\n", encoding="ascii")
            (evidence / "simulator.sha256").write_text("b" * 64 + "\n", encoding="ascii")
            (evidence / "environment.txt").write_text(
                "schema=raveil.graph-device-dag-environment/v1\nplatform=linux/amd64\n",
                encoding="ascii",
            )
            (evidence / "device.log").write_text(
                "GraphDevice-DAG-RUNTIME-V1 status=OK graphs=3 completed=4 "
                "cancelled=1 invalid_cases=8 same_rtl=1 rtl_regeneration=0 "
                "evidence=rtl-simulation-functional performance=not-measured\n",
                encoding="ascii",
            )
            by_id = {item["graph_id"]: item for item in artifact["graphs"]}
            busy_invocation = artifact["invocations"][0]
            busy_transaction = expected_transactions(
                by_id[busy_invocation["graph_id"]], input_words(busy_invocation["seed"])
            )[0]
            trace = ["GraphDevice-TRACE-V1 event=reset"] * 7
            trace.extend([
                "GraphDevice-TRACE-V1 event=reset",
                "GraphDevice-TRACE-V1 event=start",
            ])
            trace.append(
                "GraphDevice-TRACE-V1 event=transaction "
                f"write={int(busy_transaction['write'])} "
                f"address={busy_transaction['address']} "
                f"data={busy_transaction['data']:08x}",
            )
            trace.extend([
                "GraphDevice-TRACE-V1 event=cancel",
                "GraphDevice-TRACE-V1 event=reset",
            ])
            for invocation in artifact["invocations"]:
                graph_id, seed = invocation["graph_id"], invocation["seed"]
                trace.extend([
                    "GraphDevice-TRACE-V1 event=reset",
                    "GraphDevice-TRACE-V1 event=start",
                ])
                transactions = expected_transactions(by_id[graph_id], input_words(seed))
                if invocation["mode"] == "cancel":
                    transactions = transactions[:2]
                for transaction in transactions:
                    trace.append(
                        "GraphDevice-TRACE-V1 event=transaction "
                        f"write={int(transaction['write'])} "
                        f"address={transaction['address']} "
                        f"data={transaction['data']:08x}"
                    )
                if invocation["mode"] == "cancel":
                    trace.append("GraphDevice-TRACE-V1 event=cancel")
                oracle = evidence / "dag-oracles" / f"{graph_id}-seed-{seed}.bin"
                (evidence / f"fallback-output-{graph_id}-seed-{seed}.bin").write_bytes(
                    oracle.read_bytes()
                )
                if invocation["mode"] != "cancel":
                    (evidence / f"private-output-{graph_id}-seed-{seed}.bin").write_bytes(
                        oracle.read_bytes()
                    )
            (evidence / "transaction-trace.txt").write_text(
                "\n".join(trace) + "\n", encoding="ascii"
            )
            receipt = finalize(evidence)
            self.assertEqual(receipt["evidence_class"], "rtl-simulation-functional")
            self.assertTrue(receipt["same_executor_rtl"])
            self.assertFalse(receipt["rtl_regenerated_per_graph"])
            self.assertEqual(len(receipt["runs"]), 5)
            self.assertEqual(receipt["busy_mutation_transaction_count"], 1)
            self.assertEqual(receipt["transaction_counts"], [1536, 256, 2, 1024, 1536])
            with self.assertRaisesRegex(GraphDeviceDagError, "append-once"):
                finalize(evidence)

    def test_runner_invokes_one_offline_rtl_binary_and_is_non_claiming(self) -> None:
        outer = (CHISEL / "run-graph-device-dag.sh").read_text()
        inner = (CHISEL / "run-graph-device-dag-in-container.sh").read_text()
        self.assertIn("--network none", outer)
        self.assertEqual(inner.count("verilator --assert --cc"), 1)
        self.assertIn("graph_device_dag_runtime.cpp", inner)
        self.assertIn("--dag", inner)
        for text in (outer, inner):
            self.assertNotIn("vivado", text.lower())
            self.assertNotIn("bitstream", text.lower())
            self.assertNotIn("performance=measured", text)


if __name__ == "__main__":
    unittest.main()
