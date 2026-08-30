"""Evidence adapter for bounded AXI4-Lite configuration/program installation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from . import graph_device_axi4lite as control
from .graph_device_affine import _generated_header as affine_header
from .graph_device_dag import _generated_header as dag_header
from .graph_device_dag import compile_artifact as compile_dag

ROOT = control.ROOT
ABI_HASHES = control.ABI_HASHES
IMAGE_ID = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
GENERATED_FILES = {
    "abi.sha256",
    "graph_device_affine_generated.h",
    "graph_device_axi4lite_aperture_generated.h",
    "graph_device_dag_generated.h",
}
SOURCE_FILES = (
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_axi4lite_install_verilator.cpp",
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_axi4lite_install.py",
    "raveil/graph_device_affine.py",
    "raveil/graph_device_dag.py",
    "hardware/chisel/run-graph-device-axi4lite-install.sh",
    "hardware/chisel/run-graph-device-axi4lite-install-in-container.sh",
    "hardware/chisel/Dockerfile",
    *sorted(GENERATED_FILES),
)


class GraphDeviceAxi4LiteInstallError(RuntimeError):
    """The S02 installer evidence did not satisfy its closed contract."""


def prepare(output: Path) -> dict[str, Any]:
    aperture = control.prepare(output)
    (output / "graph_device_affine_generated.h").write_bytes(affine_header())
    (output / "graph_device_dag_generated.h").write_bytes(
        dag_header(compile_dag())
    )
    return aperture


def _source_path(evidence: Path, name: str) -> Path:
    return evidence / name if name in GENERATED_FILES else ROOT / name


def finalize(evidence: Path, *, verify_existing: bool = False) -> dict[str, Any]:
    if evidence.is_symlink():
        raise GraphDeviceAxi4LiteInstallError("evidence symlink rejected")
    evidence = evidence.resolve(strict=True)
    if ROOT not in evidence.parents:
        raise GraphDeviceAxi4LiteInstallError("evidence path escapes repository")
    control._verify_abis()
    expected_generated = {
        "graph_device_axi4lite_aperture_generated.h": control._header(),
        "graph_device_affine_generated.h": affine_header(),
        "graph_device_dag_generated.h": dag_header(compile_dag()),
        "abi.sha256": "".join(
            f"{digest}  {name}\n" for name, digest in sorted(ABI_HASHES.items())
        ).encode("ascii"),
    }
    for name, expected in expected_generated.items():
        if control._regular(evidence / name) != expected:
            raise GraphDeviceAxi4LiteInstallError(f"generated input drifted: {name}")
    for child in evidence.rglob("*"):
        if child.is_symlink() or not child.is_file() and not child.is_dir():
            raise GraphDeviceAxi4LiteInstallError("unsafe recursive evidence entry")
    source_manifest = control._manifest(evidence / "source.manifest")
    if tuple(line.split(" ", 1)[0] for line in source_manifest) != tuple(
        sorted(SOURCE_FILES)
    ):
        raise GraphDeviceAxi4LiteInstallError("source manifest inputs differ")
    for line in source_manifest:
        name, digest = line.split(" ", 1)
        if control._sha(control._regular(_source_path(evidence, name))) != digest:
            raise GraphDeviceAxi4LiteInstallError(f"source digest mismatch: {name}")
    for name in ("rtl-first.manifest", "rtl-second.manifest"):
        manifest = control._manifest(evidence / name)
        control._verify_manifest_files(
            manifest, evidence / name.removesuffix(".manifest"), name
        )
    if control._regular(evidence / "rtl-first.manifest") != control._regular(
        evidence / "rtl-second.manifest"
    ):
        raise GraphDeviceAxi4LiteInstallError("RTL manifests differ")
    receipt = evidence / "receipt.json"
    simulator = control._regular(evidence / "simulator.bin")
    if control._regular(evidence / "simulator.sha256").decode("ascii").strip() != control._sha(simulator):
        raise GraphDeviceAxi4LiteInstallError("simulator hash mismatch")
    log = control._regular(evidence / "device.log")
    expected_log = (
        b"GraphDevice-AXI4LITE-INSTALL-V1 status=OK "
        b"evidence=rtl-simulation-functional performance=not-measured\n"
    )
    if log != expected_log:
        raise GraphDeviceAxi4LiteInstallError("device log is not exact")
    for name in ("device.stderr", "container.stderr"):
        if control._regular(evidence / name):
            raise GraphDeviceAxi4LiteInstallError(f"{name} is not empty")
    environment = control._regular(evidence / "environment.txt")
    expected_environment = (
        "schema=raveil.graph-device-axi4lite-install-environment/v1\n"
        f"platform=linux/amd64\nimage_id={IMAGE_ID}\n"
    ).encode("ascii")
    if environment != expected_environment:
        raise GraphDeviceAxi4LiteInstallError("environment identity is not exact")
    toolchain = control._regular(evidence / "toolchain.txt")
    if not toolchain.startswith(b"Scala CLI version:") or b"Verilator" not in toolchain:
        raise GraphDeviceAxi4LiteInstallError("toolchain identity is incomplete")
    payload = {
        "schema": "raveil.graph-device-axi4lite-install-receipt/v1",
        "abi": ABI_HASHES,
        "device_log_sha256": control._sha(log),
        "aperture_sha256": control._sha(
            control._regular(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json")
        ),
        "source_manifest": control._sha(control._regular(evidence / "source.manifest")),
        "rtl_manifests": [
            control._sha(control._regular(evidence / name))
            for name in ("rtl-first.manifest", "rtl-second.manifest")
        ],
        "simulator_sha256": control._sha(simulator),
        "environment_sha256": control._sha(environment),
        "toolchain_sha256": control._sha(toolchain),
        "device_stderr_sha256": control._sha(control._regular(evidence / "device.stderr")),
        "container_stderr_sha256": control._sha(control._regular(evidence / "container.stderr")),
    }
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("ascii")
    if receipt.exists():
        if not verify_existing:
            raise GraphDeviceAxi4LiteInstallError("append-once receipt exists")
        if control._regular(receipt) != encoded:
            raise GraphDeviceAxi4LiteInstallError("existing receipt differs")
        return payload
    try:
        with receipt.open("xb") as stream:
            stream.write(encoded)
    except FileExistsError as error:
        raise GraphDeviceAxi4LiteInstallError("append-once receipt exists") from error
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "finalize", "verify"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()
    result = (
        prepare(args.output)
        if args.command == "prepare"
        else finalize(args.evidence, verify_existing=args.command == "verify")
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
