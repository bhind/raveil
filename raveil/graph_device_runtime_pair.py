"""Operator boundary for exactly two requests through one simulator build."""

from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any

from .graph_device_axi4lite_request import (
    GraphDeviceAxi4LiteRequestError,
    finalize,
)
from .graph_device_submit import admit


_MARKER = re.compile(
    r"GraphDevice-AXI4LITE-RUNTIME-DEMO-V1 status=PASS requests=2 "
    r"same_simulator=1 rejected_before_axi=1 simulator_sha256=(?P<sha>[0-9a-f]{64}) "
    r"path=(?P<path>artifacts/graph_device_axi4lite_runtime_demo/run\.[A-Za-z0-9]{6}) "
    r"private=1 publication=0 evidence=rtl-simulation-functional performance=not-measured"
)


class GraphDeviceRuntimePairError(RuntimeError):
    """The two-request runtime boundary failed closed."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _session_path(marker: str, repository: Path) -> tuple[Path, str]:
    match = _MARKER.fullmatch(marker)
    if match is None:
        raise GraphDeviceRuntimePairError("runtime pair marker is invalid")
    relative = Path(match.group("path"))
    candidate = repository / relative
    try:
        current = repository
        if current.is_symlink():
            raise GraphDeviceRuntimePairError("repository root is a symbolic link")
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise GraphDeviceRuntimePairError("runtime pair path contains a symbolic link")
        resolved_repository = repository.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_repository)
    except (OSError, ValueError) as error:
        raise GraphDeviceRuntimePairError("runtime pair path is invalid") from error
    expected_parent = resolved_repository / "artifacts" / "graph_device_axi4lite_runtime_demo"
    if resolved.parent != expected_parent or not resolved.is_dir():
        raise GraphDeviceRuntimePairError("runtime pair path escaped its artifact root")
    return resolved, match.group("sha")


def _rejected_before_axi(session: Path) -> None:
    rejected = session / "rejected-request"
    try:
        info = rejected.lstat()
    except OSError as error:
        raise GraphDeviceRuntimePairError("rejected request evidence is missing") from error
    if not stat.S_ISDIR(info.st_mode) or rejected.is_symlink():
        raise GraphDeviceRuntimePairError("rejected request evidence is unsafe")
    if os.path.lexists(rejected / "axi-transcript.log"):
        raise GraphDeviceRuntimePairError("rejected request produced AXI traffic")
    stderr = rejected / "device.stderr"
    try:
        stderr_info = stderr.lstat()
    except OSError as error:
        raise GraphDeviceRuntimePairError("rejected request diagnostic is missing") from error
    if not stat.S_ISREG(stderr_info.st_mode) or stderr_info.st_size == 0:
        raise GraphDeviceRuntimePairError("rejected request diagnostic is invalid")


def _receipt(root: Path, expected: dict[str, Any]) -> dict[str, Any]:
    try:
        receipt = finalize(root, verify_existing=True)
    except (GraphDeviceAxi4LiteRequestError, OSError) as error:
        raise GraphDeviceRuntimePairError(str(error)) from error
    if receipt.get("submission") != expected:
        raise GraphDeviceRuntimePairError("runtime pair receipt order or request differs")
    return receipt


def run_pair(
    graphs: list[str], seeds: list[int], repository: Path | None = None
) -> str:
    """Admit and execute exactly two ordered requests through one build."""
    if len(graphs) != 2 or len(seeds) != 2:
        raise GraphDeviceRuntimePairError(
            "run-pair requires exactly two --graph and two --seed values"
        )
    repo = repository or _root()
    submissions = [admit(graph, seed, repo) for graph, seed in zip(graphs, seeds)]
    runner = repo / "hardware/chisel/run-graph-device-axi4lite-runtime-demo.sh"
    command = [str(runner)]
    for submission in submissions:
        command.extend(
            ("--graph", submission["graph_path"], "--seed", str(submission["seed"]))
        )
    try:
        result = subprocess.run(
            command,
            cwd=repo,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise GraphDeviceRuntimePairError(
            f"runtime pair runner could not start: {error}"
        ) from error
    markers = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("GraphDevice-AXI4LITE-RUNTIME-DEMO-V1")
    ]
    if result.returncode != 0 or len(markers) != 1:
        raise GraphDeviceRuntimePairError("runtime pair runner failed")
    session, marker_sha = _session_path(markers[0], repo)
    receipts = [
        _receipt(session / f"request-{index}", submission)
        for index, submission in enumerate(submissions, start=1)
    ]
    simulator_hashes = {receipt.get("simulator_sha256") for receipt in receipts}
    if simulator_hashes != {marker_sha}:
        raise GraphDeviceRuntimePairError(
            "runtime pair did not use one receipt-bound simulator"
        )
    _rejected_before_axi(session)
    return "\n".join(
        (
            "GraphDevice-AXI4LITE-RUNTIME-PAIR-V1 status=PASS requests=2",
            f"Request 1 graph={submissions[0]['graph_id']} seed={submissions[0]['seed']} oracle=PASS",
            f"Request 2 graph={submissions[1]['graph_id']} seed={submissions[1]['seed']} oracle=PASS",
            f"Same simulator=PASS sha256={marker_sha}",
            "Rejected before AXI=PASS",
            "Evidence class=rtl-simulation-functional",
            "Performance=not-measured",
        )
    )
