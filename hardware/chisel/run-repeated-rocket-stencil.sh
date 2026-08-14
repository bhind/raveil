#!/bin/sh
set -eu

export RAVEIL_OWNED_CPU_CONFIG=RaveilRepeatedMatchedRocketConfig
export RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilRepeatedMatchedRocketConfig
export RAVEIL_OWNED_CPU_LABEL=rocket
export RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-repeated-rocket-v1
export RAVEIL_OWNED_CPU_MODE=controlled-repeat
exec "$(dirname "$0")/run-owned-cpu-memory-smoke.sh"
