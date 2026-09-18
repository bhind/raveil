#!/usr/bin/env python3
"""Raveil-owned publication, rejection, cancellation, and fallback boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any, Callable

import oracle

EXPECTED = {
    "neighborhood": oracle.neighborhood(),
    "elementwise": oracle.elementwise(),
    "reduction": oracle.reduction(),
}


class ExternalProcessCancelled(RuntimeError):
    """An owned external candidate was stopped and its cleanup verified."""


class ExternalProcessCleanupError(RuntimeError):
    """An owned external candidate may remain alive; never publish or fall back."""


def receipt_sha256(receipt: dict[str, Any]) -> str:
    encoded = json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def cancelled_receipt(*, candidate_started: bool = False) -> dict[str, Any]:
    return {
        "task": "T-0191", "status": "cancelled", "backend": None,
        "candidate_started": candidate_started, "published": False,
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
    except ExternalProcessCancelled:
        return cancelled_receipt(candidate_started=True)
    except (ExternalProcessCleanupError, subprocess.TimeoutExpired):
        return {
            "task": "T-0191", "status": "failed", "backend": None,
            "candidate_failure": "external-process-cleanup-uncertain",
            "published": False,
        }
    except Exception:
        return {
            "task": "T-0191", "status": "failed", "backend": None,
            "candidate_failure": reason, "cpu_fallback": "failed",
            "published": False,
        }
    programs = cpu.get("programs")
    if (
        cpu.get("backend") != "native-cpu"
        or not isinstance(programs, dict)
        or set(programs) != set(EXPECTED)
    ):
        raise RuntimeError("CPU fallback envelope is invalid")
    for name, expected in EXPECTED.items():
        if programs.get(name, {}).get("observed_u32") != expected:
            raise RuntimeError("CPU fallback oracle mismatch")
    try:
        private_identity = receipt_sha256(cpu)
    except (TypeError, ValueError):
        return {
            "task": "T-0191", "status": "failed", "backend": None,
            "candidate_failure": reason, "cpu_fallback": "invalid-receipt",
            "published": False,
        }
    return {
        "task": "T-0191", "status": "fallback", "backend": "native-cpu",
        "candidate_failure": reason,
        "results": {name: programs[name]["observed_u32"] for name in EXPECTED},
        "private_cpu_receipt_sha256": private_identity,
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
    try:
        private_identity = receipt_sha256(candidate)
    except (TypeError, ValueError):
        return fallback_receipt("candidate-receipt-not-canonical")
    return {
        "task": "T-0191", "status": "accepted", "backend": "openasip-ttasim",
        "results": {name: programs[name]["result_u32"] for name in EXPECTED},
        "private_candidate_receipt_sha256": private_identity,
        "publication_authority": "raveil", "published": True,
    }


def execute(
    candidate: Callable[[], dict[str, Any]], *, cancelled: bool = False,
    cpu_fallback: Callable[[], dict[str, Any]] | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    if cancelled or (cancel_requested is not None and cancel_requested()):
        return cancelled_receipt()
    try:
        private_receipt = candidate()
    except ExternalProcessCancelled:
        return cancelled_receipt(candidate_started=True)
    except (ExternalProcessCleanupError, subprocess.TimeoutExpired):
        return {
            "task": "T-0191", "status": "failed", "backend": None,
            "candidate_failure": "external-process-cleanup-uncertain",
            "published": False,
        }
    except Exception:
        if cancel_requested is not None and cancel_requested():
            return cancelled_receipt(candidate_started=True)
        if cpu_fallback is None:
            return fallback_receipt("candidate-execution-failed")
        return actual_cpu_fallback("candidate-execution-failed", cpu_fallback)
    if cancel_requested is not None and cancel_requested():
        return cancelled_receipt(candidate_started=True)
    result = admit(private_receipt)
    if result.get("status") == "fallback" and cpu_fallback is not None:
        return actual_cpu_fallback(str(result["candidate_failure"]), cpu_fallback)
    return result
