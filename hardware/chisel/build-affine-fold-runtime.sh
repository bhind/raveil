#!/bin/sh
set -eu
mkdir -p /tmp/fold-runtime
cd /tmp/fold-runtime
cp /source/hardware/chisel/AffineFoldRegion.scala .
cp /source/hardware/chisel/affine_fold_runtime.cpp .
cp /source/hardware/chisel/fold_config.h .
mkdir /evidence/source
cp AffineFoldRegion.scala affine_fold_runtime.cpp fold_config.h /evidence/source/
cp /source/hardware/chisel/build-affine-fold-runtime.sh /evidence/source/
scala-cli run AffineFoldRegion.scala --server=false --main-class EmitAffineFoldRegion
cp -R generated_fold /evidence/rtl
verilator --assert --cc generated_fold/*.sv --exe affine_fold_runtime.cpp \
  --build --Mdir obj_fold --top-module AffineFoldRegion --CFLAGS '-std=c++17 -I/tmp/fold-runtime'
cp obj_fold/VAffineFoldRegion /evidence/simulator.bin
scala-cli version > /evidence/toolchain.txt
java -version >> /evidence/toolchain.txt 2>&1
verilator --version >> /evidence/toolchain.txt
