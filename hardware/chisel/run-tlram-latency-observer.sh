#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
boom_build_volume=raveil-chipyard-boom-sim-build-v1
rocket_build_volume=raveil-chipyard-rocket-sim-build-v1
observer_source=/repo/hardware/chisel/tlram_endpoint_latency_observer.sv
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$boom_build_volume,target=/boom" \
    --mount "type=volume,source=$rocket_build_volume,target=/rocket" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
export PYTHONPATH=/repo
observer_source='"$observer_source"'
expected_lock_sha='"$lock_sha"'
expected_chipyard='"$chipyard_revision"'
rocket_root=/rocket/chipyard/sims/verilator
boom_root=/boom/chipyard/sims/verilator
rocket_model=/rocket/tlram-latency-observer/RocketConfig
boom_model=/boom/tlram-latency-observer/SmallBoomConfig
rocket_sim=/rocket/tlram-latency-observer/simulator-chipyard.harness-RocketConfig-observer
boom_sim=/boom/tlram-latency-observer/simulator-chipyard.harness-SmallBoomConfig-observer

[ "$(cat /locked/raveil-lock-sha256)" = "$expected_lock_sha" ]
[ "$(git -C /rocket/chipyard rev-parse HEAD)" = "$expected_chipyard" ]
[ "$(git -C /boom/chipyard rev-parse HEAD)" = "$expected_chipyard" ]
[ -z "$(git -C /rocket/chipyard status --porcelain --untracked-files=no --ignore-submodules=untracked)" ]
[ -z "$(git -C /boom/chipyard status --porcelain --untracked-files=no --ignore-submodules=untracked)" ]
verilator --version
riscv64-unknown-elf-gcc --version | sed -n "1p"

# The generated file lists retain the original /build mount locator.  Recreate
# that locator only inside this disposable container while compiling each
# volume; the validated normal simulator artifacts remain untouched.
ln -s /rocket /build
make -C "$rocket_root" -j4 \
  CONFIG=RocketConfig CONFIG_PACKAGE=chipyard \
  model_dir="$rocket_model" sim="$rocket_sim" \
  EXTRA_SIM_SOURCES="$observer_source" EXTRA_SIM_REQS="$observer_source"
unlink /build
ln -s /boom /build
make -C "$boom_root" -j4 \
  CONFIG=SmallBoomConfig CONFIG_PACKAGE=chipyard \
  model_dir="$boom_model" sim="$boom_sim" \
  EXTRA_SIM_SOURCES="$observer_source" EXTRA_SIM_REQS="$observer_source"

compile_stencil() {
  mode=$1
  define=$2
  riscv64-unknown-elf-gcc \
    -DRFC0005_SYSTEM_SCRATCHPAD=1 $define -O2 -fno-strict-aliasing \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/riscv_stencil_system_scratchpad.ld \
    /repo/hardware/chisel/riscv_stencil_smoke.S \
    /repo/hardware/chisel/riscv_stencil_smoke.c \
    -o "/tmp/${mode}.elf"
  riscv64-unknown-elf-readelf -SW "/tmp/${mode}.elf" | \
    grep -q ".scratchpad_signature"
  riscv64-unknown-elf-nm "/tmp/${mode}.elf" | \
    grep -q "08000000 B input_words$"
  riscv64-unknown-elf-nm "/tmp/${mode}.elf" | \
    grep -q "08000510 D begin_signature$"
}

run_and_validate() {
  sim=$1
  mode=$2
  implementation=$3
  "$sim" +signature="/tmp/${mode}.signature" +signature-granularity=4 \
    "/tmp/${mode}.elf" | tee "/tmp/${mode}.observer.log"
  python3 -m raveil.riscv_stencil_signature \
    --signature "/tmp/${mode}.signature"
  python3 -m raveil.tlram_latency_observer \
    --log "/tmp/${mode}.observer.log" --implementation "$implementation"
}

compile_stencil rocket_tlram_observer ""
run_and_validate "$rocket_sim" rocket_tlram_observer rocket-in-order

compile_stencil boom_tlram_observer ""
run_and_validate "$boom_sim" boom_tlram_observer boom-ooo

compile_stencil boom_diagnostic_tlram_observer -DBOOM_SERIALIZE_DISPATCH=1
riscv64-unknown-elf-objdump -d /tmp/boom_diagnostic_tlram_observer.elf | \
  grep -q "0x7c1"
run_and_validate "$boom_sim" boom_diagnostic_tlram_observer \
  boom-ooo-disabled-diagnostic

printf "TLRAM-LATENCY-OBSERVER-FUNCTIONAL-V1 status=OK implementations=rocket-in-order,boom-ooo,boom-ooo-disabled-diagnostic boundary=tlram-single-beat-tilelink-request-to-response evidence=rtl-simulation-functional-diagnostic performance=not-measured fixed_latency_claim=0 resource_match_verified=0 matched_comparison_ready=0\n"'
