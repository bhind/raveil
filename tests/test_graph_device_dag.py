import copy
import hashlib
import json
import struct
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
    load_descriptor,
    load_program_abi,
    prepare,
    programs,
    software_fallback,
    validate_descriptor,
    validate_lowering_trace,
)
from raveil.riscv_stencil_signature import input_words


ROOT = Path(__file__).resolve().parents[1]
CHISEL = ROOT / "hardware" / "chisel"


class GraphDeviceDagTests(unittest.TestCase):
    def test_forward_references_are_stably_scheduled_without_changing_semantics(self) -> None:
        ordered = copy.deepcopy(descriptors()[1])
        expected = compile_descriptor(ordered)
        nodes = ordered["nodes"]
        permuted = copy.deepcopy(ordered)
        permuted["graph_id"] = "forward-reference-horizontal"
        permuted["nodes"] = [
            nodes[2], nodes[0], nodes[1], nodes[3], nodes[4], nodes[5],
        ]

        actual = compile_descriptor(permuted)
        self.assertEqual(actual["instruction_count"], expected["instruction_count"])
        self.assertEqual(
            [entry["node_id"] for entry in actual["lowering_trace"]["instructions"]],
            [node["id"] for node in ordered["nodes"]],
        )
        self.assertNotEqual(
            actual["lowering_trace"]["descriptor_canonical_sha256"],
            expected["lowering_trace"]["descriptor_canonical_sha256"],
        )
        validate_lowering_trace(
            permuted, actual["lowering_trace"], actual["instructions"]
        )
        words = input_words(5)
        self.assertEqual(graph_oracle(permuted, words), graph_oracle(ordered, words))
        self.assertEqual(graph_oracle(permuted, words), software_fallback(actual, words))

    def test_forward_reference_trace_still_fails_closed(self) -> None:
        descriptor = copy.deepcopy(descriptors()[1])
        nodes = descriptor["nodes"]
        descriptor["nodes"] = [
            nodes[2], nodes[0], nodes[1], nodes[3], nodes[4], nodes[5],
        ]
        program = compile_descriptor(descriptor)
        malformed = copy.deepcopy(program["lowering_trace"])
        malformed["instructions"][0], malformed["instructions"][1] = (
            malformed["instructions"][1], malformed["instructions"][0]
        )
        with self.assertRaisesRegex(GraphDeviceDagError, "descriptor or words"):
            validate_lowering_trace(descriptor, malformed, program["instructions"])

    def test_unknown_cyclic_and_store_dependencies_fail_closed(self) -> None:
        for expected, mutate in (
            ("node identity", lambda nodes: nodes[1].__setitem__("id", "center")),
            ("undefined operand", lambda nodes: nodes[2].__setitem__(
                "inputs", ["center", "missing"]
            )),
            ("cycle", lambda nodes: (
                nodes[2].__setitem__("inputs", ["center", "sum1"]),
                nodes[4].__setitem__("inputs", ["sum0", "east"]),
            )),
            ("cannot be an operand", lambda nodes: nodes[2].__setitem__(
                "inputs", ["center", "store"]
            )),
        ):
            with self.subTest(expected=expected):
                descriptor = copy.deepcopy(descriptors()[1])
                mutate(descriptor["nodes"])
                with self.assertRaisesRegex(GraphDeviceDagError, expected):
                    compile_descriptor(descriptor)
        descriptor = copy.deepcopy(descriptors()[1])
        descriptor["nodes"][-2], descriptor["nodes"][-1] = (
            descriptor["nodes"][-1], descriptor["nodes"][-2]
        )
        with self.assertRaisesRegex(GraphDeviceDagError, "exactly one final"):
            compile_descriptor(descriptor)

    def test_v3_relative_loads_cover_all_eight_neighbors(self) -> None:
        path = ROOT / "tests/fixtures/graph_device_dynamic/eight-neighbor-dilation-u32.json"
        descriptor = json.loads(path.read_text(encoding="ascii"))
        program = compile_descriptor(descriptor)
        self.assertEqual(descriptor["schema"], "raveil.graph-device-dag/v2")
        self.assertEqual(program["payload"][1], 3)
        self.assertEqual(program["instruction_count"], 16)
        addresses = [
            node["address"] for node in descriptor["nodes"]
            if node["op"] == "LOAD_U32"
        ]
        self.assertEqual(
            {(value["row_delta"], value["column_delta"]) for value in addresses},
            {(row, column) for row in (-1, 0, 1) for column in (-1, 0, 1)
             if (row, column) != (0, 0)},
        )
        self.assertEqual(sum(node["op"] == "MAX_U32" for node in descriptor["nodes"]), 7)
        words = input_words(9)
        self.assertEqual(graph_oracle(descriptor, words), software_fallback(program, words))
        self.assertEqual(len(expected_transactions(program, words)), 8 * 64 + 64)

    def test_v2_descriptor_rejects_non_unit_or_malformed_coordinates(self) -> None:
        path = ROOT / "tests/fixtures/graph_device_dynamic/eight-neighbor-dilation-u32.json"
        descriptor = json.loads(path.read_text(encoding="ascii"))
        for address in (
            {"row_delta": 2, "column_delta": 0},
            {"row_delta": 0, "column_delta": -2},
            {"row_delta": True, "column_delta": 0},
            {"row_delta": 0},
        ):
            with self.subTest(address=address):
                malformed = copy.deepcopy(descriptor)
                malformed["nodes"][0]["address"] = address
                with self.assertRaisesRegex(GraphDeviceDagError, "relative address"):
                    validate_descriptor(malformed)

    def test_compiler_owns_deterministic_word_bound_lowering_trace(self) -> None:
        fanout_path = ROOT / "tests/fixtures/graph_device_dynamic/fanout-five-live.json"
        descriptor = json.loads(fanout_path.read_text(encoding="ascii"))
        first = compile_descriptor(descriptor)
        second = compile_descriptor(descriptor)
        self.assertEqual(first["lowering_trace"], second["lowering_trace"])
        self.assertEqual(
            first["program_sha256"],
            "ec13f9f0d376233b49b2d647088f71bf208ddea68e7a4d09732f660b9770ea39",
        )
        trace = first["lowering_trace"]
        self.assertEqual(trace["program_sha256"], first["program_sha256"])
        self.assertEqual(trace["instruction_count"], len(first["instructions"]))
        a0 = next(item for item in trace["instructions"] if item["node_id"] == "a0")
        self.assertEqual(a0["fan_out"], 2)
        self.assertEqual(a0["consumers"], ["a2", "a4"])
        self.assertEqual(a0["definition_index"], 5)
        self.assertEqual(a0["last_use_index"], 9)
        self.assertEqual(a0["live_range"], [5, 9])
        self.assertEqual(a0["release_after_index"], 9)
        validate_lowering_trace(descriptor, trace, first["instructions"])
        malformed = copy.deepcopy(trace)
        malformed["instructions"][5]["encoded_word"] ^= 1
        with self.assertRaisesRegex(GraphDeviceDagError, "descriptor or words"):
            validate_lowering_trace(descriptor, malformed, first["instructions"])

    def test_garden_explanation_fixture_retains_exact_compiler_output(self) -> None:
        descriptor = json.loads((
            ROOT / "tests/fixtures/graph_device_dynamic/cross-dilation-u32.json"
        ).read_text(encoding="ascii"))
        program = compile_descriptor(descriptor)
        explanation = json.loads((
            ROOT / "tests/fixtures/garden/dynamic-explanation.json"
        ).read_text(encoding="ascii"))
        self.assertEqual(explanation["lowering"], program["lowering_trace"])
        self.assertEqual(explanation["program_payload"], program["payload"])
        self.assertEqual(
            explanation["identities"]["program_sha256"],
            program["program_sha256"],
        )

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

    def test_v4_mul_wraps_u32_and_rejects_downgrade_or_reserved_bits(self) -> None:
        descriptor = load_descriptor(ROOT / "tests/fixtures/graph_device_dynamic/product-neighbors-u32.json")
        program = compile_descriptor(descriptor)
        self.assertEqual(program["payload"][1], 4)
        for left, right, expected in ((0, 7, 0), (1, 0xFFFFFFFF, 0xFFFFFFFF),
                                      (0xFFFFFFFF, 0xFFFFFFFF, 1), (0xFFFFFFFF, 2, 0xFFFFFFFE)):
            words = [0] * 324
            words[19] = left
            words[20] = right
            self.assertEqual(graph_oracle(descriptor, words)[0], expected)
            self.assertEqual(software_fallback(program, words)[0], expected)
        downgraded = copy.deepcopy(program)
        downgraded["payload"][1] = 3
        with self.assertRaises(GraphDeviceDagError):
            software_fallback(downgraded, [0] * 324)
        reserved = copy.deepcopy(program)
        reserved["instructions"][2] |= 1
        reserved["payload"][12 + 2] = reserved["instructions"][2]
        encoded = struct.pack("<5I", 4, *reserved["instructions"])
        reserved["program_sha256"] = hashlib.sha256(encoded).hexdigest()
        reserved["payload"][4:12] = struct.unpack("<8I", hashlib.sha256(encoded).digest())
        with self.assertRaisesRegex(GraphDeviceDagError, "arithmetic"):
            software_fallback(reserved, [0] * 324)

    def test_mul_is_rejected_by_legacy_descriptor_schema_and_v4_allows_max(self) -> None:
        descriptor = load_descriptor(ROOT / "tests/fixtures/graph_device_dynamic/product-neighbors-u32.json")
        legacy = copy.deepcopy(descriptor)
        legacy["schema"] = "raveil.graph-device-dag/v2"
        with self.assertRaisesRegex(GraphDeviceDagError, "schema v3"):
            validate_descriptor(legacy)
        mixed = copy.deepcopy(descriptor)
        mixed["nodes"].insert(-1, {"id": "m", "inputs": ["p", "c"], "op": "MAX_U32"})
        mixed["nodes"][-1]["input"] = "m"
        compiled = compile_descriptor(mixed)
        self.assertEqual(compiled["payload"][1], 4)
        self.assertEqual(graph_oracle(mixed, [3] * 324)[0], 9)
        self.assertEqual(software_fallback(compiled, [3] * 324), graph_oracle(mixed, [3] * 324))

    def test_v1_and_v2_program_identities_remain_stable(self) -> None:
        fanout = compile_descriptor(load_descriptor(
            ROOT / "tests/fixtures/graph_device_dynamic/fanout-five-live.json"
        ))
        dilation = compile_descriptor(load_descriptor(
            ROOT / "tests/fixtures/graph_device_dynamic/cross-dilation-u32.json"
        ))
        self.assertEqual(
            fanout["program_sha256"],
            "ec13f9f0d376233b49b2d647088f71bf208ddea68e7a4d09732f660b9770ea39",
        )
        self.assertEqual(fanout["payload"][1], 1)
        self.assertEqual(dilation["payload"][1], 2)

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
