#!/bin/sh
set -eu

if [ "$#" -ne 4 ] || [ "$1" != "--graph" ] || [ "$3" != "--seed" ]; then
  echo 'usage: run-graph-device-selected.sh --graph REPOSITORY_DESCRIPTOR --seed UINT32' >&2
  exit 2
fi
graph=$2
seed=$4
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chisel_dir=$repo_root/hardware/chisel
artifact_parent=$repo_root/artifacts/graph_device_selected
case "$artifact_parent" in "$repo_root"/artifacts/*) ;; *) exit 2;; esac
evidence_root=
completed=0
cleanup() {
  status=$?
  if [ "$completed" -ne 1 ] && [ -n "$evidence_root" ] && [ -d "$evidence_root" ]; then
    rm -rf "$evidence_root"
  fi
  exit "$status"
}
trap cleanup EXIT HUP INT TERM
cd "$repo_root"
# This happens before Docker discovery, image build, or output creation.
python3 -m raveil.graph_device_selected validate --graph "$graph" --seed "$seed" >/dev/null
mkdir -p "$artifact_parent"
evidence_root=$(mktemp -d "$artifact_parent/run.XXXXXX")
python3 -m raveil.graph_device_selected prepare --graph "$graph" --seed "$seed" --output "$evidence_root"
dockerfile_sha256=$(shasum -a 256 "$chisel_dir/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
label=$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)
if [ "$label" != "$dockerfile_sha256" ]; then
  docker build --provenance=false --label "raveil.dockerfile.sha256=$dockerfile_sha256" \
    --platform linux/amd64 --file "$chisel_dir/Dockerfile" --tag "$image" "$repo_root"
fi
image_id=$(docker image inspect --format '{{.Id}}' "$image")
{
  printf 'schema=raveil.graph-device-selected-environment/v1\nplatform=linux/amd64\n'
  printf 'dockerfile_sha256=%s\nimage_id=%s\n' "$dockerfile_sha256" "$image_id"
} > "$evidence_root/environment.txt"
docker run --rm --platform linux/amd64 --network none --security-opt no-new-privileges=true \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" \
  --mount "type=bind,source=$evidence_root,target=/evidence" \
  --workdir /repo/hardware/chisel "$image" \
  ./run-graph-device-dag-in-container.sh /evidence "$(python3 -c 'from raveil.graph_device_submit import admit; import sys; print(admit(sys.argv[1], int(sys.argv[2]))["graph_id"])' "$graph" "$seed")" "$seed"
python3 -m raveil.graph_device_selected finalize --evidence "$evidence_root" >/dev/null
completed=1
printf 'GraphDevice-SELECTED-EVIDENCE-V1 path=artifacts/graph_device_selected/%s private=1 publication=0\n' "$(basename "$evidence_root")"
