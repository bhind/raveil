"""Deterministic, vendor-neutral RTL export for the bounded Graph device."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
from typing import Any

from raveil.graph_device_axi4lite import ABI_HASHES, GraphDeviceAxi4LiteError, prepare as prepare_aperture

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "raveil.graph-device-axi4lite-rtl-export/v1"
RECEIPT_SCHEMA = "raveil.graph-device-axi4lite-rtl-export-receipt/v1"
MAX_FILE_BYTES = 8 * 1024 * 1024
SOURCE_FILES = (
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "contracts/graph_device_abi_v1.json",
    "contracts/graph_device_install_abi_v1.json",
    "contracts/graph_device_program_install_abi_v1.json",
    "hardware/chisel/Dockerfile",
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/export-graph-device-axi4lite-in-container.sh",
    "hardware/chisel/export-graph-device-axi4lite-rtl.sh",
    "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_axi4lite_export.py",
)


class GraphDeviceAxi4LiteExportError(RuntimeError):
    pass


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _regular(path: Path) -> bytes:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise GraphDeviceAxi4LiteExportError(f"missing {path.name}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size <= 0 or info.st_size > MAX_FILE_BYTES:
        raise GraphDeviceAxi4LiteExportError(f"unsafe file {path.name}")
    return path.read_bytes()


def _tree(root: Path, *, omit_manifest: bool = False) -> dict[str, dict[str, Any]]:
    try:
        mode = root.lstat().st_mode
    except FileNotFoundError as exc:
        raise GraphDeviceAxi4LiteExportError("bundle is absent") from exc
    if not stat.S_ISDIR(mode):
        raise GraphDeviceAxi4LiteExportError("bundle is not a real directory")
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if omit_manifest and rel == "manifest.json":
            continue
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            result[rel] = {"type": "directory"}
        elif stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_FILE_BYTES:
            result[rel] = {"type": "file", "bytes": info.st_size, "sha256": _sha(path)}
        else:
            raise GraphDeviceAxi4LiteExportError(f"unsafe tree entry {rel}")
    return result


def _source_sha256() -> str:
    digest = hashlib.sha256()
    for rel in SOURCE_FILES:
        data = _regular(ROOT / rel)
        digest.update(rel.encode("ascii") + b"\0" + data + b"\0")
    return digest.hexdigest()


def _expected_abi_file() -> bytes:
    return "".join(f"{digest}  {name}\n" for name, digest in sorted(ABI_HASHES.items())).encode("ascii")


def _expected_aperture_header() -> bytes:
    aperture = json.loads(_regular(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json"))["apertures"]
    return (
        "#pragma once\n"
        f"#define RAVEIL_AXI_EXEC_BASE 0x{aperture['execution']['base']:04x}U\n"
        f"#define RAVEIL_AXI_CONFIG_BASE 0x{aperture['configuration']['base']:04x}U\n"
        f"#define RAVEIL_AXI_PROGRAM_BASE 0x{aperture['program']['base']:04x}U\n"
    ).encode("ascii")


def _exclusive(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise GraphDeviceAxi4LiteExportError(f"refusing to replace {path.name}") from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def _manifest(path: Path) -> bytes:
    data = _regular(path)
    lines = data.decode("ascii").splitlines()
    pattern = re.compile(r"^[A-Za-z0-9._/-]+ [0-9a-f]{64}$")
    if not lines or lines != sorted(lines) or any(not pattern.fullmatch(line) or line.startswith("/") or ".." in line.split(" ", 1)[0].split("/") for line in lines):
        raise GraphDeviceAxi4LiteExportError(f"invalid {path.name}")
    return data


def prepare(staging: Path) -> None:
    if staging.exists() and (staging.is_symlink() or not staging.is_dir() or any(staging.iterdir())):
        raise GraphDeviceAxi4LiteExportError("staging must be a new or empty real directory")
    try:
        prepare_aperture(staging)
    except GraphDeviceAxi4LiteError as exc:
        raise GraphDeviceAxi4LiteExportError(str(exc)) from exc


def finalize(staging: Path, image_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise GraphDeviceAxi4LiteExportError("image identity is invalid")
    if _regular(staging / "abi.sha256") != _expected_abi_file():
        raise GraphDeviceAxi4LiteExportError("bundled ABI identity differs")
    if _regular(staging / "graph_device_axi4lite_aperture_generated.h") != _expected_aperture_header():
        raise GraphDeviceAxi4LiteExportError("bundled aperture header differs")
    first = _manifest(staging / "rtl.manifest")
    second = _manifest(staging / "rtl-repeat.manifest")
    if first != second:
        raise GraphDeviceAxi4LiteExportError("repeat RTL manifest differs")
    names = [line.split(" ", 1)[0] for line in first.decode("ascii").splitlines()]
    if "GraphDeviceAxi4LiteTop.sv" not in names:
        raise GraphDeviceAxi4LiteExportError("top-level RTL is absent")
    rtl_root = staging / "generated-src"
    actual_names = sorted(path.relative_to(rtl_root).as_posix() for path in rtl_root.rglob("*") if path.is_file())
    if actual_names != names:
        raise GraphDeviceAxi4LiteExportError("RTL closure differs from manifest")
    for line in first.decode("ascii").splitlines():
        name, digest = line.split(" ", 1)
        if _sha(rtl_root / name) != digest:
            raise GraphDeviceAxi4LiteExportError(f"RTL digest mismatch: {name}")
    toolchain = _regular(staging / "toolchain.txt")
    toolchain_lower = toolchain.lower()
    if not toolchain.startswith(b"Scala CLI version:") or (b"java" not in toolchain_lower and b"openjdk" not in toolchain_lower):
        raise GraphDeviceAxi4LiteExportError("toolchain identity is incomplete")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "OK",
        "top": "GraphDeviceAxi4LiteTop",
        "platform": "linux/amd64",
        "image_id": image_id,
        "source_sha256": _source_sha256(),
        "rtl_manifest_sha256": _sha_bytes(first),
        "aperture_sha256": _sha(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json"),
        "abi_sha256": ABI_HASHES,
        "absolute_base": "unassigned",
        "board": "unassigned",
        "evidence_class": "rtl-export-functional-prerequisite",
        "performance": "not-measured",
    }
    _exclusive(staging / "receipt.json", _canonical(receipt))
    manifest = {
        "schema": SCHEMA,
        "top": "GraphDeviceAxi4LiteTop",
        "receipt_sha256": _sha(staging / "receipt.json"),
        "files": _tree(staging),
    }
    _exclusive(staging / "manifest.json", _canonical(manifest))
    return receipt


def verify(bundle: Path) -> dict[str, Any]:
    manifest = json.loads(_regular(bundle / "manifest.json"))
    if set(manifest) != {"schema", "top", "receipt_sha256", "files"} or manifest["schema"] != SCHEMA or manifest["top"] != "GraphDeviceAxi4LiteTop":
        raise GraphDeviceAxi4LiteExportError("manifest schema is invalid")
    if _tree(bundle, omit_manifest=True) != manifest["files"]:
        raise GraphDeviceAxi4LiteExportError("bundle tree or digest differs")
    if _sha(bundle / "receipt.json") != manifest["receipt_sha256"]:
        raise GraphDeviceAxi4LiteExportError("receipt digest differs")
    receipt = json.loads(_regular(bundle / "receipt.json"))
    required = {"schema", "status", "top", "platform", "image_id", "source_sha256", "rtl_manifest_sha256", "aperture_sha256", "abi_sha256", "absolute_base", "board", "evidence_class", "performance"}
    if set(receipt) != required or receipt["schema"] != RECEIPT_SCHEMA or receipt["status"] != "OK" or receipt["top"] != "GraphDeviceAxi4LiteTop":
        raise GraphDeviceAxi4LiteExportError("receipt schema is invalid")
    if receipt["source_sha256"] != _source_sha256() or receipt["abi_sha256"] != ABI_HASHES:
        raise GraphDeviceAxi4LiteExportError("current source or ABI differs")
    if receipt["aperture_sha256"] != _sha(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json"):
        raise GraphDeviceAxi4LiteExportError("aperture differs")
    if _regular(bundle / "abi.sha256") != _expected_abi_file():
        raise GraphDeviceAxi4LiteExportError("bundled ABI identity differs")
    if _regular(bundle / "graph_device_axi4lite_aperture_generated.h") != _expected_aperture_header():
        raise GraphDeviceAxi4LiteExportError("bundled aperture header differs")
    if receipt["rtl_manifest_sha256"] != _sha(bundle / "rtl.manifest"):
        raise GraphDeviceAxi4LiteExportError("RTL manifest digest differs")
    if (receipt["absolute_base"], receipt["board"], receipt["evidence_class"], receipt["performance"]) != ("unassigned", "unassigned", "rtl-export-functional-prerequisite", "not-measured"):
        raise GraphDeviceAxi4LiteExportError("claim boundary differs")
    return receipt


def publish(staging: Path, output: Path) -> None:
    artifacts = (ROOT / "artifacts").resolve(strict=True)
    parent = output.parent.resolve(strict=True)
    target = parent / output.name
    try:
        target.relative_to(artifacts)
    except ValueError as exc:
        raise GraphDeviceAxi4LiteExportError("output must be below repository artifacts") from exc
    if target.exists() or target.is_symlink():
        raise GraphDeviceAxi4LiteExportError("output already exists")
    target.mkdir(mode=0o700)
    try:
        for rel, record in _tree(staging).items():
            destination = target / rel
            if record["type"] == "directory":
                destination.mkdir(mode=0o700)
            else:
                _exclusive(destination, (staging / rel).read_bytes())
    except Exception:
        shutil.rmtree(target)
        raise
