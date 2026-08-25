#!/bin/sh
set -eu

evidence_root=${1:?evidence root is required}
case "$evidence_root" in /evidence) ;; *) echo 'error: evidence root must be /evidence' >&2; exit 2;; esac

rm -rf generated_static obj_graph_device_schedule .bsp .scala-build

scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala \
  chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion

verilator --assert --cc generated_static/*.sv \
  --exe graph_device_runtime.cpp graph_device_verilator.cpp \
  --build \
  --Mdir obj_graph_device_schedule \
  --top-module StaticStencilRegion \
  --CFLAGS '-std=c++17 -I/evidence'

sha256sum obj_graph_device_schedule/VStaticStencilRegion | awk '{print $1}' > "$evidence_root/simulator.sha256"
{
  scala-cli version
  java -version 2>&1
  verilator --version
} >> "$evidence_root/environment.txt"

./obj_graph_device_schedule/VStaticStencilRegion "$evidence_root" \
  "$evidence_root/transaction-trace.txt" \
  > "$evidence_root/device.log" \
  2> "$evidence_root/device.stderr"

test ! -s "$evidence_root/device.stderr"
