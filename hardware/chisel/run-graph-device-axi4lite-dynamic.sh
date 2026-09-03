#!/bin/sh
set -eu
set -C
case "$#" in
  2) test "$1" = --request \
    || { echo 'usage: run-graph-device-axi4lite-dynamic.sh --request ROOT [--request ROOT]' >&2; exit 2; }
    request_count=1; first=$2; second= ;;
  4) test "$1" = --request && test "$3" = --request \
    || { echo 'usage: run-graph-device-axi4lite-dynamic.sh --request ROOT [--request ROOT]' >&2; exit 2; }
    request_count=2; first=$2; second=$4 ;;
  *) echo 'usage: run-graph-device-axi4lite-dynamic.sh --request ROOT [--request ROOT]' >&2; exit 2 ;;
esac
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
for request_root in "$first" ${second:+"$second"}; do
  case "$request_root" in
    "$repo_root/artifacts/graph_device_axi4lite_dynamic/"*) ;;
    *) echo 'error: dynamic request roots must be private repository artifacts' >&2; exit 2;;
  esac
  test -d "$request_root" && test ! -L "$request_root" || { echo 'error: dynamic request root is unsafe' >&2; exit 2; }
done
first_parent=$(CDPATH= cd -- "$(dirname -- "$first")" && pwd)
test "$(basename -- "$first")" = request-1 \
  || { echo 'error: first dynamic request must be request-1' >&2; exit 2; }
if test "$request_count" = 2; then
  second_parent=$(CDPATH= cd -- "$(dirname -- "$second")" && pwd)
  test "$first_parent" = "$second_parent" && test "$(basename -- "$second")" = request-2 \
    || { echo 'error: dynamic requests must be request-1/request-2 siblings' >&2; exit 2; }
fi
command -v docker >/dev/null 2>&1 || { echo 'error: docker is required' >&2; exit 1; }
dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
expected_image_id=sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)" = "$dockerfile_sha256" \
  || { echo 'error: required cached offline image is unavailable; refusing network build' >&2; exit 1; }
image_id=$(docker image inspect --format '{{.Id}}' "$image")
test "$image_id" = "$expected_image_id" || { echo 'error: cached image ID differs from reviewed immutable image' >&2; exit 1; }
session=$first_parent
for output in container.stdout container.stderr; do
  test ! -e "$session/$output" && test ! -L "$session/$output" \
    || { echo "error: dynamic session output already exists: $output" >&2; exit 2; }
done
docker run --rm --network none --security-opt no-new-privileges=true --platform linux/amd64 \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" \
  --mount "type=bind,source=$session,target=/session" \
  --workdir /repo/hardware/chisel "$image_id" \
  ./run-graph-device-axi4lite-dynamic-in-container.sh \
  "/session/$(basename "$first")" ${second:+"/session/$(basename "$second")"} "$(basename "$session")" \
  > "$session/container.stdout" 2> "$session/container.stderr"
cat "$session/container.stdout"
