#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedRocketFateConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedRocketFateConfig \
RAVEIL_OWNED_CPU_LABEL=rocket \
RAVEIL_OWNED_CPU_MODE=rocket-redirect-dcache-fate \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-rocket-redirect-dcache-fate-build-v1 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
