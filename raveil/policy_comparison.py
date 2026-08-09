from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import time

from .experiment_schema import (
    BenchmarkCandidate,
    BenchmarkManifest,
    MeasurementRecord,
    PolicyOutcome,
    PolicySelection,
    WorkloadSpec,
)
from .research_bundle import ResearchBundle, canonical_json, manifest_hash


COMPARISON_POLICIES = (
    "cold", "full-history", "bounded", "fifo", "reservoir", "random"
)


@dataclass(frozen=True)
class HistoryEntry:
    sequence: int
    workload: WorkloadSpec
    candidate_id: str
    latency_ratio: float
    energy_ratio: float


def _read_jsonl(path: Path, factory: object) -> list[object]:
    values: list[object] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                values.append(factory.from_dict(json.loads(line)))  # type: ignore[attr-defined]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"invalid JSONL at {path.name}:{line_number}: {error}") from error
    return values


def _write_jsonl(path: Path, values: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        for value in values:
            target.write(canonical_json(value.to_dict()))  # type: ignore[attr-defined]
            target.write("\n")


def workload_distance(left: WorkloadSpec, right: WorkloadSpec) -> float:
    family = 0.0 if left.family == right.family else 8.0
    lineage = 0.0 if left.lineage == right.lineage else 1.5
    shape = sum(
        abs(math.log2(a / b)) for a, b in ((left.m, right.m), (left.n, right.n), (left.k, right.k))
    )
    working_set = 0.0 if left.working_set == right.working_set else 0.75
    composition = 0.0 if left.operator_composition == right.operator_composition else 2.0
    return family + lineage + shape + working_set + composition


def _measurement_medians(
    manifest: BenchmarkManifest, records: list[MeasurementRecord]
) -> dict[tuple[str, str], tuple[float, float, int]]:
    expected_run_ids = {record.run_id for record in records}
    if len(expected_run_ids) != 1:
        raise ValueError("source measurements must have exactly one RUN-ID")
    summaries: dict[tuple[str, str], tuple[float, float, int]] = {}
    for workload in manifest.workloads:
        for candidate in manifest.candidates:
            matching = [
                record
                for record in records
                if record.workload_id == workload.workload_id
                and record.candidate_id == candidate.candidate_id
            ]
            if len(matching) != manifest.repetitions or any(
                not record.semantic_valid
                or not record.measurement_valid
                or record.latency_ns is None
                or record.energy_mj is None
                for record in matching
            ):
                raise ValueError(
                    f"source evidence is incomplete for {workload.workload_id}/{candidate.candidate_id}"
                )
            summaries[(workload.workload_id, candidate.candidate_id)] = (
                statistics.median(float(record.latency_ns) for record in matching),
                statistics.median(float(record.energy_mj) for record in matching),
                max(record.sequence for record in matching),
            )
    return summaries


def build_history(
    manifest: BenchmarkManifest, records: list[MeasurementRecord]
) -> list[HistoryEntry]:
    summaries = _measurement_medians(manifest, records)
    baseline_id = manifest.candidates[0].candidate_id
    entries: list[HistoryEntry] = []
    for workload in manifest.workloads:
        baseline_latency, baseline_energy, _ = summaries[(workload.workload_id, baseline_id)]
        for candidate in manifest.candidates:
            latency, energy, sequence = summaries[(workload.workload_id, candidate.candidate_id)]
            entries.append(
                HistoryEntry(
                    sequence=sequence,
                    workload=workload,
                    candidate_id=candidate.candidate_id,
                    latency_ratio=latency / baseline_latency,
                    energy_ratio=energy / baseline_energy,
                )
            )
    return sorted(entries, key=lambda entry: entry.sequence)


def _tail_score(entry: HistoryEntry) -> tuple[float, int]:
    tail = abs(math.log2(entry.latency_ratio)) + abs(math.log2(entry.energy_ratio))
    if entry.latency_ratio > 1.02 or entry.energy_ratio > 1.02:
        tail += 2.0
    signature = (
        f"{entry.workload.workload_id}:{entry.candidate_id}:"
        f"{entry.latency_ratio:.17g}:{entry.energy_ratio:.17g}:{entry.sequence}"
    )
    jitter = int.from_bytes(hashlib.sha256(signature.encode()).digest()[:8], "big")
    return tail, jitter


def retain_history(
    entries: list[HistoryEntry], policy: str, active_limit: int, seed: int
) -> list[HistoryEntry]:
    if policy == "full-history":
        return list(entries)
    if policy == "bounded":
        return sorted(entries, key=_tail_score, reverse=True)[:active_limit]
    if policy == "fifo":
        return entries[-active_limit:]
    if policy == "reservoir":
        randomizer = random.Random(seed)
        reservoir: list[HistoryEntry] = []
        for index, entry in enumerate(entries):
            if index < active_limit:
                reservoir.append(entry)
                continue
            replacement = randomizer.randrange(index + 1)
            if replacement < active_limit:
                reservoir[replacement] = entry
        return reservoir
    if policy == "random":
        randomizer = random.Random(seed)
        return randomizer.sample(entries, min(active_limit, len(entries)))
    if policy == "cold":
        return []
    raise ValueError(f"unknown retention policy: {policy}")


def _rank_slate(
    target: WorkloadSpec,
    candidates: tuple[BenchmarkCandidate, ...],
    history: list[HistoryEntry],
    budget: int,
) -> tuple[tuple[str, ...], float, float, bool]:
    baseline = candidates[0]
    ranked: list[tuple[float, str, float, float]] = []
    for candidate in candidates[1:]:
        neighbors = sorted(
            (
                (workload_distance(target, entry.workload), entry)
                for entry in history
                if entry.candidate_id == candidate.candidate_id
            ),
            key=lambda item: (item[0], -item[1].sequence),
        )[:12]
        if not neighbors:
            ranked.append((1.0 + candidate.cold_priority, candidate.candidate_id, 1.0, 1.0))
            continue
        weights = [1.0 / (1.0 + distance) ** 2 for distance, _ in neighbors]
        latency = sum(
            weight * entry.latency_ratio
            for weight, (_, entry) in zip(weights, neighbors, strict=True)
        ) / sum(weights)
        energy = sum(
            weight * entry.energy_ratio
            for weight, (_, entry) in zip(weights, neighbors, strict=True)
        ) / sum(weights)
        score = math.sqrt(latency * energy) + 0.01 * neighbors[0][0]
        ranked.append((score, candidate.candidate_id, latency, energy))
    ranked.sort(key=lambda item: (item[0], item[1]))
    chosen = ranked[: max(0, budget - 1)]
    slate = (baseline.candidate_id, *(item[1] for item in chosen))
    predictions = [(1.0, 1.0), *((item[2], item[3]) for item in chosen)]
    best_prediction = min(predictions, key=lambda value: math.sqrt(value[0] * value[1]))
    return slate, best_prediction[0], best_prediction[1], not bool(history)


def generate_policy_selections(
    target_manifest: BenchmarkManifest,
    source_manifest: BenchmarkManifest,
    source_records: list[MeasurementRecord],
    source_bundle_sha256: str,
    registered_at: datetime | None = None,
) -> list[PolicySelection]:
    if target_manifest.backend != source_manifest.backend:
        raise ValueError("source and target policy manifests must use the same backend")
    if target_manifest.evidence_class != source_manifest.evidence_class:
        raise ValueError("source and target policy evidence classes must match")
    if {item.candidate_id for item in target_manifest.candidates} != {
        item.candidate_id for item in source_manifest.candidates
    }:
        raise ValueError("source and target candidate sets must match")
    if {item.workload_id for item in target_manifest.workloads} & {
        item.workload_id for item in source_manifest.workloads
    }:
        raise ValueError("source and target workload IDs must be disjoint")
    history = build_history(source_manifest, source_records)
    source_run_ids = {record.run_id for record in source_records}
    if len(source_run_ids) != 1:
        raise ValueError("source policy evidence must have exactly one RUN-ID")
    source_run_id = next(iter(source_run_ids))
    timestamp = (registered_at or datetime.now(timezone.utc)).isoformat()
    digest = manifest_hash(target_manifest.to_dict())
    source_max = max(entry.sequence for entry in history)
    selections: list[PolicySelection] = []
    for policy_index, policy in enumerate(COMPARISON_POLICIES):
        retained = retain_history(
            history,
            policy,
            target_manifest.active_memory_limit,
            target_manifest.random_seed + policy_index,
        )
        for workload in target_manifest.workloads:
            started = time.perf_counter_ns()
            slate, predicted_latency, predicted_energy, abstained = _rank_slate(
                workload,
                target_manifest.candidates,
                retained,
                target_manifest.measurement_budget,
            )
            retrieval = time.perf_counter_ns() - started
            selections.append(
                PolicySelection(
                    experiment_id=target_manifest.experiment_id,
                    manifest_sha256=digest,
                    registered_at_utc=timestamp,
                    workload_id=workload.workload_id,
                    policy=policy,  # type: ignore[arg-type]
                    candidate_ids=slate,
                    measurement_budget=target_manifest.measurement_budget,
                    source_run_id=source_run_id,
                    source_bundle_sha256=source_bundle_sha256,
                    source_evidence_max_sequence=source_max,
                    retrieval_latency_ns=retrieval,
                    active_memory_records=len(retained),
                    cold_evidence_records=len(history),
                    predicted_latency_ratio=predicted_latency,
                    predicted_energy_ratio=predicted_energy,
                    abstained=abstained,
                )
            )
    return selections


def validate_policy_selections(
    manifest: BenchmarkManifest,
    selections: list[PolicySelection],
    before: datetime | None = None,
) -> None:
    expected = {
        (policy, workload.workload_id)
        for policy in COMPARISON_POLICIES
        for workload in manifest.workloads
    }
    seen: set[tuple[str, str]] = set()
    digest = manifest_hash(manifest.to_dict())
    candidate_ids = {candidate.candidate_id for candidate in manifest.candidates}
    deadline = before or datetime.now(timezone.utc)
    for selection in selections:
        key = (selection.policy, selection.workload_id)
        if key in seen:
            raise ValueError(f"duplicate PolicySelection: {selection.policy}/{selection.workload_id}")
        seen.add(key)
        if selection.experiment_id != manifest.experiment_id:
            raise ValueError("PolicySelection experiment does not match target manifest")
        if selection.manifest_sha256 != digest:
            raise ValueError("PolicySelection manifest hash does not match target manifest")
        if selection.measurement_budget != manifest.measurement_budget:
            raise ValueError("PolicySelection budget does not match target manifest")
        if set(selection.candidate_ids) - candidate_ids:
            raise ValueError("PolicySelection contains an unregistered candidate")
        registered = datetime.fromisoformat(
            selection.registered_at_utc.replace("Z", "+00:00")
        )
        if registered >= deadline:
            raise ValueError("PolicySelection must be registered before target measurement")
    if seen != expected:
        raise ValueError(
            f"PolicySelection comparison matrix mismatch: expected {len(expected)}, found {len(seen)}"
        )


def generate_policy_outcomes(
    manifest: BenchmarkManifest,
    run_id: str,
    records: list[MeasurementRecord],
    selections: list[PolicySelection],
) -> list[PolicyOutcome]:
    summaries = _measurement_medians(manifest, records)
    baseline_id = manifest.candidates[0].candidate_id
    outcomes: list[PolicyOutcome] = []
    for selection in selections:
        baseline_latency, baseline_energy, _ = summaries[
            (selection.workload_id, baseline_id)
        ]
        measured_slate = [
            (candidate_id, summaries[(selection.workload_id, candidate_id)])
            for candidate_id in selection.candidate_ids
        ]
        selected_id, selected_summary = min(
            measured_slate,
            key=lambda item: (
                math.sqrt(
                    item[1][0] / baseline_latency * item[1][1] / baseline_energy
                ),
                item[0],
            ),
        )
        workload_summaries = [
            summary
            for (workload_id, _), summary in summaries.items()
            if workload_id == selection.workload_id
        ]
        outcomes.append(
            PolicyOutcome(
                run_id=run_id,
                workload_id=selection.workload_id,
                policy=selection.policy,
                selected_candidate_id=selected_id,
                baseline_latency_ns=baseline_latency,
                selected_latency_ns=selected_summary[0],
                oracle_latency_ns=min(item[0] for item in workload_summaries),
                baseline_energy_mj=baseline_energy,
                selected_energy_mj=selected_summary[1],
                oracle_energy_mj=min(item[1] for item in workload_summaries),
                measurement_budget=selection.measurement_budget,
                retrieval_latency_ns=selection.retrieval_latency_ns,
                active_memory_records=selection.active_memory_records,
                cold_evidence_records=selection.cold_evidence_records,
                predicted_latency_ratio=selection.predicted_latency_ratio,
                predicted_energy_ratio=selection.predicted_energy_ratio,
                abstained=selection.abstained,
            )
        )
    return outcomes


def write_policy_selections(path: Path, selections: list[PolicySelection]) -> None:
    _write_jsonl(path, selections)


def write_policy_outcomes(path: Path, outcomes: list[PolicyOutcome]) -> None:
    _write_jsonl(path, outcomes)


def load_measurements(path: Path) -> list[MeasurementRecord]:
    return _read_jsonl(path, MeasurementRecord)  # type: ignore[return-value]


def load_selections(path: Path) -> list[PolicySelection]:
    return _read_jsonl(path, PolicySelection)  # type: ignore[return-value]
