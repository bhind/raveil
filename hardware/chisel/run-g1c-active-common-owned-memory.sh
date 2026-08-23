#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
rocket_source=${RAVEIL_ROCKET_CHIP_SOURCE:-"$chipyard/generators/rocket-chip"}
runner="$repo_root/hardware/chisel/run-g1c-active-common-owned-memory.sh"
verifier="$repo_root/hardware/chisel/verify_g1c_active_common_owned_memory.py"
dockerfile="$repo_root/hardware/chisel/Dockerfile.boom-sim"
pin_file="$repo_root/hardware/chisel/boom-pin.env"
overlay="$repo_root/hardware/chisel/chipyard-overlay"
patches="$repo_root/hardware/chisel/chipyard-patches"
platform=linux/amd64
image=raveil-boom-functional-sim:v1
toolchain_volume=raveil-chipyard-conda-lock-v1
lock_rel=conda-reqs/conda-lock-reqs/conda-requirements-riscv-tools-linux-64-lean.conda-lock.yml
lock_sha256=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

command -v docker >/dev/null 2>&1 || fail 'docker is required'
[ -d "$chipyard/.git" ] || fail 'a pinned Chipyard checkout is required'
[ -e "$rocket_source/.git" ] || fail 'a pinned Rocket Chip checkout is required'
[ -z "$(git -C "$chipyard" status --porcelain --untracked-files=all --ignore-submodules=none)" ] ||
  fail 'the pinned Chipyard checkout and its submodules must be exact and clean'
[ "$(shasum -a 256 "$chipyard/$lock_rel" | awk '{print $1}')" = "$lock_sha256" ] ||
  fail 'the pinned simulator lockfile hash changed'

RAVEIL_CHIPYARD_SOURCE="$chipyard" \
RAVEIL_ROCKET_CHIP_SOURCE="$rocket_source" \
  "$repo_root/hardware/chisel/verify-boom-reference.sh"

chipyard_revision=$(git -C "$chipyard" rev-parse HEAD)
rocket_revision=$(git -C "$rocket_source" rev-parse HEAD)
input_sha256=$({
  shasum -a 256 \
    "$overlay/RaveilOwnedTLMemory.scala" \
    "$overlay/RaveilDCacheOriginTagger.scala" \
    "$overlay/RaveilFixtureInputProvider.scala" \
    "$overlay/RaveilStaticStencilCore.scala" \
    "$overlay/RaveilStaticStencilTLClient.scala" \
    "$patches/t-0042-tl-token-metadata.patch" \
    "$patches/t-0042-rocket-dcache-origin-hook.patch" \
    "$patches/t-0042-tlxbar-request-defaults.patch" \
    "$runner" "$verifier" "$dockerfile" "$pin_file" |
    awk '{print $1}'
  printf 'chipyard_revision=%s\nrocket_revision=%s\n' \
    "$chipyard_revision" "$rocket_revision"
} | shasum -a 256 | awk '{print $1}')
input_prefix=$(printf '%s' "$input_sha256" | cut -c1-16)
build_volume="raveil-chipyard-g1c-active-$input_prefix"

printf 'G1C-ACTIVE-COMMON-OWNED-MEMORY-HOST-V1 input_sha256=%s chipyard_revision=%s rocket_revision=%s build_volume=%s platform=%s evidence=rtl-simulation-functional performance=not-measured\n' \
  "$input_sha256" "$chipyard_revision" "$rocket_revision" \
  "$build_volume" "$platform"

docker build --provenance=false --platform "$platform" --file "$dockerfile" --tag "$image" "$repo_root"

docker run --rm --platform "$platform" --network none \
  --security-opt no-new-privileges=true \
  --env "RAVEIL_G1C_INPUT_SHA256=$input_sha256" \
  --env "RAVEIL_G1C_CHIPYARD_REVISION=$chipyard_revision" \
  --env "RAVEIL_G1C_ROCKET_REVISION=$rocket_revision" \
  --mount "type=bind,source=$repo_root,target=/repo,readonly" \
  --mount "type=bind,source=$chipyard,target=/source,readonly" \
  --mount "type=bind,source=$overlay,target=/overlay,readonly" \
  --mount "type=bind,source=$patches,target=/patches,readonly" \
  --mount "type=bind,source=$runner,target=/identity/runner.sh,readonly" \
  --mount "type=bind,source=$verifier,target=/identity/verifier.py,readonly" \
  --mount "type=bind,source=$dockerfile,target=/identity/Dockerfile.boom-sim,readonly" \
  --mount "type=bind,source=$pin_file,target=/identity/boom-pin.env,readonly" \
  --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
  --mount "type=volume,source=$build_volume,target=/build" \
  --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
  --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/build/chipyard/.ivy2 \
  --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/build/chipyard/.sbt \
  "$image" bash -lc 'set -euo pipefail
expected_input="$RAVEIL_G1C_INPUT_SHA256"
expected_chipyard="$RAVEIL_G1C_CHIPYARD_REVISION"
expected_rocket="$RAVEIL_G1C_ROCKET_REVISION"
expected_lock="'"$lock_sha256"'"
observed=$({
  sha256sum \
    /overlay/RaveilOwnedTLMemory.scala \
    /overlay/RaveilDCacheOriginTagger.scala \
    /overlay/RaveilFixtureInputProvider.scala \
    /overlay/RaveilStaticStencilCore.scala \
    /overlay/RaveilStaticStencilTLClient.scala \
    /patches/t-0042-tl-token-metadata.patch \
    /patches/t-0042-rocket-dcache-origin-hook.patch \
    /patches/t-0042-tlxbar-request-defaults.patch \
    /identity/runner.sh /identity/verifier.py \
    /identity/Dockerfile.boom-sim /identity/boom-pin.env |
    awk "{print \$1}"
  printf "chipyard_revision=%s\nrocket_revision=%s\n" \
    "$expected_chipyard" "$expected_rocket"
} | sha256sum | awk "{print \$1}")
[ "$observed" = "$expected_input" ]
[ -x /locked/env/bin/verilator ]
[ -x /locked/env/riscv-tools/bin/firtool ]
[ -s /locked/env/riscv-tools/lib/libfesvr.a ]
[ "$(cat /locked/raveil-lock-sha256)" = "$expected_lock" ]

if [ ! -f /build/raveil-g1c-input-sha256 ]; then
  mkdir -p /build/chipyard
  cp -a /source/. /build/chipyard/
  cd /build/chipyard
  [ "$(git rev-parse HEAD)" = "$expected_chipyard" ]
  [ "$(git -C generators/rocket-chip rev-parse HEAD)" = "$expected_rocket" ]
  git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tl-token-metadata.patch
  git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-rocket-dcache-origin-hook.patch
  git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tlxbar-request-defaults.patch
  for source in RaveilOwnedTLMemory.scala RaveilDCacheOriginTagger.scala \
      RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala \
      RaveilStaticStencilTLClient.scala; do
    install -D -m 0444 "/overlay/$source" \
      "generators/chipyard/src/main/scala/raveil/$source"
  done
  printf "%s\n" "$expected_input" > /build/raveil-g1c-input-sha256
else
  [ "$(cat /build/raveil-g1c-input-sha256)" = "$expected_input" ]
  [ "$(git -C /build/chipyard rev-parse HEAD)" = "$expected_chipyard" ]
  [ "$(git -C /build/chipyard/generators/rocket-chip rev-parse HEAD)" = "$expected_rocket" ]
fi

export RISCV=/locked/env/riscv-tools
export PATH=/locked/env/bin:$RISCV/bin:$PATH
export LD_LIBRARY_PATH=$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
verilator --version | grep -q "Verilator 5.020"
"$RISCV/bin/firtool" --version | grep -q "CIRCT firtool-1.61.0"

cd /build/chipyard/sims/verilator
config=RaveilActiveIntegratedGraphRocketConfig
make -j2 CONFIG="$config" CONFIG_PACKAGE=chipyard.raveil
generated="/build/chipyard/sims/verilator/generated-src/chipyard.harness.TestHarness.$config"
fir="$generated/chipyard.harness.TestHarness.$config.fir"
graphml="$generated/chipyard.harness.TestHarness.$config.graphml"
[ -s "$fir" ] && [ -s "$graphml" ]

rocket_count=$(awk "/Rocket/{count++} END{print count+0}" "$fir")
client_count=$(awk "/RaveilStaticStencilTLClient/{count++} END{print count+0}" "$fir")
core_count=$(awk "/RaveilStaticStencilCore/{count++} END{print count+0}" "$fir")
manager_instances=$(awk "/^[[:space:]]*inst [^ ]+ of RaveilOwnedTLMemory/{count++} END{print count+0}" "$fir")
wrapper_count=$(awk "/StaticStencilRegion/{count++} END{print count+0}" "$fir")
scratchpad_count=$(awk "/OwnedFixedLatencyScratchpad/{count++} END{print count+0}" "$fir")
memory_definitions=$(awk "/val memory = SyncReadMem/{count++} END{print count+0}" /overlay/RaveilOwnedTLMemory.scala)
[ "$rocket_count" -gt 0 ] || { echo "error: Rocket is absent from integrated FIR" >&2; exit 1; }
[ "$client_count" -gt 0 ] && [ "$core_count" -gt 0 ] || { echo "error: Graph client or core is absent" >&2; exit 1; }
[ "$manager_instances" -eq 1 ] || { echo "error: integrated top does not contain exactly one manager" >&2; exit 1; }
[ "$memory_definitions" -eq 1 ] || { echo "error: manager does not define exactly one compared-data memory" >&2; exit 1; }
[ "$wrapper_count" -eq 0 ] && [ "$scratchpad_count" -eq 0 ] || { echo "error: standalone Graph memory leaked into integrated top" >&2; exit 1; }

graph_ranges=$(awk "
  /Master Name = raveil-static-stencil-graph/ { capture = 1; next }
  capture && /sourceId = IdRange/ {
    line = \$0; sub(/^.*IdRange\\(/, \"\", line); sub(/\\).*\$/, \"\", line)
    gsub(/[[:space:]]/, \"\", line); gsub(/,/, \":\", line)
    print line; capture = 0
  }
" "$graphml" | sort -u)
[ "$(printf "%s\n" "$graph_ranges" | sed "/^\$/d" | wc -l | tr -d " ")" -eq 2 ]
printf "%s\n" "$graph_ranges" | grep -qx "0:1"
printf "%s\n" "$graph_ranges" | grep -qx "1024:1025"

rtl_list=/build/g1c-generated-rtl-files.txt
find "$generated/gen-collateral" -type f \( -name "*.sv" -o -name "*.v" \) -print |
  LC_ALL=C sort > "$rtl_list"
rtl_files=$(wc -l < "$rtl_list" | tr -d " ")
[ "$rtl_files" -gt 0 ]
rtl_tree_sha256=$(while IFS= read -r file; do sha256sum "$file"; done < "$rtl_list" |
  sha256sum | awk "{print \$1}")
sim="/build/chipyard/sims/verilator/simulator-chipyard.harness-$config"
elf=/build/chipyard/generators/riscv-sodor/riscv-bmarks/multiply.riscv
[ -x "$sim" ] && [ -s "$elf" ]
sim_sha256=$(sha256sum "$sim" | awk "{print \$1}")
elf_sha256=$(sha256sum "$elf" | awk "{print \$1}")

printf "G1C-INTEGRATED-TOPOLOGY-V1 status=OK rocket=present graph_core=present graph_client=present manager_instances=1 compared_data_sync_read_mem_definitions=1 graph_wrapper=absent local_scratchpad=absent rtl_files=%s rtl_tree_sha256=%s evidence=rtl-elaboration-topology performance=not-measured\n" \
  "$rtl_files" "$rtl_tree_sha256"
timeout --foreground 120 "$sim" +permissive +verbose +permissive-off "$elf" 2>&1 |
  python3 /repo/hardware/chisel/verify_g1c_active_common_owned_memory.py
printf "G1C-CLEAN-REPLAY-V1 status=OK input_sha256=%s chipyard_revision=%s rocket_revision=%s lock_sha256=%s simulator_sha256=%s elf_sha256=%s rtl_tree_sha256=%s evidence=rtl-simulation-functional performance=not-measured\n" \
  "$expected_input" "$expected_chipyard" "$expected_rocket" "$expected_lock" \
  "$sim_sha256" "$elf_sha256" "$rtl_tree_sha256"'
