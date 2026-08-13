#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_MODE=boom-store-authorization \
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedSmallBoomFateConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedSmallBoomFateConfig \
RAVEIL_OWNED_CPU_LABEL=boom \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-boom-store-authorization-build-v1 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
