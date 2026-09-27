#!/usr/bin/env bash
# Owned offline runner: /repo /bundle /inputs readonly, /out initially empty.
set -euo pipefail
if [[ $# != 1 || ! $1 =~ ^[0-9a-f]{8}$ || ! -d /out || -n "$(ls -A /out)" ]]; then
  echo 'expected validated base and empty output directory' >&2; exit 2
fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -R /inputs/matrix /inputs/recovery /out/
verilator --version > /out/toolchain.txt
verilator --assert --cc /bundle/core/generated-src/*.sv /bundle/graph_device_board_bridge.sv \
  --exe /repo/hardware/fpga/board_execute_test.cpp \
  /repo/hardware/chisel/graph_device_runtime.cpp \
  /repo/hardware/chisel/graph_device_affine_runtime.cpp \
  /repo/hardware/chisel/graph_device_dag_runtime.cpp \
  --build --Mdir "$work/obj" --top-module GraphDeviceBoardBridge \
  "-GBASE_ADDR=32'h$1" -CFLAGS "-std=c++17 -DTEST_BASE=0x${1}U -I/inputs/matrix -I/repo/hardware/chisel" \
  > /out/build.log 2>&1
cp "$work/obj/VGraphDeviceBoardBridge" /out/simulator.bin
sha256sum /out/simulator.bin > /out/simulator.sha256
/out/simulator.bin /out > /out/device.log 2> /out/device.stderr
