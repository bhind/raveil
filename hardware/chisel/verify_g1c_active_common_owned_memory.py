#!/usr/bin/env python3
"""Verify the bounded G1c RTL smoke marker and private validation stream."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from raveil.riscv_stencil_signature import input_words
from raveil.static_region import static_stencil_oracle

LINE = re.compile(
    r"RAVEIL-G1C-VALIDATION-V1 address=\s*(\d+) index=\s*(\d+) "
    r"data=0x([0-9a-fA-F]+) error=\s*(\d+)"
)
FIXTURE = re.compile(
    r"RAVEIL-FIXTURE-STAGING-V1 invocation=\s*1 seed=\s*1 "
    r"accepted=324 completed=324 writes=324 first_word=0 last_word=323 "
    r"pending=0 candidate_accepted_before_release=\s*0 release_count=1"
)
EXECUTION = re.compile(
    r"RAVEIL-G1C-EXECUTION-COMPLETE-V1 graph_reads=\s*1280 "
    r"graph_writes=\s*256 dcache_origin_accepted=\s*0 "
    r"dcache_origin_completed=\s*0 pending=0 performance=not-measured"
)
COMPLETE = re.compile(
    r"RAVEIL-G1C-COMPLETE-V1 fixture_writes=324 "
    r"graph_execution_reads=\s*1280 graph_execution_writes=\s*256 "
    r"validation_reads=\s*256 graph_origin_accepted=\s*1792 "
    r"graph_origin_completed=\s*1792 dcache_origin_accepted=\s*0 "
    r"dcache_origin_completed=\s*0 publication=private pending=0 "
    r"performance=not-measured"
)

def main() -> int:
    text = sys.stdin.read()
    if "Assertion failed" in text or "%Error" in text or "*** FAILED ***" in text:
        raise SystemExit("G1c RTL smoke contains a simulator failure")
    if len(FIXTURE.findall(text)) != 1:
        raise SystemExit("G1c fixture staging marker is missing or duplicated")
    if len(EXECUTION.findall(text)) != 1:
        raise SystemExit("G1c execution accounting marker is missing or duplicated")
    if len(COMPLETE.findall(text)) != 1 or "*** PASSED ***" not in text:
        raise SystemExit("G1c private completion or program pass marker is missing")
    rows = [(int(a), int(i), int(d, 16), int(e)) for a, i, d, e in LINE.findall(text)]
    if len(rows) != 256 or [i for _, i, _, _ in rows] != list(range(256)):
        raise SystemExit("G1c validation stream is not exactly 256 ordered reads")
    if any(e for _, _, _, e in rows) or [a for a, _, _, _ in rows] != list(range(324, 580)):
        raise SystemExit("G1c validation returned a TileLink error")
    expected = static_stencil_oracle(input_words(1))
    actual = [d for _, _, d, _ in rows]
    if actual != expected:
        raise SystemExit("G1c validation output differs from independent oracle")
    print("G1C-ACTIVE-COMMON-OWNED-MEMORY-V1 status=OK fixture_words=324 graph_reads=1280 graph_writes=256 validation_reads=256 dcache_origin_requests=0 publication=private performance=not-measured")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
