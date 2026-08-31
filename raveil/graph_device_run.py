"""Top-level, read-only presenter for one finalized Graph-device RTL run."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import subprocess
from typing import Any

from .graph_device_dag import (
    GraphDeviceDagError, _parse_trace, _require_transactions, compile_descriptor,
    expected_transactions, validate_descriptor,
)
from .graph_device_selected import EVIDENCE, GraphDeviceSelectedError, validate_receipt
from .graph_device_submit import _canonical_path, _reject_symlinks, admit
from .riscv_stencil_signature import input_words


_MARKER = re.compile(
    r"^GraphDevice-SELECTED-EVIDENCE-V1 "
    r"path=(artifacts/graph_device_selected/run\.[A-Za-z0-9]{6}) "
    r"private=1 publication=0$"
)
_AXI_MARKER = re.compile(
    r"^GraphDevice-AXI4LITE-SELECTED-EVIDENCE-V1 "
    r"path=(artifacts/graph_device_axi4lite_selected/run\.[A-Za-z0-9]{6}) "
    r"private=1 publication=0$"
)
_BOUNDARIES = (
    "partial", "order", "duplicate", "opcode", "undefined", "reserved",
    "missing_store", "busy",
)


class GraphDeviceRunError(ValueError):
    pass


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _evidence_path(marker: str, repository: Path) -> Path:
    match = _MARKER.fullmatch(marker)
    if match is None:
        raise GraphDeviceRunError("selected runner marker is invalid")
    relative = Path(match.group(1))
    try:
        root = repository.resolve(strict=True)
    except OSError as error:
        raise GraphDeviceRunError("repository path cannot be resolved") from error
    candidate = root / relative
    for parent in (root / "artifacts", root / "artifacts/graph_device_selected", candidate):
        if parent.is_symlink():
            raise GraphDeviceRunError("selected evidence path contains a symbolic link")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise GraphDeviceRunError("selected evidence path is outside the repository") from error
    if resolved != candidate or not resolved.is_dir():
        raise GraphDeviceRunError("selected evidence path is not a real directory")
    return resolved


def _sample_cells(transactions: list[dict[str, Any]]) -> list[tuple[str, int, list[dict[str, Any]]]]:
    """Select bounded output-cell transaction groups from a completed segment."""
    cells: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for transaction in transactions:
        current.append(transaction)
        if transaction["write"]:
            cells.append(current)
            current = []
    if current or not cells:
        raise GraphDeviceRunError("selected trace has no completed output cells")
    samples: list[tuple[str, int, list[dict[str, Any]]]] = []
    seen: set[int] = set()
    for label, index in (("first", 0), ("middle", len(cells) // 2), ("last", len(cells) - 1)):
        if index not in seen:
            samples.append((label, index, cells[index]))
            seen.add(index)
    return samples


def _verified_descriptor(receipt: dict[str, Any], repository: Path) -> dict[str, Any]:
    """Capture one canonical descriptor whose bytes still bind the receipt."""
    submission = receipt["submission"]
    try:
        path = _reject_symlinks(repository, _canonical_path(submission["graph_path"]))
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != submission["descriptor_sha256"]:
            raise GraphDeviceRunError("selected descriptor bytes changed after receipt validation")
        descriptor = json.loads(raw.decode("ascii"))
        if not isinstance(descriptor, dict):
            raise GraphDeviceRunError("selected descriptor is not an object")
        validate_descriptor(descriptor)
    except (GraphDeviceDagError, OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise GraphDeviceRunError(f"selected descriptor cannot be rendered: {error}") from error
    if descriptor["graph_id"] != submission["graph_id"]:
        raise GraphDeviceRunError("selected descriptor graph identity changed after receipt validation")
    return descriptor


def _selected_trace(
    receipt: dict[str, Any], evidence: Path, descriptor: dict[str, Any]
) -> list[dict[str, Any]]:
    """Recheck the selected completion segment before presenting a second read."""
    submission = receipt["submission"]
    try:
        expected = expected_transactions(
            compile_descriptor(descriptor), input_words(submission["seed"])
        )
        events, segments = _parse_trace(evidence / "transaction-trace.txt")
        expected_events = ["reset"] * 8 + ["start", "cancel", "reset", "reset", "start"]
        if events != expected_events or len(segments) != 2:
            raise GraphDeviceDagError("selected trace lifecycle changed")
        _require_transactions(segments[1], expected, strict_prefix=False)
    except (GraphDeviceDagError, IndexError, OSError, ValueError) as error:
        raise GraphDeviceRunError(f"selected trace cannot be rendered: {error}") from error
    return segments[1]


def _node_detail(node: dict[str, Any]) -> str:
    if node["op"] == "LOAD_U32":
        return f"address={node['address']}"
    if node["op"] == "ADD_U32":
        return "inputs=" + ",".join(node["inputs"])
    return f"input={node['input']}"


def _render_trace(
    receipt: dict[str, Any], trace: list[dict[str, Any]], descriptor: dict[str, Any]
) -> list[str]:
    """Render a bounded view of already validated trace records only."""
    submission = receipt["submission"]
    try:
        words = input_words(submission["seed"])
    except ValueError as error:
        raise GraphDeviceRunError(f"selected trace context cannot be loaded: {error}") from error
    reads = sum(not transaction["write"] for transaction in trace)
    writes = sum(transaction["write"] for transaction in trace)
    lines = [
        "Installed program order (canonical; ADD internals not directly observed):",
        *(f"  node={index} id={node['id']} op={node['op']} {_node_detail(node)}" for index, node in enumerate(descriptor["nodes"])),
        f"Selected segment totals: transactions={len(trace)} reads={reads} writes={writes}",
        "Output-cell samples (bounded: first/middle/last):",
    ]
    for label, index, cell in _sample_cells(trace):
        lines.append(f"  sample={label} output_cell={index}")
        for transaction in cell:
            address = transaction["address"]
            if transaction["write"]:
                lines.append(
                    f"    WRITE address={address} data=0x{transaction['data']:08x} "
                    "(RTL-observed)"
                )
            else:
                lines.append(
                    f"    READ address={address} (RTL-observed) "
                    f"value=0x{words[address]:08x} "
                    "(receipt-bound input; not RTL-observed)"
                )
    return lines


def _render(receipt: dict[str, Any], trace: list[dict[str, Any]], descriptor: dict[str, Any]) -> str:
    submission = receipt["submission"]
    return "\n".join((
        "GraphDevice-RTL-RUN-V1 status=PASS",
        f"Graph={submission['graph_id']} seed={submission['seed']}",
        *_render_trace(receipt, trace, descriptor),
        "RTL=PASS", "Oracle=PASS", "Fallback=PASS",
        *(f"Boundary {name}=FAULT" for name in _BOUNDARIES),
        "Rejected publication=0",
        f"Evidence class={receipt['evidence_class']}",
        f"Performance={receipt['performance']}",
        "Nonclaims=" + ",".join(receipt["non_claims"]),
    ))


def _axi_evidence_path(marker: str, repository: Path) -> Path:
    match = _AXI_MARKER.fullmatch(marker)
    if match is None:
        raise GraphDeviceRunError("AXI4-Lite runner marker is invalid")
    try:
        root = repository.resolve(strict=True)
        candidate = root / Path(match.group(1))
        for parent in (
            root / "artifacts",
            root / "artifacts/graph_device_axi4lite_selected",
            candidate,
        ):
            if parent.is_symlink():
                raise GraphDeviceRunError("AXI4-Lite evidence path contains a symbolic link")
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as error:
        raise GraphDeviceRunError("AXI4-Lite evidence path is invalid") from error
    if resolved != candidate or not resolved.is_dir():
        raise GraphDeviceRunError("AXI4-Lite evidence path is unsafe")
    return resolved


def _run_axi4lite(repository: Path, submission: dict[str, Any]) -> str:
    """Run the frozen catalogue through the explicit AXI4-Lite simulation transport."""
    from .graph_device_axi4lite_selected import GraphDeviceAxi4LiteSelectedError, finalize
    runner = repository / "hardware/chisel/run-graph-device-axi4lite-selected.sh"
    try:
        result = subprocess.run([str(runner)], cwd=repository, text=True,
                                encoding="utf-8", errors="strict", capture_output=True,
                                check=False)
    except (OSError, UnicodeError) as error:
        raise GraphDeviceRunError(f"AXI4-Lite runner could not start: {error}") from error
    markers = [line for line in result.stdout.splitlines()
               if line.startswith("GraphDevice-AXI4LITE-SELECTED-EVIDENCE-V1")]
    if result.returncode != 0 or len(markers) != 1:
        raise GraphDeviceRunError("AXI4-Lite runner failed")
    evidence = _axi_evidence_path(markers[0], repository)
    try:
        receipt = finalize(evidence, verify_existing=True)
    except GraphDeviceAxi4LiteSelectedError as error:
        raise GraphDeviceRunError(str(error)) from error
    return "\n".join((
        "GraphDevice-AXI4LITE-RUN-V1 status=PASS graphs=3",
        f"Admission graph={submission['graph_id']} seed={submission['seed']}",
        "Execution scope=frozen-catalogue (not one selected invocation)",
        "Transport=axi4lite-sim", "RTL=PASS", "Oracle=PASS",
        "Private output=PASS", "Cancel=PASS", "Factory restart=PASS",
        f"Evidence class={receipt['evidence_class']}",
        f"Performance={receipt['performance']}",
    ))


def run(graph: str, seed: int, repository: Path | None = None, *, transport: str = "selected-rtl") -> str:
    """Run the lower selected runner and present only revalidated private evidence."""
    repo = repository or _root()
    if transport == "axi4lite-sim":
        # Admission remains mandatory even though the transport runs the whole
        # frozen catalogue: the command must not turn arbitrary JSON into work.
        try:
            submission = admit(graph, seed, repo)
        except ValueError as error:
            raise GraphDeviceRunError(str(error)) from error
        return _run_axi4lite(repo, submission)
    if transport != "selected-rtl":
        raise GraphDeviceRunError("graph-device transport is unsupported")
    runner = repo / "hardware/chisel/run-graph-device-selected.sh"
    try:
        result = subprocess.run(
            [str(runner), "--graph", graph, "--seed", str(seed)],
            cwd=repo, text=True, encoding="utf-8", errors="strict",
            capture_output=True, check=False,
        )
    except (OSError, UnicodeError) as error:
        raise GraphDeviceRunError(f"selected runner could not start: {error}") from error
    lines = result.stdout.splitlines()
    markers = [line for line in lines if line.startswith("GraphDevice-SELECTED-EVIDENCE-V1")]
    if result.returncode != 0:
        raise GraphDeviceRunError("selected runner failed")
    if len(markers) != 1:
        raise GraphDeviceRunError("selected runner must emit exactly one evidence marker")
    evidence = _evidence_path(markers[0], repo)
    try:
        receipt = validate_receipt(evidence, repo)
    except GraphDeviceSelectedError as error:
        raise GraphDeviceRunError(str(error)) from error
    submission = receipt["submission"]
    try:
        expected = admit(graph, seed, repo)
    except ValueError as error:
        raise GraphDeviceRunError(str(error)) from error
    if (submission["graph_path"] != graph or submission["seed"] != seed
            or submission["graph_id"] != expected["graph_id"]):
        raise GraphDeviceRunError("selected receipt does not bind requested graph and seed")
    if receipt["evidence_class"] != EVIDENCE or receipt["performance"] != "not-measured":
        raise GraphDeviceRunError("selected receipt evidence class changed")
    if receipt["invalid_programs_rejected"] != 8 or receipt["output_published_on_rejection"]:
        raise GraphDeviceRunError("selected receipt rejection boundary changed")
    descriptor = _verified_descriptor(receipt, repo)
    trace = _selected_trace(receipt, evidence, descriptor)
    return _render(receipt, trace, descriptor)
