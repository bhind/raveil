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
repeat_account=${RAVEIL_REPEAT_ACCOUNT:-}
repeat_env=
fixture_account=${RAVEIL_FIXTURE_REPEAT_ACCOUNT:-}
fixture_env=
mode_count=0
[ -z "$pilot_seed" ] || mode_count=$((mode_count + 1))
[ -z "$repeat_account" ] || mode_count=$((mode_count + 1))
[ -z "$fixture_account" ] || mode_count=$((mode_count + 1))
if [ "$mode_count" -gt 1 ]; then
    echo 'error: pilot, repeat, and fixture account are mutually exclusive' >&2
    exit 1
fi
if [ -n "$fixture_account" ]; then
    case "$fixture_account" in
        *[!0-9]*|'') echo 'error: RAVEIL_FIXTURE_REPEAT_ACCOUNT must be in [1,256]' >&2; exit 1 ;;
    esac
    [ "$fixture_account" -ge 1 ] && [ "$fixture_account" -le 256 ] || {
        echo 'error: RAVEIL_FIXTURE_REPEAT_ACCOUNT must be in [1,256]' >&2
        exit 1
    }
    fixture_env="--env=RAVEIL_FIXTURE_REPEAT_ACCOUNT=$fixture_account"
fi
if [ -n "$pilot_seed" ]; then
    case "$pilot_seed" in
        *[!0-9]*|'') echo 'error: RAVEIL_PILOT_SEED must be a positive integer' >&2; exit 1 ;;
    esac
    [ "$pilot_seed" -gt 0 ] || { echo 'error: RAVEIL_PILOT_SEED must be positive' >&2; exit 1; }
    pilot_env="--env=RAVEIL_PILOT_SEED=$pilot_seed"
fi
if [ -n "$repeat_account" ]; then
    case "$repeat_account" in
        *[!0-9]*|'') echo 'error: RAVEIL_REPEAT_ACCOUNT must be in [1,256]' >&2; exit 1 ;;
    esac
    [ "$repeat_account" -ge 1 ] && [ "$repeat_account" -le 256 ] || {
        echo 'error: RAVEIL_REPEAT_ACCOUNT must be in [1,256]' >&2
        exit 1
    }
    repeat_env="--env=RAVEIL_REPEAT_ACCOUNT=$repeat_account"
fi

if ! docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$scala_cache,target=/root/.cache" \
    --env "RAVEIL_TOOLCHAIN_SHA256=$toolchain_sha256" \
    $pilot_env \
    $repeat_env \
    $fixture_env \
    "$image" \
    ./run-static-stencil.sh >"$rtl_log" 2>&1; then
    sed -n '1,240p' "$rtl_log"
    exit 1
fi
if [ -n "$repeat_account" ] || [ -n "$fixture_account" ]; then
    # EXP-0006 outer raw is the evidence boundary.  Do not apply the legacy
    # human-readable smoke-log preview cap to repeated output evidence.
    cat "$rtl_log"
else
    sed -n '1,240p' "$rtl_log"
fi

cd "$repo_root"
if [ -n "$repeat_account" ]; then
    python3 -m raveil.t0044_repeated verify-graph \
        --log "$rtl_log" --account "$repeat_account"
    exit 0
fi
if [ -n "$fixture_account" ]; then
    exit 0
fi
if [ -n "$pilot_seed" ]; then
    python3 -m raveil.controlled_run \
        --verify-static-graph-pilot-log "$rtl_log" --seed "$pilot_seed"
    exit 0
fi
python3 -m raveil.controlled_run --verify-static-graph-log "$rtl_log"
python3 -m raveil.simulation_adapter --invocation 1 --status completed
python3 -m raveil.simulation_adapter --invocation 2 --status cancelled
python3 -m raveil.simulation_adapter --invocation 3 --status completed
