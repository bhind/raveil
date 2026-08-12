#!/usr/bin/env python3
"""Verify exact config-specific Debug SBA and DCache TileLink source ranges."""

from pathlib import Path
import hashlib
import re
import sys


EXPECTED = {
    "rocket": {
        "config": "RaveilOwnedDebugSBARocketConfig",
        "dcache_input": (513, 514),
        "debug_input": (256, 257),
        "dcache": (16416, 16448),
        "debug": (8192, 8224),
    },
    "boom": {
        "config": "RaveilOwnedDebugSBASmallBoomConfig",
        "dcache_input": (515, 516),
        "debug_input": (256, 257),
        "dcache": (16480, 16512),
        "debug": (8192, 8224),
    },
}


def source_range(text: str, master: str) -> tuple[int, int]:
    # GraphML repeats a master at multiple diplomacy transforms. The first
    # occurrence is the generated manager-list coordinate used by the
    # manager-adjacent fragmenter expansion checked below.
    match = re.search(
        rf"Master Name = {re.escape(master)}.*?sourceId = IdRange\((\d+),(\d+)\)",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise SystemExit(f"missing source range for {master}")
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in EXPECTED:
        raise SystemExit("usage: verify_owned_debug_sba_source_map.py {rocket|boom} GRAPHML")
    cpu = sys.argv[1]
    graph = Path(sys.argv[2])
    raw = graph.read_bytes()
    text = raw.decode("utf-8")
    expected = EXPECTED[cpu]
    observed = {
        "serial": source_range(text, "serial_tl_0"),
        "dcache_input": source_range(text, "Core 0 DCache MMIO"),
        "debug_input": source_range(text, "debug"),
        "custom_boot": source_range(text, "custom-boot"),
        "fragmenter": source_range(text, "TLFragmenter"),
    }
    if expected["config"] not in graph.name:
        raise SystemExit(f"wrong Debug SBA graph: {graph.name}")
    if (
        observed["serial"] != (0, 256)
        or observed["custom_boot"] != (1024, 1025)
        or observed["fragmenter"] != (0, 32800)
    ):
        raise SystemExit(f"fixed client range drifted: {observed!r}")
    if observed["dcache_input"] != expected["dcache_input"] or observed["debug_input"] != expected["debug_input"]:
        raise SystemExit(f"Debug SBA input source map drifted: {observed!r}")
    factor = observed["fragmenter"][1] // observed["custom_boot"][1]
    dcache = tuple(value * factor for value in observed["dcache_input"])
    debug = tuple(value * factor for value in observed["debug_input"])
    if factor != 32 or dcache != expected["dcache"] or debug != expected["debug"]:
        raise SystemExit(
            f"Debug SBA fragmenter expansion drifted: factor={factor} dcache={dcache} debug={debug} observed={observed!r}"
        )
    print(
        "OWNED-DEBUG-SBA-SOURCE-MAP-V1 status=OK "
        f"cpu={cpu} config={expected['config']} "
        f"debug_range={debug[0]}:{debug[1]} dcache_range={dcache[0]}:{dcache[1]} "
        "source_client_class=topology-only semantic_initiator=not-proven "
        f"graph_sha256={hashlib.sha256(raw).hexdigest()} "
        "evidence=rtl-elaboration-topology performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
