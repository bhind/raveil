#!/bin/sh
set -eu

: "${RAVEIL_TOOLCHAIN_SHA256:?Graph toolchain identity is required}"

rm -rf generated_static obj_static
scala-cli run OwnedFixedLatencyScratchpad.scala \
  chipyard-overlay/RaveilFixtureInputProvider.scala \
  chipyard-overlay/RaveilStaticStencilCore.scala StaticStencilRegion.scala \
  --server=false --main-class EmitStaticStencilRegion
verilator --assert --cc generated_static/*.sv \
  --exe static_stencil_sim_main.cpp \
  --build \
  --Mdir obj_static \
  --top-module StaticStencilRegion
artifact_sha256=$(sha256sum obj_static/VStaticStencilRegion | awk '{print $1}')
printf 'CONTROLLED-GRAPH-IDENTITY-V1 artifact_sha256=%s toolchain_sha256=%s\n' \
  "$artifact_sha256" "$RAVEIL_TOOLCHAIN_SHA256"
if [ -n "${RAVEIL_FIXTURE_REPEAT_ACCOUNT:-}" ]; then
  ./obj_static/VStaticStencilRegion \
    "--fixture-repeat-account=$RAVEIL_FIXTURE_REPEAT_ACCOUNT"
elif [ -n "${RAVEIL_REPEAT_ACCOUNT:-}" ]; then
  ./obj_static/VStaticStencilRegion "--repeat-account=$RAVEIL_REPEAT_ACCOUNT"
elif [ -n "${RAVEIL_PILOT_SEED:-}" ]; then
  ./obj_static/VStaticStencilRegion "--pilot-seed=$RAVEIL_PILOT_SEED"
else
  ./obj_static/VStaticStencilRegion
fi
scala-cli version
java -version
verilator --version
