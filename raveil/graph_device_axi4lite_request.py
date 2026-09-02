"""Private S05 AXI4-Lite evidence for one admitted Graph-device request.

The descriptor admission is performed before this module is invoked.  This
module never accepts a graph identifier as a substitute for that admission;
the evidence carries the admitted request bytes and runs the existing selected
DAG runtime through the unchanged AXI4-Lite top.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import struct
from pathlib import Path
from typing import Any

from . import graph_device_axi4lite as aperture
from . import graph_device_affine as affine_artifact
from . import graph_device_dag as dag
from . import graph_device_mvp as mvp
from .graph_device_affine import config_words, profile
from .graph_device_submit import admit
from .riscv_stencil_signature import input_words

ROOT = aperture.ROOT
IMAGE_ID = "sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c"
SCHEMA = "raveil.graph-device-axi4lite-request-receipt/v1"
GENERATED = {
    "abi.sha256", "graph_device_axi4lite_aperture_generated.h",
    "graph_device_abi_generated.h", "graph_device_affine_generated.h",
    "graph_device_dag_generated.h", "dag-artifact.json", "request.json",
    "request-input.bin", "request-oracle.bin", "uio-request.bin",
    "graph_device_uio_request_generated.h",
}
SOURCE_FILES = (
    "hardware/chisel/GraphDeviceAxi4LiteTop.scala", "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala", "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala", "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala", "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp", "hardware/chisel/graph_device_affine_runtime.h",
    "hardware/chisel/graph_device_affine_runtime.cpp", "hardware/chisel/graph_device_dag_runtime.h",
    "hardware/chisel/graph_device_dag_runtime.cpp", "hardware/chisel/graph_device_axi4lite_request_verilator.cpp",
    "hardware/chisel/graph_device_axi4lite_transport.h",
    "hardware/chisel/run-graph-device-axi4lite-request.sh", "hardware/chisel/run-graph-device-axi4lite-request-in-container.sh",
    "hardware/chisel/run-graph-device-axi4lite-runtime-demo.sh",
    "linux/include/raveil_graph_device_request.h", "linux/src/raveil_graph_device_request.cpp",
    "contracts/graph_device_axi4lite_aperture_v1.json", "raveil/graph_device_axi4lite.py",
    "raveil/graph_device_axi4lite_request.py", "raveil/graph_device_dag.py", "raveil/graph_device_affine.py",
    "raveil/graph_device_mvp.py", "raveil/graph_device_submit.py", "raveil/riscv_stencil_signature.py",
    "hardware/chisel/Dockerfile", *sorted(GENERATED),
)
_WRITE = re.compile(r"^AXI4LITE-TRACE-V1 seq=([0-9]+) op=write address=0x([0-9a-f]{8}) data=0x([0-9a-f]{8}) strobe=0xf response=([0-3]) held_b=0$")
_READ = re.compile(r"^AXI4LITE-TRACE-V1 seq=([0-9]+) op=read address=0x([0-9a-f]{8}) data=0x([0-9a-f]{8}) response=([0-3]) held_r=0$")
_NEGATIVE_PREFIX_LINES = 507
_NEGATIVE_PREFIX_SHA256 = "fc17f2cc396d43da483faedff28b41f4f3f5f2b15add8407524c4562ad9958b7"

class GraphDeviceAxi4LiteRequestError(RuntimeError): pass
def _sha(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def _canonical(value: Any) -> bytes: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
def _words(words: list[int]) -> bytes: return struct.pack(f"<{len(words)}I", *words)
def _uio_header(submission: dict[str, Any], binding: bytes, input_bytes: bytes) -> bytes:
    def array(name: str, payload: bytes) -> str:
        values = ", ".join(f"0x{value:02x}U" for value in payload)
        return f"inline constexpr std::array<unsigned char, {len(payload)}> {name} = {{{values}}};"
    request = _canonical(submission) + b"\n"
    return ("\n".join((
        "#ifndef RAVEIL_GRAPH_DEVICE_UIO_REQUEST_GENERATED_H",
        "#define RAVEIL_GRAPH_DEVICE_UIO_REQUEST_GENERATED_H",
        "#include <array>",
        "#include <cstdint>",
        "namespace raveil::graph_device::uio_request_generated {",
        f'inline constexpr const char* kGraphId = "{submission["graph_id"]}";',
        f'inline constexpr std::uint32_t kSeed = {submission["seed"]}U;',
        array("kBinding", binding),
        array("kRequestJson", request),
        array("kInput", input_bytes),
        "}",
        "#endif",
        "",
    ))).encode("ascii")
def _read(path: Path, limit: int = 32 << 20) -> bytes:
    try: info = path.lstat()
    except OSError as exc: raise GraphDeviceAxi4LiteRequestError(f"missing {path.name}") from exc
    if not stat.S_ISREG(info.st_mode) or info.st_size > limit: raise GraphDeviceAxi4LiteRequestError(f"unsafe {path.name}")
    return path.read_bytes()
def _source(evidence: Path, name: str) -> Path: return evidence / name if name in GENERATED else ROOT / name
def _manifest(path: Path) -> list[str]:
    lines = _read(path, 1 << 20).decode("ascii").splitlines()
    if not lines or lines != sorted(lines): raise GraphDeviceAxi4LiteRequestError("manifest order differs")
    for line in lines:
        name, sep, digest = line.partition(" ")
        if not sep or not name or name.startswith("/") or ".." in Path(name).parts or not re.fullmatch(r"[0-9a-f]{64}", digest): raise GraphDeviceAxi4LiteRequestError("manifest schema differs")
    return lines

def prepare(output: Path, submission: dict[str, Any]) -> dict[str, Any]:
    """Create only deterministic, private request inputs before simulation."""
    expected = admit(submission["graph_path"], submission["seed"], ROOT)
    if submission != expected: raise GraphDeviceAxi4LiteRequestError("request is not an admitted canonical submission")
    artifact = dag.prepare(output); aperture._verify_abis()
    descriptor = dag.load_descriptor(ROOT / submission["graph_path"])
    words = input_words(submission["seed"]); oracle = dag.graph_oracle(descriptor, words)
    (output / "graph_device_axi4lite_aperture_generated.h").write_bytes(aperture._header())
    (output / "abi.sha256").write_text("".join(f"{value}  {name}\n" for name, value in sorted(aperture.ABI_HASHES.items())), encoding="ascii")
    request_bytes = _canonical(submission) + b"\n"
    input_bytes = _words(words)
    (output / "request.json").write_bytes(request_bytes)
    (output / "request-input.bin").write_bytes(input_bytes)
    (output / "request-oracle.bin").write_bytes(_words(oracle))
    graph_ids = [item["graph_id"] for item in dag.descriptors(ROOT)]
    binding = struct.pack(
        "<5I", 0x52555131, 1, 20, graph_ids.index(submission["graph_id"]),
        submission["seed"],
    )
    (output / "uio-request.bin").write_bytes(binding)
    (output / "graph_device_uio_request_generated.h").write_bytes(
        _uio_header(submission, binding, input_bytes)
    )
    (output / "inputs" / f"seed-{submission['seed']}.bin").write_bytes(_words(words))
    return artifact

def _request(evidence: Path) -> dict[str, Any]:
    try: value = json.loads(_read(evidence / "request.json", 8192).decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as exc: raise GraphDeviceAxi4LiteRequestError("request encoding differs") from exc
    if not isinstance(value, dict): raise GraphDeviceAxi4LiteRequestError("request is not an object")
    try: expected = admit(value["graph_path"], value["seed"], ROOT)
    except (KeyError, ValueError) as exc: raise GraphDeviceAxi4LiteRequestError("request admission differs") from exc
    if value != expected or _read(evidence / "request.json") != _canonical(value) + b"\n": raise GraphDeviceAxi4LiteRequestError("request identity differs")
    return value

def _reject_tree(evidence: Path, submission: dict[str, Any]) -> None:
    graph, seed = submission["graph_id"], submission["seed"]
    expected = {
        "abi.sha256", "affine-artifact.json", "artifact.json", "axi-transcript.log", "config-baseline.bin", "config-compact.bin",
        "container.stderr", "container.stdout", "dag-artifact.json", "dag-oracles", "dag-programs", "device.log", "device.stderr",
        "emit-first.stderr", "emit-first.stdout", "emit-second.stderr", "emit-second.stdout", "environment.txt", "graph_device_abi_generated.h",
        "graph_device_affine_generated.h", "graph_device_axi4lite_aperture_generated.h", "graph_device_dag_generated.h", "inputs", "oracles",
        "rtl-first", "rtl-first.manifest", "rtl-second", "rtl-second.manifest", "simulator.bin", "simulator.sha256", "source.manifest",
        "toolchain.txt", "verilator.stderr", "verilator.stdout", "request.json", "request-input.bin", "request-oracle.bin", "uio-request.bin", "graph_device_uio_request_generated.h",
        f"fallback-output-{graph}-seed-{seed}.bin", f"private-output-{graph}-seed-{seed}.bin",
    }
    actual = {item.name for item in evidence.iterdir()}
    if actual not in (expected, expected | {"receipt.json"}): raise GraphDeviceAxi4LiteRequestError("evidence top-level allowlist differs")
    for item in evidence.rglob("*"):
        if not (stat.S_ISREG(item.lstat().st_mode) or stat.S_ISDIR(item.lstat().st_mode)): raise GraphDeviceAxi4LiteRequestError("evidence contains link or special file")
    nested = {
        "inputs": {f"seed-{number}.bin" for number in range(1, 6)} | {f"seed-{seed}.bin"},
        "dag-programs": {"five-point.bin", "compact-horizontal-three-point.bin", "vertical-three-point.bin"},
        "dag-oracles": {"five-point-seed-1.bin", "five-point-seed-5.bin", "compact-horizontal-three-point-seed-2.bin", "compact-horizontal-three-point-seed-3.bin", "vertical-three-point-seed-4.bin"},
        "oracles": {"baseline-seed-1.bin", "baseline-seed-2.bin", "baseline-seed-3.bin", "baseline-seed-4.bin", "compact-seed-1.bin", "compact-seed-2.bin", "compact-seed-3.bin", "compact-seed-4.bin", "seed-1.bin", "seed-2.bin", "seed-3.bin"},
    }
    for name, allowed in nested.items():
        files = {str(path.relative_to(evidence / name)) for path in (evidence / name).rglob("*") if path.is_file()}
        if files != allowed: raise GraphDeviceAxi4LiteRequestError(f"evidence nested allowlist differs: {name}")

def _validate_rtl_tree(evidence: Path, manifest: list[str]) -> None:
    expected_files = {line.partition(" ")[0] for line in manifest} | {"filelist.f"}
    expected_dirs = {"verification", "verification/assert", "verification/assume", "verification/cover"}
    for name in ("rtl-first", "rtl-second"):
        root = evidence / name
        files = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
        directories = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_dir()}
        if files != expected_files or directories != expected_dirs: raise GraphDeviceAxi4LiteRequestError("RTL evidence allowlist differs")

def _trace(payload: bytes, submission: dict[str, Any]) -> int:
    """Validate all records plus the final selected runtime lifecycle exactly.

    The negative matrix is intentionally retained as a preceding, syntactically
    complete AXI trace.  The selected execution suffix is request-dependent and
    checked word-for-word: reset/install/stage/start/polls/output reads.
    """
    try: raw = payload.decode("ascii").splitlines()
    except UnicodeError as exc: raise GraphDeviceAxi4LiteRequestError("AXI transcript is not ASCII") from exc
    if not raw or not payload.endswith(b"\n"): raise GraphDeviceAxi4LiteRequestError("AXI transcript is empty")
    if len(raw) <= _NEGATIVE_PREFIX_LINES or _sha(("\n".join(raw[:_NEGATIVE_PREFIX_LINES]) + "\n").encode("ascii")) != _NEGATIVE_PREFIX_SHA256:
        raise GraphDeviceAxi4LiteRequestError("AXI negative matrix prefix differs")
    records: list[tuple[str, int, int]] = []
    for seq, line in enumerate(raw):
        match = _WRITE.fullmatch(line) or _READ.fullmatch(line)
        if match is None or int(match.group(1)) != seq: raise GraphDeviceAxi4LiteRequestError("AXI transcript schema differs")
        op, address, data = ("write" if _WRITE.fullmatch(line) else "read"), int(match.group(2), 16), int(match.group(3), 16)
        if address >= 0x4000 or address % 4 or int(match.group(4)) != 0: raise GraphDeviceAxi4LiteRequestError("AXI transcript response or address differs")
        records.append((op, address, data))
    # Final invocation must include all 324 request-specific staging writes,
    # a start, deterministic terminal polling, and all 256 oracle reads.
    descriptor = dag.load_descriptor(ROOT / submission["graph_path"]); program = dag.compile_descriptor(descriptor)
    affine = program["affine"]; profile_name = "baseline" if affine["rows"] == 16 else "compact"
    affine_payload = config_words(profile(profile_name))
    exec_base, config_base, program_base = 0x0000, 0x2000, 0x3000
    words, oracle = input_words(submission["seed"]), dag.graph_oracle(descriptor, input_words(submission["seed"]))
    polls = {"five-point": 2817, "compact-horizontal-three-point": 449, "vertical-three-point": 1793}[submission["graph_id"]]
    # Locate last reset then require exact install/staging lifecycle after it.
    reset = ("write", exec_base + 0x10, 4)
    try: start = max(index for index, item in enumerate(records) if item == reset)
    except ValueError as exc: raise GraphDeviceAxi4LiteRequestError("AXI selected reset absent") from exc
    if start != _NEGATIVE_PREFIX_LINES:
        raise GraphDeviceAxi4LiteRequestError("AXI prefix and selected lifecycle are not contiguous")
    tail = records[start:]; expected_prefix = [reset, ("write", config_base + 0x10, 1)]
    # Affine payloads and program payload are recorded in generated artifacts;
    # check address lifecycle/count here and bind their bytes through headers.
    if tail[:2] != expected_prefix: raise GraphDeviceAxi4LiteRequestError("AXI selected lifecycle differs")
    cursor = 2
    if tail[cursor:cursor + 16] != [("write", config_base + 4 * (256 + n), value) for n, value in enumerate(affine_payload)]: raise GraphDeviceAxi4LiteRequestError("AXI affine payload lifecycle differs")
    cursor += 16
    if tail[cursor][:2] != ("write", config_base + 0x10) or tail[cursor][2] != 2 or tail[cursor + 1][:2] != ("read", config_base + 0x14) or tail[cursor + 1][2] != 2: raise GraphDeviceAxi4LiteRequestError("AXI affine commit lifecycle differs")
    cursor += 2
    if tail[cursor] != ("write", program_base + 0x10, 1): raise GraphDeviceAxi4LiteRequestError("AXI program clear differs")
    cursor += 1
    for number in range(32):
        if tail[cursor] != ("write", program_base + 4 * (256 + number), program["payload"][number]) or tail[cursor + 1] != ("read", program_base + 0x18, number + 1): raise GraphDeviceAxi4LiteRequestError("AXI program payload lifecycle differs")
        cursor += 2
    if tail[cursor] != ("write", program_base + 0x10, 2): raise GraphDeviceAxi4LiteRequestError("AXI program commit differs")
    cursor += 1
    if tail[cursor] != ("read", program_base + 0x14, 2): raise GraphDeviceAxi4LiteRequestError("AXI program status differs")
    cursor += 1
    if tail[cursor:cursor + 8] != [("read", program_base + 4 * (16 + n), value) for n, value in enumerate(program["payload"][4:12])]: raise GraphDeviceAxi4LiteRequestError("AXI program digest lifecycle differs")
    cursor += 8
    expected_stage = [("write", exec_base + 4 * (256 + n), word) for n, word in enumerate(words)]
    if tail[cursor:cursor + 324] != expected_stage: raise GraphDeviceAxi4LiteRequestError("AXI request input staging differs")
    cursor += 324
    if tail[cursor] != ("write", exec_base + 0x10, 1): raise GraphDeviceAxi4LiteRequestError("AXI start differs")
    cursor += 1
    status_address = exec_base + 0x14
    if (len(tail[cursor:cursor + polls]) != polls
            or tail[cursor:cursor + polls - 1] != [("read", status_address, 1)] * (polls - 1)
            or tail[cursor + polls - 1] != ("read", status_address, 18)):
        raise GraphDeviceAxi4LiteRequestError("AXI terminal polls differ")
    cursor += polls
    expected_output = [("read", exec_base + 4 * (1024 + n), word) for n, word in enumerate(oracle)]
    if tail[cursor:] != expected_output: raise GraphDeviceAxi4LiteRequestError("AXI private output lifecycle differs")
    return len(records)

def _expected(evidence: Path) -> dict[str, Any]:
    if evidence.is_symlink(): raise GraphDeviceAxi4LiteRequestError("evidence symlink")
    evidence = evidence.resolve(strict=True)
    if ROOT not in evidence.parents: raise GraphDeviceAxi4LiteRequestError("evidence escapes repository")
    submission = _request(evidence); _reject_tree(evidence, submission); aperture._verify_abis()
    expected_abi = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(aperture.ABI_HASHES.items())
    ).encode("ascii")
    if _read(evidence / "abi.sha256", 1024) != expected_abi:
        raise GraphDeviceAxi4LiteRequestError("ABI identity export differs")
    if _read(evidence / "graph_device_axi4lite_aperture_generated.h") != aperture._header(): raise GraphDeviceAxi4LiteRequestError("aperture header drifted")
    base = mvp.compile_artifact()
    if (_read(evidence / "artifact.json") != _canonical(base) + b"\n"
            or _read(evidence / "graph_device_abi_generated.h")
            != mvp._generated_header(base, mvp.load_device_abi())):
        raise GraphDeviceAxi4LiteRequestError("execution artifact or header differs")
    installed_affine = affine_artifact.compile_artifact()
    if (_read(evidence / "affine-artifact.json") != _canonical(installed_affine) + b"\n"
            or _read(evidence / "graph_device_affine_generated.h")
            != affine_artifact._generated_header()):
        raise GraphDeviceAxi4LiteRequestError("affine artifact or header differs")
    dag_artifact = dag.compile_artifact()
    if (_read(evidence / "dag-artifact.json") != _canonical(dag_artifact) + b"\n"
            or _read(evidence / "graph_device_dag_generated.h")
            != dag._generated_header(dag_artifact)):
        raise GraphDeviceAxi4LiteRequestError("DAG artifact or header differs")
    if _read(evidence / "request-input.bin") != _words(input_words(submission["seed"])): raise GraphDeviceAxi4LiteRequestError("request input differs")
    graph_ids = [item["graph_id"] for item in dag.descriptors(ROOT)]
    expected_uio_request = struct.pack(
        "<5I", 0x52555131, 1, 20, graph_ids.index(submission["graph_id"]),
        submission["seed"],
    )
    if _read(evidence / "uio-request.bin", 20) != expected_uio_request: raise GraphDeviceAxi4LiteRequestError("UIO request binding differs")
    if (_read(evidence / "graph_device_uio_request_generated.h", 1 << 20)
            != _uio_header(submission, expected_uio_request, _words(input_words(submission["seed"])))):
        raise GraphDeviceAxi4LiteRequestError("UIO compiled request binding differs")
    descriptor = dag.load_descriptor(ROOT / submission["graph_path"])
    oracle = _words(dag.graph_oracle(descriptor, input_words(submission["seed"])))
    if _read(evidence / "request-oracle.bin") != oracle: raise GraphDeviceAxi4LiteRequestError("request oracle differs")
    manifest = _manifest(evidence / "source.manifest")
    if tuple(line.partition(" ")[0] for line in manifest) != tuple(sorted(SOURCE_FILES)): raise GraphDeviceAxi4LiteRequestError("source set differs")
    for line in manifest:
        name, _, digest = line.partition(" ")
        if _sha(_read(_source(evidence, name))) != digest: raise GraphDeviceAxi4LiteRequestError(f"source digest differs: {name}")
    first, second = _manifest(evidence / "rtl-first.manifest"), _manifest(evidence / "rtl-second.manifest")
    if _read(evidence / "rtl-first.manifest") != _read(evidence / "rtl-second.manifest"): raise GraphDeviceAxi4LiteRequestError("RTL elaborations differ")
    for line in first:
        name, _, digest = line.partition(" ")
        if _sha(_read(evidence / "rtl-first" / name)) != digest or _sha(_read(evidence / "rtl-second" / name)) != digest: raise GraphDeviceAxi4LiteRequestError("RTL manifest binding differs")
    _validate_rtl_tree(evidence, first)
    simulator = _read(evidence / "simulator.bin", 64 << 20)
    if _read(evidence / "simulator.sha256", 128).decode("ascii").strip() != _sha(simulator): raise GraphDeviceAxi4LiteRequestError("simulator digest differs")
    environment = _read(evidence / "environment.txt", 1024)
    if environment != f"schema=raveil.graph-device-axi4lite-request-environment/v1\nplatform=linux/amd64\nimage_id={IMAGE_ID}\n".encode("ascii"): raise GraphDeviceAxi4LiteRequestError("environment differs")
    if _read(evidence / "device.stderr", 1 << 20) or _read(evidence / "container.stderr", 1 << 20): raise GraphDeviceAxi4LiteRequestError("stderr is not empty")
    log = _read(evidence / "device.log", 4096)
    expected_log = (f"GraphDevice-DAG-NEGATIVE-V1 partial=FAULT order=FAULT duplicate=FAULT opcode=FAULT undefined=FAULT reserved=FAULT missing_store=FAULT busy=FAULT cases=8 output_published=0\nGraphDevice-DAG-RUN-V1 graph={submission['graph_id']} seed={submission['seed']} mode=complete status=COMPLETED output_published=1 polls={ {'five-point': 2817, 'compact-horizontal-three-point': 449, 'vertical-three-point': 1793}[submission['graph_id']] }\nGraphDevice-DAG-SELECTED-RUNTIME-V1 status=OK graph={submission['graph_id']} seed={submission['seed']} completed=1 invalid_cases=8 same_rtl=1 rtl_regeneration=0 evidence=rtl-simulation-functional performance=not-measured\n").encode("ascii")
    if log != expected_log: raise GraphDeviceAxi4LiteRequestError("runtime outcome differs")
    private = _read(evidence / f"private-output-{submission['graph_id']}-seed-{submission['seed']}.bin", 1024)
    if private != oracle: raise GraphDeviceAxi4LiteRequestError("private output differs from independent oracle")
    transcript = _read(evidence / "axi-transcript.log", 32 << 20); count = _trace(transcript, submission)
    toolchain = _read(evidence / "toolchain.txt", 65536)
    if not toolchain.startswith(b"Scala CLI version:") or b"Verilator" not in toolchain: raise GraphDeviceAxi4LiteRequestError("toolchain differs")
    return {"schema": SCHEMA, "submission": submission, "evidence_class": "rtl-simulation-functional", "performance": "not-measured", "abi": aperture.ABI_HASHES, "source_manifest_sha256": _sha(_read(evidence / "source.manifest")), "rtl_manifest_sha256": _sha(_read(evidence / "rtl-first.manifest")), "simulator_sha256": _sha(simulator), "environment_sha256": _sha(environment), "toolchain_sha256": _sha(toolchain), "axi_transactions": count, "axi_transcript_sha256": _sha(transcript), "output_sha256": _sha(private), "oracle_sha256": _sha(oracle)}

def finalize(evidence: Path, *, verify_existing: bool = False) -> dict[str, Any]:
    payload = _expected(evidence); target = evidence / "receipt.json"; encoded = _canonical(payload) + b"\n"
    if target.exists():
        if verify_existing and _read(target, 65536) == encoded: return payload
        raise GraphDeviceAxi4LiteRequestError("append-once receipt exists")
    with target.open("xb") as stream: stream.write(encoded)
    return payload

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("prepare", "finalize", "verify")); parser.add_argument("--output", type=Path); parser.add_argument("--evidence", type=Path); parser.add_argument("--graph"); parser.add_argument("--seed", type=int); args = parser.parse_args()
    if args.command == "prepare":
        if args.graph is None or args.seed is None: parser.error("prepare requires --graph and --seed")
        result = prepare(args.output, admit(args.graph, args.seed, ROOT))
    else: result = finalize(args.evidence, verify_existing=args.command == "verify")
    print(json.dumps(result, sort_keys=True))
if __name__ == "__main__": main()
