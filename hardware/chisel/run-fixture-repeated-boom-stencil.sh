#!/bin/sh
set -eu

export RAVEIL_OWNED_CPU_CONFIG=RaveilFixtureRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig
export RAVEIL_OWNED_CPU_LABEL=boom
export RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-fixture-repeated-boom-v1
export RAVEIL_OWNED_CPU_MODE=controlled-fixture-repeat
exec "$(dirname "$0")/run-owned-cpu-memory-smoke.sh"
