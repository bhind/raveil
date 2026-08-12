#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"

"$repo_root/hardware/chisel/fetch-boom-elaboration-deps.sh"

# These additional public parent gitlinks are required only for the functional
# Verilator simulator toolchain. No recursive or optional/private setup occurs.
git -C "$chipyard" submodule update --init \
    toolchains/riscv-tools/riscv-isa-sim \
    tools/DRAMSim2 \
    tools/install-circt

[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: simulator dependency is not at its parent gitlink' >&2
    exit 1
}

printf 'BOOM-SIM-DEPS-V1 status=OK dependency_scope=explicit-public-gitlinks recursive=0 performance=not-measured\n'
