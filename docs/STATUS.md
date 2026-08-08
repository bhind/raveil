# Current status

Last updated: 2026-08-08
Version: `0.0000000000001` (`10^-13`)

この文書は構想ではなく、現行treeで実装されている範囲だけを記録します。

## Development workflow support

Repository-scoped Codex explorer, reviewer, and verifier role definitions and
two instruction-only skills are present. They govern development workflow only:
they do not alter either executable seed, accepted architecture, or evidence
class. Local IDEA/MCP endpoints and personal Codex runtime configuration remain
ignored.

## Executable track A: Sonatine Microkernel RV64 seed

QEMU RISC-V `virt`向けのfreestanding kernel seedがあります。

Implemented:

- RV64 machine-mode entry、one hart、fixed 128 MiB memory contract;
- `.bss` initializationと16 KiB boot stack;
- NS16550A polled console;
- 4 KiB bitmap physical-page allocator;
- owner、type、rights、generationを持つ64-entry capability table;
- `init`と`idle`のfixed kernel task records;
- capability-checked four-message IPC endpoint;
- CLINT 100 Hz machine timerとinteger register trap frame;
- `raveil>` shell;
- `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, `reboot` commands;
- release `-Os` build and isolated `DEBUG=1` `-Og -g3` build;
- `make debug` QEMU GDB server and `make gdb` command-line client entry
  points;
- Docker build context exclusion for host artifacts and a clean container
  release build;
- local Gate 0 CI script for host tests, release/debug RV64 builds, DWARF
  inspection, and QEMU smoke. Hosted CI/CD is intentionally not configured。

Not implemented:

- Sv39 page tables;
- U-mode isolation;
- PMP policy;
- real task context switching and preemption;
- blocking scheduler semantics;
- capability derivation/delegation;
- device-tree memory discovery;
- submission/completion ring and Daphnis Execution Subsystem device。

## Executable track B: bounded Experience seed

Python標準ライブラリだけで、次の閉ループがあります。

- immutable JSONL cold evidence;
- fixed-limit active Experience;
- repeated exact observationのaggregation;
- invalid、negative transfer、strong improvementを優先するtail retention;
- workload/hardware/shape/memory distanceによるnearest retrieval;
- typed candidate ranking;
- trusted baseline first measurement;
- deterministic analytical ToyDaphnis backend;
- cold/warm HCR benchmark。

Not implemented:

- real graph IR and equivalence proof;
- real CPU/compiler/accelerator measurement;
- neural representation、GAN/AAE、ANN;
- cross-hardware learned transfer;
- multi-objective Pareto policy;
- transactional database and distributed Experience。

## Verification status

The current acceptance suite contains nine tests covering the Python loop,
host-executable Sonatine Microkernel task/capability/IPC logic, and the isolated debug-build
contract. On 2026-08-08 all nine
passed on the user-operated macOS tree with Python 3.14.6 and Apple Clang
21.0.0. Freestanding C sources were also syntax-checked by that suite.

The artifact-creating environment did not contain QEMU or a RISC-V cross
compiler. On 2026-08-08, a user-operated Apple Silicon/Homebrew environment
successfully produced `sonatine/build/sonatine.elf` with the
`riscv64-elf-` toolchain. `file` identified it as a 64-bit RISC-V ELF, and
`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain` symbols.

On 2026-08-08 the native Homebrew path performed a clean release build, a
separate debug build, release QEMU smoke, and command-line GDB verification.
The release ELF contains no DWARF debug sections. The debug ELF contains
`.debug_info` and `.debug_line`; GDB 17.2 connected to QEMU 11.0.3,
installed a `kmain` breakpoint, and stopped at `src/kernel.c:25` with source
lines available.

Exact commands, tool versions, Git base revision, console output, and ignored
raw-log hashes are recorded in `EXP-0002`. A clean no-cache Docker build and
Docker-contained QEMU smoke also passed. Public commit `3347087` was then
cloned into a fresh directory: all nine tests, release and debug builds, DWARF
checks, and QEMU smoke passed. The same checks pass through
`scripts/ci-local.sh`. A GitHub Actions workflow briefly ran once during Gate 0
work before the local-only policy was clarified; it was then removed, and no
hosted CI/CD remains configured. A public-tree scan found no generated
evidence, build output, IDE state, credentials, or machine-local absolute
paths. Gate 0 is complete.

The installed IntelliJ 2026.2 C/C++ plugin exposes `Remote Debug`
(`CLion_Remote`) for attaching to an existing QEMU GDB stub. The configuration
type and required fields were inspected, but no claim of a completed
IDE-driven attach is made.

## Non-claims

- ToyDaphnis cycle values are analytical scaffolding, not accelerator performance.
- QEMU correctness would not establish FPGA/ASIC timing or isolation security.
- The Four-plane architecture, Rust/C++ split, Miroirs Graph Compiler, Pavane Semantic Oracle,
  Boléro Experience Runtime, Ondine Object Memory Subsystem, La Valse Optimization Subsystem,
  Scarbo Verification Subsystem, and native Daphnis Execution Subsystem are intended architecture, not all present
  in this minimal tree.
- No claim of removing general-purpose OoO hardware has been demonstrated.
