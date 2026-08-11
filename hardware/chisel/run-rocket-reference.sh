#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
rocket_source="$repo_root/external/rocket-chip"
container_script="$repo_root/hardware/chisel/rocket-reference-in-container.sh"
image='nixos/nix:2.13.3@sha256:1f8fa57de6f2f9ea5ea8d115b339fa68d2f98f20b59438bdb9d3a082ad64d4bf'
platform=linux/amd64
cache_volume=${RAVEIL_ROCKET_NIX_VOLUME:-raveil-t0105-nix-store}
case "$cache_volume" in
    [A-Za-z0-9]*) ;;
    *) echo 'error: RAVEIL_ROCKET_NIX_VOLUME must start with an ASCII alphanumeric' >&2; exit 1 ;;
esac
case "$cache_volume" in
    *[!A-Za-z0-9_.-]*) echo 'error: RAVEIL_ROCKET_NIX_VOLUME contains an invalid character' >&2; exit 1 ;;
esac
[ "${#cache_volume}" -le 96 ] || {
    echo 'error: RAVEIL_ROCKET_NIX_VOLUME is too long' >&2
    exit 1
}
output_volume="${cache_volume}-mill-out-v1"
user_cache_volume="${cache_volume}-user-cache-v1"

[ -d "$rocket_source/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-rocket.sh first' >&2
    exit 1
}
[ -z "$(git -C "$rocket_source" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: Rocket checkout or a pinned submodule has local changes' >&2
    exit 1
}
command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

printf 'ROCKET-REFERENCE-HOST-V1 image=%s platform=%s nix_cache=%s mill_output=%s user_cache=%s claim=functional-only\n' \
    "$image" "$platform" "$cache_volume" "$output_volume" "$user_cache_volume"

docker run --rm --pull=missing \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$rocket_source,target=/rocket" \
    --mount "type=bind,source=$container_script,target=/raveil-rocket-reference-in-container.sh,readonly" \
    --mount "type=volume,source=$cache_volume,target=/nix" \
    --mount "type=volume,source=$output_volume,target=/rocket/out" \
    --mount "type=volume,source=$user_cache_volume,target=/root/.cache" \
    --workdir /rocket \
    "$image" \
    sh /raveil-rocket-reference-in-container.sh
