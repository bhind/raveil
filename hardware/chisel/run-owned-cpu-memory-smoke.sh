#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
origin_overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
rocket_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch"
rocket_witness_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch"
rocket_fate_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch"
rocket_exception_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch"
boom_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch"
boom_lifecycle_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-load-lifecycle.patch"
boom_misaligned_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-misaligned-rollback.patch"
boom_store_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-store-authorization.patch"
boom_store_token_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-store-token-handoff.patch"
boom_token_fields_only_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-token-fields-only.patch"
boom_redirect_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-postrequest-redirect.patch"
xbar_request_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch"
tl_token_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-tl-token-metadata.patch"
workload="$repo_root/hardware/chisel/owned_memory_cpu_smoke.S"
verifier="$repo_root/hardware/chisel/verify_owned_memory_cpu_signature.py"
rocket_witness_workload="$repo_root/hardware/chisel/owned_memory_rocket_request_retire.S"
rocket_witness_verifier="$repo_root/hardware/chisel/verify_owned_rocket_request_retire.py"
rocket_redirect_workload="$repo_root/hardware/chisel/owned_memory_rocket_redirect_negative.S"
rocket_redirect_verifier="$repo_root/hardware/chisel/verify_owned_rocket_redirect_negative.py"
rocket_redirect_fate_verifier="$repo_root/hardware/chisel/verify_owned_rocket_redirect_dcache_fate.py"
rocket_exception_workload="$repo_root/hardware/chisel/owned_memory_rocket_postrequest_exception.S"
rocket_exception_verifier="$repo_root/hardware/chisel/verify_owned_rocket_postrequest_exception.py"
boom_lifecycle_workload="$repo_root/hardware/chisel/owned_memory_boom_load_lifecycle.S"
boom_lifecycle_verifier="$repo_root/hardware/chisel/verify_owned_boom_load_lifecycle.py"
boom_misaligned_workload="$repo_root/hardware/chisel/owned_memory_boom_misaligned_rollback.S"
boom_misaligned_verifier="$repo_root/hardware/chisel/verify_owned_boom_misaligned_rollback.py"
boom_store_workload="$repo_root/hardware/chisel/owned_memory_boom_store_authorization.S"
boom_store_verifier="$repo_root/hardware/chisel/verify_owned_boom_store_authorization.py"
boom_store_token_verifier="$repo_root/hardware/chisel/verify_owned_boom_store_token_handoff.py"
boom_store_token_default_invalid_verifier="$repo_root/hardware/chisel/verify_owned_boom_store_token_default_invalid.py"
boom_redirect_workload="$repo_root/hardware/chisel/owned_memory_boom_postrequest_redirect.S"
boom_redirect_verifier="$repo_root/hardware/chisel/verify_owned_boom_postrequest_redirect.py"
loader_probe="$repo_root/hardware/chisel/owned_memory_loader_probe.S"
loader_probe_linker="$repo_root/hardware/chisel/owned_memory_loader_probe.ld"
loader_probe_verifier="$repo_root/hardware/chisel/verify_owned_memory_loader_probe.py"
source_nonidentity_verifier="$repo_root/hardware/chisel/verify_owned_cpu_source_nonidentity.py"
source_map_verifier="$repo_root/hardware/chisel/verify_owned_cpu_source_map.py"
debug_sba_workload="$repo_root/hardware/chisel/owned_memory_debug_sba_smoke.S"
debug_sba_verifier="$repo_root/hardware/chisel/verify_owned_memory_debug_sba_signature.py"
debug_sba_source_map_verifier="$repo_root/hardware/chisel/verify_owned_debug_sba_source_map.py"
controlled_workload_s="$repo_root/hardware/chisel/riscv_stencil_smoke.S"
controlled_workload_c="$repo_root/hardware/chisel/riscv_stencil_smoke.c"
repeated_workload_s="$repo_root/hardware/chisel/riscv_stencil_repeated.S"
repeated_workload_c="$repo_root/hardware/chisel/riscv_stencil_repeated.c"
controlled_linker="$repo_root/hardware/chisel/riscv_stencil_system_scratchpad.ld"
controlled_verifier="$repo_root/raveil/controlled_run.py"
repeated_verifier="$repo_root/raveil/t0044_repeated.py"
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
controlled_seed=${RAVEIL_CONTROLLED_SEED:-1}
controlled_invocation=${RAVEIL_CONTROLLED_INVOCATION:-$controlled_seed}
controlled_serialize=${RAVEIL_CONTROLLED_SERIALIZE_DISPATCH:-0}
repeat_account=${RAVEIL_REPEAT_ACCOUNT:-1}
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

case "$controlled_seed:$controlled_invocation" in
    *[!0-9:]*|0:*|*:0)
        echo 'error: controlled seed/invocation must be positive integers and serialize must be 0 or 1' >&2
        exit 1
        ;;
esac
case "$controlled_serialize" in
    0|1) ;;
    *) echo 'error: controlled serialize must be 0 or 1' >&2; exit 1 ;;
esac
case "$repeat_account" in
    *[!0-9]*|'') echo 'error: repeat account must be in [1,256]' >&2; exit 1 ;;
esac
[ "$repeat_account" -ge 1 ] && [ "$repeat_account" -le 256 ] || {
    echo 'error: repeat account must be in [1,256]' >&2
    exit 1
}

case "$cpu_mode:$cpu_config:$cpu_config_fq:$cpu_label:$build_volume" in
    regular:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-sim-build-v1) ;;
    regular:RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-sim-build-v1) ;;
    controlled:RaveilMatchedRocketConfig:chipyard.raveil.RaveilMatchedRocketConfig:rocket:raveil-chipyard-matched-rocket-controlled-v1) ;;
    controlled:RaveilMatchedSmallBoomConfig:chipyard.raveil.RaveilMatchedSmallBoomConfig:boom:raveil-chipyard-matched-boom-controlled-v1) ;;
    controlled:RaveilMatchedSmallBoomConfig:chipyard.raveil.RaveilMatchedSmallBoomConfig:boom-serialize:raveil-chipyard-matched-boom-controlled-v1) ;;
    controlled-repeat:RaveilRepeatedMatchedRocketConfig:chipyard.raveil.RaveilRepeatedMatchedRocketConfig:rocket:raveil-chipyard-repeated-rocket-v1) ;;
    controlled-repeat:RaveilRepeatedMatchedSmallBoomConfig:chipyard.raveil.RaveilRepeatedMatchedSmallBoomConfig:boom:raveil-chipyard-repeated-boom-v1) ;;
    controlled-repeat:RaveilRepeatedMatchedSmallBoomConfig:chipyard.raveil.RaveilRepeatedMatchedSmallBoomConfig:boom-serialize:raveil-chipyard-repeated-boom-v1) ;;
    debug-sba:RaveilOwnedDebugSBARocketConfig:chipyard.raveil.RaveilOwnedDebugSBARocketConfig:rocket:raveil-chipyard-owned-debug-sba-rocket-sim-build-v1) ;;
    debug-sba:RaveilOwnedDebugSBASmallBoomConfig:chipyard.raveil.RaveilOwnedDebugSBASmallBoomConfig:boom:raveil-chipyard-owned-debug-sba-boom-sim-build-v1) ;;
    rocket-request-retire:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-request-retire-build-v1) ;;
    rocket-postrequest-redirect:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-request-retire-build-v1) ;;
    rocket-redirect-dcache-fate:RaveilOwnedRocketFateConfig:chipyard.raveil.RaveilOwnedRocketFateConfig:rocket:raveil-chipyard-owned-rocket-redirect-dcache-fate-build-v1) ;;
    rocket-postrequest-exception:RaveilOwnedRocketConfig:chipyard.raveil.RaveilOwnedRocketConfig:rocket:raveil-chipyard-owned-rocket-postrequest-exception-build-v1) ;;
    boom-load-lifecycle:RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-load-lifecycle-build-v2) ;;
    boom-misaligned-rollback:RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-misaligned-rollback-build-v2) ;;
    boom-store-authorization:RaveilOwnedSmallBoomFateConfig:chipyard.raveil.RaveilOwnedSmallBoomFateConfig:boom:raveil-chipyard-owned-boom-store-authorization-build-v1) ;;
    boom-store-token-handoff:RaveilOwnedSmallBoomTokenConfig:chipyard.raveil.RaveilOwnedSmallBoomTokenConfig:boom:raveil-chipyard-owned-boom-store-token-handoff-build-v4) ;;
    boom-store-token-default-invalid:RaveilOwnedSmallBoomTokenConfig:chipyard.raveil.RaveilOwnedSmallBoomTokenConfig:boom:raveil-chipyard-owned-boom-store-token-default-invalid-build-v1) ;;
    boom-postrequest-redirect:RaveilOwnedSmallBoomConfig:chipyard.raveil.RaveilOwnedSmallBoomConfig:boom:raveil-chipyard-owned-boom-postrequest-redirect-build-v1) ;;
    *)
        echo 'error: unsupported owned CPU smoke configuration' >&2
        exit 1
        ;;
esac

applied_patch_manifest=t-0042-tl-token-metadata.patch,t-0042-rocket-dcache-origin-hook.patch
case "$cpu_mode" in
    rocket-request-retire|rocket-postrequest-redirect|rocket-redirect-dcache-fate|rocket-postrequest-exception)
        applied_patch_manifest="$applied_patch_manifest,t-0042-rocket-request-retire-witness.patch"
        ;;
esac
case "$cpu_mode" in
    rocket-redirect-dcache-fate)
        applied_patch_manifest="$applied_patch_manifest,t-0042-rocket-redirect-dcache-fate.patch"
        ;;
    rocket-postrequest-exception)
        applied_patch_manifest="$applied_patch_manifest,t-0042-rocket-postrequest-exception.patch"
        ;;
esac
applied_patch_manifest="$applied_patch_manifest,t-0042-boom-dcache-origin-hook.patch"
case "$cpu_mode" in
    boom-load-lifecycle)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-load-lifecycle.patch"
        ;;
    boom-misaligned-rollback)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-misaligned-rollback.patch"
        ;;
    boom-store-authorization)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-store-authorization.patch"
        ;;
    boom-store-token-handoff)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-store-authorization.patch,t-0042-boom-store-token-handoff.patch"
        ;;
    boom-store-token-default-invalid)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-store-authorization.patch,t-0042-boom-token-fields-only.patch"
        ;;
    boom-postrequest-redirect)
        applied_patch_manifest="$applied_patch_manifest,t-0042-boom-postrequest-redirect.patch"
        ;;
esac
applied_patch_manifest="$applied_patch_manifest,t-0042-tlxbar-request-defaults.patch"

for input in "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" "$boom_lifecycle_patch" "$boom_misaligned_patch" "$boom_store_patch" "$boom_store_token_patch" "$boom_token_fields_only_patch" "$boom_redirect_patch" "$xbar_request_patch" "$tl_token_patch" "$workload" "$verifier" \
    "$rocket_witness_workload" "$rocket_witness_verifier" "$rocket_redirect_workload" "$rocket_redirect_verifier" "$rocket_redirect_fate_verifier" \
    "$rocket_exception_workload" "$rocket_exception_verifier" "$boom_lifecycle_workload" "$boom_lifecycle_verifier" "$boom_misaligned_workload" "$boom_misaligned_verifier" "$boom_store_workload" "$boom_store_verifier" "$boom_store_token_verifier" "$boom_store_token_default_invalid_verifier" "$boom_redirect_workload" "$boom_redirect_verifier" \
    "$loader_probe" "$loader_probe_linker" "$loader_probe_verifier" "$source_nonidentity_verifier" "$source_map_verifier" \
    "$debug_sba_workload" "$debug_sba_verifier" "$debug_sba_source_map_verifier" \
    "$controlled_workload_s" "$controlled_workload_c" "$controlled_linker" "$controlled_verifier" \
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
boom_lifecycle_patch_sha256=$(shasum -a 256 "$boom_lifecycle_patch" | awk '{print $1}')
boom_misaligned_patch_sha256=$(shasum -a 256 "$boom_misaligned_patch" | awk '{print $1}')
boom_store_patch_sha256=$(shasum -a 256 "$boom_store_patch" | awk '{print $1}')
boom_store_token_patch_sha256=$(shasum -a 256 "$boom_store_token_patch" | awk '{print $1}')
boom_token_fields_only_patch_sha256=$(shasum -a 256 "$boom_token_fields_only_patch" | awk '{print $1}')
boom_redirect_patch_sha256=$(shasum -a 256 "$boom_redirect_patch" | awk '{print $1}')
xbar_request_patch_sha256=$(shasum -a 256 "$xbar_request_patch" | awk '{print $1}')
tl_token_patch_sha256=$(shasum -a 256 "$tl_token_patch" | awk '{print $1}')
input_sha256=$(
    {
        shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" "$boom_lifecycle_patch" "$boom_misaligned_patch" "$boom_store_patch" "$boom_store_token_patch" "$boom_token_fields_only_patch" "$boom_redirect_patch" "$xbar_request_patch" "$tl_token_patch" "$workload" \
            "$rocket_witness_workload" "$rocket_witness_verifier" "$rocket_redirect_workload" "$rocket_redirect_verifier" "$rocket_redirect_fate_verifier" \
            "$rocket_exception_workload" "$rocket_exception_verifier" "$boom_lifecycle_workload" "$boom_lifecycle_verifier" "$boom_misaligned_workload" "$boom_misaligned_verifier" "$boom_store_workload" "$boom_store_verifier" "$boom_store_token_verifier" "$boom_store_token_default_invalid_verifier" "$boom_redirect_workload" "$boom_redirect_verifier" \
            "$verifier" "$loader_probe" "$loader_probe_linker" "$loader_probe_verifier" "$source_nonidentity_verifier" "$source_map_verifier" \
            "$debug_sba_workload" "$debug_sba_verifier" "$debug_sba_source_map_verifier" \
            "$controlled_workload_s" "$controlled_workload_c" "$repeated_workload_s" "$repeated_workload_c" "$controlled_linker" "$controlled_verifier" "$repeated_verifier" \
            "$linker" "$runner" "$dockerfile" |
            awk '{print $1}'
        printf '%s\n' "$cpu_mode" "$applied_patch_manifest"
        printf 'controlled_seed=%s\ncontrolled_invocation=%s\ncontrolled_serialize=%s\nrepeat_account=%s\ncpu_label=%s\n' \
            "$controlled_seed" "$controlled_invocation" "$controlled_serialize" "$repeat_account" "$cpu_label"
    } |
        shasum -a 256 |
        awk '{print $1}'
)
cache_source_sha256=$(
    {
        shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" "$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch" "$boom_lifecycle_patch" "$boom_misaligned_patch" "$boom_store_patch" "$boom_store_token_patch" "$boom_token_fields_only_patch" "$boom_redirect_patch" \
            "$xbar_request_patch" "$tl_token_patch" "$dockerfile" |
            awk '{print $1}'
        printf '%s\n' "$chipyard_revision" "$lock_sha" "$platform" "$cpu_mode" "$applied_patch_manifest"
    } |
        shasum -a 256 |
        awk '{print $1}'
)
source_sha256=$cache_source_sha256
if [ "$cpu_mode" = controlled ]; then
    source_sha256=$(
        {
            shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" \
                "$boom_hook_patch" "$xbar_request_patch" "$tl_token_patch" \
                "$controlled_workload_s" "$controlled_workload_c" \
                "$controlled_linker" "$controlled_verifier" \
                "$repeated_verifier" "$runner" \
                "$dockerfile" | awk '{print $1}'
            printf '%s\n' "$chipyard_revision" "$lock_sha" "$platform" \
                "$cpu_mode" "$applied_patch_manifest" \
                "controlled_serialize=$controlled_serialize" "cpu_label=$cpu_label"
        } | shasum -a 256 | awk '{print $1}'
    )
fi
if [ "$cpu_mode" = controlled-repeat ]; then
    source_sha256=$(
        {
            shasum -a 256 "$overlay" "$origin_overlay" "$rocket_hook_patch" \
                "$boom_hook_patch" "$xbar_request_patch" "$tl_token_patch" \
                "$repeated_workload_s" "$repeated_workload_c" \
                "$controlled_linker" "$controlled_verifier" "$runner" \
                "$dockerfile" | awk '{print $1}'
            printf '%s\n' "$chipyard_revision" "$lock_sha" "$platform" \
                "$cpu_mode" "$applied_patch_manifest" \
                "controlled_serialize=$controlled_serialize" "cpu_label=$cpu_label"
        } | shasum -a 256 | awk '{print $1}'
    )
fi

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom-sim" \
    --tag "$image" \
    "$repo_root"

dockerfile_sha256=$(shasum -a 256 "$dockerfile" | awk '{print $1}')
toolchain_sha256=$(
    printf '%s\n' "$platform" "$dockerfile_sha256" "$lock_sha" \
        'verilator=5.020' 'riscv64-unknown-elf-gcc=12.2.0' |
        shasum -a 256 |
        awk '{print $1}'
)

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
    --env "RAVEIL_BOOM_LIFECYCLE_PATCH_SHA256=$boom_lifecycle_patch_sha256" \
    --env "RAVEIL_BOOM_MISALIGNED_PATCH_SHA256=$boom_misaligned_patch_sha256" \
    --env "RAVEIL_BOOM_STORE_PATCH_SHA256=$boom_store_patch_sha256" \
    --env "RAVEIL_BOOM_STORE_TOKEN_PATCH_SHA256=$boom_store_token_patch_sha256" \
    --env "RAVEIL_BOOM_TOKEN_FIELDS_ONLY_PATCH_SHA256=$boom_token_fields_only_patch_sha256" \
    --env "RAVEIL_BOOM_REDIRECT_PATCH_SHA256=$boom_redirect_patch_sha256" \
    --env "RAVEIL_XBAR_REQUEST_PATCH_SHA256=$xbar_request_patch_sha256" \
    --env "RAVEIL_TL_TOKEN_PATCH_SHA256=$tl_token_patch_sha256" \
    --env "RAVEIL_INPUT_SHA256=$input_sha256" \
    --env "RAVEIL_SOURCE_SHA256=$source_sha256" \
    --env "RAVEIL_CACHE_SOURCE_SHA256=$cache_source_sha256" \
    --env "RAVEIL_TOOLCHAIN_SHA256=$toolchain_sha256" \
    --env "RAVEIL_APPLIED_PATCH_MANIFEST=$applied_patch_manifest" \
    --env "RAVEIL_OWNED_CPU_CONFIG=$cpu_config" \
    --env "RAVEIL_OWNED_CPU_CONFIG_FQ=$cpu_config_fq" \
    --env "RAVEIL_OWNED_CPU_LABEL=$cpu_label" \
    --env "RAVEIL_OWNED_CPU_MODE=$cpu_mode" \
    --env "RAVEIL_CONTROLLED_SEED=$controlled_seed" \
    --env "RAVEIL_CONTROLLED_INVOCATION=$controlled_invocation" \
    --env "RAVEIL_CONTROLLED_SERIALIZE_DISPATCH=$controlled_serialize" \
    --env "RAVEIL_REPEAT_ACCOUNT=$repeat_account" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
export PYTHONPATH=/repo
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
   [ "$RAVEIL_OWNED_CPU_MODE" = controlled ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = controlled-repeat ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-request-retire ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-redirect ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-redirect-dcache-fate ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = rocket-postrequest-exception ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-load-lifecycle ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-misaligned-rollback ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-authorization ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ] ||
   [ "$RAVEIL_OWNED_CPU_MODE" = boom-postrequest-redirect ]; then
  cache_key=$RAVEIL_CACHE_SOURCE_SHA256
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
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "1400d3997b94d1d5e4064d126d22aabd467905e1fd962896ac19cfbd1955371a" ]
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Xbar.scala" | awk "{print \$1}")" = "7ef8f49ccb3b8df8ba3860d1a54d1eee6d964431b77aa147dd2511f97fe3a613" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_HOOK_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-request-retire-witness.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_WITNESS_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-redirect-dcache-fate.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_FATE_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-rocket-postrequest-exception.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_EXCEPTION_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_HOOK_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-load-lifecycle.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_LIFECYCLE_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-misaligned-rollback.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_MISALIGNED_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-authorization.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_STORE_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-token-handoff.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_STORE_TOKEN_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-token-fields-only.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_TOKEN_FIELDS_ONLY_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-boom-postrequest-redirect.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_REDIRECT_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch | awk "{print \$1}")" = "$RAVEIL_XBAR_REQUEST_PATCH_SHA256" ]
  [ "$(sha256sum /repo/hardware/chisel/chipyard-patches/t-0042-tl-token-metadata.patch | awk "{print \$1}")" = "$RAVEIL_TL_TOKEN_PATCH_SHA256" ]
  git -C "$build_root/chipyard/generators/rocket-chip" apply --check --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tl-token-metadata.patch
  git -C "$build_root/chipyard/generators/rocket-chip" apply --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tl-token-metadata.patch
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
  if [ "$RAVEIL_OWNED_CPU_MODE" = boom-load-lifecycle ]; then
    git -C "$build_root/chipyard/generators/boom" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-load-lifecycle.patch
    git -C "$build_root/chipyard/generators/boom" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-load-lifecycle.patch
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-misaligned-rollback ]; then
    git -C "$build_root/chipyard/generators/boom" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-misaligned-rollback.patch
    git -C "$build_root/chipyard/generators/boom" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-misaligned-rollback.patch
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-authorization ] ||
       [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ] ||
       [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
    git -C "$build_root/chipyard/generators/boom" apply --check \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-authorization.patch
    git -C "$build_root/chipyard/generators/boom" apply \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-authorization.patch
    if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ]; then
      git -C "$build_root/chipyard/generators/boom" apply --check --unidiff-zero \
        /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-token-handoff.patch
      git -C "$build_root/chipyard/generators/boom" apply --unidiff-zero \
        /repo/hardware/chisel/chipyard-patches/t-0042-boom-store-token-handoff.patch
    elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
      git -C "$build_root/chipyard/generators/boom" apply --check --unidiff-zero \
        /repo/hardware/chisel/chipyard-patches/t-0042-boom-token-fields-only.patch
      git -C "$build_root/chipyard/generators/boom" apply --unidiff-zero \
        /repo/hardware/chisel/chipyard-patches/t-0042-boom-token-fields-only.patch
    fi
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-postrequest-redirect ]; then
    git -C "$build_root/chipyard/generators/boom" apply --check --unidiff-zero \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-postrequest-redirect.patch
    git -C "$build_root/chipyard/generators/boom" apply --unidiff-zero \
      /repo/hardware/chisel/chipyard-patches/t-0042-boom-postrequest-redirect.patch
  fi
  git -C "$build_root/chipyard/generators/rocket-chip" apply --check --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch
  git -C "$build_root/chipyard/generators/rocket-chip" apply --unidiff-zero \
    /repo/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/rocket/HellaCache.scala" | awk "{print \$1}")" = "1672c56ad0cdaad15ac0184bf17193a5417bd949662793dec9cd1b8671cd8ad3" ]
  [ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Bundles.scala" | awk "{print \$1}")" = "f1f8190de5064a50ac184749c965b09259748f7e20954fe2566cdfced9c41586" ]
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
  if [ "$RAVEIL_OWNED_CPU_MODE" = boom-load-lifecycle ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "d96fa9f10ddc07c571826ef53638752ae78f967125d7a9199da3761227834e29" ]
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-misaligned-rollback ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "1a12fdf33d797d2ae961ea5a1874d158c555372ee4f040cccb671d01ffb544e8" ]
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-authorization ] ||
       [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "beaf195dfed4457315b14aad5cb054f09bc894a6a997d63467e5fec0570154fb" ]
    if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
      [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/dcache.scala" | awk "{print \$1}")" = "dfe116bdcd69f86d64c10fc29787870eb3244ec173e355c78b2ac0de49d8d1c5" ]
      [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala" | awk "{print \$1}")" = "bdbc7eae44feac0bc71cf1769dc89230ddc6623a8c3d0a4ce391c9f7c961f042" ]
      ! grep -q 'raveilTokenValid' "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala"
      ! grep -q 'raveilTokenValid' "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala"
    fi
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "fd57219554cea6be5c30dceed6b590f864cabdd4bf2d5a8db1729f362a258815" ]
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/dcache.scala" | awk "{print \$1}")" = "bb2f712f941368e7be57049fb99378520646054ce47ac31e45bda2ebc01a2f49" ]
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala" | awk "{print \$1}")" = "92210ec6fca1699c9083c5726363e7ec48dd4d995b6238c664ddb704a2a8c755" ]
  elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-postrequest-redirect ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "d4a331e3d69e62f22b72326b893a0b5f151ff16b153161f7a71b4f1493bb2165" ]
  else
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "1400d3997b94d1d5e4064d126d22aabd467905e1fd962896ac19cfbd1955371a" ]
  fi
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
[ "$(sha256sum "$build_root/chipyard/generators/rocket-chip/src/main/scala/tilelink/Bundles.scala" | awk "{print \$1}")" = "f1f8190de5064a50ac184749c965b09259748f7e20954fe2566cdfced9c41586" ]
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
if [ "$RAVEIL_OWNED_CPU_MODE" = boom-load-lifecycle ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "d96fa9f10ddc07c571826ef53638752ae78f967125d7a9199da3761227834e29" ]
elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-misaligned-rollback ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "1a12fdf33d797d2ae961ea5a1874d158c555372ee4f040cccb671d01ffb544e8" ]
elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-authorization ] ||
     [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "beaf195dfed4457315b14aad5cb054f09bc894a6a997d63467e5fec0570154fb" ]
  if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/dcache.scala" | awk "{print \$1}")" = "dfe116bdcd69f86d64c10fc29787870eb3244ec173e355c78b2ac0de49d8d1c5" ]
    [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala" | awk "{print \$1}")" = "bdbc7eae44feac0bc71cf1769dc89230ddc6623a8c3d0a4ce391c9f7c961f042" ]
    ! grep -q 'raveilTokenValid' "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala"
    ! grep -q 'raveilTokenValid' "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala"
  fi
elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "fd57219554cea6be5c30dceed6b590f864cabdd4bf2d5a8db1729f362a258815" ]
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/dcache.scala" | awk "{print \$1}")" = "bb2f712f941368e7be57049fb99378520646054ce47ac31e45bda2ebc01a2f49" ]
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/mshrs.scala" | awk "{print \$1}")" = "92210ec6fca1699c9083c5726363e7ec48dd4d995b6238c664ddb704a2a8c755" ]
elif [ "$RAVEIL_OWNED_CPU_MODE" = boom-postrequest-redirect ]; then
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "d4a331e3d69e62f22b72326b893a0b5f151ff16b153161f7a71b4f1493bb2165" ]
else
  [ "$(sha256sum "$build_root/chipyard/generators/boom/src/main/scala/lsu/lsu.scala" | awk "{print \$1}")" = "1400d3997b94d1d5e4064d126d22aabd467905e1fd962896ac19cfbd1955371a" ]
fi
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
  unexpected=$(git status --porcelain --untracked-files=all | grep -v "^?? target/" | grep -v "^ M src/main/scala/rocket/HellaCache.scala$" | grep -v "^ M src/main/scala/rocket/RocketCore.scala$" | grep -v "^ M src/main/scala/tilelink/Bundles.scala$" | grep -v "^ M src/main/scala/tilelink/Xbar.scala$" | grep -v "^ M src/main/scala/common/tile.scala$" | grep -v "^ M src/main/scala/lsu/lsu.scala$" | grep -v "^ M src/main/scala/lsu/dcache.scala$" | grep -v "^ M src/main/scala/lsu/mshrs.scala$" || true)
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
if [ "$RAVEIL_OWNED_CPU_MODE" = controlled-repeat ]; then
  repeated_elf="$build_root/riscv_stencil_repeated.elf"
  repeated_log="$build_root/riscv_stencil_repeated.log"
  serialize_define=
  if [ "$RAVEIL_CONTROLLED_SERIALIZE_DISPATCH" = 1 ]; then
    [ "$RAVEIL_OWNED_CPU_LABEL" = boom-serialize ] || {
      echo "error: serialize-dispatch is diagnostic BOOM-only" >&2
      exit 1
    }
    serialize_define=-DBOOM_SERIALIZE_DISPATCH=1
  fi
  riscv64-unknown-elf-gcc \
    -DRFC0005_SYSTEM_SCRATCHPAD=1 \
    -DRAVEIL_REPEAT_ACCOUNT="$RAVEIL_REPEAT_ACCOUNT" \
    -O2 -fno-strict-aliasing $serialize_define \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/riscv_stencil_system_scratchpad.ld \
    /repo/hardware/chisel/riscv_stencil_repeated.S \
    /repo/hardware/chisel/riscv_stencil_repeated.c \
    -o "$repeated_elf"
  [ "$(riscv64-unknown-elf-nm "$repeated_elf" | awk '\''$3 == "input_words" { print $1 }'\'')" = 0000000008000000 ]
  [ "$(riscv64-unknown-elf-nm "$repeated_elf" | awk '\''$3 == "output_words" { print $1 }'\'')" = 0000000008000510 ]
  artifact_sha256=$(sha256sum "$repeated_elf" | awk '\''{print $1}'\'')
  rm -f "$repeated_log"
  timeout --foreground 3600 "$sim" +permissive +verbose +permissive-off \
    "$repeated_elf" 2>&1 | tee "$repeated_log"
  # Force the verbose named-volume log visible before strict verification.
  sync "$repeated_log"
  if [ "$RAVEIL_OWNED_CPU_LABEL" = rocket ]; then
    implementation=rocket-in-order
  else
    implementation=boom-ooo
  fi
  diagnostic_arg=
  if [ "$RAVEIL_OWNED_CPU_LABEL" = boom-serialize ]; then
    diagnostic_arg=--diagnostic-only
  fi
  python3 -m raveil.t0044_repeated verify-cpu \
    --log "$repeated_log" \
    --implementation "$implementation" \
    --account "$RAVEIL_REPEAT_ACCOUNT" \
    --source-sha256 "$RAVEIL_SOURCE_SHA256" \
    --artifact-sha256 "$artifact_sha256" \
    --toolchain-sha256 "$RAVEIL_TOOLCHAIN_SHA256" \
    --implementation-configuration "$RAVEIL_OWNED_CPU_CONFIG_FQ" \
    $diagnostic_arg
  printf "RAVEIL-REPEATED-CPU-HOST-V1 status=OK cpu=%s config=%s account=%s simulator_processes=1 resets=1 artifact_reloads=0 serialize_dispatch=%s source_sha256=%s artifact_sha256=%s toolchain_sha256=%s cache_source_sha256=%s build_input_sha256=%s resource_sha256=16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748 workload=frozen-rfc-0005 oracle=independent-host accounting=complete evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" \
    "$RAVEIL_REPEAT_ACCOUNT" "$RAVEIL_CONTROLLED_SERIALIZE_DISPATCH" \
    "$RAVEIL_SOURCE_SHA256" "$artifact_sha256" "$RAVEIL_TOOLCHAIN_SHA256" \
    "$RAVEIL_CACHE_SOURCE_SHA256" "$RAVEIL_INPUT_SHA256"
  exit 0
fi
if [ "$RAVEIL_OWNED_CPU_MODE" = controlled ]; then
  controlled_elf="$build_root/riscv_stencil_controlled.elf"
  controlled_signature="$build_root/riscv_stencil_controlled.signature"
  controlled_log="$build_root/riscv_stencil_controlled.log"
  serialize_define=
  if [ "$RAVEIL_CONTROLLED_SERIALIZE_DISPATCH" = 1 ]; then
    [ "$RAVEIL_OWNED_CPU_LABEL" = boom-serialize ] || {
      echo "error: serialize-dispatch is diagnostic BOOM-only" >&2
      exit 1
    }
    serialize_define=-DBOOM_SERIALIZE_DISPATCH=1
  fi
  riscv64-unknown-elf-gcc \
    -DRFC0005_SYSTEM_SCRATCHPAD=1 -O2 -fno-strict-aliasing \
    -DRAVEIL_STENCIL_SEED="$RAVEIL_CONTROLLED_SEED" $serialize_define \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/riscv_stencil_system_scratchpad.ld \
    /repo/hardware/chisel/riscv_stencil_smoke.S \
    /repo/hardware/chisel/riscv_stencil_smoke.c \
    -o "$controlled_elf"
  [ "$(riscv64-unknown-elf-nm "$controlled_elf" | awk '\''$3 == "input_words" { print $1 }'\'')" = 0000000008000000 ]
  [ "$(riscv64-unknown-elf-nm "$controlled_elf" | awk '\''$3 == "begin_signature" { print $1 }'\'')" = 0000000008000510 ]
  artifact_sha256=$(sha256sum "$controlled_elf" | awk '\''{print $1}'\'')
  rm -f "$controlled_signature" "$controlled_log"
  timeout --foreground 600 "$sim" +permissive +verbose \
    +signature="$controlled_signature" +signature-granularity=4 +permissive-off \
    "$controlled_elf" 2>&1 | tee "$controlled_log"
  python3 -m raveil.riscv_stencil_signature \
    --signature "$controlled_signature" --seed "$RAVEIL_CONTROLLED_SEED"
  if [ "$RAVEIL_OWNED_CPU_LABEL" = rocket ]; then
    implementation=rocket-in-order
  else
    implementation=boom-ooo
  fi
  python3 -m raveil.controlled_run \
    --verify-cpu-log "$controlled_log" \
    --signature "$controlled_signature" \
    --implementation "$implementation" \
    --invocation "$RAVEIL_CONTROLLED_INVOCATION" \
    --seed "$RAVEIL_CONTROLLED_SEED" \
    --source-sha256 "$RAVEIL_SOURCE_SHA256" \
    --artifact-sha256 "$artifact_sha256" \
    --toolchain-sha256 "$RAVEIL_TOOLCHAIN_SHA256" \
    --implementation-configuration "$RAVEIL_OWNED_CPU_CONFIG_FQ"
  printf "CONTROLLED-CPU-STENCIL-HOST-V1 status=OK cpu=%s config=%s seed=%s invocation=%s serialize_dispatch=%s source_sha256=%s artifact_sha256=%s toolchain_sha256=%s cache_source_sha256=%s build_input_sha256=%s resource_sha256=16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748 workload=frozen-rfc-0005 oracle=independent-host accounting=complete traffic_conservation=verified resource_contract_verified=1 resource_equality_verified=0 comparison_eligible=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_LABEL" "$RAVEIL_OWNED_CPU_CONFIG_FQ" \
    "$RAVEIL_CONTROLLED_SEED" "$RAVEIL_CONTROLLED_INVOCATION" \
    "$RAVEIL_CONTROLLED_SERIALIZE_DISPATCH" \
    "$RAVEIL_SOURCE_SHA256" "$artifact_sha256" "$RAVEIL_TOOLCHAIN_SHA256" \
    "$RAVEIL_CACHE_SOURCE_SHA256" "$RAVEIL_INPUT_SHA256"
  exit 0
fi
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

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-load-lifecycle ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_load_lifecycle.S \
    -o "$build_root/owned_memory_boom_load_lifecycle.elf"
  boom_lifecycle_signature="$build_root/owned_memory_boom_load_lifecycle.signature"
  boom_lifecycle_log="$build_root/owned_memory_boom_load_lifecycle.log"
  rm -f "$boom_lifecycle_signature" "$boom_lifecycle_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_lifecycle_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_load_lifecycle.elf" 2>&1 | tee "$boom_lifecycle_log"
  python3 /repo/hardware/chisel/verify_owned_boom_load_lifecycle.py \
    "$boom_lifecycle_log" "$boom_lifecycle_signature"
  printf "OWNED-BOOM-LOAD-LIFECYCLE-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=boom-pinned cpu_execution=rtl-simulation request_response_rob_retirement=covered transport_token_correlation=not-carried semantic_initiator=not-proven store_authorization=not-run general_boom_lifecycle=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-misaligned-rollback ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_misaligned_rollback.S \
    -o "$build_root/owned_memory_boom_misaligned_rollback.elf"
  boom_negative_signature="$build_root/owned_memory_boom_misaligned_rollback.signature"
  boom_negative_log="$build_root/owned_memory_boom_misaligned_rollback.log"
  rm -f "$boom_negative_signature" "$boom_negative_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_negative_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_misaligned_rollback.elf" 2>&1 | tee "$boom_negative_log"
  python3 /repo/hardware/chisel/verify_owned_boom_misaligned_rollback.py \
    "$boom_negative_log" "$boom_negative_signature"
  printf "OWNED-BOOM-MISALIGNED-ROLLBACK-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=boom-pinned cpu_execution=rtl-simulation request_boundary=after-exception-before-rollback post_exception_request=observed postrequest_exception=not-covered response_seen=0 rob_rollback_state=observed matching_rbk=0 transport_token_correlation=not-carried semantic_initiator=not-proven general_rollback=not-proven store_authorization=not-run resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-handoff ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_store_authorization.S \
    -o "$build_root/owned_memory_boom_store_token_handoff.elf"
  boom_store_token_signature="$build_root/owned_memory_boom_store_token_handoff.signature"
  boom_store_token_log="$build_root/owned_memory_boom_store_token_handoff.log"
  rm -f "$boom_store_token_signature" "$boom_store_token_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_store_token_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_store_token_handoff.elf" 2>&1 | tee "$boom_store_token_log"
  python3 /repo/hardware/chisel/verify_owned_boom_store_token_handoff.py \
    "$boom_store_token_log" "$boom_store_token_signature"
  printf "OWNED-BOOM-STORE-TOKEN-HANDOFF-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=boom-pinned cpu_execution=rtl-simulation store_authorization=observed boom_local_request_response_clear=observed manager_put_a_d=observed transport_token_correlation=same-token-observed store_attribution=bounded-same-token-observed malformed_metadata=fail-closed semantic_initiator=not-promoted general_store_lifecycle=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-token-default-invalid ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_store_authorization.S \
    -o "$build_root/owned_memory_boom_store_token_default_invalid.elf"
  boom_store_default_invalid_signature="$build_root/owned_memory_boom_store_token_default_invalid.signature"
  boom_store_default_invalid_log="$build_root/owned_memory_boom_store_token_default_invalid.log"
  rm -f "$boom_store_default_invalid_signature" "$boom_store_default_invalid_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_store_default_invalid_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_store_token_default_invalid.elf" 2>&1 | tee "$boom_store_default_invalid_log"
  python3 /repo/hardware/chisel/verify_owned_boom_store_authorization.py \
    "$boom_store_default_invalid_log" "$boom_store_default_invalid_signature"
  python3 /repo/hardware/chisel/verify_owned_boom_store_token_default_invalid.py \
    "$boom_store_default_invalid_log"
  printf "OWNED-BOOM-STORE-TOKEN-DEFAULT-INVALID-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s patch_manifest=%s event_source=boom-pinned cpu_execution=rtl-simulation store_authorization=observed manager_put_a_d=observed producer=absent-negotiated-default metadata_default_invalid=observed token_classification=unknown-default-invalid semantic_attribution=not-promoted manager_transaction=completed store_side_effect_readback=observed semantic_initiator=not-promoted stripped_after_valid=not-proven general_missing_metadata=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)" "$RAVEIL_APPLIED_PATCH_MANIFEST"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-store-authorization ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_store_authorization.S \
    -o "$build_root/owned_memory_boom_store_authorization.elf"
  boom_store_signature="$build_root/owned_memory_boom_store_authorization.signature"
  boom_store_log="$build_root/owned_memory_boom_store_authorization.log"
  rm -f "$boom_store_signature" "$boom_store_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_store_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_store_authorization.elf" 2>&1 | tee "$boom_store_log"
  python3 /repo/hardware/chisel/verify_owned_boom_store_authorization.py \
    "$boom_store_log" "$boom_store_signature"
  printf "OWNED-BOOM-STORE-AUTHORIZATION-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=boom-pinned cpu_execution=rtl-simulation store_authorization=observed boom_local_request_response_clear=observed manager_put_a_d=independently-observed manager_a_d_source_correlation=observed transport_token_correlation=not-carried store_attribution=not-proven semantic_initiator=not-proven general_store_lifecycle=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
    "$RAVEIL_OWNED_CPU_CONFIG_FQ" "$RAVEIL_INPUT_SHA256" "$RAVEIL_SOURCE_SHA256" \
    "$(sha256sum "$graph" | cut -c1-64)"
  exit 0
fi

if [ "$RAVEIL_OWNED_CPU_MODE" = boom-postrequest-redirect ]; then
  riscv64-unknown-elf-gcc \
    -march=rv64imafd_zicsr -mabi=lp64d -mcmodel=medany \
    -nostdlib -nostartfiles -static -Wl,--no-relax \
    -T /repo/hardware/chisel/boom_functional_smoke.ld \
    /repo/hardware/chisel/owned_memory_boom_postrequest_redirect.S \
    -o "$build_root/owned_memory_boom_postrequest_redirect.elf"
  [ "$(riscv64-unknown-elf-nm "$build_root/owned_memory_boom_postrequest_redirect.elf" | awk '\''$3 == "wrong_path_load" { print $1 }'\'')" = 0000000080000048 ]
  boom_redirect_signature="$build_root/owned_memory_boom_postrequest_redirect.signature"
  boom_redirect_log="$build_root/owned_memory_boom_postrequest_redirect.log"
  rm -f "$boom_redirect_signature" "$boom_redirect_log"
  timeout --foreground 180 "$sim" +permissive +verbose \
    +signature="$boom_redirect_signature" +signature-granularity=4 +permissive-off \
    "$build_root/owned_memory_boom_postrequest_redirect.elf" 2>&1 | tee "$boom_redirect_log"
  python3 /repo/hardware/chisel/verify_owned_boom_postrequest_redirect.py \
    "$boom_redirect_log" "$boom_redirect_signature"
  printf "OWNED-BOOM-POSTREQUEST-REDIRECT-HOST-V1 status=OK cpu=boom config=%s input_sha256=%s source_sha256=%s graph_sha256=%s event_source=boom-pinned cpu_execution=rtl-simulation memory_class=cacheable-dram owned_manager=not-exercised request_before_redirect=observed response_before_redirect=observed branch_kill=observed promotion=blocked post_tl_a_redirect=not-proven transport_cancellation=not-proven side_effect_absence=not-proven transport_token_correlation=not-carried semantic_initiator=not-proven general_rollback=not-proven resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured\n" \
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
