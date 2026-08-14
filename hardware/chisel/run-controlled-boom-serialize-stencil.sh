#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

RAVEIL_OWNED_CPU_CONFIG=RaveilMatchedSmallBoomConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilMatchedSmallBoomConfig \
RAVEIL_OWNED_CPU_LABEL=boom-serialize \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-matched-boom-controlled-v1 \
RAVEIL_OWNED_CPU_MODE=controlled \
RAVEIL_CONTROLLED_SERIALIZE_DISPATCH=1 \
  "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
