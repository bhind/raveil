from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Literal


MANIFEST_SCHEMA = "raveil.benchmark-manifest/v1"
ENVIRONMENT_SCHEMA = "raveil.environment-signature/v1"
MEASUREMENT_SCHEMA = "raveil.measurement-record/v1"
POLICY_OUTCOME_SCHEMA = "raveil.policy-outcome/v1"
BUNDLE_SCHEMA = "raveil.research-bundle/v1"

EvidenceClass = Literal["analytical", "simulation", "emulation", "fpga", "silicon"]


def validate_backend_evidence(backend: str, evidence_class: str) -> None:
    required = {
        "native-c": "silicon",
        "tvm-meta-schedule": "silicon",
        "qemu-telemetry": "emulation",
    }
    if backend in required and evidence_class != required[backend]:
        raise ValueError(f"{backend} evidence must be classified as {required[backend]}")


def _require_keys(value: dict[str, Any], keys: set[str], kind: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise ValueError(f"{kind} is missing fields: {', '.join(missing)}")


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    family: Literal["gemm", "gemm_bias_relu", "mlp2"]
    m: int
    n: int
    k: int
    lineage: str
    shape_class: str
    working_set: str
    operator_composition: str
    inner_iterations: int = 1

    def __post_init__(self) -> None:
        if min(self.m, self.n, self.k, self.inner_iterations) <= 0:
            raise ValueError(f"workload {self.workload_id} dimensions must be positive")
        if max(self.m, self.n, self.k) > 512 or self.inner_iterations > 1_000_000:
            raise ValueError(f"workload {self.workload_id} exceeds native safety bounds")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "WorkloadSpec":
        return cls(**value)


@dataclass(frozen=True)
class BenchmarkCandidate:
    candidate_id: str
    loop_order: Literal["ijk", "ikj", "tiled"]
    tile: int
    materialization: Literal["fused", "materialized"]
    cold_priority: int
    trusted_baseline: bool = False

    def __post_init__(self) -> None:
        if self.tile not in {0, 8, 16, 32, 64}:
            raise ValueError(f"candidate {self.candidate_id} has unsupported tile {self.tile}")
        if self.loop_order == "tiled" and self.tile == 0:
            raise ValueError(f"candidate {self.candidate_id} requires a tile")
        if self.loop_order != "tiled" and self.tile != 0:
            raise ValueError(f"candidate {self.candidate_id} must not set a tile")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BenchmarkCandidate":
        return cls(**value)


@dataclass(frozen=True)
class EnergyContract:
    required: bool
    sampler: Literal["powermetrics"]
    sample_interval_ms: int
    minimum_samples: int = 3
    stable_thermal_levels: tuple[str, ...] = ("Nominal",)

    def __post_init__(self) -> None:
        if self.sample_interval_ms < 20:
            raise ValueError("powermetrics sample interval must be at least 20 ms")
        if self.minimum_samples < 1:
            raise ValueError("powermetrics minimum sample count must be positive")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EnergyContract":
        copied = dict(value)
        copied["stable_thermal_levels"] = tuple(copied.get("stable_thermal_levels", ("Nominal",)))
        return cls(**copied)


@dataclass(frozen=True)
class BenchmarkManifest:
    experiment_id: str
    backend: Literal["native-c", "tvm-meta-schedule", "qemu-telemetry"]
    evidence_class: EvidenceClass
    repetitions: int
    warmups: int
    random_seed: int
    timeout_seconds: float
    measurement_budget: int
    active_memory_limit: int
    source: str
    compiler_flags: tuple[str, ...]
    energy: EnergyContract
    workloads: tuple[WorkloadSpec, ...]
    candidates: tuple[BenchmarkCandidate, ...]
    tvm_version: str | None = None
    stage: Literal["pilot", "full"] = "full"
    schema: str = MANIFEST_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != MANIFEST_SCHEMA:
            raise ValueError(f"unsupported benchmark manifest schema: {self.schema}")
        validate_backend_evidence(self.backend, self.evidence_class)
        minimum_repetitions = 15 if self.stage == "full" else 3
        if self.repetitions < minimum_repetitions:
            raise ValueError(
                f"{self.stage} manifest requires at least {minimum_repetitions} repetitions"
            )
        if self.warmups < 1:
            raise ValueError("Gate 1 requires at least one warm-up")
        if self.timeout_seconds <= 0 or self.measurement_budget < 1:
            raise ValueError("timeout and measurement budget must be positive")
        if self.active_memory_limit < 4:
            raise ValueError("active memory limit must be at least four")
        minimum_workloads = 20 if self.stage == "full" else 3
        if len(self.workloads) < minimum_workloads:
            raise ValueError(
                f"{self.stage} manifest must pre-register at least {minimum_workloads} workloads"
            )
        if not self.candidates:
            raise ValueError("manifest must contain candidates")
        baselines = [candidate for candidate in self.candidates if candidate.trusted_baseline]
        if len(baselines) != 1 or self.candidates[0] != baselines[0]:
            raise ValueError("exactly one trusted baseline must be the first candidate")
        if len({w.workload_id for w in self.workloads}) != len(self.workloads):
            raise ValueError("workload IDs must be unique")
        if len({c.candidate_id for c in self.candidates}) != len(self.candidates):
            raise ValueError("candidate IDs must be unique")
        dimensions = {
            "lineage": {w.lineage for w in self.workloads},
            "shape": {w.shape_class for w in self.workloads},
            "working-set": {w.working_set for w in self.workloads},
            "composition": {w.operator_composition for w in self.workloads},
        }
        if self.stage == "full" and any(len(values) < 2 for values in dimensions.values()):
            raise ValueError("holdouts must vary lineage, shape, working set, and composition")
        if self.stage == "pilot" and len({w.family for w in self.workloads}) < 3:
            raise ValueError("pilot manifest must cover all three native workload families")
        if self.backend == "tvm-meta-schedule" and not self.tvm_version:
            raise ValueError("TVM manifests must pin tvm_version")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BenchmarkManifest":
        _require_keys(
            value,
            {
                "schema", "experiment_id", "backend", "evidence_class", "repetitions",
                "warmups", "random_seed", "timeout_seconds", "measurement_budget",
                "active_memory_limit", "source", "compiler_flags", "energy", "workloads",
                "candidates",
            },
            "benchmark manifest",
        )
        copied = dict(value)
        copied["compiler_flags"] = tuple(copied["compiler_flags"])
        copied["energy"] = EnergyContract.from_dict(copied["energy"])
        copied["workloads"] = tuple(WorkloadSpec.from_dict(item) for item in copied["workloads"])
        copied["candidates"] = tuple(
            BenchmarkCandidate.from_dict(item) for item in copied["candidates"]
        )
        return cls(**copied)

    @classmethod
    def load(cls, path: Path) -> "BenchmarkManifest":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid benchmark manifest JSON: {error}") from error
        if not isinstance(value, dict):
            raise ValueError("benchmark manifest must be a JSON object")
        return cls.from_dict(value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EnvironmentSignature:
    run_id: str
    git_sha: str
    platform_system: str
    platform_release: str
    machine: str
    os_version: str
    cpu_model: str
    python_version: str
    compiler_version: str
    tool_versions: dict[str, str]
    evidence_class: EvidenceClass
    schema: str = ENVIRONMENT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MeasurementRecord:
    run_id: str
    sequence: int
    measured_at_utc: str
    workload_id: str
    candidate_id: str
    repetition: int
    phase: Literal["trusted-baseline", "randomized"]
    latency_ns: int | None
    cpu_power_mw: float | None
    energy_mj: float | None
    checksum: str | None
    reference_checksum: str | None
    semantic_valid: bool
    measurement_valid: bool
    failure: str
    thermal_level: str | None
    evidence_class: EvidenceClass
    power_sample_count: int = 0
    schema: str = MEASUREMENT_SCHEMA

    def __post_init__(self) -> None:
        if self.sequence < 1 or self.repetition < 0:
            raise ValueError("measurement sequence/repetition is invalid")
        if self.latency_ns is not None and self.latency_ns <= 0:
            raise ValueError("measurement latency must be positive")
        if self.cpu_power_mw is not None and self.cpu_power_mw < 0:
            raise ValueError("CPU power must not be negative")
        if self.energy_mj is not None and self.energy_mj < 0:
            raise ValueError("energy must not be negative")
        if self.power_sample_count < 0:
            raise ValueError("power sample count must not be negative")
        if self.semantic_valid and (
            self.checksum is None or self.checksum != self.reference_checksum
        ):
            raise ValueError("semantic-valid measurement requires equal checksums")
        if self.measurement_valid and (not self.semantic_valid or self.latency_ns is None):
            raise ValueError("measurement-valid record requires semantics and latency")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MeasurementRecord":
        if value.get("schema") != MEASUREMENT_SCHEMA:
            raise ValueError(f"unsupported MeasurementRecord schema: {value.get('schema')}")
        return cls(**value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyOutcome:
    run_id: str
    workload_id: str
    policy: str
    selected_candidate_id: str
    baseline_latency_ns: float
    selected_latency_ns: float
    oracle_latency_ns: float
    baseline_energy_mj: float
    selected_energy_mj: float
    oracle_energy_mj: float
    measurement_budget: int
    retrieval_latency_ns: int
    active_memory_records: int
    cold_evidence_records: int
    schema: str = POLICY_OUTCOME_SCHEMA

    def __post_init__(self) -> None:
        metrics = (
            self.baseline_latency_ns,
            self.selected_latency_ns,
            self.oracle_latency_ns,
            self.baseline_energy_mj,
            self.selected_energy_mj,
            self.oracle_energy_mj,
        )
        if any(value <= 0 for value in metrics):
            raise ValueError("PolicyOutcome latency and energy values must be positive")
        if self.measurement_budget < 1 or self.retrieval_latency_ns < 0:
            raise ValueError("PolicyOutcome budget/retrieval values are invalid")
        if self.active_memory_records < 0 or self.cold_evidence_records < 0:
            raise ValueError("PolicyOutcome evidence sizes must not be negative")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PolicyOutcome":
        if value.get("schema") != POLICY_OUTCOME_SCHEMA:
            raise ValueError(f"unsupported PolicyOutcome schema: {value.get('schema')}")
        return cls(**value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
