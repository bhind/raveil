#!/usr/bin/env python3
"""Verify a valid BOOM token is cleared before owned-manager A and D."""

from pathlib import Path
import re
import sys


STRIP_PREFIX = "RAVEIL-BOOM-TOKEN-STRIP-V1"
TOKEN_PREFIX = "RAVEIL-OWNED-TL-TOKEN-V1"
FATE_PREFIX = "RAVEIL-OWNED-TL-FATE-V1"
ADDRESS = 0x08000100
SOURCE_START = 8288
SOURCE_END = 8320
IO_MSHR_SOURCE = 3


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM stripped token verification failed: {message}")


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
    if len(sys.argv) != 2:
        fail("usage: verify_owned_boom_store_token_stripped_after_valid.py LOG")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")

    lines = log.splitlines()
    strip_entries = [
        (index, parse(line))
        for index, line in enumerate(lines)
        if line.startswith(STRIP_PREFIX)
    ]
    strip_records = [record for _, record in strip_entries]
    if [record.get("event") for record in strip_records] != ["before", "after"]:
        fail(f"exact strip witness order mismatch: {strip_records!r}")
    before, after = strip_records
    strip_schema = {"event", "valid", "epoch", "sequence", "address", "source"}
    require_keys(before, strip_schema)
    require_keys(after, strip_schema)
    if {
        "valid": before["valid"],
        "epoch": before["epoch"],
        "sequence": before["sequence"],
    } != {"valid": "1", "epoch": "1", "sequence": "1"}:
        fail(f"pre-strip token is not the exact valid producer value: {before!r}")
    if {
        "valid": after["valid"],
        "epoch": after["epoch"],
        "sequence": after["sequence"],
    } != {"valid": "0", "epoch": "0", "sequence": "0"}:
        fail(f"post-strip token is not exact invalid/zero: {after!r}")
    for record in strip_records:
        if int(record["address"], 16) != ADDRESS:
            fail(f"strip witness address mismatch: {record!r}")
        if int(record["source"]) != IO_MSHR_SOURCE:
            fail(f"strip witness I/O-MSHR source mismatch: {record!r}")
    if before["source"] != after["source"]:
        fail(f"strip witness source mismatch: {strip_records!r}")

    token_entries = [
        (index, parse(line))
        for index, line in enumerate(lines)
        if line.startswith(TOKEN_PREFIX)
    ]
    token_records = [record for _, record in token_entries]
    if [record.get("event") for record in token_records] != ["a", "d"]:
        fail(f"exact manager token A/D order mismatch: {token_records!r}")
    token_a, token_d = token_records
    require_keys(
        token_a,
        {
            "event", "valid", "epoch", "sequence", "address", "source",
            "opcode", "size", "dcache_origin", "classification",
        },
    )
    require_keys(
        token_d,
        {
            "event", "valid", "epoch", "sequence", "source", "opcode",
            "size", "denied", "corrupt", "classification",
        },
    )
    if {
        "valid": token_a["valid"],
        "epoch": token_a["epoch"],
        "sequence": token_a["sequence"],
        "opcode": token_a["opcode"],
        "size": token_a["size"],
        "dcache_origin": token_a["dcache_origin"],
        "classification": token_a["classification"],
    } != {
        "valid": "0", "epoch": "0", "sequence": "0",
        "opcode": "0", "size": "2",
        "dcache_origin": "1", "classification": "0",
    }:
        fail(f"manager token A did not observe stripped metadata: {token_a!r}")
    if int(token_a["address"], 16) != ADDRESS:
        fail(f"manager token A address mismatch: {token_a!r}")
    manager_source = int(token_a["source"])
    if not SOURCE_START <= manager_source < SOURCE_END:
        fail(f"manager token source is outside BOOM range: {manager_source}")
    if {
        "valid": token_d["valid"],
        "epoch": token_d["epoch"],
        "sequence": token_d["sequence"],
        "source": token_d["source"],
        "opcode": token_d["opcode"],
        "size": token_d["size"],
        "denied": token_d["denied"],
        "corrupt": token_d["corrupt"],
        "classification": token_d["classification"],
    } != {
        "valid": "0", "epoch": "0", "sequence": "0",
        "source": token_a["source"], "opcode": "0", "size": "2",
        "denied": "0", "corrupt": "0", "classification": "0",
    }:
        fail(f"manager token D did not retain unknown classification: {token_d!r}")

    fate_entries = [
        (index, parse(line))
        for index, line in enumerate(lines)
        if line.startswith(FATE_PREFIX)
    ]
    fate_records = [record for _, record in fate_entries]
    if [record.get("event") for record in fate_records] != ["a", "d", "a", "d"]:
        fail(f"exact manager A/D order mismatch: {fate_records!r}")
    put_a, put_d = fate_records[:2]
    exact_order = (
        strip_entries[0][0], strip_entries[1][0], fate_entries[0][0],
        token_entries[0][0], token_entries[1][0], fate_entries[1][0],
        fate_entries[2][0], fate_entries[3][0],
    )
    if exact_order != tuple(sorted(exact_order)):
        fail(f"cross-ledger event order mismatch: {exact_order!r}")
    if int(put_a.get("address", "-1"), 16) != ADDRESS:
        fail(f"manager Put address mismatch: {put_a!r}")
    if {
        "source": put_a.get("source"),
        "opcode": put_a.get("opcode"),
        "size": put_a.get("size"),
        "dcache_origin": put_a.get("dcache_origin"),
    } != {
        "source": token_a["source"], "opcode": "0", "size": "2",
        "dcache_origin": "1",
    }:
        fail(f"manager Put/token A mismatch: {put_a!r} {token_a!r}")
    if {
        "source": put_d.get("source"),
        "opcode": put_d.get("opcode"),
        "size": put_d.get("size"),
        "denied": put_d.get("denied"),
        "corrupt": put_d.get("corrupt"),
        "request_opcode": put_d.get("request_opcode"),
    } != {
        "source": token_d["source"], "opcode": "0", "size": "2",
        "denied": "0", "corrupt": "0", "request_opcode": "0",
    }:
        fail(f"manager Put/token D mismatch: {put_d!r} {token_d!r}")

    print(
        "BOOM-STORE-TOKEN-STRIPPED-AFTER-VALID-V1 status=OK "
        "cpu_execution=rtl-simulation producer=valid-before-strip "
        "pre_strip_token=valid-epoch1-sequence1 post_strip_token=invalid-zero "
        f"address=0x{ADDRESS:08x} io_mshr_source={IO_MSHR_SOURCE} "
        f"manager_source={manager_source} source_is_identity=0 "
        "stripped_after_valid=observed token_classification=unknown-stripped "
        "semantic_attribution=not-promoted manager_put_a_d=observed "
        "manager_transaction=completed "
        "store_side_effect_readback=verified-by-store-verifier "
        "semantic_initiator=not-promoted general_stripped_metadata=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
