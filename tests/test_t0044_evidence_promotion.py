from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from raveil.t0044_evidence_promotion import (
    BASE_MANIFEST_SHA256,
    EvidenceContract,
    EXP_ID,
    FAILED_RUN_ID,
    PromotionError,
    RECOVERY_RUN_ID,
    promote_evidence,
    validate_receipt,
    verify_evidence,
)


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _seal(raw: Path, schema: str, report_hash: str | None = None) -> dict[str, object]:
    files = [
        {
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path in sorted(raw.iterdir())
        if path.is_file()
    ]
    value: dict[str, object] = {"schema": schema, "files": files}
    if report_hash is not None:
        value["derived_report_sha256"] = report_hash
    return value


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.artifact_root = self.repo / "artifacts" / "research"
        self.failed = self.artifact_root / EXP_ID / FAILED_RUN_ID
        self.recovery = self.artifact_root / EXP_ID / RECOVERY_RUN_ID
        self.base_manifest = self.repo / "benchmarks" / "base.json"
        self.recovery_manifest = self.repo / "benchmarks" / "recovery.json"
        self.receipt = self.repo / "docs" / "experiments" / "receipts" / "receipt.json"
        self.config = root / "rclone.conf"
        self.repo.mkdir()
        self.config.write_text("[fake]\ntype = local\n", encoding="utf-8")
        self.config.chmod(0o600)

        base_value = {
            "schema": "test-base/v1",
            "experiment_id": EXP_ID,
            "sampling": {"run_id": FAILED_RUN_ID},
        }
        _write_json(self.base_manifest, base_value)
        failed_raw = self.failed / "raw"
        failed_raw.mkdir(parents=True)
        (failed_raw / "frozen-manifest.json").write_bytes(self.base_manifest.read_bytes())
        (failed_raw / "primary.log").write_bytes(b"sealed-primary\n")
        (failed_raw / "failure.json").write_bytes(b"failed\n")
        failed_seal = _seal(failed_raw, "raveil.research-failed-raw-seal/v1")
        _write_json(self.failed / "failed-raw-seal.json", failed_seal)
        failed_seal_hash = _sha256(self.failed / "failed-raw-seal.json")

        primary = {
            "test-primary": {
                "path": "primary.log",
                "bytes": (failed_raw / "primary.log").stat().st_size,
                "sha256": _sha256(failed_raw / "primary.log"),
            }
        }
        recovery_value = {
            "schema": "test-recovery/v1",
            "experiment_id": EXP_ID,
            "authority": {"base_manifest_sha256": _sha256(self.base_manifest)},
            "incident": {
                "failed_run_id": FAILED_RUN_ID,
                "failed_raw_seal_sha256": failed_seal_hash,
            },
            "recovery": {"run_id": RECOVERY_RUN_ID},
            "primary_raw": primary,
        }
        _write_json(self.recovery_manifest, recovery_value)
        recovery_raw = self.recovery / "raw"
        recovery_raw.mkdir(parents=True)
        (recovery_raw / "frozen-base-manifest.json").write_bytes(
            self.base_manifest.read_bytes()
        )
        (recovery_raw / "frozen-recovery-manifest.json").write_bytes(
            self.recovery_manifest.read_bytes()
        )
        (recovery_raw / "primary.log").write_bytes(
            (failed_raw / "primary.log").read_bytes()
        )
        _write_json(
            recovery_raw / "recovery-provenance.json",
            {
                "schema": "raveil.t0044-fixture-campaign-recovery-provenance/v1",
                "failed_run_id": FAILED_RUN_ID,
                "failed_raw_seal_sha256": failed_seal_hash,
                "imported_primary": primary,
                "primary_rerun": False,
                "diagnostic_retry": True,
            },
        )
        (recovery_raw / "diagnostic.log").write_bytes(b"sealed-diagnostic\n")
        report = self.recovery / "derived" / "report.json"
        _write_json(report, {"result": "bounded"})
        report_hash = _sha256(report)
        recovery_seal = _seal(
            recovery_raw, "raveil.research-raw-seal/v1", report_hash
        )
        _write_json(self.recovery / "raw-seal.json", recovery_seal)
        self.contract = EvidenceContract(
            EXP_ID,
            FAILED_RUN_ID,
            RECOVERY_RUN_ID,
            failed_seal_hash,
            _sha256(self.recovery / "raw-seal.json"),
            report_hash,
            _sha256(self.base_manifest),
            _sha256(self.recovery_manifest),
        )

    def verify(self):
        return verify_evidence(
            self.artifact_root,
            self.base_manifest,
            self.recovery_manifest,
            self.contract,
        )


class FakeRclone:
    def __init__(self, fixture: Fixture) -> None:
        self.fixture = fixture
        self.completed = False
        self.fail_check = False
        self.bad_readback = False
        self.mutate_on_copy: Path | None = None
        self.markers: dict[str, bytes] = {}
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, argv, *, cwd, env, check, capture_output, text):
        del env, check, capture_output, text
        command = tuple(argv)
        self.commands.append(command)
        if command[1:3] == ("config", "file"):
            return subprocess.CompletedProcess(command, 0, f"{self.fixture.config}\n", "")
        if command[1] == "version":
            return subprocess.CompletedProcess(command, 0, "rclone v1.75.0\n", "")
        if command[1] == "lsf":
            if self.completed:
                return subprocess.CompletedProcess(
                    command, 0, "completion-marker.json\n", ""
                )
            return subprocess.CompletedProcess(command, 3, "", "not found")
        if command[1] == "copy":
            if self.mutate_on_copy is not None:
                self.mutate_on_copy.write_bytes(b"changed-primary\n")
                self.mutate_on_copy = None
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1] == "check":
            return subprocess.CompletedProcess(
                command, 1 if self.fail_check else 0, "", "check failed"
            )
        if command[1] == "copyto":
            marker = (Path(cwd) / command[2]).read_bytes()
            self.markers[command[3]] = marker
            return subprocess.CompletedProcess(command, 0, "", "")
        if command[1] == "cat":
            marker = self.markers.get(command[2], b"")
            if self.bad_readback:
                marker += b"changed"
            return subprocess.CompletedProcess(command, 0, marker.decode("utf-8"), "")
        raise AssertionError(f"unexpected fake rclone command: {command}")


class EvidenceVerificationTests(unittest.TestCase):
    def test_verifies_both_seals_manifests_lineage_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            failed, recovery = fixture.verify()
            self.assertEqual(failed.run_id, FAILED_RUN_ID)
            self.assertEqual(recovery.run_id, RECOVERY_RUN_ID)
            self.assertGreater(failed.byte_count + recovery.byte_count, 0)

    def test_rejects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            (fixture.failed / "raw" / "failure.json").unlink()
            with self.assertRaisesRegex(PromotionError, "file set changed"):
                fixture.verify()

    def test_rejects_symbolic_link(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            target = fixture.failed / "raw" / "failure.json"
            target.unlink()
            target.symlink_to("primary.log")
            with self.assertRaisesRegex(PromotionError, "symbolic link"):
                fixture.verify()

    def test_rejects_wrong_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            with (fixture.failed / "raw" / "primary.log").open("ab") as output:
                output.write(b"x")
            with self.assertRaisesRegex(PromotionError, "size mismatch"):
                fixture.verify()

    def test_rejects_wrong_hash_at_same_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            target = fixture.failed / "raw" / "primary.log"
            target.write_bytes(b"X" * target.stat().st_size)
            with self.assertRaisesRegex(PromotionError, "hash mismatch"):
                fixture.verify()

    def test_rejects_unexpected_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            (fixture.failed / "raw" / "late.log").write_bytes(b"late")
            with self.assertRaisesRegex(PromotionError, "unexpected"):
                fixture.verify()


class RemotePromotionTests(unittest.TestCase):
    def _promote(self, fixture: Fixture, fake: FakeRclone):
        return promote_evidence(
            fixture.repo,
            fixture.artifact_root,
            fixture.base_manifest,
            fixture.recovery_manifest,
            "fake:Raveil/research-data",
            fixture.receipt,
            runner=fake,
            contract=fixture.contract,
            verifier_revision="a" * 40,
        )

    def test_immutable_copy_download_check_marker_last_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fake = FakeRclone(fixture)
            receipt = self._promote(fixture, fake)
            validate_receipt(receipt, fixture.contract)
            self.assertEqual(receipt, json.loads(fixture.receipt.read_text()))
            operations = [command[1] for command in fake.commands]
            self.assertEqual(operations.count("copy"), 2)
            self.assertEqual(operations.count("check"), 2)
            self.assertEqual(operations[-4:], ["copyto", "cat", "copyto", "cat"])
            for command in fake.commands:
                if command[1] in {"copy", "copyto"}:
                    self.assertIn("--immutable", command)
                if command[1] == "check":
                    self.assertIn("--download", command)
                    self.assertIn("--one-way", command)

    def test_refuses_completed_remote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fake = FakeRclone(fixture)
            fake.completed = True
            with self.assertRaisesRegex(PromotionError, "completed remote"):
                self._promote(fixture, fake)
            self.assertFalse(fixture.receipt.exists())

    def test_stops_on_download_check_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fake = FakeRclone(fixture)
            fake.fail_check = True
            with self.assertRaisesRegex(PromotionError, "download-based"):
                self._promote(fixture, fake)
            self.assertNotIn("copyto", [command[1] for command in fake.commands])

    def test_stops_on_marker_readback_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fake = FakeRclone(fixture)
            fake.bad_readback = True
            with self.assertRaisesRegex(PromotionError, "readback mismatch"):
                self._promote(fixture, fake)
            self.assertFalse(fixture.receipt.exists())

    def test_detects_mutation_between_copy_and_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            fake = FakeRclone(fixture)
            fake.mutate_on_copy = fixture.failed / "raw" / "primary.log"
            with self.assertRaisesRegex(PromotionError, "size mismatch|hash mismatch"):
                self._promote(fixture, fake)
            self.assertNotIn("check", [command[1] for command in fake.commands])

    def test_receipt_rejects_unknown_fields_and_machine_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(Path(directory))
            receipt = self._promote(fixture, FakeRclone(fixture))
            unknown = dict(receipt)
            unknown["extra"] = True
            with self.assertRaisesRegex(PromotionError, "unknown fields"):
                validate_receipt(unknown, fixture.contract)
            receipt["commands"][0]["argv"].append("/Users/example/rclone.conf")
            with self.assertRaisesRegex(PromotionError, "sensitive"):
                validate_receipt(receipt, fixture.contract)


if __name__ == "__main__":
    unittest.main()
