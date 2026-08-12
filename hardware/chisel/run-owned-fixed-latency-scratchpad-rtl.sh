#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-static-stencil-rtl:v1
platform=linux/amd64
scala_cache=raveil-chisel-scala-cache-v1

command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

printf 'OWNED-MEMORY-HOST-V1 image=%s platform=%s cache=%s evidence=rtl-simulation-functional performance=not-measured\n' \
    "$image" "$platform" "$scala_cache"

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile" \
    --tag "$image" \
    "$repo_root"

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$scala_cache,target=/root/.cache" \
    "$image" \
    ./run-owned-fixed-latency-scratchpad.sh
