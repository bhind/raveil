from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import stat
import tempfile
from typing import Callable, Sequence

from .graph_mvp import GraphProgram


IMPORT_SCHEMA = "raveil.graph-import/v1"
MANIFEST_SCHEMA = "raveil.iree-import-manifest/v1"
MAX_SOURCE_BYTES = 128 * 1024
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_DIAGNOSTIC_BYTES = 64 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PINNED_DISTRIBUTIONS = {
    "linux-aarch64": "c9cf39661b92bc0050f4ea9fef7d52a631294443bf2ae5d1978f0b9085be40b8",
    "linux-x86_64": "ac3505591b6b134784eae7bcdf806fc66a2d120a82134b98bd4fbe488fdf84c5",
    "macos-universal2": "2e9fc888b9044662a14eeba01b6302d75a6118f68874699dcf8f9c7e991a4ee2",
}
_PINNED_SOURCE_SHA256 = "72e4409598aeacb0967fdb0e8ae1e7d42d716f973c2e469426ac6b2eb4eae7ce"
_PINNED_SOURCE_SIZE = 1009
_PINNED_TOOL_VERSION = "3.11.0rc20260316"
_PINNED_TOOL_REVISION = "e4a3b0405d7d23554da26403658d0e8c3c5ecf25"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_regular(path: Path, limit: int, kind: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ValueError(f"{kind} must be a readable non-symlink file") from error
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or not (1 <= metadata.st_size <= limit):
            raise ValueError(f"{kind} is outside the regular-file size bound")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) != metadata.st_size or len(data) > limit:
            raise ValueError(f"{kind} changed while reading")
        return data
    finally:
        os.close(descriptor)


def _strict_json(data: bytes) -> dict[str, object]:
    if len(data) > MAX_SOURCE_BYTES or b"\x00" in data:
        raise ValueError("import manifest is oversized or contains NUL")

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(
        data.decode("utf-8"), object_pairs_hook=pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
    )
    if type(value) is not dict:
        raise ValueError("import manifest root must be an object")
    return value


@dataclass(frozen=True)
class ImportRecord:
    importer: str
    importer_version: str
    manifest_sha256: str
    source_media_type: str
    source_license: str
    source_sha256: str
    source_size: int
    tool_name: str
    tool_version: str
    tool_revision: str
    tool_license: str
    expected_distribution_sha256: str
    observed_compiler_sha256: str
    target: str
    artifact_sha256: str
    artifact_size: int
    graph_sha256: str
    evidence_class: str = "compiler-import-correctness"
    schema: str = IMPORT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != IMPORT_SCHEMA:
            raise ValueError("unsupported graph import schema")
        strings = (
            self.importer, self.importer_version, self.source_media_type,
            self.source_license, self.tool_name, self.tool_version,
            self.tool_revision, self.tool_license, self.target,
        )
        if any(type(value) is not str or not value or len(value) > 128 for value in strings):
            raise ValueError("invalid graph import identity")
        if self.evidence_class != "compiler-import-correctness":
            raise ValueError("graph import evidence class is fixed")
        for digest in (
            self.manifest_sha256, self.source_sha256, self.expected_distribution_sha256,
            self.observed_compiler_sha256,
            self.artifact_sha256, self.graph_sha256,
        ):
            if type(digest) is not str or _SHA256.fullmatch(digest) is None:
                raise ValueError("graph import digests must be lowercase SHA-256")
        if type(self.source_size) is not int or not (1 <= self.source_size <= MAX_SOURCE_BYTES):
            raise ValueError("invalid graph import source size")
        if type(self.artifact_size) is not int or not (1 <= self.artifact_size <= MAX_ARTIFACT_BYTES):
            raise ValueError("invalid graph import artifact size")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "ImportRecord":
        if set(value) != set(cls.__dataclass_fields__):
            raise ValueError("graph import record fields do not match schema")
        return cls(**value)  # type: ignore[arg-type]


@dataclass(frozen=True)
class ImportedGraph:
    program: GraphProgram
    record: ImportRecord


Runner = Callable[[Sequence[str], float], subprocess.CompletedProcess[bytes]]


def _run(argv: Sequence[str], timeout: float) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            tuple(argv), check=False, capture_output=True, timeout=timeout,
            env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("pinned IREE compiler timed out") from error


class PinnedIreeImporter:
    def __init__(self, compiler: Path, *, timeout_seconds: float = 30.0,
                 runner: Runner = _run) -> None:
        if not math.isfinite(timeout_seconds) or not (0 < timeout_seconds <= 300):
            raise ValueError("IREE timeout must be finite and between 0 and 300 seconds")
        self.compiler = compiler
        self.timeout_seconds = timeout_seconds
        self.runner = runner

    def import_program(self, manifest_path: Path) -> ImportedGraph:
        if manifest_path.is_symlink():
            raise ValueError("import manifest must be a regular non-symlink file")
        manifest_path = manifest_path.resolve(strict=True)
        manifest_bytes = _read_regular(manifest_path, MAX_SOURCE_BYTES, "import manifest")
        manifest = _strict_json(manifest_bytes)
        expected = {
            "schema", "source", "source_sha256", "source_size", "family", "m", "n", "k",
            "entry_point", "tool_name", "tool_version", "tool_revision",
            "expected_distribution_sha256", "target", "license",
        }
        if set(manifest) != expected or manifest["schema"] != MANIFEST_SCHEMA:
            raise ValueError("IREE import manifest fields or schema do not match")
        for key in ("source", "family", "entry_point", "tool_name", "tool_version",
                    "tool_revision", "target", "license"):
            if type(manifest[key]) is not str or not manifest[key]:
                raise ValueError(f"invalid IREE import manifest field: {key}")
        if manifest["family"] != "gemm" or manifest["entry_point"] != "main":
            raise ValueError("IREE import is outside the admitted canonical module")
        dimensions = tuple(manifest[key] for key in ("m", "n", "k"))
        if dimensions != (8, 8, 8) or any(type(value) is not int for value in dimensions):
            raise ValueError("IREE import dimensions are outside the admitted fixture")
        source_candidate = manifest_path.parent / str(manifest["source"])
        if source_candidate.is_symlink():
            raise ValueError("IREE source escapes its manifest directory")
        source = source_candidate.resolve(strict=True)
        if source.parent != manifest_path.parent or not source.is_file():
            raise ValueError("IREE source escapes its manifest directory")
        source_bytes = _read_regular(source, MAX_SOURCE_BYTES, "IREE source")
        source_size = len(source_bytes)
        if b"\x00" in source_bytes:
            raise ValueError("IREE source is oversized or contains NUL")
        if type(manifest["source_size"]) is not int or manifest["source_size"] != len(source_bytes):
            raise ValueError("IREE source size does not match its manifest")
        if (
            manifest["source_sha256"] != _PINNED_SOURCE_SHA256
            or manifest["source_size"] != _PINNED_SOURCE_SIZE
            or _sha256(source_bytes) != _PINNED_SOURCE_SHA256
        ):
            raise ValueError("IREE source digest does not match its manifest")
        if manifest["license"] != "Apache-2.0":
            raise ValueError("IREE fixture license is not admitted")
        if (
            manifest["tool_name"] != "iree-base-compiler"
            or manifest["tool_version"] != _PINNED_TOOL_VERSION
            or manifest["tool_revision"] != _PINNED_TOOL_REVISION
            or manifest["target"] != "local-vmvx"
        ):
            raise ValueError("IREE tool pin does not match the admitted compiler")
        distributions = manifest["expected_distribution_sha256"]
        expected_distributions = {"linux-aarch64", "linux-x86_64", "macos-universal2"}
        if (
            type(distributions) is not dict
            or set(distributions) != expected_distributions
            or distributions != _PINNED_DISTRIBUTIONS
        ):
            raise ValueError("IREE distribution digest map does not match")
        if any(type(value) is not str or _SHA256.fullmatch(value) is None
               for value in distributions.values()):
            raise ValueError("invalid IREE distribution digest")
        system = platform.system()
        machine = platform.machine()
        distribution_key = (
            "macos-universal2" if system == "Darwin" else
            f"linux-{'aarch64' if machine in {'arm64', 'aarch64'} else 'x86_64'}"
            if system == "Linux" and machine in {"arm64", "aarch64", "x86_64", "amd64"}
            else ""
        )
        if distribution_key not in distributions:
            raise RuntimeError("no pinned IREE distribution exists for this host")

        if not self.compiler.is_absolute():
            raise ValueError("IREE compiler must be an absolute regular non-symlink file")
        compiler_bytes = _read_regular(self.compiler, MAX_SOURCE_BYTES, "IREE compiler entrypoint")
        observed_compiler_sha256 = _sha256(compiler_bytes)
        version = self.runner((str(self.compiler), "--version"), self.timeout_seconds)
        if version.returncode != 0 or len(version.stdout) + len(version.stderr) > MAX_DIAGNOSTIC_BYTES:
            raise RuntimeError("pinned IREE compiler version preflight failed")
        version_text = (version.stdout + version.stderr).decode("utf-8", "strict")
        expected_version = (
            f"IREE compiler version {_PINNED_TOOL_VERSION} @ {_PINNED_TOOL_REVISION}"
        )
        if expected_version not in {line.strip() for line in version_text.splitlines()}:
            raise RuntimeError("pinned IREE compiler version does not match")

        with tempfile.TemporaryDirectory(prefix="raveil-iree-") as directory:
            copied_source = Path(directory) / "module.mlir"
            copied_source.write_bytes(source_bytes)
            artifact = Path(directory) / "module.vmfb"
            argv = (
                str(self.compiler), str(copied_source),
                "--iree-hal-target-device=local",
                "--iree-hal-local-target-device-backends=vmvx",
                f"-o={artifact}",
            )
            completed = self.runner(argv, self.timeout_seconds)
            if completed.returncode != 0:
                raise RuntimeError("pinned IREE compiler rejected the canonical source")
            if len(completed.stdout) + len(completed.stderr) > MAX_DIAGNOSTIC_BYTES:
                raise RuntimeError("pinned IREE compiler diagnostics exceeded the bound")
            try:
                artifact_bytes = _read_regular(
                    artifact, MAX_ARTIFACT_BYTES, "pinned IREE compiler artifact"
                )
            except ValueError as error:
                raise RuntimeError(str(error)) from error

        program = GraphProgram.create("gemm", 8, 8, 8)
        record = ImportRecord(
            "raveil.iree-importer", "1", _sha256(manifest_bytes), "text/x-mlir",
            str(manifest["license"]), _sha256(source_bytes), len(source_bytes),
            str(manifest["tool_name"]), str(manifest["tool_version"]),
            str(manifest["tool_revision"]), "Apache-2.0 WITH LLVM-exception",
            str(distributions[distribution_key]),
            observed_compiler_sha256,
            str(manifest["target"]), _sha256(artifact_bytes), len(artifact_bytes),
            program.identity,
        )
        return ImportedGraph(program, record)
