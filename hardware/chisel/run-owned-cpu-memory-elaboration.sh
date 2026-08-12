#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
image=raveil-boom-project-compile:v1
platform=linux/amd64

[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-elaboration-deps.sh first' >&2
    exit 1
}
[ -f "$overlay" ] || {
    echo 'error: owned CPU memory overlay is missing' >&2
    exit 1
}
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

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom" \
    --tag "$image" \
    "$repo_root"

printf 'OWNED-CPU-MEMORY-ELABORATION-HOST-V1 image=%s platform=%s overlay_sha256=%s source_copy=ephemeral evidence=rtl-elaboration-functional execution=not-run performance=not-measured\n' \
    "$image" "$platform" "$overlay_sha256"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=bind,source=$overlay,target=/overlay/RaveilOwnedTLMemory.scala,readonly" \
    --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/root/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/root/.sbt \
    "$image" \
    sh -c 'set -eu
cp -a /source /work/chipyard
cd /work/chipyard
install -D -m 0444 /overlay/RaveilOwnedTLMemory.scala \
  generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala
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
  if [ "$target" = rocket ]; then
    grep -q "Rocket" "$fir" || { echo "error: Rocket core is absent" >&2; exit 1; }
  else
    grep -q "BoomCore" "$fir" || { echo "error: BOOM core is absent" >&2; exit 1; }
  fi
  printf "OWNED-CPU-MEMORY-ELABORATION-V1 status=OK target=%s config=%s bus=pbus-uncached data_base=0x08000000 data_size=65536 control_base=0x08010000 data_width=32 outstanding=1 phase_register=present phase_attribution=software-declared initiator_attribution=unverified may_deny_put=1 execution=not-run resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-elaboration-functional performance=not-measured\n" \
    "$target" "$config"
done'
