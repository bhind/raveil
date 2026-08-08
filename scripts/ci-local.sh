#!/bin/sh

set -eu

if command -v riscv64-unknown-elf-gcc >/dev/null 2>&1; then
  cross_compile=riscv64-unknown-elf-
elif command -v riscv64-elf-gcc >/dev/null 2>&1; then
  cross_compile=riscv64-elf-
else
  echo "RISC-V cross compiler not found" >&2
  exit 1
fi

command -v python3
command -v cc
command -v "${cross_compile}gcc"
command -v "${cross_compile}readelf"
command -v qemu-system-riscv64

python3 --version
cc --version | sed -n '1p'
"${cross_compile}gcc" --version | sed -n '1p'
"${cross_compile}readelf" --version | sed -n '1p'
qemu-system-riscv64 --version | sed -n '1p'

python3 -m unittest discover -s tests -v
make -C sonatine clean all CROSS_COMPILE="$cross_compile"
make -C sonatine check-debug CROSS_COMPILE="$cross_compile"
make -C sonatine smoke CROSS_COMPILE="$cross_compile"
