#!/usr/bin/env python3
"""Verify direct S1-kill and owned-manager A/D observations for one Rocket redirect."""

from pathlib import Path
import re
import sys


CORE_PREFIX = "RAVEIL-ROCKET-DCACHE-FATE-V1"
LIFECYCLE_PREFIX = "RAVEIL-ROCKET-REQUEST-RETIRE-V1"
TL_PREFIX = "RAVEIL-OWNED-TL-FATE-V1"
ADDRESS = 0x08000100
MAGIC = 0x4B1D2E3F
SOURCE_START = 8224
SOURCE_END = 8256
TL_GET = 4
TL_ACCESS_ACK_DATA = 1


def fail(message: str) -> "None":
    raise SystemExit(f"Rocket redirect DCache-fate verification failed: {message}")


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
        fail("usage: verify_owned_rocket_redirect_dcache_fate.py LOG SIGNATURE")

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

    core_records = [
        parse(line) for line in log.splitlines() if line.startswith(CORE_PREFIX)
    ]
    if len(core_records) != 1:
        fail(f"expected one direct S1 record, found {len(core_records)}")
    s1 = core_records[0]
    require_keys(
        s1,
        {
            "event", "epoch", "sequence", "pc", "address", "store", "tag",
            "s1_kill", "s2_kill", "correlation",
        },
    )
    if {
        key: s1[key]
        for key in (
            "event", "epoch", "sequence", "store", "s1_kill", "s2_kill",
            "correlation",
        )
    } != {
        "event": "s1",
        "epoch": "1",
        "sequence": "2",
        "store": "1",
        "s1_kill": "1",
        "s2_kill": "0",
        "correlation": "accepted-request-next-cycle",
    }:
        fail(f"S1 qualification mismatch: {s1!r}")
    if int(s1["address"], 16) != ADDRESS or int(s1["pc"], 16) == 0:
        fail(f"invalid S1 address or PC: {s1!r}")

    lifecycle_records = [
        parse(line)
        for line in log.splitlines()
        if line.startswith(LIFECYCLE_PREFIX)
    ]
    expected_lifecycle = [
        ("allocate", "1"), ("request", "1"), ("retire", "1"),
        ("response", "1"), ("allocate", "2"), ("request", "2"),
        ("kill", "2"), ("allocate", "3"), ("request", "3"),
        ("retire", "3"), ("response", "3"),
    ]
    if [
        (record.get("event"), record.get("sequence"))
        for record in lifecycle_records
    ] != expected_lifecycle:
        fail(f"exact lifecycle order mismatch: {lifecycle_records!r}")
    killed_requests = [
        record
        for record in lifecycle_records
        if record.get("event") == "request" and record.get("sequence") == "2"
    ]
    killed_events = [
        record
        for record in lifecycle_records
        if record.get("event") == "kill" and record.get("sequence") == "2"
    ]
    if len(killed_requests) != 1 or len(killed_events) != 1:
        fail("expected one sequence-2 request and one sequence-2 kill record")
    killed_request = killed_requests[0]
    killed_event = killed_events[0]
    require_keys(
        killed_request,
        {"event", "epoch", "sequence", "attempt", "pc", "address", "store", "tag"},
    )
    require_keys(
        killed_event,
        {
            "event", "epoch", "sequence", "branch_pc", "pc", "store", "reason",
            "request_accepted", "branch", "taken", "direction_misprediction", "promotion",
        },
    )
    if {
        "epoch": killed_request["epoch"],
        "sequence": killed_request["sequence"],
        "attempt": killed_request["attempt"],
        "store": killed_request["store"],
    } != {"epoch": "1", "sequence": "2", "attempt": "1", "store": "1"}:
        fail(f"sequence-2 request qualification mismatch: {killed_request!r}")
    if {
        "epoch": killed_event["epoch"],
        "sequence": killed_event["sequence"],
        "store": killed_event["store"],
        "reason": killed_event["reason"],
        "request_accepted": killed_event["request_accepted"],
        "promotion": killed_event["promotion"],
    } != {
        "epoch": "1",
        "sequence": "2",
        "store": "1",
        "reason": "mem-redirect",
        "request_accepted": "1",
        "promotion": "blocked",
    }:
        fail(f"sequence-2 kill qualification mismatch: {killed_event!r}")
    if not (
        int(s1["pc"], 16)
        == int(killed_request["pc"], 16)
        == int(killed_event["pc"], 16)
        and int(s1["address"], 16) == int(killed_request["address"], 16) == ADDRESS
        and int(s1["tag"], 16) == int(killed_request["tag"], 16)
    ):
        fail(f"Rocket request/S1 correlation mismatch: {s1!r} {killed_request!r}")

    tl_records = [
        parse(line) for line in log.splitlines() if line.startswith(TL_PREFIX)
    ]
    if len(tl_records) != 4:
        fail(f"expected two manager A/D pairs, found {len(tl_records)} records")
    if [record.get("event") for record in tl_records] != ["a", "d", "a", "d"]:
        fail(f"manager A/D order mismatch: {tl_records!r}")

    observed_sources: list[int] = []
    for index in range(2):
        a_record = tl_records[index * 2]
        d_record = tl_records[index * 2 + 1]
        sequence = str(index + 1)
        require_keys(
            a_record,
            {
                "event", "manager_sequence", "address", "source", "opcode",
                "size", "dcache_origin", "expected_source", "phase",
            },
        )
        require_keys(
            d_record,
            {
                "event", "manager_sequence", "source", "opcode", "size",
                "denied", "corrupt", "request_opcode", "phase",
            },
        )
        if a_record["manager_sequence"] != sequence or d_record["manager_sequence"] != sequence:
            fail(f"manager sequence mismatch: {a_record!r} {d_record!r}")
        if int(a_record["address"], 16) != ADDRESS:
            fail(f"manager address mismatch: {a_record!r}")
        source = int(a_record["source"], 10)
        if not SOURCE_START <= source < SOURCE_END:
            fail(f"manager source is outside the pinned Rocket range: {source}")
        if int(d_record["source"], 10) != source:
            fail(f"manager A/D source mismatch: {a_record!r} {d_record!r}")
        observed_sources.append(source)
        if {
            "opcode": a_record["opcode"],
            "size": a_record["size"],
            "dcache_origin": a_record["dcache_origin"],
            "expected_source": a_record["expected_source"],
            "phase": a_record["phase"],
        } != {
            "opcode": str(TL_GET),
            "size": "2",
            "dcache_origin": "1",
            "expected_source": "1",
            "phase": "0",
        }:
            fail(f"manager A qualification mismatch: {a_record!r}")
        if {
            "opcode": d_record["opcode"],
            "size": d_record["size"],
            "denied": d_record["denied"],
            "corrupt": d_record["corrupt"],
            "request_opcode": d_record["request_opcode"],
            "phase": d_record["phase"],
        } != {
            "opcode": str(TL_ACCESS_ACK_DATA),
            "size": "2",
            "denied": "0",
            "corrupt": "0",
            "request_opcode": str(TL_GET),
            "phase": "0",
        }:
            fail(f"manager D qualification mismatch: {d_record!r}")

    print(
        "ROCKET-REDIRECT-DCACHE-FATE-V1 status=OK event_source=rocket-pinned "
        "cpu_execution=rtl-simulation dcache_s1_kill=observed s2_kill=not-asserted "
        "rocket_request_s1_correlation=observed "
        "manager_a_get=2 manager_a_put=0 manager_d=2 wrong_path_store_tl_a=not-observed "
        "transport_token_correlation=not-carried manager_a_d_source_correlation=observed "
        f"last_manager_source={observed_sources[-1]} before_after_equal=1 "
        f"observed_value=0x{before_value:08x} pre_request_kill=not-run "
        "later_cycle_kill=not-run semantic_initiator=not-proven resource_match_verified=0 "
        "matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
