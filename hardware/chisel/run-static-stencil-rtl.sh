#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-static-stencil-rtl:v1
platform=linux/amd64
scala_cache=raveil-chisel-scala-cache-v1
rtl_log=$(mktemp "${TMPDIR:-/tmp}/raveil-static-controlled.XXXXXX")
trap 'rm -f "$rtl_log"' EXIT HUP INT TERM

command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

printf 'STATIC-STENCIL-HOST-V1 image=%s platform=%s cache=%s evidence=rtl-simulation-functional performance=not-measured\n' \
    "$image" "$platform" "$scala_cache"

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile" \
    --tag "$image" \
    "$repo_root"

dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
toolchain_sha256=$(
    printf '%s\n' "$platform" "$dockerfile_sha256" \
        'scala-cli=1.10.1' 'java=17.0.19' 'verilator=4.038' |
        shasum -a 256 |
        awk '{print $1}'
)

pilot_seed=${RAVEIL_PILOT_SEED:-}
pilot_env=
if [ -n "$pilot_seed" ]; then
    case "$pilot_seed" in
        *[!0-9]*|'') echo 'error: RAVEIL_PILOT_SEED must be a positive integer' >&2; exit 1 ;;
    esac
    [ "$pilot_seed" -gt 0 ] || { echo 'error: RAVEIL_PILOT_SEED must be positive' >&2; exit 1; }
    pilot_env="--env=RAVEIL_PILOT_SEED=$pilot_seed"
fi

if ! docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$scala_cache,target=/root/.cache" \
    --env "RAVEIL_TOOLCHAIN_SHA256=$toolchain_sha256" \
    $pilot_env \
    "$image" \
    ./run-static-stencil.sh >"$rtl_log" 2>&1; then
    sed -n '1,240p' "$rtl_log"
    exit 1
fi
sed -n '1,240p' "$rtl_log"

cd "$repo_root"
if [ -n "$pilot_seed" ]; then
    python3 -m raveil.controlled_run \
        --verify-static-graph-pilot-log "$rtl_log" --seed "$pilot_seed"
    exit 0
fi
python3 -m raveil.controlled_run --verify-static-graph-log "$rtl_log"
python3 -m raveil.simulation_adapter --invocation 1 --status completed
python3 -m raveil.simulation_adapter --invocation 2 --status cancelled
python3 -m raveil.simulation_adapter --invocation 3 --status completed
