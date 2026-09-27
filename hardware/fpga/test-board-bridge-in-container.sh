#!/usr/bin/env bash
# Called in the pinned cached image; /bundle and /src read-only, /out new and writable.
set -euo pipefail
if [[ ! -d /out || -n "$(ls -A /out)" ]]; then
  echo "output must be a new empty directory" >&2; exit 2
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
verilator --version > /out/toolchain.txt
for base in 00000000 a0000000 ffffc000; do
  verilator --assert --cc /bundle/core/generated-src/*.sv /bundle/graph_device_board_bridge.sv \
    --exe /src/board_bridge_test.cpp --build --Mdir "$work/obj-$base" \
    --top-module GraphDeviceBoardBridge "-GBASE_ADDR=32'h$base" \
    -CFLAGS "-DTEST_BASE=0x${base}U" > "/out/build-$base.log" 2>&1
  "$work/obj-$base/VGraphDeviceBoardBridge" > "/out/run-$base.log" 2>&1
  sha256sum "$work/obj-$base/VGraphDeviceBoardBridge" > "/out/binary-$base.sha256"
done
if verilator --lint-only /bundle/core/generated-src/*.sv /bundle/graph_device_board_bridge.sv \
    --top-module GraphDeviceBoardBridge "-GBASE_ADDR=32'h00000004" > /out/misaligned-base.log 2>&1; then
  echo 'misaligned base unexpectedly elaborated' >&2; exit 1
fi
# Failure must be the intended parameter guard, not an unrelated tool error.
grep -q RAVEIL_BASE_ADDR_MUST_BE_16K_ALIGNED /out/misaligned-base.log
sha256sum /src/board_bridge_test.cpp /src/test-board-bridge-in-container.sh /bundle/manifest.json > /out/input.sha256
printf '%s\n' 'status=OK evidence=rtl-simulation-functional board=unassigned performance=not-measured' > /out/result.txt
