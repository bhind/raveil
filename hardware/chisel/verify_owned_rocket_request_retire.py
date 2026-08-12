#!/usr/bin/env python3
"""Verify a bounded pinned-Rocket request/retirement event stream."""

from pathlib import Path
import re
import sys


PREFIX = "RAVEIL-ROCKET-REQUEST-RETIRE-V1"
ADDRESS = 0x08000100


def fail(message: str) -> "None":
    raise SystemExit(f"Rocket request-retire verification failed: {message}")


def parse(line: str) -> dict[str, str]:
    # Chisel printf pads decimal UInt values after '=' to the signal width.
    # Remove only that formatting whitespace before applying the exact schema.
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
        fail("usage: verify_owned_rocket_request_retire.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if signature != (1, 0x4B1D2E3F):
        fail(f"signature mismatch: {signature!r}")

    records = [parse(line) for line in log.splitlines() if line.startswith(PREFIX)]
    if len(records) != 7:
        fail(f"expected seven lifecycle records, found {len(records)}")
    events = [record.get("event") for record in records]
    if events[:5] != ["allocate", "request", "retire", "allocate", "request"]:
        fail(f"event order mismatch: {records!r}")
    if set(events[5:]) != {"retire", "response"}:
        fail(f"load completion event mismatch: {records!r}")

    pcs: list[int] = []
    token_records = ((records[0], records[1], records[2], None),
                     (records[3], records[4],
                      next(record for record in records[5:] if record["event"] == "retire"),
                      next(record for record in records[5:] if record["event"] == "response")))
    for token_index, (allocate, request, retire, response) in enumerate(token_records, 1):
        require_keys(
            allocate,
            {"event", "epoch", "sequence", "pc", "address", "store", "event_source"},
        )
        require_keys(
            request,
            {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"},
        )
        require_keys(
            retire,
            {"event", "epoch", "sequence", "pc", "store", "wb_valid", "store_wb_predicate"},
        )
        expected_store = "1" if token_index == 1 else "0"
        for record in (allocate, request, retire):
            if record["epoch"] != "1" or record["sequence"] != str(token_index):
                fail(f"token mismatch: {record!r}")
            if record["store"] != expected_store:
                fail(f"operation mismatch: {record!r}")
        if allocate["event_source"] != "rocket-pinned":
            fail("event source is not pinned Rocket")
        if request["attempt"] != "1":
            fail("unexpected replay or duplicate request")
        request_tag = int(request["tag"], 16)
        for record in (allocate, request):
            if int(record["address"], 16) != ADDRESS:
                fail(f"address mismatch: {record!r}")
        pc = int(allocate["pc"], 16)
        if int(request["pc"], 16) != pc or int(retire["pc"], 16) != pc:
            fail(f"PC correlation mismatch: {allocate!r} {request!r} {retire!r}")
        pcs.append(pc)
        if retire["wb_valid"] != "1":
            fail("retirement was not qualified by wb_valid")
        if retire["store_wb_predicate"] != expected_store:
            fail(f"store WB predicate mismatch: {retire!r}")
        if token_index == 1:
            if response is not None:
                fail("store unexpectedly has a data response record")
        else:
            assert response is not None
            require_keys(
                response,
                {"event", "epoch", "sequence", "tag", "store", "response_valid", "response_has_data"},
            )
            if response["epoch"] != "1" or response["sequence"] != "2":
                fail(f"response token mismatch: {response!r}")
            if response["store"] != "0" or response["response_valid"] != "1" or response["response_has_data"] != "1":
                fail(f"response qualification mismatch: {response!r}")
            if int(response["tag"], 16) != request_tag:
                fail(f"request/response tag mismatch: {request!r} {response!r}")
    if len(set(pcs)) != 2 or not all(re.fullmatch(r"[0-9a-fA-F]+", f"{pc:x}") for pc in pcs):
        fail(f"PCs are not two distinct values: {pcs!r}")

    print(
        "ROCKET-REQUEST-RETIRE-WITNESS-V1 status=OK event_source=rocket-pinned "
        "cpu_execution=rtl-simulation allocations=2 requests=2 retirements=2 responses=1 "
        "load_positive=response-and-wb-observed store_positive=wb-observed "
        "dcache_response_tag_match=covered "
        "store_wb_predicate=wb_valid-and-isWrite core_replay=not-observed "
        "dcache_retry=not-observed negative_lifecycle=not-run "
        "d_token_correlation=not-run semantic_initiator=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
