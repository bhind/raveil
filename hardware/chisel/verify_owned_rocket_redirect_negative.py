#!/usr/bin/env python3
"""Verify one bounded pinned-Rocket post-request redirect outcome."""

from pathlib import Path
import re
import sys


PREFIX = "RAVEIL-ROCKET-REQUEST-RETIRE-V1"
ADDRESS = 0x08000100
MAGIC = 0x4B1D2E3F


def fail(message: str) -> "None":
    raise SystemExit(f"Rocket redirect-negative verification failed: {message}")


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


def verify_load(records: list[dict[str, str]], sequence: str, label: str) -> tuple[int, int]:
    allocate, request = records[:2]
    completions = records[2:]
    if {record.get("event") for record in completions} != {"retire", "response"}:
        fail(f"{label} completion mismatch: {records!r}")
    retire = next(record for record in completions if record["event"] == "retire")
    response = next(record for record in completions if record["event"] == "response")
    require_keys(allocate, {"event", "epoch", "sequence", "pc", "address", "store", "event_source"})
    require_keys(request, {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"})
    require_keys(retire, {"event", "epoch", "sequence", "pc", "store", "wb_valid", "store_wb_predicate"})
    require_keys(response, {"event", "epoch", "sequence", "tag", "store", "response_valid", "response_has_data"})
    for record in records:
        if record["epoch"] != "1" or record["sequence"] != sequence or record["store"] != "0":
            fail(f"{label} token mismatch: {record!r}")
    if allocate["event_source"] != "rocket-pinned":
        fail(f"{label} source is not pinned Rocket")
    if request["attempt"] != "1":
        fail(f"{label} was replayed or duplicated")
    if int(allocate["address"], 16) != ADDRESS or int(request["address"], 16) != ADDRESS:
        fail(f"{label} address mismatch")
    pc = int(allocate["pc"], 16)
    if int(request["pc"], 16) != pc or int(retire["pc"], 16) != pc:
        fail(f"{label} PC correlation mismatch")
    if retire["wb_valid"] != "1" or retire["store_wb_predicate"] != "0":
        fail(f"{label} retirement qualification mismatch")
    if response["response_valid"] != "1" or response["response_has_data"] != "1":
        fail(f"{label} response qualification mismatch")
    tag = int(request["tag"], 16)
    if int(response["tag"], 16) != tag:
        fail(f"{label} request/response tag mismatch")
    return pc, tag


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: verify_owned_rocket_redirect_negative.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if len(signature) != 3 or signature[0] != 1:
        fail(f"signature mismatch: {signature!r}")
    before_value, after_value = signature[1:]
    if before_value == MAGIC or before_value != after_value:
        fail(f"differential readback mismatch: {signature!r}")

    records = [parse(line) for line in log.splitlines() if line.startswith(PREFIX)]
    if len(records) != 11:
        fail(f"expected eleven lifecycle records, found {len(records)}")
    if [record.get("event") for record in records[:2]] != ["allocate", "request"]:
        fail(f"initial-load prefix mismatch: {records!r}")
    if [record.get("event") for record in records[4:9]] != [
        "allocate", "request", "kill", "allocate", "request",
    ]:
        fail(f"redirect lifecycle order mismatch: {records!r}")

    before_pc, _ = verify_load(records[:4], "1", "before load")
    killed_allocate, killed_request, killed = records[4:7]
    after_pc, _ = verify_load(records[7:], "3", "after load")

    require_keys(killed_allocate, {"event", "epoch", "sequence", "pc", "address", "store", "event_source"})
    require_keys(killed_request, {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"})
    require_keys(
        killed,
        {
            "event", "epoch", "sequence", "branch_pc", "pc", "store", "reason",
            "request_accepted", "branch", "taken", "direction_misprediction", "promotion",
        },
    )
    for record in (killed_allocate, killed_request, killed):
        if record["epoch"] != "1" or record["sequence"] != "2" or record["store"] != "1":
            fail(f"killed token mismatch: {record!r}")
    if killed_allocate["event_source"] != "rocket-pinned":
        fail("killed-store source is not pinned Rocket")
    if killed_request["attempt"] != "1":
        fail("wrong-path request was replayed or duplicated")
    if int(killed_allocate["address"], 16) != ADDRESS or int(killed_request["address"], 16) != ADDRESS:
        fail("wrong-path address mismatch")
    killed_pc = int(killed_allocate["pc"], 16)
    if int(killed_request["pc"], 16) != killed_pc or int(killed["pc"], 16) != killed_pc:
        fail("wrong-path PC correlation mismatch")
    if int(killed["branch_pc"], 16) + 4 != killed_pc:
        fail("redirecting branch is not immediately before the killed store")
    for key, value in {
        "reason": "mem-redirect",
        "request_accepted": "1",
        "branch": "1",
        "taken": "1",
        "direction_misprediction": "1",
        "promotion": "blocked",
    }.items():
        if killed[key] != value:
            fail(f"redirect qualification mismatch: {killed!r}")
    if len({before_pc, killed_pc, after_pc}) != 3:
        fail("before, killed, and after operation PCs are not distinct")

    print(
        "ROCKET-POSTREQUEST-REDIRECT-NEGATIVE-V1 status=OK event_source=rocket-pinned "
        "cpu_execution=rtl-simulation differential_loads=2 killed_tokens=1 "
        "wrong_path_core_requests=1 wrong_path_retirements=0 before_after_equal=1 "
        f"observed_value=0x{before_value:08x} memory_effect=not-observed-by-differential-loads "
        "postrequest_redirect=covered pre_request_kill=not-run "
        "dcache_s1_kill_correlation=not-run a_d_correlation=not-run "
        "semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
