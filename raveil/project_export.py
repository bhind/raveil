"""Bounded cooperative saved-run inspection and explicit derivative export.

No archive reader, importer, network access, execution, or authenticity claim.
"""
from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
import stat
import tempfile

from .project import MAX_BYTES, MAX_ENTRIES, digest, encoded, name, tree

SCHEMA = "raveil.selected-run-files/v1"
MAX_EXPORT_BYTES = 24 * 1024 * 1024
LINEAGE_ONLY = {"record.json", "record.sha256"}
WARNINGS = [
    "Saved runs can include unrelated inputs; review every selected member.",
    "Selected files can contain secrets. This is not a secret scanner.",
    "This derivative is not an authenticated experiment or replayable full run.",
    "Single-writer cooperative workspace only; no hostile concurrent isolation.",
]


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate export JSON field")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite export JSON number")


def _sha256(value):
    if (type(value) is not str or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)):
        raise ValueError("invalid export SHA-256")
    return value


def inspect_export(source: Path):
    """Check an untrusted derivative's internal consistency; never extract it."""
    if not getattr(os, "O_NOFOLLOW", 0):
        raise ValueError("no-follow reads are unavailable on this platform")
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("export inspection requires a non-linked regular file")
        if before.st_size > MAX_EXPORT_BYTES:
            raise ValueError("encoded export exceeds 24 MiB")
        chunks, remaining = [], MAX_EXPORT_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(remaining, 65536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        if (len(raw) > MAX_EXPORT_BYTES or len(raw) != before.st_size
                or (before.st_size, before.st_mtime_ns, before.st_ctime_ns)
                != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
            raise ValueError("export changed during inspection or exceeds byte budget")
    finally:
        os.close(fd)
    try:
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                            parse_constant=_reject_constant)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid export JSON encoding or nesting") from exc
    keys = {"schema", "kind", "authenticated", "replayable_full_run", "source_run_id",
            "source_record_sha256", "source_preview_sha256", "omitted_count", "files", "warnings"}
    if type(bundle) is not dict or set(bundle) != keys:
        raise ValueError("unexpected export envelope fields")
    if (bundle["schema"] != SCHEMA or bundle["kind"] != "selected-file-derivative"
            or bundle["authenticated"] is not False or bundle["replayable_full_run"] is not False
            or bundle["warnings"] != WARNINGS):
        raise ValueError("unsupported export schema or claims")
    if type(bundle["source_run_id"]) is not str:
        raise ValueError("invalid export source run ID")
    name(bundle["source_run_id"])
    for key in ("source_record_sha256", "source_preview_sha256"):
        _sha256(bundle[key])
    omitted = bundle["omitted_count"]
    files = bundle["files"]
    if (type(omitted) is not int or not 0 <= omitted <= MAX_ENTRIES
            or type(files) is not list or not 1 <= len(files) <= MAX_ENTRIES
            or len(files) + omitted > MAX_ENTRIES):
        raise ValueError("invalid export member count")
    inventory, paths, directories, total = [], set(), set(), 0
    for member in files:
        if type(member) is not dict or set(member) != {"path", "bytes", "sha256", "base64"}:
            raise ValueError("unexpected export member fields")
        path = member_name(member["path"])
        folded = path.casefold()
        if folded in paths or path in LINEAGE_ONLY:
            raise ValueError("duplicate or lineage-only export member")
        paths.add(folded)
        directories.update("/".join(folded.split("/")[:i])
                           for i in range(1, len(folded.split("/"))))
        if paths & directories or len(paths) + len(directories) + omitted > MAX_ENTRIES:
            raise ValueError("export path collision or entry budget exceeded")
        size = member["bytes"]
        if type(size) is not int or not 0 <= size <= MAX_BYTES - total:
            raise ValueError("invalid export decoded byte count")
        payload = member["base64"]
        if type(payload) is not str or len(payload) != 4 * ((size + 2) // 3):
            raise ValueError("invalid export base64 length")
        try:
            decoded = base64.b64decode(payload, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("invalid export base64") from exc
        if (len(decoded) != size or digest(decoded) != _sha256(member["sha256"])
                or base64.b64encode(decoded).decode("ascii") != payload):
            raise ValueError("export payload length/hash/encoding mismatch")
        total += size
        inventory.append({"path": path, "bytes": size, "sha256": member["sha256"]})
    return {"schema": "raveil.selected-run-inspection/v1", "internal_integrity": "consistent",
            "authenticated": False, "replayable_full_run": False, "source_verified": False,
            "bundle_sha256": digest(raw), "selected_count": len(files),
            "selected_bytes": total, "omitted_count": omitted, "files": inventory,
            "warnings": ["Self-contained hashes do not authenticate the sender or source run.",
                         "No files were extracted, imported or executed."]}


def member_name(value: str) -> str:
    if (type(value) is not str or not value.isascii() or len(value) > 4096
            or "\\" in value or ":" in value
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in {"", ".", ".."} for p in value.split("/"))):
        raise ValueError("member must be a canonical relative ASCII path")
    return value


def _capture(project, run_id: str, members: list[str] | None):
    if not getattr(os, "O_NOFOLLOW", 0):
        raise ValueError("no-follow reads are unavailable on this platform")
    run_id = name(run_id)
    record = project.load_run(run_id)
    root = project.root / "runs" / run_id
    manifest = tree(root)
    paths = sorted(member_name(p[1:]) for p, v in manifest.items() if v != "directory")
    folded = [p.casefold() for p in paths]
    dirs = {"/".join(p.casefold().split("/")[:i])
            for p in paths for i in range(1, len(p.split("/")))}
    if len(set(folded)) != len(folded) or set(folded) & dirs or len(paths) + len(dirs) > MAX_ENTRIES:
        raise ValueError("member collision or entry budget exceeded")
    selected = [] if members is None else [member_name(p) for p in members]
    if len(selected) > MAX_ENTRIES or len(set(selected)) != len(selected):
        raise ValueError("duplicate selection or selection budget exceeded")
    if any(p not in paths for p in selected):
        raise ValueError("selected member is not a saved regular file")
    if LINEAGE_ONLY.intersection(selected):
        raise ValueError("original run records are lineage-only, not exportable payloads")
    payloads, inventory, total = {}, [], 0
    for relative in paths:
        _, path = project.workspace.existing_host_path(f"runs/{run_id}/{relative}")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("export inspection requires non-linked regular files")
            if metadata.st_size > MAX_BYTES - total:
                raise ValueError("source byte budget exceeded")
            chunks, remaining = [], MAX_BYTES - total + 1
            while remaining:
                chunk = os.read(fd, min(remaining, 65536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
        finally:
            os.close(fd)
        total += len(data)
        if total > MAX_BYTES or digest(data) != manifest["/" + relative]:
            raise ValueError("saved member changed or source byte budget exceeded")
        inventory.append({"path": relative, "bytes": len(data), "sha256": digest(data),
                          "selectable": relative not in LINEAGE_ONLY,
                          "selected": relative in selected})
        if relative in selected:
            payloads[relative] = data
    if project.load_run(run_id) != record or tree(root) != manifest:
        raise ValueError("saved run changed during inspection")
    preview = {"schema": "raveil.run-export-preview/v1", "run_id": run_id,
               "source_record_sha256": manifest["/record.json"],
               "files": inventory, "total_bytes": total,
               "selected_bytes": sum(len(v) for v in payloads.values()),
               "selected_count": len(selected), "omitted_count": len(paths) - len(selected),
               "warnings": WARNINGS}
    preview["preview_sha256"] = digest(encoded(preview))
    return preview, payloads


def preview(project, run_id: str, members: list[str] | None = None):
    return _capture(project, run_id, members)[0]


def export_selected(project, run_id: str, members: list[str], destination: Path,
                    expected_preview: str, acknowledge: bool = False):
    if not acknowledge or not members:
        raise ValueError("explicit members and sensitive-data acknowledgement are required")
    view, payloads = _capture(project, run_id, members)
    if expected_preview != view["preview_sha256"]:
        raise ValueError("preview changed; inspect the same selection again")
    bundle = {"schema": SCHEMA, "kind": "selected-file-derivative",
              "authenticated": False, "replayable_full_run": False,
              "source_run_id": run_id, "source_record_sha256": view["source_record_sha256"],
              "source_preview_sha256": expected_preview, "omitted_count": view["omitted_count"],
              "files": [{"path": p, "bytes": len(data), "sha256": digest(data),
                         "base64": base64.b64encode(data).decode("ascii")}
                        for p, data in sorted(payloads.items())], "warnings": WARNINGS}
    output = encoded(bundle)
    if len(output) > MAX_EXPORT_BYTES:
        raise ValueError("encoded export exceeds 24 MiB")
    destination = Path(os.path.abspath(destination))
    for parent in (destination.parent, *destination.parent.parents):
        if parent.is_symlink():
            raise ValueError("destination parent must not be a symlink")
    parent = destination.parent.resolve(strict=True)
    if parent == project.root or project.root in parent.parents:
        raise ValueError("export destination must be outside the source project")
    target = parent / destination.name
    if os.path.lexists(target):
        raise ValueError("export destination already exists")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".raveil-export-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(output)
            stream.flush()
            os.fsync(stream.fileno())
        # Atomic no-overwrite publication on the same filesystem.
        os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink()
    return {"schema": SCHEMA, "selected_count": len(payloads),
            "omitted_count": view["omitted_count"], "bytes": len(output),
            "sha256": digest(output), "authenticated": False, "replayable_full_run": False}
