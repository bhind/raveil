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

RAVEIL_CHIPYARD_SOURCE="$chipyard" \
RAVEIL_BUILD_ONLY=1 \
    "$repo_root/hardware/chisel/run-fixture-repeated-rocket-stencil.sh"
image_id=$(docker image inspect --format '{{.Id}}' "$image")

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
mkdir /export/generated-src
cp -a "$source_dir"/. /export/generated-src/
test -n "$(find /export/generated-src -type f \( -name "*.sv" -o -name "*.v" \) -print -quit)"'

rtl_sha256=$(python3 -m raveil.t0044_physical hash-tree --path "$output_dir/generated-src")
printf '%s\n' \
    "RAVEIL-PHYSICAL-RTL-EXPORT-V1 status=OK variant=rocket-in-order config=chipyard.raveil.$config image_id=$image_id cache_source_sha256=$cache_source_sha256 rtl_sha256=$rtl_sha256 performance=not-measured"
