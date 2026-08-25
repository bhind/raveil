#!/bin/sh
# One-command, pre-data closure for the shared concrete memory source.
# The command produces structural and functional prerequisites only. It does
# not synthesize, map memories, place, route, or collect candidate results.
set -eu
umask 077

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

sha256_file() {
    shasum -a 256 "$1" | awk '{print $1}'
}

[ "$#" -eq 3 ] ||
    fail 'usage: run-exp0011-common-memory-closure.sh INTEGRATED_EXPORT BASELINE_EXPORT APPEND_ONLY_OUTPUT_DIR'
integrated_export=$1
baseline_export=$2
output_dir=$3
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"

mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
mkdir "$output_dir/derived"

"$repo_root/hardware/chisel/run-exp0011-common-memory-hierarchy-preflight.sh" \
    "$integrated_export" "$baseline_export" "$output_dir/hierarchy"
"$repo_root/hardware/chisel/run-exp0011-stdcell-memory-preflight.sh" \
    "$output_dir/source-preflight"
"$repo_root/hardware/chisel/run-exp0011-stdcell-memory-sim.sh" \
    "$output_dir/simulation"

preflight_metadata=$output_dir/source-preflight/derived/preflight-metadata.json
simulation_metadata=$output_dir/simulation/derived/simulation-metadata.json
runtime_receipt=$output_dir/simulation/raw/runtime-image-receipt.txt
raw_manifest=$output_dir/simulation/raw/sha256s.txt
hierarchy_comparison=$output_dir/hierarchy/derived/comparison-report.json
for evidence in "$preflight_metadata" "$simulation_metadata" "$runtime_receipt" "$raw_manifest" "$hierarchy_comparison"; do
    [ -s "$evidence" ] || fail "missing closure evidence: $evidence"
done

source_sha256=$(sha256_file "$repo_root/hardware/chisel/exp0011_common_stdcell_memories.sv")
preflight_runner_sha256=$(sha256_file "$repo_root/hardware/chisel/run-exp0011-stdcell-memory-preflight.sh")
simulation_runner_sha256=$(sha256_file "$repo_root/hardware/chisel/run-exp0011-stdcell-memory-sim.sh")
testbench_sha256=$(sha256_file "$repo_root/hardware/chisel/exp0011_common_stdcell_memory_tb.sv")
verifier_sha256=$(sha256_file "$repo_root/hardware/chisel/verify-boom-functional-sim-image.sh")
preflight_metadata_sha256=$(sha256_file "$preflight_metadata")
simulation_metadata_sha256=$(sha256_file "$simulation_metadata")

PYTHONPATH="$repo_root" python3 - \
    "$preflight_metadata" "$simulation_metadata" \
    "$output_dir/derived/option-b-contract.json" \
    "$repo_root" \
    "$source_sha256" "$preflight_runner_sha256" "$simulation_runner_sha256" \
    "$testbench_sha256" "$verifier_sha256" \
    "$preflight_metadata_sha256" "$simulation_metadata_sha256" <<'PY'
import json
import pathlib
import subprocess
import sys

from raveil.t0044_stdcell_memory import (
    CELL_LEF_SHA256,
    EVIDENCE_CLASS,
    EXPECTED_MACROS,
    FUNCTIONAL_CONFIG_VIEW_SHA256,
    FUNCTIONAL_PAYLOAD_MANIFEST,
    FUNCTIONAL_ROOTFS_SHA256,
    FUNCTIONAL_VERIFIER_SHA256,
    FUTURE_MAPPING_PASSES,
    LIBERTY_SHA256,
    NONCLAIMS,
    OPENRCX_SHA256,
    PHYSICAL_IMAGE_ID,
    PHYSICAL_ROOTFS_SHA256,
    POSTCONDITIONS,
    READINESS_RECEIPT_SHA256,
    SCHEMA,
    SEMANTICS,
    TECH_LEF_SHA256,
    TOTAL_STORAGE_BITS,
    YOSYS_SHA256,
)

preflight = json.loads(pathlib.Path(sys.argv[1]).read_text())
simulation = json.loads(pathlib.Path(sys.argv[2]).read_text())
output = pathlib.Path(sys.argv[3])
repo_root = pathlib.Path(sys.argv[4])
(
    source_sha256,
    preflight_runner_sha256,
    simulation_runner_sha256,
    testbench_sha256,
    verifier_sha256,
    preflight_metadata_sha256,
    simulation_metadata_sha256,
) = sys.argv[5:]
authority = subprocess.run(
    ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()
if preflight["authority_commit"] != authority or simulation["authority_commit"] != authority:
    raise SystemExit("evidence authority commits do not match current HEAD")
if verifier_sha256 != FUNCTIONAL_VERIFIER_SHA256:
    raise SystemExit("functional verifier identity drift")

record = {
    "schema": SCHEMA,
    "task_id": "T-0044",
    "authority_commit": authority,
    "freeze_state": "unfrozen",
    "experiment_id": None,
    "manifest_frozen": False,
    "claim_bearing_candidate_data_collected": False,
    "candidate_synthesis": False,
    "pnr": False,
    "evidence_class": EVIDENCE_CLASS,
    "nonclaims": NONCLAIMS,
    "candidates": {"integrated": source_sha256, "matched_rocket": source_sha256},
    "macros": list(EXPECTED_MACROS.values()),
    "total_storage_bits": TOTAL_STORAGE_BITS,
    "semantics": SEMANTICS,
    "identities": {
        "source_sha256": source_sha256,
        "preflight_runner_sha256": preflight_runner_sha256,
        "simulation_runner_sha256": simulation_runner_sha256,
        "testbench_sha256": testbench_sha256,
        "verifier_sha256": verifier_sha256,
        "readiness_receipt_sha256": READINESS_RECEIPT_SHA256,
        "preflight_receipt": {
            "sha256": preflight_metadata_sha256,
            "source_sha256": source_sha256,
            "runner_sha256": preflight_runner_sha256,
        },
        "simulation_receipt": {
            "sha256": simulation_metadata_sha256,
            "source_sha256": source_sha256,
            "runner_sha256": simulation_runner_sha256,
            "testbench_sha256": testbench_sha256,
        },
        "toolchain": {
            "physical_image": "raveil-physical-proxy-toolchain:v1",
            "physical_image_id": PHYSICAL_IMAGE_ID,
            "physical_rootfs_sha256": PHYSICAL_ROOTFS_SHA256,
            "functional_runtime_oci_index": simulation["runtime_oci_index"],
            "functional_payload_manifest": FUNCTIONAL_PAYLOAD_MANIFEST,
            "functional_config_view_sha256": FUNCTIONAL_CONFIG_VIEW_SHA256,
            "functional_rootfs_sha256": FUNCTIONAL_ROOTFS_SHA256,
            "functional_verifier_sha256": FUNCTIONAL_VERIFIER_SHA256,
            "functional_runtime_receipt_sha256": simulation["receipt_sha256"],
            "functional_runtime_descriptor_digest": simulation["descriptor_digest"],
            "functional_runtime_descriptor_media_type": simulation["descriptor_media_type"],
            "functional_runtime_descriptor_size": simulation["descriptor_size"],
            "functional_payload_media_type": simulation["payload_media_type"],
            "functional_runtime_build_ref": simulation["build_ref"],
            "platform": "linux/amd64",
            "yosys_sha256": YOSYS_SHA256,
            "yosys_version": "0.27+3",
            "verilator_sha256": simulation["verilator_sha256"],
            "verilator_version": "5.020",
            "standard_cell_liberty_sha256": LIBERTY_SHA256,
            "standard_cell_lef_sha256": CELL_LEF_SHA256,
            "technology_lef_sha256": TECH_LEF_SHA256,
            "openrcx_rule_sha256": OPENRCX_SHA256,
        },
    },
    "future_mapping_passes": FUTURE_MAPPING_PASSES,
    "postconditions": POSTCONDITIONS,
}
output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
PY

PYTHONPATH="$repo_root" python3 -m raveil.t0044_stdcell_memory \
    "$output_dir/derived/option-b-contract.json" \
    > "$output_dir/derived/contract-validation.json"
PYTHONPATH="$repo_root" python3 -m raveil.t0044_stdcell_memory \
    "$output_dir/derived/option-b-contract.json" \
    --bundle-metadata "$simulation_metadata" \
    --bundle-receipt "$runtime_receipt" \
    --bundle-raw-manifest "$raw_manifest" \
    --repo-root "$repo_root" \
    > "$output_dir/derived/bundle-validation.json"

contract_sha256=$(sha256_file "$output_dir/derived/option-b-contract.json")
bundle_sha256=$(sha256_file "$output_dir/derived/bundle-validation.json")
hierarchy_sha256=$(sha256_file "$hierarchy_comparison")
printf 'EXP0011-COMMON-MEMORY-CLOSURE-V1 status=OK contract_sha256=%s bundle_sha256=%s hierarchy_sha256=%s candidate_data=false evidence=rtl-structural-preflight,rtl-simulation-functional performance=not-measured\n' \
    "$contract_sha256" "$bundle_sha256" "$hierarchy_sha256"
