#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_MODE=debug-sba \
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedDebugSBASmallBoomConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedDebugSBASmallBoomConfig \
RAVEIL_OWNED_CPU_LABEL=boom \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-debug-sba-boom-sim-build-v1 \
    "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
