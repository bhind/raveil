"""Fail-closed validator for the unallocated T-0044 Option-B memory contract.

This module validates a proposed pre-data contract.  It does not export a
candidate, map the 4,631,296 storage bits to flops, run P&R, allocate EXP-0011,
freeze a manifest, or promote a physical/performance claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

from .t0044_integrated_rtl import (
    MEMORY_MACRO_CONTRACT,
    MEMORY_MACRO_COUNTS,
    MEMORY_MACRO_PORTS,
)

SCHEMA = "raveil.t0044-common-stdcell-memory/v2"
TOTAL_STORAGE_BITS = 4_631_296
EVIDENCE_CLASS = "physical-input-readiness-no-candidate-data"
NONCLAIMS = [
    "no EXP-0011 allocation or frozen manifest",
    "no candidate synthesis, placement, routing, parasitic, area, timing, energy, FPGA, ASIC, or silicon data",
    "no equivalence, performance, product-readiness, T-0044 completion, or go/no-go claim",
]
FUTURE_MAPPING_PASSES = ["memory_map", "dfflibmap", "abc"]
POSTCONDITIONS = [
    "no $mem* cells before P&R",
    "no reachable blackbox cells before P&R",
    "no placeholder memory views before P&R",
    "no candidate-specific source branch before P&R",
]

PHYSICAL_IMAGE_ID = "sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169"
PHYSICAL_ROOTFS_SHA256 = "21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5"
FUNCTIONAL_PAYLOAD_MANIFEST = "sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822"
FUNCTIONAL_CONFIG_VIEW_SHA256 = "32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522"
FUNCTIONAL_ROOTFS_SHA256 = "154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c"
FUNCTIONAL_VERIFIER_SHA256 = "8a27bee892581b0fadfec07312d0433f4ef3605d11b71656b3b0aeaae99b930b"
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
    "simulation_receipt", "toolchain",
})
PREFLIGHT_RECEIPT_FIELDS = frozenset({"sha256", "source_sha256", "runner_sha256"})
SIMULATION_RECEIPT_FIELDS = frozenset({"sha256", "source_sha256", "runner_sha256", "testbench_sha256"})
TOOLCHAIN_FIELDS = frozenset({
    "physical_image", "physical_image_id", "physical_rootfs_sha256",
    "functional_runtime_oci_index", "functional_payload_manifest",
    "functional_config_view_sha256", "functional_rootfs_sha256",
    "functional_verifier_sha256",
    "platform", "yosys_sha256", "yosys_version", "verilator_sha256",
    "verilator_version", "standard_cell_liberty_sha256",
    "standard_cell_lef_sha256", "technology_lef_sha256", "openrcx_rule_sha256",
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


def _exact(value: Any, fields: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields missing or unknown")
    return value


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
    for label, receipt in (("preflight", preflight), ("simulation", simulation)):
        for field, value in receipt.items():
            _sha256(value, f"{label} receipt {field}")
    if preflight["source_sha256"] != identities["source_sha256"] or preflight["runner_sha256"] != identities["preflight_runner_sha256"]:
        raise ValueError("preflight receipt/source/runner binding drift")
    if simulation["source_sha256"] != identities["source_sha256"] or simulation["runner_sha256"] != identities["simulation_runner_sha256"] or simulation["testbench_sha256"] != identities["testbench_sha256"]:
        raise ValueError("simulation receipt/source/runner/testbench binding drift")

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
        "platform": "linux/amd64", "yosys_sha256": YOSYS_SHA256,
        "yosys_version": "0.27+3", "verilator_sha256": tool["verilator_sha256"],
        "verilator_version": "5.020", "standard_cell_liberty_sha256": LIBERTY_SHA256,
        "standard_cell_lef_sha256": CELL_LEF_SHA256, "technology_lef_sha256": TECH_LEF_SHA256,
        "openrcx_rule_sha256": OPENRCX_SHA256,
    }
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="JSON contract to validate")
    args = parser.parse_args(argv)
    with args.contract.open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    print(json.dumps(validate_option_b_contract(document), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
