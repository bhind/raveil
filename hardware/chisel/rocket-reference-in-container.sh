#!/bin/sh
set -eu

ROCKET_SOURCE=${ROCKET_SOURCE:-/rocket}
ROCKET_REVISION=749a3eae9678bc70b029c5b9091fae33fad539c4
ROCKET_ORIGIN=https://github.com/chipsalliance/rocket-chip.git
CDE_REVISION=52768c97a27b254c0cc0ac9401feb55b29e18c28
CHISEL_REVISION=e3bcc90db37f1aec9f8048813f4f0666098d9bee
HARDFLOAT_REVISION=d93aa570806013dea479a92ba9bb33d1f2d4f69f
ELABORATE_CONFIG=freechips.rocketchip.system.DefaultSmallConfig
EXECUTE_CONFIG=freechips.rocketchip.system.DefaultConfig
TEST_SUITE=rv64mi-p
EXPECTED_TESTS=16

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

run_nix() {
    nix \
        --option filter-syscalls false \
        --extra-experimental-features 'nix-command flakes' \
        "$@"
}

check_revision() {
    path=$1
    expected=$2
    actual=$(git -C "$path" rev-parse HEAD)
    [ "$actual" = "$expected" ] ||
        fail "$path is at $actual, expected $expected"
}

[ -d "$ROCKET_SOURCE/.git" ] || fail "Rocket checkout not found at $ROCKET_SOURCE"
check_revision "$ROCKET_SOURCE" "$ROCKET_REVISION"
[ "$(git -C "$ROCKET_SOURCE" remote get-url origin)" = "$ROCKET_ORIGIN" ] ||
    fail "unexpected Rocket origin"
[ -z "$(git -C "$ROCKET_SOURCE" status --porcelain --ignore-submodules=none)" ] ||
    fail "Rocket checkout or a pinned submodule has local changes"
check_revision "$ROCKET_SOURCE/dependencies/cde" "$CDE_REVISION"
check_revision "$ROCKET_SOURCE/dependencies/chisel" "$CHISEL_REVISION"
check_revision "$ROCKET_SOURCE/dependencies/hardfloat" "$HARDFLOAT_REVISION"

cd "$ROCKET_SOURCE"

# A git flake input excludes ignored and untracked build products from Nix
# evaluation. The revision and flake.lock jointly fix the package graph.
flake="git+file://$ROCKET_SOURCE?rev=$ROCKET_REVISION"
packages="${flake}#legacyPackages.x86_64-linux"
spike_root=$(run_nix eval --raw "${packages}.spike.outPath")
riscv_tests_root=$(run_nix eval --raw "${packages}.riscvTests.outPath")

printf '%s\n' \
    'ROCKET-REFERENCE-SMOKE-V1 phase=environment evidence=rtl-simulation-functional'

run_nix shell \
    "${packages}.mill" \
    "${packages}.circt" \
    "${packages}.dtc" \
    "${packages}.verilator" \
    "${packages}.cmake" \
    "${packages}.ninja" \
    "${packages}.clang" \
    "${packages}.spike" \
    "${packages}.riscvTests" \
    "${packages}.coreutils" \
    "${packages}.findutils" \
    -c env \
        SPIKE_ROOT="$spike_root" \
        RISCV_TESTS_ROOT="$riscv_tests_root" \
        ROCKET_REVISION="$ROCKET_REVISION" \
        ELABORATE_CONFIG="$ELABORATE_CONFIG" \
        EXECUTE_CONFIG="$EXECUTE_CONFIG" \
        TEST_SUITE="$TEST_SUITE" \
        EXPECTED_TESTS="$EXPECTED_TESTS" \
        sh -c '
set -eu

nix --version
mill -i --version
firtool --version
verilator --version
clang --version
cmake --version
ninja --version
dtc --version

mill -i "emulator[freechips.rocketchip.system.TestHarness,$ELABORATE_CONFIG].generator.elaborate"
mill -i "runnable-riscv-test[freechips.rocketchip.system.TestHarness,$EXECUTE_CONFIG,$TEST_SUITE,none].run"

passed_dir="out/runnable-riscv-test/freechips.rocketchip.system.TestHarness/$EXECUTE_CONFIG/$TEST_SUITE/none/run.dest"
set -- "$passed_dir"/*.passed.log
[ -f "$1" ] || {
    echo "error: no passed test logs under $passed_dir" >&2
    exit 1
}
passed_count=$#
failed_count=$(find "$passed_dir" -type f -name "*.failed.log" -print | wc -l)
passed_count=$(printf "%s" "$passed_count" | tr -d "[:space:]")
failed_count=$(printf "%s" "$failed_count" | tr -d "[:space:]")
[ "$passed_count" = "$EXPECTED_TESTS" ] || {
    echo "error: expected $EXPECTED_TESTS passed tests, found $passed_count" >&2
    exit 1
}
[ "$failed_count" = 0 ] || {
    echo "error: found $failed_count failed test logs" >&2
    exit 1
}

printf "ROCKET-REFERENCE-SMOKE-V1 status=OK revision=%s elaborate_config=%s execute_config=%s suite=%s passed=%s failed=%s evidence=rtl-simulation-functional graph_rtl=not-implemented performance=not-measured\n" \
    "$ROCKET_REVISION" "$ELABORATE_CONFIG" "$EXECUTE_CONFIG" "$TEST_SUITE" \
    "$passed_count" "$failed_count"
'
