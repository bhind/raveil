#!/bin/sh
# Parse and structurally verify the two exported ChipTop RTL closures.
# No synthesis, mapping, timing, area, or other candidate data is collected.
set -eu
umask 077

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

[ "$#" -eq 3 ] ||
    fail 'usage: run-exp0011-rtl-preflight.sh INTEGRATED_EXPORT BASELINE_EXPORT APPEND_ONLY_OUTPUT_DIR'
integrated_export=$1
baseline_export=$2
output_dir=$3
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64
expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169
expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5

[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"
for export_dir in "$integrated_export" "$baseline_export"; do
    [ -s "$export_dir/ChipTop.top.f" ] || fail "missing ChipTop file list: $export_dir"
    [ -s "$export_dir/export-metadata.json" ] || fail "missing export metadata: $export_dir"
done
command -v docker >/dev/null 2>&1 || fail 'docker is required'

integrated_export=$(CDPATH= cd -- "$integrated_export" && pwd)
baseline_export=$(CDPATH= cd -- "$baseline_export" && pwd)
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl validate-export \
    --export-dir "$integrated_export" \
    --variant integrated-static-graph-rocket >/dev/null
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl validate-export \
    --export-dir "$baseline_export" \
    --variant matched-rocket-system >/dev/null
mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)
mkdir "$output_dir/raw" "$output_dir/derived"
raw_dir=$output_dir/raw
derived_dir=$output_dir/derived

image_id=$(docker image inspect --format '{{.Id}}' "$image")
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
    shasum -a 256 | awk '{print $1}')
[ "$image_id" = "$expected_image_id" ] ||
    fail "physical toolchain image ID drift: $image_id"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] ||
    fail "physical toolchain RootFS drift: $rootfs_sha256"

docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$integrated_export,target=/integrated,readonly" \
    --mount "type=bind,source=$baseline_export,target=/baseline,readonly" \
    --mount "type=bind,source=$raw_dir,target=/out" \
    "$image" sh -c 'set -eu
yosys -V > /out/yosys-version.txt
for variant in integrated baseline; do
    cd "/$variant"
    : > /tmp/read-rtl.ys
    while IFS= read -r source; do
        case "$source" in
            generated-src/*)
                base=${source#generated-src/}
                case "$base" in
                    *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-]*|*/*|"")
                        echo "error: unsafe RTL entry during preflight: $source" >&2
                        exit 1
                        ;;
                    *.sv|*.v) ;;
                    *) echo "error: unsupported RTL suffix during preflight: $source" >&2; exit 1 ;;
                esac
                ;;
            *) echo "error: non-local RTL entry during preflight: $source" >&2; exit 1 ;;
        esac
        test -f "$source"
        printf "read_verilog -sv %s\n" "$source" >> /tmp/read-rtl.ys
    done < ChipTop.top.f
    test -s /tmp/read-rtl.ys
    cat >> /tmp/read-rtl.ys <<'YOSYS'
hierarchy -generate cc_banks_0_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata
hierarchy -generate cc_dir_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata i:RW0_wmask
hierarchy -generate data_arrays_0_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata i:RW0_wmask
hierarchy -generate data_arrays_0_0_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata i:RW0_wmask
hierarchy -generate tag_array_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata i:RW0_wmask
hierarchy -generate tag_array_0_ext i:RW0_addr i:RW0_en i:RW0_clk i:RW0_wmode i:RW0_wdata o:RW0_rdata i:RW0_wmask
hierarchy -generate memory_ext i:R0_addr i:R0_en i:R0_clk o:R0_data i:W0_addr i:W0_en i:W0_clk i:W0_data i:W0_mask
YOSYS
    cp /tmp/read-rtl.ys /tmp/structural.ys
    printf "hierarchy -check -top ChipTop\nwrite_rtlil /out/%s-hierarchy.rtlil\nflatten\nproc\nopt_clean\ncheck\nwrite_json /out/%s-flat.json\n" \
        "$variant" "$variant" >> /tmp/structural.ys
    yosys -q -l "/out/$variant-yosys.log" -s /tmp/structural.ys
done
'

find "$raw_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(shasum -a 256 "$file" | awk '{print $1}')" "$(basename "$file")"
    done > "$raw_dir/sha256s.txt"
raw_manifest_sha256=$(shasum -a 256 "$raw_dir/sha256s.txt" | awk '{print $1}')

PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl analyze \
    --export-dir "$integrated_export" \
    --hierarchy "$raw_dir/integrated-hierarchy.rtlil" \
    --flat "$raw_dir/integrated-flat.json" \
    --variant integrated-static-graph-rocket \
    > "$derived_dir/integrated-report.json"
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl analyze \
    --export-dir "$baseline_export" \
    --hierarchy "$raw_dir/baseline-hierarchy.rtlil" \
    --flat "$raw_dir/baseline-flat.json" \
    --variant matched-rocket-system \
    > "$derived_dir/baseline-report.json"
PYTHONPATH="$repo_root" python3 -m raveil.t0044_integrated_rtl compare \
    --integrated-report "$derived_dir/integrated-report.json" \
    --baseline-report "$derived_dir/baseline-report.json" \
    > "$derived_dir/comparison-report.json"

runner_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/run-exp0011-rtl-preflight.sh" | awk '{print $1}')
analyzer_sha256=$(shasum -a 256 "$repo_root/raveil/t0044_integrated_rtl.py" | awk '{print $1}')
python3 - "$derived_dir/preflight-metadata.json" <<EOF
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
record = {
    "schema": "raveil.exp-0011-rtl-preflight/v1",
    "image": "$image",
    "image_id": "$image_id",
    "image_rootfs_sha256": "$rootfs_sha256",
    "platform": "$platform",
    "runner_sha256": "$runner_sha256",
    "analyzer_sha256": "$analyzer_sha256",
    "raw_manifest_sha256": "$raw_manifest_sha256",
    "commands": [
        "read each validated ChipTop.top.f entry with read_verilog -sv",
        "hierarchy -check -top ChipTop",
        "single parse: checked hierarchy RTLIL; flatten; proc; opt_clean; check; flat JSON",
    ],
    "evidence_class": "rtl-structural-preflight",
    "performance": "not-measured",
    "nonclaim": "no synthesis, mapping, timing, area, energy, FPGA, ASIC, or silicon result",
}
path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
EOF

find "$derived_dir" -type f ! -name sha256s.txt -print | LC_ALL=C sort |
    while IFS= read -r file; do
        printf '%s  %s\n' "$(shasum -a 256 "$file" | awk '{print $1}')" "$(basename "$file")"
    done > "$derived_dir/sha256s.txt"
comparison_sha256=$(shasum -a 256 "$derived_dir/comparison-report.json" | awk '{print $1}')
printf 'EXP0011-RTL-PREFLIGHT-V1 status=OK top=ChipTop integrated=chipyard.raveil.RaveilRuntimeIntegratedGraphRocketConfig baseline=chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig ports=equal rocket_module=equal rocket_instances=one-each blackboxes=matched-memory-macros-only clocks=clock_uncore,jtag_TCK,serial_tl_0_clock_in comparison_sha256=%s evidence=rtl-structural-preflight performance=not-measured\n' \
    "$comparison_sha256"
