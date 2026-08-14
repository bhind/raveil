#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
dockerfile="$repo_root/hardware/chisel/Dockerfile.physical-proxy"
image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64

command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

docker build \
    --provenance=false \
    --platform "$platform" \
    --file "$dockerfile" \
    --tag "$image" \
    "$repo_root"

image_id=$(docker image inspect --format '{{.Id}}' "$image")
image_size_bytes=$(docker image inspect --format '{{.Size}}' "$image")
dockerfile_sha256=$(shasum -a 256 "$dockerfile" | awk '{print $1}')
smoke_source_sha256=$(
    shasum -a 256 \
        "$repo_root/hardware/chisel/physical_proxy_smoke.sv" \
        "$repo_root/hardware/chisel/physical_proxy_smoke.sdc" \
        "$repo_root/hardware/chisel/run-physical-proxy-smoke-in-container.sh" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)

printf '%s\n' \
    "RAVEIL-PHYSICAL-IMAGE-V1 status=OK platform=$platform image=$image image_id=$image_id image_size_bytes=$image_size_bytes dockerfile_sha256=$dockerfile_sha256 smoke_source_sha256=$smoke_source_sha256 evidence=synthesis-toolchain-commissioning performance=not-measured"

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    "$image"
