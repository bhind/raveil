#!/bin/sh
# Deterministic all-module functional simulation in the verified tagless runtime image.
set -eu
umask 077

fail() { printf 'error: %s\n' "$*" >&2; exit 1; }
sha256_file() { shasum -a 256 "$1" | awk '{print $1}'; }

[ "$#" -eq 1 ] || fail 'usage: run-exp0011-stdcell-memory-sim.sh APPEND_ONLY_OUTPUT_DIR'
output_dir=$1
[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
source_rel=hardware/chisel/exp0011_common_stdcell_memories.sv
testbench_rel=hardware/chisel/exp0011_common_stdcell_memory_tb.sv
runner_rel=hardware/chisel/run-exp0011-stdcell-memory-sim.sh
verifier_rel=hardware/chisel/verify-boom-functional-sim-image.sh
for relative in "$source_rel" "$testbench_rel" "$verifier_rel"; do
    [ -s "$repo_root/$relative" ] || fail "missing simulation input: $relative"
done
command -v docker >/dev/null 2>&1 || fail 'docker is required'

platform=linux/amd64
expected_payload_manifest=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822
expected_config_view_sha256=32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522
expected_rootfs_sha256=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c
toolchain_volume=raveil-chipyard-conda-lock-v1
expected_lock_sha256=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d

[ -x "$repo_root/$verifier_rel" ] || fail 'functional image verifier is not executable'
image=$("$repo_root/$verifier_rel") || fail 'verified functional simulator receipt is required'
image_id=$(docker image inspect --format '{{.Id}}' "$image")
config_view_sha256=$(docker image inspect --format '{{json .Config}}' "$image" | shasum -a 256 | awk '{print $1}')
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" | shasum -a 256 | awk '{print $1}')
[ "$config_view_sha256" = "$expected_config_view_sha256" ] || fail "functional Config view drift: $config_view_sha256"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] || fail "functional image RootFS drift: $rootfs_sha256"

mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
mkdir "$output_dir/raw" "$output_dir/derived" "$output_dir/build"
raw_dir=$output_dir/raw
derived_dir=$output_dir/derived

docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$output_dir,target=/out" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    "$image" sh -c 'set -eu
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
test -x /locked/env/bin/verilator
command -v make >/dev/null 2>&1
test "$(cat /locked/raveil-lock-sha256)" = 5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
verilator_version=$(verilator --version)
case "$verilator_version" in "Verilator 5.020 "*) ;; *) echo "error: Verilator version drift: $verilator_version" >&2; exit 1;; esac
printf "%s\n" "$verilator_version" > /out/raw/verilator-version.txt
sha256sum "$(command -v verilator)" | cut -d" " -f1 > /out/raw/verilator-sha256.txt
cd /repo
verilator --binary --timing --build-jobs 1 -Wall -Wno-fatal \
  --top-module exp0011_common_stdcell_memory_tb \
  --Mdir /out/build -o memory-sim \
  hardware/chisel/exp0011_common_stdcell_memories.sv \
  hardware/chisel/exp0011_common_stdcell_memory_tb.sv \
  > /out/raw/compile-transcript.txt 2>&1
/out/build/memory-sim > /out/raw/simulation-transcript.txt 2>&1
grep -qx "EXP0011_COMMON_STDCELL_MEMORY_FUNCTIONAL_OK checks=28 modules=7" /out/raw/simulation-transcript.txt
'

find "$raw_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$raw_dir/sha256s.txt"
raw_manifest_sha256=$(sha256_file "$raw_dir/sha256s.txt")
source_sha256=$(sha256_file "$repo_root/$source_rel")
testbench_sha256=$(sha256_file "$repo_root/$testbench_rel")
runner_sha256=$(sha256_file "$repo_root/$runner_rel")
verifier_sha256=$(sha256_file "$repo_root/$verifier_rel")
verilator_sha256=$(tr -d '\n' < "$raw_dir/verilator-sha256.txt")
verilator_version=$(tr -d '\n' < "$raw_dir/verilator-version.txt")

python3 - "$derived_dir/simulation-metadata.json" <<PY
import json
import pathlib
record = {
    "schema": "raveil.exp-0011-common-stdcell-memory-functional/v2",
    "task_id": "T-0044", "authority_commit": "$(git -C "$repo_root" rev-parse HEAD)",
    "runtime_oci_index": "$image_id", "payload_manifest": "$expected_payload_manifest",
    "config_view_sha256": "$config_view_sha256",
    "rootfs_layers_sha256": "$rootfs_sha256", "platform": "$platform",
    "toolchain_volume": "$toolchain_volume", "lock_sha256": "$expected_lock_sha256",
    "verilator_version": "$verilator_version", "verilator_sha256": "$verilator_sha256",
    "source_sha256": "$source_sha256", "testbench_sha256": "$testbench_sha256",
    "runner_sha256": "$runner_sha256", "raw_manifest_sha256": "$raw_manifest_sha256",
    "verifier_sha256": "$verifier_sha256",
    "modules": ["cc_dir_ext", "cc_banks_0_ext", "data_arrays_0_ext", "tag_array_ext", "tag_array_0_ext", "data_arrays_0_0_ext", "memory_ext"],
    "checks": ["full writes", "masked writes where applicable", "one-cycle synchronous reads", "disabled output hold", "write-cycle output hold", "separate read/write clocks without same-address collision"],
    "evidence_class": "rtl-simulation-functional",
    "functional_evidence_collected": True,
    "claim_bearing_candidate_data_collected": False,
    "experiment_id": None, "manifest_frozen": False, "candidate_synthesis": False, "pnr": False,
    "nonclaims": ["no candidate comparison datum", "no synthesis, placement, routing, area, timing, energy, FPGA, ASIC, or silicon claim"],
}
pathlib.Path("$derived_dir/simulation-metadata.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
PY

find "$derived_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$derived_dir/sha256s.txt"
metadata_sha256=$(sha256_file "$derived_dir/simulation-metadata.json")
printf 'EXP0011-COMMON-STDCELL-MEMORY-FUNCTIONAL-V2 status=OK modules=7 checks=28 candidate_data=false metadata_sha256=%s evidence=rtl-simulation-functional\n' "$metadata_sha256"
