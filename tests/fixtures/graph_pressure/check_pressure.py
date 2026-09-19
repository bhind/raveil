"""Planning probes against the unchanged compiler; no hardware/performance claim."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from raveil.graph_device_dag import (GraphDeviceDagError, compile_descriptor,
                                     graph_oracle, software_fallback)
from raveil.riscv_stencil_signature import input_words

EXPECTED = {
    "chain16": ("instructions", "admitted"), "chain17": ("instructions", "rejected"),
    "eight-neighbor-dilation": ("instructions", "admitted"), "nine-cell-dilation": ("instructions", "rejected"),
    "retained8": ("registers", "admitted"), "retained9": ("registers", "rejected"),
    "late-consumer": ("schedule", "rejected"), "early-consumer": ("schedule", "admitted"),
    "shape16": ("shape", "admitted"), "rows17": ("shape", "rejected"), "columns17": ("shape", "rejected"),
    "input-stride9": ("stride", "rejected"), "input-window": ("stride", "rejected"),
    "output-stride7": ("stride", "rejected"), "output-window": ("stride", "rejected"),
    "halo1": ("halo", "admitted"), "halo2": ("halo", "rejected"),
}


def require(condition, detail):
    if not condition:
        raise ValueError(f"pressure fixture verification failed: {detail}")


def unused_nodes(descriptor):
    nodes = {node["id"]: node for node in descriptor["nodes"]}
    reached, pending = set(), [descriptor["nodes"][-1]["id"]]
    while pending:
        identifier = pending.pop()
        if identifier in reached:
            continue
        reached.add(identifier)
        node = nodes[identifier]
        pending.extend(node.get("inputs", []))
        if "input" in node:
            pending.append(node["input"])
    return sorted(set(nodes) - reached)


def check():
    source = Path(__file__).with_name("cases.json")
    fixtures = json.loads(source.read_text())
    require(fixtures["schema"] == "raveil.graph-pressure-fixtures/v1", "schema")
    cases = fixtures["cases"]
    require(len(cases) == len(EXPECTED), "case count")
    require({case["id"]: (case["dimension"], case["expected"]) for case in cases} == EXPECTED,
            "exact case/dimension/status coverage")
    results = []
    for case in cases:
        descriptor = case["descriptor"]
        result = {"id": case["id"], "dimension": case["dimension"],
                  "nodes": len(descriptor["nodes"]), "unused_nodes": unused_nodes(descriptor)}
        try:
            program = compile_descriptor(descriptor)
        except GraphDeviceDagError as exc:
            require(case["expected"] == "rejected", (case["id"], str(exc)))
            require(str(exc) == case["error"], (case["id"], str(exc)))
            result.update(status="rejected", error=str(exc))
        else:
            require(case["expected"] == "admitted", case["id"])
            require(len(program["payload"]) == 32, "transport")
            require(program["instruction_count"] == len(descriptor["nodes"]), "instruction count")
            for seed in (0, 5, 19):
                words = input_words(seed)
                require(graph_oracle(descriptor, words) == software_fallback(program, words), case["id"])
            result.update(status="admitted", program_sha256=program["program_sha256"],
                          schedule=[n["node_id"] for n in program["lowering_trace"]["instructions"]],
                          oracle_checks=3)
        results.append(result)
    by_id = {case["id"]: case["descriptor"] for case in cases}
    # Same value graph, changed author order only: current compiler rejection
    # cannot be interpreted as intrinsic arithmetic/hardware incapacity.
    for seed in (0, 5, 19):
        words = input_words(seed)
        require(graph_oracle(by_id["late-consumer"], words) == graph_oracle(by_id["early-consumer"], words),
                "schedule-pair oracle")
    require({node["id"]: node for node in by_id["late-consumer"]["nodes"]}
            == {node["id"]: node for node in by_id["early-consumer"]["nodes"]}, "same value graph")
    return {"schema": "raveil.graph-pressure-report/v1", "evidence_class": "planning-host-compiler",
            "hardware_executed": False, "performance_measured": False,
            "cases": results, "case_count": len(cases),
            "fixture_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                              for p in ("raveil/graph_device_dag.py", "raveil/graph_device_affine.py",
                                        "raveil/riscv_stencil_signature.py")}}


if __name__ == "__main__":
    print(json.dumps(check(), sort_keys=True, indent=2))
