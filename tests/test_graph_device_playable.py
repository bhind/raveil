from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_dag import (
    EVIDENCE_CLASS,
    GraphDeviceDagError,
    compile_artifact,
)
from raveil.graph_device_playable import NON_CLAIMS, parse_marker, render, validate


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
        by_id = {graph["graph_id"]: graph for graph in self.artifact["graphs"]}
        runs = []
        counts = []
        for invocation in self.artifact["invocations"]:
            graph = by_id[invocation["graph_id"]]
            full_count = (
                graph["affine"]["rows"]
                * graph["affine"]["columns"]
                * graph["transactions_per_output"]
            )
            count = 3 if invocation["mode"] == "cancel" else full_count
            output_id = hashlib.sha256(
                f"{invocation['graph_id']}:{invocation['seed']}".encode("ascii")
            ).hexdigest()
            run = {
                **invocation,
                "program_sha256": graph["program_sha256"],
                "oracle_sha256": output_id,
                "transaction_count": count,
            }
            if invocation["mode"] != "cancel":
                run["private_output_sha256"] = output_id
            runs.append(run)
            counts.append(count)
        self.receipt = {
            "schema": "raveil.graph-device-dag-receipt/v1",
            "status": "complete",
            "task": "T-0123",
            "slice": "S03",
            "evidence_class": EVIDENCE_CLASS,
            "performance": "not-measured",
            "source_sha256": self.artifact["source_sha256"],
            "artifact_sha256": hashlib.sha256(artifact_raw).hexdigest(),
            "execution_abi_sha256": self.artifact["execution_abi_sha256"],
            "affine_abi_sha256": self.artifact["affine_abi_sha256"],
            "program_abi_sha256": self.artifact["program_abi_sha256"],
            "simulator_sha256": "3" * 64,
            "environment_sha256": "4" * 64,
            "transaction_trace_sha256": "5" * 64,
            "busy_mutation_transaction_count": 1,
            "transaction_counts": counts,
            "transaction_addresses_match": True,
            "store_data_oracle_match": True,
            "same_executor_rtl": True,
            "rtl_regenerated_per_graph": False,
            "generic_fallback": True,
            "invalid_programs_rejected": True,
            "cancel_output_published": False,
            "runs": runs,
            "non_claims": NON_CLAIMS,
        }
        self._write_receipt()

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


if __name__ == "__main__":
    unittest.main()
