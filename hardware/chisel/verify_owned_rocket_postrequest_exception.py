#!/usr/bin/env python3
"""Verify one accepted pinned-Rocket request ending in a WB misalignment exception."""

from pathlib import Path
import re
import sys


LIFECYCLE_PREFIX = "RAVEIL-ROCKET-REQUEST-RETIRE-V1"
EXCEPTION_PREFIX = "RAVEIL-ROCKET-POSTREQUEST-EXCEPTION-V1"
ALIGNED_ADDRESS = 0x08000100
EXCEPTION_ADDRESS = 0x08000101
MISALIGNED_LOAD_CAUSE = 4


def fail(message: str) -> "None":
    raise SystemExit(f"Rocket post-request exception verification failed: {message}")


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


def verify_load(records: list[dict[str, str]], sequence: str) -> int:
    if len(records) != 5 or [record.get("event") for record in records] != [
        "allocate", "request", "request", "retire", "response"
    ]:
        fail(f"load lifecycle mismatch: {records!r}")
    allocate, request, retry, retire, response = records
    require_keys(allocate, {"event", "epoch", "sequence", "pc", "address", "store", "event_source"})
    require_keys(request, {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"})
    require_keys(retry, {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"})
    require_keys(retire, {"event", "epoch", "sequence", "pc", "store", "wb_valid", "store_wb_predicate"})
    require_keys(response, {"event", "epoch", "sequence", "tag", "store", "response_valid", "response_has_data"})
    for record in records:
        if record["epoch"] != "1" or record["sequence"] != sequence or record["store"] != "0":
            fail(f"load token mismatch: {record!r}")
    if allocate["event_source"] != "rocket-pinned" or (
        request["attempt"], retry["attempt"]
    ) != ("1", "2"):
        fail(f"load source or attempt mismatch: {records!r}")
    if any(int(record["address"], 16) != ALIGNED_ADDRESS for record in (allocate, request, retry)):
        fail(f"load address mismatch: {records!r}")
    pc = int(allocate["pc"], 16)
    if any(int(record["pc"], 16) != pc for record in (request, retry, retire)):
        fail(f"load PC mismatch: {records!r}")
    if len({int(record["tag"], 16) for record in (request, retry, response)}) != 1:
        fail(f"load tag mismatch: {records!r}")
    if (
        retire["wb_valid"] != "1"
        or retire["store_wb_predicate"] != "0"
        or response["response_valid"] != "1"
        or response["response_has_data"] != "1"
    ):
        fail(f"load completion qualification mismatch: {records!r}")
    return pc


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: verify_owned_rocket_postrequest_exception.py LOG SIGNATURE")
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
    if (cause, tval, trap_count) != (MISALIGNED_LOAD_CAUSE, EXCEPTION_ADDRESS, 1):
        fail(f"trap signature mismatch: {signature!r}")

    lifecycle = [
        parse(line) for line in log.splitlines() if line.startswith(LIFECYCLE_PREFIX)
    ]
    if len(lifecycle) != 10:
        fail(f"expected two completed aligned loads, found {len(lifecycle)} records")
    before_pc = verify_load(lifecycle[:5], "1")
    after_pc = verify_load(lifecycle[5:], "2")

    exception = [
        parse(line) for line in log.splitlines() if line.startswith(EXCEPTION_PREFIX)
    ]
    if [record.get("event") for record in exception] != ["request", "exception"]:
        fail(f"exact exception lifecycle mismatch: {exception!r}")
    request, outcome = exception
    require_keys(
        request,
        {
            "event", "epoch", "sequence", "attempt", "pc", "address", "store",
            "tag", "request_accepted", "event_source",
        },
    )
    require_keys(
        outcome,
        {
            "event", "epoch", "sequence", "pc", "address", "store", "tag",
            "cause", "ma_ld", "ma_st", "take_pc_wb", "promotion",
        },
    )
    if {
        key: request[key]
        for key in ("epoch", "sequence", "attempt", "store", "request_accepted", "event_source")
    } != {
        "epoch": "1", "sequence": "1", "attempt": "1", "store": "0",
        "request_accepted": "1", "event_source": "rocket-pinned",
    }:
        fail(f"request qualification mismatch: {request!r}")
    if {
        key: outcome[key]
        for key in ("epoch", "sequence", "store", "cause", "ma_ld", "ma_st", "take_pc_wb", "promotion")
    } != {
        "epoch": "1", "sequence": "1", "store": "0", "cause": "4",
        "ma_ld": "1", "ma_st": "0", "take_pc_wb": "1", "promotion": "blocked",
    }:
        fail(f"exception qualification mismatch: {outcome!r}")
    request_pc = int(request["pc"], 16)
    if not (
        int(request["address"], 16) == int(outcome["address"], 16) == EXCEPTION_ADDRESS
        and int(outcome["pc"], 16) == request_pc
        and int(outcome["tag"], 16) == int(request["tag"], 16)
        and request_pc not in {before_pc, after_pc}
    ):
        fail(f"request/exception correlation mismatch: {exception!r}")

    print(
        "ROCKET-POSTREQUEST-EXCEPTION-V1 status=OK event_source=rocket-pinned "
        "cpu_execution=rtl-simulation accepted_requests=1 wb_exceptions=1 "
        "exception=misaligned-load promotion=blocked aligned_loads=2 aligned_retries=2 before_after_equal=1 "
        f"observed_value=0x{before_value:08x} postrequest_exception=covered "
        "post_tl_a_exception=not-run transport_token_correlation=not-carried "
        "semantic_initiator=not-proven general_rollback=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
