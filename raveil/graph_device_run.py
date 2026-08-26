"""Top-level, read-only presenter for one finalized Graph-device RTL run."""

from __future__ import annotations

import re
from pathlib import Path
import subprocess
from typing import Any

from .graph_device_selected import EVIDENCE, GraphDeviceSelectedError, validate_receipt
from .graph_device_submit import admit


_MARKER = re.compile(
    r"^GraphDevice-SELECTED-EVIDENCE-V1 "
    r"path=(artifacts/graph_device_selected/run\.[A-Za-z0-9]{6}) "
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


def _render(receipt: dict[str, Any]) -> str:
    submission = receipt["submission"]
    return "\n".join((
        "GraphDevice-RTL-RUN-V1 status=PASS",
        f"Graph={submission['graph_id']} seed={submission['seed']}",
        "RTL=PASS", "Oracle=PASS", "Fallback=PASS",
        *(f"Boundary {name}=FAULT" for name in _BOUNDARIES),
        "Rejected publication=0",
        f"Evidence class={receipt['evidence_class']}",
        f"Performance={receipt['performance']}",
        "Nonclaims=" + ",".join(receipt["non_claims"]),
    ))


def run(graph: str, seed: int, repository: Path | None = None) -> str:
    """Run the lower selected runner and present only revalidated private evidence."""
    repo = repository or _root()
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
    return _render(receipt)
