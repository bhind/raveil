#!/usr/bin/env python3
"""Verify the bounded G1d Rocket-selected fallback smoke."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from raveil.riscv_stencil_signature import (  # noqa: E402
    input_words,
)
from raveil.static_region import static_stencil_oracle  # noqa: E402


FIXTURE = re.compile(
    r"RAVEIL-FIXTURE-STAGING-V1 invocation=\s*1 seed=\s*1 "
    r"accepted=324 completed=324 writes=324 first_word=0 last_word=323 "
    r"pending=0 candidate_accepted_before_release=\s*0 release_count=1"
)
EXECUTION = re.compile(
    r"RAVEIL-G1D-EXECUTION-COMPLETE-V1 dcache_reads=\s*800 "
    r"dcache_writes=\s*256 dcache_origin_accepted=\s*1056 "
    r"dcache_origin_completed=\s*1056 graph_origin_accepted=\s*0 "
    r"graph_origin_completed=\s*0 pending=0 performance=not-measured"
)
VALIDATION = re.compile(
    r"RAVEIL-G1D-VALIDATION-V1 address=\s*(\d+) index=\s*(\d+) "
    r"data=0x([0-9a-fA-F]+) error=\s*(\d+)"
)
COMPLETE = re.compile(
    r"RAVEIL-G1D-COMPLETE-V1 fixture_writes=324 "
    r"dcache_execution_reads=\s*800 dcache_execution_writes=\s*256 "
    r"validation_reads=\s*256 dcache_origin_accepted=\s*1312 "
    r"dcache_origin_completed=\s*1312 graph_origin_accepted=\s*0 "
    r"graph_origin_completed=\s*0 publication=private pending=0 "
    r"performance=not-measured"
)


def _exactly_one(pattern: re.Pattern[str], text: str, name: str) -> re.Match[str]:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"G1d {name} marker is missing or duplicated")
    return matches[0]


def verify(log_text: str) -> None:
    if any(marker in log_text for marker in ("Assertion failed", "%Error", "*** FAILED ***")):
        raise ValueError("G1d RTL smoke contains a simulator failure")

    fixture = _exactly_one(FIXTURE, log_text, "fixture staging")
    execution = _exactly_one(EXECUTION, log_text, "execution accounting")
    complete = _exactly_one(COMPLETE, log_text, "private completion")
    pass_position = log_text.find("*** PASSED ***")
    if pass_position < 0:
        raise ValueError("G1d program pass marker is missing")

    rows = [
        (int(address), int(index), int(data, 16), int(error))
        for address, index, data, error in VALIDATION.findall(log_text)
    ]
    if len(rows) != 256 or [index for _, index, _, _ in rows] != list(range(256)):
        raise ValueError("G1d validation stream is not exactly 256 ordered reads")
    if [address for address, _, _, _ in rows] != list(range(324, 580)):
        raise ValueError("G1d validation addresses are not the private output window")
    if any(error for _, _, _, error in rows):
        raise ValueError("G1d validation returned a TileLink error")

    expected = static_stencil_oracle(input_words(1))
    actual = [data for _, _, data, _ in rows]
    if actual != expected:
        raise ValueError("G1d validation output differs from independent oracle")
    first_validation = next(VALIDATION.finditer(log_text), None)
    if first_validation is None or not (
        fixture.start() < execution.start() < first_validation.start()
        < complete.start() < pass_position
    ):
        raise ValueError("G1d lifecycle markers are out of order")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        log_text = args.log.read_text(encoding="utf-8")
        verify(log_text)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        "G1D-ROCKET-FALLBACK-OWNED-MEMORY-V1 status=OK fixture_words=324 "
        "dcache_reads=800 dcache_writes=256 validation_reads=256 "
        "graph_origin_requests=0 publication=private performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
