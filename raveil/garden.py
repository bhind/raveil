"""Read-only deterministic terminal browser for validated graph snapshots."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import textwrap
from types import MappingProxyType
from typing import Mapping, TextIO

from .graph_mvp import GraphCompiler, GraphNode, GraphProgram, GraphVariant


GARDEN_SCHEMA = "raveil.garden-snapshot/v1"
DYNAMIC_EXPLANATION_SCHEMA = "raveil.garden-dynamic-explanation/v1"
LOWERING_TRACE_SCHEMA = "raveil.graph-device-lowering-trace/v1"
GARDEN_EVIDENCE_CLASS = "host-functional"
GARDEN_CLAIM_STATUS = "development-non-claim"
MAX_FIXTURE_BYTES = 64 * 1024
MAX_DEMO_COMMANDS = 8
MAX_NAVIGATION_STEPS = 64
DEFAULT_RENDER_WIDTH = 150
MIN_RENDER_WIDTH = 72
MAX_RENDER_WIDTH = 240
FUSION_TRANSFORM = "fuse:bias_add+relu"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,30}$")
DYNAMIC_OPCODES = {"LOAD_U32": 1, "ADD_U32": 2, "STORE_U32": 3, "MAX_U32": 4}
DYNAMIC_SELECTORS = {"center": 0, "north": 1, "south": 2, "west": 3, "east": 4}
DYNAMIC_MAGIC = 0x52504731
DYNAMIC_PAYLOAD_WORDS = 32
DYNAMIC_INSTRUCTION_CAPACITY = 16
DYNAMIC_VALUE_REGISTERS = 8
DYNAMIC_DEMO_COMMAND = (
    "python3 -m raveil garden --fixture "
    "tests/fixtures/garden/dynamic-explanation.json --keys 'jjq'"
)
DYNAMIC_FIXTURE_ROOT = ("tests", "fixtures", "garden")


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_dynamic_document(relative: str) -> dict[str, object]:
    """Read one normalized repository file through no-follow directory fds."""
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if type(no_follow) is not int or no_follow == 0 \
            or type(directory) is not int or directory == 0:
        raise ValueError(
            "dynamic explanation loading requires O_NOFOLLOW and O_DIRECTORY"
        )
    if type(relative) is not str or not relative:
        raise ValueError("dynamic explanation path must be normalized repository-relative text")
    lexical = Path(relative)
    if lexical.is_absolute() or lexical.as_posix() != relative \
            or any(part in {"", ".", ".."} for part in lexical.parts) \
            or lexical.parts[:len(DYNAMIC_FIXTURE_ROOT)] != DYNAMIC_FIXTURE_ROOT \
            or len(lexical.parts) != len(DYNAMIC_FIXTURE_ROOT) + 1:
        raise ValueError("dynamic explanation path must be normalized repository-relative text")
    root = _repository_root()
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | no_follow
    directory_flags = flags | directory
    opened: list[int] = []
    try:
        current = os.open(root, directory_flags)
        opened.append(current)
        for component in lexical.parts[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            opened.append(current)
        leaf = os.open(
            lexical.parts[-1], flags | getattr(os, "O_NONBLOCK", 0), dir_fd=current,
        )
        opened.append(leaf)
        before = os.fstat(leaf)
        identity = (
            before.st_dev, before.st_ino, before.st_mode, before.st_nlink,
            before.st_size, before.st_mtime_ns, before.st_ctime_ns,
        )
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("dynamic explanation fixture must be a single-link regular file")
        if not 0 < before.st_size <= MAX_FIXTURE_BYTES:
            raise ValueError("dynamic explanation fixture size is outside the bound")
        payload = b""
        while len(payload) <= before.st_size:
            chunk = os.read(leaf, min(8192, before.st_size + 1 - len(payload)))
            if not chunk:
                break
            payload += chunk
        after = os.fstat(leaf)
        after_identity = (
            after.st_dev, after.st_ino, after.st_mode, after.st_nlink,
            after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        )
        named_after = os.stat(
            lexical.parts[-1], dir_fd=current, follow_symlinks=False,
        )
        named_identity = (
            named_after.st_dev, named_after.st_ino, named_after.st_mode,
            named_after.st_nlink, named_after.st_size, named_after.st_mtime_ns,
            named_after.st_ctime_ns,
        )
        if identity != after_identity or identity != named_identity \
                or len(payload) != before.st_size:
            raise ValueError("dynamic explanation fixture changed while read")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"dynamic explanation fixture cannot be read safely: {error}") from error
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)
    try:
        value = json.loads(
            payload.decode("ascii"), object_pairs_hook=_reject_duplicate_object_pairs,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"dynamic explanation JSON is invalid: {error}") from error
    if type(value) is not dict:
        raise ValueError("dynamic explanation must be an object")
    return value


def validate_render_width(width: int) -> int:
    """Return a supported explicit display width without consulting a terminal."""
    if type(width) is not int or not MIN_RENDER_WIDTH <= width <= MAX_RENDER_WIDTH:
        raise ValueError(
            f"garden width must be an integer from {MIN_RENDER_WIDTH} to {MAX_RENDER_WIDTH}"
        )
    return width


def _wrapped_lines(items: list[str], width: int) -> list[str]:
    lines: list[str] = []
    for item in items:
        lines.extend(textwrap.wrap(
            item, width=width, break_long_words=True, break_on_hyphens=False,
        ) or [""])
    return lines


def _pane(title: str, items: list[str], width: int) -> list[str]:
    interior = width - 2
    heading = f"[ {title} ]"
    top = "+" + heading[:interior].ljust(interior, "-") + "+"
    body = ["|" + line.ljust(interior) + "|" for line in _wrapped_lines(items, interior)]
    return [top, *body, "+" + "-" * interior + "+"]


def _join_panes(panes: list[list[str]]) -> list[str]:
    body_height = max(len(pane) - 2 for pane in panes)
    aligned: list[list[str]] = []
    for pane in panes:
        blank_body = "|" + " " * (len(pane[0]) - 2) + "|"
        aligned.append([
            pane[0],
            *pane[1:-1],
            *[blank_body] * (body_height - len(pane) + 2),
            pane[-1],
        ])
    return [" ".join(pane[index] for pane in aligned) for index in range(body_height + 2)]


def _reject_duplicate_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"garden JSON contains duplicate field: {key}")
        result[key] = value
    return result


def _require_exact_keys(value: dict[str, object], expected: set[str], kind: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{kind} fields do not match schema")


def _require_text(value: object, kind: str, *, maximum: int = 256) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > maximum
        or not value.isprintable()
    ):
        raise ValueError(f"{kind} must be bounded printable single-line text")
    return value


def _require_identifier(value: object, kind: str) -> str:
    text = _require_text(value, kind, maximum=31)
    if text.isascii() is False or IDENTIFIER_RE.fullmatch(text) is None:
        raise ValueError(f"{kind} must be a bounded ASCII identifier")
    return text


def _require_sha256(value: object, kind: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{kind} must be a lowercase SHA-256 identity")
    return value


def _require_integer(
    value: object, kind: str, *, minimum: int = 0, maximum: int = 0xFFFFFFFF,
) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{kind} must be an integer from {minimum} to {maximum}")
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
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_object_pairs,
        )
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


@dataclass(frozen=True)
class DynamicLoweringInstruction:
    index: int
    node_id: str
    op: str
    dependencies: tuple[str, ...]
    selector: str | None
    fan_out: int
    consumers: tuple[str, ...]
    encoded_word: int
    source_registers: tuple[int, ...]
    destination_register: int | None
    definition_index: int | None
    last_use_index: int | None
    live_range: tuple[int, int] | None
    release_after_index: int | None


@dataclass(frozen=True)
class GardenDynamicExplanation:
    """Validated projection of retained evidence and compiler-owned lowering."""

    title: str
    graph_id: str
    program_version: int
    program_sha256: str
    lowering_trace_sha256: str
    instructions: tuple[DynamicLoweringInstruction, ...]
    affine: Mapping[str, object]
    identities: Mapping[str, str]
    agreement: Mapping[str, object]
    evidence: Mapping[str, str]
    retained_evidence_sha256: str
    performance: str
    polls: Mapping[str, object]
    demo_commands: tuple[str, ...]

    @classmethod
    def load(cls, relative: str) -> "GardenDynamicExplanation":
        return cls.from_dict(_read_dynamic_document(relative))

    @classmethod
    def from_dict(cls, raw: object) -> "GardenDynamicExplanation":
        if type(raw) is not dict:
            raise ValueError("dynamic explanation must be an object")
        _require_exact_keys(
            raw,
            {
                "schema", "title", "lowering", "program_payload", "affine",
                "identities", "agreement", "evidence", "performance", "polls",
                "lowering_trace_sha256", "retained_evidence_sha256", "demo_commands",
            },
            "dynamic explanation",
        )
        if raw["schema"] != DYNAMIC_EXPLANATION_SCHEMA:
            raise ValueError("unsupported dynamic explanation schema")
        lowering = raw["lowering"]
        if type(lowering) is not dict:
            raise ValueError("dynamic lowering trace must be an object")
        _require_exact_keys(
            lowering,
            {
                "schema", "graph_id", "descriptor_canonical_sha256",
                "program_version", "instruction_count", "program_sha256",
                "instructions",
            },
            "dynamic lowering trace",
        )
        if lowering["schema"] != LOWERING_TRACE_SCHEMA:
            raise ValueError("unsupported dynamic lowering trace schema")
        lowering_trace_sha256 = _require_sha256(
            raw["lowering_trace_sha256"], "dynamic lowering trace identity",
        )
        calculated_lowering_trace = hashlib.sha256(json.dumps(
            lowering, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")).hexdigest()
        if lowering_trace_sha256 != calculated_lowering_trace:
            raise ValueError("dynamic lowering trace digest is invalid")
        graph_id = _require_identifier(lowering["graph_id"], "dynamic graph id")
        descriptor_canonical = _require_sha256(
            lowering["descriptor_canonical_sha256"], "canonical descriptor identity",
        )
        version = _require_integer(
            lowering["program_version"], "dynamic program version", minimum=1, maximum=2,
        )
        count = _require_integer(
            lowering["instruction_count"], "dynamic instruction count",
            minimum=2, maximum=DYNAMIC_INSTRUCTION_CAPACITY,
        )
        program_sha256 = _require_sha256(
            lowering["program_sha256"], "dynamic program identity",
        )
        payload = raw["program_payload"]
        if type(payload) is not list or len(payload) != DYNAMIC_PAYLOAD_WORDS \
                or any(type(word) is not int or not 0 <= word <= 0xFFFFFFFF for word in payload):
            raise ValueError("dynamic program payload must contain exactly 32 u32 words")
        words = payload[12:12 + count]
        calculated_program = hashlib.sha256(
            struct.pack(f"<{count + 1}I", count, *words)
        ).hexdigest()
        digest_words = list(struct.unpack("<8I", bytes.fromhex(calculated_program)))
        if payload[:4] != [DYNAMIC_MAGIC, version, count, DYNAMIC_VALUE_REGISTERS] \
                or payload[4:12] != digest_words \
                or any(payload[12 + count:28]) or any(payload[28:32]) \
                or calculated_program != program_sha256:
            raise ValueError("dynamic program payload framing or digest is invalid")
        raw_entries = lowering["instructions"]
        if type(raw_entries) is not list or len(raw_entries) != count:
            raise ValueError("dynamic lowering instruction count does not match payload")
        entry_keys = {
            "index", "node_id", "op", "dependencies", "selector", "fan_out", "consumers",
            "encoded_word", "source_registers", "destination_register",
            "definition_index", "last_use_index", "live_range", "release_after_index",
        }
        parsed: list[DynamicLoweringInstruction] = []
        known_ids: set[str] = set()
        allocations: dict[str, int] = {}
        stores = 0
        for index, value in enumerate(raw_entries):
            if type(value) is not dict:
                raise ValueError("dynamic lowering instruction must be an object")
            _require_exact_keys(value, entry_keys, "dynamic lowering instruction")
            node_id = _require_identifier(value["node_id"], "dynamic node id")
            if node_id in known_ids:
                raise ValueError("dynamic node identifiers must be unique")
            op = _require_text(value["op"], "dynamic opcode", maximum=16)
            if op not in DYNAMIC_OPCODES:
                raise ValueError("dynamic opcode is unsupported")
            if version == 1 and op == "MAX_U32":
                raise ValueError("MAX_U32 requires dynamic program version 2")
            dependencies_value = value["dependencies"]
            if type(dependencies_value) is not list \
                    or any(type(item) is not str for item in dependencies_value):
                raise ValueError("dynamic dependencies must be an identifier array")
            dependencies = tuple(
                _require_identifier(item, "dynamic dependency")
                for item in dependencies_value
            )
            if any(item not in known_ids for item in dependencies):
                raise ValueError("dynamic dependencies must precede their consumer")
            selector_value = value["selector"]
            selector = None if selector_value is None else _require_text(
                selector_value, "dynamic address selector", maximum=16,
            )
            if op == "LOAD_U32":
                if dependencies or selector not in DYNAMIC_SELECTORS:
                    raise ValueError("dynamic LOAD_U32 topology is invalid")
            elif op in {"ADD_U32", "MAX_U32"}:
                if len(dependencies) != 2 or selector is not None:
                    raise ValueError("dynamic binary operation topology is invalid")
            else:
                stores += 1
                if len(dependencies) != 1 or selector is not None or index != count - 1:
                    raise ValueError("dynamic STORE_U32 must be the one final instruction")
            source_registers_value = value["source_registers"]
            if type(source_registers_value) is not list \
                    or any(type(item) is not int or not 0 <= item < DYNAMIC_VALUE_REGISTERS
                           for item in source_registers_value):
                raise ValueError("dynamic source registers are invalid")
            source_registers = tuple(source_registers_value)
            if source_registers != tuple(allocations[item] for item in dependencies):
                raise ValueError("dynamic source registers do not match dependency values")
            destination_value = value["destination_register"]
            destination = None if destination_value is None else _require_integer(
                destination_value, "dynamic destination register",
                maximum=DYNAMIC_VALUE_REGISTERS - 1,
            )
            word = _require_integer(value["encoded_word"], "dynamic encoded word")
            if word != words[index] or _require_integer(
                value["index"], "dynamic program-order index", maximum=count - 1,
            ) != index:
                raise ValueError("dynamic lowering word or program-order index is invalid")
            if op == "LOAD_U32":
                expected_word = (
                    (DYNAMIC_OPCODES[op] << 28) | (destination << 25)
                    | (DYNAMIC_SELECTORS[selector] << 22)
                ) if destination is not None else -1
            elif op in {"ADD_U32", "MAX_U32"}:
                expected_word = (
                    (DYNAMIC_OPCODES[op] << 28) | (destination << 25)
                    | (source_registers[0] << 22) | (source_registers[1] << 19)
                ) if destination is not None and len(source_registers) == 2 else -1
            else:
                expected_word = (
                    (DYNAMIC_OPCODES[op] << 28) | (source_registers[0] << 25)
                ) if destination is None and len(source_registers) == 1 else -1
            if word != expected_word:
                raise ValueError("dynamic opcode/register relation does not match encoded word")
            definition = value["definition_index"]
            if definition is not None:
                definition = _require_integer(
                    definition, "dynamic definition index", maximum=count - 1,
                )
            last_use = value["last_use_index"]
            if last_use is not None:
                last_use = _require_integer(
                    last_use, "dynamic last-use index", maximum=count - 1,
                )
            release = value["release_after_index"]
            if release is not None:
                release = _require_integer(
                    release, "dynamic release index", maximum=count - 1,
                )
            live_range_value = value["live_range"]
            if live_range_value is None:
                live_range = None
            elif type(live_range_value) is list and len(live_range_value) == 2:
                live_range = tuple(
                    _require_integer(item, "dynamic live-range index", maximum=count - 1)
                    for item in live_range_value
                )
            else:
                raise ValueError("dynamic live range must be two program-order indices or null")
            fan_out = _require_integer(
                value["fan_out"], "dynamic fan-out", maximum=count,
            )
            consumers_value = value["consumers"]
            if type(consumers_value) is not list:
                raise ValueError("dynamic consumers must be an identifier array")
            consumers = tuple(
                _require_identifier(item, "dynamic consumer") for item in consumers_value
            )
            if op == "STORE_U32":
                if any(value[field] is not None for field in (
                    "destination_register", "definition_index", "last_use_index",
                    "live_range", "release_after_index",
                )) or fan_out != 0 or consumers:
                    raise ValueError("dynamic store must not define a value lifetime")
            else:
                if definition != index or destination is None:
                    raise ValueError("dynamic definition position or register is invalid")
                allocations[node_id] = destination
            parsed.append(DynamicLoweringInstruction(
                index, node_id, op, dependencies, selector,
                fan_out, consumers, word, source_registers, destination, definition,
                last_use, live_range, release,
            ))
            known_ids.add(node_id)
        if stores != 1:
            raise ValueError("dynamic explanation requires exactly one final store")
        if (version == 2) != any(item.op == "MAX_U32" for item in parsed):
            raise ValueError("dynamic program version does not match its opcode set")
        use_positions: dict[str, list[int]] = {item.node_id: [] for item in parsed}
        for item in parsed:
            for dependency in item.dependencies:
                use_positions[dependency].append(item.index)
        for item in parsed:
            if item.op == "STORE_U32":
                continue
            positions = use_positions[item.node_id]
            consumers = tuple(parsed[index].node_id for index in positions)
            last_use = max(positions) if positions else None
            live_end = last_use if last_use is not None else count - 1
            if item.fan_out != len(positions) or item.consumers != consumers \
                    or item.last_use_index != last_use \
                    or item.live_range != (item.index, live_end) \
                    or item.release_after_index != last_use:
                raise ValueError("dynamic fan-out, lifetime, or release relation is invalid")
            for other in parsed:
                if other.index >= item.index:
                    break
                if other.destination_register == item.destination_register \
                        and other.live_range is not None \
                        and other.live_range[1] > item.index:
                    raise ValueError("dynamic value register lifetimes overlap")
        affine = raw["affine"]
        if type(affine) is not dict:
            raise ValueError("dynamic affine profile must be an object")
        affine_keys = {
            "profile", "rows", "columns", "input_stride", "output_stride",
            "active_outputs", "transactions_per_output", "configuration_sha256",
        }
        _require_exact_keys(affine, affine_keys, "dynamic affine profile")
        profile_name = _require_text(affine["profile"], "dynamic affine profile name", maximum=16)
        profile_shapes = {
            "baseline": (16, 16, 18, 16),
            "compact": (8, 8, 10, 8),
        }
        affine_shape = tuple(
            _require_integer(affine[name], f"dynamic affine {name}", minimum=1, maximum=324)
            for name in ("rows", "columns", "input_stride", "output_stride")
        )
        if profile_name not in profile_shapes or affine_shape != profile_shapes[profile_name]:
            raise ValueError("dynamic affine profile shape is unsupported")
        active_outputs = _require_integer(
            affine["active_outputs"], "dynamic affine active outputs", minimum=1, maximum=256,
        )
        transactions_per_output = _require_integer(
            affine["transactions_per_output"], "dynamic affine transactions per output",
            minimum=1, maximum=DYNAMIC_INSTRUCTION_CAPACITY + 1,
        )
        if active_outputs != affine["rows"] * affine["columns"] \
                or transactions_per_output != (
                    sum(item.op == "LOAD_U32" for item in parsed) + 1
                ):
            raise ValueError("dynamic affine counts do not match the program")
        _require_sha256(affine["configuration_sha256"], "dynamic affine identity")
        identities = raw["identities"]
        identity_keys = {
            "descriptor_sha256", "descriptor_canonical_sha256", "program_sha256",
            "request_sha256", "compiler_source_sha256", "source_manifest_sha256",
            "abi_sha256", "rtl_sha256", "toolchain_sha256", "simulator_sha256",
            "axi_trace_sha256",
        }
        if type(identities) is not dict:
            raise ValueError("dynamic identities must be an object")
        _require_exact_keys(identities, identity_keys, "dynamic identities")
        checked_identities = {
            name: _require_sha256(identities[name], f"dynamic {name}")
            for name in sorted(identity_keys)
        }
        if checked_identities["descriptor_canonical_sha256"] != descriptor_canonical \
                or checked_identities["program_sha256"] != program_sha256:
            raise ValueError("dynamic retained identities do not bind the lowering trace")
        agreement = raw["agreement"]
        if type(agreement) is not dict:
            raise ValueError("dynamic agreement must be an object")
        _require_exact_keys(
            agreement,
            {"status", "oracle_sha256", "fallback_sha256", "rtl_output_sha256"},
            "dynamic agreement",
        )
        agreement_hashes = tuple(
            _require_sha256(agreement[name], f"dynamic {name}")
            for name in ("oracle_sha256", "fallback_sha256", "rtl_output_sha256")
        )
        if agreement["status"] != "exact-match" or len(set(agreement_hashes)) != 1:
            raise ValueError("dynamic oracle/fallback/RTL agreement is not exact")
        evidence = raw["evidence"]
        expected_evidence = {
            "garden_class": "host-functional",
            "retained_execution_class": "rtl-simulation-functional",
            "claim_status": "presentation-only",
        }
        if evidence != expected_evidence:
            raise ValueError("dynamic evidence labels must separate Garden from retained RTL")
        if raw["performance"] != "not-measured":
            raise ValueError("dynamic Garden performance must remain not-measured")
        polls = raw["polls"]
        expected_polls = {
            "label": "polls=",
            "classification": "termination-diagnostic",
            "is_cycle_measurement": False,
        }
        if polls != expected_polls:
            raise ValueError("polls= must remain a termination diagnostic, not cycles")
        retained_evidence_sha256 = _require_sha256(
            raw["retained_evidence_sha256"], "retained evidence manifest identity",
        )
        retained_manifest = {
            "affine": affine,
            "agreement": agreement,
            "evidence": evidence,
            "identities": identities,
            "performance": raw["performance"],
            "polls": polls,
        }
        calculated_retained = hashlib.sha256(json.dumps(
            retained_manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")).hexdigest()
        if retained_evidence_sha256 != calculated_retained:
            raise ValueError("retained evidence manifest digest is invalid")
        commands = raw["demo_commands"]
        if commands != [DYNAMIC_DEMO_COMMAND]:
            raise ValueError("dynamic explanation permits only the fixed Garden demo command")
        return cls(
            _require_text(raw["title"], "dynamic explanation title"),
            graph_id, version, program_sha256, lowering_trace_sha256,
            tuple(parsed), MappingProxyType(dict(affine)),
            MappingProxyType(checked_identities), MappingProxyType(dict(agreement)),
            MappingProxyType(dict(evidence)), retained_evidence_sha256,
            raw["performance"], MappingProxyType(dict(polls)), tuple(commands),
        )


def _materialized_fused_plan_pair(
    variants: tuple[GraphVariant, ...],
) -> tuple[GraphVariant, GraphVariant] | None:
    """Return the first validated materialized/fused comparison, if present."""
    pairs: list[tuple[GraphVariant, GraphVariant]] = []
    for fused in variants:
        if (
            fused.memory_plan.materialization != "fused"
            or FUSION_TRANSFORM not in fused.transforms
        ):
            continue
        unfused_transforms = tuple(
            transform for transform in fused.transforms if transform != FUSION_TRANSFORM
        )
        for materialized in variants:
            if (
                materialized.memory_plan.materialization == "materialized"
                and materialized.candidate.loop_order == fused.candidate.loop_order
                and materialized.candidate.tile == fused.candidate.tile
                and materialized.program_sha256 == fused.program_sha256
                and materialized.contract_sha256 == fused.contract_sha256
                and materialized.transforms == unfused_transforms
            ):
                pairs.append((materialized, fused))
    if not pairs:
        return None
    return min(
        pairs,
        key=lambda pair: (
            pair[0].candidate.cold_priority,
            pair[1].candidate.cold_priority,
            pair[0].variant_id,
            pair[1].variant_id,
        ),
    )


class GardenBrowser:
    """Bounded navigation state with no graph execution or mutation authority."""

    def __init__(self, snapshot: GardenSnapshot, width: int = DEFAULT_RENDER_WIDTH) -> None:
        self.snapshot = snapshot
        self.width = validate_render_width(width)
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
        header = _wrapped_lines([
            "Raveil Garden | read-only graph browser",
            f"snapshot: {self.snapshot.title}",
            f"program: {program.program_id} sha256={program.identity}",
            f"shape: m={program.m} n={program.n} k={program.k} family={program.family}",
            (
                f"evidence: {self.snapshot.evidence.evidence_class} "
                f"claim={self.snapshot.evidence.claim_status}"
            ),
            "authority: observe-only execute=no mutate=no approve=no promote=no",
        ], self.width)
        navigator = [f"nodes: {len(program.nodes)}"]
        for index, node in enumerate(program.nodes):
            marker = ">" if index == self.selected else " "
            node_dependencies, node_external = self._node_dependencies(node)
            relation = ",".join(node_dependencies) or "root"
            external = ",".join(node_external) or "-"
            navigator.append(
                f"{marker} {index + 1}. {node.node_id} op={node.op} "
                f"depends={relation} external={external} output={node.output}"
            )
        inspector = [
            f"id: {selected.node_id}",
            f"op: {selected.op}",
            f"dependencies: {','.join(dependencies) or 'root'}",
            f"external inputs: {','.join(external_inputs) or '-'}",
            f"output: {selected.output}",
        ]
        variants = [
            f"evidence class: {self.snapshot.evidence.evidence_class}",
            f"non-claim status: {self.snapshot.evidence.claim_status}",
            f"evidence: {self.snapshot.evidence.statement}",
            f"selected node: {selected.node_id}; variants: {len(self.snapshot.variants)}",
        ]
        comparison = _materialized_fused_plan_pair(self.snapshot.variants)
        if comparison is not None:
            materialized, fused = comparison
            variants.extend([
                (
                    "Matched plan pair: "
                    f"{materialized.variant_id} vs {fused.variant_id} "
                    "(deterministic comparison; not a measured best-plan selection)"
                ),
                (
                    "semantic graph: unchanged; program sha256="
                    f"{materialized.program_sha256}"
                ),
                (
                    "result contract: unchanged; contract sha256="
                    f"{materialized.contract_sha256}"
                ),
                (
                    f"materialized [{materialized.variant_id}]: matmul -> bias_add -> "
                    "intermediate["
                    f"{materialized.memory_plan.maximum_intermediate_bytes}B] -> relu -> output"
                ),
                (
                    f"fused [{fused.variant_id}]: matmul -> bias_add + relu -> output; "
                    "intermediate["
                    f"{fused.memory_plan.maximum_intermediate_bytes}B]"
                ),
                (
                    "scope: intermediate buffer only; not total Graph memory "
                    f"({materialized.memory_plan.maximum_intermediate_bytes}B vs "
                    f"{fused.memory_plan.maximum_intermediate_bytes}B)"
                ),
            ])
        for variant in self.snapshot.variants:
            baseline = " baseline" if variant.candidate.trusted_baseline else ""
            variants.append(
                f"{variant.variant_id}{baseline}; transforms={'+'.join(variant.transforms)}; "
                f"memory={variant.memory_plan.materialization}:"
                f"{variant.memory_plan.maximum_intermediate_bytes}B"
            )
        panes = [
            _pane("Graph Navigator", navigator, self.width if self.width < 120 else (self.width - 2) // 3),
            _pane("Node Inspector", inspector, self.width if self.width < 120 else (self.width - 2) // 3),
            _pane("Variants / Evidence", variants, self.width if self.width < 120 else (self.width - 2) // 3),
        ]
        if self.width < 120:
            body = ["[stacked layout]"]
            for pane in panes:
                body.extend(pane)
        else:
            body = _join_panes(panes)
        footer = _wrapped_lines([
            "Commands / Status",
            "Navigation: j next | k previous | g first | G last | q quit",
            "authority: read-only; no graph execution, mutation, approval, or promotion.",
            *[f"demo: {command}" for command in self.snapshot.demo_commands],
        ], self.width)
        return "\n".join([*header, "", *body, "", *footer])


class GardenDynamicBrowser:
    """Read-only terminal projection of an already validated explanation."""

    def __init__(
        self, explanation: GardenDynamicExplanation,
        width: int = DEFAULT_RENDER_WIDTH,
    ) -> None:
        self.explanation = explanation
        self.width = validate_render_width(width)
        self.selected = 0

    def navigate(self, key: str) -> bool:
        if key == "q":
            return False
        if key == "j":
            self.selected = min(
                self.selected + 1, len(self.explanation.instructions) - 1,
            )
        elif key == "k":
            self.selected = max(self.selected - 1, 0)
        elif key == "g":
            self.selected = 0
        elif key == "G":
            self.selected = len(self.explanation.instructions) - 1
        else:
            raise ValueError("garden navigation accepts only j, k, g, G, or q")
        return True

    def render(self) -> str:
        explanation = self.explanation
        selected = explanation.instructions[self.selected]
        header = _wrapped_lines([
            "Raveil Garden | read-only dynamic execution explanation",
            f"explanation: {explanation.title}",
            f"graph: {explanation.graph_id}",
            (
                f"program: version={explanation.program_version} "
                f"sha256={explanation.program_sha256}"
            ),
            f"compiler-owned lowering trace sha256={explanation.lowering_trace_sha256}",
            (
                "evidence: Garden=host-functional presentation-only; "
                "retained execution reference=rtl-simulation-functional"
            ),
            "positions: all definition/use/lifetime/release positions are zero-based program-order indices",
            "authority: observe-only execute=no mutate=no approve=no promote=no",
        ], self.width)
        navigator = [f"instructions: {len(explanation.instructions)}"]
        for item in explanation.instructions:
            marker = ">" if item.index == self.selected else " "
            dependencies = ",".join(item.dependencies) or "root"
            fan_out = "yes" if item.fan_out > 1 else "no"
            navigator.append(
                f"{marker} [{item.index}] {item.node_id} op={item.op} "
                f"depends={dependencies} fan-out={fan_out} uses={item.fan_out} "
                f"consumers={','.join(item.consumers) or 'none'}"
            )
        if selected.destination_register is None:
            destination = "none (STORE defines no value)"
            lifetime = "none (STORE defines no value)"
            release = "none"
        else:
            destination = f"r{selected.destination_register}"
            lifetime = (
                f"definition={selected.definition_index} "
                f"last-use={selected.last_use_index if selected.last_use_index is not None else 'none'} "
                f"live-range=[{selected.live_range[0]},{selected.live_range[1]}]"
            )
            release = (
                str(selected.release_after_index)
                if selected.release_after_index is not None else "not released in program"
            )
        inspector = [
            f"program-order index: {selected.index}",
            f"node: {selected.node_id}",
            f"opcode: {selected.op}",
            f"encoded word: 0x{selected.encoded_word:08x}",
            f"dependencies: {','.join(selected.dependencies) or 'root'}",
            f"source registers: {','.join(f'r{item}' for item in selected.source_registers) or 'none'}",
            f"assigned register: {destination}",
            f"lifetime indices: {lifetime}",
            f"release after program-order index: {release}",
            (
                f"fan-out: {'yes' if selected.fan_out > 1 else 'no'}; "
                f"uses={selected.fan_out}; consumers={','.join(selected.consumers) or 'none'}"
            ),
        ]
        affine = explanation.affine
        retained = [
            (
                f"affine: profile={affine['profile']} rows={affine['rows']} "
                f"columns={affine['columns']} input-stride={affine['input_stride']} "
                f"output-stride={affine['output_stride']}"
            ),
            (
                f"affine work: outputs={affine['active_outputs']} "
                f"conformance transactions/output={affine['transactions_per_output']} "
                f"sha256={affine['configuration_sha256']}"
            ),
            *[
                f"{name}: {identity}"
                for name, identity in explanation.identities.items()
            ],
            (
                "agreement: oracle=fallback=RTL exact; output sha256="
                f"{explanation.agreement['rtl_output_sha256']}"
            ),
            "evidence class (this Garden view): host-functional",
            "retained execution evidence class: rtl-simulation-functional",
            f"retained evidence manifest sha256: {explanation.retained_evidence_sha256}",
            "performance=not-measured",
            (
                "polls= is a termination diagnostic, not cycles, elapsed time, "
                "throughput, or performance"
            ),
        ]
        pane_width = self.width if self.width < 120 else (self.width - 2) // 3
        panes = [
            _pane("Graph / Dependencies", navigator, pane_width),
            _pane("Compiler Lowering", inspector, pane_width),
            _pane("Retained Evidence", retained, pane_width),
        ]
        if self.width < 120:
            body = ["[stacked layout]"]
            for pane in panes:
                body.extend(pane)
        else:
            body = _join_panes(panes)
        footer = _wrapped_lines([
            "Commands / Status",
            "Navigation: j next | k previous | g first | G last | q quit",
            "authority: read-only; no compiler, execution, simulator, UIO, device, mutation, approval, or promotion.",
            *[f"demo: {command}" for command in explanation.demo_commands],
        ], self.width)
        return "\n".join([*header, "", *body, "", *footer])


def load_garden_view(path: str) -> GardenSnapshot | GardenDynamicExplanation:
    """Load dynamic input once under its stricter boundary; preserve legacy v1."""
    candidate = Path(path)
    if not candidate.is_absolute() and candidate.as_posix() == path \
            and all(part not in {"", ".", ".."} for part in candidate.parts):
        raw = _read_dynamic_document(path)
        if raw.get("schema") == DYNAMIC_EXPLANATION_SCHEMA:
            return GardenDynamicExplanation.from_dict(raw)
    return GardenSnapshot.load(candidate)


def render_empty() -> str:
    return "\n".join((
        "Raveil Garden | empty",
        "No validated graph snapshot is loaded.",
        "authority: observe-only execute=no mutate=no approve=no promote=no",
    ))


def render_error(message: str) -> str:
    printable = "".join(character if character.isprintable() else " " for character in message)
    bounded = " ".join(printable.split())[:512]
    return "\n".join((
        "Raveil Garden | error",
        bounded or "unknown snapshot error",
        "No graph state was accepted.",
    ))


def render_key_session(
    snapshot: GardenSnapshot | GardenDynamicExplanation,
    keys: str,
    width: int = DEFAULT_RENDER_WIDTH,
) -> str:
    if len(keys) > MAX_NAVIGATION_STEPS:
        raise ValueError("garden navigation exceeds the bounded step limit")
    browser = (
        GardenDynamicBrowser(snapshot, width)
        if isinstance(snapshot, GardenDynamicExplanation)
        else GardenBrowser(snapshot, width)
    )
    screens = [browser.render()]
    for key in keys:
        if not browser.navigate(key):
            screens.append("Raveil Garden | closed")
            break
        screens.append(browser.render())
    return "\n\n---\n\n".join(screens)


def run_interactive(
    snapshot: GardenSnapshot | GardenDynamicExplanation,
    input_stream: TextIO,
    output_stream: TextIO,
    width: int = DEFAULT_RENDER_WIDTH,
) -> int:
    browser = (
        GardenDynamicBrowser(snapshot, width)
        if isinstance(snapshot, GardenDynamicExplanation)
        else GardenBrowser(snapshot, width)
    )
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
