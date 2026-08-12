#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedRocketConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedRocketConfig \
RAVEIL_OWNED_CPU_LABEL=rocket \
RAVEIL_OWNED_CPU_MODE=rocket-request-retire \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-rocket-request-retire-build-v1 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
