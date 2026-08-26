"""Private S02 selected-Graph RTL evidence preparation and validation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

from .graph_device_dag import (
    _parse_trace, _require_transactions, compile_artifact, descriptors,
    expected_transactions, graph_oracle, prepare as prepare_dag,
)
from .graph_device_submit import admit
from .riscv_stencil_signature import input_words


SCHEMA = "raveil.graph-device-selected-receipt/v1"
EVIDENCE = "rtl-simulation-functional"
NON_CLAIMS = [
    "arbitrary-graph", "general-graph", "performance", "latency", "throughput",
    "resource", "area", "energy", "emulation", "kv260", "fpga", "asic",
    "silicon", "novelty", "patent", "legal-clearance", "data-publication",
    "experience-authority", "production-security",
]
SOURCE_PATHS = (
    "raveil/graph_device_selected.py", "raveil/graph_device_submit.py",
    "raveil/graph_device_dag.py", "hardware/chisel/graph_device_dag_runtime.h",
    "hardware/chisel/Dockerfile", "hardware/chisel/graph_device_runtime.h",
    "hardware/chisel/graph_device_runtime.cpp", "hardware/chisel/graph_device_affine_runtime.h",
    "hardware/chisel/graph_device_affine_runtime.cpp",
    "hardware/chisel/graph_device_dag_runtime.cpp",
    "hardware/chisel/graph_device_verilator.cpp",
    "hardware/chisel/run-graph-device-dag-in-container.sh",
    "hardware/chisel/run-graph-device-selected.sh",
    "hardware/chisel/OwnedFixedLatencyScratchpad.scala",
    "hardware/chisel/StaticStencilRegion.scala",
    "hardware/chisel/GraphDeviceAffineConfigInstaller.scala",
    "hardware/chisel/GraphDeviceProgramInstaller.scala",
    "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala",
    "hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala",
)
GENERATED_HEADERS = (
    "graph_device_abi_generated.h",
    "graph_device_affine_generated.h",
    "graph_device_dag_generated.h",
)


class GraphDeviceSelectedError(ValueError):
    pass


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _words(words: list[int]) -> bytes:
    return b"".join(word.to_bytes(4, "little") for word in words)


def _read(path: Path, label: str) -> bytes:
    if path.is_symlink():
        raise GraphDeviceSelectedError(f"{label} is a symbolic link")
    try:
        return path.read_bytes()
    except OSError as error:
        raise GraphDeviceSelectedError(f"{label} cannot be read: {error}") from error


def _json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_read(path, label).decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise GraphDeviceSelectedError(f"{label} is not canonical JSON") from error
    if not isinstance(value, dict):
        raise GraphDeviceSelectedError(f"{label} must be an object")
    return value


def _no_symlinks(root: Path) -> None:
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise GraphDeviceSelectedError("evidence contains a symbolic link")


def _sources(repo: Path) -> dict[str, str]:
    result = {}
    for relative in SOURCE_PATHS:
        path = repo / relative
        if path.is_symlink() or not path.is_file():
            raise GraphDeviceSelectedError(f"selected source is missing or linked: {relative}")
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _manifest(payload: bytes) -> None:
    previous = ""
    for line in payload.decode("ascii").splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[0] or fields[0].startswith("/") or ".." in Path(fields[0]).parts or fields[0] <= previous or not fields[1].isdigit() or int(fields[1]) <= 0 or len(fields[2]) != 64 or any(char not in "0123456789abcdef" for char in fields[2]):
            raise GraphDeviceSelectedError("RTL manifest schema changed")
        previous = fields[0]
    if not previous:
        raise GraphDeviceSelectedError("RTL manifest is empty")


def _cache_manifest(payload: bytes) -> None:
    previous = ""
    for line in payload.decode("ascii").splitlines():
        fields = line.split()
        if len(fields) != 3 or not fields[0] or fields[0].startswith("/") or ".." in Path(fields[0]).parts or fields[0] <= previous or not fields[1].isdigit() or int(fields[1]) < 0 or len(fields[2]) != 64 or any(char not in "0123456789abcdef" for char in fields[2]):
            raise GraphDeviceSelectedError("dependency cache manifest schema changed")
        previous = fields[0]
    if not previous:
        raise GraphDeviceSelectedError("dependency cache manifest is empty")


def prepare(graph: str, seed: int, output: Path, repository: Path | None = None) -> dict[str, Any]:
    repo = repository or _root()
    try:
        submission = admit(graph, seed, repo)
    except ValueError as error:
        raise GraphDeviceSelectedError(str(error)) from error
    created = not output.exists()
    if output.is_symlink() or (not created and (not output.is_dir() or any(output.iterdir()))):
        raise GraphDeviceSelectedError("selected evidence output must be new or an empty real directory")
    if created:
        output.mkdir(parents=True)
    try:
        selected = next(item for item in descriptors(repo) if item["graph_id"] == submission["graph_id"])
        artifact = prepare_dag(output)
        program = next(item for item in artifact["graphs"] if item["graph_id"] == submission["graph_id"])
        words = input_words(seed)
        (output / "submission.json").write_bytes(_canonical(submission) + b"\n")
        (output / "selected-artifact.json").write_bytes(_canonical(artifact) + b"\n")
        (output / "selected-sources.json").write_bytes(_canonical(_sources(repo)) + b"\n")
        (output / "input.bin").write_bytes(_words(words))
        (output / "direct-oracle.bin").write_bytes(_words(graph_oracle(selected, words)))
        inputs = output / "inputs"
        (inputs / f"seed-{seed}.bin").write_bytes(_words(words))
        (inputs / "seed-1.bin").write_bytes(_words(input_words(1)))
        return {"submission": submission, "program": program}
    except Exception:
        if created:
            shutil.rmtree(output)
        else:
            for item in output.iterdir():
                if item.is_dir() and not item.is_symlink():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        raise


def _expected_receipt(evidence: Path, repository: Path | None = None) -> dict[str, Any]:
    repo = repository or _root()
    _no_symlinks(evidence)
    submission = _json(evidence / "submission.json", "submission")
    if set(submission) != {"schema", "task", "slice", "graph_path", "graph_id", "descriptor_sha256", "program_sha256", "seed", "evidence_class", "execution", "non_claims"}:
        raise GraphDeviceSelectedError("submission envelope changed")
    if submission != admit(submission["graph_path"], submission["seed"], repo):
        raise GraphDeviceSelectedError("submission does not bind the accepted catalogue")
    artifact = _json(evidence / "selected-artifact.json", "selected artifact")
    if artifact != compile_artifact(repo):
        raise GraphDeviceSelectedError("selected artifact differs from current compiler identity")
    with tempfile.TemporaryDirectory(prefix="raveil-selected-headers-") as temporary:
        regenerated = Path(temporary)
        prepare_dag(regenerated)
        for name in GENERATED_HEADERS:
            if _read(evidence / name, name) != _read(regenerated / name, f"regenerated {name}"):
                raise GraphDeviceSelectedError(f"generated header identity changed: {name}")
    if _json(evidence / "selected-sources.json", "selected sources") != _sources(repo):
        raise GraphDeviceSelectedError("selected source identities differ")
    selected = next((item for item in artifact["graphs"] if item["graph_id"] == submission["graph_id"]), None)
    if selected is None or selected["program_sha256"] != submission["program_sha256"]:
        raise GraphDeviceSelectedError("selected program identity differs")
    expected_input = _words(input_words(submission["seed"]))
    if _read(evidence / "input.bin", "input") != expected_input:
        raise GraphDeviceSelectedError("selected input identity differs")
    descriptor = next(item for item in descriptors(repo) if item["graph_id"] == submission["graph_id"])
    expected_oracle = _words(graph_oracle(descriptor, input_words(submission["seed"])))
    names = ("direct-oracle.bin", f"fallback-output-{submission['graph_id']}-seed-{submission['seed']}.bin", f"private-output-{submission['graph_id']}-seed-{submission['seed']}.bin")
    if any(_read(evidence / name, name) != expected_oracle for name in names):
        raise GraphDeviceSelectedError("selected RTL, fallback, and direct oracle differ")
    try:
        lines = _read(evidence / "device.log", "device log").decode("ascii", "strict").splitlines()
    except UnicodeError as error:
        raise GraphDeviceSelectedError("selected device log is not ASCII") from error
    graph, seed = submission["graph_id"], submission["seed"]
    if len(lines) != 3 or lines[0] != (
        "GraphDevice-DAG-NEGATIVE-V1 partial=FAULT order=FAULT duplicate=FAULT "
        "opcode=FAULT undefined=FAULT reserved=FAULT missing_store=FAULT busy=FAULT "
        "cases=8 output_published=0"
    ) or not lines[1].startswith(
        f"GraphDevice-DAG-RUN-V1 graph={graph} seed={seed} mode=complete "
        "status=COMPLETED output_published=1 polls="
    ) or not lines[1].removeprefix(
        f"GraphDevice-DAG-RUN-V1 graph={graph} seed={seed} mode=complete "
        "status=COMPLETED output_published=1 polls="
    ).isdigit() or lines[2] != (
        f"GraphDevice-DAG-SELECTED-RUNTIME-V1 status=OK graph={graph} seed={seed} "
        "completed=1 invalid_cases=8 same_rtl=1 rtl_regeneration=0 "
        "evidence=rtl-simulation-functional performance=not-measured"
    ):
        raise GraphDeviceSelectedError("selected device log schema or accounting changed")
    for name in ("rtl-first.hashes", "rtl-second.hashes", "rtl-export.sha256", "simulator.sha256", "environment.txt", "toolchain.txt", "toolchain.sha256", "transaction-trace.txt"):
        if not _read(evidence / name, name):
            raise GraphDeviceSelectedError(f"{name} is empty")
    first = _read(evidence / "rtl-first.hashes", "first RTL hashes")
    if first != _read(evidence / "rtl-second.hashes", "second RTL hashes") or hashlib.sha256(first).hexdigest() + "\n" != _read(evidence / "rtl-export.sha256", "RTL aggregate").decode("ascii"):
        raise GraphDeviceSelectedError("RTL identity exports differ")
    hashes = first.decode("ascii").splitlines()
    if not hashes or any(len(item) != 64 or any(char not in "0123456789abcdef" for char in item) for item in hashes):
        raise GraphDeviceSelectedError("RTL file hash format changed")
    simulator = _read(evidence / "simulator.sha256", "simulator hash").decode("ascii").strip()
    if len(simulator) != 64 or any(char not in "0123456789abcdef" for char in simulator):
        raise GraphDeviceSelectedError("simulator hash format changed")
    simulator_bin = _read(evidence / "simulator.bin", "retained simulator")
    if hashlib.sha256(simulator_bin).hexdigest() != simulator:
        raise GraphDeviceSelectedError("retained simulator identity changed")
    environment = _read(evidence / "environment.txt", "environment").decode("ascii").splitlines()
    docker_sha = hashlib.sha256((repo / "hardware/chisel/Dockerfile").read_bytes()).hexdigest()
    image = environment[3][len("image_id="):] if len(environment) == 4 else ""
    if len(environment) != 4 or environment[0] != "schema=raveil.graph-device-selected-environment/v1" or environment[1] != "platform=linux/amd64" or environment[2] != f"dockerfile_sha256={docker_sha}" or len(image) != 71 or not image.startswith("sha256:") or any(char not in "0123456789abcdef" for char in image[7:]):
        raise GraphDeviceSelectedError("selected environment identity changed")
    toolchain = _read(evidence / "toolchain.txt", "toolchain")
    if any(token not in toolchain.decode("ascii") for token in ("Scala CLI", "openjdk", "Verilator")):
        raise GraphDeviceSelectedError("toolchain observation changed")
    if _read(evidence / "toolchain.sha256", "toolchain hash").decode("ascii") != hashlib.sha256(toolchain).hexdigest() + "\n":
        raise GraphDeviceSelectedError("toolchain identity changed")
    try:
        events, segments = _parse_trace(evidence / "transaction-trace.txt")
        by_id = {item["graph_id"]: item for item in artifact["graphs"]}
        expected = expected_transactions(by_id[graph], input_words(seed))
        if events != ["reset"] * 8 + ["start", "cancel", "reset", "reset", "start"] or len(segments) != 2:
            raise GraphDeviceSelectedError("selected trace lifecycle changed")
        _require_transactions(segments[0], expected_transactions(by_id["five-point"], input_words(1)), strict_prefix=True, allow_empty_prefix=True)
        _require_transactions(segments[1], expected, strict_prefix=False)
    except ValueError as error:
        raise GraphDeviceSelectedError(f"selected trace changed: {error}") from error
    first_manifest = _read(evidence / "rtl-first.manifest", "first RTL manifest")
    second_manifest = _read(evidence / "rtl-second.manifest", "second RTL manifest")
    _manifest(first_manifest)
    if first_manifest != second_manifest:
        raise GraphDeviceSelectedError("RTL manifests differ")
    cache_manifest = _read(evidence / "dependency-cache.manifest", "dependency cache manifest")
    _cache_manifest(cache_manifest)
    receipt = {"schema": SCHEMA, "task": "T-0128", "slice": "S02", "status": "complete", "evidence_class": EVIDENCE, "performance": "not-measured", "submission": submission, "artifact_sha256": hashlib.sha256(_read(evidence / "selected-artifact.json", "selected artifact")).hexdigest(), "source_sha256": hashlib.sha256(_canonical(_sources(repo))).hexdigest(), "input_sha256": hashlib.sha256(expected_input).hexdigest(), "oracle_sha256": hashlib.sha256(expected_oracle).hexdigest(), "simulator_sha256": simulator, "rtl_sha256": hashlib.sha256(first_manifest).hexdigest(), "toolchain_sha256": hashlib.sha256(toolchain).hexdigest(), "dependency_cache_sha256": hashlib.sha256(cache_manifest).hexdigest(), "invalid_programs_rejected": 8, "output_published_on_rejection": False, "non_claims": NON_CLAIMS}
    return receipt


def validate_receipt(evidence: Path, repository: Path | None = None) -> dict[str, Any]:
    """Revalidate an append-once selected receipt without changing evidence."""
    receipt = _expected_receipt(evidence, repository)
    existing = _read(evidence / "selected-receipt.json", "selected receipt")
    if existing != _canonical(receipt) + b"\n":
        raise GraphDeviceSelectedError("selected receipt identity changed")
    return receipt


def finalize(evidence: Path, repository: Path | None = None) -> dict[str, Any]:
    receipt = _expected_receipt(evidence, repository)
    target = evidence / "selected-receipt.json"
    try:
        with target.open("xb") as stream:
            stream.write(_canonical(receipt) + b"\n")
    except FileExistsError as error:
        raise GraphDeviceSelectedError("selected receipt is append-once") from error
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "prepare"):
        command = commands.add_parser(name)
        command.add_argument("--graph", required=True)
        command.add_argument("--seed", type=int, required=True)
        if name == "prepare": command.add_argument("--output", required=True, type=Path)
    finish = commands.add_parser("finalize")
    finish.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate": print(json.dumps(admit(args.graph, args.seed), sort_keys=True, separators=(",", ":")))
        elif args.command == "prepare": prepare(args.graph, args.seed, args.output)
        else: print(json.dumps(finalize(args.evidence), sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
