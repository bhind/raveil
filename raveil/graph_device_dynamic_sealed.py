"""Fail-closed, descriptor-once sealing for bounded dynamic Graph requests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import struct
import subprocess
import tempfile
import re
import secrets
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from .graph_device_dag import compile_descriptor, graph_oracle
from .graph_device_dynamic import (
    AFFINE_WORDS, HEADER_BYTES, INPUT_WORDS, PROGRAM_WORDS, REQUEST_BYTES,
    GraphDeviceDynamicError, GRAPH_ID_RE, _profile_for, _profile_payload, _request_bytes,
    _word_bytes, _marker, _write_new,
)
from .graph_device_affine import _generated_header as affine_header, profiles
from .graph_device_axi4lite import _header as aperture_header
from .graph_device_dag import _generated_header as dag_header, compile_artifact
from .graph_device_mvp import _generated_header as device_abi_header, compile_artifact as compile_device_artifact, load_device_abi
from .riscv_stencil_signature import input_words


SCHEMA = "raveil.graph-device-dynamic-sealed/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INVENTORY = ("SEALED", "affine.bin", "descriptor.json", "graph_device_abi_generated.h", "graph_device_affine_generated.h", "graph_device_axi4lite_aperture_generated.h", "graph_device_dag_generated.h", "input.bin", "manifest.json", "oracle.bin", "program.bin", "request.bin", "seed-1.bin", "source.manifest")
PAYLOADS = tuple(name for name in INVENTORY if name not in {"SEALED", "manifest.json"})
SOURCE_PATHS = (
    "contracts/graph_device_abi_v1.json", "contracts/graph_device_install_abi_v1.json",
    "contracts/graph_device_dynamic_request_v1.json", "contracts/graph_device_dynamic_request_v2.json",
    "contracts/graph_device_dynamic_request_v3.json", "contracts/graph_device_program_v2.json",
    "contracts/graph_device_program_v3.json",
    "contracts/graph_device_program_install_abi_v1.json",
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "contracts/graph_device_dynamic_sealed_v1.json", "contracts/graph_device_dynamic_sealed_v2.json",
    "raveil/graph_device_dag.py", "raveil/graph_device_dynamic.py",
    "raveil/graph_device_dynamic_sealed.py", "raveil/riscv_stencil_signature.py",
    "raveil/graph_device_affine.py", "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_mvp.py", "hardware/chisel/run-graph-device-axi4lite-dynamic.sh",
    "hardware/chisel/run-graph-device-axi4lite-dynamic-in-container.sh",
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/graph_device_dag_runtime.h", "hardware/chisel/graph_device_dag_runtime.cpp",
    "hardware/chisel/graph_device_runtime.h", "hardware/chisel/graph_device_runtime.cpp",
    "hardware/chisel/graph_device_affine_runtime.h", "hardware/chisel/graph_device_affine_runtime.cpp",
    "hardware/chisel/graph_device_axi4lite_transport.h", "hardware/chisel/Dockerfile",
    "hardware/chisel/graph_device_axi4lite_dynamic_verilator.cpp",
    "linux/include/raveil_graph_device_dynamic_request.h", "linux/src/raveil_graph_device_dynamic_request.cpp",
    "linux/src/raveil-graph-device-dynamic-uio-run.cpp", "raveil/graph_device_uio_dry_run.py",
    "raveil/static_region.py",
)


class GraphDeviceDynamicSealError(GraphDeviceDynamicError):
    """A sealed dynamic request is absent, mutable, or identity-inconsistent."""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _relative_parts(relative: str) -> tuple[str, ...]:
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in {"", ".", ".."} for part in parts):
        raise GraphDeviceDynamicSealError("repository relative path is invalid")
    return parts


def _read_repo_file(repo_fd: int, relative: str, limit: int = 65536) -> bytes:
    """Open a repository file component-by-component below an already opened root."""
    parts = _relative_parts(relative)
    parent = os.dup(repo_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, _directory_flags(), dir_fd=parent)
            os.close(parent); parent = next_fd
        return _read_at(parent, parts[-1], limit)
    except OSError as error:
        raise GraphDeviceDynamicSealError("repository source cannot be read no-follow") from error
    finally:
        os.close(parent)


def _source_snapshot(repo_fd: int) -> tuple[bytes, str]:
    rows = []
    for relative in SOURCE_PATHS:
        payload = _read_repo_file(repo_fd, relative)
        rows.append({"path": relative, "size": len(payload), "sha256": _sha(payload)})
    manifest = (json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    # The compiler identity is exactly the immutable source-manifest snapshot.
    return manifest, _sha(manifest)


def _sealed_parent(repo: Path) -> Path:
    """Private test seam; production callers cannot select an output directory."""
    return repo / "artifacts/graph_device_dynamic_sealed"


def _dynamic_parent(repo: Path) -> Path:
    """Private test seam; production CLI fixes the runner artifact root."""
    return repo / "artifacts/graph_device_axi4lite_dynamic"


def _open_dynamic_parent(repo: Path) -> tuple[Path, int]:
    parent = Path(_dynamic_parent(repo)).absolute()
    production = repo / "artifacts" / "graph_device_axi4lite_dynamic"
    if parent == production:
        root = _open_dir_path(repo)
        try:
            try: artifacts = os.open("artifacts", _directory_flags(), dir_fd=root)
            except FileNotFoundError: artifacts = _mkdir_open_at(root, "artifacts")
            try: dynamic = os.open("graph_device_axi4lite_dynamic", _directory_flags(), dir_fd=artifacts)
            except FileNotFoundError: dynamic = _mkdir_open_at(artifacts, "graph_device_axi4lite_dynamic")
            os.close(artifacts); return parent, dynamic
        finally: os.close(root)
    return parent, _open_dir_path(parent)


def _directory_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


def _open_dir_path(path: Path) -> int:
    """Open every absolute directory component without resolving a symlink."""
    if not path.is_absolute():
        raise GraphDeviceDynamicSealError("trusted directory path must be absolute")
    fd = os.open("/", _directory_flags())
    try:
        for part in path.parts[1:]:
            if part in {"", ".", ".."}:
                raise GraphDeviceDynamicSealError("trusted directory component is invalid")
            next_fd = os.open(part, _directory_flags(), dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except Exception:
        os.close(fd)
        raise


def _mkdir_open_at(parent: int, name: str, mode: int = 0o700) -> int:
    if not name or "/" in name or name in {".", ".."}:
        raise GraphDeviceDynamicSealError("direct child name is invalid")
    os.mkdir(name, mode, dir_fd=parent)
    return os.open(name, _directory_flags(), dir_fd=parent)


def _open_sealed_parent(repo: Path) -> tuple[Path, int]:
    """Open production parent below repo with mkdirat, or an existing test seam."""
    parent = Path(_sealed_parent(repo)).absolute()
    production = repo / "artifacts" / "graph_device_dynamic_sealed"
    if parent == production:
        root = _open_dir_path(repo)
        try:
            try: artifacts = os.open("artifacts", _directory_flags(), dir_fd=root)
            except FileNotFoundError: artifacts = _mkdir_open_at(root, "artifacts")
            try: sealed = os.open("graph_device_dynamic_sealed", _directory_flags(), dir_fd=artifacts)
            except FileNotFoundError: sealed = _mkdir_open_at(artifacts, "graph_device_dynamic_sealed")
            os.close(artifacts)
            return parent, sealed
        finally:
            os.close(root)
    return parent, _open_dir_path(parent)


def _read_once(path: Path, limit: int = 65536) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
                raise GraphDeviceDynamicSealError("descriptor is not a bounded regular file")
            chunks = []
            while True:
                block = os.read(fd, 65537)
                if not block:
                    break
                chunks.append(block)
            payload = b"".join(chunks)
            after = os.fstat(fd)
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) or len(payload) != info.st_size:
                raise GraphDeviceDynamicSealError("descriptor changed during the one-time read")
            return payload
        finally:
            os.close(fd)
    except OSError as error:
        raise GraphDeviceDynamicSealError("descriptor cannot be read without following links") from error


def _write_at(directory: int, name: str, payload: bytes) -> None:
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise GraphDeviceDynamicSealError("sealed payload write failed")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def seal(graph: str, seed: int, repository: Path) -> dict[str, Any]:
    repo = Path(repository).absolute()
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise GraphDeviceDynamicSealError("sealed seed is outside u32")
    try:
        repo_fd = _open_dir_path(repo)
        descriptor_bytes = _read_repo_file(repo_fd, graph)
        source_manifest, source_identity = _source_snapshot(repo_fd)
    except (OSError, GraphDeviceDynamicSealError) as error:
        raise GraphDeviceDynamicSealError("sealed descriptor/source admission is unsafe") from error
    finally:
        try: os.close(repo_fd)
        except UnboundLocalError: pass
    try:
        descriptor = json.loads(descriptor_bytes.decode("ascii"))
        program = compile_descriptor(descriptor)
    except (UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise GraphDeviceDynamicSealError(f"sealed descriptor admission failed: {error}") from error
    if program["payload"][1] not in {1, 2}:
        raise GraphDeviceDynamicSealError(
            "sealed transport admits only program versions 1 and 2; "
            "version 3 remains simulation-only"
        )
    profile = _profile_for(program)
    request = _request_bytes(program, profile, seed)
    payloads = {
            "descriptor.json": descriptor_bytes,
            "program.bin": _word_bytes(program["payload"]),
            "affine.bin": _word_bytes(profile.get("payload_words", _profile_payload(profile))),
            "input.bin": _word_bytes(input_words(seed)),
            "seed-1.bin": _word_bytes(input_words(1)),
            "source.manifest": source_manifest,
            "oracle.bin": _word_bytes(graph_oracle(descriptor, input_words(seed))),
            "request.bin": request,
            "graph_device_abi_generated.h": device_abi_header(compile_device_artifact(), load_device_abi(repo)),
            "graph_device_affine_generated.h": affine_header(),
            "graph_device_dag_generated.h": dag_header(compile_artifact(repo)),
            "graph_device_axi4lite_aperture_generated.h": aperture_header(),
        }
    # Refuse a source replacement that raced compilation/header generation.
    try:
        repo_fd = _open_dir_path(repo)
        final_source_manifest, final_source_identity = _source_snapshot(repo_fd)
    finally:
        try: os.close(repo_fd)
        except UnboundLocalError: pass
    if (final_source_manifest, final_source_identity) != (source_manifest, source_identity):
        raise GraphDeviceDynamicSealError("sealed compiler source changed during admission")
    version = int(program["payload"][1])
    manifest = {
            "schema": SCHEMA if version == 1 else "raveil.graph-device-dynamic-sealed/v2", "version": version, "graph": graph, "graph_id": program["graph_id"],
            "seed": seed, "affine": profile["name"], "request_sha256": _sha(request),
            "descriptor_sha256": _sha(descriptor_bytes), "program_sha256": program["program_sha256"],
            "compiler_source_sha256": source_identity,
            "files": {name: {"size": len(payload), "sha256": _sha(payload)} for name, payload in sorted(payloads.items())},
        }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    digest = _sha(manifest_bytes)
    # The production parent is created fd-relative; test seams must already be a
    # real non-symlink directory.
    try:
        parent, parent_fd = _open_sealed_parent(repo)
        directory = _mkdir_open_at(parent_fd, digest)
    except FileExistsError as error:
        raise GraphDeviceDynamicSealError("sealed destination already exists") from error
    except OSError as error:
        raise GraphDeviceDynamicSealError("sealed destination cannot be exclusively created") from error
    try:
        for name in (*PAYLOADS, "manifest.json"):
            _write_at(directory, name, manifest_bytes if name == "manifest.json" else payloads[name])
        _write_at(directory, "SEALED", (_sha(manifest_bytes) + "\n").encode("ascii"))
        os.fsync(directory)
    finally:
        os.close(directory)
        os.close(parent_fd)
    destination = parent / digest
    return {**manifest, "path": str(destination), "manifest_sha256": digest}


def _read_at(directory: int, name: str, limit: int = 65536) -> bytes:
    try:
        fd = os.open(name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
                raise GraphDeviceDynamicSealError("sealed inventory entry is unsafe")
            chunks = []
            remaining = info.st_size + 1
            while remaining:
                block = os.read(fd, remaining)
                if not block:
                    break
                chunks.append(block)
                remaining -= len(block)
            data = b"".join(chunks)
            after = os.fstat(fd)
            if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) or len(data) != info.st_size:
                raise GraphDeviceDynamicSealError("sealed inventory entry changed while read")
            return data
        finally:
            os.close(fd)
    except OSError as error:
        raise GraphDeviceDynamicSealError("sealed inventory cannot be opened no-follow") from error


def _read_evidence(path: Path, limit: int = 65536) -> bytes:
    """Read a runner-created regular evidence leaf without following links."""
    return _read_once(path, limit)


def _leaf_identity(directory: int, name: str) -> tuple[int, int, int, int, int, int, int]:
    info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _expected_runner_source_manifest(verified: dict[str, Any]) -> bytes:
    rows = json.loads(verified["files"]["source.manifest"].decode("ascii"))
    source = {row["path"]: row["sha256"] for row in rows}
    compiled = ("GraphDeviceAxi4LiteTop.scala", "StaticStencilRegion.scala", "OwnedFixedLatencyScratchpad.scala", "GraphDeviceAffineConfigInstaller.scala", "GraphDeviceProgramInstaller.scala", "graph_device_runtime.h", "graph_device_runtime.cpp", "graph_device_affine_runtime.h", "graph_device_affine_runtime.cpp", "graph_device_dag_runtime.h", "graph_device_dag_runtime.cpp", "graph_device_axi4lite_transport.h", "graph_device_axi4lite_dynamic_verilator.cpp")
    chip = ("RaveilFixtureInputProvider.scala", "RaveilStaticStencilCore.scala")
    rows_out = [f"compiled/{name} {source['hardware/chisel/' + name]}" for name in compiled]
    rows_out += [f"compiled/chipyard-overlay/{name} {source['hardware/chisel/chipyard-overlay/' + name]}" for name in chip]
    rows_out += [f"compiled/raveil_graph_device_dynamic_request.h {source['linux/include/raveil_graph_device_dynamic_request.h']}", f"compiled/raveil_graph_device_dynamic_request.cpp {source['linux/src/raveil_graph_device_dynamic_request.cpp']}"]
    for name in ("graph_device_abi_generated.h", "graph_device_affine_generated.h", "graph_device_dag_generated.h", "graph_device_axi4lite_aperture_generated.h"):
        rows_out.append(f"generated/{name} {_sha(verified['files'][name])}")
    orchestration = ("hardware/chisel/Dockerfile", "hardware/chisel/run-graph-device-axi4lite-dynamic.sh", "hardware/chisel/run-graph-device-axi4lite-dynamic-in-container.sh", "contracts/graph_device_dynamic_request_v1.json", "contracts/graph_device_dynamic_request_v2.json", "contracts/graph_device_dynamic_request_v3.json", "contracts/graph_device_program_v2.json", "contracts/graph_device_program_v3.json", "contracts/graph_device_abi_v1.json", "contracts/graph_device_install_abi_v1.json", "contracts/graph_device_program_install_abi_v1.json", "raveil/graph_device_dynamic.py", "raveil/graph_device_dag.py", "raveil/graph_device_affine.py", "raveil/graph_device_mvp.py", "raveil/static_region.py", "raveil/riscv_stencil_signature.py")
    rows_out += [f"orchestration/{name} {source[name]}" for name in orchestration]
    return ("\n".join(sorted(rows_out)) + "\n").encode("ascii")


def _valid_program_words(words: list[int]) -> bool:
    """Independent versioned wire-image check; this is not descriptor lowering."""
    if len(words) != PROGRAM_WORDS or words[0] != 0x52504731 or words[1] not in {1, 2} or words[3] != 8:
        return False
    count = words[2]
    if not 2 <= count <= 16 or any(words[index] for index in range(12 + count, 32)):
        return False
    defined: set[int] = set()
    for index, word in enumerate(words[12:12 + count]):
        opcode, dst = word >> 28, (word >> 25) & 7
        reserved = word & ((1 << 19) - 1)
        if opcode == 1:
            if index == count - 1 or ((word >> 22) & 7) > 4 or word & ((1 << 22) - 1):
                return False
            defined.add(dst)
        elif opcode in {2, 4}:
            left, right = (word >> 22) & 7, (word >> 19) & 7
            if (opcode == 4 and words[1] != 2) or index == count - 1 or left not in defined or right not in defined or reserved:
                return False
            defined.add(dst)
        elif opcode == 3:
            if index != count - 1 or dst not in defined or word & ((1 << 25) - 1):
                return False
        else:
            return False
    return True


def verify(bundle: Path, repository: Path) -> dict[str, Any]:
    repo = Path(repository).absolute()
    parent = Path(_sealed_parent(repo)).absolute()
    supplied = Path(bundle)
    if any(part in {"", ".", ".."} for part in supplied.parts):
        raise GraphDeviceDynamicSealError("sealed bundle path is not canonical")
    candidate = supplied.absolute()
    # Lexical direct-child equality is intentional: resolve() would follow an
    # untrusted symlink before the fd based admission below can reject it.
    if candidate.parent != parent or not candidate.name or "/" in candidate.name:
        raise GraphDeviceDynamicSealError("sealed bundle is not a direct trusted artifact child")
    try:
        parent_fd = _open_dir_path(parent)
        try:
            directory = os.open(candidate.name, _directory_flags(), dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
    except OSError as error:
        raise GraphDeviceDynamicSealError("sealed bundle root is unsafe") from error
    try:
        actual = tuple(sorted(os.listdir(directory)))
        if actual != tuple(sorted(INVENTORY)):
            raise GraphDeviceDynamicSealError("sealed bundle inventory is not closed")
        root_before = os.fstat(directory)
        leaves_before = {name: _leaf_identity(directory, name) for name in INVENTORY}
        files = {name: _read_at(directory, name) for name in INVENTORY}
        root_after = os.fstat(directory)
        leaves_after = {name: _leaf_identity(directory, name) for name in INVENTORY}
        if tuple(sorted(os.listdir(directory))) != actual or \
                (root_before.st_dev, root_before.st_ino, root_before.st_mtime_ns, root_before.st_ctime_ns) != \
                (root_after.st_dev, root_after.st_ino, root_after.st_mtime_ns, root_after.st_ctime_ns) or \
                leaves_before != leaves_after:
            raise GraphDeviceDynamicSealError("sealed bundle inventory changed while read")
    finally:
        os.close(directory)
    if files["SEALED"] != (_sha(files["manifest.json"]) + "\n").encode("ascii"):
        raise GraphDeviceDynamicSealError("sealed manifest identity differs")
    if candidate.name != _sha(files["manifest.json"]):
        raise GraphDeviceDynamicSealError("sealed bundle name differs from manifest identity")
    try:
        manifest = json.loads(files["manifest.json"].decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceDynamicSealError("sealed manifest is invalid") from error
    if set(manifest) != {"schema", "version", "graph", "graph_id", "seed", "affine", "request_sha256", "descriptor_sha256", "program_sha256", "compiler_source_sha256", "files"} \
            or manifest["schema"] not in {SCHEMA, "raveil.graph-device-dynamic-sealed/v2"} or manifest["version"] not in {1, 2} \
            or type(manifest["graph"]) is not str or _relative_parts(manifest["graph"]) != Path(manifest["graph"]).parts \
            or type(manifest["graph_id"]) is not str or GRAPH_ID_RE.fullmatch(manifest["graph_id"]) is None \
            or type(manifest["seed"]) is not int or not 0 <= manifest["seed"] <= 0xffffffff \
            or manifest["affine"] not in {"baseline", "compact"} \
            or any(type(manifest[key]) is not str or SHA256_RE.fullmatch(manifest[key]) is None
                   for key in ("request_sha256", "descriptor_sha256", "program_sha256", "compiler_source_sha256")):
        raise GraphDeviceDynamicSealError("sealed manifest source identity differs")
    if (manifest["version"] == 1) != (manifest["schema"] == SCHEMA):
        raise GraphDeviceDynamicSealError("sealed manifest version pair differs")
    if manifest["files"] != {name: {"size": len(files[name]), "sha256": _sha(files[name])} for name in PAYLOADS}:
        raise GraphDeviceDynamicSealError("sealed payload identity differs")
    try:
        repo_fd = _open_dir_path(repo)
        source_manifest, source_identity = _source_snapshot(repo_fd)
    finally:
        try: os.close(repo_fd)
        except UnboundLocalError: pass
    if manifest["compiler_source_sha256"] != source_identity or files["source.manifest"] != source_manifest:
        raise GraphDeviceDynamicSealError("sealed source manifest differs")
    if len(files["program.bin"]) != PROGRAM_WORDS * 4 or len(files["affine.bin"]) != AFFINE_WORDS * 4 \
            or len(files["input.bin"]) != INPUT_WORDS * 4 or len(files["seed-1.bin"]) != INPUT_WORDS * 4 \
            or len(files["oracle.bin"]) != 256 * 4:
        raise GraphDeviceDynamicSealError("sealed payload size is invalid")
    program = list(struct.unpack("<32I", files["program.bin"]))
    instruction_count = program[2]
    if not _valid_program_words(program) \
            or _sha(_word_bytes([instruction_count, *program[12:12 + instruction_count]])) != manifest["program_sha256"] \
            or list(struct.unpack("<8I", bytes.fromhex(manifest["program_sha256"]))) != program[4:12]:
        raise GraphDeviceDynamicSealError("sealed program digest differs")
    affine = list(struct.unpack("<16I", files["affine.bin"]))
    profile = next((item for item in profiles() if item["name"] == manifest["affine"]), None)
    if profile is None or _word_bytes(profile["payload_words"] if "payload_words" in profile else _profile_payload(profile)) != files["affine.bin"]:
        raise GraphDeviceDynamicSealError("sealed affine payload differs")
    words = list(struct.unpack("<324I", files["input.bin"]))
    if _word_bytes(input_words(manifest["seed"])) != files["input.bin"] or _word_bytes(input_words(1)) != files["seed-1.bin"]:
        raise GraphDeviceDynamicSealError("sealed input payload differs")
    if program[1] != manifest["version"]:
        raise GraphDeviceDynamicSealError("sealed request/program version pair differs")
    request = struct.pack("<8I", 0x52445731, program[1], HEADER_BYTES, 0 if manifest["affine"] == "baseline" else 1,
                          manifest["seed"], PROGRAM_WORDS, AFFINE_WORDS, INPUT_WORDS) + b"\0" * 32 \
        + manifest["graph_id"].encode("ascii") + b"\0" * (32 - len(manifest["graph_id"])) \
        + files["program.bin"] + files["affine.bin"] + files["input.bin"]
    if len(request) != REQUEST_BYTES or request != files["request.bin"] or _sha(request) != manifest["request_sha256"]:
        raise GraphDeviceDynamicSealError("sealed request payload differs")
    if _sha(files["descriptor.json"]) != manifest["descriptor_sha256"]:
        raise GraphDeviceDynamicSealError("sealed descriptor digest differs")
    return {"manifest": manifest, "request": request, "program": program, "affine": affine,
            "input": words, "oracle": files["oracle.bin"], "files": files,
            "seal_sha256": _sha(files["manifest.json"]), "manifest_sha256": _sha(files["manifest.json"])}


def _materialize_verified_at(directory: int, verified: dict[str, Any]) -> None:
    """FD-only equivalent used by execution; no untrusted destination pathname."""
    _write_at(directory, "request.bin", verified["request"])
    _write_at(directory, "request-input.bin", _word_bytes(verified["input"]))
    _write_at(directory, "request-oracle.bin", verified["oracle"])
    os.mkdir("inputs", 0o700, dir_fd=directory)
    inputs = os.open("inputs", _directory_flags(), dir_fd=directory)
    try:
        _write_at(inputs, "seed-1.bin", verified["files"]["seed-1.bin"])
        if verified["manifest"]["seed"] != 1:
            _write_at(inputs, f"seed-{verified['manifest']['seed']}.bin", _word_bytes(verified["input"]))
    finally: os.close(inputs)
    for name in ("graph_device_abi_generated.h", "graph_device_affine_generated.h", "graph_device_dag_generated.h", "graph_device_axi4lite_aperture_generated.h"):
        _write_at(directory, name, verified["files"][name])
    _write_at(directory, "seal-binding.json", (json.dumps({"schema": SCHEMA.replace("sealed", "sealed-replay"), "seal_sha256": verified["seal_sha256"], "manifest_sha256": verified["manifest_sha256"], "request_sha256": verified["manifest"]["request_sha256"]}, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii"))


def run_sealed(bundle: Path, repository: Path) -> dict[str, Any]:
    """Run one sealed request while unconditionally releasing retained FDs."""
    repo = Path(repository).absolute()
    verified = verify(bundle, repo)
    root, root_fd = _open_dynamic_parent(repo)
    with ExitStack() as stack:
        stack.callback(os.close, root_fd)
        return _run_sealed_open(repo, verified, root, root_fd, stack)


def _run_sealed_open(repo: Path, verified: dict[str, Any], root: Path, root_fd: int,
                     stack: ExitStack) -> dict[str, Any]:
    """Run one verified sealed payload through the existing shared RTL runner."""
    session_name = "run." + secrets.token_hex(4)
    try:
        session_fd = _mkdir_open_at(root_fd, session_name)
        stack.callback(os.close, session_fd)
        request_fd = _mkdir_open_at(session_fd, "request-1")
        stack.callback(os.close, request_fd)
    except OSError as error:
        stack.close()
        raise GraphDeviceDynamicSealError("dynamic replay session cannot be exclusively created") from error
    session = root / session_name
    request_root = session / "request-1"
    def close_retained() -> None:
        stack.close()
    _materialize_verified_at(request_fd, verified)
    session_identity = tuple(_leaf_identity(root_fd, session_name)[:3])
    request_identity = tuple(_leaf_identity(session_fd, "request-1")[:3])
    try:
        source_fd = _open_dir_path(repo); runner_sources_before = _source_snapshot(source_fd)
    finally:
        try: os.close(source_fd)
        except UnboundLocalError: pass
    if runner_sources_before[1] != verified["manifest"]["compiler_source_sha256"]:
        close_retained()
        raise GraphDeviceDynamicSealError("sealed source identity drifted before execution")
    runner = repo / "hardware/chisel/run-graph-device-axi4lite-dynamic.sh"
    result = subprocess.run([str(runner), "--request", str(request_root)], cwd=repo,
                            text=True, encoding="utf-8", errors="strict", capture_output=True, check=False)
    if result.returncode != 0:
        close_retained()
        raise GraphDeviceDynamicSealError("sealed dynamic runner failed")
    if tuple(_leaf_identity(root_fd, session_name)[:3]) != session_identity or \
            tuple(_leaf_identity(session_fd, "request-1")[:3]) != request_identity:
        close_retained()
        raise GraphDeviceDynamicSealError("dynamic replay directory identity changed during runner")
    try:
        source_fd = _open_dir_path(repo); runner_sources_after = _source_snapshot(source_fd)
    finally:
        try: os.close(source_fd)
        except UnboundLocalError: pass
    if runner_sources_after != runner_sources_before:
        close_retained()
        raise GraphDeviceDynamicSealError("sealed source identity drifted during execution")
    marker = _marker(result.stdout, session, 1)
    graph_id, seed = verified["manifest"]["graph_id"], verified["manifest"]["seed"]
    expected = verified["oracle"]
    outputs: dict[str, bytes] = {}
    for role, name in (("output", f"private-output-{graph_id}-seed-{seed}.bin"), ("fallback", f"fallback-output-{graph_id}-seed-{seed}.bin")):
        outputs[role] = _read_at(request_fd, name, 4096)
        if outputs[role] != expected:
            close_retained()
            raise GraphDeviceDynamicSealError("sealed RTL/fallback output differs from sealed oracle")
    evidence = {}
    evidence_bytes: dict[str, bytes] = {}
    for name in ("source.manifest", "abi.manifest", "rtl.manifest", "toolchain.txt", "simulator.bin", "simulator.sha256", "axi-transcript.log", "device.log"):
        try:
            limit = 128 * 1024 * 1024 if name == "simulator.bin" else 16 * 1024 * 1024 if name == "axi-transcript.log" else 65536
            evidence_bytes[name] = _read_at(request_fd, name, limit)
            evidence[name.replace(".", "_") + "_sha256"] = _sha(evidence_bytes[name])
        except GraphDeviceDynamicSealError as error:
            close_retained()
            raise GraphDeviceDynamicSealError(f"sealed dynamic evidence is missing {name}") from error
    if evidence_bytes["source.manifest"] != _expected_runner_source_manifest(verified):
        close_retained()
        raise GraphDeviceDynamicSealError("sealed dynamic runner source manifest differs")
    # Verilated executables exceed ordinary request/evidence leaf bounds; retain
    # a separate explicit cap rather than weakening every no-follow read.
    simulator_sha = _sha(evidence_bytes["simulator.bin"])
    if evidence_bytes["simulator.sha256"].decode("ascii").strip() != simulator_sha \
            or simulator_sha not in marker:
        close_retained()
        raise GraphDeviceDynamicSealError("sealed simulator identity is not raw-evidence bound")
    receipt = {"schema": SCHEMA.replace("sealed", "sealed-receipt"), "status": "complete",
               "graph": verified["manifest"]["graph"], "graph_id": graph_id, "seed": seed,
               "affine": verified["manifest"]["affine"],
               "sealed_manifest_sha256": verified["manifest_sha256"], "sealed_bundle_sha256": verified["seal_sha256"],
               "request_sha256": verified["manifest"]["request_sha256"], "program_sha256": verified["manifest"]["program_sha256"],
               "oracle_sha256": _sha(expected), "output_sha256": _sha(outputs["output"]), "fallback_sha256": _sha(outputs["fallback"]),
               "descriptor_sha256": verified["manifest"]["descriptor_sha256"],
               "affine_sha256": verified["manifest"]["files"]["affine.bin"]["sha256"],
               "input_sha256": verified["manifest"]["files"]["input.bin"]["sha256"],
               "compiler_source_sha256": verified["manifest"]["compiler_source_sha256"],
               "source_sha256": verified["manifest"]["compiler_source_sha256"],
               "abi_sha256": evidence["abi_manifest_sha256"], "rtl_sha256": evidence["rtl_manifest_sha256"],
               "toolchain_sha256": evidence["toolchain_txt_sha256"], "simulator_sha256": simulator_sha,
               "axi_trace_sha256": evidence["axi-transcript_log_sha256"], "marker": marker, **evidence,
               "evidence_class": "rtl-simulation-functional", "performance": "not-measured",
               "non_claims": ["no performance measurement", "no FPGA, ASIC, or silicon execution"]}
    _write_at(request_fd, "sealed-dynamic-receipt.json", (json.dumps(receipt, sort_keys=True) + "\n").encode("ascii"))
    os.fsync(request_fd)
    close_retained()
    return receipt
