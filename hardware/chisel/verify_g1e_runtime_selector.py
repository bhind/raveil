#!/usr/bin/env python3
"""Verify that one G1e RTL image selects both candidates at runtime."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SELECT = re.compile(
    r"RAVEIL-G1E-SELECT-V1 mode=(graph|rocket) locked=1 "
    r"graph_origin=([01]) dcache_origin=([01]) performance=not-measured"
)
FIXTURE = "RAVEIL-FIXTURE-STAGING-V1"


def _verify_mode(text: str, expected: str) -> None:
    if any(marker in text for marker in ("Assertion failed", "%Error", "*** FAILED ***")):
        raise ValueError(f"G1e {expected} log contains a simulator failure")
    matches = SELECT.findall(text)
    expected_bits = (expected, "1", "0") if expected == "graph" else (
        expected, "0", "1")
    if matches != [expected_bits]:
        raise ValueError(f"G1e {expected} selection is missing, duplicated, or drifted")
    select_position = text.find("RAVEIL-G1E-SELECT-V1")
    fixture_position = text.find(FIXTURE)
    pass_position = text.find("*** PASSED ***")
    if not (0 <= select_position < fixture_position < pass_position):
        raise ValueError(f"G1e {expected} selection lifecycle is out of order")


def verify(graph_text: str, rocket_text: str) -> None:
    _verify_mode(graph_text, "graph")
    _verify_mode(rocket_text, "rocket")
    if "RAVEIL-G1D-COMPLETE-V1" in graph_text:
        raise ValueError("G1e Graph run emitted Rocket completion")
    if "RAVEIL-G1C-COMPLETE-V1" in rocket_text:
        raise ValueError("G1e Rocket run emitted Graph completion")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-log", type=Path, required=True)
    parser.add_argument("--rocket-log", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verify(
            args.graph_log.read_text(encoding="utf-8"),
            args.rocket_log.read_text(encoding="utf-8"),
        )
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        "G1E-RUNTIME-SELECTOR-V1 status=OK rtl_images=1 modes=graph,rocket "
        "selection=runtime-first-owned-origin inactive_origin_requests=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
