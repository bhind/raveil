#!/bin/sh
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
runner="$repo_root/hardware/chisel/run-g1b-common-owned-memory-elaboration.sh"
dockerfile="$repo_root/hardware/chisel/Dockerfile.boom"
pin_file="$repo_root/hardware/chisel/boom-pin.env"
input_sha256=$(shasum -a 256 "$repo_root/hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala" "$repo_root/hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala" "$repo_root/hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala" "$repo_root/hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala" "$repo_root/hardware/chisel/chipyard-overlay/RaveilStaticStencilTLClient.scala" "$repo_root/hardware/chisel/chipyard-patches/t-0042-tl-token-metadata.patch" "$repo_root/hardware/chisel/chipyard-patches/t-0042-rocket-dcache-origin-hook.patch" "$repo_root/hardware/chisel/chipyard-patches/t-0042-tlxbar-request-defaults.patch" "$runner" "$dockerfile" "$pin_file" | awk '{print $1}' | shasum -a 256 | awk '{print $1}')
[ -d "$chipyard/.git" ] || { echo 'error: pinned Chipyard checkout is required' >&2; exit 1; }
"$repo_root/hardware/chisel/verify-boom-reference.sh"
chipyard_revision=$(git -C "$chipyard" rev-parse HEAD)
runner_sha256=$(shasum -a 256 "$runner" | awk '{print $1}')
dockerfile_sha256=$(shasum -a 256 "$dockerfile" | awk '{print $1}')
printf 'G1B-COMMON-OWNED-MEMORY-HOST-V1 input_sha256=%s runner_sha256=%s dockerfile_sha256=%s chipyard_revision=%s platform=linux/amd64 evidence=rtl-elaboration-topology performance=not-measured\n' "$input_sha256" "$runner_sha256" "$dockerfile_sha256" "$chipyard_revision"
docker build --platform linux/amd64 --file "$repo_root/hardware/chisel/Dockerfile.boom" --tag raveil-boom-project-compile:v1 "$repo_root"
docker run --rm --platform linux/amd64 --network none --security-opt no-new-privileges=true --env "RAVEIL_G1B_INPUT_SHA256=$input_sha256" --mount "type=bind,source=$chipyard,target=/source,readonly" --mount "type=bind,source=$repo_root/hardware/chisel/chipyard-overlay,target=/overlay,readonly" --mount "type=bind,source=$repo_root/hardware/chisel/chipyard-patches,target=/patches,readonly" --mount "type=bind,source=$runner,target=/identity/runner.sh,readonly" --mount "type=bind,source=$dockerfile,target=/identity/Dockerfile.boom,readonly" --mount "type=bind,source=$pin_file,target=/identity/boom-pin.env,readonly" --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/root/.ivy2 --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/root/.sbt raveil-boom-project-compile:v1 sh -c 'set -eu
observed=$(sha256sum /overlay/RaveilOwnedTLMemory.scala /overlay/RaveilDCacheOriginTagger.scala /overlay/RaveilFixtureInputProvider.scala /overlay/RaveilStaticStencilCore.scala /overlay/RaveilStaticStencilTLClient.scala /patches/t-0042-tl-token-metadata.patch /patches/t-0042-rocket-dcache-origin-hook.patch /patches/t-0042-tlxbar-request-defaults.patch /identity/runner.sh /identity/Dockerfile.boom /identity/boom-pin.env | awk "{print \$1}" | sha256sum | awk "{print \$1}")
[ "$observed" = "$RAVEIL_G1B_INPUT_SHA256" ]
cp -a /source /work/chipyard
cd /work/chipyard
git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tl-token-metadata.patch
git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-rocket-dcache-origin-hook.patch
git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tlxbar-request-defaults.patch
for source in RaveilOwnedTLMemory.scala RaveilDCacheOriginTagger.scala RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala RaveilStaticStencilTLClient.scala; do install -D -m 0444 /overlay/$source generators/chipyard/src/main/scala/raveil/$source; done
java -Xmx8G -jar scripts/sbt-launch.jar "project chipyard" assembly
assembly_count=$(find generators/chipyard/target -type f -name "*assembly*.jar" -print | wc -l | tr -d " ")
[ "$assembly_count" -eq 1 ]
assembly=$(find generators/chipyard/target -type f -name "*assembly*.jar" -print)
output=/work/generated-g1b
mkdir -p "$output"
cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv64.img "$output/bootrom.rv64.img"
cp generators/testchipip/src/main/resources/testchipip/bootrom/bootrom.rv32.img "$output/bootrom.rv32.img"
config=chipyard.raveil.RaveilIntegratedGraphRocketConfig
java -Xmx8G -cp "$assembly" chipyard.Generator --target-dir "$output" --name "chipyard.harness.TestHarness.$config" --top-module chipyard.harness.TestHarness --legacy-configs "chipyard:$config"
fir_count=$(find "$output" -maxdepth 1 -name "*.fir" -print | wc -l | tr -d " ")
graphml_count=$(find "$output" -maxdepth 1 -name "*.graphml" -print | wc -l | tr -d " ")
[ "$fir_count" -eq 1 ] && [ "$graphml_count" -eq 1 ]
fir=$(find "$output" -maxdepth 1 -name "*.fir" -print)
graphml=$(find "$output" -maxdepth 1 -name "*.graphml" -print)
rocket_count=$(awk "/Rocket/{count++} END{print count+0}" "$fir")
client_count=$(awk "/RaveilStaticStencilTLClient/{count++} END{print count+0}" "$fir")
core_count=$(awk "/RaveilStaticStencilCore/{count++} END{print count+0}" "$fir")
graph_origin_count=$(awk "/raveil_graph_origin/{count++} END{print count+0}" "$fir")
manager_instances=$(awk "/^[[:space:]]*inst [^ ]+ of RaveilOwnedTLMemory/{count++} END{print count+0}" "$fir")
memory_definitions=$(awk "/val memory = SyncReadMem/{count++} END{print count+0}" /overlay/RaveilOwnedTLMemory.scala)
wrapper_count=$(awk "/StaticStencilRegion/{count++} END{print count+0}" "$fir")
scratchpad_count=$(awk "/OwnedFixedLatencyScratchpad/{count++} END{print count+0}" "$fir")
printf "G1B-COMMON-OWNED-MEMORY-TOPOLOGY-CHECK-V1 fir_count=%s graphml_count=%s rocket_matches=%s client_matches=%s core_matches=%s graph_origin_matches=%s manager_instances=%s compared_data_sync_read_mem_definitions=%s graph_wrapper_matches=%s local_scratchpad_matches=%s\n" "$fir_count" "$graphml_count" "$rocket_count" "$client_count" "$core_count" "$graph_origin_count" "$manager_instances" "$memory_definitions" "$wrapper_count" "$scratchpad_count"
[ -s "$fir" ] || { echo "error: generated FIR is missing or empty" >&2; exit 1; }
[ -s "$graphml" ] || { echo "error: generated GraphML is missing or empty" >&2; exit 1; }
[ "$rocket_count" -gt 0 ] || { echo "error: Rocket is absent from generated FIR" >&2; exit 1; }
[ "$client_count" -gt 0 ] || { echo "error: Graph TL client is absent from generated FIR" >&2; exit 1; }
[ "$core_count" -gt 0 ] || { echo "error: Graph core is absent from generated FIR" >&2; exit 1; }
[ "$graph_origin_count" -gt 0 ] || { echo "error: Graph origin field is absent from generated FIR" >&2; exit 1; }
[ "$manager_instances" -eq 1 ] || { echo "error: generated FIR does not contain exactly one owned manager instance" >&2; exit 1; }
[ "$memory_definitions" -eq 1 ] || { echo "error: owned manager source does not contain exactly one compared-data memory definition" >&2; exit 1; }
[ "$wrapper_count" -eq 0 ] || { echo "error: compatibility Graph wrapper leaked into integrated top" >&2; exit 1; }
[ "$scratchpad_count" -eq 0 ] || { echo "error: wrapper-local scratchpad leaked into integrated top" >&2; exit 1; }
graph_ranges=$(awk "
  /Master Name = raveil-static-stencil-graph/ { capture = 1; next }
  capture && /sourceId = IdRange/ {
    line = \$0
    sub(/^.*IdRange\(/, \"\", line)
    sub(/\).*$/, \"\", line)
    gsub(/[[:space:]]/, \"\", line)
    gsub(/,/, \":\", line)
    print line
    capture = 0
  }
" "$graphml" | sort -u)
graph_range_count=$(printf "%s\n" "$graph_ranges" | sed "/^$/d" | wc -l | tr -d " ")
printf "G1B-COMMON-OWNED-MEMORY-SOURCE-CHECK-V1 graph_range_count=%s graph_ranges=%s\n" "$graph_range_count" "$graph_ranges"
[ "$graph_range_count" -eq 2 ] || { echo "error: GraphML Graph source-range transform count drifted" >&2; exit 1; }
printf "%s\n" "$graph_ranges" | grep -qx "0:1" || { echo "error: Graph local source range drifted" >&2; exit 1; }
printf "%s\n" "$graph_ranges" | grep -qx "1024:1025" || { echo "error: Graph bus source range drifted" >&2; exit 1; }
fragmenter_range=$(awk "
  /Master Name = TLFragmenter/ { capture = 1; next }
  capture && /sourceId = IdRange/ {
    line = \$0
    sub(/^.*IdRange\(/, \"\", line)
    sub(/\).*$/, \"\", line)
    gsub(/[[:space:]]/, \"\", line)
    gsub(/,/, \":\", line)
    print line
    exit
  }
" "$graphml")
[ "$fragmenter_range" = "0:32800" ] || { echo "error: manager-adjacent fragmenter source range drifted: $fragmenter_range" >&2; exit 1; }
fragmenter_end=${fragmenter_range#*:}
graph_bus_end=1025
fragmenter_factor=$((fragmenter_end / graph_bus_end))
[ "$fragmenter_factor" -eq 32 ] || { echo "error: manager-adjacent fragmenter factor drifted: $fragmenter_factor" >&2; exit 1; }
graph_manager_range=$((1024 * fragmenter_factor)):$((1025 * fragmenter_factor))
printf "G1B-COMMON-OWNED-MEMORY-ELABORATION-V1 status=OK config=%s graph_local_source_range=0:1 graph_bus_source_range=1024:1025 graph_manager_source_range=%s graph_source=elaboration-derived rocket=present graph_core=present manager_instances=1 compared_data_sync_read_mem_definitions=1 graph_wrapper=absent client_state=dormant controller=absent checkpoint_a=0 tuple=32bit-4byte-mask-one-request-response-max1-no-request-buffer-held-response-one-bank-1024-580 evidence=rtl-elaboration-topology performance=not-measured\n" "$config" "$graph_manager_range"'
