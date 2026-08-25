#!/bin/sh
# Resolve both exported ChipTop hierarchies through one concrete memory source.
# This is an offline structural preflight. It deliberately stops before memory
# mapping, synthesis, placement, routing, timing, area, or performance work.
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
    fail 'usage: run-exp0011-common-memory-hierarchy-preflight.sh INTEGRATED_EXPORT BASELINE_EXPORT APPEND_ONLY_OUTPUT_DIR'
integrated_export=$1
baseline_export=$2
output_dir=$3
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
source_rel=hardware/chisel/exp0011_common_stdcell_memories.sv
runner_rel=hardware/chisel/run-exp0011-common-memory-hierarchy-preflight.sh
analyzer_rel=raveil/t0044_integrated_rtl.py
image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64
expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169
expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5

[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"
[ -s "$repo_root/$source_rel" ] || fail 'missing common memory source'
for export_dir in "$integrated_export" "$baseline_export"; do
    [ -s "$export_dir/ChipTop.top.f" ] || fail "missing ChipTop file list: $export_dir"
    [ -s "$export_dir/export-metadata.json" ] || fail "missing export metadata: $export_dir"
done
command -v docker >/dev/null 2>&1 || fail 'docker is required'

integrated_export=$(CDPATH= cd -- "$integrated_export" && pwd)
baseline_export=$(CDPATH= cd -- "$baseline_export" && pwd)
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl validate-export \
    --export-dir "$integrated_export" --variant integrated-static-graph-rocket >/dev/null
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl validate-export \
    --export-dir "$baseline_export" --variant matched-rocket-system >/dev/null

image_id=$(docker image inspect --format '{{.Id}}' "$image")
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
    shasum -a 256 | awk '{print $1}')
[ "$image_id" = "$expected_image_id" ] || fail "physical toolchain image ID drift: $image_id"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] ||
    fail "physical toolchain RootFS drift: $rootfs_sha256"

mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
mkdir "$output_dir/raw" "$output_dir/derived"
raw_dir=$output_dir/raw
derived_dir=$output_dir/derived
cp "$repo_root/$source_rel" "$raw_dir/common-memory-source.sv"
source_sha256=$(sha256_file "$repo_root/$source_rel")

docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$integrated_export,target=/integrated,readonly" \
    --mount "type=bind,source=$baseline_export,target=/baseline,readonly" \
    --mount "type=bind,source=$raw_dir,target=/out" \
    "$image" sh -c 'set -eu
yosys -V > /out/yosys-version.txt
for variant in integrated baseline; do
    cd "/$variant"
    script="/out/$variant-read.ys"
    printf "read_verilog -sv /repo/hardware/chisel/exp0011_common_stdcell_memories.sv\n" > "$script"
    while IFS= read -r source; do
        case "$source" in
            generated-src/*)
                base=${source#generated-src/}
                case "$base" in
                    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-]*|*/*|"")
                        echo "error: unsafe RTL entry: $source" >&2
                        exit 1
                        ;;
                    *.sv|*.v) ;;
                    *) echo "error: unsupported RTL suffix: $source" >&2; exit 1 ;;
                esac
                ;;
            *) echo "error: non-local RTL entry: $source" >&2; exit 1 ;;
        esac
        test -f "$source"
        printf "read_verilog -sv /%s/%s\n" "$variant" "$source" >> "$script"
    done < ChipTop.top.f
    cat >> "$script" <<YOSYS
hierarchy -check -top ChipTop
proc
memory_collect
check -assert
write_json /out/$variant-hierarchy.json
flatten
opt_clean
check -assert
write_json /out/$variant-flat.json
YOSYS
    yosys -q -l "/out/$variant-yosys.log" -s "$script"
done
'

for variant in integrated baseline; do
    config=matched-rocket-system
    [ "$variant" = integrated ] && config=integrated-static-graph-rocket
    PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl analyze-concrete \
        --hierarchy "$raw_dir/$variant-hierarchy.json" \
        --flat "$raw_dir/$variant-flat.json" \
        --variant "$config" \
        --source-sha256 "$source_sha256" \
        > "$derived_dir/$variant-report.json"
done
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl compare-concrete \
    --integrated-report "$derived_dir/integrated-report.json" \
    --baseline-report "$derived_dir/baseline-report.json" \
    > "$derived_dir/comparison-report.json"

find "$raw_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$raw_dir/sha256s.txt"
raw_manifest_sha256=$(sha256_file "$raw_dir/sha256s.txt")
runner_sha256=$(sha256_file "$repo_root/$runner_rel")
analyzer_sha256=$(sha256_file "$repo_root/$analyzer_rel")
integrated_export_sha256=$(sha256_file "$integrated_export/export-metadata.json")
baseline_export_sha256=$(sha256_file "$baseline_export/export-metadata.json")

python3 - "$derived_dir/preflight-metadata.json" <<EOF
import json
import pathlib
import sys

record = {
    "schema": "raveil.exp-0011-common-memory-hierarchy-preflight/v1",
    "task_id": "T-0044",
    "authority_commit": "$(git -C "$repo_root" rev-parse HEAD)",
    "image": "$image",
    "image_id": "$image_id",
    "image_rootfs_sha256": "$rootfs_sha256",
    "platform": "$platform",
    "source_sha256": "$source_sha256",
    "runner_sha256": "$runner_sha256",
    "analyzer_sha256": "$analyzer_sha256",
    "integrated_export_metadata_sha256": "$integrated_export_sha256",
    "baseline_export_metadata_sha256": "$baseline_export_sha256",
    "raw_manifest_sha256": "$raw_manifest_sha256",
    "memory_macro_types": 7,
    "memory_macro_instances": 11,
    "reachable_blackboxes": 0,
    "evidence_class": "rtl-structural-preflight",
    "candidate_synthesis": False,
    "memory_mapping": False,
    "pnr": False,
    "nonclaims": [
        "no synthesis or memory mapping",
        "no placement or routing",
        "no timing, area, energy, performance, FPGA, ASIC, or silicon result",
    ],
}
pathlib.Path(sys.argv[1]).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
EOF

find "$derived_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(sha256_file "$file")" "$(basename "$file")"
    done > "$derived_dir/sha256s.txt"
comparison_sha256=$(sha256_file "$derived_dir/comparison-report.json")
printf 'EXP0011-COMMON-MEMORY-HIERARCHY-PREFLIGHT-V1 status=OK macro_types=7 macro_instances=11 blackboxes=0 source_sha256=%s comparison_sha256=%s evidence=rtl-structural-preflight performance=not-measured\n' \
    "$source_sha256" "$comparison_sha256"
