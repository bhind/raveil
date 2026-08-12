#!/usr/bin/env python3
"""Fail-closed verifier for the synthetic Rocket lifecycle observer marker."""

from pathlib import Path
import sys


PREFIX = "ROCKET-LIFECYCLE-OBSERVER-V1"
EXPECTED = {
    "status": "OK",
    "allocated": "21",
    "committed_load": "3",
    "committed_store": "1",
    "noncommitted": "17",
    "core_attempts": "8",
    "core_replays": "1",
    "dcache_retries": "1",
    "a_accepted": "7",
    "d_completed": "7",
    "retired": "5",
    "store_authorized": "1",
    "unknown": "2",
    "violations": "8",
    "load_positive": "covered",
    "store_positive": "covered",
    "pre_a_kill": "covered",
    "post_a_exception": "covered",
    "reset_outstanding": "covered",
    "stale_epoch": "covered",
    "stripped_metadata": "covered",
    "duplicate_token": "covered",
    "duplicate_outcome": "covered",
    "invalid_completion": "covered",
    "untagged_event": "covered",
    "d_error": "covered",
    "sequence_exhaustion": "covered",
    "event_source": "synthetic",
    "cpu_execution": "not-run",
    "semantic_initiator": "not-proven",
    "resource_match_verified": "0",
    "matched_comparison_ready": "0",
    "evidence": "rtl-simulation-functional",
    "performance": "not-measured",
}


def fail(message: str) -> "None":
    raise SystemExit(f"Rocket lifecycle observer verification failed: {message}")


def parse_marker(text: str) -> dict[str, str]:
    markers = [line for line in text.splitlines() if line.startswith(f"{PREFIX} ")]
    if len(markers) != 1:
        fail(f"expected exactly one {PREFIX} marker, found {len(markers)}")

    fields: dict[str, str] = {}
    for item in markers[0].split()[1:]:
        if "=" not in item:
            fail(f"malformed marker item: {item}")
        key, value = item.split("=", 1)
        if not key or not value:
            fail(f"empty marker key or value: {item}")
        if key in fields:
            fail(f"duplicate marker field: {key}")
        fields[key] = value
    return fields


def verify(text: str) -> None:
    fields = parse_marker(text)
    if fields.keys() != EXPECTED.keys():
        missing = sorted(EXPECTED.keys() - fields.keys())
        extra = sorted(fields.keys() - EXPECTED.keys())
        fail(f"marker schema mismatch missing={missing} extra={extra}")
    for key, expected in EXPECTED.items():
        if fields[key] != expected:
            fail(f"{key} expected {expected}, got {fields[key]}")
    if int(fields["allocated"]) != (
        int(fields["committed_load"])
        + int(fields["committed_store"])
        + int(fields["noncommitted"])
    ):
        fail("terminal outcome conservation mismatch")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify_rocket_lifecycle_observer.py LOG")
    log_path = Path(sys.argv[1])
    if not log_path.is_file():
        fail(f"log is missing: {log_path}")
    verify(log_path.read_text(encoding="utf-8"))
    print(
        "ROCKET-LIFECYCLE-OBSERVER-AUDIT-V1 status=OK schema=exact "
        "conservation=verified claims=bounded-functional-only"
    )


if __name__ == "__main__":
    main()
