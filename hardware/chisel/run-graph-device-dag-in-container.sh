#!/bin/sh
set -eu

if [ "$#" -ne 1 ] && [ "$#" -ne 3 ]; then
  echo 'usage: run-graph-device-dag-in-container.sh /evidence [GRAPH_ID SEED]' >&2
  exit 2
fi
evidence_root=$1
graph_id=${2:-}
seed=${3:-}
source_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_root=/tmp/raveil-graph-device-dag-build
case "$evidence_root" in
  /evidence) ;;
  *) echo 'error: evidence root must be /evidence' >&2; exit 2;;
esac

rm -rf "$build_root"
mkdir -p "$build_root/chipyard-overlay"
for source in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala \
  GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala \
  graph_device_runtime.cpp graph_device_runtime.h graph_device_affine_runtime.cpp \
  graph_device_affine_runtime.h graph_device_dag_runtime.cpp graph_device_dag_runtime.h \
  graph_device_verilator.cpp; do cp "$source_root/$source" "$build_root/"; done
for source in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do
  cp "$source_root/chipyard-overlay/$source" "$build_root/chipyard-overlay/"; done
cd "$build_root"
if [ -n "$graph_id" ]; then
  invalid_cache_entry=$(find /root/.cache \( -type l -o \( ! -type d -a ! -type f \) \) -print -quit)
  if [ -n "$invalid_cache_entry" ]; then
    echo 'error: dependency cache contains a symbolic link or non-regular entry' >&2
    exit 2
  fi
  find /root/.cache -type f -print | LC_ALL=C sort | while read -r file; do
    rel=${file#/root/.cache/}; size=$(wc -c < "$file" | tr -d ' '); hash=$(sha256sum "$file" | awk '{print $1}');
    printf '%s %s %s\n' "$rel" "$size" "$hash";
  done > /evidence/dependency-cache.manifest
fi

scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala \
  chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion

find generated_static -type f -name '*.sv' -exec sha256sum {} \; \
  | awk '{print $1}' > /evidence/rtl-first.hashes
find generated_static -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do
  rel=${file#generated_static/}; size=$(wc -c < "$file" | tr -d ' '); hash=$(sha256sum "$file" | awk '{print $1}');
  printf '%s %s %s\n' "$rel" "$size" "$hash";
done > /evidence/rtl-first.manifest

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
find generated_static_repeat -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do
  rel=${file#generated_static_repeat/}; size=$(wc -c < "$file" | tr -d ' '); hash=$(sha256sum "$file" | awk '{print $1}');
  printf '%s %s %s\n' "$rel" "$size" "$hash";
done > /evidence/rtl-second.manifest
cmp /evidence/rtl-first.hashes /evidence/rtl-second.hashes
sha256sum /evidence/rtl-first.hashes | awk '{print $1}' \
  > /evidence/rtl-export.sha256

verilator --assert --cc generated_static/*.sv \
  --exe graph_device_runtime.cpp graph_device_affine_runtime.cpp \
  graph_device_dag_runtime.cpp graph_device_verilator.cpp \
  --build \
  --Mdir obj_graph_device_dag \
  --top-module StaticStencilRegion \
  --CFLAGS '-std=c++17 -DRAVEIL_DAG_RUNTIME -I/evidence'

if [ -n "$graph_id" ]; then
  cp obj_graph_device_dag/VStaticStencilRegion "$evidence_root/simulator.bin"
  sha256sum "$evidence_root/simulator.bin" | awk '{print $1}' > "$evidence_root/simulator.sha256"
else
  sha256sum obj_graph_device_dag/VStaticStencilRegion | awk '{print $1}' > "$evidence_root/simulator.sha256"
fi
if [ -n "$graph_id" ]; then
  toolchain=$evidence_root/toolchain.txt
else
  toolchain=$evidence_root/environment.txt
fi
{
  scala-cli version
  java -version 2>&1
  verilator --version
} >> "$toolchain"
sha256sum "$toolchain" | awk '{print $1}' > "$evidence_root/toolchain.sha256"

if [ -n "$graph_id" ] && [ -n "$seed" ]; then
  set -- --dag-selected "$evidence_root" "$graph_id" "$seed" \
    "$evidence_root/transaction-trace.txt"
else
  set -- --dag "$evidence_root" "$evidence_root/transaction-trace.txt"
fi
./obj_graph_device_dag/VStaticStencilRegion "$@" \
  > "$evidence_root/device.log" \
  2> "$evidence_root/device.stderr"

test ! -s "$evidence_root/device.stderr"
