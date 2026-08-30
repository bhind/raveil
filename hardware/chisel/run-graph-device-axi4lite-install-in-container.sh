#!/bin/sh
set -eu
test "$#" = 1 || { echo 'usage: ... /evidence' >&2; exit 2; }
test "$1" = /evidence || { echo 'error: evidence root must be /evidence' >&2; exit 2; }
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd); build=/tmp/raveil-axi4lite-install
rm -rf "$build"; mkdir -p "$build/chipyard-overlay"
for f in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala GraphDeviceAxi4LiteTop.scala graph_device_axi4lite_install_verilator.cpp; do cp "$src/$f" "$build/"; done
for f in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do cp "$src/chipyard-overlay/$f" "$build/chipyard-overlay/"; done
for f in graph_device_axi4lite_aperture_generated.h graph_device_affine_generated.h graph_device_dag_generated.h; do cp "/evidence/$f" "$build/"; done
cd "$build"
for f in \
  hardware/chisel/GraphDeviceAxi4LiteTop.scala \
  hardware/chisel/StaticStencilRegion.scala \
  hardware/chisel/OwnedFixedLatencyScratchpad.scala \
  hardware/chisel/GraphDeviceAffineConfigInstaller.scala \
  hardware/chisel/GraphDeviceProgramInstaller.scala \
  hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala \
  hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala \
  hardware/chisel/graph_device_axi4lite_install_verilator.cpp \
  contracts/graph_device_axi4lite_aperture_v1.json \
  raveil/graph_device_axi4lite.py \
  raveil/graph_device_axi4lite_install.py \
  raveil/graph_device_affine.py \
  raveil/graph_device_dag.py \
  hardware/chisel/run-graph-device-axi4lite-install.sh \
  hardware/chisel/run-graph-device-axi4lite-install-in-container.sh \
  hardware/chisel/Dockerfile; do
  printf '%s ' "$f"; sha256sum "/repo/$f" | awk '{print $1}'
done > /tmp/source.manifest
for f in abi.sha256 graph_device_affine_generated.h graph_device_axi4lite_aperture_generated.h graph_device_dag_generated.h; do
  printf '%s ' "$f"; sha256sum "/evidence/$f" | awk '{print $1}'
done >> /tmp/source.manifest
LC_ALL=C sort /tmp/source.manifest > /evidence/source.manifest
scala_sources='GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala'
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop > /evidence/emit-first.stdout 2> /evidence/emit-first.stderr
find generated_axi4lite -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do printf '%s ' "${f#generated_axi4lite/}"; sha256sum "$f" | awk '{print $1}'; done > /evidence/rtl-first.manifest
cp -R generated_axi4lite /evidence/rtl-first
scala-cli run $scala_sources --server=false --main-class EmitGraphDeviceAxi4LiteTop -- --target-dir generated_axi4lite_repeat > /evidence/emit-second.stdout 2> /evidence/emit-second.stderr
find generated_axi4lite_repeat -type f -name '*.sv' -print | LC_ALL=C sort | while read -r f; do printf '%s ' "${f#generated_axi4lite_repeat/}"; sha256sum "$f" | awk '{print $1}'; done > /evidence/rtl-second.manifest
cp -R generated_axi4lite_repeat /evidence/rtl-second
verilator --assert --cc generated_axi4lite/*.sv --exe graph_device_axi4lite_install_verilator.cpp --build --Mdir obj_graph_device_axi4lite_install --top-module GraphDeviceAxi4LiteTop > /evidence/verilator.stdout 2> /evidence/verilator.stderr
cp obj_graph_device_axi4lite_install/VGraphDeviceAxi4LiteTop /evidence/simulator.bin
sha256sum obj_graph_device_axi4lite_install/VGraphDeviceAxi4LiteTop | awk '{print $1}' > /evidence/simulator.sha256
{ scala-cli version; java -version 2>&1; verilator --version; } > /evidence/toolchain.txt
./obj_graph_device_axi4lite_install/VGraphDeviceAxi4LiteTop > /evidence/device.log 2> /evidence/device.stderr
