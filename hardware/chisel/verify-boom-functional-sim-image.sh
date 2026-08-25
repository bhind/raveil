#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
receipt_root=$repo_root/artifacts/boom-functional-sim-images
current_pointer=$repo_root/artifacts/boom-functional-sim-image.current
expected_schema=raveil.boom-functional-sim-image/v2
expected_payload=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822
expected_config_view=32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522
expected_rootfs=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c
expected_platform=linux/amd64
expected_index_media_type=application/vnd.oci.image.index.v1+json
expected_payload_media_type=application/vnd.oci.image.manifest.v1+json
builder=./hardware/chisel/build-boom-functional-sim-image.sh

fail() {
    code=$1
    shift
    printf 'error: %s\n' "$*" >&2
    exit "$code"
}

command -v docker >/dev/null 2>&1 || fail 1 'docker is required'

if [ "$#" -gt 0 ]; then
    [ "$#" -eq 1 ] || fail 2 'usage: verify-boom-functional-sim-image.sh [RECEIPT]'
    receipt=$1
else
    [ -f "$current_pointer" ] || fail 10 "simulator current pointer missing; run $builder"
    current_image_id=$(sed -n '1p' "$current_pointer")
    [ "$(wc -l < "$current_pointer" | tr -d ' ')" -eq 1 ] ||
        fail 11 "simulator current pointer malformed; run $builder"
    current_hex=${current_image_id#sha256:}
    case "$current_hex" in
        *[!0-9a-f]*|'') fail 11 "simulator current pointer malformed; run $builder" ;;
    esac
    [ ${#current_hex} -eq 64 ] || fail 11 "simulator current pointer malformed; run $builder"
    receipt=$receipt_root/$current_hex/receipt
fi

[ -f "$receipt" ] || fail 10 "simulator receipt missing; run $builder"

awk -F= '
BEGIN {
    expected["SCHEMA"] = 1
    expected["RUNTIME_IMAGE_ID"] = 1
    expected["RUNTIME_DESCRIPTOR_DIGEST"] = 1
    expected["RUNTIME_DESCRIPTOR_MEDIA_TYPE"] = 1
    expected["RUNTIME_DESCRIPTOR_SIZE"] = 1
    expected["PAYLOAD_MANIFEST"] = 1
    expected["PAYLOAD_MEDIA_TYPE"] = 1
    expected["CONFIG_VIEW_SHA256"] = 1
    expected["ROOTFS_LAYERS_SHA256"] = 1
    expected["PLATFORM"] = 1
    expected["BUILD_REF"] = 1
}
NF != 2 || !($1 in expected) || seen[$1]++ || $2 == "" { failed = 1 }
END {
    for (key in expected) {
        if (seen[key] != 1) failed = 1
    }
    exit failed
}' "$receipt" || fail 11 "simulator receipt malformed; run $builder"

field() {
    awk -F= -v wanted="$1" '$1 == wanted { print $2 }' "$receipt"
}

schema=$(field SCHEMA)
runtime_image_id=$(field RUNTIME_IMAGE_ID)
descriptor_digest=$(field RUNTIME_DESCRIPTOR_DIGEST)
descriptor_media_type=$(field RUNTIME_DESCRIPTOR_MEDIA_TYPE)
descriptor_size=$(field RUNTIME_DESCRIPTOR_SIZE)
payload_manifest=$(field PAYLOAD_MANIFEST)
payload_media_type=$(field PAYLOAD_MEDIA_TYPE)
config_view_sha256=$(field CONFIG_VIEW_SHA256)
rootfs_sha256=$(field ROOTFS_LAYERS_SHA256)
platform=$(field PLATFORM)
build_ref=$(field BUILD_REF)

[ "$schema" = "$expected_schema" ] &&
    [ "$runtime_image_id" = "$descriptor_digest" ] &&
    [ "$descriptor_media_type" = "$expected_index_media_type" ] &&
    [ "$payload_manifest" = "$expected_payload" ] &&
    [ "$payload_media_type" = "$expected_payload_media_type" ] &&
    [ "$config_view_sha256" = "$expected_config_view" ] &&
    [ "$rootfs_sha256" = "$expected_rootfs" ] &&
    [ "$platform" = "$expected_platform" ] || fail 12 'simulator receipt authority mismatch'

runtime_hex=${runtime_image_id#sha256:}
case "$runtime_hex:$build_ref:$descriptor_size" in
    *[!0-9a-z:]*|::*|*::*|*:::*) fail 11 'simulator receipt identity syntax is invalid' ;;
esac
[ ${#runtime_hex} -eq 64 ] && [ -n "$build_ref" ] ||
    fail 11 'simulator receipt identity syntax is invalid'
case "$descriptor_size" in
    ''|*[!0-9]*) fail 11 'simulator receipt descriptor size is invalid' ;;
esac
[ "$descriptor_size" -gt 0 ] || fail 11 'simulator receipt descriptor size is zero'
if [ "${current_image_id:-$runtime_image_id}" != "$runtime_image_id" ]; then
    fail 12 'simulator current pointer and receipt disagree'
fi

actual_id=$(docker image inspect --format '{{.Id}}' "$runtime_image_id" 2>/dev/null) ||
    fail 10 "simulator image is missing; run $builder"
[ "$actual_id" = "$runtime_image_id" ] ||
    fail 13 "simulator runtime image ID mismatch (expected $runtime_image_id, got $actual_id)"

actual_descriptor=$(docker image inspect --format '{{.Descriptor.digest}}|{{.Descriptor.mediaType}}|{{.Descriptor.size}}' "$runtime_image_id")
[ "$actual_descriptor" = "$descriptor_digest|$descriptor_media_type|$descriptor_size" ] ||
    fail 15 "simulator runtime descriptor mismatch (expected $descriptor_digest|$descriptor_media_type|$descriptor_size, got $actual_descriptor)"

actual_os=$(docker image inspect --format '{{.Os}}' "$runtime_image_id")
actual_arch=$(docker image inspect --format '{{.Architecture}}' "$runtime_image_id")
[ "$actual_os/$actual_arch" = "$expected_platform" ] ||
    fail 14 "simulator platform mismatch (expected $expected_platform, got $actual_os/$actual_arch)"

actual_config_view_sha256=$(docker image inspect --format '{{json .Config}}' "$runtime_image_id" |
    shasum -a 256 | awk '{print $1}')
[ "$actual_config_view_sha256" = "$expected_config_view" ] ||
    fail 16 "simulator Config view mismatch (expected $expected_config_view, got $actual_config_view_sha256)"

actual_rootfs_sha256=$(docker image inspect --format '{{json .RootFS.Layers}}' "$runtime_image_id" |
    shasum -a 256 | awk '{print $1}')
[ "$actual_rootfs_sha256" = "$expected_rootfs" ] ||
    fail 17 "simulator RootFS layer-list mismatch (expected $expected_rootfs, got $actual_rootfs_sha256)"

attachments=$(docker buildx history inspect "$build_ref" \
    --format '{{range .Attachments}}{{.Digest}}{{"|"}}{{.Platform}}{{"|"}}{{.Type}}{{"\n"}}{{end}}' 2>/dev/null) ||
    fail 18 "simulator BuildKit record is missing; run $builder"
printf '%s\n' "$attachments" | awk -F'|' -v digest="$runtime_image_id" -v type="$expected_index_media_type" '
    $1 == digest && $2 == "" && $3 == type { count++ }
    END { exit count == 1 ? 0 : 1 }
' || fail 18 'simulator BuildKit record does not bind the runtime OCI index'
printf '%s\n' "$attachments" | awk -F'|' -v digest="$expected_payload" -v type="$expected_payload_media_type" '
    $1 == digest && $2 == "linux/amd64" && $3 == type { count++ }
    END { exit count == 1 ? 0 : 1 }
' || fail 18 'simulator BuildKit record does not bind the expected payload manifest'

printf '%s\n' "$runtime_image_id"
