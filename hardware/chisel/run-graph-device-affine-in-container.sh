#!/bin/sh
set -eu

evidence_root=${1:?evidence root is required}
case "$evidence_root" in
  /evidence) ;;
  *) echo 'error: evidence root must be /evidence' >&2; exit 2;;
esac

rm -rf generated_static generated_static_repeat obj_graph_device_affine \
  .bsp .scala-build

scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala \
  chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion

find generated_static -type f -name '*.sv' -exec sha256sum {} \; \
  | awk '{print $1}' > /evidence/rtl-first.hashes

scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala \
  chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion \
  -- --target-dir generated_static_repeat

if [ ! -d generated_static_repeat ]; then
  mv generated_static generated_static_repeat
  scala-cli run OwnedFixedLatencyScratchpad.scala \
    chipyard-overlay/RaveilFixtureInputProvider.scala \
    chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
    --server=false --main-class EmitStaticStencilRegion
fi
find generated_static_repeat -type f -name '*.sv' -exec sha256sum {} \; \
  | awk '{print $1}' > /evidence/rtl-second.hashes
cmp /evidence/rtl-first.hashes /evidence/rtl-second.hashes
sha256sum /evidence/rtl-first.hashes | awk '{print $1}' \
  > /evidence/rtl-export.sha256

verilator --assert --cc generated_static/*.sv \
  --exe graph_device_runtime.cpp graph_device_affine_runtime.cpp \
  graph_device_verilator.cpp \
  --build \
  --Mdir obj_graph_device_affine \
  --top-module StaticStencilRegion \
  --CFLAGS '-std=c++17 -DRAVEIL_AFFINE_RUNTIME -I/evidence'

sha256sum obj_graph_device_affine/VStaticStencilRegion | awk '{print $1}' \
  > "$evidence_root/simulator.sha256"
{
  scala-cli version
  java -version 2>&1
  verilator --version
} >> "$evidence_root/environment.txt"

./obj_graph_device_affine/VStaticStencilRegion --affine "$evidence_root" \
  "$evidence_root/transaction-trace.txt" \
  > "$evidence_root/device.log" \
  2> "$evidence_root/device.stderr"

test ! -s "$evidence_root/device.stderr"
