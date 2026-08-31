"""Private S04 AXI4-Lite transport evidence for the frozen three-Graph catalogue."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any

from . import graph_device_axi4lite as aperture
from . import graph_device_dag as dag

ROOT = aperture.ROOT
IMAGE_ID = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
SCHEMA = "raveil.graph-device-axi4lite-selected-receipt/v1"
AXI_TRANSACTION_COUNT = 11_444
AXI_TRANSCRIPT_SHA256 = "e266bb9ac12a97613e3c041aff73b012fa421fe40a4077e21ad83ae607e6db5b"
_AXI_WRITE = re.compile(
    r"^AXI4LITE-TRACE-V1 seq=([0-9]+) op=write address=0x([0-9a-f]{8}) "
    r"data=0x([0-9a-f]{8}) strobe=0xf response=([0-3]) held_b=0$"
)
_AXI_READ = re.compile(
    r"^AXI4LITE-TRACE-V1 seq=([0-9]+) op=read address=0x([0-9a-f]{8}) "
    r"data=0x([0-9a-f]{8}) response=([0-3]) held_r=0$"
)
GENERATED = {
    "abi.sha256", "graph_device_axi4lite_aperture_generated.h",
    "graph_device_abi_generated.h", "graph_device_affine_generated.h",
    "graph_device_dag_generated.h", "dag-artifact.json",
}
SOURCE_FILES = (
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
    "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp",
    "hardware/chisel/graph_device_affine_runtime.h",
    "hardware/chisel/graph_device_affine_runtime.cpp",
    "hardware/chisel/graph_device_dag_runtime.h",
    "hardware/chisel/graph_device_dag_runtime.cpp",
    "hardware/chisel/graph_device_axi4lite_selected_verilator.cpp",
    "hardware/chisel/run-graph-device-axi4lite-selected.sh",
    "hardware/chisel/run-graph-device-axi4lite-selected-in-container.sh",
    "contracts/graph_device_axi4lite_aperture_v1.json",
    "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_axi4lite_selected.py",
    "raveil/graph_device_dag.py",
    "raveil/graph_device_affine.py",
    "raveil/graph_device_mvp.py",
    "hardware/chisel/Dockerfile",
    *sorted(GENERATED),
)
EXPECTED_TOP_LEVEL = frozenset("""
abi.sha256 affine-artifact.json artifact.json axi-transcript.log
config-baseline.bin config-compact.bin container.stderr container.stdout
dag-artifact.json dag-oracles dag-programs device.log device.stderr
emit-first.stderr emit-first.stdout emit-second.stderr emit-second.stdout
environment.txt fallback-output-compact-horizontal-three-point-seed-2.bin
fallback-output-compact-horizontal-three-point-seed-3.bin
fallback-output-five-point-seed-1.bin fallback-output-five-point-seed-5.bin
fallback-output-vertical-three-point-seed-4.bin graph_device_abi_generated.h
graph_device_affine_generated.h graph_device_axi4lite_aperture_generated.h
graph_device_dag_generated.h inputs oracles
private-output-compact-horizontal-three-point-seed-2.bin
private-output-five-point-seed-1.bin private-output-five-point-seed-5.bin
private-output-vertical-three-point-seed-4.bin rtl-first rtl-first.manifest
rtl-second rtl-second.manifest simulator.bin simulator.sha256 source.manifest
toolchain.txt verilator.stderr verilator.stdout
""".split())
EXPECTED_NESTED_FILES = {
    "inputs": frozenset(f"seed-{seed}.bin" for seed in range(1, 6)),
    "dag-programs": frozenset({
        "five-point.bin", "compact-horizontal-three-point.bin", "vertical-three-point.bin",
    }),
    "dag-oracles": frozenset({
        "five-point-seed-1.bin", "compact-horizontal-three-point-seed-2.bin",
        "compact-horizontal-three-point-seed-3.bin", "vertical-three-point-seed-4.bin",
        "five-point-seed-5.bin",
    }),
    "oracles": frozenset({
        "baseline-seed-1.bin", "baseline-seed-2.bin", "baseline-seed-3.bin",
        "baseline-seed-4.bin", "compact-seed-1.bin", "compact-seed-2.bin",
        "compact-seed-3.bin", "compact-seed-4.bin", "seed-1.bin", "seed-2.bin",
        "seed-3.bin",
    }),
}

class GraphDeviceAxi4LiteSelectedError(RuntimeError): pass

def _read(path: Path, limit: int = 32 << 20) -> bytes:
    try: meta = path.lstat()
    except FileNotFoundError as exc: raise GraphDeviceAxi4LiteSelectedError(f"missing {path.name}") from exc
    if not stat.S_ISREG(meta.st_mode) or meta.st_size > limit:
        raise GraphDeviceAxi4LiteSelectedError(f"unsafe {path.name}")
    return path.read_bytes()

def _sha(payload: bytes) -> str: return hashlib.sha256(payload).hexdigest()

def prepare(output: Path) -> dict[str, Any]:
    # dag.prepare owns all compiler-generated program/config/input identities;
    # the aperture helper adds only the independently pinned bus namespace.
    artifact = dag.prepare(output)
    aperture._verify_abis()
    (output / "graph_device_axi4lite_aperture_generated.h").write_bytes(aperture._header())
    (output / "abi.sha256").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(aperture.ABI_HASHES.items())),
        encoding="ascii",
    )
    return artifact

def _source(evidence: Path, name: str) -> Path:
    return evidence / name if name in GENERATED else ROOT / name

def _manifest(path: Path) -> list[str]:
    lines = _read(path, 1 << 20).decode("ascii").splitlines()
    if not lines or lines != sorted(lines): raise GraphDeviceAxi4LiteSelectedError("manifest order differs")
    for line in lines:
        fields = line.split(" ")
        if (len(fields) != 2 or not fields[0] or fields[0].startswith("/")
                or ".." in Path(fields[0]).parts or len(fields[1]) != 64
                or any(char not in "0123456789abcdef" for char in fields[1])):
            raise GraphDeviceAxi4LiteSelectedError("manifest schema differs")
    return lines

def _reject_unsafe_tree(evidence: Path) -> None:
    top_level = {path.name for path in evidence.iterdir()}
    if top_level not in (set(EXPECTED_TOP_LEVEL), set(EXPECTED_TOP_LEVEL) | {"receipt.json"}):
        raise GraphDeviceAxi4LiteSelectedError("evidence top-level allowlist differs")
    for path in evidence.rglob("*"):
        try: mode = path.lstat().st_mode
        except OSError as exc: raise GraphDeviceAxi4LiteSelectedError("evidence tree cannot be inspected") from exc
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise GraphDeviceAxi4LiteSelectedError("evidence tree contains a link or special file")
    for directory, expected in EXPECTED_NESTED_FILES.items():
        actual = {
            str(path.relative_to(evidence / directory))
            for path in (evidence / directory).rglob("*") if path.is_file()
        }
        if actual != expected:
            raise GraphDeviceAxi4LiteSelectedError(f"evidence allowlist differs: {directory}")

def _validate_rtl_tree(evidence: Path, manifest: list[str]) -> None:
    expected_files = {line.split(" ", 1)[0] for line in manifest} | {"filelist.f"}
    expected_dirs = {
        "verification", "verification/assert", "verification/assume", "verification/cover",
    }
    for directory in ("rtl-first", "rtl-second"):
        root = evidence / directory
        actual_files = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
        actual_dirs = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_dir()}
        if actual_files != expected_files or actual_dirs != expected_dirs:
            raise GraphDeviceAxi4LiteSelectedError(f"RTL evidence allowlist differs: {directory}")

def _validate_transcript(payload: bytes) -> list[str]:
    try: lines = payload.decode("ascii").splitlines()
    except UnicodeError as exc: raise GraphDeviceAxi4LiteSelectedError("AXI transcript is not ASCII") from exc
    if (len(lines) != AXI_TRANSACTION_COUNT or not payload.endswith(b"\n")
            or _sha(payload) != AXI_TRANSCRIPT_SHA256):
        raise GraphDeviceAxi4LiteSelectedError("AXI transcript identity differs")
    for sequence, line in enumerate(lines):
        match = _AXI_WRITE.fullmatch(line) or _AXI_READ.fullmatch(line)
        if match is None or int(match.group(1)) != sequence:
            raise GraphDeviceAxi4LiteSelectedError("AXI transcript schema differs")
        address = int(match.group(2), 16)
        if address >= 0x4000 or address % 4:
            raise GraphDeviceAxi4LiteSelectedError("AXI transcript address differs")
    return lines

def _expected(evidence: Path, verify_existing: bool) -> dict[str, Any]:
    if evidence.is_symlink(): raise GraphDeviceAxi4LiteSelectedError("evidence symlink")
    evidence = evidence.resolve(strict=True)
    if ROOT not in evidence.parents: raise GraphDeviceAxi4LiteSelectedError("evidence escapes repository")
    _reject_unsafe_tree(evidence)
    aperture._verify_abis()
    expected_abi = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(aperture.ABI_HASHES.items())
    ).encode("ascii")
    if _read(evidence / "abi.sha256", 1024) != expected_abi:
        raise GraphDeviceAxi4LiteSelectedError("ABI identity export differs")
    if _read(evidence / "graph_device_axi4lite_aperture_generated.h") != aperture._header():
        raise GraphDeviceAxi4LiteSelectedError("aperture header drifted")
    artifact = dag.compile_artifact()
    if _read(evidence / "dag-artifact.json") != json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n":
        raise GraphDeviceAxi4LiteSelectedError("DAG artifact drifted")
    if _read(evidence / "graph_device_dag_generated.h") != dag._generated_header(artifact):
        raise GraphDeviceAxi4LiteSelectedError("DAG header drifted")
    manifest = _manifest(evidence / "source.manifest")
    if tuple(line.split(" ", 1)[0] for line in manifest) != tuple(sorted(SOURCE_FILES)):
        raise GraphDeviceAxi4LiteSelectedError("source set differs")
    for line in manifest:
        name, digest = line.split(" ", 1)
        if _sha(_read(_source(evidence, name))) != digest: raise GraphDeviceAxi4LiteSelectedError(f"source digest differs: {name}")
    first = _manifest(evidence / "rtl-first.manifest")
    second = _manifest(evidence / "rtl-second.manifest")
    if _read(evidence / "rtl-first.manifest") != _read(evidence / "rtl-second.manifest"):
        raise GraphDeviceAxi4LiteSelectedError("RTL elaborations differ")
    _validate_rtl_tree(evidence, first)
    for name in first:
        relative, digest = name.split(" ", 1)
        if _sha(_read(evidence / "rtl-first" / relative)) != digest or _sha(_read(evidence / "rtl-second" / relative)) != digest:
            raise GraphDeviceAxi4LiteSelectedError("RTL manifest binding differs")
    simulator = _read(evidence / "simulator.bin", 64 << 20)
    if _read(evidence / "simulator.sha256", 128).decode("ascii").strip() != _sha(simulator):
        raise GraphDeviceAxi4LiteSelectedError("simulator digest differs")
    env = _read(evidence / "environment.txt", 1024)
    expected_env = f"schema=raveil.graph-device-axi4lite-selected-environment/v1\nplatform=linux/amd64\nimage_id={IMAGE_ID}\n".encode("ascii")
    if env != expected_env: raise GraphDeviceAxi4LiteSelectedError("environment differs")
    toolchain = _read(evidence / "toolchain.txt", 65536)
    if not toolchain.startswith(b"Scala CLI version:") or b"Verilator" not in toolchain: raise GraphDeviceAxi4LiteSelectedError("toolchain differs")
    if _read(evidence / "device.stderr", 1 << 20) or _read(evidence / "container.stderr", 1 << 20): raise GraphDeviceAxi4LiteSelectedError("stderr is not empty")
    log = _read(evidence / "device.log", 4096)
    expected_log = (
        b"GraphDevice-DAG-NEGATIVE-V1 partial=FAULT order=FAULT duplicate=FAULT "
        b"opcode=FAULT undefined=FAULT reserved=FAULT missing_store=FAULT busy=FAULT "
        b"cases=8 output_published=0\n"
        b"GraphDevice-DAG-RUN-V1 graph=five-point seed=1 mode=complete status=COMPLETED "
        b"output_published=1 polls=2817\n"
        b"GraphDevice-DAG-RUN-V1 graph=compact-horizontal-three-point seed=2 mode=complete "
        b"status=COMPLETED output_published=1 polls=449\n"
        b"GraphDevice-DAG-RUN-V1 graph=compact-horizontal-three-point seed=3 mode=cancel "
        b"status=CANCELLED output_published=0 polls=1\n"
        b"GraphDevice-DAG-RUN-V1 graph=vertical-three-point seed=4 mode=complete "
        b"status=COMPLETED output_published=1 polls=1793\n"
        b"GraphDevice-DAG-RUN-V1 graph=five-point seed=5 mode=factory-restart "
        b"status=COMPLETED output_published=1 polls=2817\n"
        b"GraphDevice-DAG-RUNTIME-V1 status=OK graphs=3 completed=4 cancelled=1 "
        b"invalid_cases=8 same_rtl=1 rtl_regeneration=0 "
        b"evidence=rtl-simulation-functional performance=not-measured\n"
    )
    if log != expected_log:
        raise GraphDeviceAxi4LiteSelectedError("runtime outcome differs")
    transcript = _read(evidence / "axi-transcript.log", 8 << 20)
    _validate_transcript(transcript)
    outputs: dict[str, str] = {}
    for invocation in artifact["invocations"]:
        if invocation["mode"] == "cancel": continue
        graph, seed = invocation["graph_id"], invocation["seed"]
        private = _read(evidence / f"private-output-{graph}-seed-{seed}.bin", 1024)
        oracle = _read(evidence / "dag-oracles" / f"{graph}-seed-{seed}.bin", 1024)
        if private != oracle: raise GraphDeviceAxi4LiteSelectedError(f"oracle differs: {graph}/{seed}")
        outputs[f"{graph}:{seed}"] = _sha(private)
    cancelled = evidence / "private-output-compact-horizontal-three-point-seed-3.bin"
    if cancelled.exists(): raise GraphDeviceAxi4LiteSelectedError("cancelled output published")
    return {"schema": SCHEMA, "evidence_class": "rtl-simulation-functional", "performance": "not-measured", "abi": aperture.ABI_HASHES, "source_manifest_sha256": _sha(_read(evidence / "source.manifest")), "rtl_manifest_sha256": _sha(_read(evidence / "rtl-first.manifest")), "simulator_sha256": _sha(simulator), "environment_sha256": _sha(env), "toolchain_sha256": _sha(toolchain), "axi_transactions": AXI_TRANSACTION_COUNT, "axi_transcript_sha256": _sha(transcript), "outputs": outputs}

def finalize(evidence: Path, *, verify_existing: bool = False) -> dict[str, Any]:
    payload = _expected(evidence, verify_existing)
    target = evidence / "receipt.json"; encoded = (json.dumps(payload, sort_keys=True) + "\n").encode("ascii")
    if target.exists():
        if verify_existing and _read(target, 65536) == encoded: return payload
        raise GraphDeviceAxi4LiteSelectedError("append-once receipt exists")
    with target.open("xb") as stream: stream.write(encoded)
    return payload

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("prepare", "finalize", "verify")); parser.add_argument("--output", type=Path); parser.add_argument("--evidence", type=Path); args = parser.parse_args()
    print(json.dumps(prepare(args.output) if args.command == "prepare" else finalize(args.evidence, verify_existing=args.command == "verify"), sort_keys=True))
if __name__ == "__main__": main()
