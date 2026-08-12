#!/bin/sh
set -eu

rm -rf generated_static obj_static
scala-cli run OwnedFixedLatencyScratchpad.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion
verilator --assert --cc generated_static/*.sv \
  --exe static_stencil_sim_main.cpp \
  --build \
  --Mdir obj_static \
  --top-module StaticStencilRegion
./obj_static/VStaticStencilRegion
scala-cli version
java -version
verilator --version
