"""Bounded application-level workspace containment for the Native CLI."""

from __future__ import annotations

import os
import stat as stat_module
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


MAX_PATH_BYTES = 4096
MAX_FILE_BYTES = 64 * 1024
MAX_DIRECTORY_ENTRIES = 256


class WorkspaceError(ValueError):
    """A bounded, user-facing workspace operation failure."""


@dataclass(frozen=True)
class WorkspaceStat:
    path: str
    kind: str
    size: int
    readable: bool
    writable: bool


class NativeWorkspace:
    """Map virtual POSIX paths into one fixed host directory.

    This is application-level containment, not an OS security boundary. T-0100
    owns descriptor-relative hardening and platform-enforced isolation.
    """

    def __init__(self, root: Path | str) -> None:
        candidate = Path(root).expanduser()
        try:
            root_lstat = candidate.lstat()
        except OSError as exc:
            raise WorkspaceError(f"workspace is unavailable: {exc.strerror}") from exc
        if stat_module.S_ISLNK(root_lstat.st_mode):
            raise WorkspaceError("workspace root must not be a symlink")
        if not stat_module.S_ISDIR(root_lstat.st_mode):
            raise WorkspaceError("workspace root must be an existing directory")
        try:
            self._root = candidate.resolve(strict=True)
            root_stat = self._root.stat()
        except OSError as exc:
            raise WorkspaceError(f"workspace is unavailable: {exc.strerror}") from exc
        self._root_identity = (root_stat.st_dev, root_stat.st_ino)
        self._cwd_parts: tuple[str, ...] = ()

    @property
    def root(self) -> Path:
        return self._root

    def _check_root(self) -> None:
        try:
            current = self._root.lstat()
        except OSError as exc:
            raise WorkspaceError("workspace root is no longer available") from exc
        if (
            stat_module.S_ISLNK(current.st_mode)
            or not stat_module.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != self._root_identity
        ):
            raise WorkspaceError("workspace root was replaced")

    @staticmethod
    def _check_text_path(path: str) -> None:
        if not isinstance(path, str) or not path:
            raise WorkspaceError("path must not be empty")
        if "\x00" in path:
            raise WorkspaceError("path contains NUL")
        if len(path.encode("utf-8")) > MAX_PATH_BYTES:
            raise WorkspaceError(f"path exceeds {MAX_PATH_BYTES} bytes")

    def _parts(self, path: str) -> tuple[str, ...]:
        self._check_text_path(path)
        parsed = PurePosixPath(path)
        raw_parts = parsed.parts[1:] if parsed.is_absolute() else parsed.parts
        base = () if parsed.is_absolute() else self._cwd_parts
        parts = list(base)
        for component in raw_parts:
            if component in ("", "."):
                continue
            if component == "..":
                raise WorkspaceError("parent traversal '..' is not allowed")
            if "/" in component:
                raise WorkspaceError("invalid path component")
            parts.append(component)
        return tuple(parts)

    @staticmethod
    def _virtual(parts: tuple[str, ...]) -> str:
        return "/" if not parts else "/" + "/".join(parts)

    def _walk_existing(self, parts: tuple[str, ...]) -> Path:
        self._check_root()
        current = self._root
        for index, component in enumerate(parts):
            current = current / component
            try:
                item = current.lstat()
            except FileNotFoundError as exc:
                raise WorkspaceError(f"path does not exist: {self._virtual(parts)}") from exc
            except OSError as exc:
                raise WorkspaceError(f"path is unavailable: {exc.strerror}") from exc
            if stat_module.S_ISLNK(item.st_mode):
                raise WorkspaceError("symlinks are not allowed in workspace paths")
            if index < len(parts) - 1 and not stat_module.S_ISDIR(item.st_mode):
                raise WorkspaceError("path component is not a directory")
        return current

    def _new_leaf(self, path: str) -> tuple[tuple[str, ...], Path]:
        parts = self._parts(path)
        if not parts:
            raise WorkspaceError("workspace root cannot be created or replaced")
        parent = self._walk_existing(parts[:-1])
        parent_stat = parent.lstat()
        if not stat_module.S_ISDIR(parent_stat.st_mode):
            raise WorkspaceError("parent is not a directory")
        target = parent / parts[-1]
        if os.path.lexists(target):
            raise WorkspaceError(f"path already exists: {self._virtual(parts)}")
        return parts, target

    def pwd(self) -> str:
        self._check_root()
        return self._virtual(self._cwd_parts)

    def normalize(self, path: str) -> str:
        """Return a virtual path without exposing its host representation."""
        return self._virtual(self._parts(path))

    def existing_host_path(self, path: str) -> tuple[str, Path]:
        """Trusted-adapter copy-in seam; callers must not expose the host path."""
        parts = self._parts(path)
        return self._virtual(parts), self._walk_existing(parts)

    def cd(self, path: str | None = None) -> str:
        parts = self._parts(path or "/")
        target = self._walk_existing(parts)
        if not stat_module.S_ISDIR(target.lstat().st_mode):
            raise WorkspaceError("cd target is not a directory")
        self._cwd_parts = parts
        return self.pwd()

    def ls(self, path: str | None = None) -> list[str]:
        parts = self._parts(path or ".")
        target = self._walk_existing(parts)
        if not stat_module.S_ISDIR(target.lstat().st_mode):
            raise WorkspaceError("ls target is not a directory")
        names: list[str] = []
        try:
            with os.scandir(target) as entries:
                for entry in entries:
                    names.append(entry.name)
                    if len(names) > MAX_DIRECTORY_ENTRIES:
                        raise WorkspaceError(
                            f"directory exceeds {MAX_DIRECTORY_ENTRIES} entries"
                        )
        except WorkspaceError:
            raise
        except OSError as exc:
            raise WorkspaceError(f"directory is unavailable: {exc.strerror}") from exc
        return sorted(names)

    def complete_paths(self, prefix: str, *, directories_only: bool = False) -> list[str]:
        """Return bounded virtual path candidates without exposing host paths."""
        if not isinstance(prefix, str) or "\x00" in prefix:
            return []
        absolute = prefix.startswith("/")
        if prefix.endswith("/"):
            parent_text, leaf = prefix, ""
        elif "/" in prefix:
            parent_text, leaf = prefix.rsplit("/", 1)
            parent_text = parent_text or "/"
        else:
            parent_text, leaf = ".", prefix
        try:
            parent_parts = self._parts(parent_text)
            parent = self._walk_existing(parent_parts)
            if not stat_module.S_ISDIR(parent.lstat().st_mode):
                return []
            names = self.ls(self._virtual(parent_parts))
        except WorkspaceError:
            return []
        candidates: list[str] = []
        for name in names:
            if not name.startswith(leaf):
                continue
            target = parent / name
            try:
                metadata = target.lstat()
            except OSError:
                continue
            if stat_module.S_ISLNK(metadata.st_mode):
                continue
            is_directory = stat_module.S_ISDIR(metadata.st_mode)
            if directories_only and not is_directory:
                continue
            parts = (*parent_parts, name)
            virtual = self._virtual(parts)
            if not absolute:
                base = "" if parent_text == "." else parent_text.rstrip("/") + "/"
                virtual = base + name
            candidates.append(virtual + ("/" if is_directory else ""))
        return candidates

    def read_text(self, path: str) -> str:
        parts = self._parts(path)
        target = self._walk_existing(parts)
        if not stat_module.S_ISREG(target.lstat().st_mode):
            raise WorkspaceError("cat accepts regular files only")
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(target, flags)
            try:
                metadata = os.fstat(descriptor)
                if not stat_module.S_ISREG(metadata.st_mode):
                    raise WorkspaceError("cat accepts regular files only")
                if metadata.st_size > MAX_FILE_BYTES:
                    raise WorkspaceError(f"file exceeds {MAX_FILE_BYTES} bytes")
                chunks: list[bytes] = []
                remaining = MAX_FILE_BYTES + 1
                while remaining:
                    chunk = os.read(descriptor, remaining)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                data = b"".join(chunks)
            finally:
                os.close(descriptor)
        except WorkspaceError:
            raise
        except OSError as exc:
            raise WorkspaceError(f"file is unavailable: {exc.strerror}") from exc
        if len(data) > MAX_FILE_BYTES:
            raise WorkspaceError(f"file exceeds {MAX_FILE_BYTES} bytes")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WorkspaceError("file is not valid UTF-8 text") from exc
        if "\x00" in text:
            raise WorkspaceError("file appears to be binary")
        return text

    def stat(self, path: str) -> WorkspaceStat:
        parts = self._parts(path)
        target = self._walk_existing(parts)
        metadata = target.lstat()
        if stat_module.S_ISREG(metadata.st_mode):
            kind = "file"
            size = metadata.st_size
        elif stat_module.S_ISDIR(metadata.st_mode):
            kind = "directory"
            size = 0
        else:
            raise WorkspaceError("stat accepts regular files and directories only")
        return WorkspaceStat(
            path=self._virtual(parts),
            kind=kind,
            size=size,
            readable=os.access(target, os.R_OK),
            writable=os.access(target, os.W_OK),
        )

    def mkdir(self, path: str, *, mode: int = 0o777) -> str:
        if type(mode) is not int or not 0 <= mode <= 0o777:
            raise WorkspaceError("mkdir mode is invalid")
        parts, target = self._new_leaf(path)
        try:
            os.mkdir(target, mode)
        except OSError as exc:
            raise WorkspaceError(f"mkdir failed: {exc.strerror}") from exc
        return self._virtual(parts)

    def write_text(self, path: str, text: str) -> str:
        if not isinstance(text, str):
            raise WorkspaceError("write content must be text")
        data = text.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise WorkspaceError(f"content exceeds {MAX_FILE_BYTES} bytes")
        return self.write_bytes(path, data, maximum=MAX_FILE_BYTES)

    def write_bytes(self, path: str, data: bytes, *, maximum: int) -> str:
        if type(data) is not bytes or type(maximum) is not int or maximum < 0:
            raise WorkspaceError("invalid bounded byte write")
        if len(data) > maximum:
            raise WorkspaceError(f"content exceeds {maximum} bytes")
        parts, target = self._new_leaf(path)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(target, flags, 0o600)
            try:
                view = memoryview(data)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise WorkspaceError("write made no progress")
                    view = view[written:]
            finally:
                os.close(descriptor)
        except WorkspaceError:
            try:
                target.unlink()
            except OSError:
                pass
            raise
        except OSError as exc:
            raise WorkspaceError(f"write failed: {exc.strerror}") from exc
        return self._virtual(parts)

    def publish_many(self, entries: dict[str, bytes | None], *, maximum: int) -> None:
        """Best-effort all-or-none exclusive publication of bounded outputs.

        ``None`` denotes a directory.  Every target is preflighted before the
        first mutation; if a later create fails, only entries created by this
        call are removed.  This is not a filesystem transaction or an OS
        security boundary.
        """
        if type(entries) is not dict or not entries:
            if entries == {}:
                return
            raise WorkspaceError("invalid publication set")
        prepared: list[tuple[str, tuple[str, ...], bytes | None]] = []
        planned_directories = {self._parts(path) for path, data in entries.items() if data is None}
        for path in sorted(entries, key=lambda value: (len(self._parts(value)), value)):
            data = entries[path]
            if data is not None and (type(data) is not bytes or len(data) > maximum):
                raise WorkspaceError("publication exceeds byte bound")
            parts = self._parts(path)
            if not parts:
                raise WorkspaceError("workspace root cannot be created or replaced")
            existing_prefix = parts[:-1]
            while existing_prefix in planned_directories:
                existing_prefix = existing_prefix[:-1]
            parent = self._walk_existing(existing_prefix)
            if not stat_module.S_ISDIR(parent.lstat().st_mode):
                raise WorkspaceError("publication parent is not a directory")
            target = self._root.joinpath(*parts)
            if os.path.lexists(target):
                raise WorkspaceError(f"path already exists: {self._virtual(parts)}")
            prepared.append((self._virtual(parts), parts, data))
        created: list[Path] = []
        try:
            for _virtual_path, parts, data in prepared:
                target = self._root.joinpath(*parts)
                if data is None:
                    os.mkdir(target, 0o700)
                else:
                    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                    if hasattr(os, "O_NOFOLLOW"):
                        flags |= os.O_NOFOLLOW
                    descriptor = os.open(target, flags, 0o600)
                    try:
                        view = memoryview(data)
                        while view:
                            written = os.write(descriptor, view)
                            if written <= 0:
                                raise WorkspaceError("publication made no progress")
                            view = view[written:]
                    finally:
                        os.close(descriptor)
                created.append(target)
        except (OSError, WorkspaceError) as exc:
            for target in reversed(created):
                try:
                    target.rmdir() if target.is_dir() else target.unlink()
                except OSError:
                    pass
            if isinstance(exc, WorkspaceError):
                raise
            raise WorkspaceError(f"publication failed: {exc.strerror}") from exc
