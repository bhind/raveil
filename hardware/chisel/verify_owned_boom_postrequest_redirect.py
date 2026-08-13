#!/usr/bin/env python3
"""Verify one pinned-BOOM request/response followed by branch redirect."""

from pathlib import Path
import re
import sys


PREFIX = "RAVEIL-BOOM-POSTREQUEST-REDIRECT-V1"
SCRATCH_ADDRESS = 0x80010000
EXPECTED_PC = 0x80000048


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM post-request redirect verification failed: {message}")


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
        fail("usage: verify_owned_boom_postrequest_redirect.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if len(signature) != 3 or signature[0] != 1:
        fail(f"signature mismatch: {signature!r}")
    if signature[1] != signature[2]:
        fail(f"differential readback mismatch: {signature!r}")

    records = [parse(line) for line in log.splitlines() if line.startswith(PREFIX)]
    if [record.get("event") for record in records] != [
        "request", "response", "redirect"
    ]:
        fail(f"exact post-request lifecycle mismatch: {records!r}")
    request, response, redirect = records
    require_keys(
        request,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "request_accepted",
            "branch_context", "event_source",
        },
    )
    require_keys(
        response,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "response_valid",
            "before_redirect",
        },
    )
    require_keys(
        redirect,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "request_seen", "response_seen",
            "branch_killed", "commit_valid", "arch_valid", "promotion",
        },
    )
    if {
        "epoch": request["epoch"],
        "sequence": request["sequence"],
        "request_accepted": request["request_accepted"],
        "branch_context": request["branch_context"],
        "event_source": request["event_source"],
    } != {
        "epoch": "1",
        "sequence": "1",
        "request_accepted": "1",
        "branch_context": "1",
        "event_source": "boom-pinned",
    }:
        fail(f"request qualification mismatch: {request!r}")
    if {
        "response_valid": response["response_valid"],
        "before_redirect": response["before_redirect"],
    } != {"response_valid": "1", "before_redirect": "1"}:
        fail(f"response qualification mismatch: {response!r}")
    if {
        "request_seen": redirect["request_seen"],
        "response_seen": redirect["response_seen"],
        "branch_killed": redirect["branch_killed"],
        "commit_valid": redirect["commit_valid"],
        "arch_valid": redirect["arch_valid"],
        "promotion": redirect["promotion"],
    } != {
        "request_seen": "1",
        "response_seen": "1",
        "branch_killed": "1",
        "commit_valid": "0",
        "arch_valid": "0",
        "promotion": "blocked",
    }:
        fail(f"redirect qualification mismatch: {redirect!r}")
    for field in (
        "epoch", "sequence", "pc", "address", "rob_idx", "ldq_idx",
        "br_mask", "lane",
    ):
        if len({record[field] for record in records}) != 1:
            fail(f"{field} correlation mismatch: {records!r}")
    if int(request["address"], 16) != SCRATCH_ADDRESS:
        fail(f"cacheable scratch address mismatch: {request!r}")
    if int(request["pc"], 16) != EXPECTED_PC:
        fail(f"wrong-path PC mismatch: {request!r}")
    if int(request["br_mask"], 16) == 0:
        fail(f"missing speculative branch context: {request!r}")
    print(
        "BOOM-POSTREQUEST-REDIRECT-V1 status=OK event_source=boom-pinned "
        "cpu_execution=rtl-simulation requests=1 responses=1 redirects=1 "
        f"sequence=1 pc=0x{EXPECTED_PC:x} "
        f"address=0x{SCRATCH_ADDRESS:08x} memory_class=cacheable-dram "
        "request_before_redirect=observed response_before_redirect=observed "
        "branch_kill=observed promotion=blocked "
        "postrequest_redirect=covered owned_manager=not-exercised "
        "post_tl_a_redirect=not-proven "
        "transport_cancellation=not-proven side_effect_absence=not-proven "
        "transport_token_correlation=not-carried semantic_initiator=not-proven "
        "general_rollback=not-proven resource_match_verified=0 "
        "matched_comparison_ready=0 evidence=rtl-simulation-functional "
        "performance=not-measured"
    )


if __name__ == "__main__":
    main()
