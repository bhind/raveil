"""Persistent, inspectable recipes over the existing guarded executors.

Project files are cooperative local data, not an isolation or authority boundary.
Every run recompiles its recipe and stores results in a fresh private workspace.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from typing import Any
from uuid import uuid4

from .command_graph import CommandComparison, CommandGraphCompiler, ToolRegistry
from .graph_mvp import GraphProgram, run_graph_mvp
from .native_backend import NativeCBackend
from .sonatine_backend import SonatineQEMUBackend
from .workspace import NativeWorkspace
from . import project_graph

REPOSITORY = Path(__file__).resolve().parents[1]
CONFIG = {"schema": "raveil.project/v1", "recipes": "recipes", "inputs": "inputs", "runs": "runs"}
RECIPE_SCHEMA = "raveil.project-recipe/v1"
GRAPH_SNAPSHOT_RECIPE_SCHEMA = "raveil.project-recipe/v2"
RUN_SCHEMA = "raveil.project-run/v1"
NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}\Z")
MAX_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 1024
MAX_PREVIEW_BYTES = 1024


def encoded(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("project artifact write made no progress")
            view = view[written:]
    finally:
        os.close(descriptor)


def make_private_directory(path: Path) -> None:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("project workspaces require no-follow directory descriptors")
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        if not os.path.samestat(os.fstat(descriptor), path.lstat()):
            raise OSError("project directory changed during initialization")
        os.fchmod(descriptor, 0o700)
    finally:
        os.close(descriptor)


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json(workspace: NativeWorkspace, path: str) -> dict[str, Any]:
    value = json.loads(workspace.read_text(path), object_pairs_hook=_object)
    if type(value) is not dict:
        raise ValueError("expected a JSON object")
    return value


def name(value: str) -> str:
    if not NAME.fullmatch(value):
        raise ValueError("name must contain only letters, digits, '-' or '_' (1..80 characters)")
    return value


def tree(root: Path, destination: Path | None = None) -> dict[str, str]:
    """Bounded regular-file snapshot; manifest includes empty directories."""
    workspace = NativeWorkspace(root)
    manifest: dict[str, str] = {}
    total = 0
    if destination is not None:
        destination.mkdir(mode=0o700)

    def visit(relative: str) -> None:
        nonlocal total
        for entry in workspace.ls(relative or "/"):
            child = f"{relative}/{entry}"
            info = workspace.stat(child)
            if len(manifest) >= MAX_ENTRIES:
                raise ValueError("project snapshot exceeds 1024 entries")
            source = root / child.lstrip("/")
            target = destination / child.lstrip("/") if destination else None
            if info.kind == "directory":
                manifest[child] = "directory"
                if target:
                    target.mkdir(mode=0o700)
                visit(child)
            else:
                if info.size > MAX_BYTES - total:
                    raise ValueError("project snapshot exceeds 16 MiB")
                data = source.read_bytes()
                total += len(data)
                if total > MAX_BYTES:
                    raise ValueError("project snapshot exceeds 16 MiB")
                manifest[child] = digest(data)
                if target:
                    write_new(target, data)

    visit("")
    return manifest


def init_project(directory: Path) -> Path:
    if directory.is_symlink():
        raise ValueError("project directory must not be a symlink")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    workspace = NativeWorkspace(directory)
    if workspace.ls():
        raise ValueError("init requires a new or empty directory")
    make_private_directory(directory)
    for folder in ("recipes", "inputs", "runs"):
        workspace.mkdir(folder, mode=0o700)
    workspace.write_text("project.json", encoded(CONFIG).decode())
    recipes = {
        "logs": {"kind": "command", "source": "cat /events.txt | grep ERROR | wc -l > /errors.txt"},
        "files": {"kind": "command", "source": "sort /left.txt > /left-sorted.txt ||| sort /right.txt > /right-sorted.txt"},
        "gemm": {"kind": "gemm", "m": 8, "n": 8, "k": 8},
        "neighborhood": {"kind": "graph-device", "descriptor": "neighborhood.json", "seed": 1},
        "neighborhood-data": {"kind": "graph-device", "descriptor": "neighborhood.json", "input": "neighborhood-data.json"},
    }
    for recipe_name, recipe in recipes.items():
        schema = GRAPH_SNAPSHOT_RECIPE_SCHEMA if "input" in recipe else RECIPE_SCHEMA
        workspace.write_text(f"recipes/{recipe_name}.json", encoded({"schema": schema, **recipe}).decode())
    for filename, content in {
        "events.txt": "INFO start\nERROR failed\nERROR retry\n",
        "left.txt": "pear\napple\norange\n",
        "right.txt": "zebra\nbird\nant\n",
    }.items():
        workspace.write_text(f"inputs/{filename}", content)
    workspace.write_text("inputs/neighborhood.json", encoded(project_graph.sample_descriptor()).decode())
    workspace.write_text("inputs/neighborhood-data.json", encoded({"schema": project_graph.INPUT_SCHEMA,
                         "words": list(range(project_graph.INPUT_WORDS))}).decode())
    workspace.write_text(".gitignore", "runs/\n")
    workspace.write_text("README.md", """# Your Raveil workspace

Edit inputs/ and recipes/ with your usual editor. Each run keeps its own copy.
Add CHECKOUT/scripts to PATH once, then run from this project directory:

    export PATH="CHECKOUT/scripts:$PATH"
    raveil project show logs
    raveil project run logs
    raveil project run files
    raveil project runs
    raveil project diff RUN_A RUN_B
    raveil project run gemm --backend native
    raveil project run gemm --backend sonatine-qemu
    raveil project console sonatine

Try adding an ERROR line to inputs/events.txt and run logs again. Compare the
two run IDs. Inspect runs/ID/workspace/errors.txt with cat or your editor.
Recipe command paths are relative to the virtual root of the input copy.
Use your normal shell for arbitrary tools, Git, editing, and file management.
Raveil command recipes accept only the documented bounded command subset.

GEMM inputs are generated by the existing backend from the saved dimensions;
inputs/ files are used only by command recipes. Sonatine supports dimensions
1..8 and reports emulation correctness, never a speed comparison with native.
History is local development evidence, not a cache or a signed audit store.

Edit inputs/neighborhood.json to change the actual bounded RTL Graph:

    raveil project show neighborhood
    raveil project run neighborhood --backend rtl-sim

Change combine from ADD_U32 to MAX_U32 and run again, then diff the two IDs.
RTL inputs for neighborhood are generated from recipes/neighborhood.json's seed.
For editable data, use recipes/neighborhood-data.json and edit
inputs/neighborhood-data.json's exactly 324 uint32 words; its packed hash is shown
by `raveil project show neighborhood-data`.
The offline Docker/Verilator runner builds the same generic circuit each run;
there is no persistent simulator cache. Raw evidence stays in repository artifacts.
""")
    return workspace.root


class Project:
    def __init__(self, root: Path) -> None:
        self.workspace = NativeWorkspace(root)
        self.root = self.workspace.root
        if read_json(self.workspace, "project.json") != CONFIG:
            raise ValueError("unsupported project configuration; expected project/v1")
        for folder in ("recipes", "inputs", "runs"):
            if self.workspace.stat(folder).kind != "directory":
                raise ValueError(f"project {folder} must be a directory")

    def recipe(self, recipe_name: str) -> dict[str, Any]:
        recipe = read_json(self.workspace, f"recipes/{name(recipe_name)}.json")
        kind = recipe.get("kind")
        fields = {"schema", "kind", "source"} if kind == "command" else {"schema", "kind", "m", "n", "k"}
        if kind == "graph-device":
            snapshot = recipe.get("schema") == GRAPH_SNAPSHOT_RECIPE_SCHEMA
            fields = {"schema", "kind", "descriptor", "input"} if snapshot else {"schema", "kind", "descriptor", "seed"}
        if recipe.get("schema") != (GRAPH_SNAPSHOT_RECIPE_SCHEMA if kind == "graph-device" and "input" in recipe else RECIPE_SCHEMA) or set(recipe) != fields:
            raise ValueError("recipe fields do not match its exact schema")
        if kind == "command":
            if type(recipe["source"]) is not str or not recipe["source"].strip():
                raise ValueError("command recipe needs a nonempty source string")
        elif kind == "gemm":
            if any(type(recipe[key]) is not int for key in ("m", "n", "k")):
                raise ValueError("GEMM dimensions must be integers")
            GraphProgram.create("gemm", recipe["m"], recipe["n"], recipe["k"])
        elif kind == "graph-device":
            descriptor = recipe["descriptor"]
            if (type(descriptor) is not str or not descriptor.endswith(".json")
                    or "/" in descriptor or "\\" in descriptor):
                raise ValueError("Graph descriptor must be a JSON filename inside inputs/")
            name(descriptor[:-5])
            if "seed" in recipe and (type(recipe["seed"]) is not int or not 0 <= recipe["seed"] <= 0xffffffff):
                raise ValueError("Graph seed must be a uint32 integer")
            if "input" in recipe:
                input_name = recipe["input"]
                if (type(input_name) is not str or not input_name.endswith(".json")
                        or "/" in input_name or "\\" in input_name):
                    raise ValueError("Graph input must be a JSON filename inside inputs/")
                name(input_name[:-5])
        else:
            raise ValueError("recipe kind must be command, gemm or graph-device")
        return recipe

    def show(self, recipe_name: str) -> str:
        recipe = self.recipe(recipe_name)
        if recipe["kind"] == "graph-device":
            descriptor = read_json(NativeWorkspace(self.root / "inputs"), recipe["descriptor"])
            input_payload = (NativeWorkspace(self.root / "inputs").read_text(recipe["input"]).encode("utf-8")
                             if "input" in recipe else None)
            shown = project_graph.describe(descriptor, recipe.get("seed"), input_payload)
            return shown + (f"\ninput file: inputs/{recipe['input']}" if input_payload is not None else "")
        if recipe["kind"] == "gemm":
            program = GraphProgram.create("gemm", recipe["m"], recipe["n"], recipe["k"])
            return (f"{recipe_name}: GEMM {program.m}x{program.n}x{program.k}\n"
                    f"graph={program.program_id}\nprogram_sha256={program.identity}\n"
                    "nodes=1 edges=2\n"
                    f"  node-001-gemm: GEMM A[{program.m}x{program.k}] B[{program.k}x{program.n}] -> C[{program.m}x{program.n}]\n"
                    "inputs: A, B (deterministic generated matrices)\n"
                    "outputs: C (verified checksum)\n"
                    "flow: trusted baseline -> proposal -> semantic verification -> commit/rollback\n"
                    "backends: native; sonatine-qemu for dimensions 1..8")
        program = CommandGraphCompiler(NativeWorkspace(self.root / "inputs"), ToolRegistry()).compile(recipe["source"])
        lines = [f"{recipe_name}: {program.graph_id}", f"nodes={len(program.nodes)} edges={len(program.edges)}"]
        for node in program.nodes:
            lines.append(f"  {node.node_id}: {node.tool.logical_name} {' '.join(node.argv)} <- {', '.join(node.dependencies) or '(input)'}")
        lines.extend((f"inputs: {', '.join(program.declared_inputs)}", f"outputs: {', '.join(program.declared_outputs)}"))
        return "\n".join(lines)

    def run(self, recipe_name: str, backend: str, *, kernel: Path, qemu: str, compiler: str) -> dict[str, Any]:
        recipe = self.recipe(recipe_name)
        if backend not in {"native", "sonatine-qemu", "rtl-sim"}:
            raise ValueError("unsupported backend")
        if (backend == "rtl-sim") != (recipe["kind"] == "graph-device"):
            raise ValueError("graph-device recipes require --backend rtl-sim; other recipes use native or sonatine-qemu")
        if backend == "sonatine-qemu" and (recipe["kind"] != "gemm" or max(recipe[key] for key in ("m", "n", "k")) > 8):
            raise ValueError("sonatine-qemu accepts only GEMM dimensions 1..8; use native for command recipes")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:12]
        self.workspace.mkdir(f"runs/{run_id}", mode=0o700)
        directory = self.root / "runs" / run_id
        record: dict[str, Any] = {
            "schema": RUN_SCHEMA, "run_id": run_id, "recipe_name": recipe_name,
            "recipe": recipe, "recipe_sha256": digest(encoded(recipe)), "backend": backend,
            "evidence_class": {"sonatine-qemu": "qemu-emulation-correctness",
                               "native": "host-correctness", "rtl-sim": "rtl-simulation-functional"}[backend],
            "status": "failed", "error": "", "inputs": {}, "outputs": {}, "artifacts": {},
            "implementation": {}, "result": None,
        }
        write_new(directory / "recipe.json", encoded(recipe))
        try:
            stage = directory / "workspace"
            if recipe["kind"] == "command":
                record["inputs"] = tree(self.root / "inputs", directory / "inputs")
                tree(directory / "inputs", stage)
                registry = ToolRegistry()
                program = CommandGraphCompiler(NativeWorkspace(stage), registry).compile(recipe["source"])
                write_new(directory / "graph.json", encoded(program.to_dict()))
                result = CommandComparison(NativeWorkspace(stage), registry).execute(program, publish=True)
                record["result"] = result.to_dict()
                record["status"] = "succeeded" if result.semantic_valid and result.committed else "failed"
                record["implementation"] = {"tools": [node.tool.to_dict() for node in program.nodes]}
                if record["status"] == "failed":
                    record["error"] = "command comparison failed; inspect result.graph.nodes and result.direct.nodes"
                else:
                    record["outputs"] = dict(result.graph.outputs)
                write_new(directory / "stdout.txt", result.graph.stdout)
            elif recipe["kind"] == "graph-device":
                record["inputs"] = tree(self.root / "inputs", directory / "inputs")
                snapshot_manifest = dict(record["inputs"])
                descriptor_bytes = (directory / "inputs" / recipe["descriptor"]).read_bytes()
                if digest(descriptor_bytes) != snapshot_manifest["/" + recipe["descriptor"]]:
                    raise ValueError("Graph input snapshot changed before compilation")
                descriptor = json.loads(descriptor_bytes, object_pairs_hook=_object)
                if type(descriptor) is not dict:
                    raise ValueError("Graph descriptor must be a JSON object")
                program = project_graph.compile_graph(descriptor)
                explicit_input = None
                if "input" in recipe:
                    raw_input = NativeWorkspace(directory / "inputs").read_text(recipe["input"]).encode("utf-8")
                    if digest(raw_input) != snapshot_manifest["/" + recipe["input"]]:
                        raise ValueError("Graph input snapshot changed before compilation")
                    explicit_input = project_graph.input_bytes(raw_input)
                write_new(directory / "graph.json", encoded(program))
                stage.mkdir(mode=0o700)
                if explicit_input is None:
                    executed = project_graph.run_snapshot(descriptor_bytes, recipe["seed"])
                else:
                    executed = project_graph.run_snapshot(descriptor_bytes, 0, input_bytes=explicit_input)
                receipt = executed["receipt"]
                if (receipt["descriptor_sha256"] != digest(descriptor_bytes)
                        or receipt["program_sha256"] != program["program_sha256"]
                        or receipt["output_sha256"] != digest(executed["output"])):
                    raise ValueError("RTL receipt differs from the saved Graph or output")
                if explicit_input is not None and (executed["input"] != explicit_input
                        or receipt.get("input_mode") != "snapshot"
                        or receipt.get("input_sha256") != digest(explicit_input)):
                    raise ValueError("RTL receipt differs from the saved Graph input")
                if tree(directory / "inputs") != snapshot_manifest:
                    raise ValueError("Graph input snapshot changed during execution")
                write_new(directory / "receipt.json", encoded(receipt))
                write_new(directory / "stdout.txt", executed["summary"].encode())
                write_new(directory / ("input.bin" if explicit_input is not None else "generated-input.bin"), executed["input"])
                record["inputs"]["input_sha256" if explicit_input is not None else "generated_input_sha256"] = digest(executed["input"])
                if explicit_input is not None:
                    record["inputs"]["input_mode"] = "snapshot"
                for output, payload in (("output.bin", executed["output"]),
                                        ("output.txt", project_graph.output_text(executed["output"], program))):
                    write_new(stage / output, payload)
                    record["outputs"]["/" + output] = digest(payload)
                record["implementation"] = {key: receipt[key] for key in
                    ("simulator_sha256", "rtl_manifest_sha256", "source_manifest_sha256", "program_sha256")}
                record["result"] = {"validation": "oracle/fallback/RTL byte equality",
                                    "receipt": receipt, "evidence_directory": executed["evidence_directory"]}
                record["status"] = "succeeded"
            else:
                stage.mkdir(mode=0o700)
                program = GraphProgram.create("gemm", recipe["m"], recipe["n"], recipe["k"])
                write_new(directory / "graph.json", encoded(program.to_dict()))
                record["inputs"] = {"generated_program_sha256": program.identity}
                with tempfile.TemporaryDirectory(prefix="raveil-project-native-") as temporary:
                    if backend == "native":
                        source = REPOSITORY / "benchmarks/native/benchmark.c"
                        executable = _executable(compiler, "C compiler")
                        engine = NativeCBackend(source, Path(temporary) / "native", compiler=executable,
                            compiler_flags=("-O3", "-std=c11", "-Wall", "-Wextra", "-Werror", "-D_POSIX_C_SOURCE=200809L"),
                            timeout_seconds=30.0, warmups=1)
                        engine.compile()
                        record["implementation"] = {"source_sha256": digest(source.read_bytes()),
                            "compiler_sha256": digest(Path(executable).read_bytes()),
                            "binary_sha256": digest(engine.binary.read_bytes()), "flags": list(engine.compiler_flags)}
                    else:
                        executable = _executable(qemu, "QEMU; install qemu-system-riscv64")
                        _kernel(kernel)
                        record["implementation"] = {"kernel_sha256": digest(kernel.read_bytes()),
                            "qemu_sha256": digest(Path(executable).read_bytes())}
                        engine = SonatineQEMUBackend(kernel, qemu=executable)
                    result = run_graph_mvp(program, engine).to_dict()
                result["evidence_class"] = record["evidence_class"]
                record["result"] = result
                record["status"] = "failed" if result["outcome"] == "failed-closed" else "succeeded"
                record["error"] = result["rollback_reason"] if record["status"] == "failed" else ""
                record["outputs"] = {item["variant_id"]: item["checksum"] for item in result["observations"]}
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
            record["error"] = str(error)
        # Interrupted runs deliberately have no sealed record and list as incomplete.
        record["artifacts"] = tree(directory)
        payload = encoded(record)
        write_new(directory / "record.json", payload)
        write_new(directory / "record.sha256", (digest(payload) + "\n").encode())
        return record

    def load_run(self, run_id: str) -> dict[str, Any]:
        prefix = f"runs/{name(run_id)}"
        payload = self.workspace.read_text(f"{prefix}/record.json").encode()
        expected = self.workspace.read_text(f"{prefix}/record.sha256").strip()
        if digest(payload) != expected:
            raise ValueError(f"run {run_id}: record checksum mismatch")
        record = json.loads(payload, object_pairs_hook=_object)
        if type(record) is not dict or record.get("schema") != RUN_SCHEMA or record.get("run_id") != run_id:
            raise ValueError("invalid run record")
        actual = tree(self.root / prefix)
        del actual["/record.json"]
        del actual["/record.sha256"]
        if actual != record.get("artifacts") or digest(encoded(record.get("recipe"))) != record.get("recipe_sha256"):
            raise ValueError(f"run {run_id}: saved artifacts changed")
        return record

    def runs(self) -> str:
        lines = []
        for run_id in self.workspace.ls("runs"):
            try:
                record = self.load_run(run_id)
                lines.append(f"{run_id} {record['recipe_name']} {record['backend']} {record['status']}")
            except (OSError, ValueError, KeyError) as error:
                lines.append(f"{run_id} incomplete-or-invalid: {error}")
        return "\n".join(lines) or "No runs yet. Try: project run logs"

    def _preview(self, run_id: str, group: str, item: str) -> str | None:
        if not item.startswith("/"):
            return None
        root = self.root / "runs" / run_id / ("inputs" if group == "inputs" else "workspace")
        try:
            value = NativeWorkspace(root).read_text(item)
        except (OSError, ValueError, UnicodeError):
            return None
        if len(value.encode("utf-8")) > MAX_PREVIEW_BYTES:
            return None
        return json.dumps(value, ensure_ascii=False)

    def diff(self, first: str, second: str) -> str:
        left, right = self.load_run(first), self.load_run(second)
        lines = [f"{first} -> {second}"]
        graph_pair = all(record["backend"] == "rtl-sim" and record["status"] == "succeeded" for record in (left, right))
        for key in ("recipe", "backend", "evidence_class", "status"):
            if left[key] != right[key]:
                lines.append(f"{key}: {json.dumps(left[key], sort_keys=True)} -> {json.dumps(right[key], sort_keys=True)}")
        if graph_pair:
            roots = [self.root / "runs" / run_id for run_id in (first, second)]
            descriptors = [read_json(NativeWorkspace(root / "inputs"), record["recipe"]["descriptor"])
                           for root, record in zip(roots, (left, right))]
            lines.extend(project_graph.describe_changes(*descriptors,
                *(root.joinpath("workspace/output.bin").read_bytes() for root in roots)))
            for key in ("simulator_sha256", "rtl_manifest_sha256", "program_sha256"):
                before, after = left["implementation"][key], right["implementation"][key]
                lines.append(f"{key}: {'same ' + before if before == after else before + ' -> ' + after}")
        for key in ("inputs", "outputs"):
            changes = []
            for item in sorted(set(left[key]) | set(right[key])):
                before, after = left[key].get(item), right[key].get(item)
                if before != after:
                    changes.append(f"  {item}: {before or '(absent)'} -> {after or '(absent)'}")
                    before_text = None if graph_pair else self._preview(first, key, item)
                    after_text = None if graph_pair else self._preview(second, key, item)
                    if before_text is not None or after_text is not None:
                        changes.append(
                            f"    text: {before_text or '(unavailable)'} -> "
                            f"{after_text or '(unavailable)'}"
                        )
            if changes:
                lines.append(f"{key} changed:")
                lines.extend(changes)
        if len(lines) == 1:
            lines.append("No recipe, input, output, backend or status changes.")
        lines.append("Timing is not compared across backends.")
        return "\n".join(lines)


def _executable(value: str, description: str) -> str:
    resolved = shutil.which(value)
    if resolved is None:
        raise ValueError(f"missing {description}: {value}")
    return str(Path(resolved).resolve())


def _kernel(kernel: Path) -> None:
    if not kernel.is_file():
        raise ValueError("Sonatine kernel missing; run make -C sonatine in the Raveil checkout")


def command_project(args: argparse.Namespace) -> int:
    action = args.project_action
    if action == "init":
        root = init_project(Path(args.directory))
        print(f"Created {root}")
        print(f"One-time shell setup: export PATH=\"{REPOSITORY / 'scripts'}:$PATH\"")
        print(f"Next: cd {shlex.quote(str(root))} && raveil project show logs")
        return 0
    if action == "console":
        executable = _executable(args.qemu, "QEMU; install qemu-system-riscv64")
        kernel = Path(args.sonatine_kernel).resolve()
        _kernel(kernel)
        print("Sonatine console: help lists commands; exit or Ctrl+C shuts down.", flush=True)
        try:
            return subprocess.call([executable, "-machine", "virt", "-cpu", "rv64", "-m", "128M",
                                    "-smp", "1", "-bios", "none", "-nographic", "-kernel", str(kernel)])
        except KeyboardInterrupt:
            return 130
    project = Project(Path(args.project))
    if action == "show":
        print(project.show(args.recipe))
    elif action == "runs":
        print(project.runs())
    elif action == "diff":
        print(project.diff(args.first, args.second))
    else:
        if args.backend == "rtl-sim":
            print("Running Graph through offline Docker/Verilator; building the generic simulator may take a few minutes.", flush=True)
        record = project.run(args.recipe, args.backend, kernel=Path(args.sonatine_kernel).resolve(),
                             qemu=args.qemu, compiler=args.compiler)
        print(f"run={record['run_id']} status={record['status']} backend={record['backend']} evidence={record['evidence_class']}")
        directory = project.root / "runs" / record["run_id"]
        if record["status"] == "succeeded":
            if record["recipe"]["kind"] == "command":
                print("validation=PASS (Graph output matched direct reference; outputs committed)")
            elif record["recipe"]["kind"] == "graph-device":
                print("validation=PASS (descriptor oracle, C++ fallback and RTL output are byte-equal)")
                print(f"simulator_sha256={record['implementation']['simulator_sha256']}")
                print(f"Raw evidence: {record['result']['evidence_directory']}")
            else:
                print(
                    "validation=PASS (trusted GEMM baseline passed; "
                    f"outcome={record['result']['outcome']})"
                )
            if record["outputs"]:
                print("outputs:")
                for output, checksum in sorted(record["outputs"].items()):
                    print(f"  {output}: {checksum}")
                    preview = project._preview(record["run_id"], "outputs", output)
                    if preview is not None:
                        print(f"    text: {preview}")
        print(f"Saved: {directory}")
        if record["recipe"]["kind"] in {"command", "graph-device"}:
            print(f"Inspect: {directory / 'workspace'}")
        if record["error"]:
            print(record["error"])
        return 0 if record["status"] == "succeeded" else 2
    return 0


def add_project_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("project", help="edit recipes, inspect graphs and keep repeatable runs")
    commands = parser.add_subparsers(dest="project_action", required=True)
    for action in ("init", "show", "run", "runs", "diff", "console"):
        command = commands.add_parser(action)
        command.set_defaults(handler=command_project)
        if action == "init":
            command.add_argument("directory")
        elif action == "console":
            command.add_argument("target", choices=("sonatine",))
        else:
            command.add_argument("--project", default=".", help="project directory (default: current directory)")
        if action in {"show", "run"}:
            command.add_argument("recipe", help="name in recipes/, without .json")
        if action == "diff":
            command.add_argument("first")
            command.add_argument("second")
        if action == "run":
            command.add_argument("--backend", choices=("native", "sonatine-qemu", "rtl-sim"), default="native")
            command.add_argument("--compiler", default="cc")
        if action in {"run", "console"}:
            command.add_argument("--sonatine-kernel", default=str(REPOSITORY / "sonatine/build/sonatine.elf"))
            command.add_argument("--qemu", default="qemu-system-riscv64")
