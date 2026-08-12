#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
pin_file="$repo_root/hardware/chisel/boom-pin.env"
destination="$repo_root/external/chipyard"

# Repository-owned constant assignments only.
# shellcheck disable=SC1090
. "$pin_file"

if [ -e "$destination/.git" ]; then
    current=$(git -C "$destination" rev-parse HEAD)
    [ "$current" = "$CHIPYARD_REVISION" ] || {
        echo "error: Chipyard checkout is at $current, expected $CHIPYARD_REVISION" >&2
        exit 1
    }
    [ -z "$(git -C "$destination" status --porcelain --ignore-submodules=none)" ] || {
        echo 'error: Chipyard checkout or initialized submodule has local changes' >&2
        exit 1
    }
else
    [ ! -e "$destination" ] || {
        echo "error: destination exists but is not a Git checkout: $destination" >&2
        exit 1
    }
    mkdir -p "$repo_root/external"
    git clone --filter=blob:none --no-checkout "$CHIPYARD_URL" "$destination"
    git -C "$destination" checkout --detach "$CHIPYARD_REVISION"
fi

git -C "$destination" submodule update --init generators/boom

actual_chipyard=$(git -C "$destination" rev-parse HEAD)
actual_boom=$(git -C "$destination/generators/boom" rev-parse HEAD)
actual_chipyard_origin=$(git -C "$destination" remote get-url origin)
actual_boom_origin=$(git -C "$destination/generators/boom" remote get-url origin)
[ "$actual_chipyard_origin" = "$CHIPYARD_URL" ] || {
    echo "error: unexpected Chipyard origin: $actual_chipyard_origin" >&2
    exit 1
}
[ "$actual_boom" = "$BOOM_REVISION" ] || {
    echo "error: BOOM checkout is at $actual_boom, expected $BOOM_REVISION" >&2
    exit 1
}
[ "$actual_boom_origin" = "$BOOM_URL" ] || {
    echo "error: unexpected BOOM origin: $actual_boom_origin" >&2
    exit 1
}
[ -z "$(git -C "$destination/generators/boom" status --porcelain)" ] || {
    echo 'error: BOOM checkout has local changes' >&2
    exit 1
}

printf 'BOOM-CHECKOUT-V1 status=OK chipyard_revision=%s boom_revision=%s config=%s evidence=source-pin-only performance=not-measured\n' \
    "$actual_chipyard" "$actual_boom" "$BOOM_CONFIG"
