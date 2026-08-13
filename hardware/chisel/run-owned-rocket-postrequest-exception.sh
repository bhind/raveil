#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedRocketConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedRocketConfig \
RAVEIL_OWNED_CPU_LABEL=rocket \
RAVEIL_OWNED_CPU_MODE=rocket-postrequest-exception \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-rocket-postrequest-exception-build-v1 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
