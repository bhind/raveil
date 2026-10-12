#!/bin/sh
set -eu
# /runtime is the previously bound readonly build; no Scala/dependency rebuild.
mkdir -p /tmp/fold-reset
cd /tmp/fold-reset
cp /source/hardware/chisel/affine_fold_reset_probe.cpp .
cp /runtime/source/fold_config.h .
cp /runtime/rtl/*.sv .
cp affine_fold_reset_probe.cpp fold_config.h /evidence/
sha256sum /runtime/rtl/*.sv > /evidence/rtl.sha256
verilator --assert --cc ./*.sv --exe affine_fold_reset_probe.cpp --build \
  --Mdir obj_reset --top-module AffineFoldRegion --CFLAGS '-std=c++17 -I/tmp/fold-reset'
cp obj_reset/VAffineFoldRegion /evidence/reset-probe.bin
./obj_reset/VAffineFoldRegion > /evidence/device.log 2> /evidence/device.stderr
test ! -s /evidence/device.stderr
