from __future__ import annotations

import math
import random
import statistics
from typing import Iterable, Sequence

from .experiment_schema import PolicyOutcome


def percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def paired_bootstrap_median_ci(
    differences: Sequence[float], samples: int = 10_000, seed: int = 0
) -> tuple[float, float]:
    if not differences:
        raise ValueError("paired bootstrap requires differences")
    randomizer = random.Random(seed)
    medians = []
    for _ in range(samples):
        draw = [differences[randomizer.randrange(len(differences))] for _ in differences]
        medians.append(statistics.median(draw))
    return percentile(medians, 0.025), percentile(medians, 0.975)


def headroom_capture(baseline: float, selected: float, oracle: float) -> float:
    denominator = baseline - oracle
    if denominator <= 0:
        return 1.0 if selected <= baseline else 0.0
    return max(0.0, min(1.0, (baseline - selected) / denominator))


def analyze_policy_outcomes(
    outcomes: Iterable[PolicyOutcome],
    active_limit: int,
    expected_workloads: Iterable[str],
    expected_run_id: str,
    expected_measurement_budget: int,
    bootstrap_samples: int = 10_000,
) -> dict[str, object]:
    outcome_list = list(outcomes)
    required = {"cold", "bounded", "full-history"}
    allowed = required | {"fifo", "reservoir", "random"}
    expected = set(expected_workloads)
    integrity_unmet: list[str] = []
    if not expected:
        return {"gate_ready": False, "unmet": ["registered policy holdouts are required"]}
    seen: set[tuple[str, str]] = set()
    for outcome in outcome_list:
        key = (outcome.policy, outcome.workload_id)
        if key in seen:
            integrity_unmet.append(
                f"duplicate PolicyOutcome for {outcome.policy}/{outcome.workload_id}"
            )
        seen.add(key)
        if outcome.policy not in allowed:
            integrity_unmet.append(f"unknown policy in PolicyOutcome: {outcome.policy}")
        if outcome.workload_id not in expected:
            integrity_unmet.append(
                f"unknown workload in PolicyOutcome: {outcome.workload_id}"
            )
        if outcome.run_id != expected_run_id:
            integrity_unmet.append(
                f"PolicyOutcome RUN-ID mismatch for {outcome.policy}/{outcome.workload_id}"
            )
        if outcome.measurement_budget != expected_measurement_budget:
            integrity_unmet.append(
                f"PolicyOutcome budget mismatch for {outcome.policy}/{outcome.workload_id}"
            )
    present = {outcome.policy for outcome in outcome_list if outcome.policy in allowed}
    expected_pairs = {
        (policy, workload) for policy in (required | present) for workload in expected
    }
    missing = sorted(expected_pairs - seen)
    if missing:
        integrity_unmet.append(
            f"PolicyOutcome coverage is incomplete: {len(missing)} pairs missing"
        )
    extra = sorted(seen - expected_pairs)
    if extra:
        integrity_unmet.append(f"PolicyOutcome coverage has {len(extra)} unexpected pairs")
    if integrity_unmet:
        return {"gate_ready": False, "unmet": integrity_unmet}

    by_policy: dict[str, dict[str, PolicyOutcome]] = {}
    for outcome in outcome_list:
        by_policy.setdefault(outcome.policy, {})[outcome.workload_id] = outcome
    common = set.intersection(*(set(by_policy[name]) for name in required))

    latency_improvements: list[float] = []
    energy_improvements: list[float] = []
    joint_negative = 0
    latency_quality_gap: list[float] = []
    energy_quality_gap: list[float] = []
    bounded_hcr: list[float] = []
    bounded_energy_hcr: list[float] = []
    bounded_retrieval: list[float] = []
    full_retrieval: list[float] = []
    memory_ok = True
    budgets_ok = True
    for workload_id in sorted(common):
        cold = by_policy["cold"][workload_id]
        bounded = by_policy["bounded"][workload_id]
        full = by_policy["full-history"][workload_id]
        latency_improvements.append(
            (cold.selected_latency_ns - bounded.selected_latency_ns) / cold.selected_latency_ns
        )
        energy_improvements.append(
            (cold.selected_energy_mj - bounded.selected_energy_mj) / cold.selected_energy_mj
        )
        latency_bad = bounded.selected_latency_ns > cold.selected_latency_ns * 1.02
        energy_bad = bounded.selected_energy_mj > cold.selected_energy_mj * 1.02
        joint_negative += int(latency_bad or energy_bad)
        latency_quality_gap.append(
            bounded.selected_latency_ns / full.selected_latency_ns - 1.0
        )
        energy_quality_gap.append(bounded.selected_energy_mj / full.selected_energy_mj - 1.0)
        bounded_hcr.append(
            headroom_capture(
                bounded.baseline_latency_ns,
                bounded.selected_latency_ns,
                bounded.oracle_latency_ns,
            )
        )
        bounded_energy_hcr.append(
            headroom_capture(
                bounded.baseline_energy_mj,
                bounded.selected_energy_mj,
                bounded.oracle_energy_mj,
            )
        )
        bounded_retrieval.append(float(bounded.retrieval_latency_ns))
        full_retrieval.append(float(full.retrieval_latency_ns))
        memory_ok &= bounded.active_memory_records <= active_limit
        budgets_ok &= (
            bounded.measurement_budget == cold.measurement_budget == full.measurement_budget
        )

    latency_ci = paired_bootstrap_median_ci(
        latency_improvements, samples=bootstrap_samples, seed=17
    )
    energy_ci = paired_bootstrap_median_ci(
        energy_improvements, samples=bootstrap_samples, seed=29
    )
    metrics = {
        "paired_holdouts": len(common),
        "latency_median_improvement": statistics.median(latency_improvements),
        "energy_median_improvement": statistics.median(energy_improvements),
        "latency_improvement_bootstrap_95": list(latency_ci),
        "energy_improvement_bootstrap_95": list(energy_ci),
        "joint_negative_transfer_rate": joint_negative / len(common),
        "latency_full_history_quality_gap": statistics.median(latency_quality_gap),
        "energy_full_history_quality_gap": statistics.median(energy_quality_gap),
        "latency_hcr_median": statistics.median(bounded_hcr),
        "energy_hcr_median": statistics.median(bounded_energy_hcr),
        "bounded_retrieval_p95_ns": percentile(bounded_retrieval, 0.95),
        "full_history_retrieval_p95_ns": percentile(full_retrieval, 0.95),
        "active_memory_within_limit": memory_ok,
        "equal_measurement_budget": budgets_ok,
    }
    policy_metrics: dict[str, dict[str, float | int]] = {}
    for policy_name in sorted(present):
        policy_outcomes = [by_policy[policy_name][workload_id] for workload_id in sorted(common)]
        latency_ratios = [
            outcome.selected_latency_ns / outcome.baseline_latency_ns
            for outcome in policy_outcomes
        ]
        energy_ratios = [
            outcome.selected_energy_mj / outcome.baseline_energy_mj
            for outcome in policy_outcomes
        ]
        policy_metrics[policy_name] = {
            "coverage": sum(not outcome.abstained for outcome in policy_outcomes)
            / len(policy_outcomes),
            "latency_hcr_median": statistics.median(
                headroom_capture(
                    outcome.baseline_latency_ns,
                    outcome.selected_latency_ns,
                    outcome.oracle_latency_ns,
                )
                for outcome in policy_outcomes
            ),
            "energy_hcr_median": statistics.median(
                headroom_capture(
                    outcome.baseline_energy_mj,
                    outcome.selected_energy_mj,
                    outcome.oracle_energy_mj,
                )
                for outcome in policy_outcomes
            ),
            "latency_calibration_median_absolute_error": statistics.median(
                abs(outcome.predicted_latency_ratio - observed)
                for outcome, observed in zip(policy_outcomes, latency_ratios, strict=True)
            ),
            "energy_calibration_median_absolute_error": statistics.median(
                abs(outcome.predicted_energy_ratio - observed)
                for outcome, observed in zip(policy_outcomes, energy_ratios, strict=True)
            ),
            "negative_transfer_rate": sum(
                latency > 1.02 or energy > 1.02
                for latency, energy in zip(latency_ratios, energy_ratios, strict=True)
            )
            / len(policy_outcomes),
            "retrieval_p95_ns": percentile(
                [float(outcome.retrieval_latency_ns) for outcome in policy_outcomes], 0.95
            ),
            "measurement_budget": policy_outcomes[0].measurement_budget,
            "active_memory_records_max": max(
                outcome.active_memory_records for outcome in policy_outcomes
            ),
            "cold_evidence_records_max": max(
                outcome.cold_evidence_records for outcome in policy_outcomes
            ),
        }
    metrics["policy_metrics"] = policy_metrics
    unmet = []
    if metrics["latency_median_improvement"] < 0.05:
        unmet.append("latency median improvement is below 5%")
    if metrics["energy_median_improvement"] < 0.05:
        unmet.append("energy median improvement is below 5%")
    if latency_ci[0] <= 0:
        unmet.append("latency bootstrap lower bound is not above zero")
    if energy_ci[0] <= 0:
        unmet.append("energy bootstrap lower bound is not above zero")
    if metrics["joint_negative_transfer_rate"] > 0.05:
        unmet.append("joint NTR exceeds 5%")
    if metrics["latency_full_history_quality_gap"] > 0.02:
        unmet.append("latency quality gap to full history exceeds 2%")
    if metrics["energy_full_history_quality_gap"] > 0.02:
        unmet.append("energy quality gap to full history exceeds 2%")
    if not memory_ok:
        unmet.append("bounded policy exceeded active memory limit")
    if not budgets_ok:
        unmet.append("policy measurement budgets differ")
    if metrics["bounded_retrieval_p95_ns"] >= metrics["full_history_retrieval_p95_ns"]:
        unmet.append("bounded retrieval p95 is not below full history")
    return {"gate_ready": not unmet, "unmet": unmet, "metrics": metrics}
