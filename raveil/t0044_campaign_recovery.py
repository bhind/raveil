"""Operational-only recovery for the sealed EXP-0008 diagnostic timeout."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from .controlled_run import ControlledRunError
from .t0044_campaign import (
    FULL_ACCOUNT,
    VARIANTS,
    _run_campaign_command,
    _seal_failed_raw,
    _verify_expected_identities,
    build_report,
    load_manifest,
)
from .t0044_fixture import parse_variant_log
from .t0044_repeated import _canonical_bytes, _sha256, seal_raw


RECOVERY_MANIFEST_SCHEMA = "raveil.t0044-fixture-campaign-recovery-manifest/v1"
RECOVERY_REPORT_SCHEMA = "raveil.t0044-fixture-campaign-recovery-report/v1"
PRIMARY_VARIANTS = VARIANTS[:3]
DIAGNOSTIC_VARIANT = VARIANTS[3]


def load_recovery_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != RECOVERY_MANIFEST_SCHEMA:
        raise ControlledRunError("EXP-0008 recovery manifest schema changed")
    if value.get("experiment_id") != "EXP-0008":
        raise ControlledRunError("EXP-0008 recovery identity changed")
    if value.get("status") != "frozen-before-recovery-data":
        raise ControlledRunError("EXP-0008 recovery manifest is not frozen")
    if set(value) != {
        "schema", "experiment_id", "status", "authority", "incident",
        "recovery", "primary_raw", "diagnostic_expected_identity",
        "operations", "claim_boundary",
    }:
        raise ControlledRunError("EXP-0008 recovery manifest shape changed")
    authority = value["authority"]
    if set(authority) != {
        "recovery_implementation_commit", "base_implementation_commit",
        "base_manifest_sha256", "governance_ancestor", "t0042_commit",
    }:
        raise ControlledRunError("EXP-0008 recovery authority changed")
    for key in ("recovery_implementation_commit", "base_implementation_commit"):
        digest = authority[key]
        if (type(digest) is not str or len(digest) != 40
                or any(character not in "0123456789abcdef" for character in digest)):
            raise ControlledRunError("EXP-0008 recovery Git authority is invalid")
    if authority["governance_ancestor"] != (
            "ae606dea3f74d6694eecbe91fc368b097f03758c"):
        raise ControlledRunError("EXP-0008 recovery governance ancestor changed")
    if authority["t0042_commit"] != (
            "528fbe28a0dcdfbab65d4ae2995c0876857e053a"):
        raise ControlledRunError("EXP-0008 recovery T-0042 authority changed")
    incident = value["incident"]
    if set(incident) != {
        "failed_run_id", "failed_raw_seal_sha256", "failure",
        "failed_variant", "failed_exit_code", "completed_primary",
    }:
        raise ControlledRunError("EXP-0008 recovery incident shape changed")
    if incident["failure"] != "runner-hardcoded-3600-second-timeout":
        raise ControlledRunError("EXP-0008 recovery cause changed")
    if incident["failed_variant"] != DIAGNOSTIC_VARIANT:
        raise ControlledRunError("EXP-0008 recovery variant changed")
    if incident["failed_exit_code"] != 124:
        raise ControlledRunError("EXP-0008 recovery exit code changed")
    if incident["completed_primary"] != list(PRIMARY_VARIANTS):
        raise ControlledRunError("EXP-0008 recovery primary set changed")
    recovery = value["recovery"]
    if set(recovery) != {
        "run_id", "variant", "account", "simulator_timeout_seconds",
        "import_policy", "performance_contract",
    }:
        raise ControlledRunError("EXP-0008 recovery operation shape changed")
    if (not recovery["run_id"].endswith("-campaign256-recovery")
            or recovery["variant"] != DIAGNOSTIC_VARIANT
            or recovery["account"] != FULL_ACCOUNT
            or recovery["simulator_timeout_seconds"] != 10800
            or recovery["import_policy"]
            != "all-completed-primary-logs-from-sealed-failed-run"
            or recovery["performance_contract"]
            != "unchanged-base-manifest-estimator-and-decision-rules"):
        raise ControlledRunError("EXP-0008 recovery operation changed")
    primary_raw = value["primary_raw"]
    if set(primary_raw) != set(PRIMARY_VARIANTS):
        raise ControlledRunError("EXP-0008 recovery primary raw set changed")
    for variant in PRIMARY_VARIANTS:
        record = primary_raw[variant]
        if set(record) != {"path", "bytes", "sha256"}:
            raise ControlledRunError("EXP-0008 recovery primary raw shape changed")
        if record["path"] != f"{variant}.log" or record["bytes"] <= 0:
            raise ControlledRunError("EXP-0008 recovery primary raw metadata changed")
        _require_sha256(record["sha256"], "primary raw SHA-256")
    expected = value["diagnostic_expected_identity"]
    if set(expected) != {
        "implementation", "implementation_configuration", "source_sha256",
        "configuration_sha256", "toolchain_sha256", "resource_sha256",
        "contract_sha256",
    }:
        raise ControlledRunError("EXP-0008 recovery diagnostic identity changed")
    if (expected["implementation"] != "boom-ooo"
            or expected["implementation_configuration"]
            != "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig"):
        raise ControlledRunError("EXP-0008 recovery diagnostic configuration changed")
    for key in set(expected) - {"implementation", "implementation_configuration"}:
        _require_sha256(expected[key], f"diagnostic {key}")
    if value["operations"] != {
        "minimum_free_bytes_before_collection": 5368709120,
        "maximum_raw_log_bytes_per_candidate": 2147483648,
        "terminal_marker_drain_timeout_seconds": 120,
    }:
        raise ControlledRunError("EXP-0008 recovery operational limits changed")
    if value["claim_boundary"] != {
        "primary_measurements": "sealed-failed-run-only-no-rerun",
        "diagnostic_role": "diagnostic-only-not-primary-baseline",
        "deterministic_rerun_is_not_sample": True,
        "estimator_or_threshold_change": False,
        "rtl_or_elf_change": False,
    }:
        raise ControlledRunError("EXP-0008 recovery claim boundary changed")
    _require_sha256(authority["base_manifest_sha256"], "base manifest SHA-256")
    _require_sha256(incident["failed_raw_seal_sha256"], "failed seal SHA-256")
    return value


def _require_sha256(value: Any, label: str) -> None:
    if (type(value) is not str or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)):
        raise ControlledRunError(f"EXP-0008 recovery {label} is invalid")


def _verify_failed_evidence(failed_run: Path, recovery: dict[str, Any]) -> list[dict[str, Any]]:
    incident = recovery["incident"]
    if failed_run.name != incident["failed_run_id"]:
        raise ControlledRunError("EXP-0008 failed RUN-ID changed")
    seal_path = failed_run / "failed-raw-seal.json"
    if _sha256(seal_path) != incident["failed_raw_seal_sha256"]:
        raise ControlledRunError("EXP-0008 failed raw seal changed")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("schema") != "raveil.research-failed-raw-seal/v1":
        raise ControlledRunError("EXP-0008 failed raw seal schema changed")
    raw = failed_run / "raw"
    sealed_names = set()
    for record in seal.get("files", []):
        path = raw / record["path"]
        if (not path.is_file() or path.stat().st_size != record["bytes"]
                or _sha256(path) != record["sha256"]):
            raise ControlledRunError("EXP-0008 failed raw evidence changed")
        sealed_names.add(record["path"])
    if sealed_names != {path.name for path in raw.iterdir() if path.is_file()}:
        raise ControlledRunError("EXP-0008 failed raw file set changed")
    if _sha256(raw / "frozen-manifest.json") != recovery["authority"][
            "base_manifest_sha256"]:
        raise ControlledRunError("EXP-0008 failed run manifest changed")
    failure = json.loads((raw / "failure.json").read_text(encoding="utf-8"))
    if failure != {
        "schema": "raveil.research-failure/v1",
        "error": "campaign command failed with 124",
    }:
        raise ControlledRunError("EXP-0008 failed run cause changed")
    commands = [json.loads(line) for line in
                (raw / "commands.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(commands) != 4:
        raise ControlledRunError("EXP-0008 failed command count changed")
    if ([record["exit_code"] for record in commands] != [0, 0, 0, 124]
            or [record["log"] for record in commands[:3]]
            != [f"{variant}.log" for variant in PRIMARY_VARIANTS]
            or commands[3]["log"] != f"{DIAGNOSTIC_VARIANT}.log"):
        raise ControlledRunError("EXP-0008 failed command sequence changed")
    for variant in PRIMARY_VARIANTS:
        frozen = recovery["primary_raw"][variant]
        path = raw / frozen["path"]
        if path.stat().st_size != frozen["bytes"] or _sha256(path) != frozen["sha256"]:
            raise ControlledRunError("EXP-0008 completed primary log changed")
    return commands


def derive_recovery(run_dir: Path, base_manifest_path: Path,
                    recovery_manifest_path: Path) -> dict[str, Any]:
    base = load_manifest(base_manifest_path)
    recovery = load_recovery_manifest(recovery_manifest_path)
    if _sha256(base_manifest_path) != recovery["authority"]["base_manifest_sha256"]:
        raise ControlledRunError("EXP-0008 recovery base manifest drifted")
    raw = run_dir / "raw"
    if ((raw / "frozen-base-manifest.json").read_bytes()
            != base_manifest_path.read_bytes()
            or (raw / "frozen-recovery-manifest.json").read_bytes()
            != recovery_manifest_path.read_bytes()):
        raise ControlledRunError("EXP-0008 recovery frozen manifest copy changed")
    sessions = {
        variant: parse_variant_log(variant, raw / f"{variant}.log", FULL_ACCOUNT)
        for variant in VARIANTS
    }
    expected = copy.deepcopy(base)
    expected["identity_policy"]["stable_expected_by_variant"][
        DIAGNOSTIC_VARIANT] = recovery["diagnostic_expected_identity"]
    _verify_expected_identities(sessions, expected)
    report = build_report(sessions, _sha256(base_manifest_path))
    report["schema"] = RECOVERY_REPORT_SCHEMA
    report["recovery_manifest_sha256"] = _sha256(recovery_manifest_path)
    report["source_runs"] = {
        "primary": recovery["incident"]["failed_run_id"],
        "diagnostic": recovery["recovery"]["run_id"],
    }
    report["operational_recovery"] = {
        "cause": recovery["incident"]["failure"],
        "failed_exit_code": 124,
        "primary_rerun": False,
        "diagnostic_timeout_seconds": recovery["recovery"][
            "simulator_timeout_seconds"],
        "performance_contract_changed": False,
        "rtl_or_elf_changed": False,
    }
    derived = run_dir / "derived"
    derived.mkdir(exist_ok=False)
    (derived / "report.json").write_bytes(_canonical_bytes(report) + b"\n")
    return report


def collect_recovery(repo: Path, failed_run: Path, run_dir: Path,
                     base_manifest_path: Path, recovery_manifest_path: Path,
                     chipyard: Path) -> dict[str, Any]:
    base = load_manifest(base_manifest_path)
    recovery = load_recovery_manifest(recovery_manifest_path)
    if _sha256(base_manifest_path) != recovery["authority"]["base_manifest_sha256"]:
        raise ControlledRunError("EXP-0008 recovery base manifest drifted")
    if run_dir.exists():
        raise ControlledRunError("recovery RUN-ID directory already exists")
    if run_dir.name != recovery["recovery"]["run_id"]:
        raise ControlledRunError("recovery directory does not match frozen RUN-ID")
    if subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo, text=True,
    ):
        raise ControlledRunError("recovery collection requires a clean worktree")
    if shutil.disk_usage(repo).free < recovery["operations"][
            "minimum_free_bytes_before_collection"]:
        raise ControlledRunError("insufficient free space for EXP-0008 recovery")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    implementation = recovery["authority"]["recovery_implementation_commit"]
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", implementation, commit], cwd=repo,
    ).returncode:
        raise ControlledRunError("recovery implementation is not an ancestor")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{implementation}..{commit}"],
        cwd=repo, text=True,
    ).splitlines()
    allowed = {
        "benchmarks/manifests/t0044-fixture-campaign-recovery-v1.json",
        "docs/STATUS.md", "TODO.md", "docs/ROADMAP.md",
        "docs/OPEN_QUESTIONS.md", "docs/experiments/README.md",
        "docs/experiments/EXP-0008-static-full-campaign.md",
        "docs/log/2026-08-15.md", "tests/test_t0044_campaign_recovery.py",
    }
    if not set(changed).issubset(allowed):
        raise ControlledRunError("source/config changed after recovery authority")
    commands = _verify_failed_evidence(failed_run, recovery)
    raw = run_dir / "raw"
    raw.mkdir(parents=True)
    (raw / "frozen-base-manifest.json").write_bytes(base_manifest_path.read_bytes())
    (raw / "frozen-recovery-manifest.json").write_bytes(
        recovery_manifest_path.read_bytes())
    failed_raw = failed_run / "raw"
    for variant in PRIMARY_VARIANTS:
        shutil.copyfile(failed_raw / f"{variant}.log", raw / f"{variant}.log")
    command_file = raw / "commands.jsonl"
    command_file.write_bytes(b"".join(
        _canonical_bytes(record) + b"\n" for record in commands[:3]))
    provenance = {
        "schema": "raveil.t0044-fixture-campaign-recovery-provenance/v1",
        "failed_run_id": failed_run.name,
        "failed_raw_seal_sha256": _sha256(failed_run / "failed-raw-seal.json"),
        "imported_primary": recovery["primary_raw"],
        "primary_rerun": False,
        "diagnostic_retry": True,
    }
    (raw / "recovery-provenance.json").write_bytes(
        _canonical_bytes(provenance) + b"\n")
    metadata = {
        "schema": "raveil.t0044-fixture-campaign-recovery-run-metadata/v1",
        "experiment_id": "EXP-0008", "account": FULL_ACCOUNT,
        "git_commit": commit,
        "base_manifest_sha256": _sha256(base_manifest_path),
        "recovery_manifest_sha256": _sha256(recovery_manifest_path),
        "failed_run_id": failed_run.name,
        "host_wall_clock_role": "operations-only-not-cpu-performance-evidence",
    }
    (raw / "run-metadata.json").write_bytes(_canonical_bytes(metadata) + b"\n")
    env = dict(os.environ)
    for key in (
        "RAVEIL_PILOT_SEED", "RAVEIL_FIXTURE_REPEAT_ACCOUNT",
        "RAVEIL_REPEAT_ACCOUNT", "RAVEIL_REPEAT_TIMEOUT_SECONDS",
        "RAVEIL_BUILD_ONLY", "RAVEIL_CONTROLLED_SEED",
        "RAVEIL_CONTROLLED_INVOCATION", "RAVEIL_CONTROLLED_SERIALIZE_DISPATCH",
    ):
        env.pop(key, None)
    env["RAVEIL_CHIPYARD_SOURCE"] = str(chipyard)
    env["RAVEIL_ROCKET_CHIP_SOURCE"] = str(chipyard.parent / "rocket-chip")
    env["RAVEIL_REPEAT_ACCOUNT"] = str(FULL_ACCOUNT)
    env["RAVEIL_REPEAT_TIMEOUT_SECONDS"] = str(
        recovery["recovery"]["simulator_timeout_seconds"])
    required = {
        "RAVEIL-CONTROLLED-OUTPUT-V1": 256 * FULL_ACCOUNT,
        "RAVEIL-FIXTURE-INPUT-V1": 324 * FULL_ACCOUNT,
        "RAVEIL-FIXTURE-PHASE-V1": 2 * FULL_ACCOUNT,
        "RAVEIL-FIXTURE-REARM-V1": FULL_ACCOUNT,
        "RAVEIL-FIXTURE-STAGING-V1": FULL_ACCOUNT,
        "RAVEIL-FIXTURE-RESOURCE-V1": FULL_ACCOUNT,
        "RAVEIL-REPEATED-CPU-COMPLETE-V1": FULL_ACCOUNT,
        "RAVEIL-FIXTURE-CPU-HOST-V1": 1,
    }
    script = repo / "hardware/chisel/run-fixture-repeated-boom-serialize-stencil.sh"
    try:
        _run_campaign_command(
            [str(script)], env, raw / f"{DIAGNOSTIC_VARIANT}.log",
            command_file, required, "RAVEIL-FIXTURE-CPU-HOST-V1",
            {"operations": recovery["operations"]},
        )
        report = derive_recovery(run_dir, base_manifest_path, recovery_manifest_path)
        seal_raw(run_dir)
        return report
    except (ControlledRunError, OSError, ValueError, KeyError) as error:
        if raw.is_dir() and not (run_dir / "raw-seal.json").exists():
            _seal_failed_raw(run_dir, str(error))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="recover EXP-0008 diagnostic timeout")
    commands = parser.add_subparsers(dest="command", required=True)
    collect_parser = commands.add_parser("collect")
    collect_parser.add_argument("--repo", type=Path, required=True)
    collect_parser.add_argument("--failed-run-dir", type=Path, required=True)
    collect_parser.add_argument("--run-dir", type=Path, required=True)
    collect_parser.add_argument("--base-manifest", type=Path, required=True)
    collect_parser.add_argument("--recovery-manifest", type=Path, required=True)
    collect_parser.add_argument("--chipyard-source", type=Path, required=True)
    derive_parser = commands.add_parser("derive")
    derive_parser.add_argument("--run-dir", type=Path, required=True)
    derive_parser.add_argument("--base-manifest", type=Path, required=True)
    derive_parser.add_argument("--recovery-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            result = collect_recovery(
                args.repo.resolve(), args.failed_run_dir.resolve(),
                args.run_dir.resolve(), args.base_manifest.resolve(),
                args.recovery_manifest.resolve(), args.chipyard_source.resolve())
        else:
            result = derive_recovery(
                args.run_dir.resolve(), args.base_manifest.resolve(),
                args.recovery_manifest.resolve())
    except (ControlledRunError, OSError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
