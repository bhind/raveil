"""Durable promotion for the already sealed EXP-0008 evidence.

This adapter never invokes a simulator and never writes into either RUN-ID.
It validates the campaign-specific seals in place, transfers the two complete
RUN directories immutably, performs download-based checks, and uploads a
separate completion marker last.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable, Sequence


EXP_ID = "EXP-0008"
FAILED_RUN_ID = "20260814T130018Z-4368066-campaign256"
RECOVERY_RUN_ID = "20260814T153738Z-0203248-campaign256-recovery"
FAILED_SEAL_SHA256 = (
    "88fe79590c3ea98129d57363920686b084fb10b45e2a9c5fc0b53db3f3bc8726"
)
RECOVERY_SEAL_SHA256 = (
    "7c90f8a4a09291f5269e19d1425d1eac1a7915b8b3abcc4f16eb7206f438eeef"
)
DERIVED_REPORT_SHA256 = (
    "1e52c4e213cb19cb2455cfef67077d3d3acb959bfb834c24e6b12e932d2f7a65"
)
BASE_MANIFEST_SHA256 = (
    "2e2b71097bb88acf60904d17ce87ec6ec4399eaf1795a45c14542ee39f7d6359"
)
RECOVERY_MANIFEST_SHA256 = (
    "c9226d05f348c740801b7cbceb673514495c3f5fc15c1192629f31b2f58a1eb6"
)
RECEIPT_SCHEMA = "raveil.exp-0008-evidence-promotion-receipt/v1"
MARKER_SCHEMA = "raveil.exp-0008-completion-marker/v1"
EVIDENCE_CLASS = "remotely durable RTL-simulation evidence"
REMOTE_LOGICAL_ROOT = "Raveil/research-data"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
REMOTE_ROOT_RE = re.compile(r"^[A-Za-z0-9._-]+:Raveil/research-data$")
SENSITIVE_RE = re.compile(
    r"(?:/Users/|/private/|/home/|[A-Za-z]:\\\\Users\\\\|"
    r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|client[_-]?secret|refresh[_-]?token|"
    r"access[_-]?token|password\s*[=:])",
    re.IGNORECASE,
)


class PromotionError(RuntimeError):
    """Fail-closed evidence-promotion error."""


@dataclass(frozen=True)
class EvidenceContract:
    experiment_id: str
    failed_run_id: str
    recovery_run_id: str
    failed_seal_sha256: str
    recovery_seal_sha256: str
    derived_report_sha256: str
    base_manifest_sha256: str
    recovery_manifest_sha256: str


EXP0008_CONTRACT = EvidenceContract(
    EXP_ID,
    FAILED_RUN_ID,
    RECOVERY_RUN_ID,
    FAILED_SEAL_SHA256,
    RECOVERY_SEAL_SHA256,
    DERIVED_REPORT_SHA256,
    BASE_MANIFEST_SHA256,
    RECOVERY_MANIFEST_SHA256,
)


@dataclass(frozen=True)
class FileSnapshot:
    path: str
    device: int
    inode: int
    mode: int
    links: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


@dataclass(frozen=True)
class VerifiedRun:
    run_id: str
    seal_sha256: str
    derived_report_sha256: str | None
    files: tuple[FileSnapshot, ...]

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def byte_count(self) -> int:
        return sum(entry.size for entry in self.files)


Runner = Callable[..., subprocess.CompletedProcess[str]]


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PromotionError(f"{label} is unreadable or invalid JSON") from error
    if type(value) is not dict:
        raise PromotionError(f"{label} must be a JSON object")
    return value


def _regular_file_snapshot(path: Path, relative: str) -> FileSnapshot:
    try:
        before = path.lstat()
    except OSError as error:
        raise PromotionError(f"sealed file missing: {relative}") from error
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise PromotionError(f"sealed path is not a single-link regular file: {relative}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        after = path.lstat()
    except OSError as error:
        raise PromotionError(f"sealed file changed while hashing: {relative}") from error
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_nlink,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_nlink,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if identity_before != identity_after:
        raise PromotionError(f"sealed file changed while hashing: {relative}")
    return FileSnapshot(
        relative,
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_nlink,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
        digest.hexdigest(),
    )


def _require_sha256(value: Any, label: str) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise PromotionError(f"{label} is not a canonical SHA-256")
    return value


def _require_git_revision(value: Any, label: str) -> str:
    if type(value) is not str or not GIT_REVISION_RE.fullmatch(value):
        raise PromotionError(f"{label} is not a full Git revision")
    return value


def _seal_entries(seal: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    if set(seal) != {"schema", "files"} and set(seal) != {
        "schema",
        "files",
        "derived_report_sha256",
    }:
        raise PromotionError("source seal contains missing or unknown fields")
    expected_keys = {"schema", "files"}
    if schema == "raveil.research-raw-seal/v1":
        expected_keys.add("derived_report_sha256")
    if set(seal) != expected_keys or seal.get("schema") != schema:
        raise PromotionError("source seal schema or shape changed")
    entries = seal.get("files")
    if type(entries) is not list or not entries:
        raise PromotionError("source seal file list is empty or invalid")
    seen: set[str] = set()
    for entry in entries:
        if type(entry) is not dict or set(entry) != {"path", "bytes", "sha256"}:
            raise PromotionError("source seal file entry shape changed")
        relative = entry["path"]
        leaf = Path(relative) if type(relative) is str else Path(".")
        if (
            type(relative) is not str
            or leaf.is_absolute()
            or len(leaf.parts) != 1
            or relative in {"", ".", ".."}
            or relative in seen
        ):
            raise PromotionError("source seal contains an invalid or duplicate path")
        if type(entry["bytes"]) is not int or entry["bytes"] < 0:
            raise PromotionError(f"source seal has invalid size: {relative}")
        _require_sha256(entry["sha256"], f"source seal hash for {relative}")
        seen.add(relative)
    return entries


def _assert_tree(run_dir: Path, expected_files: set[str], expected_dirs: set[str]) -> None:
    if run_dir.name in {"", ".", ".."}:
        raise PromotionError("RUN-ID directory is invalid")
    try:
        root_metadata = run_dir.lstat()
    except OSError as error:
        raise PromotionError(f"required RUN-ID is missing: {run_dir.name}") from error
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise PromotionError(f"RUN-ID is not a non-symlink directory: {run_dir.name}")
    actual_files: set[str] = set()
    actual_dirs: set[str] = set()
    for path in run_dir.rglob("*"):
        relative = path.relative_to(run_dir).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise PromotionError(f"symbolic link found in sealed RUN: {relative}")
        if stat.S_ISDIR(metadata.st_mode):
            actual_dirs.add(relative)
        elif stat.S_ISREG(metadata.st_mode):
            actual_files.add(relative)
        else:
            raise PromotionError(f"unexpected special file in sealed RUN: {relative}")
    if actual_files != expected_files or actual_dirs != expected_dirs:
        missing = sorted(expected_files - actual_files)
        unexpected = sorted(actual_files - expected_files)
        changed_dirs = sorted(actual_dirs ^ expected_dirs)
        raise PromotionError(
            "sealed RUN file set changed: "
            f"missing={missing}, unexpected={unexpected}, directories={changed_dirs}"
        )


def _verify_run(
    run_dir: Path,
    run_id: str,
    seal_name: str,
    seal_schema: str,
    expected_seal_sha256: str,
    expected_report_sha256: str | None,
) -> VerifiedRun:
    if run_dir.name != run_id:
        raise PromotionError("exact RUN-ID requirement failed")
    seal_path = run_dir / seal_name
    seal_snapshot = _regular_file_snapshot(seal_path, seal_name)
    if seal_snapshot.sha256 != expected_seal_sha256:
        raise PromotionError(f"source seal hash mismatch: {seal_name}")
    seal = _load_json(seal_path, seal_name)
    entries = _seal_entries(seal, seal_schema)
    expected_files = {seal_name} | {f"raw/{entry['path']}" for entry in entries}
    expected_dirs = {"raw"}
    if expected_report_sha256 is not None:
        report_in_seal = _require_sha256(
            seal.get("derived_report_sha256"), "derived report hash in raw seal"
        )
        if report_in_seal != expected_report_sha256:
            raise PromotionError("derived report lineage changed in raw seal")
        expected_files.add("derived/report.json")
        expected_dirs.add("derived")
    _assert_tree(run_dir, expected_files, expected_dirs)
    snapshots = [seal_snapshot]
    entry_by_path = {entry["path"]: entry for entry in entries}
    for relative in sorted(entry_by_path):
        entry = entry_by_path[relative]
        snapshot = _regular_file_snapshot(run_dir / "raw" / relative, f"raw/{relative}")
        if snapshot.size != entry["bytes"]:
            raise PromotionError(f"sealed file size mismatch: raw/{relative}")
        if snapshot.sha256 != entry["sha256"]:
            raise PromotionError(f"sealed file hash mismatch: raw/{relative}")
        snapshots.append(snapshot)
    if expected_report_sha256 is not None:
        report = _regular_file_snapshot(
            run_dir / "derived" / "report.json", "derived/report.json"
        )
        if report.sha256 != expected_report_sha256:
            raise PromotionError("derived report hash mismatch")
        snapshots.append(report)
    return VerifiedRun(
        run_id,
        expected_seal_sha256,
        expected_report_sha256,
        tuple(sorted(snapshots, key=lambda value: value.path)),
    )


def _require_manifest_identity(
    base_manifest: dict[str, Any],
    recovery_manifest: dict[str, Any],
    contract: EvidenceContract,
) -> None:
    try:
        if base_manifest["experiment_id"] != contract.experiment_id:
            raise PromotionError("base manifest experiment identity changed")
        if base_manifest["sampling"]["run_id"] != contract.failed_run_id:
            raise PromotionError("base manifest RUN-ID changed")
        if recovery_manifest["experiment_id"] != contract.experiment_id:
            raise PromotionError("recovery manifest experiment identity changed")
        incident = recovery_manifest["incident"]
        recovery = recovery_manifest["recovery"]
        authority = recovery_manifest["authority"]
        if incident["failed_run_id"] != contract.failed_run_id:
            raise PromotionError("recovery failed RUN-ID lineage changed")
        if incident["failed_raw_seal_sha256"] != contract.failed_seal_sha256:
            raise PromotionError("recovery failed-seal lineage changed")
        if recovery["run_id"] != contract.recovery_run_id:
            raise PromotionError("recovery RUN-ID changed")
        if authority["base_manifest_sha256"] != contract.base_manifest_sha256:
            raise PromotionError("recovery base-manifest lineage changed")
    except (KeyError, TypeError) as error:
        raise PromotionError("frozen manifest lineage is incomplete") from error


def _verify_recovery_lineage(
    failed: VerifiedRun,
    recovery: VerifiedRun,
    recovery_dir: Path,
    recovery_manifest: dict[str, Any],
) -> None:
    provenance = _load_json(
        recovery_dir / "raw" / "recovery-provenance.json", "recovery provenance"
    )
    if set(provenance) != {
        "schema",
        "failed_run_id",
        "failed_raw_seal_sha256",
        "imported_primary",
        "primary_rerun",
        "diagnostic_retry",
    }:
        raise PromotionError("recovery provenance contains missing or unknown fields")
    if (
        provenance["schema"]
        != "raveil.t0044-fixture-campaign-recovery-provenance/v1"
        or provenance["failed_run_id"] != failed.run_id
        or provenance["failed_raw_seal_sha256"] != failed.seal_sha256
        or provenance["primary_rerun"] is not False
        or provenance["diagnostic_retry"] is not True
        or provenance["imported_primary"] != recovery_manifest.get("primary_raw")
    ):
        raise PromotionError("recovery provenance lineage changed")
    failed_files = {entry.path: entry for entry in failed.files}
    recovery_files = {entry.path: entry for entry in recovery.files}
    for record in recovery_manifest.get("primary_raw", {}).values():
        try:
            relative = f"raw/{record['path']}"
            expected_size = record["bytes"]
            expected_hash = record["sha256"]
        except (KeyError, TypeError) as error:
            raise PromotionError("recovery primary lineage is incomplete") from error
        if relative not in failed_files or relative not in recovery_files:
            raise PromotionError("recovery imported primary file is missing")
        if (
            failed_files[relative].size != expected_size
            or recovery_files[relative].size != expected_size
            or failed_files[relative].sha256 != expected_hash
            or recovery_files[relative].sha256 != expected_hash
        ):
            raise PromotionError("recovery imported primary lineage changed")


def verify_evidence(
    artifact_root: Path,
    base_manifest_path: Path,
    recovery_manifest_path: Path,
    contract: EvidenceContract = EXP0008_CONTRACT,
) -> tuple[VerifiedRun, VerifiedRun]:
    artifact_root = artifact_root.resolve()
    base_manifest_snapshot = _regular_file_snapshot(base_manifest_path, base_manifest_path.name)
    recovery_manifest_snapshot = _regular_file_snapshot(
        recovery_manifest_path, recovery_manifest_path.name
    )
    if base_manifest_snapshot.sha256 != contract.base_manifest_sha256:
        raise PromotionError("tracked base manifest hash mismatch")
    if recovery_manifest_snapshot.sha256 != contract.recovery_manifest_sha256:
        raise PromotionError("tracked recovery manifest hash mismatch")
    base_manifest = _load_json(base_manifest_path, "tracked base manifest")
    recovery_manifest = _load_json(recovery_manifest_path, "tracked recovery manifest")
    _require_manifest_identity(base_manifest, recovery_manifest, contract)

    experiment_root = artifact_root / contract.experiment_id
    failed_dir = experiment_root / contract.failed_run_id
    recovery_dir = experiment_root / contract.recovery_run_id
    failed = _verify_run(
        failed_dir,
        contract.failed_run_id,
        "failed-raw-seal.json",
        "raveil.research-failed-raw-seal/v1",
        contract.failed_seal_sha256,
        None,
    )
    recovery = _verify_run(
        recovery_dir,
        contract.recovery_run_id,
        "raw-seal.json",
        "raveil.research-raw-seal/v1",
        contract.recovery_seal_sha256,
        contract.derived_report_sha256,
    )
    failed_frozen = _regular_file_snapshot(
        failed_dir / "raw" / "frozen-manifest.json", "raw/frozen-manifest.json"
    )
    recovery_base = _regular_file_snapshot(
        recovery_dir / "raw" / "frozen-base-manifest.json",
        "raw/frozen-base-manifest.json",
    )
    recovery_frozen = _regular_file_snapshot(
        recovery_dir / "raw" / "frozen-recovery-manifest.json",
        "raw/frozen-recovery-manifest.json",
    )
    if (
        failed_frozen.sha256 != contract.base_manifest_sha256
        or recovery_base.sha256 != contract.base_manifest_sha256
        or failed_frozen.size != base_manifest_snapshot.size
        or recovery_base.size != base_manifest_snapshot.size
    ):
        raise PromotionError("frozen base manifest hash or byte count changed")
    if (
        recovery_frozen.sha256 != contract.recovery_manifest_sha256
        or recovery_frozen.size != recovery_manifest_snapshot.size
    ):
        raise PromotionError("frozen recovery manifest hash or byte count changed")
    _verify_recovery_lineage(failed, recovery, recovery_dir, recovery_manifest)
    return failed, recovery


def _same_snapshot(left: VerifiedRun, right: VerifiedRun) -> bool:
    return left == right


def _run(
    runner: Runner,
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return runner(
        tuple(argv),
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def _discover_external_config(
    repo: Path, rclone: str, runner: Runner, environment: dict[str, str]
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    result = _run(runner, (rclone, "config", "file"), cwd=repo, environment=environment)
    if result.returncode != 0:
        raise PromotionError("repository-external rclone configuration is unavailable")
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise PromotionError("repository-external rclone configuration is unavailable")
    config = Path(lines[-1]).expanduser().resolve()
    try:
        config.relative_to(repo.resolve())
    except ValueError:
        pass
    else:
        raise PromotionError("rclone configuration must remain outside the repository")
    try:
        metadata = config.stat()
    except OSError as error:
        raise PromotionError("repository-external rclone configuration is unavailable") from error
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise PromotionError("rclone configuration ownership or permissions are unsafe")
    return config, result


def _redacted_argv(argv: Sequence[str], remote_name: str) -> list[str]:
    redacted: list[str] = []
    for argument in argv:
        if argument.startswith(f"{remote_name}:"):
            redacted.append("<configured-remote>:" + argument.split(":", 1)[1])
        elif ".exp0008-promotion-" in argument:
            redacted.append("<temporary-completion-marker>")
        elif Path(argument).is_absolute():
            redacted.append("<external-path>")
        else:
            redacted.append(argument)
    return redacted


def _command_record(
    operation: str,
    argv: Sequence[str],
    result: subprocess.CompletedProcess[str],
    remote_name: str,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "argv": _redacted_argv(argv, remote_name),
        "exit_status": result.returncode,
    }


def _marker(
    run: VerifiedRun, verifier_revision: str, verified_at: str
) -> dict[str, Any]:
    return {
        "schema": MARKER_SCHEMA,
        "evidence_class": EVIDENCE_CLASS,
        "experiment_id": EXP_ID,
        "run_id": run.run_id,
        "source_seal_sha256": run.seal_sha256,
        "derived_report_sha256": run.derived_report_sha256,
        "checked_file_count": run.file_count,
        "checked_byte_count": run.byte_count,
        "verifier_git_revision": verifier_revision,
        "verified_at_utc": verified_at,
    }


def _validate_marker(value: dict[str, Any]) -> None:
    if set(value) != {
        "schema",
        "evidence_class",
        "experiment_id",
        "run_id",
        "source_seal_sha256",
        "derived_report_sha256",
        "checked_file_count",
        "checked_byte_count",
        "verifier_git_revision",
        "verified_at_utc",
    }:
        raise PromotionError("completion marker contains missing or unknown fields")
    if (
        value["schema"] != MARKER_SCHEMA
        or value["evidence_class"] != EVIDENCE_CLASS
        or value["experiment_id"] != EXP_ID
        or value["run_id"] not in {FAILED_RUN_ID, RECOVERY_RUN_ID}
        or type(value["checked_file_count"]) is not int
        or value["checked_file_count"] <= 0
        or type(value["checked_byte_count"]) is not int
        or value["checked_byte_count"] <= 0
    ):
        raise PromotionError("completion marker identity or totals are invalid")
    _require_sha256(value["source_seal_sha256"], "completion marker source seal")
    _require_git_revision(
        value["verifier_git_revision"], "completion marker verifier revision"
    )
    report_hash = value["derived_report_sha256"]
    if report_hash is not None:
        _require_sha256(report_hash, "completion marker derived report")


def validate_receipt(
    receipt: dict[str, Any], contract: EvidenceContract = EXP0008_CONTRACT
) -> None:
    expected_keys = {
        "schema",
        "status",
        "evidence_class",
        "experiment_id",
        "verifier_git_revision",
        "verification_time_utc",
        "rclone_version",
        "rclone_configuration",
        "source_hashes",
        "runs",
        "checked_file_count",
        "checked_byte_count",
        "commands",
    }
    if set(receipt) != expected_keys:
        raise PromotionError("promotion receipt contains missing or unknown fields")
    if (
        receipt["schema"] != RECEIPT_SCHEMA
        or receipt["status"] != "remote-promotion-complete"
        or receipt["evidence_class"] != EVIDENCE_CLASS
        or receipt["experiment_id"] != contract.experiment_id
        or receipt["rclone_configuration"]
        != "repository-external-owner-provided"
    ):
        raise PromotionError("promotion receipt identity changed")
    _require_git_revision(receipt["verifier_git_revision"], "receipt verifier revision")
    if (
        type(receipt["verification_time_utc"]) is not str
        or not receipt["verification_time_utc"].endswith("Z")
        or type(receipt["rclone_version"]) is not str
        or not receipt["rclone_version"].startswith("rclone v")
    ):
        raise PromotionError("promotion receipt time or rclone version is invalid")
    source_hashes = receipt["source_hashes"]
    if type(source_hashes) is not dict or set(source_hashes) != {
        "failed_seal_sha256",
        "recovery_seal_sha256",
        "derived_report_sha256",
        "base_manifest_sha256",
        "recovery_manifest_sha256",
    }:
        raise PromotionError("promotion receipt source hash shape changed")
    expected_hashes = {
        "failed_seal_sha256": contract.failed_seal_sha256,
        "recovery_seal_sha256": contract.recovery_seal_sha256,
        "derived_report_sha256": contract.derived_report_sha256,
        "base_manifest_sha256": contract.base_manifest_sha256,
        "recovery_manifest_sha256": contract.recovery_manifest_sha256,
    }
    if source_hashes != expected_hashes:
        raise PromotionError("promotion receipt source hashes changed")
    runs = receipt["runs"]
    if type(runs) is not list or len(runs) != 2:
        raise PromotionError("promotion receipt RUN list changed")
    expected_run_ids = [contract.failed_run_id, contract.recovery_run_id]
    for value, expected_run_id in zip(runs, expected_run_ids, strict=True):
        if type(value) is not dict or set(value) != {
            "run_id",
            "logical_remote_locator",
            "checked_file_count",
            "checked_byte_count",
            "completion_marker_sha256",
            "remote_check_exit_status",
            "completion_marker_readback",
        }:
            raise PromotionError("promotion receipt RUN shape changed")
        if (
            value["run_id"] != expected_run_id
            or value["logical_remote_locator"]
            != f"{REMOTE_LOGICAL_ROOT}/{contract.experiment_id}/{expected_run_id}/"
            or type(value["checked_file_count"]) is not int
            or value["checked_file_count"] <= 0
            or type(value["checked_byte_count"]) is not int
            or value["checked_byte_count"] <= 0
            or value["remote_check_exit_status"] != 0
            or value["completion_marker_readback"] != "byte-for-byte-match"
        ):
            raise PromotionError("promotion receipt RUN identity or verification changed")
        _require_sha256(value["completion_marker_sha256"], "receipt marker hash")
    if receipt["checked_file_count"] != sum(
        value["checked_file_count"] for value in runs
    ) or receipt["checked_byte_count"] != sum(
        value["checked_byte_count"] for value in runs
    ):
        raise PromotionError("promotion receipt aggregate totals changed")
    commands = receipt["commands"]
    if type(commands) is not list or not commands:
        raise PromotionError("promotion receipt command list is empty")
    for command in commands:
        if type(command) is not dict or set(command) != {
            "operation",
            "argv",
            "exit_status",
        }:
            raise PromotionError("promotion receipt command shape changed")
        if (
            type(command["operation"]) is not str
            or type(command["argv"]) is not list
            or not all(type(argument) is str for argument in command["argv"])
            or type(command["exit_status"]) is not int
        ):
            raise PromotionError("promotion receipt command value is invalid")
    expected_operations = [
        "rclone-config-file",
        "rclone-version",
        "remote-preflight",
        "immutable-copy",
        "download-check",
        "remote-preflight",
        "immutable-copy",
        "download-check",
        "completion-marker-copy",
        "completion-marker-readback",
        "completion-marker-copy",
        "completion-marker-readback",
    ]
    if [command["operation"] for command in commands] != expected_operations:
        raise PromotionError("promotion receipt command sequence changed")
    for command in commands:
        if command["operation"] == "remote-preflight":
            if command["exit_status"] not in {0, 3}:
                raise PromotionError("promotion receipt preflight status is invalid")
        elif command["exit_status"] != 0:
            raise PromotionError("promotion receipt records a failed required command")
    for command in commands:
        argv = command["argv"]
        if command["operation"] in {"immutable-copy", "completion-marker-copy"}:
            if "--immutable" not in argv:
                raise PromotionError("promotion receipt lost immutable transfer semantics")
        if command["operation"] == "download-check":
            if "--download" not in argv or "--one-way" not in argv:
                raise PromotionError("promotion receipt lost download-check semantics")
    serialized = _canonical_bytes(receipt).decode("utf-8")
    if SENSITIVE_RE.search(serialized):
        raise PromotionError("promotion receipt contains sensitive or machine-local data")


def _verifier_revision(repo: Path) -> str:
    revision = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=repo, text=True
    ).strip()
    if not GIT_REVISION_RE.fullmatch(revision):
        raise PromotionError("verifier Git revision is invalid")
    tracked = subprocess.check_output(
        (
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            "HEAD",
            "--",
            "raveil/t0044_evidence_promotion.py",
        ),
        cwd=repo,
        text=True,
    )
    if "raveil/t0044_evidence_promotion.py" not in tracked.splitlines():
        raise PromotionError("promotion requires a committed verifier")
    dirty = subprocess.check_output(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        cwd=repo,
        text=True,
    )
    if dirty:
        raise PromotionError("promotion requires a clean tracked worktree")
    return revision


def promote_evidence(
    repo: Path,
    artifact_root: Path,
    base_manifest_path: Path,
    recovery_manifest_path: Path,
    remote_root: str,
    receipt_path: Path,
    *,
    rclone: str = "rclone",
    runner: Runner = subprocess.run,
    contract: EvidenceContract = EXP0008_CONTRACT,
    verifier_revision: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    repo = repo.resolve()
    if not REMOTE_ROOT_RE.fullmatch(remote_root):
        raise PromotionError("remote root must be a configured Raveil/research-data root")
    remote_name = remote_root.split(":", 1)[0]
    revision = verifier_revision or _verifier_revision(repo)
    _require_git_revision(revision, "verifier Git revision")
    initial = verify_evidence(
        artifact_root, base_manifest_path, recovery_manifest_path, contract
    )
    environment = dict(os.environ)
    config, config_result = _discover_external_config(
        repo, rclone, runner, environment
    )
    environment["RCLONE_CONFIG"] = str(config)
    version_argv = (rclone, "version")
    version_result = _run(
        runner, version_argv, cwd=repo, environment=environment
    )
    if version_result.returncode != 0 or not version_result.stdout.splitlines():
        raise PromotionError("rclone version query failed")
    rclone_version = version_result.stdout.splitlines()[0].strip()
    commands = [
        _command_record(
            "rclone-config-file",
            (rclone, "config", "file"),
            config_result,
            remote_name,
        ),
        _command_record("rclone-version", version_argv, version_result, remote_name),
    ]
    run_dirs = {
        contract.failed_run_id: artifact_root.resolve()
        / contract.experiment_id
        / contract.failed_run_id,
        contract.recovery_run_id: artifact_root.resolve()
        / contract.experiment_id
        / contract.recovery_run_id,
    }
    checked_runs: list[VerifiedRun] = []
    for source in initial:
        source_path = run_dirs[source.run_id]
        try:
            source_argument = source_path.relative_to(repo).as_posix()
        except ValueError as error:
            raise PromotionError("evidence source must be inside the repository worktree") from error
        remote = f"{remote_root}/{contract.experiment_id}/{source.run_id}"
        lsf_argv = (rclone, "lsf", remote, "--max-depth", "1")
        listing = _run(runner, lsf_argv, cwd=repo, environment=environment)
        commands.append(_command_record("remote-preflight", lsf_argv, listing, remote_name))
        if listing.returncode == 0:
            remote_files = set(listing.stdout.splitlines())
            if "completion-marker.json" in remote_files:
                raise PromotionError("completed remote RUN already exists; overwrite refused")
        elif listing.returncode != 3:
            raise PromotionError("remote preflight failed")
        copy_argv = (
            rclone,
            "copy",
            source_argument,
            remote,
            "--immutable",
            "--exclude",
            "completion-marker.json",
        )
        copy = _run(runner, copy_argv, cwd=repo, environment=environment)
        commands.append(_command_record("immutable-copy", copy_argv, copy, remote_name))
        if copy.returncode != 0:
            raise PromotionError("immutable remote copy failed")
        after_copy = verify_evidence(
            artifact_root, base_manifest_path, recovery_manifest_path, contract
        )
        if not _same_snapshot(initial[0], after_copy[0]) or not _same_snapshot(
            initial[1], after_copy[1]
        ):
            raise PromotionError("sealed source changed during immutable copy")
        check_argv = (
            rclone,
            "check",
            source_argument,
            remote,
            "--download",
            "--one-way",
            "--exclude",
            "completion-marker.json",
        )
        check = _run(runner, check_argv, cwd=repo, environment=environment)
        commands.append(_command_record("download-check", check_argv, check, remote_name))
        if check.returncode != 0:
            raise PromotionError("download-based remote check failed")
        after_check = verify_evidence(
            artifact_root, base_manifest_path, recovery_manifest_path, contract
        )
        if not _same_snapshot(initial[0], after_check[0]) or not _same_snapshot(
            initial[1], after_check[1]
        ):
            raise PromotionError("sealed source changed during download check")
        checked_runs.append(source)

    final_sources = verify_evidence(
        artifact_root, base_manifest_path, recovery_manifest_path, contract
    )
    if final_sources != initial:
        raise PromotionError("sealed source changed before completion marker transfer")
    verified_at = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    receipt_runs: list[dict[str, Any]] = []
    artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".exp0008-promotion-", dir=artifact_root
    ) as temporary:
        temporary_root = Path(temporary).resolve()
        for source in checked_runs:
            marker_value = _marker(source, revision, verified_at)
            _validate_marker(marker_value)
            marker_bytes = _canonical_bytes(marker_value)
            marker_path = temporary_root / f"{source.run_id}-completion-marker.json"
            marker_path.write_bytes(marker_bytes)
            marker_argument = marker_path.relative_to(repo).as_posix()
            remote = f"{remote_root}/{contract.experiment_id}/{source.run_id}"
            marker_argv = (
                rclone,
                "copyto",
                marker_argument,
                f"{remote}/completion-marker.json",
                "--immutable",
            )
            marker_copy = _run(
                runner, marker_argv, cwd=repo, environment=environment
            )
            commands.append(
                _command_record("completion-marker-copy", marker_argv, marker_copy, remote_name)
            )
            if marker_copy.returncode != 0:
                raise PromotionError("completion marker immutable upload failed")
            readback_argv = (rclone, "cat", f"{remote}/completion-marker.json")
            readback = _run(
                runner, readback_argv, cwd=repo, environment=environment
            )
            commands.append(
                _command_record("completion-marker-readback", readback_argv, readback, remote_name)
            )
            if readback.returncode != 0 or readback.stdout.encode("utf-8") != marker_bytes:
                raise PromotionError("completion marker readback mismatch")
            receipt_runs.append(
                {
                    "run_id": source.run_id,
                    "logical_remote_locator": (
                        f"{REMOTE_LOGICAL_ROOT}/{contract.experiment_id}/{source.run_id}/"
                    ),
                    "checked_file_count": source.file_count,
                    "checked_byte_count": source.byte_count,
                    "completion_marker_sha256": _sha256_bytes(marker_bytes),
                    "remote_check_exit_status": 0,
                    "completion_marker_readback": "byte-for-byte-match",
                }
            )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "remote-promotion-complete",
        "evidence_class": EVIDENCE_CLASS,
        "experiment_id": contract.experiment_id,
        "verifier_git_revision": revision,
        "verification_time_utc": verified_at,
        "rclone_version": rclone_version,
        "rclone_configuration": "repository-external-owner-provided",
        "source_hashes": {
            "failed_seal_sha256": contract.failed_seal_sha256,
            "recovery_seal_sha256": contract.recovery_seal_sha256,
            "derived_report_sha256": contract.derived_report_sha256,
            "base_manifest_sha256": contract.base_manifest_sha256,
            "recovery_manifest_sha256": contract.recovery_manifest_sha256,
        },
        "runs": receipt_runs,
        "checked_file_count": sum(run.file_count for run in checked_runs),
        "checked_byte_count": sum(run.byte_count for run in checked_runs),
        "commands": commands,
    }
    validate_receipt(receipt, contract)
    receipt_path = receipt_path.resolve()
    try:
        receipt_path.relative_to(repo)
    except ValueError as error:
        raise PromotionError("receipt must be written inside the repository") from error
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with receipt_path.open("xb") as output:
            output.write(_canonical_bytes(receipt))
    except FileExistsError as error:
        raise PromotionError("promotion receipt already exists; overwrite refused") from error
    return receipt


def _summary(runs: tuple[VerifiedRun, VerifiedRun]) -> dict[str, Any]:
    return {
        "schema": "raveil.exp-0008-local-verification-summary/v1",
        "status": "locally-verified-no-simulation",
        "experiment_id": EXP_ID,
        "runs": [
            {
                "run_id": run.run_id,
                "seal_sha256": run.seal_sha256,
                "derived_report_sha256": run.derived_report_sha256,
                "checked_file_count": run.file_count,
                "checked_byte_count": run.byte_count,
            }
            for run in runs
        ],
        "checked_file_count": sum(run.file_count for run in runs),
        "checked_byte_count": sum(run.byte_count for run in runs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="verify and durably promote existing sealed EXP-0008 evidence"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "promote"):
        command = commands.add_parser(name)
        command.add_argument("--repo", type=Path, default=Path("."))
        command.add_argument(
            "--artifact-root", type=Path, default=Path("artifacts/research")
        )
        command.add_argument(
            "--base-manifest",
            type=Path,
            default=Path("benchmarks/manifests/t0044-fixture-campaign-v1.json"),
        )
        command.add_argument(
            "--recovery-manifest",
            type=Path,
            default=Path(
                "benchmarks/manifests/t0044-fixture-campaign-recovery-v1.json"
            ),
        )
    promote = commands.choices["promote"]
    promote.add_argument("--remote-root", required=True)
    promote.add_argument("--rclone", default="rclone")
    promote.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    artifact_root = (repo / args.artifact_root).resolve()
    base_manifest = (repo / args.base_manifest).resolve()
    recovery_manifest = (repo / args.recovery_manifest).resolve()
    try:
        if args.command == "verify":
            result = _summary(
                verify_evidence(artifact_root, base_manifest, recovery_manifest)
            )
        else:
            result = promote_evidence(
                repo,
                artifact_root,
                base_manifest,
                recovery_manifest,
                args.remote_root,
                repo / args.receipt,
                rclone=args.rclone,
            )
    except (PromotionError, OSError, subprocess.SubprocessError) as error:
        print(f"promotion-blocked: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
