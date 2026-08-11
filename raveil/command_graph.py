"""Owned bounded command-graph compiler, executors, and development benchmark."""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import resource
import signal
import shlex
import shutil
import statistics
import subprocess
import tempfile
import time
from typing import Any, Iterable

from .workspace import NativeWorkspace, WorkspaceError


PROGRAM_SCHEMA = "raveil.command-graph-program/v1"
RESULT_SCHEMA = "raveil.command-graph-result/v1"
BENCHMARK_SCHEMA = "raveil.command-benchmark-result/v1"
POLICY_SCHEMA = "raveil.command-execution-policy/v1"
TOOL_SCHEMA = "raveil.command-tool/v1"
NODE_SCHEMA = "raveil.command-node/v1"
EDGE_SCHEMA = "raveil.command-edge/v1"
MAX_NODES = 64
MAX_ARGV = 32
MAX_ARG_BYTES = 4096
MAX_CAPTURE_BYTES = 1024 * 1024
MAX_STAGE_BYTES = 16 * 1024 * 1024
MAX_STAGE_FILES = 1024
MAX_PARALLEL = 8
CONTROLLED_ENV = {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"}
TOOL_DIRS = (Path("/usr/bin"), Path("/bin"), Path("/usr/local/bin"), Path("/opt/homebrew/bin"))
ALLOWLIST = {
    "echo", "printf", "pwd", "ls", "cat", "stat", "mkdir", "grep", "wc",
    "sort", "uniq", "cut", "tr", "head", "tail", "tee", "cp", "sha256sum",
}


def _exact(data: dict[str, Any], expected: set[str], name: str) -> None:
    if type(data) is not dict or set(data) != expected:
        raise ValueError(f"{name} fields do not match schema")


def _text(value: Any, name: str, maximum: int = 4096) -> str:
    if type(value) is not str or not value or len(value.encode("utf-8")) > maximum or "\x00" in value:
        raise ValueError(f"invalid {name}")
    return value


def _integer(value: Any, name: str, minimum: int = 0, maximum: int = (1 << 63) - 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"invalid {name}")
    return value


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


@dataclass(frozen=True)
class ToolIdentity:
    logical_name: str
    locator: str
    version: str
    binary_sha256: str
    adapter: str
    schema: str = TOOL_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "logical_name": self.logical_name, "locator": self.locator,
                "version": self.version, "binary_sha256": self.binary_sha256, "adapter": self.adapter}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolIdentity":
        _exact(data, {"schema", "logical_name", "locator", "version", "binary_sha256", "adapter"}, "tool")
        value = cls(_text(data["logical_name"], "tool"), _text(data["locator"], "locator"),
                    _text(data["version"], "version", 512), _text(data["binary_sha256"], "binary hash", 64),
                    _text(data["adapter"], "adapter"), _text(data["schema"], "schema"))
        if value.schema != TOOL_SCHEMA or len(value.binary_sha256) != 64:
            raise ValueError("invalid tool identity")
        return value


@dataclass(frozen=True)
class ExecutionPolicy:
    timeout_ms: int = 10_000
    max_capture_bytes: int = MAX_CAPTURE_BYTES
    max_nodes: int = MAX_NODES
    max_parallel: int = 4
    schema: str = POLICY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "timeout_ms": self.timeout_ms,
                "max_capture_bytes": self.max_capture_bytes, "max_nodes": self.max_nodes,
                "max_parallel": self.max_parallel}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionPolicy":
        _exact(data, {"schema", "timeout_ms", "max_capture_bytes", "max_nodes", "max_parallel"}, "policy")
        value = cls(_integer(data["timeout_ms"], "timeout", 1, 60_000),
                    _integer(data["max_capture_bytes"], "capture", 1, MAX_CAPTURE_BYTES),
                    _integer(data["max_nodes"], "nodes", 1, MAX_NODES),
                    _integer(data["max_parallel"], "parallel", 1, MAX_PARALLEL),
                    _text(data["schema"], "schema"))
        if value.schema != POLICY_SCHEMA:
            raise ValueError("invalid policy schema")
        return value


@dataclass(frozen=True)
class CommandNode:
    node_id: str
    tool: ToolIdentity
    argv: tuple[str, ...]
    path_indices: tuple[int, ...]
    declared_writes: tuple[str, ...]
    stdin_file: str | None
    stdout_file: str | None
    dependencies: tuple[str, ...]
    dependency_mode: str
    fanout_group: int
    schema: str = NODE_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "node_id": self.node_id, "tool": self.tool.to_dict(),
                "argv": list(self.argv), "path_indices": list(self.path_indices),
                "declared_writes": list(self.declared_writes),
                "stdin_file": self.stdin_file, "stdout_file": self.stdout_file,
                "dependencies": list(self.dependencies), "dependency_mode": self.dependency_mode,
                "fanout_group": self.fanout_group}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommandNode":
        _exact(data, {"schema", "node_id", "tool", "argv", "path_indices", "declared_writes", "stdin_file", "stdout_file",
                      "dependencies", "dependency_mode", "fanout_group"}, "node")
        if (type(data["argv"]) is not list or type(data["path_indices"]) is not list
                or type(data["declared_writes"]) is not list or type(data["dependencies"]) is not list):
            raise ValueError("invalid node lists")
        argv = tuple(_text(item, "argv") for item in data["argv"])
        paths = tuple(_integer(item, "path index", 0, max(0, len(argv) - 1)) for item in data["path_indices"])
        deps = tuple(_text(item, "dependency") for item in data["dependencies"])
        stdin_file = data["stdin_file"]
        stdout_file = data["stdout_file"]
        if stdin_file is not None:
            stdin_file = _text(stdin_file, "stdin file")
        if stdout_file is not None:
            stdout_file = _text(stdout_file, "stdout file")
        writes = tuple(_text(item, "declared write") for item in data["declared_writes"])
        value = cls(_text(data["node_id"], "node id"), ToolIdentity.from_dict(data["tool"]), argv, paths, writes,
                    stdin_file, stdout_file, deps, _text(data["dependency_mode"], "dependency mode"),
                    _integer(data["fanout_group"], "fanout group", 0, MAX_NODES), _text(data["schema"], "schema"))
        if value.schema != NODE_SCHEMA or value.dependency_mode not in {"always", "success", "stream"}:
            raise ValueError("invalid node")
        return value


@dataclass(frozen=True)
class CommandEdge:
    source: str
    target: str
    kind: str
    schema: str = EDGE_SCHEMA

    def to_dict(self) -> dict[str, str]:
        return {"schema": self.schema, "source": self.source, "target": self.target, "kind": self.kind}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommandEdge":
        _exact(data, {"schema", "source", "target", "kind"}, "edge")
        value = cls(_text(data["source"], "source"), _text(data["target"], "target"),
                    _text(data["kind"], "edge kind"), _text(data["schema"], "schema"))
        if value.schema != EDGE_SCHEMA or value.kind not in {"stream", "success", "sequence"}:
            raise ValueError("invalid edge")
        return value


@dataclass(frozen=True)
class CommandGraphProgram:
    graph_id: str
    source: str
    nodes: tuple[CommandNode, ...]
    edges: tuple[CommandEdge, ...]
    declared_inputs: tuple[str, ...]
    declared_outputs: tuple[str, ...]
    policy: ExecutionPolicy
    environment: tuple[tuple[str, str], ...]
    schema: str = PROGRAM_SCHEMA

    def _identity_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "source": self.source, "nodes": [n.to_dict() for n in self.nodes],
                "edges": [e.to_dict() for e in self.edges], "declared_inputs": list(self.declared_inputs),
                "declared_outputs": list(self.declared_outputs), "policy": self.policy.to_dict(),
                "environment": [list(item) for item in self.environment]}

    @property
    def identity(self) -> str:
        return _digest(_canonical(self._identity_dict()))

    def validate(self) -> None:
        if self.schema != PROGRAM_SCHEMA or self.graph_id != f"command-{self.identity[:16]}":
            raise ValueError("command graph identity does not match")
        if not self.nodes or len(self.nodes) > self.policy.max_nodes:
            raise ValueError("invalid command graph node count")
        ids = [node.node_id for node in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate command node")
        prior: set[str] = set()
        for node in self.nodes:
            if any(dep not in prior for dep in node.dependencies):
                raise ValueError("command graph is not topological")
            prior.add(node.node_id)
        if len(set(self.declared_outputs)) != len(self.declared_outputs):
            raise ValueError("duplicate declared output")
        if len(set(self.declared_inputs)) != len(self.declared_inputs):
            raise ValueError("duplicate declared input")

    def to_dict(self) -> dict[str, Any]:
        return {"graph_id": self.graph_id, **self._identity_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommandGraphProgram":
        _exact(data, {"schema", "graph_id", "source", "nodes", "edges", "declared_inputs", "declared_outputs",
                      "policy", "environment"}, "command graph")
        for key in ("nodes", "edges", "declared_inputs", "declared_outputs", "environment"):
            if type(data[key]) is not list:
                raise ValueError("invalid command graph list")
        env: list[tuple[str, str]] = []
        for item in data["environment"]:
            if type(item) is not list or len(item) != 2:
                raise ValueError("invalid environment")
            env.append((_text(item[0], "environment key"), _text(item[1], "environment value")))
        value = cls(_text(data["graph_id"], "graph id"), _text(data["source"], "source", 8192),
                    tuple(CommandNode.from_dict(item) for item in data["nodes"]),
                    tuple(CommandEdge.from_dict(item) for item in data["edges"]),
                    tuple(_text(item, "input") for item in data["declared_inputs"]),
                    tuple(_text(item, "output") for item in data["declared_outputs"]),
                    ExecutionPolicy.from_dict(data["policy"]), tuple(env), _text(data["schema"], "schema"))
        value.validate()
        return value


class ToolRegistry:
    def __init__(self) -> None:
        self._runtime: dict[str, Path] = {}

    @staticmethod
    def _candidate(name: str) -> tuple[Path, str]:
        names = (name,) if name != "sha256sum" else ("sha256sum", "shasum")
        for directory in TOOL_DIRS:
            for candidate_name in names:
                candidate = directory / candidate_name
                try:
                    metadata = candidate.lstat()
                except OSError:
                    continue
                if candidate.is_file() and not candidate.is_symlink() and os.access(candidate, os.X_OK):
                    return candidate, candidate_name
        raise ValueError(f"allowlisted tool is unavailable: {name}")

    def resolve(self, name: str) -> ToolIdentity:
        if name not in ALLOWLIST:
            raise ValueError(f"tool is not allowlisted: {name}")
        path, actual = self._candidate(name)
        data = path.read_bytes()
        digest = _digest(data)
        version = f"unreported-{digest[:12]}"
        for option in ("--version", "-V"):
            try:
                completed = subprocess.run([str(path), option], stdin=subprocess.DEVNULL,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           env=CONTROLLED_ENV, timeout=1, check=False)
            except (OSError, subprocess.SubprocessError):
                continue
            line = completed.stdout[:256].decode("utf-8", "replace").splitlines()
            if line and completed.returncode == 0:
                version = " ".join(line[0].split())[:256]
                break
        adapter = "shasum-a-256" if name == "sha256sum" and actual == "shasum" else "direct-argv"
        identity = ToolIdentity(name, f"system://{actual}/{digest[:16]}", version, digest, adapter)
        self._runtime[digest] = path
        return identity

    def executable(self, identity: ToolIdentity) -> Path:
        path, actual = self._candidate(identity.logical_name)
        expected_adapter = "shasum-a-256" if identity.logical_name == "sha256sum" and actual == "shasum" else "direct-argv"
        if identity.adapter != expected_adapter or identity.locator != f"system://{actual}/{identity.binary_sha256[:16]}":
            raise ValueError(f"tool identity mismatch: {identity.logical_name}")
        if _digest(path.read_bytes()) != identity.binary_sha256:
            raise ValueError(f"stale tool identity: {identity.logical_name}")
        return path


def _virtual(workspace: NativeWorkspace, token: str) -> str:
    return workspace.normalize(token)


def _tool_paths(name: str, args: list[str], workspace: NativeWorkspace) -> tuple[tuple[int, ...], set[str], set[str]]:
    paths: list[int] = []
    reads: set[str] = set()
    writes: set[str] = set()
    def path(index: int, write: bool = False) -> None:
        virtual = _virtual(workspace, args[index])
        args[index] = virtual
        paths.append(index)
        (writes if write else reads).add(virtual)
    if name == "cat":
        if not args or any(item.startswith("-") for item in args): raise ValueError("cat accepts file operands only")
        for index in range(len(args)): path(index)
    elif name == "grep":
        allowed = {"-E", "-F", "-i", "-v", "-c"}; index = 0
        while index < len(args) and args[index] in allowed: index += 1
        if index >= len(args): raise ValueError("grep requires a pattern")
        if args[index].startswith("-"): raise ValueError("unsupported grep option")
        index += 1
        for operand in range(index, len(args)):
            if args[operand].startswith("-"): raise ValueError("unsupported grep option")
            path(operand)
    elif name in {"wc", "sort"}:
        allowed = {"-l", "-w", "-c"} if name == "wc" else {"-r", "-n", "-u"}
        for index, item in enumerate(args):
            if item.startswith("-"):
                if item not in allowed: raise ValueError(f"unsupported {name} option")
            else: path(index)
    elif name == "uniq":
        index = 0
        while index < len(args) and args[index].startswith("-"):
            if args[index] not in {"-c", "-d", "-u"}: raise ValueError("unsupported uniq option")
            index += 1
        if len(args) - index > 1: raise ValueError("uniq supports at most one input file")
        if index < len(args): path(index)
    elif name == "tr":
        if len(args) != 2 or any(item.startswith("-") for item in args): raise ValueError("tr requires two sets")
    elif name in {"head", "tail"}:
        index = 0
        if args[:1] == ["-n"]:
            if len(args) < 2 or not args[1].isdigit(): raise ValueError(f"invalid {name} count")
            index = 2
        elif args and args[0].startswith("-"): raise ValueError(f"unsupported {name} option")
        for operand in range(index, len(args)): path(operand)
    elif name == "cut":
        index = 0
        while index < len(args) and args[index] in {"-d", "-f"}:
            if index + 1 >= len(args): raise ValueError("invalid cut option")
            index += 2
        if index == 0: raise ValueError("cut requires -d/-f")
        for operand in range(index, len(args)): path(operand)
    elif name == "tee":
        if not args or any(item.startswith("-") for item in args): raise ValueError("tee append/options are unsupported")
        for index in range(len(args)): path(index, True)
    elif name == "cp":
        if len(args) != 2 or any(item.startswith("-") for item in args): raise ValueError("cp requires source and destination")
        path(0); path(1, True)
    elif name == "sha256sum":
        if not args or any(item.startswith("-") for item in args): raise ValueError("sha256sum accepts files only")
        for index in range(len(args)): path(index)
    elif name in {"ls", "stat"}:
        if len(args) > 1 or any(item.startswith("-") for item in args): raise ValueError(f"unsupported {name} arguments")
        if args: path(0)
    elif name == "mkdir":
        if len(args) != 1 or args[0].startswith("-"): raise ValueError("mkdir requires one path")
        path(0, True)
    elif name == "pwd":
        if args: raise ValueError("pwd accepts no arguments")
    elif name == "echo":
        if any(item.startswith("-") for item in args): raise ValueError("echo options are unsupported")
    elif name == "printf":
        if not args or "%n" in args[0]: raise ValueError("invalid printf arguments")
    else:
        raise ValueError("unsupported tool adapter")
    return tuple(paths), reads, writes


class CommandGraphCompiler:
    def __init__(self, workspace: NativeWorkspace, registry: ToolRegistry | None = None,
                 policy: ExecutionPolicy | None = None) -> None:
        self.workspace = workspace
        self.registry = registry or ToolRegistry()
        self.policy = policy or ExecutionPolicy()
        self.last_parse_ns = 0
        self.last_construction_ns = 0

    @staticmethod
    def _tokens(source: str) -> list[str]:
        if len(source.encode("utf-8")) > 8192 or "\x00" in source or "`" in source or "$" in source:
            raise ValueError("command source is invalid or oversized")
        lexer = shlex.shlex(source, posix=True, punctuation_chars="|<>&;")
        lexer.whitespace_split = True; lexer.commenters = ""
        tokens = list(lexer)
        if not tokens: raise ValueError("command is empty")
        for token in tokens:
            if token in {">>", "||", "&"} or any(char in token for char in ("*", "?", "[", "]")):
                raise ValueError(f"unsupported shell operator or expansion: {token}")
        return tokens

    def compile(self, source: str) -> CommandGraphProgram:
        parse_start = time.perf_counter_ns()
        tokens = self._tokens(source)
        self.last_parse_ns = time.perf_counter_ns() - parse_start
        construction_start = time.perf_counter_ns()
        nodes: list[CommandNode] = []; edges: list[CommandEdge] = []
        inputs: set[str] = set(); outputs: set[str] = set()
        command: list[str] = []; stdin_file: str | None = None; stdout_file: str | None = None
        pending_operator: str | None = None; previous: list[str] = []; fanout_group = 0

        def emit() -> None:
            nonlocal command, stdin_file, stdout_file, pending_operator, previous, fanout_group
            if not command: raise ValueError("operator requires a command")
            if len(command) > MAX_ARGV or sum(len(item.encode()) for item in command) > MAX_ARG_BYTES:
                raise ValueError("command argv exceeds bounds")
            name, args = command[0], command[1:]
            if "/" in name: raise ValueError("executable paths are not accepted")
            tool = self.registry.resolve(name)
            path_indices, reads, writes = _tool_paths(name, args, self.workspace)
            inputs.update(reads); outputs.update(writes)
            if stdin_file is not None: inputs.add(stdin_file)
            if stdout_file is not None: outputs.add(stdout_file)
            node_id = f"node-{len(nodes) + 1:03d}-{name}"
            mode = "always"; dependencies: tuple[str, ...] = ()
            if pending_operator == "|": mode = "stream"; dependencies = (previous[-1],)
            elif pending_operator == "&&": mode = "success"; dependencies = tuple(previous)
            elif pending_operator == ";": mode = "always"; dependencies = tuple(previous)
            elif pending_operator == "|||": fanout_group += 1
            declared_writes = tuple(sorted(writes | ({stdout_file} if stdout_file is not None else set())))
            node = CommandNode(node_id, tool, tuple(args), path_indices, declared_writes, stdin_file, stdout_file,
                               dependencies, mode, fanout_group)
            nodes.append(node)
            for dep in dependencies:
                kind = "stream" if mode == "stream" else ("success" if mode == "success" else "sequence")
                edges.append(CommandEdge(dep, node_id, kind))
            if pending_operator == "|": previous = [node_id]
            elif pending_operator == "|||": previous.append(node_id)
            else: previous = [node_id]
            command = []; stdin_file = None; stdout_file = None; pending_operator = None

        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token in {"|", "&&", ";", "|||"}:
                emit(); pending_operator = token; index += 1; continue
            if token in {"<", ">"}:
                if index + 1 >= len(tokens) or tokens[index + 1] in {"|", "&&", ";", "|||", "<", ">"}:
                    raise ValueError("redirection requires a path")
                virtual = _virtual(self.workspace, tokens[index + 1])
                if token == "<":
                    if stdin_file is not None: raise ValueError("duplicate input redirection")
                    stdin_file = virtual
                else:
                    if stdout_file is not None: raise ValueError("duplicate output redirection")
                    stdout_file = virtual
                index += 2; continue
            command.append(token); index += 1
        emit()
        if len(nodes) > self.policy.max_nodes: raise ValueError("command graph exceeds node limit")
        external_inputs: set[str] = set()
        published_outputs = outputs
        for path in inputs:
            try:
                _, host = self.workspace.existing_host_path(path)
            except WorkspaceError as exc:
                if path not in outputs or "does not exist" not in str(exc): raise
            else:
                if not host.is_file() or host.is_symlink(): raise WorkspaceError("declared input must be a regular file")
                external_inputs.add(path)
        for path in published_outputs:
            try:
                self.workspace.existing_host_path(path)
            except WorkspaceError as exc:
                if "does not exist" not in str(exc): raise
            else:
                raise WorkspaceError(f"output already exists: {path}")
        provisional = CommandGraphProgram("pending", source, tuple(nodes), tuple(edges), tuple(sorted(external_inputs)),
                                          tuple(sorted(published_outputs)), self.policy, tuple(sorted(CONTROLLED_ENV.items())))
        value = CommandGraphProgram(f"command-{provisional.identity[:16]}", source, tuple(nodes), tuple(edges),
                                    tuple(sorted(external_inputs)), tuple(sorted(published_outputs)), self.policy,
                                    tuple(sorted(CONTROLLED_ENV.items())))
        value.validate()
        self.last_construction_ns = time.perf_counter_ns() - construction_start
        return value


@dataclass(frozen=True)
class NodeOutcome:
    node_id: str; status: str; exit_status: int; stdout_sha256: str; stderr: str; duration_ns: int
    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "status": self.status, "exit_status": self.exit_status,
                "stdout_sha256": self.stdout_sha256, "stderr": self.stderr, "duration_ns": self.duration_ns}


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str; exit_status: int; stdout: bytes; stderr: str; outputs: tuple[tuple[str, str], ...]
    nodes: tuple[NodeOutcome, ...]; duration_ns: int; maximum_concurrency: int
    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "exit_status": self.exit_status,
                "stdout_encoding": "base64",
                "stdout_base64": base64.b64encode(self.stdout).decode("ascii"),
                "stdout_sha256": _digest(self.stdout), "stderr": self.stderr,
                "outputs": [{"path": p, "sha256": h} for p, h in self.outputs],
                "nodes": [node.to_dict() for node in self.nodes], "duration_ns": self.duration_ns,
                "maximum_concurrency": self.maximum_concurrency}


def _snapshot(root: Path, target: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}; total = 0; count = 0
    target.mkdir(mode=0o700)
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current); relative = current_path.relative_to(root)
        for name in list(dirs):
            source = current_path / name
            if source.is_symlink(): raise WorkspaceError("workspace snapshot rejects symlinks")
            (target / relative / name).mkdir(mode=0o700, exist_ok=True)
            manifest["/" + str((relative / name).as_posix()).lstrip("./")] = "directory"
        for name in files:
            source = current_path / name
            if source.is_symlink() or not source.is_file(): raise WorkspaceError("workspace snapshot rejects special files")
            data = source.read_bytes(); total += len(data); count += 1
            if total > MAX_STAGE_BYTES or count > MAX_STAGE_FILES: raise WorkspaceError("workspace snapshot exceeds bounds")
            destination = target / relative / name; destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data); manifest["/" + str((relative / name).as_posix()).lstrip("./")] = _digest(data)
    return manifest


def _stage_path(stage: Path, virtual: str) -> Path:
    parts = PurePosixPath(virtual).parts
    if not virtual.startswith("/") or ".." in parts: raise ValueError("invalid staged virtual path")
    return stage.joinpath(*parts[1:])


class _ExecutorBase:
    def __init__(self, workspace: NativeWorkspace, registry: ToolRegistry, policy: ExecutionPolicy) -> None:
        self.workspace = workspace; self.registry = registry; self.policy = policy

    def _run_node(self, node: CommandNode, stage: Path, stdin: bytes) -> tuple[NodeOutcome, bytes]:
        executable = self.registry.executable(node.tool)
        argv = list(node.argv)
        for index in node.path_indices: argv[index] = str(_stage_path(stage, argv[index]))
        if node.tool.adapter == "shasum-a-256": argv = ["-a", "256", *argv]
        if node.stdin_file is not None: stdin = _stage_path(stage, node.stdin_file).read_bytes()
        if node.stdout_file is not None:
            output_path = _stage_path(stage, node.stdout_file)
            if output_path.exists(): raise WorkspaceError(f"output collision: {node.stdout_file}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
        def limits() -> None:
            resource.setrlimit(resource.RLIMIT_FSIZE, (self.policy.max_capture_bytes, self.policy.max_capture_bytes))
        start = time.perf_counter_ns()
        process: subprocess.Popen[bytes] | None = None
        try:
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                process = subprocess.Popen([str(executable), *argv], stdin=subprocess.PIPE,
                                           stdout=stdout_file, stderr=stderr_file, cwd=stage,
                                           env=dict(node_env(stage)), start_new_session=True,
                                           preexec_fn=limits if os.name == "posix" else None)
                process.communicate(input=stdin, timeout=self.policy.timeout_ms / 1000)
                stdout_file.seek(0); stderr_file.seek(0)
                stdout = stdout_file.read(self.policy.max_capture_bytes + 1)
                stderr_bytes = stderr_file.read(self.policy.max_capture_bytes + 1)
                exit_status = process.returncode
            if len(stdout) > self.policy.max_capture_bytes or len(stderr_bytes) > self.policy.max_capture_bytes:
                raise ValueError("tool output exceeds bounds")
            status = "executed" if exit_status == 0 else "failed"
        except subprocess.TimeoutExpired:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=1)
                except (OSError, subprocess.TimeoutExpired):
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except OSError: pass
                    process.wait()
            stdout = b""; stderr_bytes = b"timeout"; exit_status = 124; status = "timeout"
        if node.tool.logical_name == "sha256sum" and stdout:
            lines = []
            for line in stdout.decode("utf-8", "replace").splitlines():
                digest = line.split()[0] if line.split() else ""
                lines.append(f"{digest}\n")
            stdout = "".join(lines).encode()
        if node.tool.logical_name == "wc" and stdout and exit_status == 0:
            stdout = b" ".join(stdout.split()) + b"\n"
        if node.tool.logical_name == "uniq" and "-c" in node.argv and stdout and exit_status == 0:
            normalized = []
            for line in stdout.decode("utf-8", "strict").splitlines():
                count, value = line.strip().split(maxsplit=1)
                normalized.append(f"{int(count)} {value}\n")
            stdout = "".join(normalized).encode()
        if node.stdout_file is not None and status == "executed":
            _stage_path(stage, node.stdout_file).write_bytes(stdout); stdout = b""
        duration = time.perf_counter_ns() - start
        normalized_stderr = stderr_bytes.decode("utf-8", "replace").replace(str(stage), "/")[:65536]
        outcome = NodeOutcome(node.node_id, status, exit_status, _digest(stdout),
                              normalized_stderr, duration)
        return outcome, stdout

    def _finish(self, program: CommandGraphProgram, stage: Path, initial: dict[str, str],
                outcomes: list[NodeOutcome], terminal: dict[str, bytes], start: int,
                maximum_concurrency: int) -> ExecutionOutcome:
        after: dict[str, str] = {}; unexpected: list[str] = []
        for current, dirs, files in os.walk(stage, followlinks=False):
            for name in dirs:
                path = Path(current) / name
                if path.is_symlink(): unexpected.append("symlink")
                else: after["/" + str(path.relative_to(stage).as_posix())] = "directory"
            for name in files:
                path = Path(current) / name
                if path.is_symlink() or not path.is_file(): unexpected.append("special"); continue
                virtual = "/" + str(path.relative_to(stage).as_posix())
                after[virtual] = _digest(path.read_bytes())
        allowed = set(program.declared_outputs)
        for node in program.nodes:
            allowed.update(node.declared_writes)
        for path, digest in after.items():
            if initial.get(path) != digest and path not in allowed: unexpected.append(path)
        for path in initial:
            if path not in after and path not in allowed: unexpected.append(path)
        output_hashes = tuple((path, after[path]) for path in program.declared_outputs if path in after)
        failed = next((item for item in outcomes if item.status != "executed"), None)
        status = "executed"
        exit_status = 0
        stderr = ""
        if failed is not None:
            status = failed.status; exit_status = failed.exit_status; stderr = failed.stderr
        if unexpected or len(output_hashes) != len(program.declared_outputs):
            status = "invalid-mutation"; exit_status = 125; stderr = "undeclared or missing output mutation"
        terminal_ids = [node.node_id for node in program.nodes if not any(edge.source == node.node_id for edge in program.edges)]
        stdout = b"".join(terminal.get(node_id, b"") for node_id in terminal_ids)
        return ExecutionOutcome(status, exit_status, stdout, stderr, output_hashes, tuple(outcomes),
                                time.perf_counter_ns() - start, maximum_concurrency)


def node_env(stage: Path) -> Iterable[tuple[str, str]]:
    return (*CONTROLLED_ENV.items(), ("HOME", str(stage)), ("TMPDIR", str(stage)))


class DirectCommandExecutor(_ExecutorBase):
    """Source-order interpreter with explicit join-fanout batches."""
    def execute(self, program: CommandGraphProgram, stage: Path, initial: dict[str, str]) -> ExecutionOutcome:
        start = time.perf_counter_ns(); outcomes: dict[str, NodeOutcome] = {}; streams: dict[str, bytes] = {}
        maximum = 1; index = 0
        while index < len(program.nodes):
            node = program.nodes[index]
            batch = [node]
            if not node.dependencies:
                cursor = index + 1
                while cursor < len(program.nodes) and not program.nodes[cursor].dependencies:
                    batch.append(program.nodes[cursor]); cursor += 1
            runnable: list[CommandNode] = []
            for node in batch:
                deps = [outcomes[dep] for dep in node.dependencies]
                if node.dependency_mode in {"success", "stream"} and any(item.status != "executed" for item in deps):
                    outcomes[node.node_id] = NodeOutcome(node.node_id, "skipped", 125, _digest(b""), "dependency failed", 0)
                else: runnable.append(node)
            maximum = max(maximum, min(len(runnable), program.policy.max_parallel))
            def run(node: CommandNode) -> tuple[str, NodeOutcome, bytes]:
                stdin = streams.get(node.dependencies[-1], b"") if node.dependency_mode == "stream" else b""
                outcome, stdout = self._run_node(node, stage, stdin); return node.node_id, outcome, stdout
            with ThreadPoolExecutor(max_workers=program.policy.max_parallel) as pool:
                for node_id, outcome, stdout in pool.map(run, runnable):
                    outcomes[node_id] = outcome; streams[node_id] = stdout
            index += len(batch)
        ordered = [outcomes[node.node_id] for node in program.nodes]
        return self._finish(program, stage, initial, ordered, streams, start, max(1, maximum))


class CommandGraphExecutor(_ExecutorBase):
    """DAG executor; independent ready nodes run with the policy worker cap."""
    def execute(self, program: CommandGraphProgram, stage: Path, initial: dict[str, str]) -> ExecutionOutcome:
        start = time.perf_counter_ns(); outcomes: dict[str, NodeOutcome] = {}; streams: dict[str, bytes] = {}
        pending = list(program.nodes); maximum = 0
        while pending:
            ready = [node for node in pending if all(dep in outcomes for dep in node.dependencies)]
            if not ready: raise ValueError("command graph made no progress")
            runnable: list[CommandNode] = []
            for node in ready:
                deps = [outcomes[dep] for dep in node.dependencies]
                if node.dependency_mode in {"success", "stream"} and any(item.status != "executed" for item in deps):
                    outcomes[node.node_id] = NodeOutcome(node.node_id, "skipped", 125, _digest(b""), "dependency failed", 0)
                else: runnable.append(node)
            maximum = max(maximum, min(len(runnable), program.policy.max_parallel))
            def run(node: CommandNode) -> tuple[str, NodeOutcome, bytes]:
                stdin = streams.get(node.dependencies[-1], b"") if node.dependency_mode == "stream" else b""
                outcome, stdout = self._run_node(node, stage, stdin); return node.node_id, outcome, stdout
            with ThreadPoolExecutor(max_workers=program.policy.max_parallel) as pool:
                for node_id, outcome, stdout in pool.map(run, runnable):
                    outcomes[node_id] = outcome; streams[node_id] = stdout
            pending = [node for node in pending if node not in ready]
        ordered = [outcomes[node.node_id] for node in program.nodes]
        return self._finish(program, stage, initial, ordered, streams, start, max(1, maximum))


@dataclass(frozen=True)
class CommandGraphResult:
    graph_id: str; semantic_valid: bool; committed: bool; direct: ExecutionOutcome; graph: ExecutionOutcome
    differences: tuple[str, ...]; validation_ns: int
    schema: str = RESULT_SCHEMA
    evidence_class: str = "host-correctness"
    claim_status: str = "development-non-claim"
    def to_dict(self) -> dict[str, Any]:
        return {"schema": self.schema, "graph_id": self.graph_id, "semantic_valid": self.semantic_valid,
                "committed": self.committed, "direct": self.direct.to_dict(), "graph": self.graph.to_dict(),
                "differences": list(self.differences), "validation_ns": self.validation_ns,
                "evidence_class": self.evidence_class, "claim_status": self.claim_status}


def _differences(direct: ExecutionOutcome, graph: ExecutionOutcome) -> tuple[str, ...]:
    differences = []
    if direct.stdout != graph.stdout: differences.append("stdout")
    if direct.stderr != graph.stderr: differences.append("stderr")
    if direct.exit_status != graph.exit_status or direct.status != graph.status: differences.append("status")
    if direct.outputs != graph.outputs: differences.append("outputs")
    return tuple(differences)


class CommandComparison:
    def __init__(self, workspace: NativeWorkspace, registry: ToolRegistry) -> None:
        self.workspace = workspace; self.registry = registry

    def _validate_executable(self, program: CommandGraphProgram) -> None:
        if program.environment != tuple(sorted(CONTROLLED_ENV.items())):
            raise ValueError("command graph environment is not admitted")
        expected_edges: set[tuple[str, str, str]] = set()
        all_reads: set[str] = set(); all_writes: set[str] = set()
        for node in program.nodes:
            self.registry.executable(node.tool)
            args = list(node.argv)
            path_indices, reads, writes = _tool_paths(node.tool.logical_name, args, self.workspace)
            if tuple(args) != node.argv or path_indices != node.path_indices:
                raise ValueError("command node path classification does not match")
            declared = writes | ({node.stdout_file} if node.stdout_file is not None else set())
            if tuple(sorted(declared)) != node.declared_writes:
                raise ValueError("command node writes do not match")
            all_writes.update(declared)
            all_reads.update(reads)
            if node.stdin_file is not None:
                all_reads.add(self.workspace.normalize(node.stdin_file))
            kind = "stream" if node.dependency_mode == "stream" else (
                "success" if node.dependency_mode == "success" else "sequence")
            expected_edges.update((dependency, node.node_id, kind) for dependency in node.dependencies)
        actual_edges = {(edge.source, edge.target, edge.kind) for edge in program.edges}
        if len(actual_edges) != len(program.edges) or actual_edges != expected_edges:
            raise ValueError("command graph edges do not match dependencies")
        if set(program.declared_outputs) != all_writes:
            raise ValueError("command graph outputs do not match declared writes")
        if set(program.declared_inputs) != all_reads - all_writes:
            raise ValueError("command graph inputs do not match declared reads")

    def execute(self, program: CommandGraphProgram, *, publish: bool,
                order: str = "direct-first") -> CommandGraphResult:
        program.validate()
        self._validate_executable(program)
        if order not in {"direct-first", "graph-first"}:
            raise ValueError("invalid comparison order")
        with tempfile.TemporaryDirectory(prefix="raveil-command-compare-") as directory:
            base = Path(directory); direct_stage = base / "direct"; graph_stage = base / "graph"
            initial_direct = _snapshot(self.workspace.root, direct_stage)
            initial_graph = _snapshot(self.workspace.root, graph_stage)
            if order == "direct-first":
                direct = DirectCommandExecutor(self.workspace, self.registry, program.policy).execute(program, direct_stage, initial_direct)
                graph = CommandGraphExecutor(self.workspace, self.registry, program.policy).execute(program, graph_stage, initial_graph)
            else:
                graph = CommandGraphExecutor(self.workspace, self.registry, program.policy).execute(program, graph_stage, initial_graph)
                direct = DirectCommandExecutor(self.workspace, self.registry, program.policy).execute(program, direct_stage, initial_direct)
            validation_start = time.perf_counter_ns(); differences = _differences(direct, graph)
            valid = not differences and direct.status == "executed" and graph.status == "executed"
            committed = False
            if valid and publish:
                entries = {virtual: (None if _stage_path(graph_stage, virtual).is_dir()
                                     else _stage_path(graph_stage, virtual).read_bytes())
                           for virtual in program.declared_outputs}
                self.workspace.publish_many(entries, maximum=MAX_STAGE_BYTES)
                committed = True
            validation_ns = time.perf_counter_ns() - validation_start
            return CommandGraphResult(program.graph_id, valid, committed, direct, graph, differences, validation_ns)

    def direct(self, program: CommandGraphProgram, *, publish: bool) -> ExecutionOutcome:
        program.validate()
        self._validate_executable(program)
        with tempfile.TemporaryDirectory(prefix="raveil-command-direct-") as directory:
            stage = Path(directory) / "direct"
            initial = _snapshot(self.workspace.root, stage)
            outcome = DirectCommandExecutor(self.workspace, self.registry, program.policy).execute(program, stage, initial)
            if outcome.status == "executed" and publish:
                entries = {virtual: (None if _stage_path(stage, virtual).is_dir()
                                     else _stage_path(stage, virtual).read_bytes())
                           for virtual in program.declared_outputs}
                self.workspace.publish_many(entries, maximum=MAX_STAGE_BYTES)
            return outcome


def _percentile(values: list[int], fraction: float) -> int:
    if not values: return 0
    ordered = sorted(values); index = max(0, math.ceil(fraction * len(ordered)) - 1); return ordered[index]


def _summary(values: list[int]) -> dict[str, int]:
    if not values: return {"median_ns": 0, "p95_ns": 0, "iqr_ns": 0}
    return {"median_ns": int(statistics.median(values)), "p95_ns": _percentile(values, .95),
            "iqr_ns": _percentile(values, .75) - _percentile(values, .25)}


def _bootstrap(deltas: list[int], seed: int) -> tuple[int, int]:
    if not deltas: return (0, 0)
    rng = random.Random(seed); medians = []
    for _ in range(500): medians.append(int(statistics.median(rng.choice(deltas) for _ in deltas)))
    return (_percentile(medians, .025), _percentile(medians, .975))


@dataclass(frozen=True)
class CommandBenchmarkResult:
    graph_id: str; warmups: int; repetitions: int; seed: int; order: tuple[str, ...]
    direct_execution_ns: tuple[int, ...]; graph_execution_ns: tuple[int, ...]
    direct_end_to_end_ns: tuple[int, ...]; graph_end_to_end_ns: tuple[int, ...]
    parse_ns: int; construction_ns: int; validation_ns: tuple[int, ...]; mismatch_count: int
    timeout_count: int; declared_concurrency: int
    actual_direct_concurrency: tuple[int, ...]; actual_graph_concurrency: tuple[int, ...]
    direct_nodes: tuple[tuple[NodeOutcome, ...], ...]; graph_nodes: tuple[tuple[NodeOutcome, ...], ...]
    schema: str = BENCHMARK_SCHEMA
    def to_dict(self) -> dict[str, Any]:
        deltas = [d - g for d, g in zip(self.direct_execution_ns, self.graph_execution_ns)]
        low, high = _bootstrap(deltas, self.seed)
        comparison_valid = self.mismatch_count == 0 and self.timeout_count == 0 and len(deltas) == self.repetitions
        def metrics(values: tuple[int, ...]) -> dict[str, Any]:
            if not comparison_valid:
                return {"samples_ns": [], "median_ns": None, "p95_ns": None, "iqr_ns": None}
            return {"samples_ns": list(values), **_summary(list(values))}
        return {"schema": self.schema, "graph_id": self.graph_id, "warmups": self.warmups,
                "repetitions": self.repetitions, "seed": self.seed, "order": list(self.order),
                "parse_ns": self.parse_ns, "construction_ns": self.construction_ns,
                "direct_execution": metrics(self.direct_execution_ns),
                "graph_execution": metrics(self.graph_execution_ns),
                "direct_end_to_end": metrics(self.direct_end_to_end_ns),
                "graph_end_to_end": metrics(self.graph_end_to_end_ns),
                "validation_samples_ns": list(self.validation_ns),
                "paired_delta_median_ns": int(statistics.median(deltas)) if comparison_valid else None,
                "paired_bootstrap_95_ns": [low, high] if comparison_valid else None,
                "bootstrap_resamples": 500, "comparison_valid": comparison_valid,
                "accepted_pairs": len(deltas), "rejected_pairs": self.repetitions - len(deltas),
                "mismatch_count": self.mismatch_count,
                "timeout_count": self.timeout_count, "declared_concurrency": self.declared_concurrency,
                "actual_direct_concurrency": list(self.actual_direct_concurrency),
                "actual_graph_concurrency": list(self.actual_graph_concurrency),
                "direct_node_samples": [[node.to_dict() for node in sample] for sample in self.direct_nodes],
                "graph_node_samples": [[node.to_dict() for node in sample] for sample in self.graph_nodes],
                "equal_concurrency_baseline": self.actual_direct_concurrency == self.actual_graph_concurrency,
                "crossover_evaluated": False, "crossover": None,
                "ordinary_pipeline_baseline": False,
                "scheduling_claim_eligible": False,
                "evidence_class": "host-development-smoke",
                "claim_status": "development-non-claim"}


def benchmark(program: CommandGraphProgram, workspace: NativeWorkspace, registry: ToolRegistry,
              *, warmups: int, repetitions: int, parse_ns: int, construction_ns: int,
              seed: int = 1001) -> CommandBenchmarkResult:
    if type(warmups) is not int or not 0 <= warmups <= 10 or type(repetitions) is not int or not 1 <= repetitions <= 100:
        raise ValueError("benchmark warmups/repetitions are outside bounds")
    comparison = CommandComparison(workspace, registry)
    for _ in range(warmups): comparison.execute(program, publish=False)
    order = ["direct-first" if index % 2 == 0 else "graph-first" for index in range(repetitions)]
    random.Random(seed).shuffle(order)
    direct: list[int] = []; graph: list[int] = []; direct_e2e: list[int] = []; graph_e2e: list[int] = []
    validation: list[int] = []; mismatch = 0; timeouts = 0
    direct_concurrency: list[int] = []; graph_concurrency: list[int] = []
    direct_nodes: list[tuple[NodeOutcome, ...]] = []; graph_nodes: list[tuple[NodeOutcome, ...]] = []
    for arm in order:
        result = comparison.execute(program, publish=False, order=arm)
        timed_out = result.direct.status == "timeout" or result.graph.status == "timeout"
        mismatch += int(not result.semantic_valid); timeouts += int(timed_out)
        if result.semantic_valid and not timed_out:
            direct.append(result.direct.duration_ns); graph.append(result.graph.duration_ns)
            direct_e2e.append(result.direct.duration_ns + parse_ns + result.validation_ns)
            graph_e2e.append(result.graph.duration_ns + parse_ns + construction_ns + result.validation_ns)
            validation.append(result.validation_ns)
            direct_concurrency.append(result.direct.maximum_concurrency)
            graph_concurrency.append(result.graph.maximum_concurrency)
            direct_nodes.append(result.direct.nodes)
            graph_nodes.append(result.graph.nodes)
    return CommandBenchmarkResult(program.graph_id, warmups, repetitions, seed, tuple(order), tuple(direct), tuple(graph),
                                  tuple(direct_e2e), tuple(graph_e2e), parse_ns, construction_ns, tuple(validation),
                                  mismatch, timeouts, program.policy.max_parallel, tuple(direct_concurrency),
                                  tuple(graph_concurrency), tuple(direct_nodes), tuple(graph_nodes))
