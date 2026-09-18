#!/usr/bin/env python3
"""Bounded process-lifecycle witness; not a simulator performance test."""
from __future__ import annotations

import argparse
import json
import subprocess
from unittest.mock import patch

import lifecycle
import simulate


def target_stage(argv: list[str], target: str) -> bool:
    return f"/opt/openasip/bin/{target}" in argv and (
        target != "ttasim" or simulate.SIM_SCRIPT in argv
    )


def observe(container_id: str, target: str) -> bool:
    # Docker top requires a PID column even when only command identity matters.
    probe = subprocess.run(
        [simulate.DOCKER, "top", container_id, "-eo", "pid,args"],
        capture_output=True, text=True, timeout=5,
    )
    if probe.returncode:
        # Only the known pre-start race is retryable; never hide ps/API errors.
        if "is not running" in probe.stderr or "No such container" in probe.stderr:
            return False
        raise RuntimeError("Docker process observation failed")
    return any(
        len(fields := line.split(None, 1)) == 2 and fields[0].isdigit()
        and f"/opt/openasip/bin/{target}" in fields[1]
        for line in probe.stdout.splitlines()
    )


def check(target: str) -> dict[str, object]:
    if target not in {"oacc", "ttasim"}:
        raise ValueError("unsupported cancellation target")
    original_run, original_container = simulate.run, simulate.run_container
    active = {"target_stage": False, "id": None, "observed": False}

    def traced_run(argv, **kwargs):
        if argv[:3] == [simulate.DOCKER, "start", "--attach"]:
            active["id"] = argv[3]
        return original_run(argv, **kwargs)

    def traced_container(argv, **kwargs):
        active["target_stage"] = target_stage(argv, target)
        active["id"] = None
        return original_container(argv, **kwargs)

    def requested():
        if active["observed"]:
            return True
        if not active["target_stage"] or active["id"] is None:
            return False
        active["observed"] = observe(active["id"], target)
        return active["observed"]

    with patch.object(simulate, "run", traced_run), \
         patch.object(simulate, "run_container", traced_container):
        receipt = lifecycle.execute(
            lambda: simulate.simulate(cancel_requested=requested),
            cancel_requested=requested,
        )
    if not active["observed"]:
        raise RuntimeError("target process not observed; no cancellation witness")
    if receipt != lifecycle.cancelled_receipt(candidate_started=True):
        raise RuntimeError("observed target did not produce unpublished cancellation")
    remaining = subprocess.run(
        [simulate.DOCKER, "container", "ls", "-aq", "--no-trunc",
         "--filter", "id=" + active["id"]],
        capture_output=True, text=True, timeout=5, check=True,
    )
    if remaining.stdout.strip():
        raise RuntimeError("owned container still present")
    return {"target": target, "process_observed": True,
            "owned_container_absent": True, "receipt": receipt,
            "evidence_class": "host-functional-process-lifecycle"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("oacc", "ttasim"))
    print(json.dumps(check(parser.parse_args().target), sort_keys=True))
