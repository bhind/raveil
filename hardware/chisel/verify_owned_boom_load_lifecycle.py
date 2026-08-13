#!/usr/bin/env python3
"""Verify one pinned-BOOM load request, response, and ROB retirement."""

from pathlib import Path
import re
import sys


PREFIX = "RAVEIL-BOOM-LOAD-LIFECYCLE-V1"
AUDIT_ADDRESS = 0x08000100


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM load lifecycle verification failed: {message}")


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
        fail("usage: verify_owned_boom_load_lifecycle.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if len(signature) != 2 or signature[0] != 1:
        fail(f"signature mismatch: {signature!r}")

    records = [parse(line) for line in log.splitlines() if line.startswith(PREFIX)]
    if [record.get("event") for record in records] != ["request", "response", "retire"]:
        fail(f"exact lifecycle mismatch: {records!r}")
    request, response, retire = records
    require_keys(
        request,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "request_accepted", "event_source",
        },
    )
    require_keys(
        response,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "response_valid", "data",
        },
    )
    require_keys(
        retire,
        {
            "event", "epoch", "sequence", "pc", "address", "rob_idx",
            "ldq_idx", "br_mask", "lane", "commit_valid", "arch_valid",
            "promotion",
        },
    )
    if {
        "epoch": request["epoch"],
        "sequence": request["sequence"],
        "request_accepted": request["request_accepted"],
        "event_source": request["event_source"],
    } != {
        "epoch": "1",
        "sequence": "1",
        "request_accepted": "1",
        "event_source": "boom-pinned",
    }:
        fail(f"request qualification mismatch: {request!r}")
    if response["response_valid"] != "1":
        fail(f"response qualification mismatch: {response!r}")
    if {
        "commit_valid": retire["commit_valid"],
        "arch_valid": retire["arch_valid"],
        "promotion": retire["promotion"],
    } != {"commit_valid": "1", "arch_valid": "1", "promotion": "eligible"}:
        fail(f"retirement qualification mismatch: {retire!r}")

    for field in (
        "epoch", "sequence", "pc", "address", "rob_idx", "ldq_idx",
        "br_mask", "lane",
    ):
        if len({record[field] for record in records}) != 1:
            fail(f"{field} correlation mismatch: {records!r}")
    if int(request["address"], 16) != AUDIT_ADDRESS:
        fail(f"audit address mismatch: {request!r}")
    if int(request["br_mask"], 16) != 0 or int(request["lane"]) != 0:
        fail(f"exact context mismatch: {request!r}")
    if (int(response["data"], 16) & 0xFFFFFFFF) != signature[1]:
        fail(f"response/signature mismatch: {response!r} {signature!r}")

    print(
        "BOOM-LOAD-LIFECYCLE-V1 status=OK event_source=boom-pinned "
        "cpu_execution=rtl-simulation requests=1 responses=1 rob_retirements=1 "
        f"sequence=1 pc=0x{int(request['pc'], 16):x} address=0x{AUDIT_ADDRESS:08x} "
        f"rob_idx={int(request['rob_idx'])} ldq_idx={int(request['ldq_idx'])} "
        "promotion=eligible transport_token_correlation=not-carried "
        "semantic_initiator=not-proven store_authorization=not-run "
        "general_boom_lifecycle=not-proven resource_match_verified=0 "
        "matched_comparison_ready=0 evidence=rtl-simulation-functional "
        "performance=not-measured"
    )


if __name__ == "__main__":
    main()
