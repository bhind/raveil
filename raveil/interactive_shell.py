from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import shlex
import tempfile
from typing import Callable

from .graph_mvp import (
    AnalyticalPredictor,
    ExecutionContract,
    GraphCompiler,
    GraphExecutor,
    GraphMVPResult,
    GraphProgram,
    GraphVariant,
    OptimizationProposal,
)
from .native_backend import NativeCBackend
from .workspace import NativeWorkspace, WorkspaceError
from .command_graph import (
    CommandBenchmarkResult,
    CommandComparison,
    CommandGraphCompiler,
    CommandGraphProgram,
    CommandGraphResult,
    ToolRegistry,
    benchmark as benchmark_command_graph,
)


HELP = """Available commands:
  help
      Show this command reference.
  pwd
      Show the current virtual workspace directory.
  cd [PATH]
      Change directory; no path means the virtual root.
  ls [PATH]
      List a workspace directory in lexical order.
  cat PATH
      Print one bounded UTF-8 regular file.
  stat PATH
      Show bounded virtual file metadata.
  mkdir PATH
      Create one directory without recursive parent creation.
  write PATH TEXT...
      Create one bounded UTF-8 file without overwriting.
  run COMMAND...
      Execute the bounded allowlisted command subset directly.
  graph compile COMMAND...
      Compile a pipeline, sequence, or ||| join-fanout into a command DAG.
  graph execute --compare
      Run the equal-policy direct baseline first and compare the graph result.
  graph benchmark --warmups N --repetitions N
      Run a balanced development/non-claim timing smoke.
  graph result [PATH]
      Show or exclusively save the strict command-graph comparison result.
  graph create gemm --m M --n N --k K
      Create a bounded GEMM graph with positive integer dimensions.
  graph show
      Show the current graph and its identity.
  variants
      Compile and list the canonical baseline-first variant slate.
  propose
      Ask the analytical adviser to select a variant or abstain.
  execute
      Run the trusted baseline first, then commit or roll back the proposal.
  result [PATH]
      Show the strict JSON result, or exclusively save it to PATH.
  history
      Show this session's graph workflow events.
  reset
      Clear the current graph workflow while retaining session history.
  exit
      Leave the Native Interactive CLI."""


@dataclass
class NativeInteractiveSession:
    source: Path = Path("benchmarks/native/benchmark.c")
    workspace: NativeWorkspace = field(default_factory=lambda: NativeWorkspace(Path.cwd()))
    compiler: str = "cc"
    timeout_seconds: float = 30.0
    warmups: int = 1
    inner_iterations: int = 1
    minimum_predicted_improvement: float = 0.05
    graph: GraphProgram | None = None
    variants_value: tuple[GraphVariant, ...] | None = None
    proposal: OptimizationProposal | None = None
    execution_result: GraphMVPResult | None = None
    events: list[str] = field(default_factory=list)
    command_program: CommandGraphProgram | None = None
    command_result: CommandGraphResult | None = None
    command_benchmark: CommandBenchmarkResult | None = None
    command_registry: ToolRegistry = field(default_factory=ToolRegistry)
    command_parse_ns: int = 0
    command_construction_ns: int = 0

    def create_graph(self, family: str, m: int, n: int, k: int) -> str:
        self.graph = GraphProgram.create(family, m, n, k)  # type: ignore[arg-type]
        self.variants_value = None
        self.proposal = None
        self.execution_result = None
        self.command_program = None
        self.command_result = None
        self.command_benchmark = None
        self.events.append(f"graph-created {self.graph.program_id}")
        return f"created {self.graph.program_id}"

    def show_graph(self) -> str:
        if self.command_program is not None:
            return json.dumps(self.command_program.to_dict(), indent=2, sort_keys=True)
        if self.graph is None:
            raise ValueError("no graph; run 'graph create' first")
        return json.dumps({
            "program_id": self.graph.program_id,
            "family": self.graph.family,
            "m": self.graph.m,
            "n": self.graph.n,
            "k": self.graph.k,
            "program_sha256": self.graph.identity,
        }, sort_keys=True)

    def compile_variants(self) -> str:
        if self.graph is None:
            raise ValueError("no graph; run 'graph create' first")
        if self.variants_value is None:
            self.variants_value = GraphCompiler(ExecutionContract()).compile(self.graph)
            self.events.append("variants-compiled")
        return "\n".join(item.variant_id for item in self.variants_value)

    def make_proposal(self) -> str:
        if self.graph is None or self.variants_value is None:
            raise ValueError("invalid order; run 'variants' first")
        if self.proposal is None:
            self.proposal = AnalyticalPredictor(self.minimum_predicted_improvement).propose(
                self.graph, self.variants_value
            )
            self.events.append("proposal-abstained" if self.proposal.abstained else f"proposal {self.proposal.variant_id}")
        return json.dumps(self.proposal.to_dict(), sort_keys=True)

    def execute(self) -> str:
        if self.graph is None or self.variants_value is None or self.proposal is None:
            raise ValueError("invalid order; run graph create, variants, then propose")
        if self.execution_result is not None:
            raise ValueError("graph was already executed; run 'reset' before executing again")
        with tempfile.TemporaryDirectory(prefix="raveil-native-shell-") as directory:
            backend = NativeCBackend(
                self.source,
                Path(directory) / "raveil-native",
                compiler=self.compiler,
                compiler_flags=(
                    "-O3", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-D_POSIX_C_SOURCE=200809L",
                ),
                timeout_seconds=self.timeout_seconds,
                warmups=self.warmups,
            )
            backend.compile()
            self.execution_result = GraphExecutor(backend, ExecutionContract()).execute(
                self.graph,
                self.variants_value,
                self.proposal,
                inner_iterations=self.inner_iterations,
            )
        self.events.append(f"execute {self.execution_result.outcome}")
        return f"outcome={self.execution_result.outcome} selected={self.execution_result.selected_variant}"

    def result(self, output: str | None = None) -> str:
        if self.execution_result is None:
            raise ValueError("no result; run 'execute' first")
        encoded = json.dumps(self.execution_result.to_dict(), indent=2, sort_keys=True) + "\n"
        if output is not None:
            virtual_path = self.workspace.write_text(output, encoded)
            self.events.append(f"result-saved {virtual_path}")
            return f"saved {output}"
        return encoded.rstrip()

    def history(self) -> str:
        return "\n".join(f"{index + 1}: {event}" for index, event in enumerate(self.events)) or "history is empty"

    def reset(self) -> str:
        self.graph = None
        self.variants_value = None
        self.proposal = None
        self.execution_result = None
        self.command_program = None
        self.command_result = None
        self.command_benchmark = None
        self.events.append("reset")
        return "session reset"

    def compile_command_graph(self, source: str) -> str:
        compiler = CommandGraphCompiler(self.workspace, self.command_registry)
        self.command_program = compiler.compile(source)
        self.command_parse_ns = compiler.last_parse_ns
        self.command_construction_ns = compiler.last_construction_ns
        self.command_result = None
        self.command_benchmark = None
        self.events.append(f"command-graph-compiled {self.command_program.graph_id}")
        return f"graph={self.command_program.graph_id}\nnodes={len(self.command_program.nodes)} edges={len(self.command_program.edges)}"

    def run_command(self, source: str) -> str:
        compiler = CommandGraphCompiler(self.workspace, self.command_registry)
        program = compiler.compile(source)
        outcome = CommandComparison(self.workspace, self.command_registry).direct(program, publish=True)
        self.events.append(f"command-direct {outcome.status}")
        if outcome.status != "executed":
            raise ValueError(f"command failed: status={outcome.status} exit={outcome.exit_status} {outcome.stderr}")
        return outcome.stdout.decode("utf-8", "replace").rstrip("\n")

    def execute_command_graph(self) -> str:
        if self.command_program is None:
            raise ValueError("no command graph; run 'graph compile' first")
        if self.command_result is not None:
            raise ValueError("command graph was already executed; compile or reset first")
        self.command_result = CommandComparison(self.workspace, self.command_registry).execute(
            self.command_program, publish=True
        )
        self.events.append(f"command-graph-execute semantic={self.command_result.semantic_valid}")
        return "\n".join((
            f"semantic={'valid' if self.command_result.semantic_valid else 'invalid'}",
            f"baseline_exit={self.command_result.direct.exit_status}",
            f"graph_exit={self.command_result.graph.exit_status}",
            f"committed={str(self.command_result.committed).lower()}",
        ))

    def benchmark_command_graph(self, warmups: int, repetitions: int) -> str:
        if self.command_program is None:
            raise ValueError("no command graph; run 'graph compile' first")
        self.command_benchmark = benchmark_command_graph(
            self.command_program, self.workspace, self.command_registry,
            warmups=warmups, repetitions=repetitions,
            parse_ns=self.command_parse_ns, construction_ns=self.command_construction_ns,
        )
        value = self.command_benchmark.to_dict()
        self.events.append("command-graph-benchmark development-non-claim")
        return "\n".join((
            "benchmark=development-non-claim",
            f"direct_median_ns={value['direct_execution']['median_ns']}",
            f"graph_median_ns={value['graph_execution']['median_ns']}",
            f"semantic_mismatches={value['mismatch_count']}",
            "crossover=none",
        ))

    def command_graph_result(self, output: str | None) -> str:
        if self.command_result is None:
            raise ValueError("no command graph result; run 'graph execute --compare' first")
        encoded = json.dumps(self.command_result.to_dict(), indent=2, sort_keys=True) + "\n"
        if output is not None:
            virtual = self.workspace.write_text(output, encoded)
            self.events.append(f"command-result-saved {virtual}")
            return f"saved {virtual}"
        return encoded.rstrip()


def _dimension(tokens: list[str], name: str) -> int:
    try:
        index = tokens.index(name)
        return int(tokens[index + 1])
    except (ValueError, IndexError) as exc:
        raise ValueError(f"graph create requires {name} INTEGER") from exc


def dispatch(session: NativeInteractiveSession, line: str) -> tuple[bool, str]:
    stripped = line.strip()
    if stripped.startswith("run "):
        return True, session.run_command(stripped[4:])
    if stripped.startswith("graph compile "):
        return True, session.compile_command_graph(stripped[len("graph compile "):])
    if stripped == "graph execute --compare":
        return True, session.execute_command_graph()
    if stripped.startswith("graph benchmark "):
        benchmark_tokens = shlex.split(stripped)
        if len(benchmark_tokens) != 6 or benchmark_tokens[:2] != ["graph", "benchmark"]:
            raise ValueError("usage: graph benchmark --warmups N --repetitions N")
        return True, session.benchmark_command_graph(
            _dimension(benchmark_tokens, "--warmups"), _dimension(benchmark_tokens, "--repetitions")
        )
    if stripped == "graph result" or stripped.startswith("graph result "):
        result_tokens = shlex.split(stripped)
        if len(result_tokens) not in {2, 3}:
            raise ValueError("usage: graph result [PATH]")
        return True, session.command_graph_result(result_tokens[2] if len(result_tokens) == 3 else None)
    try:
        tokens = shlex.split(line)
    except ValueError as exc:
        raise ValueError(f"invalid command line: {exc}") from exc
    if not tokens:
        return True, ""
    if tokens == ["help"]:
        return True, HELP
    if tokens == ["exit"]:
        return False, "bye"
    if tokens == ["pwd"]:
        return True, session.workspace.pwd()
    if tokens and tokens[0] == "cd" and len(tokens) <= 2:
        return True, session.workspace.cd(tokens[1] if len(tokens) == 2 else None)
    if tokens and tokens[0] == "ls" and len(tokens) <= 2:
        return True, "\n".join(session.workspace.ls(tokens[1] if len(tokens) == 2 else None))
    if tokens and tokens[0] == "cat" and len(tokens) == 2:
        return True, session.workspace.read_text(tokens[1])
    if tokens and tokens[0] == "stat" and len(tokens) == 2:
        metadata = session.workspace.stat(tokens[1])
        return True, "\n".join((
            f"path: {metadata.path}",
            f"type: {metadata.kind}",
            f"size: {metadata.size}",
            f"readable: {str(metadata.readable).lower()}",
            f"writable: {str(metadata.writable).lower()}",
        ))
    if tokens and tokens[0] == "mkdir" and len(tokens) == 2:
        return True, f"directory created: {session.workspace.mkdir(tokens[1])}"
    if tokens and tokens[0] == "write" and len(tokens) >= 3:
        content = " ".join(tokens[2:])
        content = content.replace("\\n", "\n").replace("\\t", "\t")
        virtual_path = session.workspace.write_text(tokens[1], content)
        return True, f"file written: {virtual_path}"
    if tokens[:3] == ["graph", "create", "gemm"]:
        allowed = {"graph", "create", "gemm", "--m", "--n", "--k"}
        if len(tokens) != 9 or any(token.startswith("--") and token not in allowed for token in tokens):
            raise ValueError("usage: graph create gemm --m M --n N --k K")
        return True, session.create_graph("gemm", _dimension(tokens, "--m"), _dimension(tokens, "--n"), _dimension(tokens, "--k"))
    if tokens == ["graph", "show"]:
        return True, session.show_graph()
    if tokens == ["variants"]:
        return True, session.compile_variants()
    if tokens == ["propose"]:
        return True, session.make_proposal()
    if tokens == ["execute"]:
        return True, session.execute()
    if tokens and tokens[0] == "result" and len(tokens) <= 2:
        return True, session.result(tokens[1] if len(tokens) == 2 else None)
    if tokens == ["history"]:
        return True, session.history()
    if tokens == ["reset"]:
        return True, session.reset()
    raise ValueError("unknown command; run 'help'")


def run_interactive_shell(
    session: NativeInteractiveSession,
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    try:
        import readline  # noqa: F401 - activates the host Python line editor
    except ImportError:
        pass
    output_fn("Raveil Native Interactive CLI; type 'help'")
    while True:
        try:
            line = input_fn("raveil> ")
            keep_running, message = dispatch(session, line)
            if message:
                output_fn(message)
            if not keep_running:
                return 0
        except (EOFError, KeyboardInterrupt):
            output_fn("bye")
            return 0
        except (FileExistsError, FileNotFoundError, OSError, RuntimeError, ValueError, WorkspaceError) as exc:
            output_fn(f"error: {exc}")
