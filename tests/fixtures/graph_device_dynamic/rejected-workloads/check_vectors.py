"""Check T-0181 planning fixtures without implementing proposed opcodes."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[3]))

from raveil.graph_device_dag import GraphDeviceDagError, MAX_IMMEDIATE, validate_descriptor


MASK = 0xFFFFFFFF


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="ascii"))


def reject_current_attempts(fixture: dict) -> None:
    for attempt in fixture["current_attempts"]:
        try:
            validate_descriptor(attempt["descriptor"])
        except GraphDeviceDagError as error:
            assert str(error) == attempt["expected_error"], (str(error), attempt["expected_error"])
        else:
            raise AssertionError(f"current implementation unexpectedly admitted {fixture['candidate']}")


def proposed_ge_imm_admits(vector: dict) -> bool:
    immediate = vector["immediate"]
    return (type(immediate) is int and 0 <= immediate <= MAX_IMMEDIATE
            and vector["source_defined"] and vector["program_version"] == 6)


def main() -> None:
    const = load("full-width-source-free-fill.json")
    subtract = load("dark-frame-subtract-saturating.json")
    threshold = load("threshold-cross-dilate.json")
    for fixture in (const, subtract, threshold):
        assert fixture["schema"] == "raveil.rejected-graph-workload/v1"
        reject_current_attempts(fixture)

    for vector in const["truth_vectors"]:
        assert vector["output"] == vector["literal"] & MASK
    assert const["truth_vectors"][1]["literal"] == MAX_IMMEDIATE
    assert const["truth_vectors"][2]["literal"] == MAX_IMMEDIATE + 1
    assert 15 * MAX_IMMEDIATE < 4045620583

    for vector in subtract["truth_vectors"]:
        sample, dark = vector["inputs"]
        assert vector["output"] == max(sample - dark, 0)

    intended = threshold["current_attempts"][0]["descriptor"]
    assert len(intended["nodes"]) == 15
    assert sum(node["op"] == "GE_IMM_U32" for node in intended["nodes"]) == 5
    for vector in threshold["truth_vectors"]:
        assert vector["output"] == int(vector["input"] >= vector["threshold"])

    for vector in threshold["proposed_rejection_vectors"]:
        assert vector["expected"] == "reject"
        assert not proposed_ge_imm_admits(vector), vector["case"]

    print("T-0181 vectors PASS: 3 rejected programs, 4 current attempts, 15 truth and 5 proposed-rejection vectors")


if __name__ == "__main__":
    main()
