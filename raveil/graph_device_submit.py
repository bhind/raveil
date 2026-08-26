"""Fail-closed admission for one accepted Graph-device descriptor.

This boundary deliberately prepares no device work.  It binds an operator's
repository-relative descriptor selection to the frozen T-0123 catalogue so a
later transport-neutral runtime can consume the submission without accepting
arbitrary Graph JSON.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .graph_device_dag import GraphDeviceDagError, compile_descriptor, load_descriptor
from .riscv_stencil_signature import input_words


SUBMISSION_SCHEMA = "raveil.graph-device-submission/v1"
TASK = "T-0128"
SLICE = "S01"
EVIDENCE_CLASS = "host-functional"
EXECUTION = "not-started"
NON_CLAIMS = [
    "rtl-simulation",
    "arbitrary-graph",
    "general-graph",
    "performance",
    "latency",
    "throughput",
    "resource",
    "area",
    "energy",
    "emulation",
    "kv260",
    "fpga",
    "asic",
    "silicon",
    "novelty",
    "patent",
    "legal-clearance",
    "data-publication",
    "experience-authority",
    "production-security",
]

# These are byte identities of the T-0123 canonical descriptor files, rather
# than a re-serialization of their JSON.  Formatting changes are therefore an
# admission failure too.
CATALOGUE = {
    "contracts/graph_device_dags/five-point.json": {
        "descriptor_sha256": "75dd54355b1454efe6a4fe2dabeced64c4052a425b1d8e872a81470fc3be8980",
        "graph_id": "five-point",
        "program_sha256": "83ba878d2dddb952d08a9366e3d640d631bc463740b0781c2249bf47e6e785bd",
    },
    "contracts/graph_device_dags/compact-horizontal-three-point.json": {
        "descriptor_sha256": "b52348d785fae07bcca00030565efa84596a05a8a869c8f5fc1812a003cd6d8e",
        "graph_id": "compact-horizontal-three-point",
        "program_sha256": "9c16c4a8b574b534a85918d51790803aa9ab80ad1e22cbf4e838f9de3a2055ee",
    },
    "contracts/graph_device_dags/vertical-three-point.json": {
        "descriptor_sha256": "ee3988a9b65140642c73d1272bb21ffa07c6ed89a0cd66d5495806c383217aad",
        "graph_id": "vertical-three-point",
        "program_sha256": "325b4a49ee875e1c329ecff55be41a9cdaddc22b8ef4ca9ee37e6f0d8978dc02",
    },
}


class GraphDeviceSubmissionError(ValueError):
    """A requested submission escaped the fixed operator admission boundary."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_path(value: str) -> Path:
    if value not in CATALOGUE:
        raise GraphDeviceSubmissionError("graph must name one canonical repository descriptor")
    path = Path(value)
    if path.is_absolute() or path.as_posix() != value:
        raise GraphDeviceSubmissionError("graph path is not canonical repository-relative")
    return path


def _reject_symlinks(repo: Path, relative: Path) -> Path:
    candidate = repo / relative
    current = repo
    if current.is_symlink():
        raise GraphDeviceSubmissionError("repository root is a symbolic link")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise GraphDeviceSubmissionError("graph path contains a symbolic link")
    try:
        resolved_repo = repo.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise GraphDeviceSubmissionError(f"graph descriptor cannot be resolved: {error}") from error
    if resolved.parent != (resolved_repo / "contracts" / "graph_device_dags"):
        raise GraphDeviceSubmissionError("graph path escaped the canonical descriptor directory")
    return candidate


def _catalogue_entry(repo: Path, relative: str) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = CATALOGUE[relative]
    path = _reject_symlinks(repo, Path(relative))
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise GraphDeviceSubmissionError(f"graph descriptor cannot be read: {error}") from error
    if hashlib.sha256(raw).hexdigest() != expected["descriptor_sha256"]:
        raise GraphDeviceSubmissionError("graph descriptor bytes differ from the accepted catalogue")
    try:
        descriptor = load_descriptor(path)
        program = compile_descriptor(descriptor)
    except GraphDeviceDagError as error:
        raise GraphDeviceSubmissionError(str(error)) from error
    if descriptor["graph_id"] != expected["graph_id"] or \
            program["program_sha256"] != expected["program_sha256"]:
        raise GraphDeviceSubmissionError("graph descriptor identity differs from the accepted catalogue")
    return descriptor, program


def admit(graph: str, seed: int, root: Path | None = None) -> dict[str, Any]:
    """Return a deterministic non-executing submission for one frozen graph."""
    relative = _canonical_path(graph).as_posix()
    if type(seed) is not int:
        raise GraphDeviceSubmissionError("seed must be an integer")
    try:
        input_words(seed)
    except ValueError as error:
        raise GraphDeviceSubmissionError(str(error)) from error
    repo = root if root is not None else _root()
    entries = {item: _catalogue_entry(repo, item) for item in CATALOGUE}
    graph_ids = [descriptor["graph_id"] for descriptor, _ in entries.values()]
    program_ids = [program["program_sha256"] for _, program in entries.values()]
    if len(set(graph_ids)) != len(CATALOGUE) or len(set(program_ids)) != len(CATALOGUE):
        raise GraphDeviceSubmissionError("accepted catalogue contains duplicate identity")
    descriptor, program = entries[relative]
    expected = CATALOGUE[relative]
    return {
        "schema": SUBMISSION_SCHEMA,
        "task": TASK,
        "slice": SLICE,
        "graph_path": relative,
        "graph_id": descriptor["graph_id"],
        "descriptor_sha256": expected["descriptor_sha256"],
        "program_sha256": program["program_sha256"],
        "seed": seed,
        "evidence_class": EVIDENCE_CLASS,
        "execution": EXECUTION,
        "non_claims": NON_CLAIMS,
    }


def render_submission(graph: str, seed: int, root: Path | None = None) -> str:
    return json.dumps(admit(graph, seed, root), sort_keys=True, separators=(",", ":"))
