"""Bounded cooperative local build reuse; never stores execution results."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

IMAGE = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
MEMBERS = ("simulator.bin", "source.manifest", "rtl.manifest", "abi.manifest", "toolchain.txt", "identity.json")
HEADERS = ("graph_device_abi_generated.h", "graph_device_affine_generated.h",
           "graph_device_dag_generated.h", "graph_device_axi4lite_aperture_generated.h")
LIMIT = 16 * 1024 * 1024
MAX_ENTRIES = 8
SCHEMA = "raveil.compiled-simulator-bundle/v1"


class BuildCacheError(ValueError):
    """A cache is unsafe or inconsistent; explicit fresh mode remains available."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def _digest(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise BuildCacheError("invalid build identity")
    return value


def _directory(path: Path, *, private: bool = True) -> None:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() \
            or (private and info.st_mode & 0o077):
        raise BuildCacheError("unsafe cache directory")


def _read(path: Path, limit: int = LIMIT) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            raise BuildCacheError("unsafe or oversized build member")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            value = stream.read(limit + 1)
        if len(value) > limit or len(value) != info.st_size:
            raise BuildCacheError("build member changed while reading")
        return value
    finally:
        os.close(fd)


def _write(path: Path, value: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(value)


def _payloads(root: Path) -> dict[str, bytes]:
    payloads = {name: _read(root / name) for name in MEMBERS}
    if sum(map(len, payloads.values())) > LIMIT:
        raise BuildCacheError("build bundle exceeds byte budget")
    return payloads


def _manifest(key: str, payloads: dict[str, bytes]) -> dict:
    return {"schema": SCHEMA, "key": _digest(key), "members": {
        name: {"sha256": _sha(data), "bytes": len(data)} for name, data in payloads.items()}}


class BuildCache:
    def __init__(self, root: Path):
        self.root = root
        # The caller supplies a repository-owned root, never a project recipe path.
        for parent in reversed(root.parents):
            if parent.is_symlink():
                raise BuildCacheError("symlink cache ancestor")
        root.mkdir(mode=0o700, exist_ok=True)
        _directory(root)

    def read(self, key: str) -> dict[str, bytes] | None:
        entry = self.root / _digest(key)
        try:
            _directory(entry)
        except FileNotFoundError:
            return None
        if {p.name for p in entry.iterdir()} != {*MEMBERS, "manifest.json"}:
            raise BuildCacheError("unexpected build bundle members")
        payloads = _payloads(entry)
        if _sha(payloads["identity.json"]) != key:
            raise BuildCacheError("bundle belongs to another build identity")
        if _read(entry / "manifest.json", 8192) != _json(_manifest(key, payloads)):
            raise BuildCacheError("build bundle digest mismatch")
        return payloads

    def stage(self, key: str, target: Path) -> bool:
        _directory(target.parent)
        payloads = self.read(key)
        if payloads is None:
            return False
        target.mkdir(mode=0o700)
        for name, data in payloads.items():
            _write(target / name, data)
            if _read(target / name) != data:
                raise BuildCacheError("staged build differs")
        # sha256sum accepts this fixed-name manifest inside the offline container.
        _write(target / "bundle.sha256", "".join(
            f"{_sha(payloads[name])}  {name}\n" for name in MEMBERS).encode("ascii"))
        return True

    def publish(self, key: str, source: Path) -> bool:
        _digest(key)
        payloads = _payloads(source)
        if _sha(payloads["identity.json"]) != key:
            raise BuildCacheError("publication identity mismatch")
        fd = os.open(self.root / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                raise BuildCacheError("unsafe build cache lock")
            fcntl.flock(fd, fcntl.LOCK_EX)
            if self.read(key) is not None:
                return False
            entries = list(self.root.iterdir())
            if any(p.name != "lock" and not re.fullmatch(r"[0-9a-f]{64}|stage\.[A-Za-z0-9_]+", p.name)
                   for p in entries):
                raise BuildCacheError("unexpected cache root member")
            # Abandoned stages consume capacity; never auto-delete them.
            if len([p for p in entries if p.name != "lock"]) >= MAX_ENTRIES:
                return False
            stage = Path(tempfile.mkdtemp(prefix="stage.", dir=self.root))
            for name, data in payloads.items():
                _write(stage / name, data)
            _write(stage / "manifest.json", _json(_manifest(key, payloads)))
            os.rename(stage, self.root / key)  # under the cooperative publication lock
            return True
        finally:
            os.close(fd)


def dependency_digest(repo: Path) -> str:
    result = subprocess.run([
        "docker", "run", "--rm", "--network", "none", "--platform", "linux/amd64",
        "--security-opt", "no-new-privileges=true", "--pull", "never",
        "--mount", "type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly",
        "--mount", f"type=bind,source={repo},target=/repo,readonly", IMAGE,
        "bash", "/repo/hardware/chisel/build-cache-dependencies.sh"],
        capture_output=True, text=True, check=False)
    if result.returncode:
        raise BuildCacheError("offline dependency identity probe failed")
    return _digest(result.stdout.strip())


def identity(repo: Path, request: Path, dependencies: str) -> bytes:
    # Lazy import avoids the sealed module's existing dependency on dynamic.py.
    from .graph_device_dynamic_sealed import SOURCE_PATHS
    extra = ("raveil/graph_device_build_cache.py", "hardware/chisel/build-cache-dependencies.sh")
    sources = {name: _sha(_read(repo / name)) for name in (*SOURCE_PATHS, *extra)}
    headers = {name: _sha(_read(request / name)) for name in HEADERS}
    return _json({"schema": SCHEMA, "image": IMAGE, "dependencies": _digest(dependencies),
                  "sources": sources, "headers": headers})


def prepare(repo: Path, session: Path, request: Path) -> dict:
    dependencies = dependency_digest(repo)
    provenance = identity(repo, request, dependencies)
    key = _sha(provenance)
    _write(request / "identity.json", provenance)
    _write(session / "build-identity.json", provenance)
    cache = BuildCache(repo / "artifacts" / "compiled-simulator-cache-v1")
    hit = cache.stage(key, session / "reuse-build")
    _write(session / "build-dependencies.sha256", (dependencies + "\n").encode("ascii"))
    return {"cache": cache, "key": key, "dependencies": dependencies, "hit": hit}


def finish(context: dict, repo: Path, session: Path, request: Path) -> None:
    if dependency_digest(repo) != context["dependencies"]:
        raise BuildCacheError("dependency identity changed during execution")
    if _sha(identity(repo, request, context["dependencies"])) != context["key"]:
        raise BuildCacheError("source identity changed during execution")
    stored = False if context["hit"] else context["cache"].publish(context["key"], request)
    _write(session / "build-reuse-receipt.json", _json({
        "schema": "raveil.build-reuse-receipt/v1", "key": context["key"],
        "image": IMAGE, "dependencies": context["dependencies"],
        "cache_hit": context["hit"], "published": stored,
        "elaborations": int(not context["hit"]), "builds": int(not context["hit"]),
        "execution_reused": False, "performance": "not-measured"}))
