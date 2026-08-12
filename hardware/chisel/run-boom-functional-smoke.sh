#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
chipyard="$repo_root/external/chipyard"
image=raveil-boom-functional-sim:v1
platform=linux/amd64
toolchain_volume=raveil-chipyard-conda-lock-v1
build_volume=raveil-chipyard-boom-sim-build-v1
lock_rel=conda-reqs/conda-lock-reqs/conda-requirements-riscv-tools-linux-64-lean.conda-lock.yml
lock_sha=5248d0e404ab5ac0884ffd03934e31b757c6999c9987009e5cfd5d80fc21da3d
firtool_sha=e09cfe2f50fb9d3ce301206bf48cc428b4d40960618e0552724203259dfc156b
fesvr_sha=b3a75b5ced0451f4436147fa480745bd7cc4b296366ccf73f1caae80cc0d7588
chipyard_revision=ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1

command -v docker >/dev/null 2>&1 || {
    echo 'error: docker is required' >&2
    exit 1
}
[ -d "$chipyard/.git" ] || {
    echo 'error: run ./hardware/chisel/fetch-boom-simulator-deps.sh first' >&2
    exit 1
}

"$repo_root/hardware/chisel/verify-boom-reference.sh"
[ -z "$(git -C "$chipyard" status --porcelain --ignore-submodules=none)" ] || {
    echo 'error: Chipyard checkout or simulator dependency is not exact and clean' >&2
    exit 1
}
[ "$(shasum -a 256 "$chipyard/$lock_rel" | awk '{print $1}')" = "$lock_sha" ] || {
    echo 'error: Chipyard simulator lockfile hash changed' >&2
    exit 1
}

docker build \
    --platform "$platform" \
    --file "$repo_root/hardware/chisel/Dockerfile.boom-sim" \
    --tag "$image" \
    "$repo_root"

printf 'BOOM-SIM-TOOLCHAIN-HOST-V1 image=%s platform=%s lock_sha256=%s conda_lock_bootstrap=unlocked cache=evidence-neutral performance=not-measured\n' \
    "$image" "$platform" "$lock_sha"

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked" \
    "$image" \
    bash -lc 'set -euo pipefail
lock=/source/'"$lock_rel"'
expected_lock='"$lock_sha"'
expected_firtool='"$firtool_sha"'
expected_fesvr='"$fesvr_sha"'
actual_lock=$(sha256sum "$lock" | awk "{print \$1}")
[ "$actual_lock" = "$expected_lock" ]
if [ ! -x /locked/env/bin/verilator ]; then
  conda-lock install --conda /opt/conda/bin/conda -p /locked/env "$lock"
fi
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
verilator --version | grep -q "Verilator 5.020"
riscv64-unknown-elf-gcc --version | grep -q "12.2.0"
dtc --version | grep -q "DTC 1.6.1"
if [ ! -x "$RISCV/bin/firtool" ]; then
  /source/tools/install-circt/bin/download-release-or-nightly-circt.sh \
    -f circt-full-shared-linux-x64.tar.gz -i "$RISCV" \
    -v version-file -x /source/conda-reqs/circt.json -g null
fi
"$RISCV/bin/firtool" --version | grep -q "CIRCT firtool-1.61.0"
[ "$(sha256sum "$RISCV/bin/firtool" | awk "{print \$1}")" = "$expected_firtool" ]
if [ ! -s "$RISCV/lib/libfesvr.a" ] || [ ! -f "$RISCV/include/fesvr/htif.h" ]; then
  cp -a /source/toolchains/riscv-tools/riscv-isa-sim /work/riscv-isa-sim
  mkdir /work/riscv-isa-sim/build
  cd /work/riscv-isa-sim/build
  ../configure --prefix="$RISCV" --with-boost=no --with-boost-asio=no \
    --with-boost-regex=no >/dev/null
  make -j2 libfesvr.a
  install -m 0644 libfesvr.a "$RISCV/lib/libfesvr.a"
  make install-hdrs install-config-hdrs >/dev/null
fi
test -s "$RISCV/lib/libfesvr.a"
test -f "$RISCV/include/fesvr/htif.h"
[ "$(sha256sum "$RISCV/lib/libfesvr.a" | awk "{print \$1}")" = "$expected_fesvr" ]
printf "%s\n" "$expected_lock" > /locked/raveil-lock-sha256
printf "BOOM-SIM-TOOLCHAIN-V1 status=OK lock_sha256=%s verilator=5.020 firtool=1.61.0 riscv_gcc=12.2.0 fesvr=present evidence=functional-bootstrap performance=not-measured\n" "$expected_lock"'

docker run --rm \
    --platform "$platform" \
    --security-opt no-new-privileges=true \
    --mount "type=bind,source=$repo_root,target=/repo,readonly" \
    --mount "type=bind,source=$chipyard,target=/source,readonly" \
    --mount "type=volume,source=$toolchain_volume,target=/locked,readonly" \
    --mount "type=volume,source=$build_volume,target=/build" \
    "$image" \
    bash -lc 'set -euo pipefail
export PATH=/locked/env/bin:/locked/env/riscv-tools/bin:$PATH
export RISCV=/locked/env/riscv-tools
expected_chipyard='"$chipyard_revision"'
[ "$(cat /locked/raveil-lock-sha256)" = '"$lock_sha"' ]
if [ ! -d /build/chipyard/.git ]; then
  cp -a /source /build/chipyard
fi
[ "$(git -C /build/chipyard rev-parse HEAD)" = "$expected_chipyard" ]
[ -z "$(git -C /build/chipyard status --porcelain --untracked-files=no --ignore-submodules=untracked)" ]
cd /build/chipyard/sims/verilator
make -j2 CONFIG=SmallBoomConfig CONFIG_PACKAGE=chipyard
sim=/build/chipyard/sims/verilator/simulator-chipyard.harness-SmallBoomConfig
test -x "$sim"
riscv64-unknown-elf-gcc \
  -march=rv64imafd -mabi=lp64d -mcmodel=medany \
  -nostdlib -nostartfiles -static -Wl,--no-relax \
  -T /repo/hardware/chisel/boom_functional_smoke.ld \
  /repo/hardware/chisel/boom_functional_smoke.S \
  -o /build/boom_functional_smoke.elf
riscv64-unknown-elf-readelf -h /build/boom_functional_smoke.elf | \
  grep -q "Machine:.*RISC-V"
riscv64-unknown-elf-nm /build/boom_functional_smoke.elf | \
  grep -q " T _start$"
riscv64-unknown-elf-nm /build/boom_functional_smoke.elf | \
  grep -q " D tohost$"
"$sim" +permissive +permissive-off /build/boom_functional_smoke.elf
printf "BOOM-FUNCTIONAL-SMOKE-V1 status=OK config=chipyard.SmallBoomConfig workload=sum-store-load-tohost evidence=rtl-simulation-functional adapter=not-emitted performance=not-measured\n"'
