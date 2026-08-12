#!/bin/sh
set -eu

rm -rf generated_static obj_static
scala-cli run StaticStencilRegion.scala --server=false --main-class EmitStaticStencilRegion
verilator --cc generated_static/StaticStencilRegion.sv \
  --exe static_stencil_sim_main.cpp \
  --build \
  --Mdir obj_static \
  --top-module StaticStencilRegion
./obj_static/VStaticStencilRegion
scala-cli version
java -version
verilator --version
