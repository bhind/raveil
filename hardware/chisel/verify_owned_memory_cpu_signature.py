#!/usr/bin/env python3
from pathlib import Path
import hashlib
import sys


EXPECTED = (
    1,
    0,
    0x11223344,
    0x5522AA44,
    0xCAFEBABE,
    2,
    8,
    8,
    2,
    3,
    2,
    1,
)

SOURCE_RANGES = {
    "rocket": (8224, 8256),
    "boom": (8288, 8320),
}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in SOURCE_RANGES:
        raise SystemExit(
            "usage: verify_owned_memory_cpu_signature.py {rocket|boom} SIGNATURE"
        )
    cpu = sys.argv[1]
    source_start, source_end = SOURCE_RANGES[cpu]
    raw = Path(sys.argv[2]).read_bytes()
    lines = [line.strip() for line in raw.decode("ascii").splitlines()]
    observed = tuple(int(line, 16) for line in lines if line)
    expected_prefix = EXPECTED + (
        source_start,
        source_end,
        8,
        8,
        0,
        0,
    )
    if (
        len(observed) != 30
        or observed[:18] != expected_prefix
        or not source_start <= observed[18] < source_end
        or not source_start <= observed[19] < source_end
        or observed[20:24] != (2, 2, 8, 8)
        or observed[24:26] != (0, 0)
        or not source_start <= observed[26] < source_end
        or not source_start <= observed[27] < source_end
        or observed[28:] != (2, 2)
    ):
        raise SystemExit(
            f"owned memory CPU signature mismatch: observed={observed!r} "
            f"expected_prefix={expected_prefix!r} source_range="
            f"[{source_start},{source_end}) phases=(2,2) "
            "dcache_origin=(8,8) non_dcache_origin=(0,0)"
        )
    print(
        f"OWNED-MEMORY-CPU-SIGNATURE-V3 status=OK cpu={cpu} "
        "tohost=1 reset_phase=0 data=11223344,5522aa44,cafebabe "
        "phase=2 accepted=8 completed=8 "
        "installation_reads=2 installation_writes=3 "
        "execution_reads=2 execution_writes=1 "
        f"expected_source_range={source_start}:{source_end} "
        "expected_source_accepted=8 expected_source_completed=8 "
        "unexpected_source_accepted=0 unexpected_source_completed=0 "
        f"last_sources={observed[18]},{observed[19]} "
        "last_phases=2,2 "
        "dcache_origin_accepted=8 dcache_origin_completed=8 "
        "non_dcache_origin_accepted=0 non_dcache_origin_completed=0 "
        f"last_dcache_origin_sources={observed[26]},{observed[27]} "
        "last_dcache_origin_phases=2,2 "
        "dcache_origin_path=observed semantic_initiator=not-proven "
        f"signature_sha256={hashlib.sha256(raw).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
