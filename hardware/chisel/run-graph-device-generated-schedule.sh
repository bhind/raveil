#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chisel_dir=$repo_root/hardware/chisel
artifact_parent=$repo_root/artifacts/graph_device_schedule
case "$chisel_dir" in "$repo_root"/*) ;; *) exit 1;; esac
case "$artifact_parent" in "$repo_root"/artifacts/*) ;; *) exit 1;; esac

cleanup() {
  rm -rf "$chisel_dir/generated_static" "$chisel_dir/obj_graph_device_schedule" \
    "$chisel_dir/.bsp" "$chisel_dir/.scala-build"
}
trap cleanup EXIT HUP INT TERM
cleanup

command -v docker >/dev/null 2>&1 || { echo 'error: docker is required' >&2; exit 1; }
mkdir -p "$artifact_parent"
evidence_root=$(mktemp -d "$artifact_parent/run.XXXXXX")

cd "$repo_root"
python3 -m raveil.graph_device_schedule prepare --output "$evidence_root"

dockerfile_sha256=$(shasum -a 256 "$chisel_dir/Dockerfile" | awk '{print $1}')
image="raveil-graph_device-schedule:sha256-${dockerfile_sha256}"
label=$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)
if [ "$label" != "$dockerfile_sha256" ]; then
  docker build --provenance=false \
    --label "raveil.dockerfile.sha256=$dockerfile_sha256" \
    --platform linux/amd64 \
    --file "$chisel_dir/Dockerfile" \
    --tag "$image" \
    "$repo_root"
fi
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image")" = "$dockerfile_sha256"
image_id=$(docker image inspect --format '{{.Id}}' "$image")

{
  printf 'schema=raveil.graph-device-schedule-environment/v1\n'
  printf 'platform=linux/amd64\n'
  printf 'dockerfile_sha256=%s\n' "$dockerfile_sha256"
  printf 'image_id=%s\n' "$image_id"
} > "$evidence_root/environment.txt"

docker run --rm \
  --platform linux/amd64 \
  --network none \
  --security-opt no-new-privileges=true \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache \
  --mount "type=bind,source=$repo_root,target=/repo" \
  --mount "type=bind,source=$evidence_root,target=/evidence" \
  --workdir /repo/hardware/chisel \
  "$image" \
  ./run-graph-device-generated-schedule-in-container.sh /evidence

python3 -m raveil.graph_device_mvp finalize --evidence "$evidence_root"
python3 -m raveil.graph_device_schedule finalize --evidence "$evidence_root"
printf 'GraphDevice-SCHEDULE-EVIDENCE-V1 path=artifacts/graph_device_schedule/%s private=1 publication=0\n' \
  "$(basename "$evidence_root")"
