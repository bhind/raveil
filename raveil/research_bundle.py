from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any, Iterable

from .experiment_schema import BUNDLE_SCHEMA


RUN_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{7,12}-[0-9a-f]{8}$")
SENSITIVE_RE = re.compile(
    r"(?:/Users/|/home/|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|client_secret|refresh_token|password\s*[=:]|\"username\"\s*:|serial(?:_number)?\s*[=:])",
    re.IGNORECASE,
)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_hash(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def make_run_id(git_sha: str, manifest_digest: str, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{git_sha[:9]}-{manifest_digest[:8]}"


@dataclass(frozen=True)
class BundleFile:
    path: str
    size: int
    sha256: str


class ResearchBundle:
    def __init__(self, artifact_root: Path, experiment_id: str, run_id: str) -> None:
        if not re.fullmatch(r"EXP-[0-9]{4}", experiment_id):
            raise ValueError("invalid experiment ID")
        if not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("invalid run ID")
        self.artifact_root = artifact_root.resolve()
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.path = self.artifact_root / experiment_id / run_id
        self._assert_inside_root(self.path)

    def _assert_inside_root(self, path: Path) -> None:
        try:
            path.resolve().relative_to(self.artifact_root)
        except ValueError as error:
            raise ValueError("bundle path escapes artifact root") from error

    @property
    def sealed(self) -> bool:
        return (self.path / "bundle-manifest.json").exists()

    def create(self) -> None:
        if self.path.exists():
            raise FileExistsError(f"run bundle already exists: {self.run_id}")
        self.path.mkdir(parents=True)

    def require_mutable(self) -> None:
        if self.sealed:
            raise RuntimeError("sealed bundle cannot be changed; create a new RUN-ID")

    def write_json(self, relative: str, value: object) -> None:
        self.require_mutable()
        target = self.path / relative
        self._assert_inside_root(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(canonical_json(value) + "\n", encoding="utf-8")

    def append_jsonl(self, relative: str, value: object) -> None:
        self.require_mutable()
        target = self.path / relative
        self._assert_inside_root(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as output:
            output.write(canonical_json(value) + "\n")

    def _files(self, exclude: set[str] | None = None) -> list[BundleFile]:
        excluded = exclude or set()
        files = []
        for path in sorted(self.path.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"symbolic links are not allowed in a research bundle: {path.name}")
            if not path.is_file():
                continue
            relative = path.relative_to(self.path).as_posix()
            if relative in excluded:
                continue
            files.append(BundleFile(relative, path.stat().st_size, sha256_file(path)))
        return files

    def _scan_sensitive(self, files: Iterable[BundleFile]) -> None:
        for entry in files:
            path = self.path / entry.path
            if path.suffix not in {".json", ".jsonl", ".txt", ".log"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            match = SENSITIVE_RE.search(text)
            if match:
                raise ValueError(f"sensitive or machine-local content in {entry.path}: {match.group(0)}")

    def seal(
        self,
        command: tuple[str, ...],
        tool_versions: dict[str, str],
        environment_signature: dict[str, Any],
    ) -> dict[str, Any]:
        self.require_mutable()
        if not (self.path / "measurement.jsonl").is_file():
            raise RuntimeError("measurement.jsonl is required before sealing")
        initial_files = self._files(exclude={"completion-marker.json", "bundle-manifest.json"})
        self._scan_sensitive(initial_files)
        data_hash = hashlib.sha256(
            canonical_json([asdict(entry) for entry in initial_files]).encode("utf-8")
        ).hexdigest()
        self.write_json(
            "completion-marker.json",
            {
                "schema": BUNDLE_SCHEMA,
                "experiment_id": self.experiment_id,
                "run_id": self.run_id,
                "data_hash": data_hash,
            },
        )
        files = self._files(exclude={"bundle-manifest.json"})
        self._scan_sensitive(files)
        bundle_hash = hashlib.sha256(
            canonical_json([asdict(entry) for entry in files]).encode("utf-8")
        ).hexdigest()
        value = {
            "schema": BUNDLE_SCHEMA,
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "bundle_hash": bundle_hash,
            "files": [asdict(entry) for entry in files],
            "tool_versions": tool_versions,
            "command": list(command),
            "environment_signature": environment_signature,
            "manifest_excludes_self": True,
        }
        self.write_json("bundle-manifest.json", value)
        for path in sorted(self.path.rglob("*"), reverse=True):
            mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH
            if path.is_dir():
                mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(path, mode)
        os.chmod(self.path, stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        return value

    def verify(self) -> dict[str, Any]:
        manifest_path = self.path / "bundle-manifest.json"
        if not manifest_path.is_file():
            raise RuntimeError("bundle is not sealed")
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_paths = {entry["path"] for entry in value["files"]}
        actual_paths = set()
        for path in self.path.rglob("*"):
            if path.is_symlink():
                raise RuntimeError(f"symbolic link found in sealed bundle: {path.name}")
            if path.is_file() and path != manifest_path:
                actual_paths.add(path.relative_to(self.path).as_posix())
        if actual_paths != expected_paths:
            unexpected = sorted(actual_paths - expected_paths)
            missing = sorted(expected_paths - actual_paths)
            raise RuntimeError(
                f"sealed bundle file set changed: unexpected={unexpected}, missing={missing}"
            )
        for entry in value["files"]:
            path = self.path / entry["path"]
            self._assert_inside_root(path)
            if not path.is_file() or path.stat().st_size != entry["size"]:
                raise RuntimeError(f"bundle file missing or wrong size: {entry['path']}")
            if sha256_file(path) != entry["sha256"]:
                raise RuntimeError(f"bundle hash mismatch: {entry['path']}")
        calculated = hashlib.sha256(canonical_json(value["files"]).encode("utf-8")).hexdigest()
        if calculated != value["bundle_hash"]:
            raise RuntimeError("bundle manifest hash mismatch")
        return value

    def sync(self, remote_root: str, rclone: str = "rclone", config: Path | None = None) -> str:
        self.verify()
        if not remote_root or remote_root.endswith(":"):
            raise ValueError("remote root must include a configured remote and base directory")
        remote = f"{remote_root.rstrip('/')}/{self.experiment_id}/{self.run_id}"
        base = [rclone]
        if config is not None:
            resolved_config = config.resolve()
            git = subprocess.run(
                ("git", "rev-parse", "--show-toplevel"),
                check=False,
                capture_output=True,
                text=True,
            )
            if git.returncode == 0:
                repository = Path(git.stdout.strip()).resolve()
                if resolved_config == repository or repository in resolved_config.parents:
                    raise ValueError("rclone configuration must be outside the repository tree")
            base.extend(("--config", str(config)))
        listing = subprocess.run(
            (*base, "lsf", remote), check=False, capture_output=True, text=True
        )
        if listing.returncode == 0:
            remote_files = set(listing.stdout.splitlines())
            if "completion-marker.json" in remote_files:
                raise FileExistsError("completed remote run bundle already exists; overwrite refused")
        elif listing.returncode != 3:
            raise RuntimeError(listing.stderr.strip() or "remote preflight failed")
        source = str(self.path)
        copy = subprocess.run(
            (*base, "copy", source, remote, "--immutable", "--exclude", "completion-marker.json"),
            check=False,
            capture_output=True,
            text=True,
        )
        if copy.returncode != 0:
            raise RuntimeError(copy.stderr.strip() or "rclone copy failed")
        check = subprocess.run(
            (*base, "check", source, remote, "--download", "--one-way", "--exclude", "completion-marker.json"),
            check=False,
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            raise RuntimeError(check.stderr.strip() or "remote hash/size verification failed")
        marker = subprocess.run(
            (
                *base,
                "copyto",
                str(self.path / "completion-marker.json"),
                f"{remote}/completion-marker.json",
                "--immutable",
            ),
            check=False,
            capture_output=True,
            text=True,
        )
        if marker.returncode != 0:
            raise RuntimeError(marker.stderr.strip() or "completion marker upload failed")
        remote_marker = subprocess.run(
            (*base, "cat", f"{remote}/completion-marker.json"),
            check=False,
            capture_output=True,
            text=True,
        )
        local_marker = (self.path / "completion-marker.json").read_text(encoding="utf-8")
        if remote_marker.returncode != 0 or remote_marker.stdout != local_marker:
            raise RuntimeError("remote completion marker verification failed")
        return remote
