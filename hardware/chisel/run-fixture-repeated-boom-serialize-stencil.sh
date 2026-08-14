#!/bin/sh
set -eu

export RAVEIL_OWNED_CPU_CONFIG=RaveilFixtureRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_LABEL=boom-serialize
export RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-fixture-repeated-boom-v1
export RAVEIL_OWNED_CPU_MODE=controlled-fixture-repeat
export RAVEIL_CONTROLLED_SERIALIZE_DISPATCH=1
exec "$(dirname "$0")/run-owned-cpu-memory-smoke.sh"
