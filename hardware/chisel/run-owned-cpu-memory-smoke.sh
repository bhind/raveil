#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
origin_overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
rocket_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch"
rocket_witness_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch"
rocket_fate_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch"
rocket_exception_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch"
boom_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch"
xbar_request_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch"
workload="$repo_root/hardware/chisel/owned_memory_cpu_smoke.S"
verifier="$repo_root/hardware/chisel/verify_owned_memory_cpu_signature.py"
rocket_witness_workload="$repo_root/hardware/chisel/owned_memory_rocket_request_retire.S"
rocket_witness_verifier="$repo_root/hardware/chisel/verify_owned_rocket_request_retire.py"
rocket_redirect_workload="$repo_root/hardware/chisel/owned_memory_rocket_redirect_negative.S"
rocket_redirect_verifier="$repo_root/hardware/chisel/verify_owned_rocket_redirect_negative.py"
rocket_redirect_fate_verifier="$repo_root/hardware/chisel/verify_owned_rocket_redirect_dcache_fate.py"
rocket_exception_workload="$repo_root/hardware/chisel/owned_memory_rocket_postrequest_exception.S"
rocket_exception_verifier="$repo_root/hardware/chisel/verify_owned_rocket_postrequest_exception.py"
loader_probe="$repo_root/hardware/chisel/owned_memory_loader_probe.S"
loader_probe_linker="$repo_root/hardware/chisel/owned_memory_loader_probe.ld"
loader_probe_verifier="$repo_root/hardware/chisel/verify_owned_memory_loader_probe.py"
source_nonidentity_verifier="$repo_root/hardware/chisel/verify_owned_cpu_source_nonidentity.py"
source_map_verifier="$repo_root/hardware/chisel/verify_owned_cpu_source_map.py"
debug_sba_workload="$repo_root/hardware/chisel/owned_memory_debug_sba_smoke.S"
debug_sba_verifier="$repo_root/hardware/chisel/verify_owned_memory_debug_sba_signature.py"
debug_sba_source_map_verifier="$repo_root/hardware/chisel/verify_owned_debug_sba_source_map.py"
linker="$repo_root/hardware/chisel/boom_functional_smoke.ld"
runner="$repo_root/hardware/chisel/run-owned-cpu-memory-smoke.sh"
dockerfile="$repo_root/hardware/chisel/Dockerfile.boom-sim"
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
cpu_config=${RAVEIL_OWNED_CPU_CONFIG:?owned CPU config is required}
cpu_config_fq=${RAVEIL_OWNED_CPU_CONFIG_FQ:?owned CPU fully qualified config is required}
cpu_label=${RAVEIL_OWNED_CPU_LABEL:?owned CPU label is required}
build_volume=${RAVEIL_OWNED_CPU_BUILD_VOLUME:?owned CPU build volume is required}
cpu_mode=${RAVEIL_OWNED_CPU_MODE:-regular}
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

case "$cpu_mode:$cpu_config:$cpu_config_fq:$cpu_label:$build_volume" in
    regular:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-sim-build-v1) ;;
    regular:RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-sim-build-v1) ;;
    debug-sba:RaveilOwnedDebugSBARocketConfig:chipyard.raveil.RaveilOwnedDebugSBARocketConfig:rocket:raveil-chipyard-owned-debug-sba-rocket-sim-build-v1) ;;
    debug-sba:RaveilOwnedDebugSBASmallBoomConfig:chipyard.raveil.RaveilOwnedDebugSBASmallBoomConfig:boom:raveil-chipyard-owned-debug-sba-boom-sim-build-v1) ;;
    rocket-request-retire:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-request-retire-build-v1) ;;
    rocket-postrequest-redirect:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-request-retire-build-v1) ;;
    rocket-redirect-dcache-fate:RaveilOwnedRocketFateConfig:chipyard.raveil.RaveilOwnedRocketFateConfig:rocket:raveil-chipyard-owned-rocket-redirect-dcache-fate-build-v1) ;;
    rocket-postrequest-exception:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-postrequest-exception-build-v1) ;;
    *)
        echo 'error: unsupported owned CPU smoke configuration' >&2
        exit 1
        ;;
esac

for input in "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" "$xbar_request_patch" "$workload" "$verifier" \
    "$rocket_witness_workload" "$rocket_witness_verifier" "$rocket_redirect_workload" "$rocket_redirect_verifier" "$rocket_redirect_fate_verifier" \
    "$rocket_exception_workload" "$rocket_exception_verifier" \
    "$loader_probe" "$loader_probe_linker" "$loader_probe_verifier" "$source_nonidentity_verifier" "$source_map_verifier" \
    "$debug_sba_workload" "$debug_sba_verifier" "$debug_sba_source_map_verifier" \
    "$linker" "$runner" "$dockerfile"; do
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
origin_overlay_sha256=$(shasum -a 256 "$origin_overlay" | awk '{print $1}')
rocket_hook_patch_sha256=$(shasum -a 256 "$rocket_hook_patch" | awk '{print $1}')
rocket_witness_patch_sha256=$(shasum -a 256 "$rocket_witness_patch" | awk '{print $1}')
rocket_fate_patch_sha256=$(shasum -a 256 "$rocket_fate_patch" | awk '{print $1}')
rocket_exception_patch_sha256=$(shasum -a 256 "$rocket_exception_patch" | awk '{print $1}')
boom_hook_patch_sha256=$(shasum -a 256 "$boom_hook_patch" | awk '{print $1}')
xbar_request_patch_sha256=$(shasum -a 256 "$xbar_request_patch" | awk '{print $1}')
input_sha256=$(
    shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" "$xbar_request_patch" "$workload" \
        "$rocket_witness_workload" "$rocket_witness_verifier" "$rocket_redirect_workload" "$rocket_redirect_verifier" "$rocket_redirect_fate_verifier" \
        "$rocket_exception_workload" "$rocket_exception_verifier" \
        "$verifier" "$loader_probe" "$loader_probe_linker" "$loader_probe_verifier" "$source_nonidentity_verifier" "$source_map_verifier" \
        "$debug_sba_workload" "$debug_sba_verifier" "$debug_sba_source_map_verifier" \
        "$linker" "$runner" "$dockerfile" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)
source_sha256=$(
    {
        shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" \
            "$xbar_request_patch" "$dockerfile" |
            awk '{print $1}'
        printf '%s\n' "$chipyard_revision" "$lock_sha" "$platform"
    } |
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
    --env "RAVEIL_ORIGIN_OVERLAY_SHA256=$origin_overlay_sha256" \
    --env "RAVEIL_ROCKET_HOOK_PATCH_SHA256=$rocket_hook_patch_sha256" \
    --env "RAVEIL_ROCKET_WITNESS_PATCH_SHA256=$rocket_witness_patch_sha256" \
    --env "RAVEIL_ROCKET_FATE_PATCH_SHA256=$rocket_fate_patch_sha256" \
    --env "RAVEIL_ROCKET_EXCEPTION_PATCH_SHA256=$rocket_exception_patch_sha256" \
    --env "RAVEIL_BOOM_HOOK_PATCH_SHA256=$boom_hook_patch_sha256" \
    --env "RAVEIL_XBAR_REQUEST_PATCH_SHA256=$xbar_request_patch_sha256" \
    --env "RAVEIL_INPUT_SHA256=$input_sha256" \
    --env "RAVEIL_SOURCE_SHA256=$source_sha256" \
    --env "RAVEIL_OWNED_CPU_CONFIG=$cpu_config" \
    --env "RAVEIL_OWNED_CPU_CONFIG_FQ=$cpu_config_fq" \
    --env "RAVEIL_OWNED_CPU_LABEL=$cpu_label" \
    --env "RAVEIL_OWNED_CPU_MODE=$cpu_mode" \
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

cache_key=$RAVEIL_INPUT_SHA256
if [ "$RAVEIL_OWNED_CPU_MODE" = debug-sba ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
  cache_key=$RAVEIL_SOURCE_SHA256
fi
build_root=/build/$cache_key
ready_marker="$build_root/.raveil-source-ready"
if [ -e "$build_root" ] && [ ! -f "$ready_marker" ]; then
  echo "error: persistent simulator source cache is incomplete" >&2
  exit 1
fi
if [ ! -e "$build_root" ]; then
  mkdir "$build_root" || {
    echo "error: persistent simulator source cache initialization raced another invocation" >&2
    exit 1
  }
  cp -a /source "$build_root/chipyard"
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/HellaCache.scala" | awk "{print \$1}")" = "d7ce4d0fd84c118fc0db36254f98889b509b6070d1d48dfbc52bb7139a8ca6d2" ]
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "0435dce882f4ad37ee566218fcd8b7d6f9e088c50448677d6eb6efac7e9029ac" ]
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/common/tile.scala" | awk "{print \$1}")" = "570d48ccd0978b55ea9aba77af4a6b8280194d09e2e6c3f018dbe963ec65a9dc" ]
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Xbar.scala" | awk "{print \$1}")" = "7ef8f49ccb3b8df8ba3860d1a54d1eee6d964431b77aa147dd2511f97fe3a613" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_HOOK_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_WITNESS_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_FATE_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_EXCEPTION_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_HOOK_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch | awk "{print \$1}")" = "$RAVEIL_XBAR_REQUEST_PATCH_SHA256" ]
  git -C "$build_root/chipyard/generators/rocket-chip" apply --check --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch
  git -C "$build_root/chipyard/generators/rocket-chip" apply --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch
  if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ] ||
     [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ] ||
     [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ] ||
     [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
    git -C "$build_root/chipyard/generators/rocket-chip" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch
    git -C "$build_root/chipyard/generators/rocket-chip" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch
  fi
  if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ]; then
    git -C "$build_root/chipyard/generators/rocket-chip" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch
    git -C "$build_root/chipyard/generators/rocket-chip" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch
  fi
  if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
    git -C "$build_root/chipyard/generators/rocket-chip" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch
    git -C "$build_root/chipyard/generators/rocket-chip" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch
  fi
  git -C "$build_root/chipyard/generators/boom" apply --check --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch
  git -C "$build_root/chipyard/generators/boom" apply --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch
  git -C "$build_root/chipyard/generators/rocket-chip" apply --check --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch
  git -C "$build_root/chipyard/generators/rocket-chip" apply --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/HellaCache.scala" | awk "{print \$1}")" = "1672c56ad0cdaad15ac0184bf17193a5417bd949662793dec9cd1b8671cd8ad3" ]
  if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "f3015d47932074f79a6e78ca96c45de009a2f049b02ae3a1afa6f885b06774d8" ]
  elif [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "de13ae897d3df31dadb12e4128ba582b5c36ce89774985f931992df5087c4805" ]
  elif [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ] ||
       [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "29a1032a10aeb744853fdf50b0bfa962415461d253e7a74152852b020539b7a2" ]
  else
    [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "0435dce882f4ad37ee566218fcd8b7d6f9e088c50448677d6eb6efac7e9029ac" ]
  fi
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/common/tile.scala" | awk "{print \$1}")" = "2f25f75be69e2dc05c12137e35415224a950306cfbd19a0b2c1d071087bee9d6" ]
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Xbar.scala" | awk "{print \$1}")" = "4867e293671c4df061637b01f358772595c0ec0efff359deeacb8572dde4cbe2" ]
  install -D -m 0444 /repo/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala \
    "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala"
  install -D -m 0444 /repo/hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala \
    "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilDCacheOriginTagger.scala"
  printf "%s\n" "$cache_key" > "$ready_marker"
fi
[ -d "$build_root/chipyard/.git" ]
[ "$(cat "$ready_marker")" = "$cache_key" ]
[ "$(git -C "$build_root/chipyard" rev-parse HEAD)" = "$expected_chipyard" ]
[ "$(sha256sum "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala" | awk "{print \$1}")" = "$RAVEIL_OVERLAY_SHA256" ]
[ "$(sha256sum "$build_root/chipyard/generators/chipyard/src/main/scala/raveil/RaveilDCacheOriginTagger.scala" | awk "{print \$1}")" = "$RAVEIL_ORIGIN_OVERLAY_SHA256" ]
[ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/HellaCache.scala" | awk "{print \$1}")" = "1672c56ad0cdaad15ac0184bf17193a5417bd949662793dec9cd1b8671cd8ad3" ]
if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "f3015d47932074f79a6e78ca96c45de009a2f049b02ae3a1afa6f885b06774d8" ]
elif [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "de13ae897d3df31dadb12e4128ba582b5c36ce89774985f931992df5087c4805" ]
elif [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ] ||
     [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "29a1032a10aeb744853fdf50b0bfa962415461d253e7a74152852b020539b7a2" ]
else
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/RocketCore.scala" | awk "{print \$1}")" = "0435dce882f4ad37ee566218fcd8b7d6f9e088c50448677d6eb6efac7e9029ac" ]
fi
[ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/common/tile.scala" | awk "{print \$1}")" = "2f25f75be69e2dc05c12137e35415224a950306cfbd19a0b2c1d071087bee9d6" ]
[ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Xbar.scala" | awk "{print \$1}")" = "4867e293671c4df061637b01f358772595c0ec0efff359deeacb8572dde4cbe2" ]
expected_overlay_status="?? generators/chipyard/src/main/scala/raveil/RaveilDCacheOriginTagger.scala
?? generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala"
[ "$(git -C "$build_root/chipyard" status --porcelain --untracked-files=all --ignore-submodules=dirty)" = "$expected_overlay_status" ] || {
  echo "error: persistent simulator source cache contains an unexpected top-level change" >&2
  exit 1
}
git -C "$build_root/chipyard" diff --quiet --ignore-submodules=dirty
! git -C "$build_root/chipyard" submodule status | grep -q "^+"
git -C "$build_root/chipyard" submodule foreach --quiet --recursive '\''
  git diff --check
  unexpected=$(git status --porcelain --untracked-files=all | grep -v "^?? target/" | grep -v "^ M src/main/scala/rocket/HellaCache.scala$" | grep -v "^ M src/main/scala/rocket/RocketCore.scala$" | grep -v "^ M src/main/scala/tilelink/Xbar.scala$" | grep -v "^ M src/main/scala/common/tile.scala$" || true)
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
if [ "$RAVEIL_OWNED_CPU_MODE" = debug-sba ]; then
  python3 /repo/hardware/chisel/verify_owned_debug_sba_source_map.py \
    "$RAVEIL_OWNED_CPU_LABEL" "$graph"
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_debug_sba_smoke.S \
    -o "$build_root/owned_memory_debug_sba_smoke.elf"
  debug_signature="$build_root/owned_memory_debug_sba_smoke.signature"
  rm -f "$debug_signature"
  timeout --foreground 180 "$sim" +signature="$debug_signature" +signature-granularity=4 \
    +permissive +permissive-off "$build_root/owned_memory_debug_sba_smoke.elf"
  python3 /repo/hardware/chisel/verify_owned_memory_debug_sba_signature.py \
    "$RAVEIL_OWNED_CPU_LABEL" "$debug_signature"
  printf "OWNED-CPU-DEBUG-SBA-SMOKE-V1 status=OK cpu=%s config=%s input_sha256=%s graph_sha256=%s dmi_driver=repository-owned source_client_class=debug-sba-observed semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi
python3 /repo/hardware/chisel/verify_owned_cpu_source_map.py \
  "$RAVEIL_OWNED_CPU_LABEL" "$graph"

if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_rocket_request_retire.S \
    -o "$build_root/owned_memory_rocket_request_retire.elf"
  witness_signature="$build_root/owned_memory_rocket_request_retire.signature"
  witness_log="$build_root/owned_memory_rocket_request_retire.log"
  rm -f "$witness_signature" "$witness_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$witness_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_rocket_request_retire.elf" 2>&1 | tee "$witness_log"
  python3 /repo/hardware/chisel/verify_owned_rocket_request_retire.py \
    "$witness_log" "$witness_signature"
  printf "OWNED-ROCKET-REQUEST-RETIRE-HOST-V1 status=OK cpu=rocket config=%s input_sha256=%s graph_sha256=%s event_source=rocket-pinned cpu_execution=rtl-simulation d_token_correlation=not-run semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_rocket_redirect_negative.S \
    -o "$build_root/owned_memory_rocket_redirect_negative.elf"
  redirect_signature="$build_root/owned_memory_rocket_redirect_negative.signature"
  redirect_log="$build_root/owned_memory_rocket_redirect_negative.log"
  rm -f "$redirect_signature" "$redirect_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$redirect_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_rocket_redirect_negative.elf" 2>&1 | tee "$redirect_log"
  python3 /repo/hardware/chisel/verify_owned_rocket_redirect_negative.py \
    "$redirect_log" "$redirect_signature"
  printf "OWNED-ROCKET-POSTREQUEST-REDIRECT-HOST-V1 status=OK cpu=rocket config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=rocket-pinned cpu_execution=rtl-simulation postrequest_redirect=covered pre_request_kill=not-run dcache_s1_kill_correlation=not-run a_d_correlation=not-run semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_rocket_redirect_negative.S \
    -o "$build_root/owned_memory_rocket_redirect_dcache_fate.elf"
  fate_signature="$build_root/owned_memory_rocket_redirect_dcache_fate.signature"
  fate_log="$build_root/owned_memory_rocket_redirect_dcache_fate.log"
  rm -f "$fate_signature" "$fate_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$fate_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_rocket_redirect_dcache_fate.elf" 2>&1 | tee "$fate_log"
  python3 /repo/hardware/chisel/verify_owned_rocket_redirect_negative.py \
    "$fate_log" "$fate_signature"
  python3 /repo/hardware/chisel/verify_owned_rocket_redirect_dcache_fate.py \
    "$fate_log" "$fate_signature"
  printf "OWNED-ROCKET-REDIRECT-DCACHE-FATE-HOST-V1 status=OK cpu=rocket config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=rocket-pinned cpu_execution=rtl-simulation dcache_s1_kill=observed wrong_path_store_tl_a=not-observed transport_token_correlation=not-carried semantic_initiator=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_rocket_postrequest_exception.S \
    -o "$build_root/owned_memory_rocket_postrequest_exception.elf"
  exception_signature="$build_root/owned_memory_rocket_postrequest_exception.signature"
  exception_log="$build_root/owned_memory_rocket_postrequest_exception.log"
  rm -f "$exception_signature" "$exception_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$exception_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_rocket_postrequest_exception.elf" 2>&1 | tee "$exception_log"
  python3 /repo/hardware/chisel/verify_owned_rocket_postrequest_exception.py \
    "$exception_log" "$exception_signature"
  printf "OWNED-ROCKET-POSTREQUEST-EXCEPTION-HOST-V1 status=OK cpu=rocket config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=rocket-pinned cpu_execution=rtl-simulation postrequest_exception=covered post_tl_a_exception=not-run transport_token_correlation=not-carried semantic_initiator=not-proven general_rollback=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

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

riscv64-unknown-elf-gcc \
  -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
  -nostdlib -nostartfiles -static -Wl,--no-relax \
  -T /repo/hardware/chisel/owned_memory_loader_probe.ld \
  /repo/hardware/chisel/owned_memory_loader_probe.S \
  -o "$build_root/owned_memory_loader_probe.elf"
probe_elf="$build_root/owned_memory_loader_probe.elf"
probe_load_count=$(riscv64-unknown-elf-readelf -lW "$probe_elf" | \
  awk '\''$1 == "LOAD" && $3 == "0x0000000008000000" { count += 1 } END { print count + 0 }'\'')
[ "$probe_load_count" = 1 ] || {
  echo "error: loader probe must contain exactly one PT_LOAD at 0x08000000" >&2
  exit 1
}
probe_load=$(riscv64-unknown-elf-readelf -lW "$probe_elf" | \
  awk '\''$1 == "LOAD" && $3 == "0x0000000008000000" { print $3, $4, $5, $6, $7 }'\'')
[ "$probe_load" = "0x0000000008000000 0x0000000008000000 0x000004 0x000004 RW" ] || {
  echo "error: loader probe PT_LOAD layout is not the exact four-byte writable owned-memory payload" >&2
  exit 1
}
probe_symbols=$(riscv64-unknown-elf-nm -n "$probe_elf")
[ "$(printf "%s\n" "$probe_symbols" | awk '\''$3 == "loader_probe_payload" { print $1 }'\'')" = 0000000008000000 ]
[ "$(printf "%s\n" "$probe_symbols" | awk '\''$3 == "_start" { print $1 }'\'')" = 0000000080000000 ]
[ "$(printf "%s\n" "$probe_symbols" | awk '\''$3 == "begin_signature" { print $1 }'\'')" = 00000000800001f0 ]
[ "$(printf "%s\n" "$probe_symbols" | awk '\''$3 == "end_signature" { print $1 }'\'')" = 0000000080000274 ]
[ "$(printf "%s\n" "$probe_symbols" | awk '\''$3 == "tohost" { print $1 }'\'')" = 0000000080000280 ]

loader_signature="$build_root/owned_memory_loader_probe.signature"
rm -f "$loader_signature"
"$sim" +signature="$loader_signature" +signature-granularity=4 \
  +permissive +permissive-off "$probe_elf"
python3 /repo/hardware/chisel/verify_owned_memory_loader_probe.py \
  "$RAVEIL_OWNED_CPU_LABEL" "$loader_signature"
python3 /repo/hardware/chisel/verify_owned_cpu_source_nonidentity.py \
  "$RAVEIL_OWNED_CPU_LABEL" "$signature" "$loader_signature" \
  "$build_root/owned_memory_cpu_smoke.elf" "$probe_elf"
printf "OWNED-CPU-LOADER-PROBE-AUDIT-V1 status=OK cpu=%s config=%s input_sha256=%s graph_sha256=%s transport=SimTSI-FESVR-PT_LOAD preload_bypass=absent evidence=rtl-simulation-functional performance=not-measured\n" \
  "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" \
  "$(sha256sum "$graph" | cut -c1-64)"
printf "OWNED-CPU-MEMORY-SMOKE-V3 status=OK cpu=%s config=%s input_sha256=%s phase_fences=iorw direct_manager_path=verified source_client_class=dcache-mmio-verified dcache_origin_path=observed semantic_initiator=not-proven cpu_execution=%s-rtl-simulation resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
  "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" '"$input_sha256"' "$RAVEIL_OWNED_CPU_LABEL"'
