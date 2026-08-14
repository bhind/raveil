#!/bin/sh
set -eu

[ "$#" -eq 1 ] || {
    echo 'usage: export-physical-graph-rtl.sh OUTPUT_DIR' >&2
    exit 2
}

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
output_dir=$1
image=raveil-static-stencil-rtl:v1
platform=linux/amd64
scala_cache=raveil-chisel-scala-cache-v1

[ ! -e "$output_dir" ] || {
    echo "error: output path already exists: $output_dir" >&2
    exit 1
}
mkdir -p "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)

docker build --provenance=false \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile" \
    --tag "$image" \
    "$repo_root"
image_id=$(docker image inspect --format '{{.Id}}' "$image")

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$scala_cache,target=/root/.cache" \
    --mount "type=bind,source=$output_dir,target=/export" \
    "$image" \
    sh -lc 'set -eu
rm -rf generated_static
scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala StaticStencilRegion.scala \
  --server=false --main-class EmitPhysicalStaticStencilRegion
mkdir /export/generated-src
cp generated_physical_static/*.sv /export/generated-src/
test -n "$(find /export/generated-src -type f -name "*.sv" -print -quit)"'

source_sha256=$(
    shasum -a 256 \
        "$repo_root/hardware/chisel/OwnedFixedLatencyScratchpad.scala" \
        "$repo_root/hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala" \
        "$repo_root/hardware/chisel/StaticStencilRegion.scala" |
        awk '{print $1}' | shasum -a 256 | awk '{print $1}'
)
rtl_sha256=$(python3 -m raveil.t0044_physical hash-tree --path "$output_dir/generated-src")
printf '%s\n' \
    "RAVEIL-PHYSICAL-RTL-EXPORT-V1 status=OK variant=static-graph top=StaticStencilRegion image_id=$image_id source_sha256=$source_sha256 rtl_sha256=$rtl_sha256 performance=not-measured"
