#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
image=raveil-boom-project-compile:v1
platform=linux/amd64

[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-elaboration-deps.sh first' >&2
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

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom" \
    --tag "$image" \
    "$repo_root"

printf 'BOOM-ELABORATION-HOST-V1 image=%s platform=%s source_copy=ephemeral dependency_resolution=maven-coordinate-not-lockfile apt_packages=unlocked evidence=rtl-elaboration-functional performance=not-measured\n' \
    "$image" "$platform"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/root/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/root/.sbt \
    "$image" \
    sh -c 'set -eu
cp -a /source /work/chipyard
cd /work/chipyard
dtc --version
java -Xmx8G -jar scripts/sbt-launch.jar "project chipyard" assembly
assembly=$(find generators/chipyard/target -type f -name "*assembly*.jar" -print | head -n 1)
[ -n "$assembly" ] || { echo "error: chipyard assembly jar was not produced" >&2; exit 1; }
mkdir -p /work/generated-boom
cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv64.img \
  /work/generated-boom/bootrom.rv64.img
cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv32.img \
  /work/generated-boom/bootrom.rv32.img
java -Xmx8G -cp "$assembly" chipyard.Generator \
  --target-dir /work/generated-boom \
  --name chipyard.harness.TestHarness.chipyard.SmallBoomConfig \
  --top-module chipyard.harness.TestHarness \
  --legacy-configs chipyard:SmallBoomConfig
fir=$(find /work/generated-boom -maxdepth 1 -type f -name "*.fir" -print | head -n 1)
anno=$(find /work/generated-boom -maxdepth 1 -type f -name "*.anno.json" -print | head -n 1)
[ -s "$fir" ] || { echo "error: BOOM FIRRTL was not emitted" >&2; exit 1; }
[ -s "$anno" ] || { echo "error: BOOM annotations were not emitted" >&2; exit 1; }
grep -q "BoomCore" "$fir" || { echo "error: emitted FIRRTL does not contain BoomCore" >&2; exit 1; }
printf "BOOM-ELABORATION-V1 status=OK config=chipyard.SmallBoomConfig output=firrtl boom_core=present evidence=rtl-elaboration-functional execution=not-run performance=not-measured\n"'
