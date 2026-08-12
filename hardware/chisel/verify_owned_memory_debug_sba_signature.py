#!/usr/bin/env python3
"""Verify bounded DMI-to-Debug-SBA owned-memory functional evidence."""

from pathlib import Path
import hashlib
import sys


SOURCE_RANGES = {
    "rocket": {"dcache": (16416, 16448), "debug": (8192, 8224)},
    "boom": {"dcache": (16480, 16512), "debug": (8192, 8224)},
}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in SOURCE_RANGES:
        raise SystemExit(
            "usage: verify_owned_memory_debug_sba_signature.py {rocket|boom} SIGNATURE"
        )
    cpu = sys.argv[1]
    ranges = SOURCE_RANGES[cpu]
    raw = Path(sys.argv[2]).read_bytes()
    observed = tuple(
        int(line.strip(), 16)
        for line in raw.decode("ascii").splitlines()
        if line.strip()
    )
    if len(observed) != 37:
        raise SystemExit(f"Debug SBA signature length mismatch: {len(observed)}")
    debug_sources = observed[12:14] + observed[16:18] + observed[35:37]
    dcache_sources = observed[31:33]
    valid = (
        observed[0] == 1
        and observed[1:12] == (0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1)
        and observed[14:16] == (0, 0)
        and observed[18:21] == (0, 0, 0xA5)
        and observed[21:31] == (2, 2, 1, 1, 1, 1, 1, 1, 1, 1)
        and observed[33:35] == (0, 0)
        and all(ranges["debug"][0] <= value < ranges["debug"][1] for value in debug_sources)
        and all(ranges["dcache"][0] <= value < ranges["dcache"][1] for value in dcache_sources)
    )
    if not valid:
        raise SystemExit(
            f"owned memory Debug SBA signature mismatch: observed={observed!r} "
            f"ranges={ranges!r}"
        )
    print(
        "OWNED-MEMORY-DEBUG-SBA-SIGNATURE-V1 status=OK "
        f"cpu={cpu} payload=a5 pre_aggregate=1:1 post_aggregate=2:2 "
        "expected_dcache=1:1 unexpected_debug=1:1 "
        "dcache_origin=1:1 non_dcache_origin=1:1 "
        f"debug_source_range={ranges['debug'][0]}:{ranges['debug'][1]} "
        f"dcache_source_range={ranges['dcache'][0]}:{ranges['dcache'][1]} "
        "request_response_phase=0:0 source_client_class=debug-sba-observed "
        "semantic_initiator=not-proven evidence=rtl-simulation-functional "
        f"performance=not-measured signature_sha256={hashlib.sha256(raw).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
