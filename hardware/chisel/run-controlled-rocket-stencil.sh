#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

RAVEIL_OWNED_CPU_CONFIG=RaveilMatchedRocketConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilMatchedRocketConfig \
RAVEIL_OWNED_CPU_LABEL=rocket \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-matched-rocket-controlled-v1 \
RAVEIL_OWNED_CPU_MODE=controlled \
  "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
