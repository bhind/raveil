#!/usr/bin/env python3
"""Execute the real candidate behind Raveil's lifecycle authority boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import lifecycle
import host_check
import simulate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--cancel-before-start", action="store_true")
    parser.add_argument("--force-candidate-failure-for-test", action="store_true")
    args = parser.parse_args()
    candidate = (
        (lambda: (_ for _ in ()).throw(RuntimeError("forced candidate failure")))
        if args.force_candidate_failure_for_test
        else (lambda: simulate.simulate(evidence_dir=args.evidence_dir))
    )
    result = lifecycle.execute(
        candidate,
        cancelled=args.cancel_before_start,
        cpu_fallback=host_check.run,
    )
    if args.evidence_dir is not None and result.get("status") == "accepted":
        (args.evidence_dir / "authorized-receipt.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
