#!/usr/bin/env python3
"""Verify one BOOM store token from CPU authorization through manager D."""

from pathlib import Path
import re
import sys


CORE_PREFIX = "RAVEIL-BOOM-STORE-AUTH-V1"
TL_PREFIX = "RAVEIL-OWNED-TL-FATE-V1"
TOKEN_PREFIX = "RAVEIL-OWNED-TL-TOKEN-V1"
ADDRESS = 0x08000100
MAGIC = 0x51A7C0DE
SOURCE_START = 8288
SOURCE_END = 8320
TL_PUT_FULL_DATA = 0
TL_GET = 4
TL_ACCESS_ACK = 0
TL_ACCESS_ACK_DATA = 1


def fail(message: str) -> "None":
    raise SystemExit(f"BOOM store token handoff verification failed: {message}")


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
        fail("usage: verify_owned_boom_store_token_handoff.py LOG SIGNATURE")
    log = Path(sys.argv[1]).read_text(encoding="utf-8")
    signature = tuple(
        int(line, 16)
        for line in Path(sys.argv[2]).read_text(encoding="ascii").splitlines()
        if line.strip()
    )
    if signature != (1, MAGIC, MAGIC):
        fail(f"signature mismatch: {signature!r}")

    records = [parse(line) for line in log.splitlines() if line.startswith(CORE_PREFIX)]
    if [record.get("event") for record in records] != [
        "authorize", "request", "response", "clear"
    ]:
        fail(f"exact BOOM-local lifecycle mismatch: {records!r}")
    authorize, request, response, clear = records
    common = {
        "event", "epoch", "sequence", "pc", "address", "rob_idx",
        "stq_idx", "br_mask", "lane",
    }
    require_keys(
        authorize,
        common | {"commit_valid", "arch_valid", "committed_write", "event_source"},
    )
    require_keys(request, common | {"request_accepted", "store"})
    require_keys(response, common | {"response_valid", "uses_stq", "succeeded_write"})
    require_keys(
        clear,
        common | {"request_seen", "response_seen", "stq_succeeded", "promotion"},
    )
    if {
        "epoch": authorize["epoch"],
        "sequence": authorize["sequence"],
        "commit_valid": authorize["commit_valid"],
        "arch_valid": authorize["arch_valid"],
        "committed_write": authorize["committed_write"],
        "event_source": authorize["event_source"],
    } != {
        "epoch": "1", "sequence": "1", "commit_valid": "1",
        "arch_valid": "1", "committed_write": "1", "event_source": "boom-pinned",
    }:
        fail(f"authorization qualification mismatch: {authorize!r}")
    if {"request_accepted": request["request_accepted"], "store": request["store"]} != {
        "request_accepted": "1", "store": "1"
    }:
        fail(f"request qualification mismatch: {request!r}")
    if {
        "response_valid": response["response_valid"],
        "uses_stq": response["uses_stq"],
        "succeeded_write": response["succeeded_write"],
    } != {"response_valid": "1", "uses_stq": "1", "succeeded_write": "1"}:
        fail(f"response qualification mismatch: {response!r}")
    if {
        "request_seen": clear["request_seen"],
        "response_seen": clear["response_seen"],
        "stq_succeeded": clear["stq_succeeded"],
        "promotion": clear["promotion"],
    } != {
        "request_seen": "1", "response_seen": "1", "stq_succeeded": "1",
        "promotion": "eligible-local",
    }:
        fail(f"clear qualification mismatch: {clear!r}")
    for field in (
        "epoch", "sequence", "pc", "address", "rob_idx", "stq_idx",
        "br_mask", "lane",
    ):
        if len({record[field] for record in records}) != 1:
            fail(f"{field} correlation mismatch: {records!r}")
    if int(authorize["address"], 16) != ADDRESS or int(authorize["pc"], 16) == 0:
        fail(f"audit address or PC mismatch: {authorize!r}")
    if int(authorize["br_mask"], 16) != 0 or int(authorize["lane"]) != 0:
        fail(f"exact BOOM context mismatch: {authorize!r}")

    token_records = [
        parse(line) for line in log.splitlines() if line.startswith(TOKEN_PREFIX)
    ]
    if [record.get("event") for record in token_records] != ["a", "d"]:
        fail(f"exact token A/D order mismatch: {token_records!r}")
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
        "valid": "1", "epoch": authorize["epoch"],
        "sequence": authorize["sequence"],
        "opcode": str(TL_PUT_FULL_DATA), "size": "2", "dcache_origin": "1",
        "classification": "1",
    }:
        fail(f"token A qualification mismatch: {token_a!r}")
    if int(token_a["address"], 16) != ADDRESS:
        fail(f"token A address mismatch: {token_a!r}")
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
        "valid": "1", "epoch": authorize["epoch"],
        "sequence": authorize["sequence"], "source": token_a["source"],
        "opcode": str(TL_ACCESS_ACK), "size": "2", "denied": "0",
        "corrupt": "0", "classification": "1",
    }:
        fail(f"token D qualification mismatch: {token_d!r}")
    if not SOURCE_START <= int(token_a["source"]) < SOURCE_END:
        fail(f"token A source is outside the pinned BOOM range: {token_a!r}")

    tl_records = [parse(line) for line in log.splitlines() if line.startswith(TL_PREFIX)]
    if [record.get("event") for record in tl_records] != ["a", "d", "a", "d"]:
        fail(f"exact manager A/D order mismatch: {tl_records!r}")
    observed_sources: list[int] = []
    for index, expected_opcode in enumerate(("put", "get")):
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
        source = int(a_record["source"])
        if not SOURCE_START <= source < SOURCE_END:
            fail(f"manager source is outside the pinned BOOM range: {source}")
        if int(d_record["source"]) != source:
            fail(f"manager A/D source mismatch: {a_record!r} {d_record!r}")
        observed_sources.append(source)
        a_opcode = int(a_record["opcode"])
        expected_a = a_opcode == TL_PUT_FULL_DATA if expected_opcode == "put" else a_opcode == TL_GET
        expected_d_opcode = TL_ACCESS_ACK if expected_opcode == "put" else TL_ACCESS_ACK_DATA
        if not expected_a or {
            "size": a_record["size"],
            "dcache_origin": a_record["dcache_origin"],
            "expected_source": a_record["expected_source"],
            "phase": a_record["phase"],
        } != {"size": "2", "dcache_origin": "1", "expected_source": "1", "phase": "0"}:
            fail(f"manager A qualification mismatch: {a_record!r}")
        if {
            "opcode": d_record["opcode"],
            "size": d_record["size"],
            "denied": d_record["denied"],
            "corrupt": d_record["corrupt"],
            "request_opcode": d_record["request_opcode"],
            "phase": d_record["phase"],
        } != {
            "opcode": str(expected_d_opcode), "size": "2", "denied": "0",
            "corrupt": "0", "request_opcode": str(a_opcode), "phase": "0",
        }:
            fail(f"manager D qualification mismatch: {d_record!r}")

    print(
        "BOOM-STORE-TOKEN-HANDOFF-V1 status=OK event_source=boom-pinned "
        "cpu_execution=rtl-simulation authorizations=1 requests=1 responses=1 clears=1 "
        f"sequence=1 pc=0x{int(authorize['pc'], 16):x} address=0x{ADDRESS:08x} "
        f"rob_idx={int(authorize['rob_idx'])} stq_idx={int(authorize['stq_idx'])} "
        f"manager_put_opcode={int(tl_records[0]['opcode'])} manager_puts=1 manager_gets=1 "
        f"manager_d=2 last_manager_source={observed_sources[-1]} "
        "store_authorization=observed boom_local_request_response_clear=observed "
        "manager_put_a_d=observed manager_a_d_source_correlation=observed "
        "transport_token_correlation=same-token-observed "
        "store_attribution=bounded-same-token-observed semantic_initiator=not-promoted "
        "malformed_metadata=fail-closed general_store_lifecycle=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )


if __name__ == "__main__":
    main()
