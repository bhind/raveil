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

## Executable track A: Sonatine RV64 seed

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
- `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, `reboot` commands。

Not implemented:

- Sv39 page tables;
- U-mode isolation;
- PMP policy;
- real task context switching and preemption;
- blocking scheduler semantics;
- capability derivation/delegation;
- device-tree memory discovery;
- submission/completion ring and Daphnis device。

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

The current acceptance suite contains eight tests covering the Python loop and
host-executable Sonatine task/capability/IPC logic. On 2026-08-08 all eight
passed on the user-operated macOS tree with Python 3.14.6 and Apple Clang
21.0.0. Freestanding C sources were also syntax-checked by that suite.

The artifact-creating environment did not contain QEMU or a RISC-V cross
compiler. On 2026-08-08, a user-operated Apple Silicon/Homebrew environment
successfully produced `sonatine/build/sonatine.elf` with the
`riscv64-elf-` toolchain. `file` identified it as a 64-bit RISC-V ELF, and
`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain` symbols.

That local ELF contained `.symtab` and `.strtab`, but no `.debug_info` or
`.debug_line`; source-level debugging is therefore not yet configured.

On 2026-08-08, the existing ELF passed the native Homebrew
`make -C sonatine ... smoke` path under QEMU 11.0.3 with exit status 0.
The complete console transcript, tool versions, Git code revision, and ignored
smoke-log hash are recorded in `EXP-0002`. This session did not perform a
clean rebuild, Docker reproduction, or GDB attachment, so Gate 0 remains in
progress.

## Non-claims

- ToyDaphnis cycle values are analytical scaffolding, not accelerator performance.
- QEMU correctness would not establish FPGA/ASIC timing or isolation security.
- The Four-plane architecture, Rust/C++ split, Miroirs, Pavane, Boléro, Ondine,
  La Valse, Scarbo, and native Daphnis are intended architecture, not all present
  in this minimal tree.
- No claim of removing general-purpose OoO hardware has been demonstrated.
