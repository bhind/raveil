#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
pin_file="$repo_root/hardware/chisel/rocket-pin.env"
destination="$repo_root/external/rocket-chip"

# This file contains repository-owned constant assignments only.
# shellcheck disable=SC1090
. "$pin_file"

if [ -e "$destination/.git" ]; then
    current=$(git -C "$destination" rev-parse HEAD)
    if [ "$current" != "$ROCKET_REVISION" ]; then
        echo "error: existing Rocket checkout is at $current, expected $ROCKET_REVISION" >&2
        exit 1
    fi
    if [ -n "$(git -C "$destination" status --porcelain)" ]; then
        echo "error: existing Rocket checkout has local changes" >&2
        exit 1
    fi
else
    if [ -e "$destination" ]; then
        echo "error: destination exists but is not a Git checkout: $destination" >&2
        exit 1
    fi
    mkdir -p "$repo_root/external"
    git clone --filter=blob:none --no-checkout "$ROCKET_URL" "$destination"
    git -C "$destination" checkout --detach "$ROCKET_REVISION"
fi

git -C "$destination" submodule update --init --recursive --depth 1

actual=$(git -C "$destination" rev-parse HEAD)
origin=$(git -C "$destination" remote get-url origin)
printf 'ROCKET-CHECKOUT-V1 status=OK revision=%s origin=%s path=%s\n' \
    "$actual" "$origin" "$destination"
