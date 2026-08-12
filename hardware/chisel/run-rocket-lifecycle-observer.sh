#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
rtl="$repo_root/hardware/chisel/RaveilRocketLifecycleObserver.scala"
driver="$repo_root/hardware/chisel/rocket_lifecycle_observer_sim_main.cpp"
verifier="$repo_root/hardware/chisel/verify_rocket_lifecycle_observer.py"
runner="$repo_root/hardware/chisel/run-rocket-lifecycle-observer.sh"
dockerfile="$repo_root/hardware/chisel/Dockerfile"
image=raveil-static-stencil-rtl:v1
platform=linux/amd64
scala_cache=raveil-chisel-scala-cache-v1

for input in "$rtl" "$driver" "$verifier" "$runner" "$dockerfile"; do
    [ -f "$input" ] || {
        echo "error: required Rocket lifecycle observer input is missing: $input" >&2
        exit 1
    }
done
command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

input_sha256=$(
    shasum -a 256 "$rtl" "$driver" "$verifier" "$runner" "$dockerfile" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)

docker build \
    --platform "$platform" \
    --provenance=false \
    --file "$dockerfile" \
    --tag "$image" \
    "$repo_root"

printf 'ROCKET-LIFECYCLE-OBSERVER-HOST-V1 image=%s platform=%s input_sha256=%s event_source=synthetic cpu_execution=not-run semantic_initiator=not-proven resource_match_verified=0 evidence=rtl-simulation-functional performance=not-measured\n' \
    "$image" "$platform" "$input_sha256"

observer_log=$(mktemp "${TMPDIR:-/tmp}/raveil-rocket-lifecycle-observer.XXXXXX")
trap 'rm -f "$observer_log"' EXIT HUP INT TERM

if ! docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=volume,source=$scala_cache,target=/root/.cache" \
    "$image" \
    sh -c 'set -eu
rm -rf generated_rocket_lifecycle_observer obj_rocket_lifecycle_observer
scala-cli run RaveilRocketLifecycleObserver.scala --server=false \
  --main-class EmitRaveilRocketLifecycleObserver
verilator --assert --cc \
  generated_rocket_lifecycle_observer/RaveilRocketLifecycleObserver.sv \
  --exe rocket_lifecycle_observer_sim_main.cpp \
  --build \
  --Mdir obj_rocket_lifecycle_observer \
  --top-module RaveilRocketLifecycleObserver \
  -CFLAGS "-std=c++17 -Wall -Wextra -Werror"
./obj_rocket_lifecycle_observer/VRaveilRocketLifecycleObserver' \
    >"$observer_log" 2>&1; then
    cat "$observer_log"
    exit 1
fi
cat "$observer_log"
python3 "$verifier" "$observer_log"
