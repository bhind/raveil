# EXP-0002: Sonatine RV64 reproducibility

Status: In progress
Evidence class: QEMU emulation and host-tool inspection
Last updated: 2026-08-08

## Objective

Reproduce the freestanding RV64 build and Sonatine shell from the real Git tree,
verify command-line QEMU/GDB independently of the IDE, and record enough
environment information for Gate 0.

## Environment observed

- MacBook Air `Mac14,15`, Apple M2, 24 GB;
- macOS 26.5.1 build 25F80, arm64;
- Git code revision:
  `d4204e10f62b4d232c6fdcf8a02a098cee595d3a`;
- `riscv64-elf-gcc (GCC) 16.1.0`;
- `GNU gdb (GDB) 17.2`;
- `QEMU emulator version 11.0.3`;
- Homebrew executable prefix: `/opt/homebrew/bin/`.

Machine serials and unique identifiers are intentionally not recorded.

## Build evidence

A user-operated native build had already generated
`sonatine/build/sonatine.elf`. On 2026-08-08, `file` identified it as:

```text
ELF 64-bit LSB executable, UCB RISC-V, RVC, soft-float ABI,
version 1 (SYSV), statically linked, not stripped
```

`riscv64-elf-nm` had previously confirmed `_start`, `trap_entry`, and
`kmain`. `readelf -S` still finds neither `.debug_info` nor
`.debug_line`; source debugging is not yet enabled.

This session did not clean and rebuild the existing artifact, so clean native
build reproducibility remains open.

## QEMU smoke command

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  smoke
```

Exit status: 0.

Console transcript:

```text
Raveil boot v0.0000000000001
Sonatine kernel (RV64 QEMU virt)
  [ok] console / ns16550a polled UART
  [ok] physical memory / 4 KiB bitmap allocator
  [ok] capability / generation-checked fixed table
  [ok] task / init + idle kernel tasks
  [ok] IPC / bounded mailbox protected by capabilities
  [ok] timer / CLINT machine timer at 100 Hz
starting init task id=1

Raveil shell v0.0000000000001
type 'help' for commands

raveil> info
Raveil 0.0000000000001 / Sonatine RV64 / QEMU virt / M-mode
authority: one hart; paging: off; user isolation: not yet
raveil> mem
RAM pages total=32768 free=32759 first-free=0x80009000
raveil> ps
id  state    name
1   running  init
2   ready    idle
raveil> caps
handle      owner type object rights
0x10001  1     2    1      0x1c
0x10002  1     1    1      0x11
raveil> ticks
0
raveil> ipc
ipc: received tag=0x52 sender=1 word0=0x52415645494c
raveil> alloc
alloc: page=0x80009000 free 32759 -> 32758 -> 32759 (released)
raveil> reboot
leaving QEMU
raveil>
```

Raw ignored log: `sonatine/build/smoke.log`
SHA-256:
`314c185549dfd5e11e48f467320ac871e3862960bdb4d02d40ba86c909c0475f`

## Remaining work

- perform and record a clean native and Docker build;
- add and verify `DEBUG=1` with `.debug_info` and `.debug_line`;
- run QEMU `-S -s`, attach GDB, break at `kmain`, and record the result;
- inspect the actual IntelliJ C/C++ run-configuration list;
- repeat from a clean clone/CI before completing Gate 0.

QEMU success is emulation evidence only; it does not establish U-mode
isolation, preemptive scheduling, FPGA timing, or silicon behavior.
