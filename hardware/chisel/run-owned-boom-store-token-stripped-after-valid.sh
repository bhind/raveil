#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
RAVEIL_OWNED_CPU_MODE=boom-store-token-stripped-after-valid \
RAVEIL_OWNED_CPU_CONFIG=RaveilOwnedSmallBoomTokenConfig \
RAVEIL_OWNED_CPU_CONFIG_FQ=chipyard.raveil.RaveilOwnedSmallBoomTokenConfig \
RAVEIL_OWNED_CPU_LABEL=boom \
RAVEIL_OWNED_CPU_BUILD_VOLUME=raveil-chipyard-owned-boom-store-token-stripped-after-valid-build-v2 \
    exec "$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
