"""Owned compiler, validator, and oracle for the bounded static RTL region.

This module defines one functional-simulation contract.  It does not measure
performance and it does not expose a product ISA.
"""

from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json
from typing import Any


SCHEMA = "raveil.static-region/v1"
COMPILER_IDENTITY = "raveil.static-stencil-compiler/v1"
ORACLE_IDENTITY = "raveil.static-stencil-oracle/v1"
TARGET_SIGNATURE = "raveil.chisel.static-stencil-region/v1"
UINT32_MASK = (1 << 32) - 1


class StaticRegionContractError(ValueError):
    """The descriptor is outside the accepted RFC-0005 boundary."""


def compile_static_stencil_descriptor() -> dict[str, Any]:
    """Construct the only graph descriptor admitted by ADR-0039."""

    nodes = [
        {
            "id": "load_center",
            "op": "LOAD_U32",
            "effect": {"kind": "READ", "object": "A", "affine": "18*y+x"},
        },
        {
            "id": "load_north",
            "op": "LOAD_U32",
            "effect": {"kind": "READ", "object": "A", "affine": "18*(y-1)+x"},
        },
        {
            "id": "load_south",
            "op": "LOAD_U32",
            "effect": {"kind": "READ", "object": "A", "affine": "18*(y+1)+x"},
        },
        {
            "id": "load_west",
            "op": "LOAD_U32",
            "effect": {"kind": "READ", "object": "A", "affine": "18*y+x-1"},
        },
        {
            "id": "load_east",
            "op": "LOAD_U32",
            "effect": {"kind": "READ", "object": "A", "affine": "18*y+x+1"},
        },
        {"id": "add_0", "op": "ADD_U32"},
        {"id": "add_1", "op": "ADD_U32"},
        {"id": "add_2", "op": "ADD_U32"},
        {"id": "add_3", "op": "ADD_U32"},
        {
            "id": "store_output",
            "op": "STORE_U32",
            "effect": {
                "kind": "WRITE",
                "object": "B",
                "affine": "16*(y-1)+(x-1)",
            },
        },
    ]
    edges = [
        {"producer": "load_center", "consumer": "add_0", "input": 0},
        {"producer": "load_north", "consumer": "add_0", "input": 1},
        {"producer": "add_0", "consumer": "add_1", "input": 0},
        {"producer": "load_south", "consumer": "add_1", "input": 1},
        {"producer": "add_1", "consumer": "add_2", "input": 0},
        {"producer": "load_west", "consumer": "add_2", "input": 1},
        {"producer": "add_2", "consumer": "add_3", "input": 0},
        {"producer": "load_east", "consumer": "add_3", "input": 1},
        {"producer": "add_3", "consumer": "store_output", "input": 0},
    ]
    schedule = [
        {"cycle": 0, "nodes": ["load_center"]},
        {"cycle": 1, "nodes": ["load_north", "add_0"]},
        {"cycle": 2, "nodes": ["load_south", "add_1"]},
        {"cycle": 3, "nodes": ["load_west", "add_2"]},
        {"cycle": 4, "nodes": ["load_east", "add_3"]},
        {"cycle": 5, "nodes": ["store_output"]},
    ]
    return {
        "schema": SCHEMA,
        "compiler_identity": COMPILER_IDENTITY,
        "oracle_identity": ORACLE_IDENTITY,
        "target_signature": TARGET_SIGNATURE,
        "workload": {
            "name": "five-point-stencil-u32",
            "input_shape": [18, 18],
            "output_shape": [16, 16],
            "iteration": {"y": [1, 16], "x": [1, 16], "order": "row-major"},
            "arithmetic": "uint32-modulo-2^32",
        },
        "objects": [
            {
                "id": "A",
                "effect": "READ",
                "element_type": "uint32",
                "elements": 324,
                "bytes": 1296,
                "binding": "read-only",
                "requires_disjoint_from": ["B"],
            },
            {
                "id": "B",
                "effect": "WRITE",
                "element_type": "uint32",
                "elements": 256,
                "bytes": 1024,
                "binding": "exclusive-private-output",
                "publication": "host-after-independent-validation",
                "requires_disjoint_from": ["A"],
            },
        ],
        "nodes": nodes,
        "edges": edges,
        "schedule": schedule,
        "resources": {
            "integer_adders": 1,
            "scratchpad_read_ports": 1,
            "scratchpad_write_ports": 1,
            "runtime_ready_slots": 0,
        },
        "bounds": {
            "max_nodes": 64,
            "max_edges": 128,
            "active_invocations": 1,
            "installed_templates": 1,
            "cycles_per_output": 6,
            "outputs_per_invocation": 256,
            "max_cycles": 8192,
        },
        "fallback": {
            "isa": "RV64IM",
            "restart": "from-beginning",
            "unknown_alias": "reject-before-start",
        },
        "excluded": [
            "branch",
            "indirect-address",
            "atomics",
            "volatile",
            "mmio",
            "coherent-shared-write",
            "runtime-token-issue",
            "register-rename",
            "reorder-buffer",
            "general-lsu",
            "commit-frontier",
            "issue-mode-switching",
            "precise-mid-region-restart",
        ],
    }


def canonical_descriptor_bytes(descriptor: dict[str, Any]) -> bytes:
    validate_static_stencil_descriptor(descriptor)
    return json.dumps(
        descriptor,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def configuration_id(descriptor: dict[str, Any] | None = None) -> str:
    selected = descriptor if descriptor is not None else compile_static_stencil_descriptor()
    return hashlib.sha256(canonical_descriptor_bytes(selected)).hexdigest()


def validate_static_stencil_descriptor(descriptor: dict[str, Any]) -> None:
    """Recompute structural and effect invariants without trusting the compiler."""

    expected_top_level = {
        "schema",
        "compiler_identity",
        "oracle_identity",
        "target_signature",
        "workload",
        "objects",
        "nodes",
        "edges",
        "schedule",
        "resources",
        "bounds",
        "fallback",
        "excluded",
    }
    if set(descriptor) != expected_top_level:
        raise StaticRegionContractError("descriptor fields changed")

    if descriptor.get("schema") != SCHEMA:
        raise StaticRegionContractError("unsupported schema")
    if descriptor.get("target_signature") != TARGET_SIGNATURE:
        raise StaticRegionContractError("unsupported target")
    if descriptor.get("compiler_identity") != COMPILER_IDENTITY:
        raise StaticRegionContractError("unsupported compiler")
    if descriptor.get("oracle_identity") != ORACLE_IDENTITY:
        raise StaticRegionContractError("unsupported oracle")

    workload = descriptor.get("workload")
    expected_workload = {
        "name": "five-point-stencil-u32",
        "input_shape": [18, 18],
        "output_shape": [16, 16],
        "iteration": {"y": [1, 16], "x": [1, 16], "order": "row-major"},
        "arithmetic": "uint32-modulo-2^32",
    }
    if workload != expected_workload:
        raise StaticRegionContractError("workload is outside the accepted stencil")

    objects = descriptor.get("objects")
    if not isinstance(objects, list) or len(objects) != 2:
        raise StaticRegionContractError("exactly two objects are required")
    by_object = {item.get("id"): item for item in objects if isinstance(item, dict)}
    if set(by_object) != {"A", "B"}:
        raise StaticRegionContractError("object identities must be A and B")
    if (
        by_object["A"].get("effect") != "READ"
        or by_object["A"].get("element_type") != "uint32"
        or by_object["A"].get("elements") != 324
        or by_object["A"].get("bytes") != 1296
        or by_object["A"].get("binding") != "read-only"
    ):
        raise StaticRegionContractError("A must be the bounded read object")
    if (
        by_object["B"].get("effect") != "WRITE"
        or by_object["B"].get("element_type") != "uint32"
        or by_object["B"].get("elements") != 256
        or by_object["B"].get("bytes") != 1024
        or by_object["B"].get("publication") != "host-after-independent-validation"
    ):
        raise StaticRegionContractError("B must be the bounded write object")
    if by_object["A"].get("requires_disjoint_from") != ["B"]:
        raise StaticRegionContractError("A must require disjoint B")
    if by_object["B"].get("requires_disjoint_from") != ["A"]:
        raise StaticRegionContractError("B must require disjoint A")
    if by_object["B"].get("binding") != "exclusive-private-output":
        raise StaticRegionContractError("B must remain a private output")
    if set(by_object["A"]) != {
        "id",
        "effect",
        "element_type",
        "elements",
        "bytes",
        "binding",
        "requires_disjoint_from",
    }:
        raise StaticRegionContractError("A object fields changed")
    if set(by_object["B"]) != {
        "id",
        "effect",
        "element_type",
        "elements",
        "bytes",
        "binding",
        "publication",
        "requires_disjoint_from",
    }:
        raise StaticRegionContractError("B object fields changed")

    nodes = descriptor.get("nodes")
    edges = descriptor.get("edges")
    bounds = descriptor.get("bounds")
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(bounds, dict):
        raise StaticRegionContractError("nodes, edges, and bounds are required")
    if len(nodes) > bounds.get("max_nodes", -1) or len(nodes) != 10:
        raise StaticRegionContractError("node bound or exact graph shape failed")
    if len(edges) > bounds.get("max_edges", -1) or len(edges) != 9:
        raise StaticRegionContractError("edge bound or exact graph shape failed")

    by_node: dict[str, dict[str, Any]] = {}
    allowed_ops = {"LOAD_U32", "ADD_U32", "STORE_U32"}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise StaticRegionContractError("node identity is missing")
        node_id = node["id"]
        if node_id in by_node:
            raise StaticRegionContractError("duplicate node identity")
        if node.get("op") not in allowed_ops:
            raise StaticRegionContractError("unsupported operation")
        expected_node_fields = {"id", "op"}
        if node.get("op") in {"LOAD_U32", "STORE_U32"}:
            expected_node_fields.add("effect")
        if set(node) != expected_node_fields:
            raise StaticRegionContractError("node fields changed")
        by_node[node_id] = node

    indegree = {node_id: 0 for node_id in by_node}
    successors: dict[str, list[str]] = defaultdict(list)
    consumer_inputs: set[tuple[str, int]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise StaticRegionContractError("edge must be an object")
        if set(edge) != {"producer", "consumer", "input"}:
            raise StaticRegionContractError("edge fields changed")
        producer = edge.get("producer")
        consumer = edge.get("consumer")
        input_index = edge.get("input")
        if producer not in by_node or consumer not in by_node:
            raise StaticRegionContractError("edge endpoint is missing")
        if input_index not in {0, 1} or (consumer, input_index) in consumer_inputs:
            raise StaticRegionContractError("consumer input is invalid or multiply produced")
        consumer_inputs.add((consumer, input_index))
        successors[producer].append(consumer)
        indegree[consumer] += 1

    expected_edges = {
        ("load_center", "add_0", 0),
        ("load_north", "add_0", 1),
        ("add_0", "add_1", 0),
        ("load_south", "add_1", 1),
        ("add_1", "add_2", 0),
        ("load_west", "add_2", 1),
        ("add_2", "add_3", 0),
        ("load_east", "add_3", 1),
        ("add_3", "store_output", 0),
    }
    actual_edges = {
        (edge["producer"], edge["consumer"], edge["input"]) for edge in edges
    }
    if actual_edges != expected_edges:
        raise StaticRegionContractError("dependency graph changed")

    queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
    visited = 0
    while queue:
        current = queue.popleft()
        visited += 1
        for successor in successors[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    if visited != len(by_node):
        raise StaticRegionContractError("graph must be acyclic")

    load_nodes = [node for node in nodes if node.get("op") == "LOAD_U32"]
    store_nodes = [node for node in nodes if node.get("op") == "STORE_U32"]
    add_nodes = [node for node in nodes if node.get("op") == "ADD_U32"]
    if len(load_nodes) != 5 or len(add_nodes) != 4 or len(store_nodes) != 1:
        raise StaticRegionContractError("operation counts do not match the contract")
    if any(node.get("effect", {}).get("object") != "A" for node in load_nodes):
        raise StaticRegionContractError("all loads must read A")
    if store_nodes[0].get("effect", {}).get("object") != "B":
        raise StaticRegionContractError("the store must write B")
    expected_affine = {
        "load_center": "18*y+x",
        "load_north": "18*(y-1)+x",
        "load_south": "18*(y+1)+x",
        "load_west": "18*y+x-1",
        "load_east": "18*y+x+1",
        "store_output": "16*(y-1)+(x-1)",
    }
    for node_id, affine in expected_affine.items():
        expected_effect = {
            "kind": "WRITE" if node_id == "store_output" else "READ",
            "object": "B" if node_id == "store_output" else "A",
            "affine": affine,
        }
        if by_node[node_id].get("effect") != expected_effect:
            raise StaticRegionContractError("operation effect contract changed")

    schedule = descriptor.get("schedule")
    expected_schedule = [
        {"cycle": 0, "nodes": ["load_center"]},
        {"cycle": 1, "nodes": ["load_north", "add_0"]},
        {"cycle": 2, "nodes": ["load_south", "add_1"]},
        {"cycle": 3, "nodes": ["load_west", "add_2"]},
        {"cycle": 4, "nodes": ["load_east", "add_3"]},
        {"cycle": 5, "nodes": ["store_output"]},
    ]
    if schedule != expected_schedule:
        raise StaticRegionContractError("schedule must have six fixed cycles")
    scheduled = [node_id for item in schedule for node_id in item.get("nodes", [])]
    if len(scheduled) != len(set(scheduled)) or set(scheduled) != set(by_node):
        raise StaticRegionContractError("every node must be scheduled exactly once")
    node_cycle = {
        node_id: item["cycle"] for item in schedule for node_id in item.get("nodes", [])
    }
    for edge in edges:
        if node_cycle[edge["producer"]] > node_cycle[edge["consumer"]]:
            raise StaticRegionContractError("schedule violates a dependency")
    for item in schedule:
        cycle_nodes = [by_node[node_id] for node_id in item["nodes"]]
        if sum(node["op"] == "LOAD_U32" for node in cycle_nodes) > 1:
            raise StaticRegionContractError("schedule exceeds the read-port bound")
        if sum(node["op"] == "ADD_U32" for node in cycle_nodes) > 1:
            raise StaticRegionContractError("schedule exceeds the adder bound")
        if sum(node["op"] == "STORE_U32" for node in cycle_nodes) > 1:
            raise StaticRegionContractError("schedule exceeds the write-port bound")

    resources = descriptor.get("resources")
    if resources != {
        "integer_adders": 1,
        "scratchpad_read_ports": 1,
        "scratchpad_write_ports": 1,
        "runtime_ready_slots": 0,
    }:
        raise StaticRegionContractError("resource contract changed")
    if bounds != {
        "max_nodes": 64,
        "max_edges": 128,
        "active_invocations": 1,
        "installed_templates": 1,
        "cycles_per_output": 6,
        "outputs_per_invocation": 256,
        "max_cycles": 8192,
    }:
        raise StaticRegionContractError("bounds changed")
    if descriptor.get("fallback") != {
        "isa": "RV64IM",
        "restart": "from-beginning",
        "unknown_alias": "reject-before-start",
    }:
        raise StaticRegionContractError("fallback contract changed")

    excluded_items = descriptor.get("excluded")
    if not isinstance(excluded_items, list):
        raise StaticRegionContractError("exclusions must be a list")
    excluded = set(excluded_items)
    required_exclusions = {
        "branch",
        "indirect-address",
        "atomics",
        "volatile",
        "mmio",
        "coherent-shared-write",
        "runtime-token-issue",
        "register-rename",
        "reorder-buffer",
        "general-lsu",
        "commit-frontier",
        "issue-mode-switching",
        "precise-mid-region-restart",
    }
    if excluded != required_exclusions or len(excluded_items) != len(excluded):
        raise StaticRegionContractError("an ADR-0039 exclusion is missing")


def static_stencil_oracle(input_words: list[int]) -> list[int]:
    """Execute the exact uint32 stencil semantics independently of RTL."""

    if len(input_words) != 324:
        raise StaticRegionContractError("the oracle requires exactly 324 input words")
    words = [word & UINT32_MASK for word in input_words]
    output: list[int] = []
    for y in range(1, 17):
        for x in range(1, 17):
            center = 18 * y + x
            value = (
                words[center]
                + words[center - 18]
                + words[center + 18]
                + words[center - 1]
                + words[center + 1]
            ) & UINT32_MASK
            output.append(value)
    return output
