"""Evidence preparation for the bounded Graph-device AXI4-Lite control slice."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ABI_HASHES = {
    "graph_device_abi_v1.json": "374f68614f4f5c226b503101fa6fbd95d68ddbb594b8e13712d3fd59dd77c4a9",
    "graph_device_install_abi_v1.json": "509aaea7436db6170f641bdea033b9178d27c5a5e8134526ce017b3d5509babf",
    "graph_device_program_install_abi_v1.json": "0d833b8db807dcd56fc12d9e00682df08ea759f75dd7a789d3aeba8482f92a92",
}
SOURCE_FILES = (
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_axi4lite_control_verilator.cpp",
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "raveil/graph_device_axi4lite.py",
    "hardware/chisel/run-graph-device-axi4lite-control.sh",
    "hardware/chisel/run-graph-device-axi4lite-control-in-container.sh",
    "hardware/chisel/Dockerfile",
    "graph_device_axi4lite_aperture_generated.h",
    "abi.sha256",
)

class GraphDeviceAxi4LiteError(RuntimeError): pass

def _regular(path: Path) -> bytes:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc: raise GraphDeviceAxi4LiteError(f"missing {path.name}") from exc
    if not stat.S_ISREG(mode): raise GraphDeviceAxi4LiteError(f"unsafe file {path.name}")
    return path.read_bytes()

def _sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def _aperture() -> dict[str, Any]:
    return json.loads(_regular(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json"))

def _header() -> bytes:
    a = _aperture()["apertures"]
    return ("#pragma once\n"
            f"#define RAVEIL_AXI_EXEC_BASE 0x{a['execution']['base']:04x}U\n"
            f"#define RAVEIL_AXI_CONFIG_BASE 0x{a['configuration']['base']:04x}U\n"
            f"#define RAVEIL_AXI_PROGRAM_BASE 0x{a['program']['base']:04x}U\n").encode("ascii")

def _verify_abis() -> None:
    for name, expected in ABI_HASHES.items():
        if _sha(_regular(ROOT / "contracts" / name)) != expected:
            raise GraphDeviceAxi4LiteError(f"ABI hash mismatch: {name}")

def prepare(output: Path) -> dict[str, Any]:
    if output.exists() and (output.is_symlink() or not output.is_dir() or any(output.iterdir())):
        raise GraphDeviceAxi4LiteError("output must be a new or empty real directory")
    output.mkdir(parents=True, exist_ok=True)
    _verify_abis()
    (output / "graph_device_axi4lite_aperture_generated.h").write_bytes(_header())
    (output / "abi.sha256").write_text("".join(f"{v}  {k}\n" for k, v in sorted(ABI_HASHES.items())), encoding="ascii")
    return _aperture()

def _manifest(path: Path) -> list[str]:
    text = _regular(path).decode("ascii")
    lines = [line for line in text.splitlines() if line]
    pattern = re.compile(r"^[A-Za-z0-9._/-]+ [0-9a-f]{64}$")
    names = [x.split(" ", 1)[0] for x in lines]
    if (lines != sorted(lines) or not lines or any(name.startswith("/") or ".." in name.split("/") or not pattern.fullmatch(x) for name, x in zip(names, lines))):
        raise GraphDeviceAxi4LiteError(f"invalid manifest {path.name}")
    return lines

def _verify_manifest_files(lines: list[str], base: Path, label: str) -> None:
    for line in lines:
        name, digest = line.split(" ", 1)
        candidate = base / name
        try:
            candidate.relative_to(base)
        except ValueError as exc:
            raise GraphDeviceAxi4LiteError(f"{label} path escapes root") from exc
        if _sha(_regular(candidate)) != digest:
            raise GraphDeviceAxi4LiteError(f"{label} digest mismatch: {name}")

def _source_path(evidence: Path, name: str) -> Path:
    return evidence / name if name in {"graph_device_axi4lite_aperture_generated.h", "abi.sha256"} else ROOT / name

def finalize(evidence: Path) -> dict[str, Any]:
    if evidence.is_symlink(): raise GraphDeviceAxi4LiteError("evidence symlink rejected")
    evidence = evidence.resolve(strict=True)
    if ROOT not in evidence.parents: raise GraphDeviceAxi4LiteError("evidence path escapes repository")
    _verify_abis()
    if _regular(evidence / "graph_device_axi4lite_aperture_generated.h") != _header():
        raise GraphDeviceAxi4LiteError("generated aperture header drifted")
    for child in evidence.rglob("*"):
        if child.is_symlink() or not child.is_file() and not child.is_dir():
            raise GraphDeviceAxi4LiteError("unsafe recursive evidence entry")
    source_manifest = _manifest(evidence / "source.manifest")
    if tuple(line.split(" ", 1)[0] for line in source_manifest) != tuple(sorted(SOURCE_FILES)):
        raise GraphDeviceAxi4LiteError("source manifest inputs differ")
    for line in source_manifest:
        name, digest = line.split(" ", 1)
        if _sha(_regular(_source_path(evidence, name))) != digest:
            raise GraphDeviceAxi4LiteError(f"source digest mismatch: {name}")
    for name in ("rtl-first.manifest", "rtl-second.manifest"):
        rtl = _manifest(evidence / name)
        _verify_manifest_files(rtl, evidence / name.removesuffix(".manifest"), name)
    if _regular(evidence / "rtl-first.manifest") != _regular(evidence / "rtl-second.manifest"):
        raise GraphDeviceAxi4LiteError("RTL manifests differ")
    for name in ("simulator.sha256", "environment.txt", "toolchain.txt", "device.log", "abi.sha256"):
        _regular(evidence / name)
    receipt = evidence / "receipt.json"
    if receipt.exists(): raise GraphDeviceAxi4LiteError("append-once receipt exists")
    simulator = _regular(evidence / "simulator.bin")
    if _regular(evidence / "simulator.sha256").decode("ascii").strip() != _sha(simulator):
        raise GraphDeviceAxi4LiteError("simulator hash mismatch")
    log = _regular(evidence / "device.log")
    if log != b"GraphDevice-AXI4LITE-CONTROL-V1 status=OK evidence=rtl-simulation-functional performance=not-measured\n":
        raise GraphDeviceAxi4LiteError("device log is not exact")
    expected_abi = "".join(f"{v}  {k}\n" for k, v in sorted(ABI_HASHES.items())).encode("ascii")
    if _regular(evidence / "abi.sha256") != expected_abi:
        raise GraphDeviceAxi4LiteError("ABI evidence hash drifted")
    environment = _regular(evidence / "environment.txt")
    if not re.fullmatch(rb"schema=raveil\.graph-device-axi4lite-environment/v1\nplatform=linux/amd64\nimage_id=sha256:[0-9a-f]{64}\n", environment):
        raise GraphDeviceAxi4LiteError("environment identity is not exact")
    toolchain = _regular(evidence / "toolchain.txt")
    if not toolchain.startswith(b"Scala CLI version:") or b"Verilator" not in toolchain:
        raise GraphDeviceAxi4LiteError("toolchain identity is incomplete")
    payload = {"schema": "raveil.graph-device-axi4lite-control-receipt/v1", "abi": ABI_HASHES,
               "device_log_sha256": _sha(log), "aperture_sha256": _sha(_regular(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json")),
               "source_manifest": _sha(_regular(evidence / "source.manifest")),
               "rtl_manifests": [_sha(_regular(evidence / n)) for n in ("rtl-first.manifest", "rtl-second.manifest")],
               "simulator_sha256": _sha(simulator), "environment_sha256": _sha(environment),
               "toolchain_sha256": _sha(toolchain)}
    fd = None
    try:
        fd = receipt.open("x", encoding="ascii")
        fd.write(json.dumps(payload, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise GraphDeviceAxi4LiteError("append-once receipt exists") from exc
    finally:
        if fd is not None: fd.close()
    return payload

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("command", choices=("prepare", "finalize")); p.add_argument("--output", type=Path); p.add_argument("--evidence", type=Path); a=p.parse_args()
    print(json.dumps(prepare(a.output) if a.command == "prepare" else finalize(a.evidence), sort_keys=True))
if __name__ == "__main__": main()
