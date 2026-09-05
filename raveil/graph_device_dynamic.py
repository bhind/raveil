"""Bounded dynamic Graph-device request preparation and one/two-request runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
from typing import Any, Sequence

from .graph_device_affine import _generated_header as affine_header
from .graph_device_affine import profiles
from .graph_device_axi4lite import _header as aperture_header
from .graph_device_dag import (
    _generated_header as dag_header,
    compile_artifact,
    compile_descriptor,
    graph_oracle,
    load_descriptor,
)
from .graph_device_mvp import _generated_header as device_abi_header
from .graph_device_mvp import compile_artifact as compile_device_artifact
from .graph_device_mvp import load_device_abi
from .graph_device_submit import CATALOGUE
from .riscv_stencil_signature import input_words


SCHEMA = "raveil.graph-device-dynamic-request/v1"
MAGIC = 0x52445731
VERSION = 1
HEADER_BYTES = 64
GRAPH_ID_BYTES = 32
PROGRAM_WORDS = 32
AFFINE_WORDS = 16
INPUT_WORDS = 324
REQUEST_BYTES = HEADER_BYTES + GRAPH_ID_BYTES + (PROGRAM_WORDS + AFFINE_WORDS + INPUT_WORDS) * 4
PROFILE_BY_SHAPE = {(16, 16): "baseline", (8, 8): "compact"}
GRAPH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,30}$")


class GraphDeviceDynamicError(ValueError):
    """A dynamic request escaped its bounded host admission boundary."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _word_bytes(words: Sequence[int]) -> bytes:
    return struct.pack(f"<{len(words)}I", *(int(word) & 0xFFFFFFFF for word in words))


def _canonical_path(repo: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise GraphDeviceDynamicError("graph path is invalid")
    path = Path(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts:
        raise GraphDeviceDynamicError("graph path must be repository-relative")
    current = repo
    if current.is_symlink():
        raise GraphDeviceDynamicError("repository root is a symbolic link")
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise GraphDeviceDynamicError("graph path contains a symbolic link")
    try:
        resolved = (repo / path).resolve(strict=True)
        resolved.relative_to(repo.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise GraphDeviceDynamicError("graph path cannot be resolved") from error
    return repo / path


def _profile_for(program: dict[str, Any]) -> dict[str, Any]:
    affine = program["affine"]
    name = PROFILE_BY_SHAPE.get((affine["rows"], affine["columns"]))
    if name is None or affine["input_stride"] != ({"baseline": 18, "compact": 10}[name]) \
            or affine["output_stride"] != ({"baseline": 16, "compact": 8}[name]):
        raise GraphDeviceDynamicError("dynamic request must use the baseline or compact affine profile")
    return next(item for item in profiles() if item["name"] == name)


def _request_bytes(program: dict[str, Any], profile: dict[str, Any], seed: int) -> bytes:
    graph_id = program["graph_id"]
    if not isinstance(graph_id, str) or GRAPH_ID_RE.fullmatch(graph_id) is None:
        raise GraphDeviceDynamicError("graph_id is not a bounded ASCII identifier")
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise GraphDeviceDynamicError("seed is outside u32")
    name = profile["name"]
    graph_id_bytes = graph_id.encode("ascii") + b"\0"
    graph_id_bytes += b"\0" * (GRAPH_ID_BYTES - len(graph_id_bytes))
    if len(graph_id_bytes) != GRAPH_ID_BYTES:
        raise GraphDeviceDynamicError("graph_id is too long")
    version = int(program["payload"][1])
    if version not in {1, 2, 3}:
        raise GraphDeviceDynamicError("program version is unsupported")
    header = struct.pack(
        "<8I", MAGIC, version, HEADER_BYTES, 0 if name == "baseline" else 1,
        seed, PROGRAM_WORDS, AFFINE_WORDS, INPUT_WORDS,
    )
    return header + b"\0" * 32 + graph_id_bytes + _word_bytes(program["payload"]) \
        + _word_bytes(profile["payload_words"] if "payload_words" in profile
                      else _profile_payload(profile)) + _word_bytes(input_words(seed))


def _profile_payload(profile: dict[str, Any]) -> list[int]:
    digest = bytes.fromhex(profile["configuration_sha256"])
    # config_words() is intentionally reproduced only for the fixed wire image;
    # admission still obtains the canonical values from graph_device_affine.
    return [0x52414631, 1, profile["rows"], profile["columns"],
            profile["input_stride"], profile["output_stride"], profile["active_outputs"],
            profile["transactions_per_output"],
            *[int.from_bytes(digest[index:index + 4], "little")
              for index in range(0, 32, 4)]]


def _write_new(path: Path, payload: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(payload)


def prepare_request(output: Path, graph: str, seed: int, repository: Path | None = None) -> dict[str, Any]:
    repo = (repository or _root()).resolve(strict=True)
    if output.exists():
        if output.is_symlink() or not output.is_dir() or any(output.iterdir()):
            raise GraphDeviceDynamicError("request output must be a new or empty directory")
    output.mkdir(parents=True, exist_ok=True)
    descriptor_path = _canonical_path(repo, graph)
    try:
        descriptor = load_descriptor(descriptor_path)
        program = compile_descriptor(descriptor)
    except (OSError, ValueError) as error:
        raise GraphDeviceDynamicError(f"descriptor admission failed: {error}") from error
    profile = _profile_for(program)
    request = _request_bytes(program, profile, seed)
    inputs = output / "inputs"
    inputs.mkdir()
    _write_new(output / "request.bin", request)
    selected_input = _word_bytes(input_words(seed))
    _write_new(output / "request-input.bin", selected_input)
    _write_new(inputs / "seed-1.bin", _word_bytes(input_words(1)))
    if seed != 1:
        _write_new(inputs / f"seed-{seed}.bin", selected_input)
    _write_new(output / "request-oracle.bin", _word_bytes(graph_oracle(descriptor, input_words(seed))))
    _write_new(
        output / "graph_device_abi_generated.h",
        device_abi_header(compile_device_artifact(), load_device_abi(repo)),
    )
    _write_new(output / "graph_device_affine_generated.h", affine_header())
    _write_new(output / "graph_device_dag_generated.h", dag_header(compile_artifact(repo)))
    # The static catalogue header is copied by the runner from a canonical
    # preparation; it is deliberately not used to dispatch this request.
    _write_new(output / "graph_device_axi4lite_aperture_generated.h", aperture_header())
    metadata = {
        "schema": SCHEMA if program["payload"][1] == 1 else f"raveil.graph-device-dynamic-request/v{program['payload'][1]}", "graph": graph, "graph_id": program["graph_id"],
        "affine": profile["name"], "seed": seed,
        "descriptor_sha256": hashlib.sha256(descriptor_path.read_bytes()).hexdigest(),
        "program_sha256": program["program_sha256"],
    }
    _write_new(output / "request.json", (json.dumps(metadata, sort_keys=True) + "\n").encode("ascii"))
    return {"descriptor": descriptor, "program": program, "profile": profile, "request": request,
            "metadata": metadata}


def _marker(output: str, session: Path, request_count: int) -> str:
    markers = [line for line in output.splitlines() if line.startswith("GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V1")]
    if len(markers) != 1:
        raise GraphDeviceDynamicError("dynamic runner marker is missing or duplicated")
    pattern = re.compile(
        rf"GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V1 status=PASS requests={request_count} "
        rf"same_simulator=1 invoked_{'once' if request_count == 1 else 'twice'}=1 rtl_emitted_once=1 simulator_built_once=1 rejected_before_axi=1 "
        r"simulator_sha256=[0-9a-f]{64} path=artifacts/graph_device_axi4lite_dynamic/run\.[A-Za-z0-9_]{8} "
        r"evidence=rtl-simulation-functional performance=not-measured"
    )
    if pattern.fullmatch(markers[0]) is None or markers[0].split(" path=", 1)[1].split(" ", 1)[0] != \
            f"artifacts/graph_device_axi4lite_dynamic/{session.name}":
        raise GraphDeviceDynamicError("dynamic runner marker is not confined to the retained session")
    return markers[0]


def _run_dynamic(graphs: list[str], seeds: list[int], repository: Path | None, command: str) -> str:
    if len(graphs) not in {1, 2} or len(graphs) != len(seeds):
        raise GraphDeviceDynamicError(f"{command} request count is invalid")
    repo = (repository or _root()).resolve(strict=True)
    first = repo / "artifacts/graph_device_axi4lite_dynamic"
    if first.exists() and (first.is_symlink() or not first.is_dir()):
        raise GraphDeviceDynamicError("dynamic artifact root is unsafe")
    first.mkdir(parents=True, exist_ok=True)
    import tempfile
    session = Path(tempfile.mkdtemp(prefix="run.", dir=first))
    request_roots = [session / f"request-{index}" for index in range(1, len(graphs) + 1)]
    prepared = [prepare_request(root, graph, seed, repo) for root, graph, seed in zip(request_roots, graphs, seeds)]
    if any(item["profile"]["name"] not in {"baseline", "compact"} for item in prepared):
        raise GraphDeviceDynamicError("dynamic profiles are restricted to baseline and compact")
    runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
    try:
        result = subprocess.run(
            [str(runner), *[part for root in request_roots for part in ("--request", str(root))]],
            cwd=repo, text=True, encoding="utf-8", errors="strict", capture_output=True, check=False,
        )
    except (OSError, UnicodeError) as error:
        raise GraphDeviceDynamicError(f"dynamic runner could not start: {error}") from error
    if result.returncode != 0:
        raise GraphDeviceDynamicError("dynamic runner failed")
    marker = _marker(result.stdout, session, len(graphs))
    invocation = "once" if len(graphs) == 1 else "twice"
    if f"requests={len(graphs)}" not in marker or "same_simulator=1" not in marker \
            or f"invoked_{invocation}=1" not in marker:
        raise GraphDeviceDynamicError("dynamic runner did not prove one build and the requested invocations")
    marker_hash = re.search(r"simulator_sha256=([0-9a-f]{64})", marker)
    if marker_hash is None:
        raise GraphDeviceDynamicError("dynamic simulator identity is missing")
    receipts = []
    for root, item, seed in zip(request_roots, prepared, seeds):
        output = root / f"private-output-{item['program']['graph_id']}-seed-{seed}.bin"
        fallback = root / f"fallback-output-{item['program']['graph_id']}-seed-{seed}.bin"
        expected = _word_bytes(graph_oracle(item["descriptor"], input_words(seed)))
        if (root / "request.bin").read_bytes() != item["request"] \
                or (root / "request-oracle.bin").read_bytes() != expected \
                or output.read_bytes() != expected or fallback.read_bytes() != expected:
            raise GraphDeviceDynamicError("dynamic RTL/fallback output differs from independent oracle")
        simulator = (root / "simulator.bin").read_bytes()
        simulator_sha = hashlib.sha256(simulator).hexdigest()
        if simulator_sha != marker_hash.group(1) or (root / "simulator.sha256").read_text(encoding="ascii").strip() != simulator_sha:
            raise GraphDeviceDynamicError("dynamic simulator digest is not receipt-bound")
        for name in ("axi-transcript.log", "device.log", "toolchain.txt", "source.manifest", "abi.manifest", "rtl.manifest"):
            if not (root / name).is_file():
                raise GraphDeviceDynamicError(f"dynamic evidence is missing {name}")
        receipt_path = root / "dynamic-receipt.json"
        receipt = {"schema": SCHEMA.replace("request", "receipt"), "status": "complete",
                   "graph_id": item["program"]["graph_id"], "seed": seed,
                   "affine": item["profile"]["name"], "descriptor_sha256": item["metadata"]["descriptor_sha256"],
                   "program_sha256": item["program"]["program_sha256"],
                   "request_sha256": hashlib.sha256((root / "request.bin").read_bytes()).hexdigest(),
                   "oracle_sha256": hashlib.sha256(expected).hexdigest(),
                   "fallback_sha256": hashlib.sha256(fallback.read_bytes()).hexdigest(),
                   "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                   "simulator_sha256": simulator_sha,
                   "rtl_manifest_sha256": hashlib.sha256((root / "rtl.manifest").read_bytes()).hexdigest(),
                   "source_manifest_sha256": hashlib.sha256((root / "source.manifest").read_bytes()).hexdigest(),
                   "abi_manifest_sha256": hashlib.sha256((root / "abi.manifest").read_bytes()).hexdigest(),
                   "toolchain_sha256": hashlib.sha256((root / "toolchain.txt").read_bytes()).hexdigest(),
                   "trace_sha256": hashlib.sha256((root / "axi-transcript.log").read_bytes()).hexdigest(),
                   "evidence_class": "rtl-simulation-functional", "performance": "not-measured"}
        try:
            _write_new(receipt_path, (json.dumps(receipt, sort_keys=True) + "\n").encode("ascii"))
        except FileExistsError as error:
            raise GraphDeviceDynamicError("dynamic receipt is append-once") from error
        receipts.append(receipt)
    if len(receipts) == 2 and receipts[0]["simulator_sha256"] != receipts[1]["simulator_sha256"]:
        raise GraphDeviceDynamicError("dynamic requests used different simulator binaries")
    lines = [
        f"GraphDevice-AXI4LITE-DYNAMIC-RUN-{command.removeprefix('dynamic-run').upper().lstrip('-') or 'SINGLE'}-V1 status=PASS requests={len(graphs)}",
        *[f"Request {index} graph={item['program']['graph_id']} seed={seed} oracle=PASS fallback=PASS"
          for index, (item, seed) in enumerate(zip(prepared, seeds), start=1)],
        marker,
        f"Same simulator=PASS invoked_{invocation}=PASS receipts={len(receipts)}",
        "Evidence class=rtl-simulation-functional",
        "Performance=not-measured",
    ]
    return "\n".join(lines)


def run_dynamic(graph: str, seed: int, repository: Path | None = None) -> str:
    if graph in CATALOGUE:
        raise GraphDeviceDynamicError("dynamic-run graph must be outside the frozen catalogue")
    return _run_dynamic([graph], [seed], repository, "dynamic-run")


def run_dynamic_pair(graphs: list[str], seeds: list[int], repository: Path | None = None) -> str:
    if len(graphs) != 2 or len(seeds) != 2:
        raise GraphDeviceDynamicError("dynamic-run-pair requires exactly two --descriptor and two --seed values")
    if graphs[0] not in CATALOGUE:
        raise GraphDeviceDynamicError("first dynamic graph must be a frozen catalogue descriptor")
    if graphs[1] in CATALOGUE:
        raise GraphDeviceDynamicError("second dynamic graph must be outside the frozen catalogue")
    return _run_dynamic(graphs, seeds, repository, "dynamic-run-pair")
