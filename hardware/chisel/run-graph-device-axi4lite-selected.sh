#!/bin/sh
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
artifact_parent=$repo_root/artifacts/graph_device_axi4lite_selected
mkdir -p "$artifact_parent"
evidence_root=$(mktemp -d "$artifact_parent/run.XXXXXX")
trap 'rm -rf "$repo_root/hardware/chisel/generated_axi4lite_selected" "$repo_root/hardware/chisel/generated_axi4lite_selected_repeat" "$repo_root/hardware/chisel/obj_graph_device_axi4lite_selected"' EXIT HUP INT TERM
command -v docker >/dev/null 2>&1 || { echo 'error: docker is required' >&2; exit 1; }
dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
expected_image_id=sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)" = "$dockerfile_sha256" || { echo 'error: required cached offline image is unavailable; refusing network build' >&2; exit 1; }
image_id=$(docker image inspect --format '{{.Id}}' "$image")
test "$image_id" = "$expected_image_id" || { echo 'error: cached image ID differs from reviewed immutable image' >&2; exit 1; }
cd "$repo_root"
python3 -m raveil.graph_device_axi4lite_selected prepare --output "$evidence_root"
printf 'schema=raveil.graph-device-axi4lite-selected-environment/v1\nplatform=linux/amd64\nimage_id=%s\n' "$image_id" > "$evidence_root/environment.txt"
docker run --rm --network none --security-opt no-new-privileges=true --platform linux/amd64 \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" --mount "type=bind,source=$evidence_root,target=/evidence" \
  --workdir /repo/hardware/chisel "$image_id" ./run-graph-device-axi4lite-selected-in-container.sh /evidence > "$evidence_root/container.stdout" 2> "$evidence_root/container.stderr"
python3 -m raveil.graph_device_axi4lite_selected finalize --evidence "$evidence_root" >/dev/null
python3 -m raveil.graph_device_axi4lite_selected verify --evidence "$evidence_root" >/dev/null
printf 'GraphDevice-AXI4LITE-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_axi4lite_selected/%s private=1 publication=0\n' "$(basename "$evidence_root")"
