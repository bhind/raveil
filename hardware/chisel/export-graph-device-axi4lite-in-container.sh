#!/bin/sh
set -eu
test "$#" = 1 && test "$1" = /bundle || { echo 'usage: ... /bundle' >&2; exit 2; }
src=/repo/hardware/chisel
build=/tmp/raveil-graph-device-rtl-export
rm -rf "$build"
mkdir -p "$build/chipyard-overlay"
for file in OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala GraphDeviceAxi4LiteTop.scala; do
  cp "$src/$file" "$build/"
done
for file in RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala; do
  cp "$src/chipyard-overlay/$file" "$build/chipyard-overlay/"
done
cd "$build"
sources='GraphDeviceAxi4LiteTop.scala StaticStencilRegion.scala OwnedFixedLatencyScratchpad.scala GraphDeviceAffineConfigInstaller.scala GraphDeviceProgramInstaller.scala chipyard-overlay/RaveilFixtureInputProvider.scala chipyard-overlay/RaveilStaticStencilCore.scala'
scala-cli run $sources --server=false --main-class EmitGraphDeviceAxi4LiteTop -- --target-dir generated-src
scala-cli run $sources --server=false --main-class EmitGraphDeviceAxi4LiteTop -- --target-dir generated-repeat
find generated-src -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do printf '%s ' "${file#generated-src/}"; sha256sum "$file" | awk '{print $1}'; done > /bundle/rtl.manifest
find generated-repeat -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do printf '%s ' "${file#generated-repeat/}"; sha256sum "$file" | awk '{print $1}'; done > /bundle/rtl-repeat.manifest
cmp /bundle/rtl.manifest /bundle/rtl-repeat.manifest
mkdir /bundle/generated-src
find generated-src -type f -name '*.sv' -print | LC_ALL=C sort | while read -r file; do
  relative=${file#generated-src/}
  mkdir -p "/bundle/generated-src/$(dirname -- "$relative")"
  cp "$file" "/bundle/generated-src/$relative"
done
{ scala-cli version; java -version 2>&1; } > /bundle/toolchain.txt
