from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_dag import (
    GraphDeviceDagError,
    _generated_header,
    compile_artifact,
    expected_transactions,
    finalize,
)
from raveil.graph_device_playable import parse_marker, render, validate
from raveil.riscv_stencil_signature import input_words


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii") + b"\n"


class PlayableValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.artifact = compile_artifact()
        artifact_raw = _canonical(self.artifact)
        (self.root / "dag-artifact.json").write_bytes(artifact_raw)
        hashes_raw = ("1" * 64 + "\n" + "2" * 64 + "\n").encode("ascii")
        (self.root / "rtl-first.hashes").write_bytes(hashes_raw)
        (self.root / "rtl-second.hashes").write_bytes(hashes_raw)
        self.rtl_identity = hashlib.sha256(hashes_raw).hexdigest()
        (self.root / "rtl-export.sha256").write_text(
            self.rtl_identity + "\n", encoding="ascii"
        )
        (self.root / "graph_device_dag_generated.h").write_bytes(
            _generated_header(self.artifact)
        )
        (self.root / "device.log").write_text(
            "GraphDevice-DAG-RUNTIME-V1 status=OK graphs=3 completed=4 "
            "cancelled=1 invalid_cases=8\n",
            encoding="ascii",
        )
        (self.root / "simulator.sha256").write_text("3" * 64 + "\n", encoding="ascii")
        (self.root / "environment.txt").write_text(
            "schema=raveil.graph-device-dag-environment/v1\n",
            encoding="ascii",
        )
        (self.root / "dag-oracles").mkdir()
        by_id = {graph["graph_id"]: graph for graph in self.artifact["graphs"]}
        for invocation in self.artifact["invocations"]:
            graph_id = invocation["graph_id"]
            seed = invocation["seed"]
            output = f"{graph_id}:{seed}".encode("ascii")
            oracle = self.root / "dag-oracles" / f"{graph_id}-seed-{seed}.bin"
            oracle.write_bytes(output)
            (self.root / f"fallback-output-{graph_id}-seed-{seed}.bin").write_bytes(output)
            if invocation["mode"] != "cancel":
                (self.root / f"private-output-{graph_id}-seed-{seed}.bin").write_bytes(output)

        def event(name: str) -> str:
            return f"GraphDevice-TRACE-V1 event={name}\n"

        def transactions(items) -> str:
            return "".join(
                "GraphDevice-TRACE-V1 event=transaction "
                f"write={int(item['write'])} address={item['address']} "
                f"data={item['data']:08x}\n"
                for item in items
            )

        invocation_transactions = [
            expected_transactions(by_id[item["graph_id"]], input_words(item["seed"]))
            for item in self.artifact["invocations"]
        ]
        trace = event("reset") * 8
        trace += event("start") + transactions(invocation_transactions[0][:1])
        trace += event("cancel") + event("reset") + event("reset")
        trace += event("start") + transactions(invocation_transactions[0]) + event("reset")
        trace += event("start") + transactions(invocation_transactions[1]) + event("reset")
        trace += event("start") + transactions(invocation_transactions[2][:3]) + event("cancel")
        trace += event("reset")
        trace += event("start") + transactions(invocation_transactions[3]) + event("reset")
        trace += event("start") + transactions(invocation_transactions[4])
        (self.root / "transaction-trace.txt").write_text(trace, encoding="ascii")
        self.receipt = finalize(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_receipt(self) -> None:
        (self.root / "dag-receipt.json").write_bytes(_canonical(self.receipt))

    def _reject_receipt(self, mutate) -> None:
        original = deepcopy(self.receipt)
        mutate(self.receipt)
        self._write_receipt()
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)
        self.receipt = original
        self._write_receipt()

    def test_render_is_deterministic_and_shows_capability_only(self) -> None:
        first = render(self.root)
        self.assertEqual(first, render(self.root))
        self.assertEqual(first.count("RTL=PASS oracle=PASS fallback=PASS"), 3)
        for graph in self.artifact["graphs"]:
            self.assertIn(graph["graph_id"], first)
        self.assertIn(f"shared RTL sha256={self.rtl_identity}", first)
        self.assertIn("performance=not-measured", first)
        self.assertIn("fixed baseline=five-point-only", first)
        for metric in ("cycles=", "speedup=", "latency=", "area=", "energy="):
            self.assertNotIn(metric, first)

    def test_parse_marker_accepts_only_the_private_unpublished_run_path(self) -> None:
        marker = (
            "GraphDevice-DAG-EVIDENCE-V1 "
            "path=artifacts/graph_device_dag/run.Ab12Z9 private=1 publication=0"
        )
        self.assertEqual(
            parse_marker(marker), Path("artifacts/graph_device_dag/run.Ab12Z9")
        )

    def test_parse_marker_rejects_malformed_or_escaping_values(self) -> None:
        invalid = (
            "",
            "GraphDevice-DAG-EVIDENCE-V1 path=artifacts/graph_device_dag/run.abc123 private=1",
            "GraphDevice-DAG-EVIDENCE-V1 path=artifacts/graph_device_dag/run.abc123 private=1 publication=0 extra=1",
            "GraphDevice-DAG-EVIDENCE-V1 path=artifacts/graph_device_dag/../../x private=1 publication=0",
            "GraphDevice-DAG-EVIDENCE-V1 path=artifacts/graph_device_dag/run.abc12 private=1 publication=0",
            "GraphDevice-DAG-EVIDENCE-V1 path=artifacts/graph_device_dag/run.abc123 private=0 publication=0",
        )
        for marker in invalid:
            with self.subTest(marker=marker), self.assertRaises(GraphDeviceDagError):
                parse_marker(marker)

    def test_rejects_receipt_envelope_drift(self) -> None:
        for field, value in (
            ("schema", "wrong"),
            ("status", "partial"),
            ("evidence_class", "host-functional"),
            ("performance", "measured"),
        ):
            with self.subTest(field=field):
                self._reject_receipt(
                    lambda receipt, f=field, v=value: receipt.__setitem__(f, v)
                )

    def test_rejects_receipt_field_addition(self) -> None:
        self._reject_receipt(lambda receipt: receipt.__setitem__("cycles", 1))

    def test_rejects_artifact_or_receipt_identity_drift(self) -> None:
        self._reject_receipt(
            lambda receipt: receipt.__setitem__("artifact_sha256", "0" * 64)
        )
        artifact = deepcopy(self.artifact)
        artifact["graphs"][0]["instruction_count"] += 1
        (self.root / "dag-artifact.json").write_bytes(_canonical(artifact))
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_duplicate_graph_identity(self) -> None:
        artifact = deepcopy(self.artifact)
        artifact["graphs"][1]["graph_id"] = artifact["graphs"][0]["graph_id"]
        (self.root / "dag-artifact.json").write_bytes(_canonical(artifact))
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_duplicate_program_identity(self) -> None:
        artifact = deepcopy(self.artifact)
        artifact["graphs"][1]["program_sha256"] = artifact["graphs"][0]["program_sha256"]
        (self.root / "dag-artifact.json").write_bytes(_canonical(artifact))
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_missing_completed_graph(self) -> None:
        self._reject_receipt(lambda receipt: receipt["runs"].pop(3))

    def test_rejects_private_output_oracle_mismatch(self) -> None:
        self._reject_receipt(
            lambda receipt: receipt["runs"][0].__setitem__(
                "private_output_sha256", "0" * 64
            )
        )

    def test_rejects_required_agreement_flag_drift(self) -> None:
        for field in (
            "same_executor_rtl",
            "generic_fallback",
            "invalid_programs_rejected",
            "transaction_addresses_match",
            "store_data_oracle_match",
        ):
            with self.subTest(field=field):
                self._reject_receipt(
                    lambda receipt, f=field: receipt.__setitem__(f, False)
                )

    def test_rejects_first_second_rtl_mismatch(self) -> None:
        (self.root / "rtl-second.hashes").write_text("3" * 64 + "\n", encoding="ascii")
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_empty_or_malformed_rtl_file_identity(self) -> None:
        for value in (b"", b"not-a-hash\n"):
            with self.subTest(value=value):
                (self.root / "rtl-first.hashes").write_bytes(value)
                (self.root / "rtl-second.hashes").write_bytes(value)
                with self.assertRaises(GraphDeviceDagError):
                    validate(self.root)

    def test_rejects_aggregate_rtl_identity_mismatch(self) -> None:
        (self.root / "rtl-export.sha256").write_text("0" * 64 + "\n", encoding="ascii")
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_cancelled_output_publication(self) -> None:
        self._reject_receipt(
            lambda receipt: receipt["runs"][2].__setitem__(
                "private_output_sha256", "6" * 64
            )
        )

    def test_rejects_lifecycle_mode_substitution(self) -> None:
        self._reject_receipt(
            lambda receipt: receipt["runs"][1].__setitem__("mode", "restart")
        )

    def test_rejects_raw_trace_substitution(self) -> None:
        with (self.root / "transaction-trace.txt").open("a", encoding="ascii") as stream:
            stream.write("GraphDevice-TRACE-V1 event=reset\n")
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_raw_output_substitution(self) -> None:
        output = self.root / "private-output-five-point-seed-1.bin"
        output.write_bytes(output.read_bytes() + b"changed")
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)

    def test_rejects_symbolic_link_in_evidence(self) -> None:
        link = self.root / "unexpected-link"
        try:
            link.symlink_to(self.root / "dag-artifact.json")
        except OSError as error:
            self.skipTest(f"symbolic links unavailable: {error}")
        with self.assertRaises(GraphDeviceDagError):
            validate(self.root)


if __name__ == "__main__":
    unittest.main()
