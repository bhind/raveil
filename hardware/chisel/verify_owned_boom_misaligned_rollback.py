#!/usr/bin/env python3
"""Verify one pinned-BOOM misaligned-load exception and ROB rollback."""

from pathlib import Path
import re
import sys


PREFIX = "RAVEIL-BOOM-MISALIGNED-ROLLBACK-V1"
EXCEPTION_ADDRESS = 0x08000101
MISALIGNED_LOAD_CAUSE = 4


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM misaligned rollback verification failed: {message}")


def parse(line: str) -> dict[str, str]:
    line = re.sub(r"=\s+", "=", line)
    fields: dict[str, str] = {}
    for item in line.split()[1:]:
        if "=" not in item:
            fail(f"malformed item: {item}")
        key, value = item.split("=", 1)
        if not key or not value or key in fields:
            fail(f"invalid or duplicate field: {item}")
        fields[key] = value
    return fields


def require_keys(fields: dict[str, str], expected: set[str]) -> None:
    if fields.keys() != expected:
        fail(
            f"schema mismatch missing={sorted(expected - fields.keys())} "
            f"extra={sorted(fields.keys() - expected)}"
        )


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: verify_owned_boom_misaligned_rollback.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if len(signature) != 6 or signature[0] != 1:
        fail(f"signature mismatch: {signature!r}")
    before_value, after_value, cause, tval, trap_count = signature[1:]
    if before_value != after_value:
        fail(f"differential readback mismatch: {signature!r}")
    if (cause, tval, trap_count) != (
        MISALIGNED_LOAD_CAUSE,
        EXCEPTION_ADDRESS,
        1,
    ):
        fail(f"trap signature mismatch: {signature!r}")

    records = [
        parse(line) for line in log.splitlines() if line.startswith(PREFIX)
    ]
    event_order = [record.get("event") for record in records]
    if event_order != ["candidate", "exception", "request", "rollback"]:
        fail(f"exact negative lifecycle mismatch: {records!r}")
    candidate, exception, request, rollback = records
    require_keys(
        candidate,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "cause", "ma_ld",
            "request_accepted", "event_source",
        },
    )
    require_keys(
        exception,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "cause", "mem_xcpt_valid",
            "promotion",
        },
    )
    require_keys(
        request,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "request_accepted",
            "after_exception",
        },
    )
    require_keys(
        rollback,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "rollback", "matching_rbk",
            "request_accepted", "request_count", "response_seen",
            "core_exception_seen", "commit_valid", "arch_valid", "promotion",
        },
    )

    if {
        "epoch": candidate["epoch"],
        "sequence": candidate["sequence"],
        "cause": candidate["cause"],
        "ma_ld": candidate["ma_ld"],
        "event_source": candidate["event_source"],
    } != {
        "epoch": "1",
        "sequence": "1",
        "cause": "4",
        "ma_ld": "1",
        "event_source": "boom-pinned",
    }:
        fail(f"candidate qualification mismatch: {candidate!r}")
    if candidate["request_accepted"] != "0":
        fail(f"candidate request qualification mismatch: {candidate!r}")
    if {
        "cause": exception["cause"],
        "mem_xcpt_valid": exception["mem_xcpt_valid"],
        "promotion": exception["promotion"],
    } != {
        "cause": "4",
        "mem_xcpt_valid": "1",
        "promotion": "blocked",
    }:
        fail(f"exception qualification mismatch: {exception!r}")
    if {
        "rollback": rollback["rollback"],
        "matching_rbk": rollback["matching_rbk"],
        "request_accepted": rollback["request_accepted"],
        "request_count": rollback["request_count"],
        "response_seen": rollback["response_seen"],
        "core_exception_seen": rollback["core_exception_seen"],
        "commit_valid": rollback["commit_valid"],
        "arch_valid": rollback["arch_valid"],
        "promotion": rollback["promotion"],
    } != {
        "rollback": "1",
        "matching_rbk": "0",
        "request_accepted": "1",
        "request_count": "1",
        "response_seen": "0",
        "core_exception_seen": "1",
        "commit_valid": "0",
        "arch_valid": "0",
        "promotion": "blocked",
    }:
        fail(f"rollback qualification mismatch: {rollback!r}")
    for field in (
        "epoch", "sequence", "pc", "address", "rob_idx", "ldq_idx",
        "br_mask", "lane",
    ):
        if len({record[field] for record in records}) != 1:
            fail(f"{field} correlation mismatch: {records!r}")
    if int(candidate["address"], 16) != EXCEPTION_ADDRESS:
        fail(f"exception address mismatch: {candidate!r}")
    if int(candidate["br_mask"], 16) != 0 or int(candidate["lane"]) != 0:
        fail(f"exact context mismatch: {candidate!r}")
    if {
        "request_accepted": request["request_accepted"],
        "after_exception": request["after_exception"],
        "request_count": rollback["request_count"],
    } != {
        "request_accepted": "1",
        "after_exception": "1",
        "request_count": "1",
    }:
        fail(f"later request qualification mismatch: {records!r}")
    print(
        "BOOM-MISALIGNED-ROLLBACK-V1 status=OK event_source=boom-pinned "
        "cpu_execution=rtl-simulation candidates=1 exceptions=1 "
        "rob_rollback_state_events=1 "
        f"sequence=1 pc=0x{int(candidate['pc'], 16):x} "
        f"address=0x{EXCEPTION_ADDRESS:08x} cause=misaligned-load "
        "request_accepted=1 request_count=1 "
        "response_seen=0 matching_rbk=0 "
        "request_boundary=after-exception-before-rollback "
        "post_exception_request=observed postrequest_exception=not-covered "
        "rob_rollback_state=observed promotion=blocked "
        "transport_token_correlation=not-carried semantic_initiator=not-proven "
        "general_rollback=not-proven store_authorization=not-run "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
