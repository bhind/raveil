from __future__ import annotations

from dataclasses import dataclass
import math

from .backend import ToyDaphnis
from .experience import ExperienceStore
from .model import Candidate, Context, Metrics


class NearestExperiencePolicy:
    """Ranks candidates from bounded, nearby Experience records."""

    def rank(
        self,
        context: Context,
        candidates: tuple[Candidate, ...],
        store: ExperienceStore,
    ) -> list[tuple[float, Candidate, str]]:
        ranked: list[tuple[float, Candidate, str]] = []
        for candidate in candidates:
            neighbors = store.nearest(context, candidate.candidate_id)
            valid = [(distance, record) for distance, record in neighbors if record.metrics.valid]
            invalid = [(distance, record) for distance, record in neighbors if not record.metrics.valid]
            if not valid:
                risk = 0.75 if invalid and invalid[0][0] < 0.5 else 0.0
                ranked.append((candidate.cold_prior + risk, candidate, "cold-prior"))
                continue

            weights = [record.samples / (1.0 + distance) ** 2 for distance, record in valid]
            weighted_ratio = sum(
                weight * record.relative_cycles for weight, (_, record) in zip(weights, valid)
            ) / sum(weights)
            min_distance = valid[0][0]
            samples = sum(record.samples for _, record in valid)
            uncertainty = 0.08 / math.sqrt(samples)
            # A failure boundary must matter locally without poisoning a different
            # memory regime. Its influence therefore decays faster than success evidence.
            invalid_risk = sum(
                record.samples * math.exp(-4.0 * distance) for distance, record in invalid
            ) / max(1.0, sum(weights))
            score = weighted_ratio + 0.03 * min_distance + uncertainty + 0.25 * invalid_risk
            ranked.append((score, candidate, f"experience n={samples} d={min_distance:.2f}"))
        ranked.sort(key=lambda item: (item[0], item[1].candidate_id))
        return ranked


@dataclass(frozen=True)
class Trial:
    candidate: Candidate
    metrics: Metrics
    reason: str


@dataclass(frozen=True)
class TuningResult:
    context: Context
    budget: int
    trials: tuple[Trial, ...]
    best: Trial
    oracle: Trial
    baseline_cycles: int
    headroom_capture: float


class Tuner:
    def __init__(
        self,
        backend: ToyDaphnis,
        store: ExperienceStore,
        policy: NearestExperiencePolicy,
        candidates: tuple[Candidate, ...],
    ) -> None:
        if not candidates or candidates[0].candidate_id != "baseline":
            raise ValueError("the first candidate must be the trusted baseline")
        self.backend = backend
        self.store = store
        self.policy = policy
        self.candidates = candidates

    def tune(self, context: Context, budget: int) -> TuningResult:
        if budget < 1:
            raise ValueError("measurement budget must be positive")

        baseline_candidate = self.candidates[0]
        baseline_metrics = self.backend.measure(context, baseline_candidate)
        if not baseline_metrics.valid:
            raise RuntimeError(f"trusted baseline is invalid: {baseline_metrics.reason}")
        trials = [Trial(baseline_candidate, baseline_metrics, "trusted-baseline")]
        self.store.append(context, baseline_candidate, baseline_metrics, baseline_metrics.cycles)
        tried = {baseline_candidate.candidate_id}

        while len(trials) < min(budget, len(self.candidates)):
            available = tuple(c for c in self.candidates if c.candidate_id not in tried)
            score, candidate, reason = self.policy.rank(context, available, self.store)[0]
            metrics = self.backend.measure(context, candidate)
            self.store.append(context, candidate, metrics, baseline_metrics.cycles)
            trials.append(Trial(candidate, metrics, f"{reason} score={score:.3f}"))
            tried.add(candidate.candidate_id)

        valid_trials = [trial for trial in trials if trial.metrics.valid]
        best = min(valid_trials, key=lambda trial: trial.metrics.cycles)
        oracle_candidates = [
            Trial(candidate, self.backend.measure(context, candidate), "oracle-only")
            for candidate in self.candidates
        ]
        oracle = min(
            (trial for trial in oracle_candidates if trial.metrics.valid),
            key=lambda trial: trial.metrics.cycles,
        )
        denominator = baseline_metrics.cycles - oracle.metrics.cycles
        if denominator <= 0:
            capture = 1.0
        else:
            capture = (baseline_metrics.cycles - best.metrics.cycles) / denominator
            capture = max(0.0, min(1.0, capture))
        return TuningResult(
            context=context,
            budget=budget,
            trials=tuple(trials),
            best=best,
            oracle=oracle,
            baseline_cycles=baseline_metrics.cycles,
            headroom_capture=capture,
        )
