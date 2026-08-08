# Sonatine Microkernel debugging on macOS

Classification: reusable development guide

This guide records the verified command-line path and the observed IntelliJ
IDEA C/C++ plugin behavior. Actual machine evidence and tool versions belong in
[EXP-0002](../experiments/EXP-0002-sonatine-rv64-reproducibility.md).

## Prerequisites

Confirm the installed tools instead of assuming their Homebrew names:

```bash
command -v riscv64-elf-gcc
command -v riscv64-elf-gdb
command -v qemu-system-riscv64
```

The verified Apple Silicon installation used the
`/opt/homebrew/bin/riscv64-elf-` prefix.

## Release build and smoke test

```bash
make -C sonatine clean
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf-
file sonatine/build/sonatine.elf

make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  smoke
```

Inspect the entry symbols with:

```bash
/opt/homebrew/bin/riscv64-elf-nm -n sonatine/build/sonatine.elf \
  | grep -E '(_start|trap_entry|kmain)'
```

The C entry point is `kmain`, not `kernel_main`.

## Checking debug symbols

Build and check the isolated debug ELF:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  check-debug

/opt/homebrew/bin/riscv64-elf-readelf -S sonatine/build/debug/sonatine.elf \
  | grep -E '\.debug_(info|line)'
```

If the output is empty, the ELF cannot support verified source-line
breakpoints. The debug mode uses `-Og -g3` for C and `-g3` for assembly,
builds under `sonatine/build/debug/`, and leaves the release `-Os` objects
under `sonatine/build/`.

## Command-line GDB target

Start QEMU paused in terminal 1:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  debug
```

Connect in terminal 2:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  gdb
```

The `gdb` target loads `build/debug/sonatine.elf`, connects to
`127.0.0.1:1234`, and creates a `kmain` breakpoint. At the GDB prompt:

```gdb
continue
```

The verified result stops at `src/kernel.c:25`. This proves command-line
source debugging only; do not infer IDE attachment from it.

## IntelliJ IDEA C/C++ plugin

The observed IntelliJ installation exposed:

```text
Settings
-> Build, Execution, Deployment
-> Toolchains
```

The toolchain used:

| Field | Value |
|---|---|
| Name | `Raveil RISC-V` |
| C Compiler | `/opt/homebrew/bin/riscv64-elf-gcc` |
| C++ Compiler | `/opt/homebrew/bin/riscv64-elf-g++` |
| Debugger | Not specified |

It did not expose CMake or Build Tool fields on that screen, nor an observed
Makefile settings page or Debug Profiles page.

The Custom Build Target used `/usr/bin/make`, working directory
`$ProjectFileDir$/sonatine`, and:

- build arguments:
  `CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- all`;
- clean arguments: `clean`.

`Build Project` and `Rebuild Project` were usable even though
`Build -> Clean` remained disabled.

Before documenting IDE attachment, inspect
`Run -> Edit Configurations... -> +` in the installed plugin. Use a genuine
C/C++ remote GDB configuration only if present. Do not use Remote JVM Debug or
copy CLion-specific fields into this guide.

The inspected IntelliJ 2026.2 plugins provide `Remote Debug` with type ID
`CLion_Remote`. For Sonatine use:

- target: `127.0.0.1:1234`;
- symbol file: `sonatine/build/debug/sonatine.elf`;
- debugger: the `Raveil RISC-V` custom GDB profile;
- sysroot: empty;
- path mappings: normally unnecessary for the current DWARF paths.

Do not select `Remote GDB Server`; that configuration launches a remote
`gdbserver` and does not attach to an already-running QEMU stub. Create the
`Remote Debug` configuration once through the installed IDE UI and read back
the generated XML before sharing it, because debugger-profile serialization is
version-sensitive.
