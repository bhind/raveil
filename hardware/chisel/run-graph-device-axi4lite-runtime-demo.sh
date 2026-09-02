#!/bin/sh
set -eu
test "$#" = 0 || { echo 'usage: run-graph-device-axi4lite-runtime-demo.sh' >&2; exit 2; }
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
artifact_parent=$repo_root/artifacts/graph_device_axi4lite_runtime_demo
mkdir -p "$artifact_parent"
session=$(mktemp -d "$artifact_parent/run.XXXXXX")
trap 'rm -rf "$repo_root/hardware/chisel/generated_axi4lite_request" "$repo_root/hardware/chisel/generated_axi4lite_request_repeat" "$repo_root/hardware/chisel/obj_graph_device_axi4lite_request"' EXIT HUP INT TERM
command -v docker >/dev/null 2>&1 || { echo 'error: docker is required' >&2; exit 1; }
dockerfile_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/Dockerfile" | awk '{print $1}')
image="raveil-graph-device-dag:sha256-${dockerfile_sha256}"
expected_image_id=sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c
test "$(docker image inspect --format '{{index .Config.Labels "raveil.dockerfile.sha256"}}' "$image" 2>/dev/null || true)" = "$dockerfile_sha256" || { echo 'error: required cached offline image is unavailable; refusing network build' >&2; exit 1; }
image_id=$(docker image inspect --format '{{.Id}}' "$image")
test "$image_id" = "$expected_image_id" || { echo 'error: cached image ID differs from reviewed immutable image' >&2; exit 1; }

first=$session/five-point-seed-1
second=$session/vertical-three-point-seed-4294967295
rejected=$session/rejected-request
mkdir "$first" "$second" "$rejected"
cd "$repo_root"
python3 -m raveil.graph_device_axi4lite_request prepare --output "$first" --graph contracts/graph_device_dags/five-point.json --seed 1 >/dev/null
python3 -m raveil.graph_device_axi4lite_request prepare --output "$second" --graph contracts/graph_device_dags/vertical-three-point.json --seed 4294967295 >/dev/null
cp -R "$first/." "$rejected/"
python3 - "$rejected/uio-request.bin" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
payload = bytearray(path.read_bytes())
payload[0] ^= 0xff
path.write_bytes(payload)
PY
for evidence in "$first" "$second"; do
  printf 'schema=raveil.graph-device-axi4lite-request-environment/v1\nplatform=linux/amd64\nimage_id=%s\n' "$image_id" > "$evidence/environment.txt"
done
docker run --rm --network none --security-opt no-new-privileges=true --platform linux/amd64 \
  --mount type=volume,source=raveil-chisel-scala-cache-v1,target=/root/.cache,readonly \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" \
  --mount "type=bind,source=$session,target=/session" \
  --workdir /repo/hardware/chisel "$image_id" \
  ./run-graph-device-axi4lite-request-in-container.sh \
  --reject /session/rejected-request /session/five-point-seed-1 \
  /session/vertical-three-point-seed-4294967295 \
  > "$session/container.stdout" 2> "$session/container.stderr"
for evidence in "$first" "$second"; do
  : > "$evidence/container.stdout"
  : > "$evidence/container.stderr"
  python3 -m raveil.graph_device_axi4lite_request finalize --evidence "$evidence" >/dev/null
  python3 -m raveil.graph_device_axi4lite_request verify --evidence "$evidence" >/dev/null
done
first_sha=$(awk '{print $1}' "$first/simulator.sha256")
second_sha=$(awk '{print $1}' "$second/simulator.sha256")
test "$first_sha" = "$second_sha" || { echo 'error: requests used different simulator binaries' >&2; exit 1; }
printf 'GraphDevice-AXI4LITE-RUNTIME-DEMO-V1 status=PASS requests=2 same_simulator=1 rejected_before_axi=1 simulator_sha256=%s path=artifacts/graph_device_axi4lite_runtime_demo/%s private=1 publication=0 evidence=rtl-simulation-functional performance=not-measured\n' "$first_sha" "$(basename "$session")"
