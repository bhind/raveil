#!/bin/sh
set -eu
# Called only inside the pinned, network-disabled image, with /source read-only.
mkdir -p /tmp/fold-build
cd /tmp/fold-build
cp /source/hardware/chisel/AffineFoldRegion.scala .
cp /source/hardware/chisel/affine_fold_verilator.cpp .
cp /evidence/fold_config.h /evidence/fold_vectors.h .
scala-cli run AffineFoldRegion.scala --server=false --main-class EmitAffineFoldRegion
cp -R generated_fold /evidence/rtl
verilator --assert --cc generated_fold/*.sv --exe affine_fold_verilator.cpp \
  --build --Mdir obj_fold --top-module AffineFoldRegion \
  --CFLAGS '-std=c++17 -I/tmp/fold-build'
cp obj_fold/VAffineFoldRegion /evidence/simulator.bin
./obj_fold/VAffineFoldRegion /evidence/transactions.txt > /evidence/device.log 2> /evidence/device.stderr
test ! -s /evidence/device.stderr
scala-cli version > /evidence/toolchain.txt
java -version >> /evidence/toolchain.txt 2>&1
verilator --version >> /evidence/toolchain.txt
