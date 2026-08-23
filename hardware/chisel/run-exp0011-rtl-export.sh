#!/bin/sh
# Export a self-contained, physical-lowering-compatible ChipTop RTL closure.
# This command performs elaboration/export only. It never runs synthesis or PPA.
set -eu
umask 077

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

[ "$#" -eq 2 ] || fail 'usage: run-exp0011-rtl-export.sh VARIANT APPEND_ONLY_OUTPUT_DIR'
variant=$1
output_dir=$2
case "$variant" in
    integrated-static-graph-rocket)
        config=RaveilRuntimeIntegratedGraphRocketConfig
        ;;
    matched-rocket-system)
        config=RaveilFixtureRepeatedMatchedRocketConfig
        ;;
    *) fail "unknown variant: $variant" ;;
esac

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard=${RAVEIL_CHIPYARD_SOURCE:-"$repo_root/external/chipyard"}
rocket=${RAVEIL_ROCKET_CHIP_SOURCE:-"$chipyard/generators/rocket-chip"}
overlay="$repo_root/hardware/chisel/chipyard-overlay"
patches="$repo_root/hardware/chisel/chipyard-patches"
dockerfile="$repo_root/hardware/chisel/Dockerfile.boom-sim"
pin_file="$repo_root/hardware/chisel/boom-pin.env"
runner="$repo_root/hardware/chisel/run-exp0011-rtl-export.sh"
platform=linux/amd64
image=raveil-boom-functional-sim:v1
expected_image_id=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822
expected_rootfs_sha256=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c
toolchain_volume=raveil-chipyard-conda-lock-v1
lock_rel=conda-reqs/conda-lock-reqs/conda-requirements-riscv-tools-linux-64-lean.conda-lock.yml
lock_sha256=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
base_lowering=emittedLineLength=2048,noAlwaysComb,disallowLocalVariables,verifLabels,locationInfoStyle=wrapInAtSquareBracket
physical_lowering=$base_lowering,disallowPackedArrays

[ ! -e "$output_dir" ] || fail "append-only output path already exists: $output_dir"
command -v docker >/dev/null 2>&1 || fail 'docker is required'
[ -d "$chipyard/.git" ] || fail 'a pinned Chipyard checkout is required'
[ -e "$rocket/.git" ] || fail 'a pinned Rocket Chip checkout is required'
[ -z "$(git -C "$chipyard" status --porcelain --untracked-files=all --ignore-submodules=none)" ] ||
    fail 'the pinned Chipyard checkout and its submodules must be exact and clean'
[ "$(shasum -a 256 "$chipyard/$lock_rel" | awk '{print $1}')" = "$lock_sha256" ] ||
    fail 'the pinned simulator lockfile hash changed'
RAVEIL_CHIPYARD_SOURCE="$chipyard" RAVEIL_ROCKET_CHIP_SOURCE="$rocket" \
    "$repo_root/hardware/chisel/verify-boom-reference.sh"

chipyard_revision=$(git -C "$chipyard" rev-parse HEAD)
rocket_revision=$(git -C "$rocket" rev-parse HEAD)
source_sha256=$({
    shasum -a 256 \
        "$overlay/RaveilOwnedTLMemory.scala" \
        "$overlay/RaveilDCacheOriginTagger.scala" \
        "$overlay/RaveilFixtureInputProvider.scala" \
        "$overlay/RaveilStaticStencilCore.scala" \
        "$overlay/RaveilStaticStencilTLClient.scala" \
        "$patches/t-0042-tl-token-metadata.patch" \
        "$patches/t-0042-rocket-dcache-origin-hook.patch" \
        "$patches/t-0042-tlxbar-request-defaults.patch" |
        awk '{print $1}'
    printf 'variant=%s\nconfig=%s\nchipyard_revision=%s\nrocket_revision=%s\nlock_sha256=%s\n' \
        "$variant" "$config" "$chipyard_revision" "$rocket_revision" "$lock_sha256"
} | shasum -a 256 | awk '{print $1}')
runner_sha256=$(shasum -a 256 "$runner" | awk '{print $1}')
input_sha256=$({
    printf '%s\n%s\n' "$source_sha256" "$runner_sha256"
    shasum -a 256 \
        "$dockerfile" \
        "$pin_file" \
        "$chipyard/common.mk" \
        "$repo_root/hardware/chisel/verify-boom-reference.sh" \
        "$repo_root/raveil/t0044_physical.py" |
        awk '{print $1}'
} | shasum -a 256 | awk '{print $1}')
prefix=${RAVEIL_EXP0011_CACHE_PREFIX:-$(printf '%s' "$input_sha256" | cut -c1-16)}
case "$prefix" in
    *[!0-9a-f]*|'') fail 'RAVEIL_EXP0011_CACHE_PREFIX must be lowercase hexadecimal' ;;
esac
[ "${#prefix}" -eq 16 ] || fail 'RAVEIL_EXP0011_CACHE_PREFIX must contain 16 hexadecimal characters'
normal_volume="raveil-exp0011-${variant}-normal-$prefix"
physical_volume="raveil-exp0011-${variant}-physical-$prefix"

mkdir "$output_dir"
output_dir=$(CDPATH= cd -- "$output_dir" && pwd)

image_id=$(docker image inspect --format '{{.Id}}' "$image")
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
    shasum -a 256 | awk '{print $1}')
[ "$image_id" = "$expected_image_id" ] || fail "RTL export image ID drift: $image_id"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] || fail "RTL export image RootFS drift: $rootfs_sha256"

docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    --env "RAVEIL_CONFIG=$config" \
    --env "RAVEIL_SOURCE_SHA256=$source_sha256" \
    --env "RAVEIL_CHIPYARD_REVISION=$chipyard_revision" \
    --env "RAVEIL_ROCKET_REVISION=$rocket_revision" \
    --env "RAVEIL_LOCK_SHA256=$lock_sha256" \
    --env "RAVEIL_BASE_LOWERING=$base_lowering" \
    --env "RAVEIL_PHYSICAL_LOWERING=$physical_lowering" \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=bind,source=$overlay,target=/overlay,readonly" \
    --mount "type=bind,source=$patches,target=/patches,readonly" \
    --mount "type=bind,source=$output_dir,target=/export" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$normal_volume,target=/normal" \
    --mount "type=volume,source=$physical_volume,target=/physical" \
    --mount type=volume,source=raveil-chipyard-sbt-cache-v1,target=/root/.cache \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/normal/chipyard/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/normal/chipyard/.sbt \
    --mount type=volume,source=raveil-chipyard-ivy-cache-v1,target=/physical/chipyard/.ivy2 \
    --mount type=volume,source=raveil-chipyard-sbt-global-v1,target=/physical/chipyard/.sbt \
    "$image" bash -lc 'set -euo pipefail
export RISCV=/locked/env/riscv-tools
export PATH=/locked/env/bin:$RISCV/bin:$PATH
test -x /locked/env/bin/verilator
test -x "$RISCV/bin/firtool"
test "$(cat /locked/raveil-lock-sha256)" = "$RAVEIL_LOCK_SHA256"
verilator --version | grep -q "Verilator 5.020"
"$RISCV/bin/firtool" --version | grep -q "CIRCT firtool-1.61.0"

prepare_tree() {
    tree=$1
    marker=$tree/raveil-exp0011-source-sha256
    if test ! -f "$marker"; then
        mkdir -p "$tree/chipyard"
        cp -a /source/. "$tree/chipyard/"
        cd "$tree/chipyard"
        test "$(git rev-parse HEAD)" = "$RAVEIL_CHIPYARD_REVISION"
        test "$(git -C generators/rocket-chip rev-parse HEAD)" = "$RAVEIL_ROCKET_REVISION"
        git -C generators/rocket-chip apply --check --unidiff-zero /patches/t-0042-tl-token-metadata.patch
        git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tl-token-metadata.patch
        git -C generators/rocket-chip apply --check --unidiff-zero /patches/t-0042-rocket-dcache-origin-hook.patch
        git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-rocket-dcache-origin-hook.patch
        git -C generators/rocket-chip apply --check --unidiff-zero /patches/t-0042-tlxbar-request-defaults.patch
        git -C generators/rocket-chip apply --unidiff-zero /patches/t-0042-tlxbar-request-defaults.patch
        for source in RaveilOwnedTLMemory.scala RaveilDCacheOriginTagger.scala \
            RaveilFixtureInputProvider.scala RaveilStaticStencilCore.scala \
            RaveilStaticStencilTLClient.scala; do
            install -D -m 0444 "/overlay/$source" \
                "generators/chipyard/src/main/scala/raveil/$source"
        done
        printf "%s\n" "$RAVEIL_SOURCE_SHA256" > "$marker"
    else
        test "$(cat "$marker")" = "$RAVEIL_SOURCE_SHA256"
    fi
}

prepare_tree /normal
prepare_tree /physical
export LD_LIBRARY_PATH=$RISCV/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
long_name=chipyard.harness.TestHarness.$RAVEIL_CONFIG
normal_target=/normal/chipyard/sims/verilator/generated-src/$long_name/$long_name.top.f
physical_target=/physical/chipyard/sims/verilator/generated-src/$long_name/$long_name.top.f
cd /normal/chipyard/sims/verilator
make -j2 CONFIG="$RAVEIL_CONFIG" CONFIG_PACKAGE=chipyard.raveil "$normal_target"
cd /physical/chipyard/sims/verilator
ENABLE_YOSYS_FLOW=1 make -j2 CONFIG="$RAVEIL_CONFIG" CONFIG_PACKAGE=chipyard.raveil "$physical_target"

normal=/normal/chipyard/sims/verilator/generated-src/$long_name
physical=/physical/chipyard/sims/verilator/generated-src/$long_name
test -d "$normal" && test -d "$physical"
test "$(cat "$normal/.mfc_lowering_options")" = "$RAVEIL_BASE_LOWERING"
test "$(cat "$physical/.mfc_lowering_options")" = "$RAVEIL_PHYSICAL_LOWERING"

for relative in "$long_name.fir" .sfc_level .extra_firrtl_options "$long_name.sfc.fir" \
    "$long_name.mems.conf" model_module_hierarchy.json \
    model_module_hierarchy.uniquified.json top_module_hierarchy.json; do
    test -s "$normal/$relative" && test -s "$physical/$relative"
    test "$(sha256sum "$normal/$relative" | cut -d" " -f1)" = \
         "$(sha256sum "$physical/$relative" | cut -d" " -f1)"
done
for relative in "$long_name.appended.anno.json" "$long_name.sfc.anno.json"; do
    sed "s!/normal!<build-root>!g" "$normal/$relative" > "/tmp/normal-$relative"
    sed "s!/physical!<build-root>!g" "$physical/$relative" > "/tmp/physical-$relative"
    ! grep -F -e "/normal" -e "/physical" "/tmp/normal-$relative" "/tmp/physical-$relative"
    cmp "/tmp/normal-$relative" "/tmp/physical-$relative"
done
for suffix in top.f model.f; do
    sed "s!.*/!!" "$normal/$long_name.$suffix" | LC_ALL=C sort > "/tmp/normal-$suffix"
    sed "s!.*/!!" "$physical/$long_name.$suffix" | LC_ALL=C sort > "/tmp/physical-$suffix"
    cmp "/tmp/normal-$suffix" "/tmp/physical-$suffix"
done

mkdir /export/generated-src
physical_filelist="$physical/$long_name.top.f"
test -s "$physical_filelist"
: > /export/ChipTop.top.f
while IFS= read -r source; do
    case "$source" in
        "$physical"/gen-collateral/*.sv|"$physical"/gen-collateral/*.v) ;;
        *) echo "error: non-canonical physical RTL entry: $source" >&2; exit 1 ;;
    esac
    base=$(basename "$source")
    case "$base" in
        *[!ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-]*|"")
            echo "error: unsafe physical RTL basename: $base" >&2
            exit 1
            ;;
        *.sv|*.v) ;;
        *) echo "error: unsupported physical RTL suffix: $base" >&2; exit 1 ;;
    esac
    target=/export/generated-src/$base
    test ! -e "$target"
    cp "$source" "$target"
    printf "generated-src/%s\n" "$base" >> /export/ChipTop.top.f
done < "$physical_filelist"
test -s /export/ChipTop.top.f
grep -qx "generated-src/ChipTop.sv" /export/ChipTop.top.f
! grep -q "TestHarness" /export/ChipTop.top.f
find /export/generated-src -type f | LC_ALL=C sort | sed "s!^/export/!!" > /export/rtl-files.txt
test "$(wc -l < /export/rtl-files.txt | tr -d " ")" = \
     "$(wc -l < /export/ChipTop.top.f | tr -d " ")"

cp "$physical/$long_name.fir" /export/pre-firtool.fir
cp "$physical/$long_name.mems.conf" /export/memory-macro-contract.txt
cp "$physical/top_module_hierarchy.json" /export/top-module-hierarchy.json
cp "$physical/model_module_hierarchy.json" /export/model-module-hierarchy.json
cp "$physical/model_module_hierarchy.uniquified.json" /export/model-module-hierarchy-uniquified.json
{
    printf "schema=raveil.exp-0011-lowering-provenance/v1\n"
    printf "normal_lowering=%s\nphysical_lowering=%s\n" "$RAVEIL_BASE_LOWERING" "$RAVEIL_PHYSICAL_LOWERING"
    for relative in "$long_name.fir" .sfc_level .extra_firrtl_options "$long_name.sfc.fir" \
        "$long_name.mems.conf" model_module_hierarchy.json \
        model_module_hierarchy.uniquified.json top_module_hierarchy.json; do
        printf "shared_file=%s sha256=%s\n" "$relative" \
            "$(sha256sum "$physical/$relative" | cut -d" " -f1)"
    done
    for relative in "$long_name.appended.anno.json" "$long_name.sfc.anno.json"; do
        printf "shared_normalized_annotation=%s sha256=%s\n" "$relative" \
            "$(sha256sum "/tmp/physical-$relative" | cut -d" " -f1)"
    done
    for suffix in top.f model.f; do
        printf "shared_normalized_filelist=%s sha256=%s\n" "$suffix" \
            "$(sha256sum "/tmp/physical-$suffix" | cut -d" " -f1)"
    done
    printf "status=shared-elaboration-identical\n"
} > /export/lowering-provenance.txt
'

rtl_sha256=$(PYTHONPATH="$repo_root" python3 -m raveil.t0044_physical hash-tree --path "$output_dir/generated-src")
rtl_filelist_sha256=$(shasum -a 256 "$output_dir/rtl-files.txt" | awk '{print $1}')
firrtl_sha256=$(shasum -a 256 "$output_dir/pre-firtool.fir" | awk '{print $1}')
hierarchy_sha256=$(shasum -a 256 "$output_dir/top-module-hierarchy.json" | awk '{print $1}')
lowering_provenance_sha256=$(shasum -a 256 "$output_dir/lowering-provenance.txt" | awk '{print $1}')
rocket_rtl_sha256=$(shasum -a 256 "$output_dir/generated-src/Rocket.sv" | awk '{print $1}')
memory_macro_contract_sha256=$(shasum -a 256 "$output_dir/memory-macro-contract.txt" | awk '{print $1}')

python3 - "$output_dir/export-metadata.json" <<EOF
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
record = {
    "schema": "raveil.exp-0011-rtl-export/v1",
    "variant": "$variant",
    "config": "chipyard.raveil.$config",
    "top": "ChipTop",
    "source_sha256": "$source_sha256",
    "input_sha256": "$input_sha256",
    "runner_sha256": "$runner_sha256",
    "chipyard_revision": "$chipyard_revision",
    "rocket_revision": "$rocket_revision",
    "lock_sha256": "$lock_sha256",
    "image": "$image",
    "image_id": "$image_id",
    "image_rootfs_sha256": "$rootfs_sha256",
    "platform": "$platform",
    "normal_volume": "$normal_volume",
    "physical_volume": "$physical_volume",
    "normal_lowering": "$base_lowering",
    "physical_lowering": "$physical_lowering",
    "rtl_sha256": "$rtl_sha256",
    "rtl_filelist_sha256": "$rtl_filelist_sha256",
    "firrtl_sha256": "$firrtl_sha256",
    "hierarchy_sha256": "$hierarchy_sha256",
    "lowering_provenance_sha256": "$lowering_provenance_sha256",
    "rocket_rtl_sha256": "$rocket_rtl_sha256",
    "memory_macro_contract_sha256": "$memory_macro_contract_sha256",
    "evidence_class": "rtl-elaboration-export",
    "performance": "not-measured",
    "nonclaim": "structural export only; no synth/abc/stat/sta",
}
path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
EOF

printf 'EXP0011-RTL-EXPORT-V1 status=OK variant=%s config=chipyard.raveil.%s top=ChipTop source_sha256=%s input_sha256=%s rtl_sha256=%s rtl_filelist_sha256=%s firrtl_sha256=%s hierarchy_sha256=%s rocket_rtl_sha256=%s lowering_provenance_sha256=%s evidence=rtl-elaboration-export performance=not-measured\n' \
    "$variant" "$config" "$source_sha256" "$input_sha256" "$rtl_sha256" \
    "$rtl_filelist_sha256" "$firrtl_sha256" "$hierarchy_sha256" \
    "$rocket_rtl_sha256" "$lowering_provenance_sha256"
