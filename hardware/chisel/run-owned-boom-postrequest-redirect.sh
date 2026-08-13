#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_MODE=boom-postrequest-redirect \
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedSmallBoomConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedSmallBoomConfig \
RAVEIL_OWNED_CPU_LABEL=boom \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-boom-postrequest-redirect-build-v1 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
