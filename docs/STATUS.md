# Current status

Last updated: 2026-08-09
Version: `0.0000000000001` (`10^-13`)

この文書は構想ではなく、現行treeで実装されている範囲だけを記録します。

## Development workflow support

Repository-scoped Project Manager, three Implementer, Tester, Performance
Reviewer, Security Reviewer, Researcher, and Librarian role definitions are
present. The read-only Librarian plus `raveil-context-librarian` skill rank a
small task-specific reading packet instead of loading all project records.
The Librarian is named Vreji and also reports prior-art similarity and IP-risk
gaps under ADR-0014 while remaining unable to decide infringement, legal
clearance, freedom to operate, or implementation approval.
Task-governance, Gate 0 evidence, and remote-release skills remain available.
These govern development workflow only; local IDEA/MCP endpoints and personal
Codex runtime configuration remain ignored.

Gate 0 is complete, so tracked work now uses a dedicated
`<type>/<record-id>-<short-slug>` lowercase branch.

## Executable track A: Sonatine Microkernel RV64 seed

QEMU RISC-V `virt`向けのfreestanding kernel seedがあります。

Implemented:

- RV64 machine-mode entry、one hart、fixed 128 MiB memory contract;
- versioned `qemu-virt-rv64-v1` platform contract with pinned QEMU `virt`,
  `rv64` CPU, 128 MiB RAM, one hart, no firmware, and compile/test assertions
  tying the fixed MMIO/RAM assumptions to the launch configuration;
- Sv39 page-table construction with a supervisor-only 128 MiB kernel identity
  map, an explicit non-executable user window, page-walk validation, and an
  aligned `satp` root; current M-mode execution does not yet enforce the maps;
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

- S/U privilege transition and enforcement of the constructed Sv39 maps;
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

Gate 1 measurement infrastructure is also implemented:

- versioned BenchmarkManifest, EnvironmentSignature, MeasurementRecord,
  PolicySelection, and PolicyOutcome Python contracts;
- a common `MeasurementBackend.measure(context, candidate)` protocol;
- a committed six-workload powermetrics pilot manifest plus a separate
  24-holdout full manifest separating lineage, shape, working set, and operator
  composition;
- a native C adapter for GEMM, GEMM+bias+ReLU, and two-stage MLP with
  deterministic `int32` inputs, `int64` accumulation, and reference checksum;
- baseline-first, seeded randomized candidate schedules with five repetitions
  for the non-claim pilot and at least 15 for the full experiment;
- a tracked fixed-argument C helper and helper-only non-interactive
  sudo/powermetrics boundary; runtime root-ownership, non-symlink, and
  non-writable-path checks; standalone manifest-aware preflight; a minimum three
  CPU-power samples per measured window; a sampler-readiness barrier that
  excludes exactly its startup observation while preserving later samples
  already buffered in the same read; an explicitly synchronized fake-sampler
  regression that does not infer sample count from elapsed sleep time;
  thermal-stability checks; and same-Mac relative energy calculation;
- an optional, command-recorded between-workload cooldown that idles for a
  configured minimum and requires two consecutive valid thermal preflights;
  measurement-window thermal changes still fail closed and cooldown evidence is
  appended to the run bundle; the same recovery boundary follows backend
  preparation before the first measurement;
- paired-bootstrap, latency/energy HCR, joint NTR, full-history quality-gap,
  active-memory, equal-budget, and retrieval-p95 analysis functions;
- repetition-aware hierarchical-bootstrap sensitivity intervals, per-candidate
  energy-variation and normalized time-block drift diagnostics, plus start/end
  battery, available CPU-frequency, and system-load measurement context;
- fail-closed policy evidence analysis requiring an exact manifest-wide
  cold/bounded/full-history/FIFO/reservoir/random matrix, unique rows, matching
  run/manifest/budget/candidate provenance, preregistration before measurement,
  and summary values recomputed from raw measurements;
- a production policy-plan path that reads a sealed, disjoint-workload source
  run and generates equal-budget cold, full-history, bounded, FIFO, reservoir,
  and random candidate slates; target runs copy the plan before measurement and
  analysis automatically emits slate-bound outcomes;
- a committed 24-workload fixed-C history manifest with distinct IDs, lineage,
  and shapes but the same ten-candidate contract as the target holdouts;
- a target active-memory limit of 64 summary records versus 240 full-history
  records, fixed from source-only simulation before any target measurement;
- per-policy HCR, energy-HCR, coverage, calibration error, NTR, retrieval p95,
  measurement budget, active-memory maximum, and cold-evidence counts;
- `experiment run`, `analyze`, `seal`, and `sync` CLI lifecycle;
- ignored local research bundles with SHA-256/size manifests, immutable sealing,
  rclone immutable copy/download verification, overwrite refusal, and a
  completion marker copied last; mutable writes resolve and remain inside their
  own RUN-ID directory rather than merely the shared artifact root;
- a completed non-claim fixed-C sampler pilot with 90/90 valid semantic and
  measurement records, all nominal thermal samples, minimum power-sample count
  three, and a sealed Google Drive-verified bundle;
- a completed 24-workload fixed-C history-source run with 3,600/3,600 valid
  silicon measurement records, zero checksum mismatches, all nominal thermal
  observations, three-to-fourteen CPU-power samples per window, and a sealed,
  Google Drive-verified bundle;
- a completed first fixed-C target policy run with 3,600/3,600 valid silicon
  measurements and a complete 144-row pre-registered policy matrix; bounded
  retained 64 versus 240 full-history summaries and reduced retrieval p95, but
  its cold-relative median latency and energy improvements were both zero, so
  the Gate improvement and bootstrap criteria did not pass;
- a completed independent fixed-C target rerun with cooldown boundaries,
  3,600/3,600 valid semantic and silicon measurements, all measurement windows
  `Nominal`, a sealed and Google Drive-verified bundle, and the same zero median
  latency/energy improvement conclusion; its joint NTR was 12.5%, so the fixed-C
  Gate hypothesis failed independently;
- a pinned official Apache TVM 0.25.0.post1 / TVM FFI 0.1.12 Apple Silicon
  adapter that lowers the same int32/int64 workload and candidate contracts,
  commits constrained schedules to a MetaSchedule JSON database, queries them
  back before compilation, and passes a 60-kernel semantic/database-reuse smoke;

Not implemented or not yet evidenced:

- real graph IR and equivalence proof;
- a Gate-passing fixed-C policy result;
- system installation and post-`sudo -k` verification of the root-owned
  powermetrics helper and helper-only sudoers rule;
- completed powermetrics datasets for the pinned TVM adapter;
- neural representation、GAN/AAE、ANN;
- cross-hardware learned transfer;
- multi-objective Pareto policy;
- transactional database and distributed Experience。

## Verification status

The original Gate 0 acceptance suite contains nine tests covering the Python
loop, host-executable Sonatine Microkernel task/capability/IPC logic, and the
isolated debug-build contract. The current host acceptance suite contains 49
tests. On 2026-08-10 all 49 passed on macOS with Python 3.14.6; they include
the Gate 1 manifest, native C checksums across all candidate families,
baseline/randomization, timeout/dimension failure, energy/thermal fail-closed
parsing, the compiled helper allowlist and installation-integrity boundary,
standalone preflight, concise CLI failure reporting, statistics,
run/analyze/seal lifecycle, bundle sync command boundaries, agent permissions,
the existing Experience loop, Sonatine host checks, exact six-policy matrix
integrity, preregistration planning and binding, raw-measurement summary
verification, fixed-C/TVM manifest-contract identity,
workload/repetition hierarchical bootstrap, the same-read sampler
readiness/measurement boundary, and cross-RUN mutable path isolation.
This is implementation verification, not EXP-0003 performance evidence.

On the T-0022 policy-integrity worktree, `scripts/ci-local.sh` passed with exit
status 0: all 40 host tests, clean RV64 release/debug builds, DWARF checks, and
QEMU smoke. The ignored emulation smoke-log SHA-256 was
`314c185549dfd5e11e48f467320ac871e3862960bdb4d02d40ba86c909c0475f`.

On the sampler-readiness-corrected 2026-08-08 Gate 1 pilot worktree,
`scripts/ci-local.sh` passed: all 33 host tests, clean RV64 release/debug builds,
DWARF checks, and QEMU smoke completed with exit status 0. The QEMU portion is
emulation regression evidence only.

On the T-0068 least-privilege-helper worktree, `scripts/ci-local.sh` passed with
exit status 0: all 38 host tests, clean RV64 release/debug builds, DWARF checks,
and QEMU smoke. The ignored emulation smoke-log SHA-256 was
`c222caea0fdc41b0b3992a7772ddde6db99e2a693d915afff36283ffa73e018b`.

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
- No Gate 1 latency or energy improvement is claimed. Independent fixed-C and
  pinned TVM target executions both produced zero median latency and energy
  improvement and exceeded the joint NTR limit. Their sealed bundles were
  immutably copied to Google Drive and download-verified. Gate 1 is closed as a
  falsified preregistered 5% hypothesis; the measurement system remains a
  maintenance-mode verification facility while Sonatine Gate 2 is active.
