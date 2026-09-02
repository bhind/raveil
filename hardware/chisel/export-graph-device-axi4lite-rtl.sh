#!/bin/sh
set -eu
usage='usage: export-graph-device-axi4lite-rtl.sh [--verify] OUTPUT_DIR'
mode=export
if [ "$#" = 2 ] && [ "$1" = --verify ]; then mode=verify; shift; fi
test "$#" = 1 || { echo "$usage" >&2; exit 2; }
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd -P)
output=$1
if [ "$mode" = verify ]; then
  cd "$repo_root"
  python3 -c 'from pathlib import Path; from raveil.graph_device_axi4lite_export import verify; import sys; verify(Path(sys.argv[1]))' "$output"
  printf '%s\n' 'GraphDevice-AXI4LITE-RTL-EXPORT-VERIFY-V1 status=OK'
  exit
fi
parent=$(dirname -- "$output"); name=$(basename -- "$output")
test -d "$parent" || { echo 'error: output parent must already exist' >&2; exit 1; }
parent=$(CDPATH= cd -- "$parent" && pwd -P)
artifacts=$(CDPATH= cd -- "$repo_root/artifacts" && pwd -P)
case "$parent/$name" in "$artifacts"/*) ;; *) echo 'error: output must be below repository artifacts' >&2; exit 1;; esac
output=$parent/$name
test ! -e "$output" && test ! -L "$output" || { echo 'error: output already exists' >&2; exit 1; }
dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)" = "$dockerfile_sha256" || { echo 'error: required cached offline image is unavailable or mismatched' >&2; exit 1; }
image_id=$(docker image inspect --format '{{.Id}}' "$image")
staging=$(mktemp -d "$artifacts/graph-device-rtl-export.XXXXXX")
cleanup(){ rm -rf "$staging"; }
trap cleanup EXIT HUP INT TERM
cd "$repo_root"
python3 -c 'from pathlib import Path; from raveil.graph_device_axi4lite_export import prepare; import sys; prepare(Path(sys.argv[1]))' "$staging"
docker run --rm --network none --security-opt no-new-privileges=true --platform linux/amd64 \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" \
  --mount "type=bind,source=$staging,target=/bundle" \
  --workdir /repo/hardware/chisel "$image_id" ./export-graph-device-axi4lite-in-container.sh /bundle
python3 -c 'from pathlib import Path; from raveil.graph_device_axi4lite_export import finalize, publish, verify; import sys; staging=Path(sys.argv[1]); output=Path(sys.argv[3]); finalize(staging, sys.argv[2]); publish(staging, output); verify(output)' "$staging" "$image_id" "$output"
printf '%s\n' "GraphDevice-AXI4LITE-RTL-EXPORT-V1 status=OK path=${output#$repo_root/} top=GraphDeviceAxi4LiteTop absolute_base=unassigned board=unassigned evidence=rtl-export-functional-prerequisite performance=not-measured"
