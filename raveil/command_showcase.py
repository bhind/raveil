"""Synthetic, non-claim Command Graph showcase for the Native CLI.

The showcase deliberately uses only the existing bounded command-graph
compiler and its direct-argv tool registry.  Its cache is a demonstrator for
validated derived artifacts, not a CommandGraphExecutor production feature.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import stat as stat_module
import tempfile
import time
from typing import Any

from .command_graph import (
    CommandComparison,
    CommandGraphCompiler,
    ExecutionPolicy,
    ToolRegistry,
)
from .workspace import NativeWorkspace, WorkspaceError


SHOWCASE_SCHEMA = "raveil.command-graph-showcase/v1"
SCENARIOS = ("showcase-parallel", "showcase-incremental", "control-small")
PARALLEL_NODES = (16, 32, 64)
INPUT_BYTES = 60 * 1024
SMALL_INPUT_BYTES = 512
MAX_SHOWCASE_PARALLEL = 8


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _existing_file(workspace: NativeWorkspace, virtual: str) -> bytes:
    _virtual, path = workspace.existing_host_path(virtual)
    metadata = path.lstat()
    if not stat_module.S_ISREG(metadata.st_mode) or stat_module.S_ISLNK(metadata.st_mode):
        raise WorkspaceError("showcase input/cache entry must be a regular non-symlink file")
    return path.read_bytes()


def _input_bytes(index: int, maximum: int) -> bytes:
    """Create a deterministic, deliberately unsorted ordinary text file."""
    lines: list[bytes] = []
    counter = 0
    while sum(map(len, lines)) < maximum:
        token = hashlib.sha256(f"raveil-showcase-v1:{index}:{counter}".encode("ascii")).hexdigest()
        lines.append(f"{token} record-{(counter * 73 + index * 19) % 1009:04d}\n".encode("ascii"))
        counter += 1
    data = b"".join(lines)
    # Retain complete lines; every ordinary sort input remains deterministic.
    return data[: data.rfind(b"\n", 0, maximum) + 1]


@dataclass(frozen=True)
class ShowcaseSpec:
    scenario: str
    nodes: int
    bytes_per_input: int

    @property
    def root(self) -> str:
        return f"/showcase/{self.scenario}"

    @property
    def source_directory(self) -> str:
        return self.root + "/inputs"

    @property
    def mutation_directory(self) -> str:
        return self.root + "/mutations"

    @property
    def cache_directory(self) -> str:
        return self.root + "/cache"

    @property
    def state_path(self) -> str:
        return self.root + "/state.json"

    def input_path(self, index: int) -> str:
        return f"{self.source_directory}/input-{index:03d}.txt"

    def active_input_path(self, workspace: NativeWorkspace, index: int) -> str:
        changed = f"{self.mutation_directory}/input-{index:03d}.txt"
        try:
            workspace.existing_host_path(changed)
        except WorkspaceError as exc:
            if "does not exist" not in str(exc):
                raise
            return self.input_path(index)
        return changed

    def output_path(self, index: int) -> str:
        return f"/outputs/output-{index:03d}.txt"


def _spec(scenario: str, nodes: int | None = None) -> ShowcaseSpec:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown showcase scenario: {scenario}")
    if scenario == "control-small":
        if nodes not in {None, 4}:
            raise ValueError("control-small fixes node count at 4")
        return ShowcaseSpec(scenario, 4, SMALL_INPUT_BYTES)
    if nodes not in {None, *PARALLEL_NODES}:
        raise ValueError("showcase parallel node count must be 16, 32, or 64")
    return ShowcaseSpec(scenario, 16 if nodes is None else nodes, INPUT_BYTES)


def list_showcases() -> str:
    return "\n".join((
        "Scope: conceptual tool/process-level illustration only; this is far above the intended native operation/dependency/effect graph and does not test an ISA or CPU microarchitecture.",
        "showcase-parallel: synthetic 16/32/64-way independent sort; sequential, equal-concurrency, and graph paths",
        "showcase-incremental: the same synthetic fan-out plus verified demo-only derived-artifact reuse",
        "control-small: four 512-byte sorts; Graph overhead may dominate",
        "Experience: not connected to Command Graph admission, scheduling, reuse, or commit in this demo.",
        "Evidence: host-development-smoke / development-non-claim; EXP-0004 remains Planned.",
    ))


def prepare_showcase(workspace: NativeWorkspace, scenario: str, nodes: int | None = None) -> str:
    spec = _spec(scenario, nodes)
    # Every path is exclusively created. Re-running prepare is deliberately an error.
    workspace.mkdir("/showcase") if "showcase" not in workspace.ls("/") else None
    workspace.mkdir("/outputs") if "outputs" not in workspace.ls("/") else None
    workspace.mkdir(spec.root)
    workspace.mkdir(spec.source_directory)
    workspace.mkdir(spec.cache_directory)
    workspace.mkdir(spec.mutation_directory)
    for index in range(spec.nodes):
        workspace.write_bytes(spec.input_path(index), _input_bytes(index, spec.bytes_per_input), maximum=64 * 1024)
    state = {
        "schema": SHOWCASE_SCHEMA,
        "scenario": spec.scenario,
        "nodes": spec.nodes,
        "bytes_per_input": spec.bytes_per_input,
        "input_sha256": {spec.input_path(index): _sha256(_input_bytes(index, spec.bytes_per_input)) for index in range(spec.nodes)},
        "synthetic": True,
        "claim_status": "development-non-claim",
    }
    workspace.write_text(spec.state_path, _canonical(state) + "\n")
    return "\n".join((
        f"prepared scenario={spec.scenario} synthetic=true nodes={spec.nodes} bytes_per_input={spec.bytes_per_input}",
        "abstraction=tool-process conceptual-only; not native operation/ISA/microarchitecture granularity",
        "workload=independent ordinary sort files; direct argv allowlist; shell=False",
        "Experience=not-connected (advice-only; no proposal, admission, scheduling, reuse, or commit authority)",
        "next: showcase run --workspace PATH --scenario " + spec.scenario,
    ))


def _require_prepared(workspace: NativeWorkspace, spec: ShowcaseSpec) -> None:
    try:
        state = json.loads(_existing_file(workspace, spec.state_path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("showcase state is malformed") from exc
    if (
        type(state) is not dict
        or state.get("schema") != SHOWCASE_SCHEMA
        or state.get("scenario") != spec.scenario
        or state.get("nodes") != spec.nodes
        or state.get("bytes_per_input") != spec.bytes_per_input
        or state.get("synthetic") is not True
        or state.get("claim_status") != "development-non-claim"
    ):
        raise ValueError("showcase state does not match the requested synthetic scenario")


def mutate_showcase(workspace: NativeWorkspace, scenario: str, index: int = 0,
                    nodes: int | None = None) -> str:
    spec = _spec(scenario, nodes)
    _require_prepared(workspace, spec)
    if not 0 <= index < spec.nodes:
        raise ValueError("mutation node is outside this prepared scenario")
    # The original remains immutable; selecting this deterministic replacement is the one-input change.
    original = _existing_file(workspace, spec.input_path(index))
    changed = original + b"0000000000000000000000000000000000000000000000000000000000000000 mutation\n"
    target = f"{spec.mutation_directory}/input-{index:03d}.txt"
    workspace.write_bytes(target, changed, maximum=64 * 1024)
    return "\n".join((
        f"mutated input=node-{index + 1:03d} deterministic=true original_sha256={_sha256(original)}",
        f"active_sha256={_sha256(changed)}; original retained; next run will invalidate only this input recipe when cache proof holds",
    ))


def _source(spec: ShowcaseSpec, workspace: NativeWorkspace, operator: str) -> str:
    return f" {operator} ".join(
        f"sort {spec.active_input_path(workspace, index)} > {spec.output_path(index)}"
        for index in range(spec.nodes)
    )


def _node_recipe(node: Any) -> str:
    return _sha256(_canonical(node.to_dict()).encode("ascii"))


def _cache_path(spec: ShowcaseSpec, node: Any, input_digest: str, output_digest: str) -> str:
    return f"{spec.cache_directory}/{node.node_id}-{_node_recipe(node)[:16]}-{input_digest[:16]}-{output_digest}.out"


def _cache_hit(workspace: NativeWorkspace, spec: ShowcaseSpec, node: Any, input_digest: str) -> tuple[str, bytes] | None:
    prefix = f"{node.node_id}-{_node_recipe(node)[:16]}-{input_digest[:16]}-"
    for name in workspace.ls(spec.cache_directory):
        if not name.startswith(prefix) or not name.endswith(".out"):
            continue
        claimed = name[len(prefix):-4]
        if len(claimed) != 64:
            continue
        virtual = f"{spec.cache_directory}/{name}"
        data = _existing_file(workspace, virtual)
        if _sha256(data) == claimed:
            return virtual, data
    return None


def _single_node_output(spec: ShowcaseSpec, workspace: NativeWorkspace, source: str) -> tuple[bytes, str]:
    """Run a one-node candidate only after a direct/graph semantic comparison."""
    with tempfile.TemporaryDirectory(prefix="raveil-showcase-node-") as directory:
        root = Path(directory)
        (root / "showcase" / spec.scenario / "inputs").mkdir(parents=True)
        (root / "showcase" / spec.scenario / "mutations").mkdir(parents=True)
        (root / "outputs").mkdir()
        # Copy only the declared input path. This is a private controlled comparison workspace.
        active = source.split()[1]
        relative = active.lstrip("/")
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_existing_file(workspace, active))
        temporary = NativeWorkspace(root)
        registry = ToolRegistry()
        program = CommandGraphCompiler(temporary, registry, ExecutionPolicy(max_nodes=1, max_parallel=1)).compile(source)
        result = CommandComparison(temporary, registry).execute(program, publish=True)
        if not result.semantic_valid:
            raise RuntimeError("single-node candidate failed semantic validation")
        output = _existing_file(temporary, program.declared_outputs[0])
        return output, program.graph_id


def run_showcase(workspace: NativeWorkspace, scenario: str, nodes: int | None = None) -> str:
    spec = _spec(scenario, nodes)
    _require_prepared(workspace, spec)
    registry = ToolRegistry()
    policy = ExecutionPolicy(max_nodes=spec.nodes, max_parallel=MAX_SHOWCASE_PARALLEL)
    sequential_compiler = CommandGraphCompiler(workspace, registry, policy)
    sequential = sequential_compiler.compile(_source(spec, workspace, ";"))
    graph_compiler = CommandGraphCompiler(workspace, registry, policy)
    graph_program = graph_compiler.compile(_source(spec, workspace, "|||"))
    comparison = CommandComparison(workspace, registry)

    # Baseline-first evaluation: source-order sequential, then the equal-cap
    # direct fan-out baseline, then the DAG candidate under the identical cap.
    sequential_outcome = comparison.direct(sequential, publish=False)
    compared = comparison.execute(graph_program, publish=False, order="direct-first")
    if sequential_outcome.status != "executed" or not compared.semantic_valid:
        raise RuntimeError("showcase admission or semantic validation failed")
    if sequential_outcome.outputs != compared.direct.outputs:
        raise RuntimeError("sequential and equal-concurrency baseline outputs differ")

    # Validated demo-only reuse: each cached artifact binds current input,
    # complete node recipe/tool identity, and the payload hash in its filename.
    reuse_start = time.perf_counter_ns()
    executed: list[str] = []
    reused: list[str] = []
    invalidated: list[str] = []
    for index, node in enumerate(graph_program.nodes):
        active = spec.active_input_path(workspace, index)
        input_digest = _sha256(_existing_file(workspace, active))
        hit = _cache_hit(workspace, spec, node, input_digest)
        if hit is not None:
            reused.append(node.node_id)
            continue
        if any(name.startswith(node.node_id + "-") for name in workspace.ls(spec.cache_directory)):
            invalidated.append(node.node_id)
        source = f"sort {active} > /outputs/output-{index:03d}.txt"
        output, _identity = _single_node_output(spec, workspace, source)
        cache = _cache_path(spec, node, input_digest, _sha256(output))
        workspace.write_bytes(cache, output, maximum=64 * 1024)
        executed.append(node.node_id)

    graph_end_to_end = (graph_compiler.last_parse_ns + graph_compiler.last_construction_ns
                        + compared.graph.duration_ns + compared.validation_ns)
    cache_phase_ns = time.perf_counter_ns() - reuse_start
    evaluation_total = (sequential_outcome.duration_ns + compared.direct.duration_ns
                        + compared.graph.duration_ns + graph_end_to_end)
    candidate_delta = compared.direct.duration_ns - compared.graph.duration_ns
    speedup = compared.direct.duration_ns / max(1, compared.graph.duration_ns)
    critical = max((node.duration_ns for node in compared.graph.nodes), default=0)
    output_manifest = _sha256(_canonical(list(compared.graph.outputs)).encode("ascii"))
    lines = [
        f"showcase={spec.scenario} synthetic=true evidence=host-development-smoke claim=development-non-claim",
        "abstraction=tool-process conceptual-only; native operation/dependency/effect graph, OoO replacement, cache hierarchy, pipeline, ISA, area, and energy are not evaluated",
        f"graph id={graph_program.graph_id} nodes={len(graph_program.nodes)} edges={len(graph_program.edges)} critical_path=one-independent-sort-node observed_ns={critical}",
        "graph_nodes=" + ",".join(node.node_id for node in graph_program.nodes),
        "graph_edges=none (independent fan-out)",
        f"admission=accepted tools=hash-bound-direct-argv controlled_env=true shell=False max_parallel={policy.max_parallel}",
        "Experience=not-connected advice-only; no Experience record/proposal can admit, schedule, reuse, validate, or commit this command graph",
        f"semantic_hashes=valid outputs={len(compared.graph.outputs)} output_manifest_sha256={output_manifest} direct_graph_exact=true sequential_equal_exact=true",
        f"baseline sequential execution_ns={sequential_outcome.duration_ns} observed_parallelism={sequential_outcome.maximum_concurrency}",
        f"baseline equal-concurrency execution_ns={compared.direct.duration_ns} observed_parallelism={compared.direct.maximum_concurrency}",
        f"candidate graph construction_ns={graph_compiler.last_construction_ns} execution_ns={compared.graph.duration_ns} end_to_end_ns={graph_end_to_end} observed_parallelism={compared.graph.maximum_concurrency}",
        f"candidate-only delta_ns={candidate_delta} speedup={speedup:.3f}x (display only; not a performance claim)",
        f"baseline-first evaluation_total_ns={evaluation_total}; this repeatedly executes baselines and is not a production speedup",
        "production_reuse=not-implemented in CommandGraphExecutor; showcase_cache=validated-demo-only",
        f"reuse executed={len(executed)}[{','.join(executed)}] reused={len(reused)}[{','.join(reused)}] invalidated={len(invalidated)}[{','.join(invalidated)}]",
        f"showcase_cache_phase_ns={cache_phase_ns}; cached payloads were re-hashed and cache misses were separately direct/graph validated (not a production fast path)",
        "EXP-0004=Planned; this synthetic smoke neither completes nor reanalyzes the claim experiment.",
    ]
    return "\n".join(lines)
