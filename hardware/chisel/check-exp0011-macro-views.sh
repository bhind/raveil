#!/bin/sh
# Reproduce the pre-data EXP-0011 inventory of required memory physical views.
# This does not allocate/freeze an experiment or collect candidate data.
set -eu

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

[ "$#" -eq 0 ] || fail 'usage: check-exp0011-macro-views.sh'
command -v docker >/dev/null 2>&1 || fail 'docker is required'

image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64
expected_image_id=sha256:7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169
expected_rootfs_sha256=21620b37d8c2f62d831d186304b2b32912e6f0d5d34ca14a8e659edbbdfbeac5

image_id=$(docker image inspect --format '{{.Id}}' "$image")
rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$image" |
    shasum -a 256 | awk '{print $1}')
[ "$image_id" = "$expected_image_id" ] || fail "physical toolchain image ID drift: $image_id"
[ "$rootfs_sha256" = "$expected_rootfs_sha256" ] ||
    fail "physical toolchain RootFS drift: $rootfs_sha256"

printf 'schema=raveil.exp-0011-macro-view-inventory/v1\n'
printf 'image=%s\n' "$image"
printf 'image_id=%s\n' "$image_id"
printf 'image_rootfs_sha256=%s\n' "$rootfs_sha256"
printf 'platform=%s\n' "$platform"

docker run --rm --platform "$platform" --network none \
    --security-opt no-new-privileges=true \
    "$image" sh -c 'set -eu
pdk_root=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A
test -d "$pdk_root"
printf "search_root=%s\n" "$pdk_root"
printf "required_predicate=fixed-string macro-name content match in every regular *.lib and *.lef file\n"
printf "supplemental_predicate=case-sensitive macro-name filename match in every regular *.gds file\n"
printf "sort=LC_ALL=C full-path ascending\n"
macros="cc_dir_ext
cc_banks_0_ext
data_arrays_0_ext
tag_array_ext
tag_array_0_ext
data_arrays_0_0_ext
memory_ext"
for suffix in lib lef; do
    find "$pdk_root" -type f -name "*.$suffix" \
        -exec grep -F -H \
            -e cc_dir_ext \
            -e cc_banks_0_ext \
            -e data_arrays_0_ext \
            -e tag_array_ext \
            -e tag_array_0_ext \
            -e data_arrays_0_0_ext \
            -e memory_ext \
            {} + 2>/dev/null | LC_ALL=C sort > "/tmp/$suffix-matches"
done
for macro in $macros; do
    for suffix in lib lef; do
        matches=$(grep -F "$macro" "/tmp/$suffix-matches" 2>/dev/null |
            cut -d: -f1 | LC_ALL=C sort -u || true)
        count=$(printf "%s\n" "$matches" | awk "NF { count += 1 } END { print count + 0 }")
        printf "macro=%s view=%s required=true count=%s\n" "$macro" "$suffix" "$count"
        if test -n "$matches"; then
            printf "%s\n" "$matches" | sed "s|^|match=$macro:$suffix:|"
        fi
    done
    matches=$(find "$pdk_root" -type f -name "*$macro*.gds" | LC_ALL=C sort)
    count=$(printf "%s\n" "$matches" | awk "NF { count += 1 } END { print count + 0 }")
    printf "macro=%s view=gds required=false count=%s\n" "$macro" "$count"
    if test -n "$matches"; then
        printf "%s\n" "$matches" | sed "s|^|match=$macro:gds:|"
    fi
done
'

printf 'evidence_class=physical-input-readiness-no-candidate-data\n'
printf 'experiment_allocated=false\n'
printf 'manifest_frozen=false\n'
printf 'candidate_data_collected=false\n'
