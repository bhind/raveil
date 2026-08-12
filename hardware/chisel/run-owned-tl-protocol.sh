#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
runner="$repo_root/hardware/chisel/run-owned-tl-protocol.sh"
memory_overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
harness_overlay="$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLProtocolHarness.scala"
driver="$repo_root/hardware/chisel/owned_tl_protocol_sim_main.cpp"
dockerfile="$repo_root/hardware/chisel/Dockerfile.owned-tl"
image=raveil-owned-tl-protocol:v1
platform=linux/amd64

for input in "$runner" "$memory_overlay" "$harness_overlay" "$driver" "$dockerfile"; do
    [ -f "$input" ] || {
        echo "error: required owned TL protocol input is missing: $input" >&2
        exit 1
    }
done
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

input_sha256=$(
    shasum -a 256 "$runner" "$memory_overlay" "$harness_overlay" "$driver" "$dockerfile" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)
overlay_sha256=$(
    shasum -a 256 "$memory_overlay" "$harness_overlay" |
        awk '{print $1}' |
        shasum -a 256 |
        awk '{print $1}'
)

docker build \
    --platform "$platform" \
    --provenance=false \
    --file "$dockerfile" \
    --tag "$image" \
    "$repo_root"
image_id=$(docker image inspect --format '{{.Id}}' "$image")
chipyard_revision=$(git -C "$chipyard" rev-parse HEAD)
assembly_key=$(
    printf '%s\n%s\n%s\n' \
        "$overlay_sha256" "$chipyard_revision" "$image_id" |
        shasum -a 256 |
        awk '{print $1}'
)

printf 'OWNED-TL-PROTOCOL-HOST-V2 image=%s image_id=%s platform=%s input_sha256=%s overlay_sha256=%s chipyard_revision=%s assembly_key=%s source_copy=ephemeral assembly_cache=content-addressed-verified cpu_execution=not-run semantic_initiator=not-proven resource_match_verified=0 evidence=rtl-simulation-functional performance=not-measured\n' \
    "$image" "$image_id" "$platform" "$input_sha256" "$overlay_sha256" \
    "$chipyard_revision" "$assembly_key"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=bind,source=$memory_overlay,target=/overlay/RaveilOwnedTLMemory.scala,readonly" \
    --mount "type=bind,source=$harness_overlay,target=/overlay/RaveilOwnedTLProtocolHarness.scala,readonly" \
    --mount "type=bind,source=$driver,target=/overlay/owned_tl_protocol_sim_main.cpp,readonly" \
    --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/root/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/root/.sbt \
    --mount type=volume,source=raveil-owned-tl-assembly-v1,target=/assembly-cache \
    --env "RAVEIL_ASSEMBLY_KEY=$assembly_key" \
    "$image" \
    sh -c 'set -eu
cp -a /source /work/chipyard
cd /work/chipyard
install -D -m 0444 /overlay/RaveilOwnedTLMemory.scala \
  generators/chipyard/src/main/scala/raveil/RaveilOwnedTLMemory.scala
install -D -m 0444 /overlay/RaveilOwnedTLProtocolHarness.scala \
  generators/chipyard/src/main/scala/raveil/RaveilOwnedTLProtocolHarness.scala
assembly_dir=/assembly-cache/$RAVEIL_ASSEMBLY_KEY
assembly=$assembly_dir/chipyard-assembly.jar
assembly_checksum=$assembly_dir/chipyard-assembly.jar.sha256
if [ -e "$assembly" ] || [ -e "$assembly_checksum" ]; then
  [ -s "$assembly" ] && [ -s "$assembly_checksum" ] || {
    echo "error: cached assembly is incomplete" >&2
    exit 1
  }
  (cd "$assembly_dir" && sha256sum -c chipyard-assembly.jar.sha256)
else
  java -Xmx6G -Dsbt.task.cpus=2 -jar scripts/sbt-launch.jar "project chipyard" assembly
  built_assembly=$(find generators/chipyard/target -type f -name "*assembly*.jar" -print | head -n 1)
  [ -n "$built_assembly" ] || { echo "error: chipyard assembly jar was not produced" >&2; exit 1; }
  mkdir "$assembly_dir"
  install -m 0444 "$built_assembly" "$assembly"
  (cd "$assembly_dir" && sha256sum chipyard-assembly.jar > chipyard-assembly.jar.sha256)
fi
[ -s "$assembly" ] || { echo "error: chipyard assembly jar was not produced" >&2; exit 1; }
output=/work/generated-owned-tl-protocol
mkdir -p "$output"
java -Xmx8G -cp "$assembly" chipyard.Generator \
  --target-dir "$output" \
  --name chipyard.raveil.RaveilOwnedTLProtocolHarness \
  --top-module chipyard.raveil.RaveilOwnedTLProtocolHarness \
  --legacy-configs chipyard:chipyard.RocketConfig
fir=$(find "$output" -maxdepth 1 -type f -name "*.fir" -print | head -n 1)
anno=$(find "$output" -maxdepth 1 -type f -name "*.anno.json" -print | head -n 1)
[ -s "$fir" ] || { echo "error: protocol harness FIRRTL was not emitted" >&2; exit 1; }
[ -s "$anno" ] || { echo "error: protocol harness annotations were not emitted" >&2; exit 1; }
verilog="$output/RaveilOwnedTLProtocolHarness.v"
java -Xmx8G -cp "$assembly" firrtl.stage.FirrtlMain \
  -i "$fir" \
  -o "$verilog" \
  -td "$output" \
  -faf "$anno" \
  -X verilog
[ -s "$verilog" ] || { echo "error: protocol harness Verilog was not emitted" >&2; exit 1; }
verilator --assert --cc "$verilog" \
  generators/rocket-chip/src/main/resources/vsrc/plusarg_reader.v \
  --exe /overlay/owned_tl_protocol_sim_main.cpp \
  --build \
  --Mdir "$output/verilator" \
  --top-module RaveilOwnedTLProtocolHarness \
  -CFLAGS "-std=c++17 -Wall -Wextra -Werror"
"$output/verilator/VRaveilOwnedTLProtocolHarness"'
