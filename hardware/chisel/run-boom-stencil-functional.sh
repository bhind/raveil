#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=$("$repo_root/hardware/chisel/verify-boom-functional-sim-image.sh")
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
build_volume=raveil-chipyard-boom-sim-build-v1

# Revalidate source/toolchain/simulator and both minimal control modes first.
"$repo_root/hardware/chisel/run-boom-functional-smoke.sh"

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$build_volume,target=/build" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export PYTHONPATH=/repo
sim=/build/chipyard/sims/verilator/simulator-chipyard.harness-SmallBoomConfig
test -x "$sim"

compile_stencil() {
  mode=$1
  define=$2
  riscv64-unknown-elf-gcc \
    $define -O2 -fno-strict-aliasing \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/riscv_stencil_smoke.S \
    /repo/hardware/chisel/riscv_stencil_smoke.c \
    -o "/build/${mode}.elf"
  riscv64-unknown-elf-nm "/build/${mode}.elf" | grep -q " D begin_signature$"
  riscv64-unknown-elf-nm "/build/${mode}.elf" | grep -q " D end_signature$"
}

compile_stencil boom_ooo_stencil ""
"$sim" +signature=/tmp/boom_ooo.signature +signature-granularity=4 \
  /build/boom_ooo_stencil.elf
python3 -m raveil.riscv_stencil_signature --signature /tmp/boom_ooo.signature
python3 -m raveil.simulation_adapter --implementation boom-ooo \
  --invocation 1 --status completed

compile_stencil boom_serialize_dispatch_stencil -DBOOM_SERIALIZE_DISPATCH=1
riscv64-unknown-elf-objdump -d /build/boom_serialize_dispatch_stencil.elf | \
  grep -q "0x7c1"
"$sim" +signature=/tmp/boom_serialize_dispatch.signature \
  +signature-granularity=4 /build/boom_serialize_dispatch_stencil.elf
python3 -m raveil.riscv_stencil_signature \
  --signature /tmp/boom_serialize_dispatch.signature
python3 -m raveil.simulation_adapter \
  --implementation boom-ooo-disabled-diagnostic \
  --invocation 2 --status completed

printf "BOOM-STENCIL-FUNCTIONAL-V1 status=OK modes=boom-ooo,boom-ooo-disabled-diagnostic outputs_per_mode=256 oracle=independent-host memory_model=cache-backed-variable-latency resource_match_verified=0 matched_comparison_ready=0 adapter=v2 performance=not-measured\n"'
