from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from . import __version__
from .model import Candidate, Context, Metrics


SCHEMA = "raveil.experience/v0.0000000000001"


@dataclass(frozen=True)
class ExperienceRecord:
    sequence: int
    context: Context
    candidate: Candidate
    metrics: Metrics
    baseline_cycles: int
    samples: int = 1

    @property
    def relative_cycles(self) -> float:
        if not self.metrics.valid:
            return math.inf
        return self.metrics.cycles / max(1, self.baseline_cycles)

    @property
    def exact_key(self) -> tuple[object, ...]:
        return (
            self.context.workload,
            self.context.shape,
            self.context.memory_budget_kib,
            self.context.hardware.name,
            self.candidate.candidate_id,
            self.metrics.valid,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "raveil_version": __version__,
            "sequence": self.sequence,
            "samples": self.samples,
            "context": self.context.to_dict(),
            "candidate": self.candidate.to_dict(),
            "metrics": self.metrics.to_dict(),
            "baseline_cycles": self.baseline_cycles,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "ExperienceRecord":
        if value.get("schema") != SCHEMA:
            raise ValueError(f"unsupported Experience schema: {value.get('schema')}")
        return cls(
            sequence=int(value["sequence"]),
            samples=int(value.get("samples", 1)),
            context=Context.from_dict(value["context"]),  # type: ignore[arg-type]
            candidate=Candidate.from_dict(value["candidate"]),  # type: ignore[arg-type]
            metrics=Metrics.from_dict(value["metrics"]),  # type: ignore[arg-type]
            baseline_cycles=int(value["baseline_cycles"]),
        )


class ExperienceStore:
    """Append-only cold evidence plus a bounded in-memory episodic index."""

    def __init__(self, path: Path | None = None, active_limit: int = 256) -> None:
        if active_limit < 4:
            raise ValueError("active_limit must be at least 4")
        self.path = path
        self.active_limit = active_limit
        self._active: list[ExperienceRecord] = []
        self._cold_count = 0
        self._next_sequence = 1
        if path is not None and path.exists():
            self._load()

    @property
    def cold_count(self) -> int:
        return self._cold_count

    @property
    def active_count(self) -> int:
        return len(self._active)

    def append(
        self,
        context: Context,
        candidate: Candidate,
        metrics: Metrics,
        baseline_cycles: int,
    ) -> ExperienceRecord:
        record = ExperienceRecord(
            sequence=self._next_sequence,
            context=context,
            candidate=candidate,
            metrics=metrics,
            baseline_cycles=baseline_cycles,
        )
        self._next_sequence += 1
        self._cold_count += 1
        self._active.append(record)
        self._consolidate()
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as output:
                output.write(json.dumps(record.to_dict(), separators=(",", ":"), allow_nan=False))
                output.write("\n")
        return record

    def nearest(
        self,
        context: Context,
        candidate_id: str,
        limit: int = 12,
    ) -> list[tuple[float, ExperienceRecord]]:
        matches = [
            (context.distance(record.context), record)
            for record in self._active
            if record.candidate.candidate_id == candidate_id
        ]
        matches.sort(key=lambda item: (item[0], -item[1].sequence))
        return matches[:limit]

    def active_records(self) -> tuple[ExperienceRecord, ...]:
        return tuple(self._active)

    def fork(self) -> "ExperienceStore":
        """Copy the online state without sharing or extending the cold log."""
        clone = ExperienceStore(active_limit=self.active_limit)
        clone._active = list(self._active)
        clone._cold_count = self._cold_count
        clone._next_sequence = self._next_sequence
        return clone

    def _load(self) -> None:
        assert self.path is not None
        with self.path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                try:
                    record = ExperienceRecord.from_dict(json.loads(line))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise ValueError(f"invalid Experience record at line {line_number}: {error}") from error
                self._cold_count += record.samples
                self._next_sequence = max(self._next_sequence, record.sequence + 1)
                self._active.append(record)
                if len(self._active) >= self.active_limit * 2:
                    self._consolidate()
        self._consolidate()

    def _consolidate(self) -> None:
        if len(self._active) <= self.active_limit:
            return

        merged: dict[tuple[object, ...], ExperienceRecord] = {}
        for record in self._active:
            previous = merged.get(record.exact_key)
            if previous is None:
                merged[record.exact_key] = record
                continue
            total = previous.samples + record.samples
            if previous.metrics.valid and record.metrics.valid:
                cycles = round(
                    (previous.metrics.cycles * previous.samples + record.metrics.cycles * record.samples)
                    / total
                )
                energy = (
                    previous.metrics.energy_units * previous.samples
                    + record.metrics.energy_units * record.samples
                ) / total
                metrics = replace(record.metrics, cycles=cycles, energy_units=energy)
            else:
                metrics = record.metrics
            baseline = round(
                (previous.baseline_cycles * previous.samples + record.baseline_cycles * record.samples)
                / total
            )
            merged[record.exact_key] = replace(
                record,
                metrics=metrics,
                baseline_cycles=baseline,
                samples=total,
            )

        ranked = sorted(merged.values(), key=self._retention_score, reverse=True)
        self._active = ranked[: self.active_limit]

    @staticmethod
    def _retention_score(record: ExperienceRecord) -> tuple[float, float, int]:
        if not record.metrics.valid:
            tail = 8.0
        else:
            tail = abs(math.log2(max(record.relative_cycles, 1e-9)))
            if record.relative_cycles > 1.0:
                tail += 1.0
        signature = json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(signature.encode("utf-8")).digest()
        jitter = int.from_bytes(digest[:8], "big") / 2**64
        return (tail, jitter, record.sequence)


def export_records(records: Iterable[ExperienceRecord]) -> list[dict[str, object]]:
    return [record.to_dict() for record in records]
