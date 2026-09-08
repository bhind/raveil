"""Read-only admission checks for editable project recipes.

This module intentionally does not execute a workload, invoke a tool, create a
run, or inspect a Docker daemon/image. It gives the interactive workspace a
small, deterministic inventory of known prerequisites and unknowns.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable

from .command_graph import ALLOWLIST, CommandGraphCompiler, ToolIdentity, ToolRegistry
from .graph_mvp import GraphProgram
from . import project_graph
from .workspace import NativeWorkspace, WorkspaceError


PASS = "pass"
FAIL = "fail"
NOT_APPLICABLE = "not-applicable"
NOT_CHECKED = "not-checked"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    required: bool = True

    def render(self) -> str:
        return f"{self.name}: {self.status} - {self.detail}"


@dataclass(frozen=True)
class Probes:
    """Small injected read-only seams; none may execute a program."""

    executable: Callable[[str], str | None]
    regular_file: Callable[[Path], bool]
    executable_file: Callable[[Path], bool]


def _executable(name: str) -> str | None:
    if name in ALLOWLIST:
        try:
            path, _ = ToolRegistry._candidate(name)
        except ValueError:
            return None
        return str(path.resolve())
    value = shutil.which(name)
    return str(Path(value).resolve()) if value is not None else None


def _regular_file(path: Path) -> bool:
    # Match project._kernel and the actual backend's ordinary-file admission.
    return path.is_file()


def _executable_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and os.access(path, os.X_OK)


DEFAULT_PROBES = Probes(_executable, _regular_file, _executable_file)


class _AdmissionToolRegistry(ToolRegistry):
    """Validate compiler syntax/path policy without ToolRegistry's --version call."""

    def resolve(self, name: str) -> ToolIdentity:
        if name not in ALLOWLIST:
            raise ValueError(f"tool is not allowlisted: {name}")
        # This identity is deliberately not runnable.  Tool availability is a
        # separate check below, so compilation remains entirely non-executing.
        return ToolIdentity(name, f"preflight://{name}", "not-invoked", "0" * 64, "not-invoked")


def _check(name: str, action: Callable[[], str], *, required: bool = True) -> Check:
    try:
        return Check(name, PASS, action(), required)
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError) as error:
        return Check(name, FAIL, str(error), required)


def _recipe_and_admission(project: Any, recipe_name: str) -> tuple[dict[str, Any] | None, list[Check], Any | None]:
    """Return admitted recipe and a compiler product without evaluating it."""
    try:
        recipe = project.recipe(recipe_name)
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError) as error:
        return None, [Check("recipe", FAIL, str(error)),
                      Check("input", NOT_APPLICABLE, "recipe was not admitted", False),
                      Check("admission", NOT_APPLICABLE, "recipe was not admitted", False)], None

    checks = [Check("recipe", PASS, f"{recipe['kind']} recipe schema admitted")]
    if recipe["kind"] == "command":
        compiler = CommandGraphCompiler(NativeWorkspace(project.root / "inputs"), _AdmissionToolRegistry())
        try:
            program = compiler.compile(recipe["source"])
        except WorkspaceError as error:
            checks.extend((Check("input", FAIL, str(error)),
                           Check("admission", NOT_APPLICABLE,
                                 "command input validation failed", False)))
            return recipe, checks, None
        except (OSError, ValueError, RuntimeError, TypeError, KeyError) as error:
            checks.extend((Check("input", NOT_APPLICABLE,
                                 "command admission did not complete; declared inputs were not accepted", False),
                           Check("admission", FAIL, str(error))))
            return recipe, checks, None
        inputs = ", ".join(program.declared_inputs) or "none"
        outputs = ", ".join(program.declared_outputs) or "none"
        checks.extend((Check("input", PASS,
                             f"declared regular inputs admitted: {inputs}; declared outputs absent: {outputs}"),
                       Check("admission", PASS, f"allowlist/path policy admitted {len(program.nodes)} node(s)")))
        return recipe, checks, program
    if recipe["kind"] == "gemm":
        admission = _check("admission", lambda: _gemm_admission(recipe))
        checks.extend((Check("input", NOT_APPLICABLE, "GEMM inputs are deterministically generated", False), admission))
        return recipe, checks, None

    inputs = NativeWorkspace(project.root / "inputs")
    descriptor: dict[str, Any] | None = None
    try:
        value = json.loads(inputs.read_text(recipe["descriptor"]), object_pairs_hook=_object)
        if type(value) is not dict:
            raise ValueError("Graph descriptor must be a JSON object")
        descriptor = value
        input_detail = f"descriptor inputs/{recipe['descriptor']} is readable"
        if "input" in recipe:
            project_graph.input_bytes(inputs.read_text(recipe["input"]).encode("utf-8"))
            input_detail += f"; snapshot inputs/{recipe['input']} is valid"
        else:
            input_detail += f"; deterministic seed={recipe['seed']} is admitted"
        checks.append(Check("input", PASS, input_detail))
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError) as error:
        checks.append(Check("input", FAIL, str(error)))
    if descriptor is None:
        checks.append(Check("admission", NOT_APPLICABLE, "Graph input failed validation", False))
    else:
        checks.append(_check("admission", lambda: _graph_admission(descriptor)))
    return recipe, checks, None


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def _gemm_admission(recipe: dict[str, Any]) -> str:
    program = GraphProgram.create("gemm", recipe["m"], recipe["n"], recipe["k"])
    return f"GEMM {program.m}x{program.n}x{program.k} admitted"


def _graph_admission(descriptor: dict[str, Any]) -> str:
    program = project_graph.compile_graph(descriptor)
    return f"Graph {program['graph_id']} transport profile admitted"


def _tools(recipe: dict[str, Any], backend: str, *, repository: Path, kernel: Path,
           compiler: str, qemu: str, probes: Probes, admitted_program: Any | None) -> Check:
    if backend == "native" and recipe["kind"] == "command":
        if admitted_program is None:
            return Check("tools", NOT_APPLICABLE, "command admission did not produce a graph", False)
        missing = [node.tool.logical_name for node in admitted_program.nodes
                   if probes.executable(node.tool.logical_name) is None]
        if missing:
            return Check("tools", FAIL, "missing required command tool(s): " + ", ".join(sorted(set(missing))))
        return Check("tools", PASS, "required command tools found without invocation: "
                     + ", ".join(sorted({node.tool.logical_name for node in admitted_program.nodes})))
    if backend == "native" and recipe["kind"] == "gemm":
        if probes.executable(compiler) is None:
            return Check("tools", FAIL, f"missing C compiler: {compiler}")
        source = repository / "benchmarks/native/benchmark.c"
        if not probes.regular_file(source):
            return Check("tools", FAIL, f"missing native benchmark source: {source}")
        return Check("tools", PASS, f"C compiler and native source present; compiler not invoked ({compiler})")
    if backend == "sonatine-qemu":
        missing = []
        if probes.executable(qemu) is None:
            missing.append(f"QEMU: {qemu}")
        if not probes.regular_file(kernel):
            missing.append(f"Sonatine kernel: {kernel}")
        if missing:
            return Check("tools", FAIL, "missing " + "; ".join(missing))
        return Check("tools", PASS, "QEMU and Sonatine kernel present; neither invoked")
    if backend == "rtl-sim":
        runner = repository / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
        dockerfile = repository / "hardware/chisel/Dockerfile"
        missing = []
        if not probes.executable_file(runner):
            missing.append(str(runner.relative_to(repository)) + " (not an executable regular file)")
        if not probes.regular_file(dockerfile):
            missing.append(str(dockerfile.relative_to(repository)))
        if probes.executable("docker") is None:
            missing.append("docker CLI")
        if missing:
            return Check("tools", FAIL, "missing " + ", ".join(missing)
                         + "; Docker daemon/image: not-checked")
        return Check("tools", PASS, "Docker CLI and RTL runner files present; Docker daemon/image: not-checked")
    return Check("tools", NOT_APPLICABLE, "backend is incompatible with this recipe", False)


def check(project: Any, recipe_name: str, backend: str, *, repository: Path, kernel: Path,
          compiler: str, qemu: str, probes: Probes = DEFAULT_PROBES) -> tuple[int, str]:
    """Render a deterministic, non-mutating known-prerequisite report.

    The return code is zero exactly when all required checks pass; unsupported
    backend/recipe pairs are an admission failure rather than a silent skip.
    """
    if backend not in {"native", "sonatine-qemu", "rtl-sim"}:
        checks = [Check("recipe", NOT_APPLICABLE, "backend is unsupported", False),
                  Check("input", NOT_APPLICABLE, "backend is unsupported", False),
                  Check("admission", FAIL, "unsupported backend"),
                  Check("tools", NOT_APPLICABLE, "backend is unsupported", False)]
    else:
        recipe, checks, admitted_program = _recipe_and_admission(project, recipe_name)
        if recipe is not None:
            compatible = ((backend == "rtl-sim") == (recipe["kind"] == "graph-device"))
            if backend == "sonatine-qemu":
                compatible = recipe["kind"] == "gemm" and max(recipe[key] for key in ("m", "n", "k")) <= 8
            if not compatible:
                checks = [item for item in checks if item.name != "admission"] + [
                    Check("admission", FAIL, f"{recipe['kind']} recipe is incompatible with backend {backend}")]
                checks.append(Check("tools", NOT_APPLICABLE, "backend is incompatible with this recipe", False))
            else:
                checks.append(_tools(recipe, backend, repository=repository, kernel=kernel,
                                     compiler=compiler, qemu=qemu, probes=probes,
                                     admitted_program=admitted_program))
        else:
            checks.append(Check("tools", NOT_APPLICABLE, "recipe was not admitted", False))
    known_prerequisites = all(item.status == PASS for item in checks if item.required)
    lines = [f"RAVEIL-PROJECT-CHECK-V1 recipe={recipe_name} backend={backend} "
             f"known_prerequisites={'true' if known_prerequisites else 'false'} "
             "execution_readiness=not-checked actions=0 runs_created=0",
             *(item.render() for item in checks),
             "summary: KNOWN-PREREQUISITES-PASS; execution readiness NOT CHECKED "
             "(no workload, tool invocation, run, build, network, simulation, device or install action)"
             if known_prerequisites else
             "summary: KNOWN-PREREQUISITES-FAIL; execution readiness NOT CHECKED "
             "(no workload, tool invocation, run, build, network, simulation, device or install action)"]
    return (0 if known_prerequisites else 2), "\n".join(lines)
