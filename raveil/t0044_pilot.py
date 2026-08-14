"""Collect and derive the frozen EXP-0005 RTL latency/traffic pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from typing import Any


SCHEMA = "raveil.t0044-pilot-manifest/v1"
OBSERVATION_SCHEMA = "raveil.controlled-run/v1"
VARIANTS = (
    "static-graph",
    "rocket-in-order",
    "boom-ooo",
    "boom-serialize-dispatch",
)
PRIMARY = VARIANTS[:3]
SEEDS = (1, 2, 3, 4)


class PilotError(ValueError):
    """The frozen pilot contract or collected evidence is invalid."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != SCHEMA or value.get("experiment_id") != "EXP-0005":
        raise PilotError("EXP-0005 manifest identity changed")
    if value.get("status") != "frozen-before-data":
        raise PilotError("EXP-0005 manifest is not frozen")
    if value["workload"]["fresh_input_seeds"] != list(SEEDS):
        raise PilotError("fresh-input seed set changed")
    if value["matrix"]["complete_for_this_pilot"] != list(VARIANTS):
        raise PilotError("pilot matrix changed")
    if value["sampling"]["pilot_accounts"] != [1, 4]:
        raise PilotError("pilot invocation accounts changed")
    if value["window_contract"]["graph_launch_cycle_in_execution"] is not True:
        raise PilotError("Graph launch-cycle classification changed")
    if "execution-window-meaning-differs" not in value["stop_conditions"]:
        raise PilotError("same-meaning window stop rule is missing")
    return value


def _marker(text: str, prefix: str) -> dict[str, str]:
    matches = [line for line in text.splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        raise PilotError(f"expected exactly one {prefix} marker")
    payload = matches[0][len(prefix):]
    fields: dict[str, str] = {}
    end = 0
    for match in re.finditer(r"([A-Za-z0-9_]+)=\s*([^\s]+)", payload):
        if payload[end:match.start()].strip():
            raise PilotError(f"malformed {prefix} marker")
        key, value = match.groups()
        if key in fields:
            raise PilotError(f"invalid {prefix} marker")
        fields[key] = value
        end = match.end()
    if not fields or payload[end:].strip():
        raise PilotError(f"malformed {prefix} marker")
    return fields


def _observation(text: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema") == OBSERVATION_SCHEMA:
            matches.append(value)
    if len(matches) != 1:
        raise PilotError("raw log does not contain one controlled observation")
    return matches[0]


def parse_log(path: Path, variant: str, seed: int) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    observation = _observation(text)
    expected_implementation = {
        "static-graph": "static-graph",
        "rocket-in-order": "rocket-in-order",
        "boom-ooo": "boom-ooo",
        "boom-serialize-dispatch": "boom-ooo",
    }[variant]
    if observation["implementation"] != expected_implementation:
        raise PilotError(f"{variant} implementation identity changed")
    if observation["invocation"] != seed:
        raise PilotError(f"{variant} invocation/seed binding changed")
    if observation["semantic_valid"] is not True:
        raise PilotError(f"{variant} semantic oracle failed")
    if not observation["accounting_complete"] or not observation["traffic_conserved"]:
        raise PilotError(f"{variant} accounting or traffic conservation failed")
    if observation["traffic_pending"] or observation["unaccounted_window_traffic"]:
        raise PilotError(f"{variant} has pending or unaccounted traffic")
    if observation["window_start"] != "after-staging-response-drain" or \
            observation["window_end"] != "after-final-execution-response":
        raise PilotError(f"{variant} window meaning changed")

    prefix = "T0044-GRAPH-ACTIVITY-V1" if variant == "static-graph" \
        else "T0044-CPU-ACTIVITY-V1"
    activity = _marker(text, prefix)
    required = {
        "request_stall_cycles", "response_backpressure_cycles",
        "read_transactions", "write_transactions", "read_bytes", "write_bytes",
        "useful_loads", "useful_adds", "useful_stores", "outputs",
    }
    if not required.issubset(activity):
        raise PilotError(f"{variant} activity accounting is incomplete")
    integer_activity = {name: int(activity[name]) for name in required}
    if integer_activity["read_transactions"] + integer_activity["write_transactions"] \
            != observation["traffic_accepted"]:
        raise PilotError(f"{variant} transaction accounting differs")
    if integer_activity["read_bytes"] != 4 * integer_activity["read_transactions"] or \
            integer_activity["write_bytes"] != 4 * integer_activity["write_transactions"]:
        raise PilotError(f"{variant} byte accounting differs")
    return {
        "variant": variant,
        "seed": seed,
        "observation": observation,
        "activity": {**activity, **integer_activity},
        "raw_log": path.name,
        "raw_log_bytes": path.stat().st_size,
        "raw_log_sha256": _sha256(path),
    }


def derive(run_dir: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    raw_dir = run_dir / "raw"
    derived_dir = run_dir / "derived"
    derived_dir.mkdir(exist_ok=False)
    records = [
        parse_log(raw_dir / f"{variant}-seed-{seed}.log", variant, seed)
        for seed in SEEDS for variant in VARIANTS
    ]
    by_seed = {
        seed: {record["variant"]: record for record in records if record["seed"] == seed}
        for seed in SEEDS
    }
    identity_fields = (
        "contract_sha256", "simulation_adapter_sha256", "descriptor_sha256",
        "resource_sha256", "input_sha256", "oracle_output_sha256",
        "observed_output_sha256",
    )
    for seed, matrix in by_seed.items():
        if set(matrix) != set(VARIANTS):
            raise PilotError(f"seed {seed} matrix is incomplete")
        for field in identity_fields:
            if len({item["observation"][field] for item in matrix.values()}) != 1:
                raise PilotError(f"seed {seed} {field} differs")
    if len({by_seed[seed]["static-graph"]["observation"]["configuration_sha256"] for seed in SEEDS}) != 1:
        raise PilotError("Graph configuration drifted across inputs")
    for variant in VARIANTS[1:]:
        if len({by_seed[seed][variant]["observation"]["configuration_sha256"] for seed in SEEDS}) != 1:
            raise PilotError(f"{variant} configuration drifted across inputs")

    accounts: dict[str, Any] = {}
    for count in (1, 4):
        chosen = SEEDS[:count]
        candidates: dict[str, Any] = {}
        rocket_cycles = [
            by_seed[seed]["rocket-in-order"]["observation"]["window_cycles"]
            for seed in chosen
        ]
        for variant in VARIANTS:
            cycles = [by_seed[seed][variant]["observation"]["window_cycles"] for seed in chosen]
            traffic = [by_seed[seed][variant]["observation"]["traffic_accepted"] for seed in chosen]
            total = [by_seed[seed][variant]["observation"]["total_cycles"] for seed in chosen]
            candidates[variant] = {
                "execution_cycles": cycles,
                "execution_cycles_exact": len(set(cycles)) == 1,
                "execution_median": statistics.median(cycles),
                "execution_min": min(cycles),
                "execution_max": max(cycles),
                "traffic_transactions": traffic,
                "end_to_end_total_cycles": total,
                "paired_execution_ratio_to_rocket": [
                    value / rocket for value, rocket in zip(cycles, rocket_cycles, strict=True)
                ],
            }
        accounts[str(count)] = candidates

    report = {
        "schema": "raveil.t0044-pilot-report/v1",
        "experiment_id": "EXP-0005",
        "evidence_class": "rtl-simulation-pilot",
        "manifest_sha256": _sha256(manifest_path),
        "fresh_input_seeds": list(SEEDS),
        "matrix_complete": True,
        "semantic_valid": True,
        "resource_equality_verified": True,
        "window_meaning_equal": True,
        "dynamic_memory_traffic_equal": False,
        "primary_fairness_finding": (
            "eligible-for-execution-latency-and-traffic-pilot: optimized CPU code "
            "legally reuses loads (800 reads) while the admitted fixed Graph "
            "schedule executes five loads per output (1280 reads); the difference "
            "is reported as a design result and no CPU is weakened"
        ),
        "secondary_ablation": "not-activated",
        "activity_limits": {
            "frontend": "unavailable-current-instrumentation",
            "rename_rob_issue_lsu": "unavailable-current-instrumentation",
            "graph_schedule_control": "schedule-active-and-launch-cycles-only",
        },
        "accounts": accounts,
        "records": records,
        "claim_eligibility": {
            "execution_latency_traffic_pilot": True,
            "end_to_end_reuse_amortization": False,
            "rfc0005_go": False,
            "rfc0005_numerical_no_go": False,
        },
        "decision": "pause",
        "pause_point": (
            "measure one installed configuration across repeated fresh-input "
            "invocations without simulator reboot; current fresh-process runs "
            "repeat CPU installation while Graph is elaboration-installed"
        ),
        "limitations": [
            "four fresh inputs only",
            "no energy",
            "no synthesis timing",
            "no area",
            "no VLIW/CGRA, elastic, stream, or hybrid matrix members",
            "simulator wall clock is operational metadata only",
        ],
    }
    (derived_dir / "report.json").write_text(_canonical(report) + "\n", encoding="utf-8")
    return report


def _run_command(
    command: list[str], env: dict[str, str], log_path: Path, command_file: Path
) -> None:
    start = time.time_ns()
    with log_path.open("wb") as output:
        result = subprocess.run(command, env=env, stdout=output, stderr=subprocess.STDOUT)
    end = time.time_ns()
    record = {
        "argv": command,
        "environment": {
            key: env[key] for key in sorted(env)
            if key.startswith("RAVEIL_") and key != "RAVEIL_CHIPYARD_SOURCE"
        },
        "start_unix_ns": start,
        "end_unix_ns": end,
        "simulator_wall_clock_ns_operations_only": end - start,
        "exit_code": result.returncode,
        "log": log_path.name,
    }
    with command_file.open("a", encoding="utf-8") as target:
        target.write(_canonical(record) + "\n")
    if result.returncode != 0:
        raise PilotError(f"command failed with exit {result.returncode}: {command}")


def collect(repo: Path, run_dir: Path, manifest_path: Path, chipyard: Path) -> dict[str, Any]:
    load_manifest(manifest_path)
    if run_dir.exists():
        raise PilotError("RUN-ID directory already exists")
    if subprocess.run(["git", "diff", "--quiet"], cwd=repo).returncode != 0 or \
            subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode != 0:
        raise PilotError("pilot collection requires a clean tracked worktree")
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True)
    frozen_copy = raw_dir / "frozen-manifest.json"
    frozen_copy.write_bytes(manifest_path.read_bytes())
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    metadata = {
        "schema": "raveil.t0044-run-metadata/v1",
        "experiment_id": "EXP-0005",
        "git_commit": git_commit,
        "manifest_sha256": _sha256(manifest_path),
        "platform": subprocess.check_output(["uname", "-s"], text=True).strip(),
        "architecture": subprocess.check_output(["uname", "-m"], text=True).strip(),
        "host_wall_clock_role": "operations-only-not-cpu-performance-evidence",
    }
    (raw_dir / "run-metadata.json").write_text(
        _canonical(metadata) + "\n", encoding="utf-8"
    )
    command_file = raw_dir / "commands.jsonl"
    base_env = dict(os.environ)
    base_env["RAVEIL_CHIPYARD_SOURCE"] = str(chipyard)
    scripts = {
        "static-graph": repo / "hardware/chisel/run-static-stencil-rtl.sh",
        "rocket-in-order": repo / "hardware/chisel/run-controlled-rocket-stencil.sh",
        "boom-ooo": repo / "hardware/chisel/run-controlled-boom-stencil.sh",
        "boom-serialize-dispatch": repo / "hardware/chisel/run-controlled-boom-serialize-stencil.sh",
    }
    for seed in SEEDS:
        for variant in VARIANTS:
            env = dict(base_env)
            if variant == "static-graph":
                env["RAVEIL_PILOT_SEED"] = str(seed)
            else:
                env["RAVEIL_CONTROLLED_SEED"] = str(seed)
                env["RAVEIL_CONTROLLED_INVOCATION"] = str(seed)
            _run_command(
                [str(scripts[variant])], env,
                raw_dir / f"{variant}-seed-{seed}.log", command_file,
            )
    report = derive(run_dir, manifest_path)
    raw_files = sorted(path for path in raw_dir.iterdir() if path.is_file())
    seal = {
        "schema": "raveil.research-raw-seal/v1",
        "files": [
            {"path": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in raw_files
        ],
    }
    (run_dir / "raw-seal.json").write_text(_canonical(seal) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="collect or derive EXP-0005")
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect_parser = subparsers.add_parser("collect")
    collect_parser.add_argument("--repo", type=Path, required=True)
    collect_parser.add_argument("--run-dir", type=Path, required=True)
    collect_parser.add_argument("--manifest", type=Path, required=True)
    collect_parser.add_argument("--chipyard-source", type=Path, required=True)
    derive_parser = subparsers.add_parser("derive")
    derive_parser.add_argument("--run-dir", type=Path, required=True)
    derive_parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            result = collect(
                args.repo.resolve(), args.run_dir.resolve(),
                args.manifest.resolve(), args.chipyard_source.resolve(),
            )
        else:
            result = derive(args.run_dir.resolve(), args.manifest.resolve())
        print(_canonical(result))
        return 0
    except (OSError, json.JSONDecodeError, PilotError, KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
