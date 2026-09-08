#!/usr/bin/env python3
"""Raveil-owned publication, rejection, cancellation, and fallback boundary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import oracle

EXPECTED = {
    "neighborhood": oracle.neighborhood(),
    "elementwise": oracle.elementwise(),
    "reduction": oracle.reduction(),
}


def cancelled_receipt() -> dict[str, Any]:
    return {
        "task": "T-0191", "status": "cancelled", "backend": None,
        "candidate_started": False, "published": False,
    }


def fallback_receipt(reason: str) -> dict[str, Any]:
    return {
        "task": "T-0191", "status": "fallback", "backend": "cpu-oracle",
        "candidate_failure": reason, "results": EXPECTED, "published": True,
        "publication_authority": "raveil",
    }


def actual_cpu_fallback(
    reason: str, cpu_fallback: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    try:
        cpu = cpu_fallback()
    except Exception:
        return {
            "task": "T-0191", "status": "failed", "backend": None,
            "candidate_failure": reason, "cpu_fallback": "failed",
            "published": False,
        }
    programs = cpu.get("programs")
    if cpu.get("backend") != "native-cpu" or not isinstance(programs, dict):
        raise RuntimeError("CPU fallback envelope is invalid")
    for name, expected in EXPECTED.items():
        if programs.get(name, {}).get("observed_u32") != expected:
            raise RuntimeError("CPU fallback oracle mismatch")
    return {
        "task": "T-0191", "status": "fallback", "backend": "native-cpu",
        "candidate_failure": reason, "cpu_receipt": cpu,
        "publication_authority": "raveil", "published": True,
    }


def admit(candidate: dict[str, Any], *, cancelled: bool = False) -> dict[str, Any]:
    if cancelled:
        return cancelled_receipt()
    if candidate.get("published") is not False:
        return fallback_receipt("candidate-crossed-publication-boundary")
    programs = candidate.get("programs")
    if not isinstance(programs, dict) or set(programs) != set(EXPECTED):
        return fallback_receipt("candidate-program-set-rejected")
    for name, expected in EXPECTED.items():
        record = programs.get(name)
        if not isinstance(record, dict) or record.get("result_u32") != expected:
            return fallback_receipt(f"candidate-oracle-rejected:{name}")
    accepted = deepcopy(candidate)
    accepted["status"] = "accepted"
    accepted["backend"] = "openasip-ttasim"
    accepted["publication_authority"] = "raveil"
    accepted["published"] = True
    return accepted


def execute(
    candidate: Callable[[], dict[str, Any]], *, cancelled: bool = False,
    cpu_fallback: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if cancelled:
        return cancelled_receipt()
    try:
        private_receipt = candidate()
    except Exception:
        if cpu_fallback is None:
            return fallback_receipt("candidate-execution-failed")
        return actual_cpu_fallback("candidate-execution-failed", cpu_fallback)
    result = admit(private_receipt)
    if result.get("status") == "fallback" and cpu_fallback is not None:
        return actual_cpu_fallback(str(result["candidate_failure"]), cpu_fallback)
    return result
