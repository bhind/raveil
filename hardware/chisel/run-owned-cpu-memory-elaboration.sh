#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
origin_overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
rocket_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch"
boom_hook_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-boom-dcache-origin-hook.patch"
xbar_request_patch="$repo_root/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch"
dockerfile="$repo_root/hardware/chisel/Dockerfile.boom"
image=raveil-boom-project-compile:v1
platform=linux/amd64

[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-elaboration-deps.sh first' >&2
    exit 1
}
for input in "$overlay" "$origin_overlay" "$rocket_hook_patch" "$boom_hook_patch" "$xbar_request_patch" "$dockerfile"; do
    [ -f "$input" ] || {
        echo "error: required owned CPU elaboration input is missing: $input" >&2
        exit 1
    }
done
command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

"$repo_root/hardware/chisel/verify-boom-reference.sh"
[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: Chipyard checkout or initialized dependency is not exact and clean' >&2
    exit 1
}

overlay_sha256=$(shasum -a 256 "$overlay" | awk '{print $1}')
origin_overlay_sha256=$(shasum -a 256 "$origin_overlay" | awk '{print $1}')
rocket_hook_patch_sha256=$(shasum -a 256 "$rocket_hook_patch" | awk '{print $1}')
boom_hook_patch_sha256=$(shasum -a 256 "$boom_hook_patch" | awk '{print $1}')
xbar_request_patch_sha256=$(shasum -a 256 "$xbar_request_patch" | awk '{print $1}')
dockerfile_sha256=$(shasum -a 256 "$dockerfile" | awk '{print $1}')

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom" \
    --tag "$image" \
    "$repo_root"

printf 'OWNED-CPU-MEMORY-ELABORATION-HOST-V2 image=%s platform=%s overlay_sha256=%s origin_overlay_sha256=%s rocket_hook_patch_sha256=%s boom_hook_patch_sha256=%s xbar_request_patch_sha256=%s dockerfile_sha256=%s source_copy=ephemeral evidence=rtl-elaboration-functional execution=not-run performance=not-measured\n' \
    "$image" "$platform" "$overlay_sha256" "$origin_overlay_sha256" \
    "$rocket_hook_patch_sha256" "$boom_hook_patch_sha256" "$xbar_request_patch_sha256" "$dockerfile_sha256"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=bind,source=$overlay,target=/overlay/RaveilOwnedTLMemory.scala,readonly" \
    --mount "type=bind,source=$origin_overlay,target=/overlay/RaveilDCacheOriginTagger.scala,readonly" \
    --mount "type=bind,source=$rocket_hook_patch,target=/patches/rocket.patch,readonly" \
    --mount "type=bind,source=$boom_hook_patch,target=/patches/boom.patch,readonly" \
    --mount "type=bind,source=$xbar_request_patch,target=/patches/xbar.patch,readonly" \
    --env "RAVEIL_OVERLAY_SHA256=$overlay_sha256" \
    --env "RAVEIL_ORIGIN_OVERLAY_SHA256=$origin_overlay_sha256" \
    --env "RAVEIL_ROCKET_HOOK_PATCH_SHA256=$rocket_hook_patch_sha256" \
    --env "RAVEIL_BOOM_HOOK_PATCH_SHA256=$boom_hook_patch_sha256" \
    --env "RAVEIL_XBAR_REQUEST_PATCH_SHA256=$xbar_request_patch_sha256" \
    --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/root/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/root/.sbt \
    "$image" \
    sh -c 'set -eu
cp -a /source /work/chipyard
cd /work/chipyard
[ "$(sha256sum generators/rocket-chip/src/main/scala/rocket/HellaCache.scala | awk "{print \$1}")" = "d7ce4d0fd84c118fc0db36254f98889b509b6070d1d48dfbc52bb7139a8ca6d2" ]
[ "$(sha256sum generators/boom/src/main/scala/common/tile.scala | awk "{print \$1}")" = "570d48ccd0978b55ea9aba77af4a6b8280194d09e2e6c3f018dbe963ec65a9dc" ]
[ "$(sha256sum generators/rocket-chip/src/main/scala/tilelink/Xbar.scala | awk "{print \$1}")" = "7ef8f49ccb3b8df8ba3860d1a54d1eee6d964431b77aa147dd2511f97fe3a613" ]
[ "$(sha256sum /patches/rocket.patch | awk "{print \$1}")" = "$RAVEIL_ROCKET_HOOK_PATCH_SHA256" ]
[ "$(sha256sum /patches/boom.patch | awk "{print \$1}")" = "$RAVEIL_BOOM_HOOK_PATCH_SHA256" ]
[ "$(sha256sum /patches/xbar.patch | awk "{print \$1}")" = "$RAVEIL_XBAR_REQUEST_PATCH_SHA256" ]
git -C generators/rocket-chip apply --check --unidiff-zero /patches/rocket.patch
git -C generators/rocket-chip apply --unidiff-zero /patches/rocket.patch
git -C generators/boom apply --check --unidiff-zero /patches/boom.patch
git -C generators/boom apply --unidiff-zero /patches/boom.patch
git -C generators/rocket-chip apply --check --unidiff-zero /patches/xbar.patch
git -C generators/rocket-chip apply --unidiff-zero /patches/xbar.patch
[ "$(sha256sum generators/rocket-chip/src/main/scala/rocket/HellaCache.scala | awk "{print \$1}")" = "1672c56ad0cdaad15ac0184bf17193a5417bd949662793dec9cd1b8671cd8ad3" ]
[ "$(sha256sum generators/boom/src/main/scala/common/tile.scala | awk "{print \$1}")" = "2f25f75be69e2dc05c12137e35415224a950306cfbd19a0b2c1d071087bee9d6" ]
[ "$(sha256sum generators/rocket-chip/src/main/scala/tilelink/Xbar.scala | awk "{print \$1}")" = "4867e293671c4df061637b01f358772595c0ec0efff359deeacb8572dde4cbe2" ]
[ "$(sha256sum /overlay/RaveilOwnedTLMemory.scala | awk "{print \$1}")" = "$RAVEIL_OVERLAY_SHA256" ]
[ "$(sha256sum /overlay/RaveilDCacheOriginTagger.scala | awk "{print \$1}")" = "$RAVEIL_ORIGIN_OVERLAY_SHA256" ]
install -D -m 0444 /overlay/RaveilOwnedTLMemory.scala \
  generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala
install -D -m 0444 /overlay/RaveilDCacheOriginTagger.scala \
  generators/chipyard/src/main/scala/raveil/RaveilDCacheOriginTagger.scala
java -Xmx8G -jar scripts/sbt-launch.jar "project chipyard" assembly
assembly=$(find generators/chipyard/target -type f -name "*assembly*.jar" -print | head -n 1)
[ -n "$assembly" ] || { echo "error: chipyard assembly jar was not produced" >&2; exit 1; }
mkdir -p /work/generated-owned-rocket /work/generated-owned-boom
for target in rocket boom; do
  if [ "$target" = rocket ]; then
    config=chipyard.raveil.RaveilOwnedRocketConfig
  else
    config=chipyard.raveil.RaveilOwnedSmallBoomConfig
  fi
  output=/work/generated-owned-$target
  cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv64.img "$output/bootrom.rv64.img"
  cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv32.img "$output/bootrom.rv32.img"
  java -Xmx8G -cp "$assembly" chipyard.Generator \
    --target-dir "$output" \
    --name "chipyard.harness.TestHarness.$config" \
    --top-module chipyard.harness.TestHarness \
    --legacy-configs "chipyard:$config"
  fir=$(find "$output" -maxdepth 1 -type f -name "*.fir" -print | head -n 1)
  anno=$(find "$output" -maxdepth 1 -type f -name "*.anno.json" -print | head -n 1)
  [ -s "$fir" ] || { echo "error: $target FIRRTL was not emitted" >&2; exit 1; }
  [ -s "$anno" ] || { echo "error: $target annotations were not emitted" >&2; exit 1; }
  grep -q "RaveilOwnedTLMemory" "$fir" || { echo "error: $target owned memory is absent" >&2; exit 1; }
  grep -q "RaveilDCacheOriginTagger" "$fir" || { echo "error: $target DCache-origin tagger is absent" >&2; exit 1; }
  if [ "$target" = rocket ]; then
    grep -q "Rocket" "$fir" || { echo "error: Rocket core is absent" >&2; exit 1; }
  else
    grep -q "BoomCore" "$fir" || { echo "error: BOOM core is absent" >&2; exit 1; }
  fi
  printf "OWNED-CPU-MEMORY-ELABORATION-V2 status=OK target=%s config=%s bus=pbus-uncached data_base=0x08000000 data_size=65536 control_base=0x08010000 data_width=32 outstanding=1 phase_register=present phase_attribution=software-declared dcache_origin_path=structurally-elaborated initiator_attribution=unverified semantic_initiator=not-proven may_deny_put=1 execution=not-run resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-elaboration-functional performance=not-measured\n" \
    "$target" "$config"
done'
