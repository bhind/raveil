#!/bin/sh
set -eu

rm -rf generated obj_dir
scala-cli run Counter.scala --server=false --main-class EmitCounter
verilator --cc generated/Counter.sv --exe sim_main.cpp --build --top-module Counter
./obj_dir/VCounter
scala-cli version
java -version
verilator --version
