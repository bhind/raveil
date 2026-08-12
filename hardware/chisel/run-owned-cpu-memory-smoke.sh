#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
workload="$repo_root/hardware/chisel/owned_memory_cpu_smoke.S"
verifier="$repo_root/hardware/chisel/verify_owned_memory_cpu_signature.py"
source_map_verifier="$repo_root/hardware/chisel/verify_owned_cpu_source_map.py"
linker="$repo_root/hardware/chisel/boom_functional_smoke.ld"
runner="$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
cpu_config=${RAVEIL_OWNED_CPU_CONFIG:?owned CPU config is required}
cpu_config_fq=${RAVEIL_OWNED_CPU_CONFIG_FQ:?owned CPU fully qualified config is required}
cpu_label=${RAVEIL_OWNED_CPU_LABEL:?owned CPU label is required}
build_volume=${RAVEIL_OWNED_CPU_BUILD_VOLUME:?owned CPU build volume is required}
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

case "$cpu_config:$cpu_config_fq:$cpu_label:$build_volume" in
    RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-sim-build-v1) ;;
    RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-sim-build-v1) ;;
    *)
        echo 'error: unsupported owned CPU smoke configuration' >&2
        exit 1
        ;;
esac

for input in "$overlay" "$workload" "$verifier" "$source_map_verifier" "$linker" "$runner"; do
    [ -f "$input" ] || {
        echo "error: required owned CPU smoke input is missing: $input" >&2
        exit 1
    }
done
[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-simulator-deps.sh first' >&2
    exit 1
}
command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

"$repo_root/hardware/chisel/verify-boom-reference.sh"
[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: Chipyard checkout or simulator dependency is not exact and clean' >&2
    exit 1
}

overlay_sha256=$(shasum -a 256 "$overlay" | awk '{print $1}')
input_sha256=$(
    shasum -a 256 "$overlay" "$workload" "$verifier" "$source_map_verifier" "$linker" "$runner" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom-sim" \
    --tag "$image" \
    "$repo_root"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$build_volume,target=/build" \
    --env "RAVEIL_OVERLAY_SHA256=$overlay_sha256" \
    --env "RAVEIL_OWNED_CPU_CONFIG=$cpu_config" \
    --env "RAVEIL_OWNED_CPU_CONFIG_FQ=$cpu_config_fq" \
    --env "RAVEIL_OWNED_CPU_LABEL=$cpu_label" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
expected_chipyard='"$chipyard_revision"'
expected_lock='"$lock_sha"'
[ -x /locked/env/bin/verilator ] || {
  echo "error: run ./hardware/chisel/run-boom-functional-smoke.sh once to prepare the pinned simulator toolchain" >&2
  exit 1
}
[ "$(cat /locked/raveil-lock-sha256)" = "$expected_lock" ]
verilator --version | grep -q "Verilator 5.020"
riscv64-unknown-elf-gcc --version | grep -q "12.2.0"

build_root=/build/$RAVEIL_OVERLAY_SHA256
if [ ! -d "$build_root/chipyard/.git" ]; then
  mkdir -p "$build_root"
  cp -a /source "$build_root/chipyard"
  install -D -m 0444 /repo/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala \
    "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala"
fi
[ "$(git -C "$build_root/chipyard" rev-parse HEAD)" = "$expected_chipyard" ]
[ "$(sha256sum "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala" | awk "{print \$1}")" = "$RAVEIL_OVERLAY_SHA256" ]
expected_overlay_status="?? generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala"
[ "$(git -C "$build_root/chipyard" status --porcelain --untracked-files=all --ignore-submodules=dirty)" = "$expected_overlay_status" ] || {
  echo "error: persistent simulator source cache contains an unexpected top-level change" >&2
  exit 1
}
git -C "$build_root/chipyard" diff --quiet --ignore-submodules=dirty
! git -C "$build_root/chipyard" submodule status | grep -q "^+"
git -C "$build_root/chipyard" submodule foreach --quiet --recursive '\''
  git diff --quiet
  unexpected=$(git status --porcelain --untracked-files=all | grep -v "^?? target/" || true)
  [ -z "$unexpected" ] || {
    echo "error: persistent simulator submodule cache contains an unexpected change: $name" >&2
    echo "$unexpected" >&2
    exit 1
  }
'\''

cd "$build_root/chipyard/sims/verilator"
make -j2 CONFIG="$RAVEIL_OWNED_CPU_CONFIG" CONFIG_PACKAGE=chipyard.raveil
sim="$build_root/chipyard/sims/verilator/simulator-chipyard.harness-$RAVEIL_OWNED_CPU_CONFIG"
test -x "$sim"
graph="$build_root/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.$RAVEIL_OWNED_CPU_CONFIG/chipyard.harness.TestHarness.$RAVEIL_OWNED_CPU_CONFIG.graphml"
test -f "$graph"
python3 /repo/hardware/chisel/verify_owned_cpu_source_map.py \
  "$RAVEIL_OWNED_CPU_LABEL" "$graph"

riscv64-unknown-elf-gcc \
  -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
  -nostdlib -nostartfiles -static -Wl,--no-relax \
  -T /repo/hardware/chisel/boom_functional_smoke.ld \
  /repo/hardware/chisel/owned_memory_cpu_smoke.S \
  -o "$build_root/owned_memory_cpu_smoke.elf"
riscv64-unknown-elf-nm "$build_root/owned_memory_cpu_smoke.elf" | grep -q " D begin_signature$"
riscv64-unknown-elf-nm "$build_root/owned_memory_cpu_smoke.elf" | grep -q " D end_signature$"
riscv64-unknown-elf-nm "$build_root/owned_memory_cpu_smoke.elf" | grep -q " D tohost$"

signature="$build_root/owned_memory_cpu.signature"
rm -f "$signature"
"$sim" +signature="$signature" +signature-granularity=4 \
  +permissive +permissive-off "$build_root/owned_memory_cpu_smoke.elf"
python3 /repo/hardware/chisel/verify_owned_memory_cpu_signature.py \
  "$RAVEIL_OWNED_CPU_LABEL" "$signature"
printf "OWNED-CPU-MEMORY-SMOKE-V2 status=OK cpu=%s config=%s input_sha256=%s phase_fences=iorw direct_manager_path=verified source_client_class=dcache-mmio-verified semantic_initiator=not-proven cpu_execution=%s-rtl-simulation resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
  "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" '"$input_sha256"' "$RAVEIL_OWNED_CPU_LABEL"'
