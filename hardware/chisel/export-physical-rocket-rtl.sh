#!/bin/sh
set -eu

[ "$#" -eq 1 ] || {
    echo 'usage: export-physical-rocket-rtl.sh OUTPUT_DIR' >&2
    exit 2
}

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
output_dir=$1
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
image=raveil-boom-functional-sim:v1
platform=linux/amd64
build_volume=raveil-chipyard-fixture-repeated-rocket-v1
cache_source_sha256=${RAVEIL_PHYSICAL_CPU_CACHE_SOURCE_SHA256:?CPU cache-source identity is required}
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
    RAVEIL_BUILD_ONLY=1 \
        "$repo_root/hardware/chisel/run-fixture-repeated-rocket-stencil.sh"
)
printf '%s\n' "$build_output"
build_marker=$(printf '%s\n' "$build_output" | grep '^RAVEIL-FIXTURE-BUILD-V1 ')
[ "$(printf '%s\n' "$build_marker" | wc -l | tr -d ' ')" -eq 1 ]
source_sha256=$(printf '%s\n' "$build_marker" | sed -n 's/.* source_sha256=\([0-9a-f]\{64\}\) .*/\1/p')
toolchain_sha256=$(printf '%s\n' "$build_marker" | sed -n 's/.* toolchain_sha256=\([0-9a-f]\{64\}\) .*/\1/p')
[ "${#source_sha256}" -eq 64 ]
[ "${#toolchain_sha256}" -eq 64 ]
generator_rootfs_sha256=$(
    docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
        shasum -a 256 | awk '{print $1}'
)

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$build_volume,target=/build,readonly" \
    --mount "type=bind,source=$output_dir,target=/export" \
    --env "RAVEIL_CACHE_SOURCE_SHA256=$cache_source_sha256" \
    --env "RAVEIL_CPU_CONFIG=$config" \
    "$image" \
    bash -lc 'set -euo pipefail
build_root=/build/$RAVEIL_CACHE_SOURCE_SHA256
[ "$(cat "$build_root/.raveil-source-ready")" = "$RAVEIL_CACHE_SOURCE_SHA256" ]
source_dir="$build_root/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG"
[ -d "$source_dir" ]
filelist="$(dirname "$source_dir")/chipyard.harness.TestHarness.$RAVEIL_CPU_CONFIG.top.f"
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
printf '%s\n' \
    "RAVEIL-PHYSICAL-RTL-EXPORT-V1 status=OK variant=rocket-in-order top=Rocket config=chipyard.raveil.$config generator_rootfs_sha256=$generator_rootfs_sha256 cache_source_sha256=$cache_source_sha256 source_sha256=$source_sha256 toolchain_sha256=$toolchain_sha256 rtl_sha256=$rtl_sha256 rtl_filelist_sha256=$rtl_filelist_sha256 performance=not-measured"
