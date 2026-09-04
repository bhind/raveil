"""Read-only conversion of a verified sealed request into a UIO transport plan."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
import os
import secrets
from typing import Callable
from .graph_device_dynamic_sealed import (_directory_flags, _materialize_verified_at,
                                          _mkdir_open_at, _open_dynamic_parent,
                                          _source_snapshot, verify, GraphDeviceDynamicSealError)
from .graph_device_axi4lite import _aperture, _verify_abis
from .graph_device_mvp import load_device_abi
from .graph_device_affine import load_install_abi
from .graph_device_dag import load_program_abi


def plan(bundle: Path, device: str, repository: Path) -> dict:
    match = re.fullmatch(r"/dev/uio(0|[1-9][0-9]{0,8})", device) if isinstance(device, str) else None
    if match is None:
        raise ValueError("UIO dry-run device must be a canonical /dev/uioN path")
    sealed = verify(bundle, repository)
    _verify_abis()
    aperture = _aperture()
    areas = aperture["apertures"]
    # This conversion is deliberately only a relative plan; the checked
    # contract supplies every address value and no transport primitive exists.
    result = {"schema": "raveil.graph-device-uio-dry-run/v1", "graph_id": sealed["manifest"]["graph_id"],
            "seed": sealed["manifest"]["seed"], "device": device, "aperture_bytes": max(int(item["limit"]) for item in areas.values()),
            "execution_namespace": int(areas["execution"]["base"]), "affine_namespace": int(areas["configuration"]["base"]), "program_namespace": int(areas["program"]["base"]),
            "request_sha256": sealed["manifest"]["request_sha256"], "program_sha256": sealed["manifest"]["program_sha256"],
            "affine_sha256": sealed["manifest"]["files"]["affine.bin"]["sha256"], "input_sha256": sealed["manifest"]["files"]["input.bin"]["sha256"],
            "seal_sha256": sealed["seal_sha256"], "device_opened": 0, "mmap": 0, "mmio": 0, "performance": "not-measured"}
    device_abi, affine_abi, program_abi = load_device_abi(repository), load_install_abi(repository), load_program_abi(repository)
    payloads = (
        ("program-payload-write", "program.bin", "program", program_abi["payload_window"]["base_word"], sealed["manifest"]["files"]["program.bin"]["sha256"], 0),
        ("program-commit", None, "program", program_abi["registers"]["control"], None, program_abi["control_bits"]["commit"]),
        ("affine-payload-write", "affine.bin", "configuration", affine_abi["payload_window"]["base_word"], sealed["manifest"]["files"]["affine.bin"]["sha256"], 0),
        ("affine-commit", None, "configuration", affine_abi["registers"]["control"], None, affine_abi["control_bits"]["commit"]),
        ("input-write", "input.bin", "execution", device_abi["input_window"]["base_word"], sealed["manifest"]["files"]["input.bin"]["sha256"], 0),
        ("execution-start", None, "execution", device_abi["registers"]["control"], None, device_abi["control_bits"]["start"]),
        ("output-read", "oracle.bin", "execution", device_abi["output_window"]["base_word"], sealed["manifest"]["files"]["oracle.bin"]["sha256"], 0),
    )
    operations = []
    for operation, file_name, namespace, word, digest, control_value in payloads:
        base, limit = int(areas[namespace]["base"]), int(areas[namespace]["limit"])
        size = len(sealed["files"][file_name]) if file_name else 4
        offset = base + int(word) * 4
        if offset < base or offset + size > limit:
            raise ValueError("sealed payload exceeds checked UIO namespace")
        row = {"operation": operation, "namespace": namespace, "offset": offset, "bytes": size}
        if digest: row["sha256"] = digest
        if control_value: row["value_u32"] = int(control_value)
        operations.append(row)
    result["operations"] = operations
    result["evidence_class"] = "host-functional"
    result["non_claims"] = ["no device open", "no mmap", "no MMIO", "performance not measured"]
    result["plan_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    return result


def handoff_verified_for_test(bundle: Path, device: str, repository: Path,
                              runner: Callable[[str, Path], None]) -> Path:
    """Test-only handoff: verify once, project bytes privately, invoke no device code."""
    if re.fullmatch(r"/dev/uio(0|[1-9][0-9]{0,8})", device) is None:
        raise ValueError("UIO test device must be canonical")
    verified = verify(bundle, repository)
    root, root_fd = _open_dynamic_parent(Path(repository).absolute())
    try:
        session = "uio." + secrets.token_hex(4)
        session_fd = _mkdir_open_at(root_fd, session)
        try:
            request_fd = _mkdir_open_at(session_fd, "verified-request")
            try: _materialize_verified_at(request_fd, verified)
            finally: os.close(request_fd)
        finally: os.close(session_fd)
    finally: os.close(root_fd)
    repo_fd = os.open(Path(repository).absolute(), _directory_flags())
    try:
        if _source_snapshot(repo_fd)[1] != verified["manifest"]["compiler_source_sha256"]:
            raise GraphDeviceDynamicSealError("sealed source identity drifted before test handoff")
    finally: os.close(repo_fd)
    projected = root / session / "verified-request"
    runner(device, projected)
    return projected
