"""Fail-closed validator for the unallocated T-0044 Option-B memory contract.

This module validates a proposed pre-data contract.  It does not export a
candidate, map the 4,631,296 storage bits to flops, run P&R, allocate EXP-0011,
freeze a manifest, or promote a physical/performance claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from .t0044_integrated_rtl import (
    MEMORY_MACRO_CONTRACT,
    MEMORY_MACRO_COUNTS,
    MEMORY_MACRO_PORTS,
)

SCHEMA = "raveil.t0044-common-stdcell-memory/v4"
RUNTIME_RECEIPT_SCHEMA = "raveil.boom-functional-sim-image/v2"
METADATA_SCHEMA = "raveil.exp-0011-common-stdcell-memory-functional/v3"
TOTAL_STORAGE_BITS = 4_631_296
EVIDENCE_CLASS = "physical-input-readiness-no-candidate-data"
NONCLAIMS = [
    "no EXP-0011 allocation or frozen manifest",
    "no candidate synthesis, placement, routing, parasitic, area, timing, energy, FPGA, ASIC, or silicon data",
    "no equivalence, performance, product-readiness, T-0044 completion, or go/no-go claim",
]
FUTURE_MAPPING_PASSES = ["memory_map", "dfflibmap", "abc"]
POSTCONDITIONS = [
    "after future mapping passes, the mapped netlist has no $mem* cells before P&R",
    "after future mapping passes, the mapped netlist has no reachable blackbox cells before P&R",
    "after future mapping passes, the mapped netlist has no placeholder memory views before P&R",
    "the future mapped netlist has no candidate-specific source branch before P&R",
]

PHYSICAL_IMAGE_ID = "sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169"
PHYSICAL_ROOTFS_SHA256 = "21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5"
FUNCTIONAL_PAYLOAD_MANIFEST = "sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822"
FUNCTIONAL_CONFIG_VIEW_SHA256 = "32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522"
FUNCTIONAL_ROOTFS_SHA256 = "154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c"
FUNCTIONAL_VERIFIER_SHA256 = "8a27bee892581b0fadfec07312d0433f4ef3605d11b71656b3b0aeaae99b930b"
FUNCTIONAL_LOCK_SHA256 = "5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d"
FUNCTIONAL_TOOLCHAIN_VOLUME = "raveil-chipyard-conda-lock-v1"
READINESS_RECEIPT_SHA256 = "0c64aa343b6801c0846744364f2d5dece7af00e26648d53b437de51ea74f3945"
YOSYS_SHA256 = "a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508"
LIBERTY_SHA256 = "e66aab4e0a3eef8d0b13eb5b75aaadb725ba78b032203342eb1e419a2c111baf"
CELL_LEF_SHA256 = "cf8bcac8e831cff18c22a80999af3a97c8247028cd7dbbcdd8e3b73f725069ec"
TECH_LEF_SHA256 = "1a18b353fb5457caf0eca5b3cb28b2c0c9bbacdbbdeee7c4fc64a115932066c2"
OPENRCX_SHA256 = "682de2d5ceba1fffbdd58ee3033b2ab89ac81ced4ad3f51406f77a05ec4bca8b"

_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_PLACEHOLDERS = frozenset({"0" * 64, "f" * 64, "deadbeef" * 8})

TOP_FIELDS = frozenset({
    "schema", "task_id", "authority_commit", "freeze_state", "experiment_id",
    "manifest_frozen", "claim_bearing_candidate_data_collected",
    "candidate_synthesis", "pnr",
    "evidence_class", "nonclaims", "candidates", "macros",
    "total_storage_bits", "semantics", "identities", "future_mapping_passes",
    "postconditions",
})
IDENTITY_FIELDS = frozenset({
    "source_sha256", "preflight_runner_sha256", "simulation_runner_sha256",
    "testbench_sha256", "verifier_sha256", "readiness_receipt_sha256", "preflight_receipt",
    "simulation_receipt", "hierarchy_receipt", "toolchain",
})
PREFLIGHT_RECEIPT_FIELDS = frozenset({
    "sha256", "source_sha256", "runner_sha256", "raw_manifest_sha256",
    "derived_manifest_sha256",
})
SIMULATION_RECEIPT_FIELDS = frozenset({
    "sha256", "source_sha256", "runner_sha256", "testbench_sha256",
    "raw_manifest_sha256", "derived_manifest_sha256",
})
HIERARCHY_RECEIPT_FIELDS = frozenset({
    "metadata_sha256", "comparison_sha256", "raw_manifest_sha256",
    "derived_manifest_sha256", "source_sha256", "runner_sha256",
    "analyzer_sha256",
})
TOOLCHAIN_FIELDS = frozenset({
    "physical_image", "physical_image_id", "physical_rootfs_sha256",
    "functional_runtime_oci_index", "functional_payload_manifest",
    "functional_config_view_sha256", "functional_rootfs_sha256",
    "functional_verifier_sha256", "functional_runtime_receipt_sha256",
    "functional_runtime_descriptor_digest",
    "functional_runtime_descriptor_media_type",
    "functional_runtime_descriptor_size", "functional_payload_media_type",
    "functional_runtime_build_ref",
    "platform", "yosys_sha256", "yosys_version", "verilator_sha256",
    "verilator_version", "standard_cell_liberty_sha256",
    "standard_cell_lef_sha256", "technology_lef_sha256", "openrcx_rule_sha256",
})
RUNTIME_RECEIPT_FIELDS = frozenset({
    "SCHEMA", "RUNTIME_IMAGE_ID", "RUNTIME_DESCRIPTOR_DIGEST",
    "RUNTIME_DESCRIPTOR_MEDIA_TYPE", "RUNTIME_DESCRIPTOR_SIZE",
    "PAYLOAD_MANIFEST", "PAYLOAD_MEDIA_TYPE", "CONFIG_VIEW_SHA256",
    "ROOTFS_LAYERS_SHA256", "PLATFORM", "BUILD_REF",
})
METADATA_FIELDS = frozenset({
    "schema", "task_id", "authority_commit", "runtime_oci_index",
    "descriptor_digest", "descriptor_media_type", "descriptor_size",
    "payload_manifest", "payload_media_type", "config_view_sha256",
    "rootfs_layers_sha256", "platform", "build_ref", "receipt_sha256",
    "receipt_path", "receipt_copy_sha256", "toolchain_volume", "lock_sha256",
    "verilator_version", "verilator_sha256", "source_sha256",
    "testbench_sha256", "runner_sha256", "raw_manifest_sha256",
    "verifier_sha256", "modules", "checks", "evidence_class",
    "functional_evidence_collected", "claim_bearing_candidate_data_collected",
    "experiment_id", "manifest_frozen", "candidate_synthesis", "pnr",
    "nonclaims",
})
HIERARCHY_METADATA_FIELDS = frozenset({
    "schema", "task_id", "authority_commit", "image", "image_id",
    "image_rootfs_sha256", "platform", "source_sha256", "runner_sha256",
    "analyzer_sha256", "integrated_export_metadata_sha256",
    "baseline_export_metadata_sha256", "raw_manifest_sha256",
    "memory_macro_types", "memory_macro_instances", "reachable_blackboxes",
    "evidence_class", "candidate_synthesis", "memory_mapping", "pnr",
    "nonclaims",
})
PREFLIGHT_METADATA_FIELDS = frozenset({
    "schema", "task_id", "authority_commit", "image", "image_id",
    "image_rootfs_sha256", "platform", "source_sha256", "runner_sha256",
    "readiness_receipt_sha256", "inventory_runner_sha256", "yosys_sha256",
    "yosys_version", "yosys_revision", "raw_manifest_sha256", "tops",
    "fresh_yosys_processes", "total_storage_bits", "commands",
    "evidence_class", "experiment_id", "manifest_frozen",
    "preflight_evidence_collected", "claim_bearing_candidate_data_collected",
    "candidate_synthesis", "pnr", "nonclaims",
})
HIERARCHY_COMPARISON_FIELDS = frozenset({
    "schema", "status", "source_sha256", "memory_macro_instances",
    "memory_macro_types", "rocket_module_canonical_sha256",
    "common_clock_roots", "reachable_blackboxes", "nonclaims",
})
MACRO_FIELDS = frozenset({"name", "depth", "width", "count", "ports", "mask_granularity"})
SEMANTICS = {
    "contents": "uninitialized",
    "reset": "none",
    "one_rw_read": "one-cycle synchronous read on enabled rising edge",
    "one_rw_output_hold": ["disabled", "write"],
    "one_rw_write": "masked or full write on enabled rising edge",
    "write_cycle_output": "not contractually observed beyond hold behavior",
    "memory_ext_read": "one-cycle synchronous read on R0_clk enabled rising edge",
    "memory_ext_write": "byte-masked write on W0_clk enabled rising edge",
    "memory_ext_collision": "same-address cross-clock read/write collision undefined and excluded from tests",
}
FUNCTIONAL_MODULES = [
    "cc_dir_ext", "cc_banks_0_ext", "data_arrays_0_ext", "tag_array_ext",
    "tag_array_0_ext", "data_arrays_0_0_ext", "memory_ext",
]
FUNCTIONAL_CHECKS = [
    "full writes", "masked writes where applicable",
    "one-cycle synchronous reads", "disabled output hold",
    "write-cycle output hold",
    "separate read/write clocks without same-address collision",
]
FUNCTIONAL_NONCLAIMS = [
    "no candidate comparison datum",
    "no synthesis, placement, routing, area, timing, energy, FPGA, ASIC, or silicon claim",
]


def _exact(value: Any, fields: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields missing or unknown")
    return value


def _load_json_bytes(value: bytes, label: str) -> Any:
    def exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"{label} contains a duplicate JSON key: {key}")
            result[key] = item
        return result

    try:
        return json.loads(value, object_pairs_hook=exact_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from error


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value) or value in _PLACEHOLDERS:
        raise ValueError(f"{label} must be a non-placeholder lowercase SHA-256")
    return value


def _image_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _IMAGE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase sha256 image identity")
    _sha256(value.removeprefix("sha256:"), label)
    return value


def _macro_contract() -> dict[str, dict[str, Any]]:
    macros: dict[str, dict[str, Any]] = {}
    for name, declaration in MEMORY_MACRO_CONTRACT.items():
        tokens = declaration.split()
        fields = dict(zip(tokens[::2], tokens[1::2]))
        macros[name] = {
            "name": name,
            "depth": int(fields["depth"]),
            "width": int(fields["width"]),
            "count": MEMORY_MACRO_COUNTS[name],
            "ports": fields["ports"],
            "mask_granularity": int(fields["mask_gran"]) if "mask_gran" in fields else None,
        }
    return macros


EXPECTED_MACROS = _macro_contract()


def validate_option_b_contract(document: dict[str, Any]) -> dict[str, Any]:
    """Validate and summarize one exact unallocated Option-B contract."""
    contract = _exact(document, TOP_FIELDS, "contract")
    if contract["schema"] != SCHEMA or contract["task_id"] != "T-0044":
        raise ValueError("schema or task drift")
    if not isinstance(contract["authority_commit"], str) or not _HEX40.fullmatch(contract["authority_commit"]):
        raise ValueError("authority_commit must be a lowercase 40-hex Git object ID")
    if contract["freeze_state"] != "unfrozen" or contract["experiment_id"] is not None:
        raise ValueError("EXP-0011 must remain absent and the contract unfrozen")
    for field in (
        "manifest_frozen", "claim_bearing_candidate_data_collected",
        "candidate_synthesis", "pnr",
    ):
        if contract[field] is not False:
            raise ValueError(f"{field} must be false")
    if contract["evidence_class"] != EVIDENCE_CLASS or contract["nonclaims"] != NONCLAIMS:
        raise ValueError("evidence class or exact nonclaims drift")

    candidates = _exact(contract["candidates"], frozenset({"integrated", "matched_rocket"}), "candidates")
    integrated = _sha256(candidates["integrated"], "integrated candidate identity")
    matched = _sha256(candidates["matched_rocket"], "matched-Rocket candidate identity")
    if integrated != matched:
        raise ValueError("candidate memory identities must be byte-identical")

    macros = contract["macros"]
    if not isinstance(macros, list) or len(macros) != len(EXPECTED_MACROS):
        raise ValueError("macro list must contain exactly seven entries")
    actual_macros: dict[str, dict[str, Any]] = {}
    for entry in macros:
        macro = _exact(entry, MACRO_FIELDS, "macro")
        name = macro["name"]
        if not isinstance(name, str) or name in actual_macros:
            raise ValueError("macro names must be unique strings")
        actual_macros[name] = macro
    if actual_macros != EXPECTED_MACROS:
        raise ValueError("macro name/depth/width/count/ports/mask contract drift")
    computed_bits = sum(m["depth"] * m["width"] * m["count"] for m in actual_macros.values())
    if computed_bits != TOTAL_STORAGE_BITS or contract["total_storage_bits"] != computed_bits:
        raise ValueError("total storage bit denominator drift")
    if contract["semantics"] != SEMANTICS:
        raise ValueError("read/write/hold/collision semantics drift")

    identities = _exact(contract["identities"], IDENTITY_FIELDS, "identities")
    for field in ("source_sha256", "preflight_runner_sha256", "simulation_runner_sha256", "testbench_sha256", "verifier_sha256"):
        _sha256(identities[field], field)
    if identities["verifier_sha256"] != FUNCTIONAL_VERIFIER_SHA256:
        raise ValueError("functional verifier source drift")
    if identities["readiness_receipt_sha256"] != READINESS_RECEIPT_SHA256:
        raise ValueError("merged readiness receipt identity drift")
    preflight = _exact(identities["preflight_receipt"], PREFLIGHT_RECEIPT_FIELDS, "preflight_receipt")
    simulation = _exact(identities["simulation_receipt"], SIMULATION_RECEIPT_FIELDS, "simulation_receipt")
    hierarchy = _exact(
        identities["hierarchy_receipt"],
        HIERARCHY_RECEIPT_FIELDS,
        "hierarchy_receipt",
    )
    for label, receipt in (
        ("preflight", preflight),
        ("simulation", simulation),
        ("hierarchy", hierarchy),
    ):
        for field, value in receipt.items():
            _sha256(value, f"{label} receipt {field}")
    if preflight["source_sha256"] != identities["source_sha256"] or preflight["runner_sha256"] != identities["preflight_runner_sha256"]:
        raise ValueError("preflight receipt/source/runner binding drift")
    if simulation["source_sha256"] != identities["source_sha256"] or simulation["runner_sha256"] != identities["simulation_runner_sha256"] or simulation["testbench_sha256"] != identities["testbench_sha256"]:
        raise ValueError("simulation receipt/source/runner/testbench binding drift")
    if hierarchy["source_sha256"] != identities["source_sha256"]:
        raise ValueError("hierarchy receipt/source binding drift")

    tool = _exact(identities["toolchain"], TOOLCHAIN_FIELDS, "toolchain")
    runtime_oci_index = _image_id(
        tool["functional_runtime_oci_index"], "functional runtime OCI index"
    )
    expected_tool = {
        "physical_image": "raveil-physical-proxy-toolchain:v1",
        "physical_image_id": PHYSICAL_IMAGE_ID,
        "physical_rootfs_sha256": PHYSICAL_ROOTFS_SHA256,
        "functional_runtime_oci_index": runtime_oci_index,
        "functional_payload_manifest": FUNCTIONAL_PAYLOAD_MANIFEST,
        "functional_config_view_sha256": FUNCTIONAL_CONFIG_VIEW_SHA256,
        "functional_rootfs_sha256": FUNCTIONAL_ROOTFS_SHA256,
        "functional_verifier_sha256": FUNCTIONAL_VERIFIER_SHA256,
        "functional_runtime_receipt_sha256": tool["functional_runtime_receipt_sha256"],
        "functional_runtime_descriptor_digest": runtime_oci_index,
        "functional_runtime_descriptor_media_type":
            "application/vnd.oci.image.index.v1+json",
        "functional_runtime_descriptor_size": tool["functional_runtime_descriptor_size"],
        "functional_payload_media_type":
            "application/vnd.oci.image.manifest.v1+json",
        "functional_runtime_build_ref": tool["functional_runtime_build_ref"],
        "platform": "linux/amd64", "yosys_sha256": YOSYS_SHA256,
        "yosys_version": "0.27+3", "verilator_sha256": tool["verilator_sha256"],
        "verilator_version": "5.020", "standard_cell_liberty_sha256": LIBERTY_SHA256,
        "standard_cell_lef_sha256": CELL_LEF_SHA256, "technology_lef_sha256": TECH_LEF_SHA256,
        "openrcx_rule_sha256": OPENRCX_SHA256,
    }
    _sha256(tool["functional_runtime_receipt_sha256"], "functional runtime receipt")
    if (
        not isinstance(tool["functional_runtime_descriptor_size"], int)
        or isinstance(tool["functional_runtime_descriptor_size"], bool)
        or tool["functional_runtime_descriptor_size"] <= 0
    ):
        raise ValueError("functional runtime descriptor size drift")
    if (
        not isinstance(tool["functional_runtime_build_ref"], str)
        or re.fullmatch(r"[0-9a-z]+", tool["functional_runtime_build_ref"]) is None
    ):
        raise ValueError("functional runtime build reference drift")
    _sha256(tool["verilator_sha256"], "verilator_sha256")
    if tool != expected_tool:
        raise ValueError("tool, image, Liberty, LEF, technology, or RC identity drift")
    if contract["future_mapping_passes"] != FUTURE_MAPPING_PASSES:
        raise ValueError("future mapping pass drift")
    if contract["postconditions"] != POSTCONDITIONS:
        raise ValueError("future postcondition drift")

    # Keep the executable interface authority live: a validator update cannot
    # silently lose a canonical macro port while retaining the textual contract.
    if set(MEMORY_MACRO_PORTS) != set(actual_macros):
        raise ValueError("canonical macro interface set drift")
    return {
        "schema": SCHEMA,
        "status": "valid-unfrozen-pre-data",
        "macro_types": len(actual_macros),
        "macro_instances": sum(m["count"] for m in actual_macros.values()),
        "total_storage_bits": computed_bits,
        "evidence_class": EVIDENCE_CLASS,
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def verify_evidence_manifest(manifest_bytes: bytes, directory: Path) -> dict[str, Any]:
    """Rehash one flat evidence directory from its canonical size/hash manifest."""
    if not manifest_bytes or not manifest_bytes.endswith(b"\n"):
        raise ValueError("evidence manifest must be nonempty and newline terminated")
    try:
        lines = manifest_bytes.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("evidence manifest must be ASCII") from error
    entries: dict[str, tuple[str, int]] = {}
    for line in lines:
        match = re.fullmatch(
            r"([0-9a-f]{64})  (0|[1-9][0-9]*)  ([A-Za-z0-9][A-Za-z0-9._-]*)",
            line,
        )
        if match is None:
            raise ValueError("malformed evidence manifest entry")
        digest, size_text, name = match.groups()
        if name == "sha256s.txt" or name in entries:
            raise ValueError("duplicate or self-referential evidence manifest entry")
        entries[name] = (digest, int(size_text))
    if list(entries) != sorted(entries):
        raise ValueError("evidence manifest paths are not canonically sorted")
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("evidence manifest directory is missing or symlinked")
    actual_names = {
        path.name for path in directory.iterdir() if path.name != "sha256s.txt"
    }
    if actual_names != set(entries):
        raise ValueError("evidence manifest file set mismatch")
    for name, (digest, size) in entries.items():
        path = directory / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"evidence payload is missing or symlinked: {name}")
        payload = path.read_bytes()
        if len(payload) != size or _sha256_bytes(payload) != digest:
            raise ValueError(f"evidence payload size or hash mismatch: {name}")
    return {
        "manifest_sha256": _sha256_bytes(manifest_bytes),
        "entries": len(entries),
    }


def validate_mapped_netlist_postconditions(document: dict[str, Any]) -> dict[str, Any]:
    """Check future post-mapping netlist conditions without running mapping or P&R."""
    design_modules = document.get("modules")
    if not isinstance(design_modules, dict) or not design_modules:
        raise ValueError("mapped netlist lacks modules")
    for module_name, module in design_modules.items():
        if not isinstance(module, dict):
            raise ValueError(f"mapped netlist module is malformed: {module_name}")
        if module.get("attributes", {}).get("blackbox") not in (None, 0, "0", False):
            raise ValueError(f"mapped netlist contains a blackbox: {module_name}")
        cells = module.get("cells", {})
        if not isinstance(cells, dict):
            raise ValueError(f"mapped netlist cells are malformed: {module_name}")
        for cell in cells.values():
            cell_type = cell.get("type") if isinstance(cell, dict) else None
            if not isinstance(cell_type, str):
                raise ValueError(f"mapped netlist cell type is malformed: {module_name}")
            if cell_type.startswith("$mem"):
                raise ValueError(f"mapped netlist retains an abstract memory cell: {cell_type}")
    return {"status": "mapped-netlist-postconditions-satisfied", "pnr": False}


def parse_runtime_receipt(receipt_bytes: bytes) -> dict[str, str]:
    """Parse the exact ADR-0062 receipt syntax and reject any field drift."""
    try:
        text = receipt_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("runtime receipt is not UTF-8") from error
    lines = text.splitlines()
    if len(lines) != len(RUNTIME_RECEIPT_FIELDS) or any(
        not line or line.count("=") != 1 for line in lines
    ):
        raise ValueError("runtime receipt line structure drift")
    receipt: dict[str, str] = {}
    for line in lines:
        key, value = line.split("=", 1)
        if key in receipt or key not in RUNTIME_RECEIPT_FIELDS or not value:
            raise ValueError("runtime receipt fields missing, duplicated, or unknown")
        receipt[key] = value
    if set(receipt) != RUNTIME_RECEIPT_FIELDS:
        raise ValueError("runtime receipt fields missing, duplicated, or unknown")
    if receipt["SCHEMA"] != RUNTIME_RECEIPT_SCHEMA:
        raise ValueError("runtime receipt schema drift")
    runtime = _image_id(receipt["RUNTIME_IMAGE_ID"], "runtime image ID")
    if receipt["RUNTIME_DESCRIPTOR_DIGEST"] != runtime:
        raise ValueError("runtime descriptor does not bind the runtime image")
    if receipt["RUNTIME_DESCRIPTOR_MEDIA_TYPE"] != "application/vnd.oci.image.index.v1+json":
        raise ValueError("runtime descriptor media type drift")
    try:
        descriptor_size = int(receipt["RUNTIME_DESCRIPTOR_SIZE"])
    except ValueError as error:
        raise ValueError("runtime descriptor size drift") from error
    if descriptor_size <= 0 or str(descriptor_size) != receipt["RUNTIME_DESCRIPTOR_SIZE"]:
        raise ValueError("runtime descriptor size drift")
    if receipt["PAYLOAD_MANIFEST"] != FUNCTIONAL_PAYLOAD_MANIFEST:
        raise ValueError("runtime payload manifest drift")
    if receipt["PAYLOAD_MEDIA_TYPE"] != "application/vnd.oci.image.manifest.v1+json":
        raise ValueError("runtime payload media type drift")
    if receipt["CONFIG_VIEW_SHA256"] != FUNCTIONAL_CONFIG_VIEW_SHA256:
        raise ValueError("runtime Config view drift")
    if receipt["ROOTFS_LAYERS_SHA256"] != FUNCTIONAL_ROOTFS_SHA256:
        raise ValueError("runtime RootFS list drift")
    if receipt["PLATFORM"] != "linux/amd64":
        raise ValueError("runtime platform drift")
    if re.fullmatch(r"[0-9a-z]+", receipt["BUILD_REF"]) is None:
        raise ValueError("runtime build reference drift")
    return receipt


def validate_evidence_bundle(
    contract: dict[str, Any],
    metadata_bytes: bytes,
    receipt_bytes: bytes,
    raw_manifest_bytes: bytes,
    *,
    repo_root: Path,
    evidence_root: Path,
) -> dict[str, Any]:
    """Bind the v4 contract to all three closure legs and their payload bytes."""
    validate_option_b_contract(contract)
    if not evidence_root.is_dir() or evidence_root.is_symlink():
        raise ValueError("closure evidence root is missing or symlinked")
    leg_paths = {
        "hierarchy": evidence_root / "hierarchy",
        "preflight": evidence_root / "source-preflight",
        "simulation": evidence_root / "simulation",
    }
    seals: dict[str, dict[str, Any]] = {}
    for label, leg in leg_paths.items():
        raw_bytes = (leg / "raw/sha256s.txt").read_bytes()
        derived_bytes = (leg / "derived/sha256s.txt").read_bytes()
        seals[label] = {
            "raw": verify_evidence_manifest(raw_bytes, leg / "raw"),
            "derived": verify_evidence_manifest(derived_bytes, leg / "derived"),
        }
    canonical_simulation_manifest = (
        leg_paths["simulation"] / "raw/sha256s.txt"
    ).read_bytes()
    if raw_manifest_bytes != canonical_simulation_manifest:
        raise ValueError("supplied and closure simulation raw manifests differ")
    metadata = _load_json_bytes(metadata_bytes, "functional metadata")
    metadata = _exact(metadata, METADATA_FIELDS, "functional metadata")
    receipt = parse_runtime_receipt(receipt_bytes)
    if metadata_bytes != (
        leg_paths["simulation"] / "derived/simulation-metadata.json"
    ).read_bytes():
        raise ValueError("supplied and closure functional metadata differ")
    if receipt_bytes != (
        leg_paths["simulation"] / "raw/runtime-image-receipt.txt"
    ).read_bytes():
        raise ValueError("supplied and closure runtime receipts differ")
    if metadata["schema"] != METADATA_SCHEMA or metadata["task_id"] != "T-0044":
        raise ValueError("functional metadata schema or task drift")
    if not isinstance(metadata["authority_commit"], str) or _HEX40.fullmatch(metadata["authority_commit"]) is None:
        raise ValueError("functional metadata authority format drift")
    try:
        current_head = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("cannot resolve current implementation authority") from error
    if metadata["authority_commit"] != current_head or contract["authority_commit"] != current_head:
        raise ValueError("contract or metadata authority is not current HEAD")

    for key in (
        "config_view_sha256", "rootfs_layers_sha256", "receipt_sha256",
        "receipt_copy_sha256", "lock_sha256", "verilator_sha256",
        "source_sha256", "testbench_sha256", "runner_sha256",
        "raw_manifest_sha256", "verifier_sha256",
    ):
        _sha256(metadata[key], key)
    for key in ("runtime_oci_index", "descriptor_digest", "payload_manifest"):
        _image_id(metadata[key], key)
    if (
        not isinstance(metadata["descriptor_size"], int)
        or isinstance(metadata["descriptor_size"], bool)
        or metadata["descriptor_size"] <= 0
    ):
        raise ValueError("functional metadata descriptor size drift")

    projection = {
        "runtime_oci_index": receipt["RUNTIME_IMAGE_ID"],
        "descriptor_digest": receipt["RUNTIME_DESCRIPTOR_DIGEST"],
        "descriptor_media_type": receipt["RUNTIME_DESCRIPTOR_MEDIA_TYPE"],
        "descriptor_size": int(receipt["RUNTIME_DESCRIPTOR_SIZE"]),
        "payload_manifest": receipt["PAYLOAD_MANIFEST"],
        "payload_media_type": receipt["PAYLOAD_MEDIA_TYPE"],
        "config_view_sha256": receipt["CONFIG_VIEW_SHA256"],
        "rootfs_layers_sha256": receipt["ROOTFS_LAYERS_SHA256"],
        "platform": receipt["PLATFORM"],
        "build_ref": receipt["BUILD_REF"],
    }
    if any(metadata[key] != value for key, value in projection.items()):
        raise ValueError("functional metadata and runtime receipt projection mismatch")
    receipt_sha256 = _sha256_bytes(receipt_bytes)
    if metadata["receipt_sha256"] != receipt_sha256 or metadata["receipt_copy_sha256"] != receipt_sha256:
        raise ValueError("runtime receipt byte hash mismatch")
    expected_receipt_path = (
        f"artifacts/boom-functional-sim-images/"
        f"{receipt['RUNTIME_IMAGE_ID'].removeprefix('sha256:')}/receipt"
    )
    if metadata["receipt_path"] != expected_receipt_path:
        raise ValueError("runtime receipt path is not digest-named")
    canonical_receipt = repo_root / expected_receipt_path
    if not canonical_receipt.is_file() or canonical_receipt.read_bytes() != receipt_bytes:
        raise ValueError("canonical and evidence-copy runtime receipts differ")

    identities = contract["identities"]
    tool = identities["toolchain"]
    hierarchy_metadata_bytes = (
        leg_paths["hierarchy"] / "derived/preflight-metadata.json"
    ).read_bytes()
    hierarchy_comparison_bytes = (
        leg_paths["hierarchy"] / "derived/comparison-report.json"
    ).read_bytes()
    preflight_metadata_bytes = (
        leg_paths["preflight"] / "derived/preflight-metadata.json"
    ).read_bytes()
    hierarchy_metadata = _exact(
        _load_json_bytes(hierarchy_metadata_bytes, "hierarchy metadata"),
        HIERARCHY_METADATA_FIELDS,
        "hierarchy metadata",
    )
    hierarchy_comparison = _exact(
        _load_json_bytes(hierarchy_comparison_bytes, "hierarchy comparison"),
        HIERARCHY_COMPARISON_FIELDS,
        "hierarchy comparison",
    )
    preflight_metadata = _exact(
        _load_json_bytes(preflight_metadata_bytes, "source preflight metadata"),
        PREFLIGHT_METADATA_FIELDS,
        "source preflight metadata",
    )
    for label, value, encoded in (
        ("hierarchy metadata", hierarchy_metadata, hierarchy_metadata_bytes),
        ("hierarchy comparison", hierarchy_comparison, hierarchy_comparison_bytes),
        ("source preflight metadata", preflight_metadata, preflight_metadata_bytes),
    ):
        if _canonical_json_bytes(value) != encoded:
            raise ValueError(f"{label} canonical encoding drift")
    hierarchy_receipt = identities["hierarchy_receipt"]
    hierarchy_bindings = {
        "metadata_sha256": _sha256_bytes(hierarchy_metadata_bytes),
        "comparison_sha256": _sha256_bytes(hierarchy_comparison_bytes),
        "raw_manifest_sha256": seals["hierarchy"]["raw"]["manifest_sha256"],
        "derived_manifest_sha256": seals["hierarchy"]["derived"]["manifest_sha256"],
        "source_sha256": hierarchy_metadata["source_sha256"],
        "runner_sha256": hierarchy_metadata["runner_sha256"],
        "analyzer_sha256": hierarchy_metadata["analyzer_sha256"],
    }
    if hierarchy_receipt != hierarchy_bindings:
        raise ValueError("contract does not bind the exact hierarchy evidence")
    if (
        hierarchy_metadata["schema"]
        != "raveil.exp-0011-common-memory-hierarchy-preflight/v1"
        or hierarchy_metadata["task_id"] != "T-0044"
        or hierarchy_metadata["authority_commit"] != current_head
        or hierarchy_metadata["source_sha256"] != identities["source_sha256"]
        or hierarchy_metadata["image_id"] != PHYSICAL_IMAGE_ID
        or hierarchy_metadata["image_rootfs_sha256"] != PHYSICAL_ROOTFS_SHA256
        or hierarchy_metadata["platform"] != "linux/amd64"
        or hierarchy_metadata["runner_sha256"] != hierarchy_receipt["runner_sha256"]
        or hierarchy_metadata["analyzer_sha256"] != hierarchy_receipt["analyzer_sha256"]
        or hierarchy_metadata["raw_manifest_sha256"]
        != seals["hierarchy"]["raw"]["manifest_sha256"]
        or hierarchy_metadata["memory_macro_types"] != 7
        or hierarchy_metadata["memory_macro_instances"] != 11
        or hierarchy_metadata["reachable_blackboxes"] != 0
        or hierarchy_metadata["evidence_class"] != "rtl-structural-preflight"
        or hierarchy_metadata["candidate_synthesis"] is not False
        or hierarchy_metadata["memory_mapping"] is not False
        or hierarchy_metadata["pnr"] is not False
    ):
        raise ValueError("hierarchy metadata identity or claim boundary drift")
    for key in ("integrated_export_metadata_sha256", "baseline_export_metadata_sha256"):
        _sha256(hierarchy_metadata[key], f"hierarchy {key}")
    if (
        hierarchy_comparison["schema"]
        != "raveil.exp-0011-common-memory-concrete/v1"
        or hierarchy_comparison["status"] != "structural-only"
        or hierarchy_comparison["source_sha256"] != identities["source_sha256"]
        or hierarchy_comparison["memory_macro_types"] != 7
        or hierarchy_comparison["memory_macro_instances"] != 11
        or hierarchy_comparison["reachable_blackboxes"] != 0
        or hierarchy_comparison["common_clock_roots"]
        != ["clock_uncore", "jtag_TCK", "serial_tl_0_clock_in"]
    ):
        raise ValueError("hierarchy comparison identity or fairness boundary drift")
    _sha256(
        hierarchy_comparison["rocket_module_canonical_sha256"],
        "hierarchy Rocket canonical identity",
    )
    preflight_receipt = identities["preflight_receipt"]
    if preflight_receipt != {
        "sha256": _sha256_bytes(preflight_metadata_bytes),
        "source_sha256": preflight_metadata["source_sha256"],
        "runner_sha256": preflight_metadata["runner_sha256"],
        "raw_manifest_sha256": seals["preflight"]["raw"]["manifest_sha256"],
        "derived_manifest_sha256": seals["preflight"]["derived"]["manifest_sha256"],
    }:
        raise ValueError("contract does not bind the exact source preflight evidence")
    if (
        preflight_metadata["schema"]
        != "raveil.exp-0011-common-stdcell-memory-preflight/v2"
        or preflight_metadata["task_id"] != "T-0044"
        or preflight_metadata["authority_commit"] != current_head
        or preflight_metadata["source_sha256"] != identities["source_sha256"]
        or preflight_metadata["image_id"] != PHYSICAL_IMAGE_ID
        or preflight_metadata["image_rootfs_sha256"] != PHYSICAL_ROOTFS_SHA256
        or preflight_metadata["platform"] != "linux/amd64"
        or preflight_metadata["runner_sha256"] != identities["preflight_runner_sha256"]
        or preflight_metadata["readiness_receipt_sha256"] != READINESS_RECEIPT_SHA256
        or preflight_metadata["yosys_sha256"] != YOSYS_SHA256
        or preflight_metadata["tops"] != FUNCTIONAL_MODULES
        or preflight_metadata["raw_manifest_sha256"]
        != seals["preflight"]["raw"]["manifest_sha256"]
        or preflight_metadata["total_storage_bits"] != TOTAL_STORAGE_BITS
        or preflight_metadata["claim_bearing_candidate_data_collected"] is not False
        or preflight_metadata["candidate_synthesis"] is not False
        or preflight_metadata["pnr"] is not False
    ):
        raise ValueError("source preflight identity or claim boundary drift")
    contract_bindings = {
        "source_sha256": identities["source_sha256"],
        "testbench_sha256": identities["testbench_sha256"],
        "runner_sha256": identities["simulation_runner_sha256"],
        "verifier_sha256": identities["verifier_sha256"],
    }
    if any(metadata[key] != value for key, value in contract_bindings.items()):
        raise ValueError("contract and functional source identity mismatch")
    tool_bindings = {
        "runtime_oci_index": tool["functional_runtime_oci_index"],
        "descriptor_digest": tool["functional_runtime_descriptor_digest"],
        "descriptor_media_type": tool["functional_runtime_descriptor_media_type"],
        "descriptor_size": tool["functional_runtime_descriptor_size"],
        "payload_manifest": tool["functional_payload_manifest"],
        "payload_media_type": tool["functional_payload_media_type"],
        "config_view_sha256": tool["functional_config_view_sha256"],
        "rootfs_layers_sha256": tool["functional_rootfs_sha256"],
        "platform": tool["platform"],
        "build_ref": tool["functional_runtime_build_ref"],
        "receipt_sha256": tool["functional_runtime_receipt_sha256"],
    }
    if any(metadata[key] != value for key, value in tool_bindings.items()):
        raise ValueError("contract and functional runtime identity mismatch")
    if identities["simulation_receipt"]["sha256"] != _sha256_bytes(metadata_bytes):
        raise ValueError("contract does not bind the exact functional metadata bytes")
    if metadata["raw_manifest_sha256"] != _sha256_bytes(raw_manifest_bytes):
        raise ValueError("functional metadata does not bind the raw manifest bytes")
    if identities["simulation_receipt"] != {
        "sha256": _sha256_bytes(metadata_bytes),
        "source_sha256": metadata["source_sha256"],
        "runner_sha256": metadata["runner_sha256"],
        "testbench_sha256": metadata["testbench_sha256"],
        "raw_manifest_sha256": seals["simulation"]["raw"]["manifest_sha256"],
        "derived_manifest_sha256": seals["simulation"]["derived"]["manifest_sha256"],
    }:
        raise ValueError("contract does not bind the exact functional evidence tree")

    file_bindings = {
        "source_sha256": "hardware/chisel/exp0011_common_stdcell_memories.sv",
        "testbench_sha256": "hardware/chisel/exp0011_common_stdcell_memory_tb.sv",
        "runner_sha256": "hardware/chisel/run-exp0011-stdcell-memory-sim.sh",
        "verifier_sha256": "hardware/chisel/verify-boom-functional-sim-image.sh",
    }
    for key, relative in file_bindings.items():
        path = repo_root / relative
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != metadata[key]:
            raise ValueError(f"current file identity mismatch: {relative}")
    additional_bindings = (
        (identities["preflight_runner_sha256"],
         "hardware/chisel/run-exp0011-stdcell-memory-preflight.sh"),
        (identities["hierarchy_receipt"]["runner_sha256"],
         "hardware/chisel/run-exp0011-common-memory-hierarchy-preflight.sh"),
        (identities["hierarchy_receipt"]["analyzer_sha256"],
         "raveil/t0044_integrated_rtl.py"),
    )
    for expected, relative in additional_bindings:
        path = repo_root / relative
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != expected:
            raise ValueError(f"current file identity mismatch: {relative}")
    if (
        metadata["toolchain_volume"] != FUNCTIONAL_TOOLCHAIN_VOLUME
        or metadata["lock_sha256"] != FUNCTIONAL_LOCK_SHA256
        or not isinstance(metadata["verilator_version"], str)
        or not metadata["verilator_version"].startswith("Verilator 5.020 ")
        or metadata["modules"] != FUNCTIONAL_MODULES
        or metadata["checks"] != FUNCTIONAL_CHECKS
        or metadata["nonclaims"] != FUNCTIONAL_NONCLAIMS
        or json.dumps(metadata, indent=2, sort_keys=True).encode() + b"\n" != metadata_bytes
    ):
        raise ValueError("functional evidence content or canonical encoding drift")
    if (
        metadata["evidence_class"] != "rtl-simulation-functional"
        or metadata["functional_evidence_collected"] is not True
        or metadata["claim_bearing_candidate_data_collected"] is not False
        or metadata["experiment_id"] is not None
        or metadata["manifest_frozen"] is not False
        or metadata["candidate_synthesis"] is not False
        or metadata["pnr"] is not False
    ):
        raise ValueError("functional evidence claim boundary drift")
    return {
        "schema": "raveil.t0044-evidence-bundle/v2",
        "status": "valid-unfrozen-pre-data",
        "authority_commit": current_head,
        "runtime_oci_index": receipt["RUNTIME_IMAGE_ID"],
        "receipt_sha256": receipt_sha256,
        "metadata_sha256": _sha256_bytes(metadata_bytes),
        "hierarchy_comparison_sha256": _sha256_bytes(hierarchy_comparison_bytes),
        "evidence_seals": seals,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="JSON contract to validate")
    parser.add_argument("--bundle-metadata", type=Path)
    parser.add_argument("--bundle-receipt", type=Path)
    parser.add_argument("--bundle-raw-manifest", type=Path)
    parser.add_argument("--bundle-root", type=Path)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args(argv)
    document = _load_json_bytes(args.contract.read_bytes(), "contract")
    if args.bundle_metadata or args.bundle_receipt or args.bundle_raw_manifest or args.bundle_root or args.repo_root:
        if not args.bundle_metadata or not args.bundle_receipt or not args.bundle_raw_manifest or not args.bundle_root or not args.repo_root:
            raise ValueError("bundle validation requires metadata, receipt, raw manifest, evidence root, and repo root")
        result = validate_evidence_bundle(
            document,
            args.bundle_metadata.read_bytes(),
            args.bundle_receipt.read_bytes(),
            args.bundle_raw_manifest.read_bytes(),
            repo_root=args.repo_root,
            evidence_root=args.bundle_root,
        )
    else:
        result = validate_option_b_contract(document)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
