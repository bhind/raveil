#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
pin_file="$repo_root/hardware/chisel/boom-pin.env"
chipyard="$repo_root/external/chipyard"
boom="$chipyard/generators/boom"

# Repository-owned constant assignments only.
# shellcheck disable=SC1090
. "$pin_file"

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

[ -e "$boom/.git" ] || fail 'run ./hardware/chisel/fetch-boom-reference.sh first'
[ "$(git -C "$chipyard" rev-parse HEAD)" = "$CHIPYARD_REVISION" ] || fail 'Chipyard revision mismatch'
[ "$(git -C "$boom" rev-parse HEAD)" = "$BOOM_REVISION" ] || fail 'BOOM revision mismatch'
[ "$(git -C "$chipyard" remote get-url origin)" = "$CHIPYARD_URL" ] || fail 'Chipyard origin mismatch'
[ "$(git -C "$boom" remote get-url origin)" = "$BOOM_URL" ] || fail 'BOOM origin mismatch'
[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || fail 'external source is dirty'

gitlink=$(git -C "$chipyard" ls-tree HEAD generators/boom | awk '{print $3}')
[ "$gitlink" = "$BOOM_REVISION" ] || fail 'Chipyard BOOM gitlink mismatch'

license_hash=$(shasum -a 256 "$boom/LICENSE" | awk '{print $1}')
sifive_hash=$(shasum -a 256 "$boom/LICENSE.SiFive" | awk '{print $1}')
[ "$license_hash" = "$BOOM_LICENSE_SHA256" ] || fail 'BOOM LICENSE hash mismatch'
[ "$sifive_hash" = "$BOOM_SIFIVE_LICENSE_SHA256" ] || fail 'BOOM LICENSE.SiFive hash mismatch'

config="$chipyard/generators/chipyard/src/main/scala/config/BoomConfigs.scala"
mixins="$boom/src/main/scala/common/config-mixins.scala"
parameters="$boom/src/main/scala/common/parameters.scala"
core="$boom/src/main/scala/exu/core.scala"
custom_csrs="$repo_root/external/rocket-chip/src/main/scala/tile/CustomCSRs.scala"

grep -q 'class SmallBoomConfig' "$config" || fail 'SmallBoomConfig is absent'
grep -q 'new boom.common.WithNSmallBooms(1)' "$config" || fail 'SmallBoomConfig is not the pinned one-tile mixin'
grep -q 'numRobEntries = 32' "$mixins" || fail 'Small BOOM ROB contract changed'
grep -q 'Disable OOO when this bit is high' "$parameters" || fail 'disableOOO diagnostic bit is absent'
grep -q 'def disableOOO = getOrElse(chickenCSR, _.value(3), true.B)' "$parameters" || fail 'disableOOO bit mapping changed'
grep -q 'custom_csrs.disableOOO' "$core" || fail 'disableOOO diagnostic is not consumed by BOOM core'
grep -q 'protected def chickenCSRId = 0x7c1' "$custom_csrs" || fail 'chicken CSR address changed'

printf 'BOOM-SOURCE-REFERENCE-V1 status=OK chipyard_revision=%s boom_revision=%s config=%s disable_ooo_csr=%s disable_ooo_mask=%s diagnostic=serialize-dispatch structures=retained evidence=source-verification performance=not-measured\n' \
    "$CHIPYARD_REVISION" "$BOOM_REVISION" "$BOOM_CONFIG" \
    "$BOOM_DISABLE_OOO_CSR" "$BOOM_DISABLE_OOO_MASK"
