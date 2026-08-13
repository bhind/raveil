#!/usr/bin/env python3
"""Verify the config-specific TileLink client map emitted by Chipyard."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys


EXPECTED = {
    "rocket": {
        "configs": (
            "RaveilOwnedRocketConfig",
            "RaveilOwnedRocketFateConfig",
        ),
        "input": (257, 258),
        "expanded": (8224, 8256),
    },
    "boom": {
        "configs": ("RaveilOwnedSmallBoomConfig",),
        "input": (259, 260),
        "expanded": (8288, 8320),
    },
}


def source_range(text: str, master: str) -> tuple[int, int]:
    match = re.search(
        rf"Master Name = {re.escape(master)}.*?"
        r"sourceId = IdRange\((\d+),(\d+)\)",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise SystemExit(f"missing source range for {master}")
    return int(match.group(1)), int(match.group(2))


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in EXPECTED:
        raise SystemExit(
            "usage: verify_owned_cpu_source_map.py {rocket|boom} GRAPHML"
        )
    cpu = sys.argv[1]
    graph = Path(sys.argv[2])
    raw = graph.read_bytes()
    text = raw.decode("utf-8")
    expected = EXPECTED[cpu]

    matching_configs = tuple(
        config
        for config in expected["configs"]
        if graph.name == f"chipyard.harness.TestHarness.{config}.graphml"
    )
    if len(matching_configs) != 1:
        raise SystemExit(
            f"wrong graph for {cpu}: expected one of {expected['configs']}, "
            f"got {graph.name}"
        )
    config = matching_configs[0]
    if source_range(text, "serial_tl_0") != (0, 256):
        raise SystemExit("serial/SimTSI source range drifted")
    if source_range(text, "Core 0 DCache MMIO") != expected["input"]:
        raise SystemExit("CPU DCache MMIO source range drifted")
    if source_range(text, "custom-boot") != (512, 513):
        raise SystemExit("custom-boot source range drifted")
    fragmenter_range = source_range(text, "TLFragmenter")
    if fragmenter_range != (0, 16416):
        raise SystemExit("manager-adjacent fragmenter source range drifted")

    factor = fragmenter_range[1] // 513
    observed_expanded = tuple(value * factor for value in expected["input"])
    if factor != 32 or observed_expanded != expected["expanded"]:
        raise SystemExit(
            f"fragmenter expansion drifted: factor={factor} "
            f"range={observed_expanded}"
        )

    print(
        "OWNED-CPU-SOURCE-MAP-V1 status=OK "
        f"cpu={cpu} config={config} "
        f"input_mmio_range={expected['input'][0]}:{expected['input'][1]} "
        f"manager_mmio_range={observed_expanded[0]}:{observed_expanded[1]} "
        "serial_range=0:8192 fragmenter_factor=32 "
        f"graph_sha256={hashlib.sha256(raw).hexdigest()} "
        "evidence=rtl-elaboration-topology performance=not-measured"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
