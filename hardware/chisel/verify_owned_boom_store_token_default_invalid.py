#!/usr/bin/env python3
"""Verify that absent BOOM token production remains default-invalid at manager D."""

from pathlib import Path
import re
import sys


TOKEN_PREFIX = "RAVEIL-OWNED-TL-TOKEN-V1"
FATE_PREFIX = "RAVEIL-OWNED-TL-FATE-V1"
ADDRESS = 0x08000100
SOURCE_START = 8288
SOURCE_END = 8320


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM default-invalid token verification failed: {message}")


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
        fail("usage: verify_owned_boom_store_token_default_invalid.py LOG")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    token_records = [
        parse(line) for line in log.splitlines() if line.startswith(TOKEN_PREFIX)
    ]
    if [record.get("event") for record in token_records] != ["a", "d"]:
        fail(f"exact default-invalid token A/D order mismatch: {token_records!r}")
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
        "valid": "0", "epoch": "0", "sequence": "0", "opcode": "0",
        "size": "2", "dcache_origin": "1", "classification": "0",
    }:
        fail(f"default-invalid token A mismatch: {token_a!r}")
    if int(token_a["address"], 16) != ADDRESS:
        fail(f"default-invalid token A address mismatch: {token_a!r}")
    source = int(token_a["source"])
    if not SOURCE_START <= source < SOURCE_END:
        fail(f"default-invalid token source is outside BOOM range: {source}")
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
        fail(f"default-invalid token D mismatch: {token_d!r}")

    fate_records = [
        parse(line) for line in log.splitlines() if line.startswith(FATE_PREFIX)
    ]
    if [record.get("event") for record in fate_records] != ["a", "d", "a", "d"]:
        fail(f"exact manager A/D order mismatch: {fate_records!r}")
    put_a, put_d = fate_records[:2]
    if int(put_a.get("address", "-1"), 16) != ADDRESS:
        fail(f"manager Put address mismatch: {put_a!r}")
    if {
        "source": put_a.get("source"),
        "opcode": put_a.get("opcode"),
        "dcache_origin": put_a.get("dcache_origin"),
    } != {
        "source": token_a["source"], "opcode": "0", "dcache_origin": "1",
    }:
        fail(f"manager Put/token A mismatch: {put_a!r} {token_a!r}")
    if {
        "source": put_d.get("source"),
        "opcode": put_d.get("opcode"),
        "denied": put_d.get("denied"),
        "corrupt": put_d.get("corrupt"),
    } != {
        "source": token_d["source"], "opcode": "0", "denied": "0",
        "corrupt": "0",
    }:
        fail(f"manager Put/token D mismatch: {put_d!r} {token_d!r}")

    print(
        "BOOM-STORE-TOKEN-DEFAULT-INVALID-V1 status=OK cpu_execution=rtl-simulation "
        f"address=0x{ADDRESS:08x} source={source} token_a_d=default-invalid-zero "
        "token_classification=unknown-default-invalid "
        "semantic_attribution=not-promoted manager_put_a_d=observed "
        "manager_transaction=completed "
        "store_side_effect_readback=verified-by-store-verifier "
        "semantic_initiator=not-promoted general_missing_metadata=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
