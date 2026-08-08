from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess

from .analysis import analyze_policy_outcomes
from .experiment_schema import (
    BenchmarkCandidate,
    BenchmarkManifest,
    EnvironmentSignature,
    MeasurementRecord,
    PolicyOutcome,
)
from .native_backend import NativeCBackend, NativeMeasurement
from .power import PowerSample, PowermetricsSampler
from .research_bundle import ResearchBundle, make_run_id, manifest_hash


def _command_output(command: tuple[str, ...], default: str = "unknown") -> str:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return default
    if completed.returncode != 0:
        return default
    return completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else default


def git_sha() -> str:
    value = _command_output(("git", "rev-parse", "HEAD"), "")
    if not value or len(value) < 12:
        raise RuntimeError("experiment run requires a Git worktree with a resolved HEAD")
    return value


def git_root() -> Path:
    value = _command_output(("git", "rev-parse", "--show-toplevel"), "")
    if not value:
        raise RuntimeError("experiment run requires a Git worktree")
    return Path(value)


def require_clean_worktree() -> None:
    completed = subprocess.run(
        ("git", "status", "--porcelain", "--untracked-files=all"),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or completed.stdout.strip():
        raise RuntimeError("experiment run requires a clean tracked/untracked Git worktree")


def environment_signature(
    run_id: str, evidence_class: str, compiler: str = "cc"
) -> EnvironmentSignature:
    os_version = _command_output(("sw_vers", "-productVersion"), platform.version())
    cpu_model = _command_output(("sysctl", "-n", "machdep.cpu.brand_string"), platform.machine())
    compiler_version = _command_output((compiler, "--version"))
    return EnvironmentSignature(
        run_id=run_id,
        git_sha=git_sha(),
        platform_system=platform.system(),
        platform_release=platform.release(),
        machine=platform.machine(),
        os_version=os_version,
        cpu_model=cpu_model,
        python_version=platform.python_version(),
        compiler_version=compiler_version,
        tool_versions={
            "rclone": _command_output(("rclone", "version"), "not-invoked"),
            "powermetrics": _command_output(("/usr/bin/powermetrics", "--help")),
        },
        evidence_class=evidence_class,  # type: ignore[arg-type]
    )


def measurement_order(
    candidates: tuple[BenchmarkCandidate, ...], repetitions: int, seed: int
) -> list[tuple[BenchmarkCandidate, int, str]]:
    baseline = candidates[0]
    scheduled = [
        (candidate, repetition, "randomized")
        for candidate in candidates
        for repetition in range(repetitions)
        if not (candidate == baseline and repetition == 0)
    ]
    random.Random(seed).shuffle(scheduled)
    return [(baseline, 0, "trusted-baseline"), *scheduled]


def run_experiment(
    manifest_path: Path,
    artifact_root: Path,
    compiler: str = "cc",
) -> tuple[ResearchBundle, bool]:
    require_clean_worktree()
    manifest = BenchmarkManifest.load(manifest_path)
    if manifest.backend != "native-c":
        raise RuntimeError("TVM execution is deferred until the fixed-C pilot is stable")
    if manifest.energy.required and (
        platform.system() != "Darwin" or platform.machine() != "arm64"
    ):
        raise RuntimeError("the Gate 1 powermetrics contract requires Apple Silicon macOS")
    digest = manifest_hash(manifest.to_dict())
    sha = git_sha()
    run_id = make_run_id(sha, digest)
    sampler = PowermetricsSampler(
        interval_ms=manifest.energy.sample_interval_ms,
        stable_levels=manifest.energy.stable_thermal_levels,
    )
    if manifest.energy.required:
        preflight = sampler.preflight()
        if not preflight.valid:
            raise RuntimeError(f"powermetrics preflight failed closed: {preflight.failure}")
    bundle = ResearchBundle(artifact_root, manifest.experiment_id, run_id)
    bundle.create()
    signature = environment_signature(run_id, manifest.evidence_class, compiler)
    bundle.write_json("manifest.json", manifest.to_dict())
    bundle.write_json("environment.json", signature.to_dict())
    source = Path(manifest.source)
    if source.is_absolute():
        raise ValueError("manifest source must be a repository-relative path")
    source = git_root() / source
    if not source.is_file():
        raise FileNotFoundError(f"manifest source does not exist: {manifest.source}")
    bundled_source = bundle.path / "sources" / "benchmark.c"
    bundled_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, bundled_source)
    backend = NativeCBackend(
        source=bundled_source,
        binary=bundle.path / "tools" / "native-benchmark",
        compiler=compiler,
        compiler_flags=manifest.compiler_flags,
        timeout_seconds=manifest.timeout_seconds,
        warmups=manifest.warmups,
    )
    compile_command = backend.compile()
    bundle.write_json(
        "commands.json",
        {
            "compile": [compiler, *manifest.compiler_flags, manifest.source, "-o", "tools/native-benchmark"],
            "run": ["python", "-m", "raveil", "experiment", "run", "--manifest", "<manifest>"],
        },
    )
    sequence = 0
    all_valid = True
    for workload_index, workload in enumerate(manifest.workloads):
        order = measurement_order(
            manifest.candidates,
            manifest.repetitions,
            manifest.random_seed + workload_index,
        )
        for candidate, repetition, phase in order:
            sequence += 1
            raw_path = bundle.path / "powermetrics" / f"{sequence:06d}.txt"

            def operation() -> NativeMeasurement:
                return backend.measure(workload, candidate)

            if manifest.energy.required:
                native, power = sampler.measure(operation, raw_path)
            else:
                native = operation()
                power = PowerSample(None, None, True)
            if native is None:
                native = NativeMeasurement(None, None, None, False, "benchmark not run")
            latency = native.latency_ns
            energy = None
            if latency is not None and power.cpu_power_mw is not None:
                energy = power.cpu_power_mw * latency / 1_000_000_000.0
            measurement_valid = native.semantic_valid and power.valid and latency is not None
            failure = "; ".join(part for part in (native.failure, power.failure) if part)
            record = MeasurementRecord(
                run_id=run_id,
                sequence=sequence,
                measured_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                workload_id=workload.workload_id,
                candidate_id=candidate.candidate_id,
                repetition=repetition,
                phase=phase,  # type: ignore[arg-type]
                latency_ns=latency,
                cpu_power_mw=power.cpu_power_mw,
                energy_mj=energy,
                checksum=native.checksum,
                reference_checksum=native.reference_checksum,
                semantic_valid=native.semantic_valid,
                measurement_valid=measurement_valid,
                failure=failure,
                thermal_level=power.thermal_level,
                evidence_class=manifest.evidence_class,
            )
            bundle.append_jsonl("measurement.jsonl", record.to_dict())
            all_valid &= measurement_valid
            if manifest.energy.required and not power.valid:
                bundle.write_json(
                    "run-failure.json",
                    {"sequence": sequence, "failure": failure, "fail_closed": True},
                )
                return bundle, False
    bundle.write_json(
        "run-summary.json",
        {
            "run_id": run_id,
            "records": sequence,
            "all_measurements_valid": all_valid,
            "compile_command_recorded": bool(compile_command),
        },
    )
    return bundle, all_valid


def find_bundle(artifact_root: Path, run_id: str) -> ResearchBundle:
    matches = [path for path in artifact_root.glob(f"EXP-[0-9][0-9][0-9][0-9]/{run_id}") if path.is_dir()]
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one local bundle for RUN-ID {run_id}, found {len(matches)}")
    return ResearchBundle(artifact_root, matches[0].parent.name, run_id)


def _read_jsonl(path: Path, factory: object) -> list[object]:
    values = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                values.append(factory.from_dict(value))  # type: ignore[attr-defined]
            except (json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
                raise ValueError(f"invalid JSONL at {path.name}:{line_number}: {error}") from error
    return values


def analyze_bundle(bundle: ResearchBundle, bootstrap_samples: int = 10_000) -> dict[str, object]:
    bundle.require_mutable()
    manifest = BenchmarkManifest.from_dict(
        json.loads((bundle.path / "manifest.json").read_text(encoding="utf-8"))
    )
    records = _read_jsonl(bundle.path / "measurement.jsonl", MeasurementRecord)
    grouped: dict[tuple[str, str], list[MeasurementRecord]] = {}
    for raw in records:
        record = raw  # type: ignore[assignment]
        grouped.setdefault((record.workload_id, record.candidate_id), []).append(record)
    semantic_ok = all(
        record.semantic_valid
        and record.checksum is not None
        and record.checksum == record.reference_checksum
        for record in records  # type: ignore[attr-defined]
    )
    measurements_ok = all(
        record.measurement_valid
        and record.latency_ns is not None
        and (not manifest.energy.required or record.energy_mj is not None)
        for record in records  # type: ignore[attr-defined]
    )
    repetitions_ok = all(len(values) >= manifest.repetitions for values in grouped.values())
    expected_groups = len(manifest.workloads) * len(manifest.candidates)
    complete_matrix = len(grouped) == expected_groups
    policy_path = bundle.path / "policy-outcomes.jsonl"
    if policy_path.exists():
        outcomes = _read_jsonl(policy_path, PolicyOutcome)
        policy = analyze_policy_outcomes(
            outcomes, manifest.active_memory_limit, bootstrap_samples=bootstrap_samples  # type: ignore[arg-type]
        )
    else:
        policy = {
            "gate_ready": False,
            "unmet": ["pre-registered cold/bounded/full-history PolicyOutcome evidence is absent"],
        }
    unmet = []
    if not semantic_ok:
        unmet.append("one or more semantic checksums failed")
    if not measurements_ok:
        unmet.append("one or more latency/energy measurements failed closed")
    if not repetitions_ok or not complete_matrix:
        unmet.append("candidate measurement matrix is incomplete")
    unmet.extend(policy.get("unmet", []))  # type: ignore[arg-type]
    unmet.extend(
        [
            "independent rerun comparison is not attached",
            "fixed-C versus pinned TVM conclusion is not available",
            "remote immutable bundle verification has not occurred",
        ]
    )
    result: dict[str, object] = {
        "schema": "raveil.experiment-analysis/v1",
        "run_id": bundle.run_id,
        "evidence_class": manifest.evidence_class,
        "semantic_checksums_pass": semantic_ok,
        "all_measurements_valid": measurements_ok,
        "complete_measurement_matrix": complete_matrix and repetitions_ok,
        "policy": policy,
        "gate_conclusion": "incomplete",
        "unmet": unmet,
        "claims": [],
        "non_claims": [
            "No RISC-V or Daphnis hardware performance claim",
            "powermetrics energy is an estimated same-Mac relative metric only",
        ],
    }
    bundle.write_json("analysis.json", result)
    return result


def seal_bundle(bundle: ResearchBundle) -> dict[str, object]:
    if not (bundle.path / "analysis.json").is_file():
        raise RuntimeError("analyze the run before sealing")
    environment = json.loads((bundle.path / "environment.json").read_text(encoding="utf-8"))
    return bundle.seal(
        command=("python", "-m", "raveil", "experiment", "seal", "--run", bundle.run_id),
        tool_versions=environment["tool_versions"],
        environment_signature=environment,
    )
