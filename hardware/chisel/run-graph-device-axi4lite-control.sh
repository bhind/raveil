#!/bin/sh
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
artifact_parent=$repo_root/artifacts/graph_device_axi4lite_control
mkdir -p "$artifact_parent"
evidence_root=$(mktemp -d "$artifact_parent/run.XXXXXX")
trap 'rm -rf "$repo_root/hardware/chisel/generated_axi4lite" "$repo_root/hardware/chisel/generated_axi4lite_repeat" "$repo_root/hardware/chisel/obj_graph_device_axi4lite"' EXIT HUP INT TERM
command -v docker >/dev/null 2>&1 || { echo 'error: docker is required' >&2; exit 1; }
dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)" = "$dockerfile_sha256" || { echo 'error: required cached offline image is unavailable; refusing network build' >&2; exit 1; }
image_id=$(docker image inspect --format '{{.Id}}' "$image")
case "$image_id" in sha256:[0-9a-f][0-9a-f]*) ;; *) echo 'error: cached image ID is not immutable sha256' >&2; exit 1;; esac
test "${#image_id}" = 71 || { echo 'error: cached image ID has unexpected length' >&2; exit 1; }
cd "$repo_root"
python3 -m raveil.graph_device_axi4lite prepare --output "$evidence_root"
printf 'schema=raveil.graph-device-axi4lite-environment/v1\nplatform=linux/amd64\nimage_id=%s\n' "$image_id" > "$evidence_root/environment.txt"
docker run --rm --network none --security-opt no-new-privileges=true --platform linux/amd64 \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" --mount "type=bind,source=$evidence_root,target=/evidence" \
  --workdir /repo/hardware/chisel "$image_id" ./run-graph-device-axi4lite-control-in-container.sh /evidence > "$evidence_root/container.stdout" 2> "$evidence_root/container.stderr"
python3 -m raveil.graph_device_axi4lite finalize --evidence "$evidence_root"
printf 'GraphDevice-AXI4LITE-CONTROL-EVIDENCE-V1 path=artifacts/graph_device_axi4lite_control/%s private=1 publication=0\n' "$(basename "$evidence_root")"
