#!/bin/sh
set -eu

[ "$#" -eq 1 ] || {
    echo 'usage: export-physical-rocket-rtl.sh OUTPUT_DIR' >&2
    exit 2
}

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
output_dir=$1
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
image=$("$repo_root/hardware/chisel/verify-boom-functional-sim-image.sh")
platform=linux/amd64
build_volume=raveil-chipyard-physical-yosys-rocket-v1
baseline_build_volume=raveil-chipyard-fixture-repeated-rocket-v1
baseline_cache_source_sha256=${RAVEIL_PHYSICAL_CPU_BASELINE_CACHE_SOURCE_SHA256:-${RAVEIL_PHYSICAL_CPU_CACHE_SOURCE_SHA256:?baseline CPU cache-source identity is required}}
config=RaveilFixtureRepeatedMatchedRocketConfig

[ ! -e "$output_dir" ] || {
    echo "error: output path already exists: $output_dir" >&2
    exit 1
}
[ -d "$chipyard/.git" ] || {
    echo 'error: pinned Chipyard checkout is required' >&2
    exit 1
}
mkdir -p "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)

build_output=$(
    RAVEIL_CHIPYARD_SOURCE="$chipyard" \
        "$repo_root/hardware/chisel/run-physical-yosys-rocket-build.sh"
)
printf '%s\n' "$build_output"
build_marker=$(printf '%s\n' "$build_output" | grep '^RAVEIL-PHYSICAL-ROCKET-BUILD-V1 ')
[ "$(printf '%s\n' "$build_marker" | wc -l | tr -d ' ')" -eq 1 ]
source_sha256=$(printf '%s\n' "$build_marker" | sed -n 's/.* source_sha256=\([0-9a-f]\{64\}\) .*/\1/p')
toolchain_sha256=$(printf '%s\n' "$build_marker" | sed -n 's/.* toolchain_sha256=\([0-9a-f]\{64\}\) .*/\1/p')
cache_source_sha256=$(printf '%s\n' "$build_marker" | sed -n 's/.* cache_source_sha256=\([0-9a-f]\{64\}\) .*/\1/p')
[ "${#source_sha256}" -eq 64 ]
[ "${#toolchain_sha256}" -eq 64 ]
[ "${#cache_source_sha256}" -eq 64 ]
generator_rootfs_sha256=$(
    docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
        shasum -a 256 | awk '{print $1}'
)

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$build_volume,target=/build,readonly" \
    --mount "type=volume,source=$baseline_build_volume,target=/baseline,readonly" \
    --mount "type=bind,source=$output_dir,target=/export" \
    --env "RAVEIL_CACHE_SOURCE_SHA256=$cache_source_sha256" \
    --env "RAVEIL_BASELINE_CACHE_SOURCE_SHA256=$baseline_cache_source_sha256" \
    --env "RAVEIL_CPU_CONFIG=$config" \
    "$image" \
    bash -lc 'set -euo pipefail
build_root=/build/$RAVEIL_CACHE_SOURCE_SHA256
[ "$(cat "$build_root/.raveil-source-ready")" = "$RAVEIL_CACHE_SOURCE_SHA256" ]
source_dir="$build_root/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG"
[ -d "$source_dir" ]
baseline_dir="/baseline/$RAVEIL_BASELINE_CACHE_SOURCE_SHA256/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG"
[ -d "$baseline_dir" ]
long_name=chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG
base_options=emittedLineLength=2048,noAlwaysComb,disallowLocalVariables,verifLabels,locationInfoStyle=wrapInAtSquareBracket
physical_options=$base_options,disallowPackedArrays
[ "$(cat "$baseline_dir/.mfc_lowering_options")" = "$base_options" ]
[ "$(cat "$source_dir/.mfc_lowering_options")" = "$physical_options" ]
for relative in \
    "$long_name.fir" \
    .sfc_level \
    .extra_firrtl_options \
    "$long_name.sfc.fir"; do
    [ -f "$baseline_dir/$relative" ]
    [ -f "$source_dir/$relative" ]
    [ "$(sha256sum "$baseline_dir/$relative" | awk "{print \$1}")" = \
      "$(sha256sum "$source_dir/$relative" | awk "{print \$1}")" ] || {
        echo "error: physical lowering changed shared elaboration input: $relative" >&2
        exit 1
    }
done
for relative in \
    "$long_name.appended.anno.json" \
    "$long_name.sfc.anno.json"; do
    baseline_normalized=/tmp/baseline-$relative
    physical_normalized=/tmp/physical-$relative
    sed "s!/build/$RAVEIL_BASELINE_CACHE_SOURCE_SHA256!<build-root>!g" \
        "$baseline_dir/$relative" > "$baseline_normalized"
    sed "s!/build/$RAVEIL_CACHE_SOURCE_SHA256!<build-root>!g" \
        "$source_dir/$relative" > "$physical_normalized"
    ! grep -q "$RAVEIL_BASELINE_CACHE_SOURCE_SHA256" "$baseline_normalized"
    ! grep -q "$RAVEIL_CACHE_SOURCE_SHA256" "$physical_normalized"
    cmp "$baseline_normalized" "$physical_normalized" || {
        echo "error: physical lowering changed normalized annotation: $relative" >&2
        exit 1
    }
done
for relative in \
    model_module_hierarchy.json \
    model_module_hierarchy.uniquified.json \
    top_module_hierarchy.json; do
    [ -f "$baseline_dir/$relative" ]
    [ -f "$source_dir/$relative" ]
    [ "$(sha256sum "$baseline_dir/$relative" | awk "{print \$1}")" = \
      "$(sha256sum "$source_dir/$relative" | awk "{print \$1}")" ] || {
        echo "error: physical lowering changed module hierarchy: $relative" >&2
        exit 1
    }
done
for suffix in top.f model.f; do
    baseline_list=/tmp/baseline-$suffix
    physical_list=/tmp/physical-$suffix
    sed 's!.*/!!' "$baseline_dir/$long_name.$suffix" | LC_ALL=C sort > "$baseline_list"
    sed 's!.*/!!' "$source_dir/$long_name.$suffix" | LC_ALL=C sort > "$physical_list"
    cmp "$baseline_list" "$physical_list" || {
        echo "error: physical lowering changed normalized $suffix" >&2
        exit 1
    }
done
{
    printf "schema=raveil.physical-rocket-lowering-provenance/v1\n"
    printf "baseline_cache_source_sha256=%s\n" "$RAVEIL_BASELINE_CACHE_SOURCE_SHA256"
    printf "physical_cache_source_sha256=%s\n" "$RAVEIL_CACHE_SOURCE_SHA256"
    printf "baseline_lowering_options=%s\n" "$base_options"
    printf "physical_lowering_options=%s\n" "$physical_options"
    for relative in \
        "$long_name.fir" \
        .sfc_level \
        .extra_firrtl_options \
        "$long_name.sfc.fir"; do
        digest=$(sha256sum "$source_dir/$relative" | awk "{print \$1}")
        printf "shared_file=%s sha256=%s\n" "$relative" "$digest"
    done
    for relative in \
        "$long_name.appended.anno.json" \
        "$long_name.sfc.anno.json"; do
        digest=$(sha256sum "/tmp/physical-$relative" | awk "{print \$1}")
        printf "shared_normalized_annotation=%s sha256=%s\n" "$relative" "$digest"
    done
    for relative in \
        model_module_hierarchy.json \
        model_module_hierarchy.uniquified.json \
        top_module_hierarchy.json; do
        digest=$(sha256sum "$source_dir/$relative" | awk "{print \$1}")
        printf "shared_hierarchy=%s sha256=%s\n" "$relative" "$digest"
    done
    for suffix in top.f model.f; do
        digest=$(sha256sum "/tmp/physical-$suffix" | awk "{print \$1}")
        printf "shared_normalized_filelist=%s sha256=%s\n" "$suffix" "$digest"
    done
    printf "status=shared-elaboration-identical\n"
} > /export/lowering-provenance.txt
filelist="$source_dir/chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG.top.f"
[ -f "$filelist" ]
mkdir /export/generated-src
while IFS= read -r source; do
    case "$source" in
        "$source_dir"/gen-collateral/*.sv|"$source_dir"/gen-collateral/*.v) ;;
        *) echo "error: non-canonical RTL file-list entry: $source" >&2; exit 1 ;;
    esac
    target=/export/generated-src/$(basename "$source")
    [ ! -e "$target" ]
    cp "$source" "$target"
done < "$filelist"
test -n "$(find /export/generated-src -type f \( -name "*.sv" -o -name "*.v" \) -print -quit)"
find /export/generated-src -type f -print | LC_ALL=C sort > /export/rtl-files.txt'

rtl_sha256=$(python3 -m raveil.t0044_physical hash-tree --path "$output_dir/generated-src")
rtl_filelist_sha256=$(shasum -a 256 "$output_dir/rtl-files.txt" | awk '{print $1}')
lowering_provenance_sha256=$(shasum -a 256 "$output_dir/lowering-provenance.txt" | awk '{print $1}')
printf '%s\n' \
    "RAVEIL-PHYSICAL-RTL-EXPORT-V1 status=OK variant=rocket-in-order top=Rocket config=chipyard.raveil.$config generator_rootfs_sha256=$generator_rootfs_sha256 baseline_cache_source_sha256=$baseline_cache_source_sha256 cache_source_sha256=$cache_source_sha256 source_sha256=$source_sha256 toolchain_sha256=$toolchain_sha256 compatibility_lowering=disallowPackedArrays lowering_provenance_sha256=$lowering_provenance_sha256 rtl_sha256=$rtl_sha256 rtl_filelist_sha256=$rtl_filelist_sha256 performance=not-measured"
