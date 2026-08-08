# Sonatine debugging on macOS

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

Check for source debug information:

```bash
/opt/homebrew/bin/riscv64-elf-readelf -S sonatine/build/sonatine.elf \
  | grep -E '\.debug_(info|line)'
```

If the output is empty, the ELF cannot support verified source-line
breakpoints. A debug mode should use `-Og -g3` for C and `-g3` for assembly
without weakening the release `-Os` path. Consult [STATUS](../STATUS.md),
[TODO](../../TODO.md), and
[EXP-0002](../experiments/EXP-0002-sonatine-rv64-reproducibility.md) for the
current implementation and verification state.

## Command-line GDB target

When the current STATUS confirms debug symbols exist, start QEMU paused:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  debug
```

Then connect:

```bash
/opt/homebrew/bin/riscv64-elf-gdb sonatine/build/sonatine.elf
```

```gdb
target remote 127.0.0.1:1234
break kmain
continue
```

Record the actual breakpoint and source-line result in EXP-0002. Do not claim
IDE debugging from command-line GDB evidence alone.

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
