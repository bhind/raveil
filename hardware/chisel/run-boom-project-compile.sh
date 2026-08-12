#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
image=raveil-boom-project-compile:v1
platform=linux/amd64

[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-reference.sh first' >&2
    exit 1
}
command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}

"$repo_root/hardware/chisel/verify-boom-reference.sh"

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom" \
    --tag "$image" \
    "$repo_root"

printf 'BOOM-PROJECT-COMPILE-HOST-V1 image=%s platform=%s source_copy=ephemeral dependency_resolution=maven-coordinate-not-lockfile apt_packages=unlocked evidence=rtl-source-functional performance=not-measured\n' \
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
java -version
git --version
java -jar scripts/sbt-launch.jar "project boom" compile
printf "BOOM-PROJECT-COMPILE-V1 status=OK config=chipyard.SmallBoomConfig scope=scala-project evidence=rtl-source-functional elaboration=not-run performance=not-measured\n"'
