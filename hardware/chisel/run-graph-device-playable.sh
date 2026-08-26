#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
log=$(mktemp)
trap 'rm -f "$log"' EXIT HUP INT TERM

cd "$repo_root"
if ! ./hardware/chisel/run-graph-device-dag.sh >"$log" 2>&1; then
  cat "$log" >&2
  exit 1
fi

marker_count=$(awk '/^GraphDevice-DAG-EVIDENCE-V1 / { count++ } END { print count+0 }' "$log")
if [ "$marker_count" -ne 1 ]; then
  echo 'error: expected exactly one Graph-device evidence marker' >&2
  exit 1
fi
marker=$(awk '/^GraphDevice-DAG-EVIDENCE-V1 / { print; exit }' "$log")
if ! relative_path=$(python3 -m raveil.graph_device_playable marker "$marker"); then
  exit 1
fi
evidence="$repo_root/$relative_path"
if [ ! -d "$evidence" ]; then
  echo 'error: evidence directory is missing' >&2
  exit 1
fi
python3 -m raveil.graph_device_playable show "$relative_path"
