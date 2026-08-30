"""Materialize one strict, read-only Graph MVP snapshot for host inspection."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import stat

from .graph_mvp import (
    ExecutionContract,
    GraphCompiler,
    GraphMVPResult,
    GraphProgram,
    GraphVariant,
    MiroirsStructuralValidator,
)
from .workspace import MAX_FILE_BYTES, NativeWorkspace, WorkspaceError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _strict_json(path: Path) -> tuple[dict[str, object], bytes]:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError(f"input is unavailable: {path}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError(f"input must be a regular non-symlink file: {path}")
    if metadata.st_size > MAX_FILE_BYTES:
        raise ValueError(f"input exceeds {MAX_FILE_BYTES} byte bound: {path}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicates)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid strict JSON input {path}: {error}") from error
    if type(value) is not dict:
        raise ValueError(f"input root must be an object: {path}")
    return value, raw


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def _empty_output_root(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise ValueError(f"output root is unavailable: {path}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("output root must be an existing non-symlink directory")
    try:
        if next(path.iterdir(), None) is not None:
            raise ValueError("output root must be empty; refusing overwrite")
    except OSError as error:
        raise ValueError(f"output root is unavailable: {path}") from error


def _validate(program: GraphProgram, result: GraphMVPResult) -> ExecutionContract:
    contract = ExecutionContract()
    variants = tuple(GraphVariant.from_dict(item) for item in result.variants)
    MiroirsStructuralValidator().validate(program, contract, variants, result.proposal)
    if result.program_id != program.program_id or result.program_sha256 != program.identity:
        raise ValueError("result program lineage does not match program input")
    if result.contract_sha256 != contract.identity:
        raise ValueError("result contract lineage does not match canonical contract")
    if variants != GraphCompiler(contract).compile(program):
        raise ValueError("result variants do not match canonical compiler output")
    variant_ids = tuple(item.variant_id for item in variants)
    baseline_id = variant_ids[0]
    observation_ids = tuple(item.variant_id for item in result.observations)
    proposal_id = result.proposal.variant_id
    expected_observations = (
        (baseline_id,)
        if result.proposal.abstained or result.outcome == "failed-closed"
        else (baseline_id, proposal_id)
    )
    if observation_ids != expected_observations:
        raise ValueError("result observations do not match the execution outcome")
    selected = result.selected_variant
    if result.outcome == "failed-closed":
        consistent = selected is None and bool(result.rollback_reason)
    elif result.outcome == "abstained":
        consistent = (
            result.proposal.abstained
            and selected == baseline_id
            and bool(result.rollback_reason)
        )
    elif result.outcome == "rolled-back":
        consistent = (
            not result.proposal.abstained
            and selected == baseline_id
            and bool(result.rollback_reason)
        )
    elif result.outcome == "committed-proposal":
        consistent = (
            not result.proposal.abstained
            and selected == proposal_id
            and result.rollback_reason == ""
        )
    else:
        consistent = False
    if not consistent:
        raise ValueError("result selection does not match its outcome and proposal")
    if result.outcome != "failed-closed":
        baseline_observation = result.observations[0]
        if (
            not baseline_observation.semantic_valid
            or baseline_observation.checksum is None
            or baseline_observation.checksum
            != baseline_observation.reference_checksum
        ):
            raise ValueError("trusted baseline observation is not semantically valid")
    if selected is not None:
        selected_observation = next(
            item for item in result.observations if item.variant_id == selected
        )
        if (
            not selected_observation.semantic_valid
            or selected_observation.checksum is None
            or selected_observation.checksum
            != selected_observation.reference_checksum
        ):
            raise ValueError("selected result observation is not semantically valid")
    if result.outcome == "committed-proposal":
        baseline, candidate = result.observations
        if (
            baseline.latency_ns is None
            or candidate.latency_ns is None
            or candidate.latency_ns >= baseline.latency_ns
        ):
            raise ValueError("committed result does not improve the observed development run")
    return contract


def materialize(program_path: Path, result_path: Path, output_root: Path) -> str:
    """Publish a deterministic inspection projection and return its manifest hash."""
    program_value, program_raw = _strict_json(program_path)
    result_value, result_raw = _strict_json(result_path)
    program = GraphProgram.from_dict(program_value)
    result = GraphMVPResult.from_dict(result_value)
    contract = _validate(program, result)
    _empty_output_root(output_root)

    entries: dict[str, bytes | None] = {
        "nodes": None,
        "variants": None,
        "memory-plans": None,
    }
    entries["program.json"] = _json(program.to_dict())
    entries["contract.json"] = _json(asdict(contract))
    for ordinal, node in enumerate(program.nodes):
        entries[f"nodes/{ordinal:03d}.json"] = _json(node.to_dict())
    for ordinal, variant in enumerate(result.variants):
        entries[f"variants/{ordinal:03d}.json"] = _json(variant)
        entries[f"memory-plans/{ordinal:03d}.json"] = _json(variant["memory_plan"])
    entries["proposal.json"] = _json(result.proposal.to_dict())
    entries["selection.txt"] = (
        f"selected_variant={result.selected_variant}\n"
        f"outcome={result.outcome}\n"
        "authority=observe-only\n"
    ).encode("utf-8")
    entries["result.json"] = _json(result.to_dict())
    tree_lines = ["graph-directory/v1"] + [
        path + "/" for path in sorted(entries) if entries[path] is None
    ]
    tree_lines.extend(
        sorted(
            [path for path, data in entries.items() if data is not None]
            + ["manifest.json"]
        )
    )
    entries["tree.txt"] = ("\n".join(tree_lines) + "\n").encode("utf-8")
    manifest = {
        "schema": "raveil.graph-directory-manifest/v1",
        "claim_status": result.claim_status,
        "evidence_class": result.evidence_class,
        "authority": "observe-only",
        "source_sha256": {"program.json": _sha256(program_raw), "result.json": _sha256(result_raw)},
        "files_sha256": {path: _sha256(data) for path, data in sorted(entries.items()) if data is not None},
    }
    entries["manifest.json"] = _json(manifest)
    workspace = NativeWorkspace(output_root)
    try:
        workspace.publish_many(entries, maximum=MAX_FILE_BYTES)
    except WorkspaceError as error:
        raise ValueError(f"directory publication failed: {error}") from error
    return _sha256(entries["manifest.json"])
