#!/usr/bin/env python3
"""Read-only known-optimization control; never an optimizer or admission path.

Run from the repository root: python3 docs/research/probes/constant_work_baseline.py
The fixed fixture proves a test harness boundary, not a novel transformation,
representative model behavior, RTL execution, or measured performance.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import itertools
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from raveil.graph_device_dag import (  # noqa: E402
    MAX_IMMEDIATE, compile_descriptor, graph_oracle, software_fallback,
)

FIXTURE = "examples/graph-workloads/inputs/threshold-cross-dilate-descriptor.json"
INPUT = "examples/graph-workloads/inputs/threshold-cross-dilate-input.json"
SOURCES = (
    FIXTURE, INPUT, "raveil/graph_device_dag.py",
    "raveil/graph_device_affine.py", "raveil/graph_device_mvp.py",
    "raveil/riscv_stencil_signature.py",
    "docs/research/probes/constant_work_baseline.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pair(threshold):
    """Two hand-authored equivalent graphs, restricted to one existing fixture."""
    before = json.loads((ROOT / FIXTURE).read_text())
    require(before["schema"] == "raveil.graph-device-dag/v5", "fixture schema drift")
    require(before["affine"] == {"rows": 8, "columns": 8,
            "input_stride": 10, "output_stride": 8}, "fixture shape drift")
    require(len(before["nodes"]) == 15, "fixture node count drift")
    loads = [deepcopy(n) for n in before["nodes"] if n["op"] == "LOAD_U32"]
    expected = {"center": (0, 0), "north": (-1, 0), "south": (1, 0),
                "west": (0, -1), "east": (0, 1)}
    require({n["id"]: (n["address"]["row_delta"], n["address"]["column_delta"])
             for n in loads} == expected, "fixture load drift")
    for node in before["nodes"]:
        if node["op"] == "GE_IMM_U32":
            require(node["immediate"] == 100, "fixture threshold drift")
            node["immediate"] = threshold
    after = deepcopy(before)
    after["graph_id"] = "threshold-after-max-control"
    after["nodes"] = loads + [
        {"id": "ns", "op": "MAX_U32", "inputs": ["north", "south"]},
        {"id": "we", "op": "MAX_U32", "inputs": ["west", "east"]},
        {"id": "neighbors", "op": "MAX_U32", "inputs": ["ns", "we"]},
        {"id": "all-max", "op": "MAX_U32", "inputs": ["center", "neighbors"]},
        {"id": "hit", "op": "GE_IMM_U32", "input": "all-max", "immediate": threshold},
        {"id": "store", "op": "STORE_U32", "input": "hit"},
    ]
    return before, after


def independent_reference(words, threshold):
    # Direct five-address specification, independent of compiler/opcode/graph traversal.
    out = [0] * 256
    for row in range(8):
        for col in range(8):
            center = (row + 1) * 10 + col + 1
            out[row * 8 + col] = int(any(words[i] >= threshold for i in
                (center, center - 10, center + 10, center - 1, center + 1)))
    return out


def summary(graph, program):
    counts = Counter(n["op"] for n in graph["nodes"])
    return {"ops_per_cell": dict(sorted(counts.items())),
            "instruction_count": program["instruction_count"],
            "fixed_install_payload_bytes": 4 * len(program["payload"]),
            "logical_load_store_bytes_64_cells":
                64 * 4 * program["transactions_per_output"],
            "program_sha256": program["program_sha256"]}


def main():
    fixture_input = json.loads((ROOT / INPUT).read_text())
    # Explicit fixture schema is checked below; snapshots never become immutable weights.
    require(set(fixture_input) == {"schema", "words"}, "input fixture fields drift")
    require(fixture_input["schema"] == "raveil.graph-input/v1", "input schema drift")
    actual_words = fixture_input["words"]
    require(len(actual_words) == 324 and all(type(x) is int and 0 <= x <= 0xffffffff
            for x in actual_words), "input fixture words drift")
    rows, cases, lemma_cases = [], 0, 0
    rng = random.Random(197)
    for threshold in (0, 1, 100, MAX_IMMEDIATE):
        before, after = pair(threshold)
        programs = [compile_descriptor(g) for g in (before, after)]
        values = sorted({0, 1, max(0, threshold - 1), threshold,
                         threshold + 1, 0xffffffff})
        # Exhaust the chosen boundary alphabet, not the full uint32 domain.
        for values5 in itertools.product(values, repeat=5):
            require(max(int(x >= threshold) for x in values5)
                    == int(max(values5) >= threshold), "identity failed")
            lemma_cases += 1
        inputs = [actual_words, *([v] * 324 for v in values),
                  [values[i % len(values)] for i in range(324)],
                  *([rng.getrandbits(32) for _ in range(324)] for _ in range(8)),
                  *([rng.choice(values) for _ in range(324)] for _ in range(8))]
        for words in inputs:
            expected = independent_reference(words, threshold)
            for graph, program in zip((before, after), programs):
                require(graph_oracle(graph, words) == expected, "graph oracle mismatch")
                require(software_fallback(program, words) == expected, "fallback mismatch")
            cases += 1
        rows.append({"threshold": threshold, "before": summary(before, programs[0]),
                     "known_control": summary(after, programs[1])})
    # Counterexample: differing thresholds do not permit the same interchange.
    require(max(int(5 >= 10), int(0 >= 0)) != int(max(5, 0) >= 10),
            "negative control lost")
    print(json.dumps({"schema": "raveil.constant-work-preflight/v1",
        "evidence_class": "host-functional-and-analytical-counts",
        "treatment": "known monotone threshold/max identity; not novel",
        "source_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in SOURCES},
        "functional_input_cases": cases, "boundary_alphabet_cases": lemma_cases,
        "different_threshold_counterexample": True, "rows": rows,
        "timing_measured": False, "rtl_executed": False,
        "real_model_weights_tested": False, "hardware_advantage_established": False},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
