#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
graph_log=$(mktemp "${TMPDIR:-/tmp}/raveil-controlled-graph.XXXXXX")
rocket_log=$(mktemp "${TMPDIR:-/tmp}/raveil-controlled-rocket.XXXXXX")
boom_log=$(mktemp "${TMPDIR:-/tmp}/raveil-controlled-boom.XXXXXX")
trap 'rm -f "$graph_log" "$rocket_log" "$boom_log"' EXIT HUP INT TERM

run_and_replay() {
    output=$1
    shift
    if "$@" >"$output" 2>&1; then
        sed -n '1,240p' "$output"
    else
        sed -n '1,240p' "$output"
        return 1
    fi
}

run_and_replay "$graph_log" \
    "$repo_root/hardware/chisel/run-static-stencil-rtl.sh"
run_and_replay "$rocket_log" \
    "$repo_root/hardware/chisel/run-controlled-rocket-stencil.sh"
run_and_replay "$boom_log" \
    "$repo_root/hardware/chisel/run-controlled-boom-stencil.sh"

cd "$repo_root"
python3 -m raveil.controlled_run \
    --aggregate-logs "$graph_log" "$rocket_log" "$boom_log"
