#!/bin/sh
set -eu

export RAVEIL_OWNED_CPU_CONFIG=RaveilRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_LABEL=boom
export RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-repeated-boom-v1
export RAVEIL_OWNED_CPU_MODE=controlled-repeat
export RAVEIL_CONTROLLED_SERIALIZE_DISPATCH=0
exec "$(dirname "$0")/run-owned-cpu-memory-smoke.sh"
