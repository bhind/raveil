#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
build_volume=raveil-chipyard-rocket-sim-build-v1
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

# Revalidate the shared pinned Chipyard source and functional toolchain. This
# also reruns the BOOM control smokes; none of these executions is timed.
"$repo_root/hardware/chisel/run-boom-functional-smoke.sh"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$build_volume,target=/build" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
export PYTHONPATH=/repo
expected_chipyard='"$chipyard_revision"'
[ "$(cat /locked/raveil-lock-sha256)" = '"$lock_sha"' ]
if [ ! -d /build/chipyard/.git ]; then
  cp -a /source /build/chipyard
fi
[ "$(git -C /build/chipyard rev-parse HEAD)" = "$expected_chipyard" ]
[ -z "$(git -C /build/chipyard status --porcelain --untracked-files=no --ignore-submodules=untracked)" ]

cd /build/chipyard/sims/verilator
make -j2 CONFIG=RocketConfig CONFIG_PACKAGE=chipyard
sim=/build/chipyard/sims/verilator/simulator-chipyard.harness-RocketConfig
test -x "$sim"

riscv64-unknown-elf-gcc \
  -O2 -fno-strict-aliasing \
  -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
  -nostdlib -nostartfiles -static -Wl,--no-relax \
  -T /repo/hardware/chisel/boom_functional_smoke.ld \
  /repo/hardware/chisel/riscv_stencil_smoke.S \
  /repo/hardware/chisel/riscv_stencil_smoke.c \
  -o /build/rocket_stencil.elf
riscv64-unknown-elf-nm /build/rocket_stencil.elf | grep -q " D begin_signature$"
riscv64-unknown-elf-nm /build/rocket_stencil.elf | grep -q " D end_signature$"

"$sim" +signature=/tmp/rocket.signature +signature-granularity=4 \
  /build/rocket_stencil.elf
python3 -m raveil.riscv_stencil_signature --signature /tmp/rocket.signature
python3 -m raveil.simulation_adapter --implementation rocket-in-order \
  --invocation 3 --status completed

printf "ROCKET-STENCIL-FUNCTIONAL-V1 status=OK config=chipyard.RocketConfig outputs=256 oracle=independent-host memory_model=cache-backed-variable-latency resource_match_verified=0 matched_comparison_ready=0 adapter=v2 performance=not-measured\n"'
