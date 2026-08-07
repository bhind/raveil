from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


@dataclass(frozen=True)
class Hardware:
    name: str = "toy-daphnis-v1"
    lanes: int = 16
    local_memory_kib: int = 64
    external_bytes_per_cycle: int = 32

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Hardware":
        return cls(**value)


@dataclass(frozen=True)
class Context:
    workload: str
    shape: int
    memory_budget_kib: int
    hardware: Hardware = Hardware()

    def __post_init__(self) -> None:
        if self.shape <= 0:
            raise ValueError("shape must be positive")
        if self.memory_budget_kib <= 0:
            raise ValueError("memory budget must be positive")

    def distance(self, other: "Context") -> float:
        workload = 0.0 if self.workload == other.workload else 8.0
        hardware = 0.0 if self.hardware.name == other.hardware.name else 4.0
        lanes = abs(math.log2(self.hardware.lanes / other.hardware.lanes))
        shape = abs(math.log2(self.shape / other.shape))
        memory = abs(math.log2(self.memory_budget_kib / other.memory_budget_kib))
        return workload + hardware + lanes + shape + 0.75 * memory

    def to_dict(self) -> dict[str, Any]:
        return {
            "workload": self.workload,
            "shape": self.shape,
            "memory_budget_kib": self.memory_budget_kib,
            "hardware": self.hardware.to_dict(),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Context":
        return cls(
            workload=value["workload"],
            shape=int(value["shape"]),
            memory_budget_kib=int(value["memory_budget_kib"]),
            hardware=Hardware.from_dict(value["hardware"]),
        )


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    vector_width: int
    tile_length: int
    memory_policy: str
    cold_prior: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Candidate":
        return cls(**value)


@dataclass(frozen=True)
class Metrics:
    cycles: int
    peak_memory_kib: float
    external_bytes: int
    energy_units: float
    valid: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Metrics":
        return cls(**value)


def seed_candidates() -> tuple[Candidate, ...]:
    return (
        Candidate("baseline", 1, 64, "keep", 1.00),
        Candidate("vector8", 8, 256, "keep", 0.92),
        Candidate("vector16", 16, 512, "keep", 0.94),
        Candidate("remat16", 16, 512, "rematerialize", 1.08),
        Candidate("spill8", 8, 256, "spill", 1.12),
    )

