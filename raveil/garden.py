"""Read-only deterministic terminal browser for validated graph snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TextIO

from .graph_mvp import GraphCompiler, GraphNode, GraphProgram, GraphVariant


GARDEN_SCHEMA = "raveil.garden-snapshot/v1"
GARDEN_EVIDENCE_CLASS = "host-functional"
GARDEN_CLAIM_STATUS = "development-non-claim"
MAX_FIXTURE_BYTES = 64 * 1024
MAX_DEMO_COMMANDS = 8
MAX_NAVIGATION_STEPS = 64


def _require_exact_keys(value: dict[str, object], expected: set[str], kind: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{kind} fields do not match schema")


def _require_text(value: object, kind: str, *, maximum: int = 256) -> str:
    if type(value) is not str or not value or len(value) > maximum or any(
        character in value for character in "\r\n\x00"
    ):
        raise ValueError(f"{kind} must be bounded single-line text")
    return value


def _program_from_dict(value: object) -> GraphProgram:
    if type(value) is not dict:
        raise ValueError("garden program must be an object")
    _require_exact_keys(
        value,
        {"program_id", "family", "m", "n", "k", "nodes", "schema"},
        "garden program",
    )
    raw_nodes = value["nodes"]
    if type(raw_nodes) is not list or not raw_nodes:
        raise ValueError("garden program nodes must be a nonempty array")
    family = _require_text(value["family"], "garden program family")
    schema = _require_text(value["schema"], "garden program schema")
    dimensions: list[int] = []
    for name in ("m", "n", "k"):
        dimension = value[name]
        if type(dimension) is not int:
            raise ValueError(f"garden program {name} must be an integer")
        dimensions.append(dimension)
    nodes: list[GraphNode] = []
    for raw_node in raw_nodes:
        if type(raw_node) is not dict:
            raise ValueError("garden graph node must be an object")
        _require_exact_keys(raw_node, {"node_id", "op", "inputs", "output"}, "garden node")
        raw_inputs = raw_node["inputs"]
        if type(raw_inputs) is not list or any(type(item) is not str for item in raw_inputs):
            raise ValueError("garden node inputs must be a string array")
        nodes.append(
            GraphNode(
                _require_text(raw_node["node_id"], "garden node id"),
                _require_text(raw_node["op"], "garden node operation"),
                tuple(raw_inputs),
                _require_text(raw_node["output"], "garden node output"),
            )
        )
    return GraphProgram(
        _require_text(value["program_id"], "garden program id"),
        family,
        dimensions[0],
        dimensions[1],
        dimensions[2],
        tuple(nodes),
        schema,
    )


@dataclass(frozen=True)
class GardenEvidence:
    evidence_class: str
    claim_status: str
    statement: str

    @classmethod
    def from_dict(cls, value: object) -> "GardenEvidence":
        if type(value) is not dict:
            raise ValueError("garden evidence must be an object")
        _require_exact_keys(value, {"class", "claim_status", "statement"}, "garden evidence")
        evidence_class = _require_text(value["class"], "garden evidence class")
        claim_status = _require_text(value["claim_status"], "garden claim status")
        statement = _require_text(value["statement"], "garden evidence statement", maximum=512)
        if evidence_class != GARDEN_EVIDENCE_CLASS:
            raise ValueError("Garden S01 accepts host-functional evidence only")
        if claim_status != GARDEN_CLAIM_STATUS:
            raise ValueError("Garden S01 accepts development-non-claim snapshots only")
        return cls(evidence_class, claim_status, statement)


@dataclass(frozen=True)
class GardenSnapshot:
    title: str
    program: GraphProgram
    variants: tuple[GraphVariant, ...]
    evidence: GardenEvidence
    demo_commands: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> "GardenSnapshot":
        if not path.is_file():
            raise ValueError("garden fixture must be a regular file")
        if path.stat().st_size > MAX_FIXTURE_BYTES:
            raise ValueError("garden fixture exceeds the bounded size")
        raw = json.loads(path.read_text(encoding="utf-8"))
        if type(raw) is not dict:
            raise ValueError("garden snapshot must be an object")
        _require_exact_keys(
            raw,
            {"schema", "title", "program", "variants", "evidence", "demo_commands"},
            "garden snapshot",
        )
        if raw["schema"] != GARDEN_SCHEMA:
            raise ValueError("unsupported garden snapshot schema")
        program = _program_from_dict(raw["program"])
        raw_variants = raw["variants"]
        if type(raw_variants) is not list or not raw_variants:
            raise ValueError("garden variants must be a nonempty array")
        if any(type(item) is not dict for item in raw_variants):
            raise ValueError("garden variants must contain objects")
        variants = tuple(GraphVariant.from_dict(item) for item in raw_variants)
        canonical_variants = GraphCompiler().compile(program)
        if variants != canonical_variants:
            raise ValueError("garden variants do not match the canonical compiler slate")
        raw_commands = raw["demo_commands"]
        if type(raw_commands) is not list or not 1 <= len(raw_commands) <= MAX_DEMO_COMMANDS:
            raise ValueError("garden demo commands must be a bounded nonempty array")
        commands = tuple(
            _require_text(command, "garden demo command", maximum=512)
            for command in raw_commands
        )
        if any(not command.startswith("python3 -m raveil ") for command in commands):
            raise ValueError("garden demo commands must use the Raveil module CLI")
        return cls(
            _require_text(raw["title"], "garden title"),
            program,
            variants,
            GardenEvidence.from_dict(raw["evidence"]),
            commands,
        )


class GardenBrowser:
    """Bounded navigation state with no graph execution or mutation authority."""

    def __init__(self, snapshot: GardenSnapshot) -> None:
        self.snapshot = snapshot
        self.selected = 0

    def navigate(self, key: str) -> bool:
        if key == "q":
            return False
        if key == "j":
            self.selected = min(self.selected + 1, len(self.snapshot.program.nodes) - 1)
        elif key == "k":
            self.selected = max(self.selected - 1, 0)
        elif key == "g":
            self.selected = 0
        elif key == "G":
            self.selected = len(self.snapshot.program.nodes) - 1
        else:
            raise ValueError("garden navigation accepts only j, k, g, G, or q")
        return True

    def _node_dependencies(self, node: GraphNode) -> tuple[tuple[str, ...], tuple[str, ...]]:
        producers = {item.output: item.node_id for item in self.snapshot.program.nodes}
        dependencies = tuple(producers[item] for item in node.inputs if item in producers)
        external_inputs = tuple(item for item in node.inputs if item not in producers)
        return dependencies, external_inputs

    def render(self) -> str:
        program = self.snapshot.program
        selected = program.nodes[self.selected]
        dependencies, external_inputs = self._node_dependencies(selected)
        lines = [
            "Raveil Garden | read-only graph browser",
            f"snapshot: {self.snapshot.title}",
            f"program: {program.program_id} sha256={program.identity}",
            f"shape: m={program.m} n={program.n} k={program.k} family={program.family}",
            (
                f"evidence: {self.snapshot.evidence.evidence_class} "
                f"claim={self.snapshot.evidence.claim_status}"
            ),
            "authority: observe-only execute=no mutate=no approve=no promote=no",
            "",
            f"Nodes ({len(program.nodes)})",
        ]
        for index, node in enumerate(program.nodes):
            marker = ">" if index == self.selected else " "
            node_dependencies, node_external = self._node_dependencies(node)
            relation = ",".join(node_dependencies) or "root"
            external = ",".join(node_external) or "-"
            lines.append(
                f"{marker} {index + 1}. {node.node_id} op={node.op} "
                f"depends={relation} external={external} output={node.output}"
            )
        lines.extend((
            "",
            f"Selected: {selected.node_id}",
            f"  dependencies: {','.join(dependencies) or 'root'}",
            f"  external-inputs: {','.join(external_inputs) or '-'}",
            f"  output: {selected.output}",
            "",
            f"Variants ({len(self.snapshot.variants)})",
        ))
        for variant in self.snapshot.variants:
            baseline = " baseline" if variant.candidate.trusted_baseline else ""
            lines.append(
                f"  - {variant.variant_id}{baseline}; transforms={'+'.join(variant.transforms)}; "
                f"memory={variant.memory_plan.materialization}:"
                f"{variant.memory_plan.maximum_intermediate_bytes}B"
            )
        lines.extend(("", "Demo commands"))
        lines.extend(f"  $ {command}" for command in self.snapshot.demo_commands)
        lines.extend(("", "Navigation: j next | k previous | g first | G last | q quit"))
        return "\n".join(lines)


def render_empty() -> str:
    return "\n".join((
        "Raveil Garden | empty",
        "No validated graph snapshot is loaded.",
        "authority: observe-only execute=no mutate=no approve=no promote=no",
    ))


def render_error(message: str) -> str:
    bounded = " ".join(message.split())[:512]
    return "\n".join((
        "Raveil Garden | error",
        bounded or "unknown snapshot error",
        "No graph state was accepted.",
    ))


def render_key_session(snapshot: GardenSnapshot, keys: str) -> str:
    if len(keys) > MAX_NAVIGATION_STEPS:
        raise ValueError("garden navigation exceeds the bounded step limit")
    browser = GardenBrowser(snapshot)
    screens = [browser.render()]
    for key in keys:
        if not browser.navigate(key):
            screens.append("Raveil Garden | closed")
            break
        screens.append(browser.render())
    return "\n\n---\n\n".join(screens)


def run_interactive(snapshot: GardenSnapshot, input_stream: TextIO, output_stream: TextIO) -> int:
    browser = GardenBrowser(snapshot)
    output_stream.write(browser.render() + "\n")
    if not input_stream.isatty():
        return 0
    for _ in range(MAX_NAVIGATION_STEPS):
        output_stream.write("garden> ")
        output_stream.flush()
        line = input_stream.readline()
        if not line:
            return 0
        key = line.strip()
        try:
            if not browser.navigate(key):
                output_stream.write("Raveil Garden | closed\n")
                return 0
        except ValueError as error:
            output_stream.write(render_error(str(error)) + "\n")
            continue
        output_stream.write(browser.render() + "\n")
    output_stream.write(render_error("garden navigation reached the bounded step limit") + "\n")
    return 2
