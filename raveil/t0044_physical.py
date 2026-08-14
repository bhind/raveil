from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
from typing import Any


SCHEMA = "raveil.t0044-physical-screen/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
AREA_RE = re.compile(r"Chip area for module '\\(?P<top>[^']+)': (?P<area>[0-9.]+)")
SLACK_RE = re.compile(r"(?P<slack>-?[0-9.]+)\s+slack \((?P<status>MET|VIOLATED)\)")
STARTPOINT_RE = re.compile(r"^Startpoint:\s+(?P<value>\S+)", re.MULTILINE)
ENDPOINT_RE = re.compile(r"^Endpoint:\s+(?P<value>\S+)", re.MULTILINE)
PATH_GROUP_RE = re.compile(r"^Path Group:\s+(?P<value>\S+)", re.MULTILINE)
RAW_REQUIRED = {
    "blackboxes.txt",
    "container.log",
    "constraint.sdc",
    "mapped.v",
    "opensta.log",
    "rtl-files.txt",
    "run-metadata.json",
    "stat.json",
    "synthesis.ys",
    "timing.tcl",
    "tool-identity.txt",
    "yosys.log",
}


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(path: pathlib.Path) -> str:
    if not path.is_dir():
        raise ValueError(f"tree is not a directory: {path}")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise ValueError("tree has no files")
    for item in files:
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data_hash = bytes.fromhex(sha256_file(item))
        digest.update(data_hash)
    return digest.hexdigest()


def file_map_sha256(path: pathlib.Path, *, excluded: set[str] | None = None) -> dict[str, str]:
    excluded = excluded or set()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    result = {
        item.relative_to(path).as_posix(): sha256_file(item)
        for item in files
        if item.relative_to(path).as_posix() not in excluded
    }
    if not result:
        raise ValueError("tree has no admitted files")
    return result


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _field(document: dict[str, Any], dotted: str) -> Any:
    value: Any = document
    for component in dotted.split("."):
        if not isinstance(value, dict) or component not in value:
            raise ValueError(f"missing manifest field: {dotted}")
        value = value[component]
    return value


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    document = json.loads(path.read_text())
    if document.get("schema") != SCHEMA or document.get("status") != "frozen":
        raise ValueError("manifest is not the frozen EXP-0009 schema")
    if document.get("experiment_id") != "EXP-0009" or document.get("task_id") != "T-0044":
        raise ValueError("manifest authority IDs are wrong")
    if document.get("matrix") != ["static-graph", "rocket-in-order"]:
        raise ValueError("physical screening matrix drift")
    if document.get("clock_period_ns") != 20.0:
        raise ValueError("clock constraint drift")
    if document.get("constraints") != {
        "clock_port": "clock",
        "input_delay_ns": 1.0,
        "output_delay_ns": 1.0,
    }:
        raise ValueError("I/O constraint drift")
    if document.get("corner") != "sky130_fd_sc_hd__tt_025C_1v80":
        raise ValueError("physical corner drift")
    if document.get("partition_policy") != {
        "common_fixture": "excluded-at-explicit-candidate-boundary",
        "common_memory": "excluded-at-explicit-candidate-boundary",
        "fallback_composition": "rocket-fallback-plus-graph-incremental",
        "whole_system_claim": False,
    }:
        raise ValueError("partition policy drift")
    collector_policy = document.get("collector_policy")
    if collector_policy is not None and collector_policy != {
        "blackbox_selection_mode": "yosys-module-name-single-instance-v1",
        "blackbox_before_checked_hierarchy": True,
    }:
        raise ValueError("collector policy drift")
    toolchain = document.get("toolchain")
    if not isinstance(toolchain, dict):
        raise ValueError("toolchain identity is missing")
    for name in (
        "image_id",
        "yosys_sha256",
        "opensta_sha256",
        "liberty_sha256",
        "conda_environment_sha256",
        "system_packages_sha256",
    ):
        value = toolchain.get(name)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value.removeprefix("sha256:")):
            raise ValueError(f"invalid toolchain identity: {name}")
    authority = document.get("implementation_authority")
    if not isinstance(authority, str) or not re.fullmatch(r"[0-9a-f]{40}", authority):
        raise ValueError("implementation authority is not a full commit")
    if document.get("decision_rules") != {
        "incremental_area_ratio_no_go_above": 0.25,
        "graph_timing_miss_only_if_rocket_meets": True,
        "pass_label": "advance-to-integrated-physical",
        "incomplete_label": "pause-boundary",
    }:
        raise ValueError("decision rule drift")
    if document.get("report_contract") != {
        "raw_schema": "raveil.t0044-physical-run/v1",
        "result_schema": "raveil.t0044-physical-result/v1",
        "matrix_schema": "raveil.t0044-physical-matrix/v1",
        "deterministic_reruns_are_samples": False,
        "evidence_class": "synthesis-estimate",
    }:
        raise ValueError("report contract drift")
    for variant in document["matrix"]:
        _variant_contract(document, variant)
    return document


def verify_authority(manifest: dict[str, Any]) -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    authority = manifest["implementation_authority"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", authority, "HEAD"],
        cwd=root,
        check=True,
    )


def _variant_contract(manifest: dict[str, Any], variant: str) -> dict[str, Any]:
    variants = manifest.get("variants")
    if not isinstance(variants, dict) or set(variants) != set(manifest["matrix"]):
        raise ValueError("variant contracts do not match the frozen matrix")
    contract = variants.get(variant)
    if not isinstance(contract, dict):
        raise ValueError("variant contract is missing")
    if not isinstance(contract.get("top"), str) or not contract["top"]:
        raise ValueError("variant top is missing")
    blackboxes = contract.get("blackboxes")
    if not isinstance(blackboxes, list) or not all(
        isinstance(item, str) and item for item in blackboxes
    ):
        raise ValueError("variant blackboxes are invalid")
    if not SHA256_RE.fullmatch(str(contract.get("rtl_sha256", ""))):
        raise ValueError("variant RTL identity is invalid")
    if contract.get("partition_role") not in {
        "graph-candidate-local-incremental",
        "rocket-fallback-denominator",
    }:
        raise ValueError("variant partition role is invalid")
    if not isinstance(contract.get("configuration_id"), str) or not contract[
        "configuration_id"
    ]:
        raise ValueError("variant configuration identity is missing")
    for name in ("source_sha256", "generator_image_id"):
        value = str(contract.get(name, "")).removeprefix("sha256:")
        if not SHA256_RE.fullmatch(value):
            raise ValueError(f"variant generation identity is invalid: {name}")
    if contract.get("clock_port") != "clock":
        raise ValueError("variant clock port drift")
    missing = contract.get("missing_components")
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        raise ValueError("variant missing-component declaration is invalid")
    return contract


def variant_field(manifest: dict[str, Any], variant: str, field: str) -> str:
    contract = _variant_contract(manifest, variant)
    if field == "blackboxes":
        return ",".join(contract["blackboxes"])
    if field != "top":
        raise ValueError("unsupported variant field")
    return contract[field]


def _verify_variant_inputs(
    manifest: dict[str, Any], variant: str, top: str, blackboxes: str, rtl_dir: pathlib.Path
) -> str:
    contract = _variant_contract(manifest, variant)
    if top != contract["top"]:
        raise ValueError("variant top drift")
    requested_blackboxes = [] if not blackboxes else blackboxes.split(",")
    if requested_blackboxes != contract["blackboxes"]:
        raise ValueError("variant blackbox drift")
    rtl_sha256 = tree_sha256(rtl_dir)
    if rtl_sha256 != contract["rtl_sha256"]:
        raise ValueError("variant RTL identity drift")
    return rtl_sha256


def write_run_metadata(
    manifest_path: pathlib.Path,
    variant: str,
    top: str,
    blackboxes: str,
    rtl_dir: pathlib.Path,
    raw_dir: pathlib.Path,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    verify_authority(manifest)
    if variant not in manifest["matrix"]:
        raise ValueError("variant is outside the frozen matrix")
    rtl_sha256 = _verify_variant_inputs(manifest, variant, top, blackboxes, rtl_dir)
    metadata = {
        "schema": "raveil.t0044-physical-run/v1",
        "experiment_id": "EXP-0009",
        "variant": variant,
        "top": top,
        "blackboxes": [] if not blackboxes else blackboxes.split(","),
        "rtl_sha256": rtl_sha256,
        "manifest_sha256": sha256_file(manifest_path),
        "toolchain_image_id": manifest["toolchain"]["image_id"],
        "clock_period_ns": manifest["clock_period_ns"],
        "corner": "sky130_fd_sc_hd__tt_025C_1v80",
        "container_exit_code": 0,
        "network": "none",
        "performance": "candidate-data",
        "evidence_class": "synthesis-estimate",
    }
    output = raw_dir / "run-metadata.json"
    if output.exists():
        raise ValueError("raw run metadata already exists")
    output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return metadata


def seal_raw(
    manifest_path: pathlib.Path, variant: str, raw_dir: pathlib.Path
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    verify_authority(manifest)
    _variant_contract(manifest, variant)
    seal_path = raw_dir / "raw-seal.json"
    if seal_path.exists():
        raise ValueError("raw evidence is already sealed")
    names = {item.relative_to(raw_dir).as_posix() for item in raw_dir.rglob("*") if item.is_file()}
    if names != RAW_REQUIRED:
        raise ValueError(f"raw evidence file set drift: {sorted(names ^ RAW_REQUIRED)}")
    files = file_map_sha256(raw_dir)
    seal = {
        "schema": "raveil.t0044-physical-raw-seal/v1",
        "experiment_id": "EXP-0009",
        "variant": variant,
        "manifest_sha256": sha256_file(manifest_path),
        "files": files,
        "files_sha256": canonical_sha256(files),
    }
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    return seal


def record_failure(
    manifest_path: pathlib.Path,
    variant: str,
    rtl_dir: pathlib.Path,
    raw_dir: pathlib.Path,
    container_exit_code: int,
) -> dict[str, Any]:
    if container_exit_code == 0:
        raise ValueError("failure record requires a nonzero exit code")
    manifest = load_manifest(manifest_path)
    verify_authority(manifest)
    contract = _variant_contract(manifest, variant)
    rtl_sha256 = _verify_variant_inputs(
        manifest, variant, contract["top"], ",".join(contract["blackboxes"]), rtl_dir
    )
    metadata_path = raw_dir / "failure-metadata.json"
    seal_path = raw_dir / "failed-seal.json"
    if metadata_path.exists() or seal_path.exists():
        raise ValueError("failed raw evidence is already sealed")
    metadata = {
        "schema": "raveil.t0044-physical-failure/v1",
        "experiment_id": "EXP-0009",
        "variant": variant,
        "rtl_sha256": rtl_sha256,
        "manifest_sha256": sha256_file(manifest_path),
        "container_exit_code": container_exit_code,
        "eligibility": "ineligible-operational-failure",
        "performance_claim": False,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    files = file_map_sha256(raw_dir)
    seal = {
        "schema": "raveil.t0044-physical-failed-seal/v1",
        "experiment_id": "EXP-0009",
        "variant": variant,
        "files": files,
        "files_sha256": canonical_sha256(files),
    }
    seal_path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    return seal


def _load_verified_seal(
    manifest_path: pathlib.Path, variant: str, raw_dir: pathlib.Path
) -> dict[str, Any]:
    seal_path = raw_dir / "raw-seal.json"
    if not seal_path.is_file():
        raise ValueError("raw evidence is not sealed")
    seal = json.loads(seal_path.read_text())
    if seal.get("schema") != "raveil.t0044-physical-raw-seal/v1":
        raise ValueError("raw seal schema drift")
    if seal.get("variant") != variant or seal.get("manifest_sha256") != sha256_file(
        manifest_path
    ):
        raise ValueError("raw seal authority drift")
    files = file_map_sha256(raw_dir, excluded={"raw-seal.json"})
    if set(files) != RAW_REQUIRED or seal.get("files") != files:
        raise ValueError("sealed raw evidence changed")
    if seal.get("files_sha256") != canonical_sha256(files):
        raise ValueError("raw seal digest drift")
    return seal


def _read_identity(path: pathlib.Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        key, separator, value = line.partition("=")
        if not separator or not key or key in result:
            raise ValueError("malformed tool identity")
        result[key] = value
    return result


def _parse_stat(path: pathlib.Path, top: str) -> tuple[float, int]:
    document = json.loads(path.read_text())
    modules = document.get("modules")
    if not isinstance(modules, dict):
        raise ValueError("Yosys stat modules are missing")
    module = modules.get(top) or modules.get(f"\\{top}")
    if not isinstance(module, dict):
        raise ValueError("Yosys stat top is missing")
    area = module.get("area")
    cells = module.get("num_cells")
    if not isinstance(area, (int, float)) or area <= 0:
        raise ValueError("mapped area is invalid")
    if not isinstance(cells, int) or cells <= 0:
        raise ValueError("mapped cell count is invalid")
    return float(area), cells


def derive_one(
    manifest_path: pathlib.Path,
    variant: str,
    rtl_dir: pathlib.Path,
    raw_dir: pathlib.Path,
    derived_dir: pathlib.Path,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    verify_authority(manifest)
    if variant not in manifest["matrix"]:
        raise ValueError("variant is outside the frozen matrix")
    contract = _variant_contract(manifest, variant)
    rtl_sha256 = _verify_variant_inputs(
        manifest, variant, contract["top"], ",".join(contract["blackboxes"]), rtl_dir
    )
    seal = _load_verified_seal(manifest_path, variant, raw_dir)
    yosys_path = raw_dir / "yosys.log"
    opensta_path = raw_dir / "opensta.log"
    mapped_path = raw_dir / "mapped.v"
    metadata_path = raw_dir / "run-metadata.json"
    stat_path = raw_dir / "stat.json"
    for path in (yosys_path, opensta_path, mapped_path, metadata_path, stat_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"missing raw evidence: {path.name}")
    yosys = yosys_path.read_text(errors="strict")
    opensta = opensta_path.read_text(errors="strict")
    for forbidden in ("ERROR:", "Error:", "unresolved", "not found"):
        if forbidden in yosys or forbidden in opensta:
            raise ValueError(f"forbidden report diagnostic: {forbidden}")
    areas = AREA_RE.findall(yosys)
    slacks = SLACK_RE.findall(opensta)
    if len(areas) != 1 or len(slacks) != 1:
        raise ValueError("area or timing result is incomplete/ambiguous")
    top, area_text = areas[0]
    if top != contract["top"]:
        raise ValueError("reported synthesis top drift")
    slack_text, timing_status = slacks[0]
    slack = float(slack_text)
    if (timing_status == "MET") != (slack >= 0.0):
        raise ValueError("timing status contradicts setup slack")
    startpoints = STARTPOINT_RE.findall(opensta)
    endpoints = ENDPOINT_RE.findall(opensta)
    path_groups = PATH_GROUP_RE.findall(opensta)
    if len(startpoints) != 1 or len(endpoints) != 1 or path_groups != ["clock"]:
        raise ValueError("timing path or clock group is incomplete")
    stat_area, mapped_cells = _parse_stat(stat_path, top)
    if abs(stat_area - float(area_text)) > 0.000001:
        raise ValueError("Yosys area reports disagree")
    if not re.search(rf"(?m)^module\s+\\?{re.escape(top)}(?:\s|\()", mapped_path.read_text()):
        raise ValueError("mapped netlist top is missing")
    identity = _read_identity(raw_dir / "tool-identity.txt")
    for manifest_name, identity_name in (
        ("yosys_sha256", "yosys_sha256"),
        ("opensta_sha256", "opensta_sha256"),
        ("liberty_sha256", "liberty_sha256"),
    ):
        if identity.get(identity_name) != manifest["toolchain"][manifest_name]:
            raise ValueError(f"runtime tool identity drift: {identity_name}")
    if identity.get("clock_port") != "clock" or identity.get("clock_period_ns") != "20.000":
        raise ValueError("runtime clock identity drift")
    if identity.get("input_delay_ns") != "1.000" or identity.get("output_delay_ns") != "1.000":
        raise ValueError("runtime I/O delay drift")
    collector_policy = manifest.get("collector_policy")
    if collector_policy is not None and identity.get("blackbox_selection_mode") != collector_policy[
        "blackbox_selection_mode"
    ]:
        raise ValueError("runtime blackbox selection mode drift")
    expected_rtl_files = sorted(
        f"/rtl/{item.relative_to(rtl_dir).as_posix()}"
        for item in rtl_dir.rglob("*")
        if item.is_file() and item.suffix in {".sv", ".v"}
    )
    if (raw_dir / "rtl-files.txt").read_text().splitlines() != expected_rtl_files:
        raise ValueError("captured RTL file list drift")
    expected_blackboxes = contract["blackboxes"]
    if (raw_dir / "blackboxes.txt").read_text().splitlines() != expected_blackboxes:
        raise ValueError("captured blackbox list drift")
    metadata = json.loads(metadata_path.read_text())
    if metadata.get("manifest_sha256") != sha256_file(manifest_path):
        raise ValueError("run metadata manifest drift")
    if metadata.get("variant") != variant or metadata.get("top") != top:
        raise ValueError("run metadata variant drift")
    result = {
        "schema": "raveil.t0044-physical-result/v1",
        "experiment_id": "EXP-0009",
        "evidence_class": "synthesis-estimate",
        "variant": variant,
        "top": top,
        "partition_role": contract["partition_role"],
        "blackboxes": contract["blackboxes"],
        "mapped_area_um2": float(area_text),
        "mapped_cells": mapped_cells,
        "setup_slack_ns": slack,
        "timing_met": timing_status == "MET",
        "critical_path": {"startpoint": startpoints[0], "endpoint": endpoints[0]},
        "clock_period_ns": manifest["clock_period_ns"],
        "rtl_sha256": rtl_sha256,
        "manifest_sha256": sha256_file(manifest_path),
        "raw_seal_sha256": sha256_file(raw_dir / "raw-seal.json"),
        "raw_files_sha256": seal["files_sha256"],
        "mapped_netlist_sha256": sha256_file(mapped_path),
        "raw_sha256": {
            "yosys": sha256_file(yosys_path),
            "opensta": sha256_file(opensta_path),
        },
        "performance_claim": False,
        "energy_claim": False,
        "whole_system_claim": False,
        "eligibility": "partition-complete",
        "missing_components": contract["missing_components"],
    }
    if derived_dir.exists():
        raise ValueError("derived result directory already exists")
    derived_dir.mkdir(parents=True)
    output = derived_dir / "result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def derive_matrix(
    manifest_path: pathlib.Path,
    graph_result_path: pathlib.Path,
    rocket_result_path: pathlib.Path,
    derived_dir: pathlib.Path,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    verify_authority(manifest)
    graph = json.loads(graph_result_path.read_text())
    rocket = json.loads(rocket_result_path.read_text())
    expected = ((graph, "static-graph"), (rocket, "rocket-in-order"))
    for result, variant in expected:
        if result.get("schema") != "raveil.t0044-physical-result/v1":
            raise ValueError("partition result schema drift")
        if result.get("variant") != variant or result.get("eligibility") != "partition-complete":
            raise ValueError("partition result is incomplete")
        if result.get("manifest_sha256") != sha256_file(manifest_path):
            raise ValueError("partition result manifest drift")
        contract = _variant_contract(manifest, variant)
        if result.get("partition_role") != contract["partition_role"]:
            raise ValueError("partition role drift")
        if result.get("rtl_sha256") != contract["rtl_sha256"]:
            raise ValueError("partition RTL drift")
        if result.get("whole_system_claim") is not False:
            raise ValueError("partition result overclaims whole-system evidence")
    graph_area = float(graph["mapped_area_um2"])
    rocket_area = float(rocket["mapped_area_um2"])
    if graph_area <= 0.0 or rocket_area <= 0.0:
        raise ValueError("partition area is invalid")
    ratio = graph_area / rocket_area
    if ratio > manifest["decision_rules"]["incremental_area_ratio_no_go_above"]:
        outcome = "early-no-go-area"
    elif not bool(graph["timing_met"]) and bool(rocket["timing_met"]):
        outcome = "early-no-go-timing"
    elif bool(graph["timing_met"]) and bool(rocket["timing_met"]):
        outcome = manifest["decision_rules"]["pass_label"]
    else:
        outcome = manifest["decision_rules"]["incomplete_label"]
    result = {
        "schema": "raveil.t0044-physical-matrix/v1",
        "experiment_id": "EXP-0009",
        "evidence_class": "synthesis-estimate",
        "manifest_sha256": sha256_file(manifest_path),
        "outcome": outcome,
        "graph_incremental_area_um2": graph_area,
        "rocket_fallback_area_um2": rocket_area,
        "analytical_logic_composition_area_um2": graph_area + rocket_area,
        "incremental_area_ratio": ratio,
        "clock_period_ns": manifest["clock_period_ns"],
        "graph_timing_met": bool(graph["timing_met"]),
        "rocket_timing_met": bool(rocket["timing_met"]),
        "common_memory_included": False,
        "whole_system_claim": False,
        "energy_claim": False,
        "missing_components": sorted(
            set(graph.get("missing_components", []))
            | set(rocket.get("missing_components", []))
            | {"common-memory-area", "fallback-integration", "placement-routing"}
        ),
        "result_sha256": {
            "static-graph": sha256_file(graph_result_path),
            "rocket-in-order": sha256_file(rocket_result_path),
        },
    }
    if derived_dir.exists():
        raise ValueError("matrix result directory already exists")
    derived_dir.mkdir(parents=True)
    (derived_dir / "matrix.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    hash_parser = subparsers.add_parser("hash-tree")
    hash_parser.add_argument("--path", type=pathlib.Path, required=True)
    verify_parser = subparsers.add_parser("verify-manifest")
    verify_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    field_parser = subparsers.add_parser("manifest-field")
    field_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    field_parser.add_argument("--field", required=True)
    variant_parser = subparsers.add_parser("variant-field")
    variant_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    variant_parser.add_argument("--variant", required=True)
    variant_parser.add_argument("--field", choices=("top", "blackboxes"), required=True)
    derive_parser = subparsers.add_parser("derive-one")
    derive_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    derive_parser.add_argument("--variant", required=True)
    derive_parser.add_argument("--rtl-dir", type=pathlib.Path, required=True)
    derive_parser.add_argument("--raw-dir", type=pathlib.Path, required=True)
    derive_parser.add_argument("--derived-dir", type=pathlib.Path, required=True)
    metadata_parser = subparsers.add_parser("write-run-metadata")
    metadata_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    metadata_parser.add_argument("--variant", required=True)
    metadata_parser.add_argument("--top", required=True)
    metadata_parser.add_argument("--blackboxes", required=True)
    metadata_parser.add_argument("--rtl-dir", type=pathlib.Path, required=True)
    metadata_parser.add_argument("--raw-dir", type=pathlib.Path, required=True)
    seal_parser = subparsers.add_parser("seal-raw")
    seal_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    seal_parser.add_argument("--variant", required=True)
    seal_parser.add_argument("--raw-dir", type=pathlib.Path, required=True)
    failure_parser = subparsers.add_parser("record-failure")
    failure_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    failure_parser.add_argument("--variant", required=True)
    failure_parser.add_argument("--rtl-dir", type=pathlib.Path, required=True)
    failure_parser.add_argument("--raw-dir", type=pathlib.Path, required=True)
    failure_parser.add_argument("--container-exit-code", type=int, required=True)
    matrix_parser = subparsers.add_parser("derive-matrix")
    matrix_parser.add_argument("--manifest", type=pathlib.Path, required=True)
    matrix_parser.add_argument("--graph-result", type=pathlib.Path, required=True)
    matrix_parser.add_argument("--rocket-result", type=pathlib.Path, required=True)
    matrix_parser.add_argument("--derived-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if args.command == "hash-tree":
        print(tree_sha256(args.path))
    elif args.command == "verify-manifest":
        manifest = load_manifest(args.manifest)
        verify_authority(manifest)
        print("EXP-0009 manifest verified")
    elif args.command == "manifest-field":
        print(_field(load_manifest(args.manifest), args.field))
    elif args.command == "variant-field":
        print(variant_field(load_manifest(args.manifest), args.variant, args.field))
    elif args.command == "derive-one":
        print(
            json.dumps(
                derive_one(
                    args.manifest, args.variant, args.rtl_dir, args.raw_dir, args.derived_dir
                ),
                sort_keys=True,
            )
        )
    elif args.command == "write-run-metadata":
        print(
            json.dumps(
                write_run_metadata(
                    args.manifest,
                    args.variant,
                    args.top,
                    args.blackboxes,
                    args.rtl_dir,
                    args.raw_dir,
                ),
                sort_keys=True,
            )
        )
    elif args.command == "seal-raw":
        print(json.dumps(seal_raw(args.manifest, args.variant, args.raw_dir), sort_keys=True))
    elif args.command == "record-failure":
        print(
            json.dumps(
                record_failure(
                    args.manifest,
                    args.variant,
                    args.rtl_dir,
                    args.raw_dir,
                    args.container_exit_code,
                ),
                sort_keys=True,
            )
        )
    elif args.command == "derive-matrix":
        print(
            json.dumps(
                derive_matrix(
                    args.manifest,
                    args.graph_result,
                    args.rocket_result,
                    args.derived_dir,
                ),
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
