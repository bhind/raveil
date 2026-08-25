from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_mvp import finalize as finalize_graph_device

from raveil.graph_device_schedule import (
    RECEIPT_SCHEMA,
    T0123ScheduleError,
    compile_generated_schedule,
    expected_transactions,
    finalize,
    prepare,
    source_id,
    validate_generated_schedule,
)


ROOT = Path(__file__).resolve().parents[1]
CHISEL = ROOT / "hardware" / "chisel"


class GraphDeviceGeneratedScheduleTests(unittest.TestCase):
    def _prepared(self, root: Path) -> Path:
        evidence = root / "evidence"
        prepare(evidence)
        artifact = json.loads((evidence / "artifact.json").read_text())
        lines = [
            "GraphDevice-ABI-V1 status=OK identity=52560101 "
            f"descriptor={artifact['descriptor_sha256']} "
            f"configuration={artifact['configuration_sha256']} "
            f"implementation={artifact['implementation_sha256']}",
        ]
        for seed in (1, 2):
            oracle = evidence / "oracles" / f"seed-{seed}.bin"
            output = evidence / f"private-output-seed-{seed}.bin"
            output.write_bytes(oracle.read_bytes())
            words = [
                int.from_bytes(oracle.read_bytes()[index:index + 4], "little")
                for index in range(0, oracle.stat().st_size, 4)
            ]
            lines.append(
                f"GraphDevice-RUN-{seed}-V1 status=COMPLETED staged_words=324 "
                f"polls=3073 output_valid=1 output_words=256 "
                f"checksum={sum(words) & 0xffffffffffffffff:016x}"
            )
        lines.extend([
            "GraphDevice-CANCEL-V1 seed=3 status=CANCELLED output_valid=0 "
            "output_words=0 blocked_read=1 published=0",
            "GraphDevice-RESET-RESTART-V1 status=OK seed=2",
            "GraphDevice-DEVICE-RUNTIME-V1 status=OK completed=2 cancelled=1 "
            "resets=2 evidence=rtl-simulation-functional performance=not-measured",
        ])
        (evidence / "device.log").write_text(
            "\n".join(lines) + "\n", encoding="ascii"
        )
        (evidence / "simulator.sha256").write_text("a" * 64 + "\n", encoding="ascii")
        (evidence / "environment.txt").write_text(
            "schema=raveil.graph-device-schedule-environment/v1\n"
            "platform=linux/amd64\n",
            encoding="ascii",
        )
        finalize_graph_device(evidence)
        return evidence

    def _write_receipt(self, evidence: Path, receipt: dict[str, object]) -> None:
        (evidence / "receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="ascii",
        )

    def _trace_line(self, transaction: dict[str, object]) -> str:
        data = transaction["data"] if transaction["data"] is not None else 0
        return (
            "GraphDevice-TRACE-V1 event=transaction "
            f"write={int(bool(transaction['write']))} "
            f"address={transaction['address']} data={int(data):08x}"
        )

    def _complete_trace(self, evidence: Path) -> None:
        schedule = compile_generated_schedule()
        lines = ["GraphDevice-TRACE-V1 event=reset", "GraphDevice-TRACE-V1 event=start"]
        lines.extend(self._trace_line(item) for item in expected_transactions(schedule, 1))
        lines.append("GraphDevice-TRACE-V1 event=start")
        lines.extend(
            self._trace_line(item) for item in expected_transactions(schedule, 3)[:5]
        )
        lines.extend([
            "GraphDevice-TRACE-V1 event=cancel",
            "GraphDevice-TRACE-V1 event=reset",
            "GraphDevice-TRACE-V1 event=start",
        ])
        lines.extend(self._trace_line(item) for item in expected_transactions(schedule, 2))
        (evidence / "transaction-trace.txt").write_text(
            "\n".join(lines) + "\n", encoding="ascii"
        )

    def test_compiler_emits_canonical_immutable_existing_schedule(self) -> None:
        first = compile_generated_schedule()
        second = compile_generated_schedule()
        self.assertEqual(first, second)
        validate_generated_schedule(first)
        self.assertEqual(first["schema"], "raveil.graph-device-generated-schedule/v1")
        self.assertEqual(first["slice"], "S01")
        self.assertEqual(len(first["abi_sha256"]), 64)
        self.assertEqual(first["internal_scratchpad_mapping"]["input_words"]["base_word"], 0)
        self.assertEqual(first["internal_scratchpad_mapping"]["output_words"]["base_word"], 324)
        self.assertEqual(first["internal_scratchpad_mapping"]["host_abi_input_offset"], 256)
        self.assertEqual(first["internal_scratchpad_mapping"]["host_abi_output_offset"], 1024)
        self.assertEqual(first["source_sha256"], source_id())
        self.assertEqual(len(first["schedule"]), 10)
        self.assertEqual(len(first["transaction_template"]), 6)
        self.assertEqual(
            [item["node"] for item in first["transaction_template"]],
            [
                "load_center", "load_north", "load_south",
                "load_west", "load_east", "store_output",
            ],
        )
        changed = json.loads(json.dumps(first))
        changed["schedule"][0]["node"] = "load_north"
        with self.assertRaisesRegex(T0123ScheduleError, "content or identity"):
            validate_generated_schedule(changed)

    def test_expected_trace_is_bounded_and_matches_owned_memory_layout(self) -> None:
        transactions = expected_transactions(compile_generated_schedule(), 1)
        self.assertEqual(len(transactions), 1536)
        self.assertEqual(
            [(item["write"], item["address"]) for item in transactions[:6]],
            [(False, 19), (False, 1), (False, 37), (False, 18), (False, 20), (True, 324)],
        )
        self.assertEqual(sum(item["write"] for item in transactions), 256)
        self.assertTrue(all(0 <= int(item["address"]) < 580 for item in transactions))

    def test_prepare_binds_graph_device_artifact_and_generated_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            schedule = prepare(evidence)
            self.assertTrue((evidence / "artifact.json").is_file())
            self.assertTrue((evidence / "generated-schedule.json").is_file())
            self.assertEqual(
                json.loads((evidence / "generated-schedule.json").read_text()), schedule
            )

    def test_finalizer_proves_complete_traces_cancel_prefix_and_append_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_trace(evidence)
            receipt = finalize(evidence)
            self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
            self.assertEqual(receipt["completed_transaction_counts"], [1536, 1536])
            self.assertEqual(receipt["cancelled_transaction_count"], 5)
            self.assertTrue(receipt["transaction_trace_equivalent"])
            self.assertTrue(receipt["store_data_oracle_match"])
            self.assertFalse(receipt["schedule_consumed_by_executor"])
            self.assertEqual(len(receipt["artifact_sha256"]), 64)
            self.assertEqual(len(receipt["simulator_sha256"]), 64)
            self.assertEqual(len(receipt["environment_sha256"]), 64)
            self.assertEqual(len(receipt["run_input_sha256"]), 2)
            self.assertEqual(len(receipt["run_oracle_sha256"]), 2)
            self.assertEqual(len(receipt["run_output_sha256"]), 2)
            with self.assertRaisesRegex(T0123ScheduleError, "append-once"):
                finalize(evidence)

    def test_trace_address_and_store_data_mismatches_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_trace(evidence)
            trace = (evidence / "transaction-trace.txt").read_text()
            trace = trace.replace("address=19", "address=20", 1)
            (evidence / "transaction-trace.txt").write_text(trace, encoding="ascii")
            with self.assertRaisesRegex(T0123ScheduleError, "schedule mismatch"):
                finalize(evidence)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_trace(evidence)
            trace = (evidence / "transaction-trace.txt").read_text()
            store_line = next(line for line in trace.splitlines() if "write=1" in line)
            changed = store_line[:-1] + ("0" if store_line[-1] != "0" else "1")
            trace = trace.replace(store_line, changed, 1)
            (evidence / "transaction-trace.txt").write_text(trace, encoding="ascii")
            with self.assertRaisesRegex(T0123ScheduleError, "store data mismatch"):
                finalize(evidence)

    def test_minimal_or_tampered_prerequisite_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_trace(evidence)
            minimal = {
                "schema": "raveil.graph-device-simulation-receipt/v1",
                "status": "complete",
                "evidence_class": "rtl-simulation-functional",
                "abi_sha256": "a" * 64,
                "runs": [{"seed": 1, "oracle_match": True}, {"seed": 2, "oracle_match": True}],
                "cancel": {"seed": 3, "cancelled": True},
                "reset_restart": {"passed": True},
            }
            self._write_receipt(evidence, minimal)
            with self.assertRaisesRegex(T0123ScheduleError, "receipt fields"):
                finalize(evidence)

        mutations = (
            ("artifact_sha256", "0" * 64),
            ("abi_sha256", "0" * 64),
            ("descriptor_sha256", "0" * 64),
            ("configuration_sha256", "0" * 64),
            ("implementation_sha256", "0" * 64),
            ("source_sha256", "0" * 64),
            ("simulator_sha256", "0" * 64),
            ("environment_sha256", "0" * 64),
        )
        for field, replacement in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                self._complete_trace(evidence)
                receipt = json.loads((evidence / "receipt.json").read_text())
                receipt[field] = replacement
                self._write_receipt(evidence, receipt)
                with self.assertRaisesRegex(T0123ScheduleError, field):
                    finalize(evidence)

    def test_run_cancel_and_payload_tamper_fail_closed(self) -> None:
        receipt_mutations = (
            ("run publication", lambda receipt: receipt["runs"][0].__setitem__("published", True)),
            ("run input hash", lambda receipt: receipt["runs"][0].__setitem__("input_sha256", "0" * 64)),
            ("run oracle hash", lambda receipt: receipt["runs"][1].__setitem__("oracle_sha256", "0" * 64)),
            ("cancel publication", lambda receipt: receipt["cancel"].__setitem__("published", True)),
            ("cancel output valid", lambda receipt: receipt["cancel"].__setitem__("output_valid", True)),
            ("restart seed", lambda receipt: receipt["reset_restart"].__setitem__("restart_seed", 1)),
        )
        for label, mutate in receipt_mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                self._complete_trace(evidence)
                receipt = json.loads((evidence / "receipt.json").read_text())
                mutate(receipt)
                self._write_receipt(evidence, receipt)
                with self.assertRaises(T0123ScheduleError):
                    finalize(evidence)

        payloads = (
            "inputs/seed-1.bin",
            "oracles/seed-2.bin",
            "private-output-seed-1.bin",
            "environment.txt",
            "simulator.sha256",
            "artifact.json",
        )
        for relative in payloads:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                self._complete_trace(evidence)
                path = evidence / relative
                payload = bytearray(path.read_bytes())
                payload[0] ^= 1
                path.write_bytes(payload)
                with self.assertRaises(T0123ScheduleError):
                    finalize(evidence)

    def test_trace_schema_numeric_lifecycle_and_count_drift_fail_closed(self) -> None:
        def replace_first(text: str, old: str, new: str) -> str:
            self.assertIn(old, text)
            return text.replace(old, new, 1)

        def drop_first_transaction(text: str) -> str:
            lines = text.splitlines()
            index = next(
                index for index, line in enumerate(lines) if "event=transaction" in line
            )
            del lines[index]
            return "\n".join(lines) + "\n"

        mutations = (
            ("schema", lambda text: replace_first(text, "GraphDevice-TRACE-V1", "BAD-TRACE-V1")),
            ("duplicate", lambda text: replace_first(text, "write=0", "write=0 write=0")),
            ("nonnumeric", lambda text: replace_first(text, "address=19", "address=x")),
            ("range", lambda text: replace_first(text, "address=19", "address=580")),
            ("extra field", lambda text: replace_first(text, "address=19", "address=19 extra=1")),
            ("outside", lambda text: "GraphDevice-TRACE-V1 event=transaction write=0 address=0 data=00000000\n" + text),
            ("lifecycle", lambda text: replace_first(text, "event=reset", "event=cancel")),
            ("count", drop_first_transaction),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                self._complete_trace(evidence)
                trace_path = evidence / "transaction-trace.txt"
                trace_path.write_text(mutate(trace_path.read_text()), encoding="ascii")
                with self.assertRaises(T0123ScheduleError):
                    finalize(evidence)

    def test_cancel_trace_must_be_nonempty_strict_prefix(self) -> None:
        schedule = compile_generated_schedule()
        cancel_transactions = expected_transactions(schedule, 3)
        for label, count in (("empty", 0), ("complete", len(cancel_transactions))):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                evidence = self._prepared(Path(temporary))
                lines = ["GraphDevice-TRACE-V1 event=reset", "GraphDevice-TRACE-V1 event=start"]
                lines.extend(self._trace_line(item) for item in expected_transactions(schedule, 1))
                lines.append("GraphDevice-TRACE-V1 event=start")
                lines.extend(self._trace_line(item) for item in cancel_transactions[:count])
                lines.extend([
                    "GraphDevice-TRACE-V1 event=cancel",
                    "GraphDevice-TRACE-V1 event=reset",
                    "GraphDevice-TRACE-V1 event=start",
                ])
                lines.extend(self._trace_line(item) for item in expected_transactions(schedule, 2))
                (evidence / "transaction-trace.txt").write_text(
                    "\n".join(lines) + "\n", encoding="ascii"
                )
                with self.assertRaisesRegex(T0123ScheduleError, "strict prefix"):
                    finalize(evidence)

    def test_schedule_abi_and_mapping_drift_fail_closed(self) -> None:
        schedule = compile_generated_schedule()
        for field_path in ("abi", "mapping"):
            with self.subTest(field_path=field_path):
                changed = deepcopy(schedule)
                if field_path == "abi":
                    changed["abi_sha256"] = "0" * 64
                else:
                    changed["internal_scratchpad_mapping"]["output_words"]["base_word"] = 325
                with self.assertRaisesRegex(T0123ScheduleError, "content or identity"):
                    validate_generated_schedule(changed)

    def test_observation_ports_do_not_change_the_owned_device_abi(self) -> None:
        abi = (ROOT / "contracts" / "graph_device_abi_v1.json").read_text()
        core = (
            CHISEL / "chipyard-overlay" / "RaveilStaticStencilCore.scala"
        ).read_text()
        top = (CHISEL / "StaticStencilRegion.scala").read_text()
        wrapper = (CHISEL / "graph_device_verilator.cpp").read_text()
        self.assertNotIn("transactionTrace", abi)
        self.assertIn("transactionTraceValid := requestFire", core)
        self.assertIn("transactionTraceAddress", top)
        self.assertIn("set_transaction_trace", wrapper)
        self.assertIn("io_transactionTraceValid", wrapper)
        self.assertIn("[TRACE_PATH]", wrapper)

    def test_schedule_runner_is_offline_nonclaiming_and_uses_existing_executor(self) -> None:
        outer = CHISEL / "run-graph-device-generated-schedule.sh"
        inner = CHISEL / "run-graph-device-generated-schedule-in-container.sh"
        self.assertNotEqual(outer.stat().st_mode & 0o111, 0)
        self.assertNotEqual(inner.stat().st_mode & 0o111, 0)
        outer_text = outer.read_text()
        inner_text = inner.read_text()
        self.assertIn("--network none", outer_text)
        self.assertIn("no-new-privileges=true", outer_text)
        self.assertIn("raveil.graph_device_mvp finalize", outer_text)
        self.assertIn("raveil.graph_device_schedule finalize", outer_text)
        self.assertIn("RaveilStaticStencilCore.scala", inner_text)
        self.assertIn("transaction-trace.txt", inner_text)
        for text in (outer_text, inner_text):
            self.assertNotIn("performance=measured", text)
            self.assertNotIn("vivado", text.lower())
            self.assertNotIn("bitstream", text.lower())


if __name__ == "__main__":
    unittest.main()
