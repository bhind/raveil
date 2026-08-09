# EXP-0002: Sonatine Microkernel RV64 reproducibility

Status: Completed
Evidence class: QEMU emulation and host-tool inspection
Last updated: 2026-08-08

## Objective

Reproduce the freestanding RV64 build and Sonatine Microkernel (Sonatine) shell from the real Git tree,
verify command-line QEMU/GDB independently of the IDE, and record enough
environment information for Gate 0.

## Environment observed

- MacBook Air `Mac14,15`, Apple M2, 24 GB;
- macOS 26.5.1 build 25F80, arm64;
- original smoke evidence Git revision:
  `d4204e10f62b4d232c6fdcf8a02a098cee595d3a`;
- debug/GDB evidence base revision:
  `88b44d11b777c02f1963c835e99bb317f6d94dbd`, with the Makefile, test,
  and matching record updates uncommitted during collection;
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

`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain`.

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

## Clean release and debug builds

Commands:

```bash
make -C sonatine clean
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf-
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- check-debug
```

All commands exited 0. The release compiler command retained `-Os` and its ELF
had no `.debug_info` or `.debug_line`. The debug build used `-Og -g3` for
C and `-g3` for assembly in a separate `build/debug/` directory.

```text
[ 9] .debug_info  PROGBITS
[15] .debug_line  PROGBITS
[17] .debug_line_str PROGBITS
```

`file` identified the debug artifact as a 64-bit RISC-V ELF with
`debug_info`, not stripped. Its SHA-256 was
`a2852e69e65c21130f19d8b7f2872640a6510eec11a321ef35f40ea499b42125`.

The rebuilt release ELF then passed `make ... smoke` with exit status 0.

## Command-line GDB evidence

Terminal 1:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  debug
```

Terminal 2 used the equivalent of the repository's interactive `make gdb`
target while enabling an ignored raw log:

```bash
/opt/homebrew/bin/riscv64-elf-gdb -q -batch \
  sonatine/build/debug/sonatine.elf \
  -ex 'target remote 127.0.0.1:1234' \
  -ex 'break kmain' \
  -ex 'continue' \
  -ex 'info breakpoints' \
  -ex 'frame' \
  -ex 'list' \
  -ex 'detach'
```

Exit status: 0.

```text
Breakpoint 1 at 0x800006ce: file src/kernel.c, line 25.

Breakpoint 1, kmain () at src/kernel.c:25
25  void kmain(void) {
breakpoint already hit 1 time
#0  kmain () at src/kernel.c:25
```

Raw ignored log: `sonatine/build/debug/gdb-kmain.log`

SHA-256:
`26f0eadfe5a71803e58e554486479b5d7d927de599181fdf886d50f64e0780fd`

The interactive `make debug` plus `make gdb` path was also run and stopped at
the same source line. The first sandboxed attempt could not bind/connect to
localhost; the successful evidence was collected with local TCP permission.

## Clean Docker build and smoke

Environment:

- Docker Desktop 4.85.0;
- Docker client/engine 29.6.2;
- client `darwin/arm64`, engine `linux/arm64`;
- LinuxKit kernel 6.12.76, overlayfs;
- container GCC 12.2.0;
- container QEMU 7.2.22.

The first no-cache image build exposed a validity defect: host
`sonatine/build/` occupied a 1.01 MB context and the Dockerfile reported
`Nothing to be done for 'all'`. That image was rejected as Gate evidence.
`sonatine/.dockerignore` now excludes `build/`, and the Dockerfile runs
`make clean && make`.

Successful clean command:

```bash
docker build --no-cache --progress=plain \
  --iidfile <temporary-iid-file> \
  -t raveil-sonatine:gate0-clean-20260808 \
  sonatine
```

Exit status: 0. The context was 1.18 kB. The log showed `rm -rf build`, all
ten C compilations, both assembly compilations, and the final RV64 link with
release `-Os`. Base image:
`debian:bookworm-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241`.
Result image ID:
`sha256:3225bf6bc3ae06f872e384704499e93f3069629a11dba70f6c4b23a3ad71bf9c`.

Smoke command:

```bash
docker run --rm raveil-sonatine:gate0-clean-20260808 make smoke
```

Exit status: 0. The console contained all six boot `[ok]` lines, the shell,
task and capability tables, successful IPC, page allocation/release, QEMU
finisher exit, and both final grep checks.

Raw temporary smoke log: `raveil-gate0-docker-smoke-20260808.log`

Size: 1018 bytes

SHA-256:
`e6d9a39352cbf598abe834e59365c8f0616db91352b5d2433be5c25542aba0c2`

Evidence class: Docker Desktop Linux/arm64 QEMU emulation, not FPGA or silicon.

## IntelliJ configuration inspection

The installed IntelliJ IDEA 2026.2.0.1 C/C++ and Native Debug plugins expose
`Remote Debug` (type `CLion_Remote`) for an existing GDB stub. `Remote GDB
Server` is a different SSH/upload workflow and is not appropriate for
Sonatine. No Sonatine Remote Debug configuration currently exists, and
IDE-driven `kmain` attachment was not claimed.

## Public clean-clone and CI verification

Public commit: `33470874dd54f577ad3a60320487f6e14b096b9b`

The repository was cloned from `https://github.com/bhind/raveil.git` into a
new temporary directory. The following commands all exited 0:

```bash
python3 -m unittest discover -s tests -v
make -C sonatine clean all CROSS_COMPILE=riscv64-elf-
make -C sonatine check-debug CROSS_COMPILE=riscv64-elf-
make -C sonatine smoke CROSS_COMPILE=riscv64-elf-
```

All nine tests passed. The release and isolated debug builds completed,
`.debug_info` and `.debug_line` were present in the debug ELF, and the smoke
log contained the shell and successful IPC markers.

The same verification is exposed locally as:

```bash
scripts/ci-local.sh
```

A GitHub Actions workflow run (`31248762110`) completed successfully before
the project owner clarified that hosted CI/CD must not be used because of cost.
The workflow was removed immediately afterward. This historical run is not the
current CI policy or a dependency of Gate 0.

The public tracked-file list contained no build directories, IDEA state,
Python bytecode, generated JSONL evidence, or `.env` files. A content scan
found no private-key marker, GitHub credential pattern, or machine-local home
directory path.

Evidence class: fresh public Git clone plus local macOS/QEMU emulation. This
remains software/emulation evidence, not FPGA or silicon evidence.

## Remaining work

None for Gate 0.

QEMU success is emulation evidence only; it does not establish U-mode
isolation, preemptive scheduling, FPGA timing, or silicon behavior.
