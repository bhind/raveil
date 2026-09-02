#!/bin/sh
set -eu
reject=
if test "${1-}" = --reject; then
  test "$#" -ge 4 || { echo 'usage: ... [--reject REJECT_ROOT] REQUEST_ROOT [REQUEST_ROOT ...]' >&2; exit 2; }
  reject=$2
  shift 2
fi
test "$#" -ge 1 || { echo 'usage: ... [--reject REJECT_ROOT] REQUEST_ROOT [REQUEST_ROOT ...]' >&2; exit 2; }
first_evidence=$1
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build=/tmp/raveil-axi4lite-request
rm -rf "$build"
mkdir -p "$build/chipyard-overlay"
for f in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala GraphDeviceAxi4LiteTop.scala graph_device_runtime.h graph_device_runtime.cpp graph_device_affine_runtime.h graph_device_affine_runtime.cpp graph_device_dag_runtime.h graph_device_dag_runtime.cpp graph_device_axi4lite_transport.h graph_device_axi4lite_request_verilator.cpp; do
  cp "$src/$f" "$build/"
done
for f in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do
  cp "$src/chipyard-overlay/$f" "$build/chipyard-overlay/"
done
cp /repo/linux/include/raveil_graph_device_request.h "$build/"
cp /repo/linux/src/raveil_graph_device_request.cpp "$build/"
for f in graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do
  cp "$first_evidence/$f" "$build/"
done
for evidence do
  for f in graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do
    cmp "$first_evidence/$f" "$evidence/$f"
  done
done
cd "$build"
for f in hardware/chisel/GraphDeviceAxi4LiteTop.scala hardware/chisel/StaticStencilRegion.scala hardware/chisel/OwnedFixedLatencyScratchpad.scala hardware/chisel/GraphDeviceAffineConfigInstaller.scala hardware/chisel/GraphDeviceProgramInstaller.scala hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala hardware/chisel/graph_device_runtime.h hardware/chisel/graph_device_runtime.cpp hardware/chisel/graph_device_affine_runtime.h hardware/chisel/graph_device_affine_runtime.cpp hardware/chisel/graph_device_dag_runtime.h hardware/chisel/graph_device_dag_runtime.cpp hardware/chisel/graph_device_axi4lite_transport.h hardware/chisel/graph_device_axi4lite_request_verilator.cpp hardware/chisel/run-graph-device-axi4lite-request.sh hardware/chisel/run-graph-device-axi4lite-request-in-container.sh hardware/chisel/run-graph-device-axi4lite-runtime-demo.sh linux/include/raveil_graph_device_request.h linux/src/raveil_graph_device_request.cpp contracts/graph_device_axi4lite_aperture_v1.json raveil/graph_device_axi4lite.py raveil/graph_device_axi4lite_request.py raveil/graph_device_dag.py raveil/graph_device_affine.py raveil/graph_device_mvp.py raveil/graph_device_submit.py raveil/riscv_stencil_signature.py hardware/chisel/Dockerfile; do
  printf '%s ' "$f"
  sha256sum "/repo/$f" | awk '{print $1}'
done > /tmp/source-common.manifest
scala_sources='GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala'
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop > /tmp/emit-first.stdout 2> /tmp/emit-first.stderr
find generated_axi4lite -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do
  printf '%s ' "${f#generated_axi4lite/}"
  sha256sum "$f" | awk '{print $1}'
done > /tmp/rtl-first.manifest
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop -- --target-dir generated_axi4lite_repeat > /tmp/emit-second.stdout 2> /tmp/emit-second.stderr
find generated_axi4lite_repeat -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do
  printf '%s ' "${f#generated_axi4lite_repeat/}"
  sha256sum "$f" | awk '{print $1}'
done > /tmp/rtl-second.manifest
verilator --assert --cc generated_axi4lite/*.sv \
  --exe graph_device_runtime.cpp graph_device_affine_runtime.cpp \
  graph_device_dag_runtime.cpp raveil_graph_device_request.cpp \
  graph_device_axi4lite_request_verilator.cpp --build \
  --Mdir obj_graph_device_axi4lite_request \
  --top-module GraphDeviceAxi4LiteTop \
  > /tmp/verilator.stdout 2> /tmp/verilator.stderr
{ scala-cli version; java -version 2>&1; verilator --version; } > /tmp/toolchain.txt
if test -n "$reject"; then
  rm -f "$reject/axi-transcript.log"
  if ./obj_graph_device_axi4lite_request/VGraphDeviceAxi4LiteTop "$reject" > "$reject/device.log" 2> "$reject/device.stderr"; then
    echo 'error: malformed runtime request was accepted' >&2
    exit 1
  fi
  test ! -e "$reject/axi-transcript.log" || { echo 'error: rejected request produced AXI traffic' >&2; exit 1; }
fi
for evidence do
  cp /tmp/source-common.manifest /tmp/source.manifest
  for f in abi.sha256 graph_device_axi4lite_aperture_generated.h graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_uio_request_generated.h dag-artifact.json request.json request-input.bin request-oracle.bin uio-request.bin; do
    printf '%s ' "$f"
    sha256sum "$evidence/$f" | awk '{print $1}'
  done >> /tmp/source.manifest
  LC_ALL=C sort /tmp/source.manifest > "$evidence/source.manifest"
  cp /tmp/emit-first.stdout /tmp/emit-first.stderr "$evidence/"
  cp /tmp/emit-second.stdout /tmp/emit-second.stderr "$evidence/"
  cp /tmp/rtl-first.manifest "$evidence/rtl-first.manifest"
  cp /tmp/rtl-second.manifest "$evidence/rtl-second.manifest"
  cp -R generated_axi4lite "$evidence/rtl-first"
  cp -R generated_axi4lite_repeat "$evidence/rtl-second"
  cp /tmp/verilator.stdout /tmp/verilator.stderr "$evidence/"
  cp /tmp/toolchain.txt "$evidence/toolchain.txt"
  cp obj_graph_device_axi4lite_request/VGraphDeviceAxi4LiteTop "$evidence/simulator.bin"
  sha256sum "$evidence/simulator.bin" | awk '{print $1}' > "$evidence/simulator.sha256"
  ./obj_graph_device_axi4lite_request/VGraphDeviceAxi4LiteTop "$evidence" > "$evidence/device.log" 2> "$evidence/device.stderr"
done
