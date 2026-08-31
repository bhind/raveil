#!/bin/sh
set -eu
test "$#" = 3 && test "$1" = /evidence || { echo 'usage: ... /evidence GRAPH_ID SEED' >&2; exit 2; }
evidence=$1; graph_id=$2; seed=$3
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); build=/tmp/raveil-axi4lite-request
rm -rf "$build"; mkdir -p "$build/chipyard-overlay"
for f in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala GraphDeviceAxi4LiteTop.scala graph_device_runtime.h graph_device_runtime.cpp graph_device_affine_runtime.h graph_device_affine_runtime.cpp graph_device_dag_runtime.h graph_device_dag_runtime.cpp graph_device_axi4lite_request_verilator.cpp; do cp "$src/$f" "$build/"; done
for f in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do cp "$src/chipyard-overlay/$f" "$build/chipyard-overlay/"; done
for f in graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h graph_device_axi4lite_aperture_generated.h; do cp "$evidence/$f" "$build/"; done
cd "$build"
for f in hardware/chisel/GraphDeviceAxi4LiteTop.scala hardware/chisel/StaticStencilRegion.scala hardware/chisel/OwnedFixedLatencyScratchpad.scala hardware/chisel/GraphDeviceAffineConfigInstaller.scala hardware/chisel/GraphDeviceProgramInstaller.scala hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala hardware/chisel/graph_device_runtime.h hardware/chisel/graph_device_runtime.cpp hardware/chisel/graph_device_affine_runtime.h hardware/chisel/graph_device_affine_runtime.cpp hardware/chisel/graph_device_dag_runtime.h hardware/chisel/graph_device_dag_runtime.cpp hardware/chisel/graph_device_axi4lite_request_verilator.cpp hardware/chisel/run-graph-device-axi4lite-request.sh hardware/chisel/run-graph-device-axi4lite-request-in-container.sh contracts/graph_device_axi4lite_aperture_v1.json raveil/graph_device_axi4lite.py raveil/graph_device_axi4lite_request.py raveil/graph_device_dag.py raveil/graph_device_affine.py raveil/graph_device_mvp.py raveil/graph_device_submit.py raveil/riscv_stencil_signature.py hardware/chisel/Dockerfile; do printf '%s ' "$f"; sha256sum "/repo/$f" | awk '{print $1}'; done > /tmp/source.manifest
for f in abi.sha256 graph_device_axi4lite_aperture_generated.h graph_device_abi_generated.h graph_device_affine_generated.h graph_device_dag_generated.h dag-artifact.json request.json request-input.bin request-oracle.bin; do printf '%s ' "$f"; sha256sum "$evidence/$f" | awk '{print $1}'; done >> /tmp/source.manifest
LC_ALL=C sort /tmp/source.manifest > "$evidence/source.manifest"
scala_sources='GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala'
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop > "$evidence/emit-first.stdout" 2> "$evidence/emit-first.stderr"
find generated_axi4lite -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do printf '%s ' "${f#generated_axi4lite/}"; sha256sum "$f" | awk '{print $1}'; done > "$evidence/rtl-first.manifest"
cp -R generated_axi4lite "$evidence/rtl-first"
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop -- --target-dir generated_axi4lite_repeat > "$evidence/emit-second.stdout" 2> "$evidence/emit-second.stderr"
find generated_axi4lite_repeat -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do printf '%s ' "${f#generated_axi4lite_repeat/}"; sha256sum "$f" | awk '{print $1}'; done > "$evidence/rtl-second.manifest"
cp -R generated_axi4lite_repeat "$evidence/rtl-second"
verilator --assert --cc generated_axi4lite/*.sv --exe graph_device_runtime.cpp graph_device_affine_runtime.cpp graph_device_dag_runtime.cpp graph_device_axi4lite_request_verilator.cpp --build --Mdir obj_graph_device_axi4lite_request --top-module GraphDeviceAxi4LiteTop > "$evidence/verilator.stdout" 2> "$evidence/verilator.stderr"
cp obj_graph_device_axi4lite_request/VGraphDeviceAxi4LiteTop "$evidence/simulator.bin"
sha256sum "$evidence/simulator.bin" | awk '{print $1}' > "$evidence/simulator.sha256"
{ scala-cli version; java -version 2>&1; verilator --version; } > "$evidence/toolchain.txt"
./obj_graph_device_axi4lite_request/VGraphDeviceAxi4LiteTop "$evidence" "$graph_id" "$seed" > "$evidence/device.log" 2> "$evidence/device.stderr"
