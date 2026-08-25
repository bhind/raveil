#!/bin/sh
set -eu
umask 077

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
dockerfile=$repo_root/hardware/chisel/Dockerfile.boom-sim
verifier=$repo_root/hardware/chisel/verify-boom-functional-sim-image.sh
receipt_root=$repo_root/artifacts/boom-functional-sim-images
current_pointer=$repo_root/artifacts/boom-functional-sim-image.current
expected_payload=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822
expected_config_view=32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522
expected_rootfs=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c
index_media_type=application/vnd.oci.image.index.v1+json
payload_media_type=application/vnd.oci.image.manifest.v1+json

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

command -v docker >/dev/null 2>&1 || fail 'docker is required'
command -v python3 >/dev/null 2>&1 || fail 'python3 is required'

tmp_iid=$(mktemp "${TMPDIR:-/tmp}/raveil-boom-image.XXXXXX")
tmp_meta=$(mktemp "${TMPDIR:-/tmp}/raveil-boom-meta.XXXXXX")
tmp_receipt=
tmp_pointer=
trap 'rm -f "$tmp_iid" "$tmp_meta" ${tmp_receipt:+"$tmp_receipt"} ${tmp_pointer:+"$tmp_pointer"}' EXIT HUP INT TERM

docker buildx build \
    --load \
    --platform linux/amd64 \
    --provenance=mode=min \
    --metadata-file "$tmp_meta" \
    --file "$dockerfile" \
    --iidfile "$tmp_iid" \
    "$repo_root"

runtime_image_id=$(sed -n '1p' "$tmp_iid")
metadata_fields=$(python3 - "$tmp_meta" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    metadata = json.load(source)
descriptor = metadata.get("containerimage.descriptor", {})
fields = (
    metadata.get("containerimage.digest", ""),
    descriptor.get("digest", ""),
    descriptor.get("mediaType", ""),
    str(descriptor.get("size", "")),
    metadata.get("buildx.build.ref", ""),
)
if any("\n" in field for field in fields):
    raise SystemExit(1)
print("\n".join(fields))
PY
) || fail 'Docker metadata is not valid JSON'
[ "$(printf '%s\n' "$metadata_fields" | wc -l | tr -d ' ')" -eq 5 ] ||
    fail 'Docker metadata did not contain five identity fields'
metadata_image_id=$(printf '%s\n' "$metadata_fields" | sed -n '1p')
descriptor_digest=$(printf '%s\n' "$metadata_fields" | sed -n '2p')
descriptor_media_type=$(printf '%s\n' "$metadata_fields" | sed -n '3p')
descriptor_size=$(printf '%s\n' "$metadata_fields" | sed -n '4p')
build_ref=$(printf '%s\n' "$metadata_fields" | sed -n '5p')

runtime_hex=${runtime_image_id#sha256:}
metadata_hex=${metadata_image_id#sha256:}
descriptor_hex=${descriptor_digest#sha256:}
case "$runtime_hex:$metadata_hex:$descriptor_hex" in
    *[!0-9a-f:]*|::*|*::*|*:::*) fail 'Docker metadata contains invalid image identities' ;;
esac
[ ${#runtime_hex} -eq 64 ] && [ ${#metadata_hex} -eq 64 ] && [ ${#descriptor_hex} -eq 64 ] ||
    fail 'Docker metadata contains incomplete image identities'
[ "$runtime_image_id" = "$metadata_image_id" ] && [ "$runtime_image_id" = "$descriptor_digest" ] ||
    fail 'Docker iidfile, digest, and descriptor identities disagree'
[ "$descriptor_media_type" = "$index_media_type" ] ||
    fail "Docker descriptor media type mismatch: $descriptor_media_type"
case "$descriptor_size" in
    ''|*[!0-9]*) fail 'Docker descriptor size is invalid' ;;
esac
[ "$descriptor_size" -gt 0 ] || fail 'Docker descriptor size is zero'

build_ref_short=${build_ref##*/}
case "$build_ref_short" in
    ''|*[!0-9a-z]*) fail 'Docker metadata did not contain a valid build reference' ;;
esac

attachments=$(docker buildx history inspect "$build_ref_short" \
    --format '{{range .Attachments}}{{.Digest}}{{"|"}}{{.Platform}}{{"|"}}{{.Type}}{{"\n"}}{{end}}')
printf '%s\n' "$attachments" | awk -F'|' -v digest="$runtime_image_id" -v type="$index_media_type" '
    $1 == digest && $2 == "" && $3 == type { count++ }
    END { exit count == 1 ? 0 : 1 }
' || fail 'Build record does not contain the exact runtime OCI index'
printf '%s\n' "$attachments" | awk -F'|' -v digest="$expected_payload" -v type="$payload_media_type" '
    $1 == digest && $2 == "linux/amd64" && $3 == type { count++ }
    END { exit count == 1 ? 0 : 1 }
' || fail 'Build record does not contain the expected linux/amd64 payload manifest'

mkdir -p "$receipt_root"
chmod 0700 "$receipt_root"
record_dir=$receipt_root/$runtime_hex
[ ! -e "$record_dir" ] || fail "immutable simulator receipt already exists: $record_dir"
tmp_receipt=$(mktemp "$receipt_root/.receipt.XXXXXX")
printf '%s\n' \
    'SCHEMA=raveil.boom-functional-sim-image/v2' \
    "RUNTIME_IMAGE_ID=$runtime_image_id" \
    "RUNTIME_DESCRIPTOR_DIGEST=$descriptor_digest" \
    "RUNTIME_DESCRIPTOR_MEDIA_TYPE=$descriptor_media_type" \
    "RUNTIME_DESCRIPTOR_SIZE=$descriptor_size" \
    "PAYLOAD_MANIFEST=$expected_payload" \
    "PAYLOAD_MEDIA_TYPE=$payload_media_type" \
    "CONFIG_VIEW_SHA256=$expected_config_view" \
    "ROOTFS_LAYERS_SHA256=$expected_rootfs" \
    'PLATFORM=linux/amd64' \
    "BUILD_REF=$build_ref_short" > "$tmp_receipt"

verified_image_id=$("$verifier" "$tmp_receipt")
[ "$verified_image_id" = "$runtime_image_id" ] ||
    fail 'verifier returned a different runtime image identity'

mkdir -m 0700 "$record_dir"
mv "$tmp_receipt" "$record_dir/receipt"
tmp_receipt=
tmp_pointer=$(mktemp "$repo_root/artifacts/.boom-functional-sim-image.current.XXXXXX")
printf '%s\n' "$runtime_image_id" > "$tmp_pointer"
mv "$tmp_pointer" "$current_pointer"
tmp_pointer=

printf 'BOOM-SIM-IMAGE-BUILT runtime_image_id=%s payload_manifest=%s config_view_sha256=%s rootfs_layers_sha256=%s platform=linux/amd64 tag_mutation=none receipt=append-only evidence=rtl-simulation-functional performance=not-measured\n' \
    "$runtime_image_id" "$expected_payload" "$expected_config_view" "$expected_rootfs"
