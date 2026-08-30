"""Evidence adapter for one bounded Graph execution through AXI4-Lite."""
from __future__ import annotations

import argparse
import json
import re
import stat
import struct
from pathlib import Path
from typing import Any

from . import graph_device_axi4lite as control
from .graph_device_mvp import (
    _generated_header as abi_header,
    compile_artifact,
    load_device_abi,
)
from .riscv_stencil_signature import input_words
from .static_region import static_stencil_oracle

ROOT = control.ROOT
ABI_HASHES = control.ABI_HASHES
IMAGE_ID = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
GENERATED_FILES = {
    "abi.sha256",
    "graph_device_abi_generated.h",
    "graph_device_axi4lite_aperture_generated.h",
    "graph_device_axi4lite_execute_vectors.h",
    "input-seed-1.bin",
    "input-seed-2.bin",
    "input-seed-3.bin",
    "oracle-seed-1.bin",
    "oracle-seed-2.bin",
}
SOURCE_FILES = (
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_axi4lite_execute_verilator.cpp",
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_axi4lite_execute.py",
    "raveil/graph_device_mvp.py",
    "raveil/riscv_stencil_signature.py",
    "raveil/static_region.py",
    "hardware/chisel/run-graph-device-axi4lite-execute.sh",
    "hardware/chisel/run-graph-device-axi4lite-execute-in-container.sh",
    "hardware/chisel/Dockerfile",
    *sorted(GENERATED_FILES),
)


class GraphDeviceAxi4LiteExecuteError(RuntimeError):
    """The S03 execution evidence did not satisfy its closed contract."""


def _bounded_regular(path: Path, maximum: int, *, exact: int | None = None) -> bytes:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise GraphDeviceAxi4LiteExecuteError(f"missing {path.name}") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise GraphDeviceAxi4LiteExecuteError(f"unsafe file {path.name}")
    if exact is not None and metadata.st_size != exact:
        raise GraphDeviceAxi4LiteExecuteError(f"unexpected size for {path.name}")
    if metadata.st_size > maximum:
        raise GraphDeviceAxi4LiteExecuteError(f"oversized file {path.name}")
    return path.read_bytes()


_WRITE_TRACE = re.compile(
    r"^AXI4LITE-TRACE-V1 seq=(\d+) op=write address=0x([0-9a-f]{8}) "
    r"data=0x([0-9a-f]{8}) strobe=0x([0-9a-f]) response=([023]) held_b=(\d+)$"
)
_READ_TRACE = re.compile(
    r"^AXI4LITE-TRACE-V1 seq=(\d+) op=read address=0x([0-9a-f]{8}) "
    r"data=0x([0-9a-f]{8}) response=([023]) held_r=(\d+)$"
)


def _trace_summary(payload: bytes) -> dict[str, int]:
    try:
        lines = payload.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise GraphDeviceAxi4LiteExecuteError("AXI transcript is not ASCII") from error
    if not lines or not payload.endswith(b"\n") or len(lines) > 10_000:
        raise GraphDeviceAxi4LiteExecuteError("AXI transcript bounds differ")
    summary = {
        "transactions": len(lines),
        "okay_input_writes": 0,
        "okay_output_reads": 0,
        "denied_output_reads": 0,
        "okay_start_writes": 0,
        "okay_cancel_writes": 0,
        "okay_reset_writes": 0,
        "held_b_cycles": 0,
        "held_r_cycles": 0,
    }
    semantic_events: list[tuple[Any, ...]] = []
    for sequence, line in enumerate(lines):
        write = _WRITE_TRACE.fullmatch(line)
        read = _READ_TRACE.fullmatch(line)
        if write is None and read is None:
            raise GraphDeviceAxi4LiteExecuteError("invalid AXI transcript line")
        match = write if write is not None else read
        assert match is not None
        if int(match.group(1)) != sequence:
            raise GraphDeviceAxi4LiteExecuteError("AXI transcript sequence differs")
        address = int(match.group(2), 16)
        response = int(match.group(5 if write is not None else 4))
        held = int(match.group(6 if write is not None else 5))
        if held > 8192:
            raise GraphDeviceAxi4LiteExecuteError("AXI transcript hold is unbounded")
        if write is not None:
            data = int(match.group(3), 16)
            summary["held_b_cycles"] += held
            if response == 0 and 0x0400 <= address < 0x0910:
                summary["okay_input_writes"] += 1
                semantic_events.append(("input", address, data, held))
            if response == 0 and address == 0x0010:
                if data == 1:
                    summary["okay_start_writes"] += 1
                elif data == 2:
                    summary["okay_cancel_writes"] += 1
                elif data == 4:
                    summary["okay_reset_writes"] += 1
                if data in (1, 2, 4):
                    semantic_events.append(("control", data, held))
        else:
            summary["held_r_cycles"] += held
            if 0x1000 <= address < 0x1400:
                if response == 0:
                    summary["okay_output_reads"] += 1
                    semantic_events.append(("output", address, int(match.group(3), 16), held))
                elif response == 2:
                    summary["denied_output_reads"] += 1
                    semantic_events.append(("denied-output", address, held))
    expected = {
        "transactions": 7160,
        "okay_input_writes": 3 * 324,
        "okay_output_reads": 2 * 256,
        "denied_output_reads": 3,
        "okay_start_writes": 3,
        "okay_cancel_writes": 1,
        "okay_reset_writes": 3,
        "held_b_cycles": 4100,
        "held_r_cycles": 4,
    }
    if any(summary[name] != value for name, value in expected.items()):
        raise GraphDeviceAxi4LiteExecuteError("AXI transcript coverage differs")
    vectors = _vectors()

    def input_events(seed: int) -> list[tuple[Any, ...]]:
        return [
            ("input", 0x0400 + 4 * index, word, 0)
            for index, word in enumerate(vectors[seed][0])
        ]

    def output_events(seed: int, *, first_hold: int = 0) -> list[tuple[Any, ...]]:
        return [
            (
                "output",
                0x1000 + 4 * index,
                word,
                first_hold if index == 0 else 0,
            )
            for index, word in enumerate(vectors[seed][1])
        ]

    expected_events = (
        [("denied-output", 0x1000, 0), ("control", 4, 0)]
        + input_events(1)
        + [("control", 1, 4)]
        + output_events(1, first_hold=4)
        + [("control", 4, 0)]
        + input_events(3)
        + [
            ("control", 1, 0),
            ("denied-output", 0x1000, 0),
            ("control", 2, 4096),
            ("denied-output", 0x1000, 0),
            ("control", 4, 0),
        ]
        + input_events(2)
        + [("control", 1, 0)]
        + output_events(2)
    )
    if semantic_events != expected_events:
        raise GraphDeviceAxi4LiteExecuteError("AXI transcript semantic order differs")
    return summary


def _words_bytes(words: list[int]) -> bytes:
    return struct.pack(f"<{len(words)}I", *(word & 0xFFFFFFFF for word in words))


def _vectors() -> dict[int, tuple[list[int], list[int], int]]:
    result = {}
    for seed in (1, 2, 3):
        inputs = input_words(seed)
        oracle = static_stencil_oracle(inputs)
        result[seed] = (inputs, oracle, sum(oracle) & 0xFFFFFFFFFFFFFFFF)
    return result


def _vectors_header() -> bytes:
    lines = [
        "#ifndef RAVEIL_GRAPH_DEVICE_AXI4LITE_EXECUTE_VECTORS_H",
        "#define RAVEIL_GRAPH_DEVICE_AXI4LITE_EXECUTE_VECTORS_H",
        "#include <array>",
        "#include <cstdint>",
        "namespace raveil::graph_device::axi_execute_vectors {",
    ]
    for seed, (inputs, oracle, checksum) in _vectors().items():
        input_values = ", ".join(f"0x{word:08x}U" for word in inputs)
        lines.append(
            f"inline constexpr std::array<std::uint32_t, 324> kSeed{seed}Input = "
            f"{{{{{input_values}}}}};"
        )
        if seed in (1, 2):
            oracle_values = ", ".join(f"0x{word:08x}U" for word in oracle)
            lines.append(
                f"inline constexpr std::array<std::uint32_t, 256> kSeed{seed}Oracle = "
                f"{{{{{oracle_values}}}}};"
            )
            lines.append(
                f"inline constexpr std::uint64_t kSeed{seed}Checksum = "
                f"0x{checksum:016x}ULL;"
            )
    lines.extend(["}", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _expected_generated() -> dict[str, bytes]:
    artifact = compile_artifact()
    abi = load_device_abi()
    vectors = _vectors()
    generated = {
        "graph_device_axi4lite_aperture_generated.h": control._header(),
        "graph_device_abi_generated.h": abi_header(artifact, abi),
        "graph_device_axi4lite_execute_vectors.h": _vectors_header(),
        "abi.sha256": "".join(
            f"{digest}  {name}\n" for name, digest in sorted(ABI_HASHES.items())
        ).encode("ascii"),
    }
    for seed, (inputs, oracle, _) in vectors.items():
        generated[f"input-seed-{seed}.bin"] = _words_bytes(inputs)
        if seed in (1, 2):
            generated[f"oracle-seed-{seed}.bin"] = _words_bytes(oracle)
    return generated


def prepare(output: Path) -> dict[str, Any]:
    aperture = control.prepare(output)
    for name, payload in _expected_generated().items():
        (output / name).write_bytes(payload)
    return aperture


def _source_path(evidence: Path, name: str) -> Path:
    return evidence / name if name in GENERATED_FILES else ROOT / name


def finalize(evidence: Path, *, verify_existing: bool = False) -> dict[str, Any]:
    if evidence.is_symlink():
        raise GraphDeviceAxi4LiteExecuteError("evidence symlink rejected")
    evidence = evidence.resolve(strict=True)
    if ROOT not in evidence.parents:
        raise GraphDeviceAxi4LiteExecuteError("evidence path escapes repository")
    control._verify_abis()
    for name, expected in _expected_generated().items():
        if _bounded_regular(evidence / name, len(expected), exact=len(expected)) != expected:
            raise GraphDeviceAxi4LiteExecuteError(f"generated input drifted: {name}")
    for child in evidence.rglob("*"):
        if child.is_symlink() or not child.is_file() and not child.is_dir():
            raise GraphDeviceAxi4LiteExecuteError("unsafe recursive evidence entry")
    _bounded_regular(evidence / "source.manifest", 1 << 20)
    source_manifest = control._manifest(evidence / "source.manifest")
    if tuple(line.split(" ", 1)[0] for line in source_manifest) != tuple(
        sorted(SOURCE_FILES)
    ):
        raise GraphDeviceAxi4LiteExecuteError("source manifest inputs differ")
    for line in source_manifest:
        name, digest = line.split(" ", 1)
        if control._sha(control._regular(_source_path(evidence, name))) != digest:
            raise GraphDeviceAxi4LiteExecuteError(f"source digest mismatch: {name}")
    for name in ("rtl-first.manifest", "rtl-second.manifest"):
        _bounded_regular(evidence / name, 1 << 20)
        manifest = control._manifest(evidence / name)
        for line in manifest:
            rtl_name = line.split(" ", 1)[0]
            _bounded_regular(evidence / name.removesuffix(".manifest") / rtl_name, 32 << 20)
        control._verify_manifest_files(
            manifest, evidence / name.removesuffix(".manifest"), name
        )
    if control._regular(evidence / "rtl-first.manifest") != control._regular(
        evidence / "rtl-second.manifest"
    ):
        raise GraphDeviceAxi4LiteExecuteError("RTL manifests differ")
    simulator = _bounded_regular(evidence / "simulator.bin", 64 << 20)
    if _bounded_regular(evidence / "simulator.sha256", 128).decode("ascii").strip() != control._sha(simulator):
        raise GraphDeviceAxi4LiteExecuteError("simulator hash mismatch")
    for name in ("device.stderr", "container.stderr"):
        if _bounded_regular(evidence / name, 1 << 20):
            raise GraphDeviceAxi4LiteExecuteError(f"{name} is not empty")
    log = _bounded_regular(evidence / "device.log", 1024)
    expected_log = (
        b"GraphDevice-AXI4LITE-EXECUTE-V1 status=OK inputs=324 outputs=256 "
        b"oracle=match cancel=denied-output restart=match "
        b"evidence=rtl-simulation-functional performance=not-measured\n"
    )
    if log != expected_log:
        raise GraphDeviceAxi4LiteExecuteError("device log is not exact")
    environment = _bounded_regular(evidence / "environment.txt", 1024)
    expected_environment = (
        "schema=raveil.graph-device-axi4lite-execute-environment/v1\n"
        f"platform=linux/amd64\nimage_id={IMAGE_ID}\n"
    ).encode("ascii")
    if environment != expected_environment:
        raise GraphDeviceAxi4LiteExecuteError("environment identity is not exact")
    toolchain = _bounded_regular(evidence / "toolchain.txt", 64 << 10)
    if not toolchain.startswith(b"Scala CLI version:") or b"Verilator" not in toolchain:
        raise GraphDeviceAxi4LiteExecuteError("toolchain identity is incomplete")
    transcript = _bounded_regular(evidence / "axi-transcript.log", 2 << 20)
    trace_summary = _trace_summary(transcript)
    output_hashes = {}
    for seed in (1, 2):
        output = _bounded_regular(evidence / f"output-seed-{seed}.bin", 1024, exact=1024)
        oracle = _bounded_regular(evidence / f"oracle-seed-{seed}.bin", 1024, exact=1024)
        if output != oracle:
            raise GraphDeviceAxi4LiteExecuteError(f"seed {seed} output differs from oracle")
        output_hashes[str(seed)] = control._sha(output)
    if (evidence / "output-seed-3.bin").exists():
        raise GraphDeviceAxi4LiteExecuteError("cancelled seed published output")
    payload = {
        "schema": "raveil.graph-device-axi4lite-execute-receipt/v1",
        "abi": ABI_HASHES,
        "aperture_sha256": control._sha(
            control._regular(ROOT / "contracts/graph_device_axi4lite_aperture_v1.json")
        ),
        "source_manifest": control._sha(control._regular(evidence / "source.manifest")),
        "rtl_manifests": [
            control._sha(control._regular(evidence / name))
            for name in ("rtl-first.manifest", "rtl-second.manifest")
        ],
        "simulator_sha256": control._sha(simulator),
        "device_log_sha256": control._sha(log),
        "axi_transcript_sha256": control._sha(transcript),
        "axi_trace_summary": trace_summary,
        "device_stderr_sha256": control._sha(
            _bounded_regular(evidence / "device.stderr", 1 << 20)
        ),
        "container_stderr_sha256": control._sha(
            _bounded_regular(evidence / "container.stderr", 1 << 20)
        ),
        "environment_sha256": control._sha(environment),
        "toolchain_sha256": control._sha(toolchain),
        "outputs": output_hashes,
    }
    receipt = evidence / "receipt.json"
    encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("ascii")
    if receipt.exists():
        if not verify_existing:
            raise GraphDeviceAxi4LiteExecuteError("append-once receipt exists")
        if _bounded_regular(receipt, 64 << 10) != encoded:
            raise GraphDeviceAxi4LiteExecuteError("existing receipt differs")
        return payload
    try:
        with receipt.open("xb") as stream:
            stream.write(encoded)
    except FileExistsError as error:
        raise GraphDeviceAxi4LiteExecuteError("append-once receipt exists") from error
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
