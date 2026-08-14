#!/bin/sh
set -eu

[ "$#" -eq 5 ] || {
    echo 'usage: run-physical-proxy-synthesis.sh MANIFEST VARIANT RTL_DIR RAW_DIR DERIVED_DIR' >&2
    exit 2
}

manifest=$1
variant=$2
rtl_dir=$3
raw_dir=$4
derived_dir=$5
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
image=raveil-physical-proxy-toolchain:v1
platform=linux/amd64

python3 -m raveil.t0044_physical verify-manifest --manifest "$manifest"
git -C "$repo_root" diff --quiet
git -C "$repo_root" diff --cached --quiet
[ -z "$(git -C "$repo_root" status --porcelain --untracked-files=all)" ] || {
    echo 'error: physical candidate collection requires a clean worktree' >&2
    exit 1
}
[ -d "$rtl_dir" ]
[ ! -e "$raw_dir" ] || {
    echo "error: raw evidence path already exists: $raw_dir" >&2
    exit 1
}
[ ! -e "$derived_dir" ] || {
    echo "error: derived result path already exists: $derived_dir" >&2
    exit 1
}
mkdir -p "$raw_dir"
rtl_dir=$(CDPATH= cd -- "$rtl_dir" && pwd)
raw_dir=$(CDPATH= cd -- "$raw_dir" && pwd)

expected_image_id=$(python3 -m raveil.t0044_physical manifest-field \
    --manifest "$manifest" --field toolchain.image_id)
top=$(python3 -m raveil.t0044_physical variant-field \
    --manifest "$manifest" --variant "$variant" --field top)
blackboxes=$(python3 -m raveil.t0044_physical variant-field \
    --manifest "$manifest" --variant "$variant" --field blackboxes)
actual_image_id=$(docker image inspect --format '{{.Id}}' "$image")
[ "$actual_image_id" = "$expected_image_id" ] || {
    echo 'error: physical toolchain image drift' >&2
    exit 1
}

set +e
docker run --rm \
    --platform "$platform" \
    --network none \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$rtl_dir,target=/rtl,readonly" \
    --mount "type=bind,source=$raw_dir,target=/evidence" \
    --mount "type=bind,source=$repo_root/hardware/chisel/run-physical-proxy-synthesis-in-container.sh,target=/runner.sh,readonly" \
    --env "RAVEIL_PHYSICAL_VARIANT=$variant" \
    --env "RAVEIL_PHYSICAL_TOP=$top" \
    --env "RAVEIL_PHYSICAL_BLACKBOX_MODULES=$blackboxes" \
    --entrypoint /bin/sh \
    "$image" \
    /runner.sh > "$raw_dir/container.log" 2>&1
container_exit_code=$?
set -e
if [ "$container_exit_code" -ne 0 ]; then
    python3 -m raveil.t0044_physical record-failure \
        --manifest "$manifest" --variant "$variant" --rtl-dir "$rtl_dir" \
        --raw-dir "$raw_dir" --container-exit-code "$container_exit_code"
    cat "$raw_dir/container.log" >&2
    exit "$container_exit_code"
fi
cat "$raw_dir/container.log"

python3 -m raveil.t0044_physical write-run-metadata \
    --manifest "$manifest" --variant "$variant" --top "$top" \
    --blackboxes "$blackboxes" --rtl-dir "$rtl_dir" --raw-dir "$raw_dir"
python3 -m raveil.t0044_physical seal-raw \
    --manifest "$manifest" --variant "$variant" --raw-dir "$raw_dir"

python3 -m raveil.t0044_physical derive-one \
    --manifest "$manifest" --variant "$variant" --rtl-dir "$rtl_dir" \
    --raw-dir "$raw_dir" --derived-dir "$derived_dir"
