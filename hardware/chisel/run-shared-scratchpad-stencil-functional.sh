#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
boom_build_volume=raveil-chipyard-boom-sim-build-v1
rocket_build_volume=raveil-chipyard-rocket-sim-build-v1
memory_model=shared-tilelink-banked-scratchpad-unverified-latency

# Revalidate both pinned CPU controls and the common semantic workload first.
"$repo_root/hardware/chisel/run-boom-stencil-functional.sh"
"$repo_root/hardware/chisel/run-rocket-stencil-functional.sh"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$boom_build_volume,target=/boom" \
    --mount "type=volume,source=$rocket_build_volume,target=/rocket" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export PYTHONPATH=/repo
abstract_config=/repo/external/chipyard/generators/chipyard/src/main/scala/config/AbstractConfig.scala
scratchpad_config=/repo/external/chipyard/generators/testchipip/src/main/scala/soc/Configs.scala
boom_sim=/boom/chipyard/sims/verilator/simulator-chipyard.harness-SmallBoomConfig
rocket_sim=/rocket/chipyard/sims/verilator/simulator-chipyard.harness-RocketConfig
test -x "$boom_sim"
test -x "$rocket_sim"
grep -q "WithMbusScratchpad(base = 0x08000000" "$abstract_config"
grep -q "size = 64 \* 1024" "$abstract_config"
grep -q "banks: Int = 1" "$scratchpad_config"
grep -q "partitions: Int = 1" "$scratchpad_config"
grep -q "subBanks: Int = 1" "$scratchpad_config"

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
  invocation=$4
  "$sim" +signature="/tmp/${mode}.signature" +signature-granularity=4 \
    "/tmp/${mode}.elf"
  python3 -m raveil.riscv_stencil_signature \
    --signature "/tmp/${mode}.signature"
  python3 -m raveil.simulation_adapter --implementation "$implementation" \
    --memory-model '"$memory_model"' --invocation "$invocation" \
    --status completed
}

compile_stencil rocket_shared_scratchpad ""
run_and_validate "$rocket_sim" rocket_shared_scratchpad rocket-in-order 4

compile_stencil boom_shared_scratchpad ""
run_and_validate "$boom_sim" boom_shared_scratchpad boom-ooo 5

compile_stencil boom_diagnostic_shared_scratchpad -DBOOM_SERIALIZE_DISPATCH=1
riscv64-unknown-elf-objdump -d /tmp/boom_diagnostic_shared_scratchpad.elf | \
  grep -q "0x7c1"
run_and_validate "$boom_sim" boom_diagnostic_shared_scratchpad \
  boom-ooo-disabled-diagnostic 6

printf "SHARED-SCRATCHPAD-STENCIL-FUNCTIONAL-V1 status=OK implementations=rocket-in-order,boom-ooo,boom-ooo-disabled-diagnostic base=0x08000000 size=65536 banks=1 partitions=1 subbanks=1 outputs_per_mode=256 oracle=independent-host memory_model='"$memory_model"' resource_match_verified=0 matched_comparison_ready=0 adapter=v2 performance=not-measured\n"'
