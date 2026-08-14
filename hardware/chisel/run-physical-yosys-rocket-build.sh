#!/bin/sh
set -eu

export RAVEIL_OWNED_CPU_CONFIG=RaveilFixtureRepeatedMatchedRocketConfig
export RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig
export RAVEIL_OWNED_CPU_LABEL=rocket
export RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-physical-yosys-rocket-v1
export RAVEIL_OWNED_CPU_MODE=controlled-fixture-repeat
export RAVEIL_PHYSICAL_YOSYS_FLOW=1
export RAVEIL_BUILD_ONLY=1
exec "$(dirname "$0")/run-owned-cpu-memory-smoke.sh"
