#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"

"$repo_root/hardware/chisel/fetch-boom-reference.sh"

# These are the public projects referenced by Chipyard 1.11.0's `chipyard`
# SBT project. Gitlink revisions in the pinned parent remain authority.
git -C "$chipyard" submodule update --init \
    generators/boom \
    generators/rocket-chip \
    generators/hardfloat \
    generators/testchipip \
    generators/hwacha \
    generators/rocket-chip-blocks \
    generators/rocket-chip-inclusive-cache \
    generators/sha3 \
    generators/gemmini \
    generators/icenet \
    generators/cva6 \
    generators/nvdla \
    generators/riscv-sodor \
    generators/ibex \
    generators/fft-generator \
    generators/constellation \
    generators/mempress \
    generators/bar-fetchers \
    generators/shuttle \
    generators/caliptra-aes-acc \
    generators/rocc-acc-utils \
    tools/barstools \
    tools/dsptools \
    tools/rocket-dsp-utils \
    tools/fixedpoint \
    tools/cde \
    sims/firesim

[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: Chipyard checkout or initialized dependency is not at its parent gitlink' >&2
    exit 1
}

printf 'BOOM-ELABORATION-DEPS-V1 status=OK parent=chipyard-1.11.0 dependency_scope=explicit-public-gitlinks recursive=0 performance=not-measured\n'
