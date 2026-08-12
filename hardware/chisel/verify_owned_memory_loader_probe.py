#!/usr/bin/env python3
import sys
from pathlib import Path


SOURCE_RANGES = {
    "rocket": (8224, 8256),
    "boom": (8288, 8320),
}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in SOURCE_RANGES:
        raise SystemExit("usage: verify_owned_memory_loader_probe.py rocket|boom SIGNATURE")
    cpu = sys.argv[1]
    lines = [line.strip() for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
    if len(lines) != 33:
        raise SystemExit(f"expected 33 signature words, got {len(lines)}")
    try:
        observed = [int(line, 16) for line in lines]
    except ValueError as exc:
        raise SystemExit(f"signature is not hexadecimal: {exc}") from exc

    expected = [
        1, 2, 2, 0, 0, 2, 2, 0, 0, 2, 2,
        None, None, 0, 0, 0x6C6F6164,
        3, 3, 1, 1, 2, 2, 1, 1, 2, 2,
        None, None, 0, 0, *SOURCE_RANGES[cpu], 0,
    ]
    for index, (actual, wanted) in enumerate(zip(observed, expected, strict=True)):
        if wanted is not None and actual != wanted:
            raise SystemExit(
                f"signature word {index} mismatch: expected 0x{wanted:08x}, got 0x{actual:08x}"
            )
    for index in (11, 12):
        if not 0 <= observed[index] < 8192:
            raise SystemExit(f"pre-CPU source word {index} is outside serial range: {observed[index]}")
    start, end = SOURCE_RANGES[cpu]
    for index in (26, 27):
        if not start <= observed[index] < end:
            raise SystemExit(f"DCache source word {index} is outside [{start},{end}): {observed[index]}")

    print(
        "OWNED-MEMORY-LOADER-PROBE-V1 status=OK "
        f"cpu={cpu} serial_source={observed[11]},{observed[12]} "
        "pre_cpu_origin=0,0 pre_cpu_non_origin=2,2 loader_requests=2 "
        f"dcache_source={observed[26]},{observed[27]} "
        "post_cpu_origin=1,1 post_cpu_non_origin=2,2 "
        "loader_path=SimTSI-FESVR-PT_LOAD-tested semantic_initiator=not-proven "
        "resource_match_verified=0 matched_comparison_ready=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
