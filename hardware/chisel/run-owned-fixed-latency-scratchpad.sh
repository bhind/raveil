#!/bin/sh
set -eu

rm -rf generated_owned_memory obj_owned_memory
scala-cli run OwnedFixedLatencyScratchpad.scala --server=false \
    --main-class EmitOwnedFixedLatencyScratchpad
verilator --assert --cc generated_owned_memory/OwnedFixedLatencyScratchpad.sv \
    --exe owned_fixed_latency_scratchpad_sim_main.cpp \
    --build \
    --Mdir obj_owned_memory \
    --top-module OwnedFixedLatencyScratchpad
./obj_owned_memory/VOwnedFixedLatencyScratchpad
scala-cli version
java -version
verilator --version
