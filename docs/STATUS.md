# Current status

Last updated: 2026-08-11
Development state: `unreleased`
Latest feature release: `v0.0000000000001` (`10^-13`), immutable historical seed
Current Pre-release: `v0.0000000000002`, T-0092 Sonatine operator demo,
published from `d59873cb8e27bf033b32a2a72d2fa3d04576dc79`
Current corrective Pre-release: `v0.0000000000003`, T-0096 interactive
control fix, published from `c8002cf4d87e6a0a907f9327dc42cce2c90e9673`
Current Native Pre-release: `v0.0000000000004`, T-0099 Native CLI workspace,
published from `3cfb13c762b51291d08d519126286aad078df7a1`
Current Command Graph Pre-release: `v0.0000000000005`, T-0101 Native Command
Graph, published from `8ba6c17794d27913b6c8f2b5318be6f6296488ac`.
Current Native CLI Pre-release: `v0.0000000000006`, T-0102 bounded Tab
completion, published from `5f3d8d0d0a3a609af7ffc25a8be40aeb78bf6524`.

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
The agent call-sign catalog is also local-only under ignored `.codex/` state;
the root `AgentNames.md` is absent and explicitly ignored. Historical releases
that already contained it remain immutable provenance.

ADR-0026 adds lightweight defect governance. Existing experiment failures,
negative results, regression tests, and logs remain authoritative evidence;
`docs/FAILURE_KNOWLEDGE.md` indexes reusable prevention lessons, and the GitHub
bug template captures actionable defects without making Issues project
authority. Same-branch corrected defects do not require issue-tracker churn.

Gate 0 is complete, so tracked work now uses a dedicated
`<type>/<record-id>-<short-slug>` lowercase branch.

## Delivery-line state

The manufacturing line resumed for the sole P0 T-0086 after T-0087
reconciliation. ADR-0024 makes a
GNU/Linux userspace graph vertical slice the next delivery line without
discarding any current artifact. Sonatine Microkernel (Sonatine), the Linux harness,
shared job/object/completion contracts, job rings, completion telemetry,
Experience infrastructure, EXP-0003 evidence, and metadata-shadow finalization
remain implemented and preserved.

T-0086 is implemented by selective port onto the T-0087 milestone state. The
donor branch was not merged, so none of its deletions or stale records entered
the result.

## GNU/Linux userspace graph MVP

T-0098 adds `python3 -m raveil shell` as the primary human-facing Native
userspace path. One explicit session owns the current graph, canonical variant
slate, proposal, execution result, and local command history while delegating
all authority to the existing GraphCompiler, AnalyticalPredictor,
Miroirs/Pavane-backed GraphExecutor, and NativeCBackend. Invalid order,
malformed arguments, duplicate execution, and overwrite fail without a
traceback. Results retain `raveil.graph-mvp-result/v1` and remain host-
correctness development evidence only.

T-0099 adds `--workspace PATH` and fixes one existing real directory as the
session's virtual `/`. Bounded `pwd`, `cd`, `ls`, `cat`, `stat`, `mkdir`, and
exclusive `write` commands share one `NativeWorkspace`; graph result files use
the same virtual path boundary. Parent traversal, symlink components, broken
links, special files, excessive paths/files/listings, root replacement, and
overwrite fail closed without exposing host absolute paths. The existing
GraphCompiler, adviser, Miroirs/Pavane-backed GraphExecutor, NativeCBackend,
baseline-first rule, commit/rollback, and result v1 remain unchanged.

This is application-level workspace containment and host-correctness evidence,
not hostile-code isolation. T-0100 remains open for descriptor-relative and
platform-enforced worker isolation. Sonatine and its shell are unchanged.

T-0101 adds a separate strict `CommandGraphProgram` rather than reusing tensor
graphs for shell work. The Native CLI now supports direct `run`, deterministic
`graph compile`, command `graph show`, baseline-first `graph execute --compare`,
balanced development `graph benchmark`, and exclusive `graph result`. The
bounded grammar covers quoted argv, pipelines, redirection, success/sequence
edges, and owned `|||` join-fanout over hash-bound allowlisted host tools.
Direct and DAG executors use equal workspace snapshots, controlled environments,
resource limits, and concurrency; exact stdout/status/output agreement gates
publication. Failure, timeout, stale identity, undeclared mutation, and output
collision remain uncommitted. Existing GEMM behavior and schemas are unchanged.

The manual `cat | grep | wc` demo returned `2` through real host tools and exact
direct/graph agreement. Its four-repetition timing is development/non-claim;
EXP-0004 remains Planned; the smoke sets `crossover_evaluated=false` and makes
no performance claim.
The current direct interpreter buffers pipeline stages, so benchmark records
mark ordinary-pipeline and scheduling claims ineligible; EXP-0004 retains the
concurrent OS-pipeline baseline as required future measurement work.

T-0102 adds host readline/libedit Tab completion without changing dispatch or
authority. Completion candidates are limited to documented commands, graph
subcommands/options, the fixed Command Graph tool allowlist, and bounded
virtual-workspace paths. Symlinks and host paths are omitted; completed input
still passes through the existing parser, workspace checks, and guarded graph
flow. Completion is ephemeral host usability, not expansion, arbitrary PATH
lookup, persistence, or an OS isolation boundary.

ADR-0025 implements one OS/ISA-neutral owned `GraphProgram` and
`ExecutionContract` for bounded GEMM and GEMM+bias+ReLU graphs. A fixed
structural compiler emits a unique baseline-first slate; an analytical adviser
either proposes an admitted variant or abstains. The executor always runs and
semantically validates the trusted baseline first, compares a proposed result
against both its reference checksum and the baseline, and then records explicit
commit or rollback. Invalid baselines fail closed.

The `graph-mvp` CLI compiles the existing native-C adapter with strict C11,
executes the vertical slice, and exclusively creates a segregated
`raveil.graph-mvp-result/v1` JSON result. The result is host-correctness
evidence, not Experience, MeasurementRecord, completion telemetry, silicon
performance, or energy evidence.

T-0090 makes backend choice explicit. `native` remains the default.
`sonatine-qemu` accepts one bounded GEMM of at most 8x8x8 through a versioned
128-byte pointer-free request loaded into the fixed QEMU RAM contract. Sonatine
validates it, reuses JobDescriptor, ObjectManifest, rings, CompletionRecord,
approval, and metadata finalization, then emits one request-bound result frame.
The host rejects missing, duplicate, stale, malformed, unknown, unapproved,
timeout, or nonzero-exit results. Its evidence class is fixed to
`qemu-emulation-correctness`, and latency is deliberately absent.

The verified 8x8 GEMM path runs the trusted baseline, produces the same exact
checksum as the native backend, and records explicit adviser abstention. QEMU
`EXECUTED` is not sufficient: semantic validity is exposed only after exact
checksum agreement plus Sonatine approval/finalization.

T-0041 now gives `GraphVariant`, `MemoryPlan`, and `OptimizationProposal`
strict v1 schemas with exact-key deserialization. Variants bind the owned
program and execution-contract identities; proposals additionally bind the
complete ordered candidate set. The executor rejects stale or malformed
lineage before invoking a backend. The bounded host-memory plan remains
descriptive and is not resource-enforcement or performance evidence.

T-0043 makes the named Miroirs and Pavane boundaries executable in the same
OS/ISA-neutral frontend. Miroirs rejects any graph, contract, variant slate, or
proposal that differs from the canonical owned compiler output before a backend
call. Pavane independently regenerates the deterministic `int32` inputs,
executes the bounded `int64` GEMM or GEMM+bias+ReLU reference, computes the
owned FNV-1a checksum, and compares both baseline and candidate observations to
that expected value. Backend-supplied `semantic_valid` and reference checksums
cannot approve a self-consistent wrong result. Semantic approval remains
independent of selection timing, so the timing-free Sonatine/QEMU baseline
continues to support explicit abstention.

T-0040 adds the first pinned upstream compiler import under ADR-0032. The
adapter admits only the repository-authored 8x8x8 i32-input/i64-accumulation
GEMM fixture, verifies its strict manifest and SHA-256, checks
`iree-base-compiler` package 3.11.0 and exact compiler revision, bounds the
subprocess and private VMFB, and emits only the existing canonical
`GraphProgram` plus a separate pointer-free `raveil.graph-import/v1`
provenance sidecar. The imported graph then follows the
unchanged Miroirs, baseline-first, Pavane, proposal/abstention, and explicit
commit/rollback path. No MLIR/IREE object or VMFB enters an owned public
contract.

The GNU/Linux arm64 container compiled the real fixture and completed the
native graph demo with explicit abstention and an exact valid baseline. This is
compiler/import and host correctness only. IREE runtime execution, general
MLIR import, optimization quality, latency, energy, FPGA, ASIC, and silicon
remain non-claims.

The native result adapter and Sonatine serial adapter now also reject
non-canonical scalar encodings, wrong JSON types, missing fields, negative
latency, zero cookies, and invalid binding ranges. These checks are correctness
boundaries only and create no performance or hardware claim.

The completed tree passed the full local test suite plus RV64 release/debug,
DWARF, U-mode shell, telemetry replay, and graph differential checks. A Linux arm64 container
also passed the 29 focused graph/backend tests and actual QEMU/native
differential. These are host and emulation correctness results only.

Sixteen focused tests pass on native macOS and in a Debian 12 arm64 GNU/Linux
container. The real Linux smoke ran baseline then candidate and chose rollback
because the candidate did not improve that development run. This is functional
control-loop evidence only. Sonatine and all prior artifacts remain unchanged.

## Executable track A: Sonatine Microkernel RV64 seed

QEMU RISC-V `virt`向けのfreestanding kernel seedがあります。

T-0034 adds an executable Four-plane write firewall under ADR-0030. Program,
Graph, Data, and Experience use distinct capability object types and exact
type/right/owner/generation checks. Fixed boot-scoped registries seal full
Program identities and Program-bound Graph identities. The normal job path
requires Data authority for object registration, submission, and metadata
publication; separate Program authority gates injected semantic approval;
Experience authority admits only a bounded consumed-completion observation.

The public job authority header no longer exposes unguarded registration,
submission, approval, or finalization functions. Host tests exercise all 16
plane-capability/operation combinations, identity mismatch, wrong owner,
attenuated delegation, and revoked-handle denial. QEMU smoke executes the same
guarded path. This is a single-hart volatile kernel policy seed, not physical
plane isolation, persistent authority, per-object least privilege, DMA/IOMMU,
or hardware evidence.

Implemented:

- RV64 machine-mode entry、one hart、fixed 128 MiB memory contract;
- versioned `qemu-virt-rv64-v1` platform contract with pinned QEMU `virt`,
  `rv64` CPU, 128 MiB RAM, one hart, no firmware, and compile/test assertions
  tying the fixed MMIO/RAM assumptions to the launch configuration;
- Sv39 page-table construction with a supervisor-only 128 MiB kernel identity
  map, an explicit non-executable user window, page-walk validation, and an
  aligned `satp` root; current M-mode execution does not yet enforce the maps;
- transient U-mode init/fault probes followed by a persistent scripted U-mode
  shell copied into separate U/R/X code and U/R/W stack pages, with RAM-only
  PMP admission and trusted kernel-stack trap entry through `mscratch`; the
  retained M-mode diagnostic shell is not entered by the normal boot path;
- fail-closed U-mode trap disposition: an illegal-instruction probe and unknown
  syscalls return through trusted kernel-stack control and ABI state to the
  diagnostic kernel instead of resuming or hanging;
- a persistent scripted U-mode shell task with current-task-bound console,
  clock, and scalar endpoint syscalls; no user-provided task/owner identity,
  `CONTROL` operation, kernel pointer, or arbitrary user pointer crosses the
  syscall veneer;
- a line-oriented `raveil-u> ` U-mode command shell with an eight-byte
  task-owned scalar buffer, CR/LF/CRLF handling, empty-line suppression,
  backspace/delete editing, fail-closed overflow recovery, explicit unknown
  command errors, and `help`, `info`, `ticks`, `ipc`, `fs`, and `exit`;
- a T-0092 native operator demo adding `ls`, `cat`, `echo`, `write`, `stat`,
  `jobs`, `run`, `cancel`, and `result`; VFS commands use the real bounded
  nodes, while graph commands require a distinct non-delegable demo capability
  and reuse the bound job/completion, Experience-observation, byte-shadow,
  independent fixed-GEMM semantic comparison, approval, commit, cancellation,
  and rollback seams;
- an exact bounded `RAVEIL-SONATINE-DEMO-V1` frame with monotonic sequence and
  a strict host `sonatine-demo` runner. The runner binds repository revision,
  kernel and input SHA-256, fixed transcript, QEMU/Python versions, every frame,
  final state, semantic result, checksum, and exit status into one exclusively
  published `raveil.sonatine-demo-result/v1` JSON record;
- command state that remains intact across real CLINT preemption without
  passing a line pointer to the kernel; the only added console operation emits
  one seven-bit scalar byte after current-task and capability validation;
- T-0096 correction removes per-preemption UART prose from normal
  operation and treats ETX as an operator request for the same current-task-
  checked shutdown used by `exit`; local and fresh-clone QEMU verification
  passed and v0.0000000000003 is published as a Pre-release;
- non-blocking U-mode console reads that return `WOULD_BLOCK` instead of
  polling in M-mode with interrupts masked; M-origin faults take a distinct
  fail-stop path, and seed shutdown is restricted to the scheduler-registered
  U-mode init task;
- one shared 272-byte M/U trap frame preserving x1-x31, interrupted `sp`,
  `mepc`, and `mstatus`, with `mscratch` bound to the running context's trusted
  kernel-stack top;
- `.bss` initializationと16 KiB boot stack;
- NS16550A polled console;
- 4 KiB bitmap physical-page allocator;
- owner、type、rights、generationを持つ64-entry capability table;
- `init`と`idle`のfixed kernel task records;
- an RV64 callee-saved context frame and independent 4 KiB idle stack, with a
  verified cooperative `init -> idle -> init` round trip;
- CLINT 100 Hz timer-driven preemption that switches `init -> idle -> init`
  from a live U-mode shell to M-mode idle and back to the same user frame;
- a non-reentrant timer-dispatch guard that rejects nested scheduling without
  changing the incoming frame/PC, incrementing the tick, or performing another
  context selection;
- capability-checked four-message IPC endpoint;
- queued IPC blocking/retry state transitions with operation-specific wake-up,
  distinct denied/invalid results, and ready-only task selection;
- `CONTROL`-authorized capability delegation to non-recursive leaf grants with
  nonempty attenuated rights and independent generation-checked revocation;
- kernel-derived smoke evidence for forged, wrong-owner, and send-only receive
  capability rejection, followed by a valid endpoint round trip;
- a two-node VFS with immutable initramfs `/hello`, volatile bounded RamFS
  `/scratch`, filesystem root capabilities, and pointer-free byte I/O from the
  persistent U-mode shell before and after CLINT preemption;
- fail-closed capability generation exhaustion that retires a slot instead of
  wrapping an old handle back into validity;
- CLINT 100 Hz machine timerとinteger register trap frame;
- a retained legacy `raveil>` M-mode diagnostic shell implementation that is
  no longer entered by the normal smoke boot path;
- `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, `reboot` commands;
- release `-Os` build and isolated `DEBUG=1` `-Og -g3` build;
- `make debug` QEMU GDB server and `make gdb` command-line client entry
  points;
- Docker build context exclusion for host artifacts and a clean container
  release build;
- local Gate 0 CI script for host tests, release/debug RV64 builds, DWARF
  inspection, and QEMU smoke. Hosted CI/CD is intentionally not configured。

Not implemented:

- S-mode kernel execution;
- PMP policy;
- persistent scheduling of multiple user contexts;
- persistent multi-user blocking scheduler execution, cancellation, and
  fairness;
- capability derivation trees and cascading revocation;
- device-tree memory discovery;
- real Daphnis Execution Subsystem device, MMIO/DMA/IRQ transport, and
  U-mode-facing submission path.

## Linux driver-development harness

Linux is implemented as a non-authoritative development/transport-validation
host under ADR-0019. The tree contains a Raveil-owned fixed-width v1 PING/NOP
ABI, a pure-C one-inflight contract core, and Linux-only unprivileged
`SOCK_SEQPACKET` daemon/client sources. The daemon uses a mode-0600 socket under
`XDG_RUNTIME_DIR`, accepts one client, verifies `SO_PEERCRED` against its own
UID, rejects partial/version/size/flags/opcode-invalid messages, and copies no
user pointer into the contract.

The protocol core is host-tested. A Debian bookworm arm64 Docker build compiled
the Linux-only daemon/client with GCC 12.2.0 and `-Werror`; a UID/GID 65534
container smoke used a private mode-0700 runtime tmpfs, verified socket mode
0600, completed PING, and verified normal socket cleanup. This is Linux
container correctness, not a kernel driver, real Daphnis device, JobDescriptor,
DMA/MMIO/IRQ path, performance result, Experience writer, or Sonatine
replacement.

## Shared job/completion contracts

ADR-0020 is implemented as a platform-neutral strict-C11 contract and
validator. JobDescriptor v1 is a fixed 320-byte, four-object envelope with
opaque identities, nonzero resource ceilings, generation/version/range/effect
references, and fail-closed reserved/unused slots. CompletionRecord v1 is a
fixed 176-byte observation carrying job ID plus execution epoch, sequence, and
cookie claims; T-0031 must enforce their trusted issuance, equality, and
one-shot consumption. Executed outputs must exactly match WRITE objects and
advance versions.

These validators establish structural correctness only. No executable path yet
resolves descriptor IDs as caller capabilities, commits output, or writes
telemetry to Experience. Linux PING/NOP remains a separate transport envelope.

ADR-0021 implements the kernel-internal T-0031 seed: an exact 64-byte
ObjectManifest v1 validator, fixed eight-entry boot-scoped object table,
four-entry submission and completion rings, and four-entry inflight ledger.
Admission checks ID, generation, visible version, bounds, and permitted effect.
Sonatine issues boot-scoped epoch/sequence/cookie bindings; wrong, stale, or
duplicate completions fail closed and valid completions are consumed once.
Host tests and a QEMU kernel smoke cover the state machine. The rings are
single-hart and kernel-owned; they are not Linux, U-mode, shared-memory, DMA,
MMIO, IRQ, hardware, or performance evidence. `EXECUTED` does not change the
visible object version or commit data.

ADR-0022 implements the T-0032 emulation telemetry seed. After successful
one-shot completion consumption, Sonatine emits one bounded versioned UART
frame with binding, observed status/detail/output versions, and QEMU machine
timer ticks spanning the kernel smoke path from manifest construction through
completion consumption. This is not execution latency. The host CLI ingests
only this frame into a separate mode-0600,
single-writer, hash-chained append-only cold journal with raw-log provenance and
full-history duplicate detection. Source/backend/evidence/platform are fixed to
Sonatine/QEMU/emulation and cannot be overridden by guest data. Re-ingesting the
same source is idempotent.

Completion telemetry is not `ExperienceRecord`, `MeasurementRecord`, semantic
validity, commit evidence, silicon performance, energy evidence, or active
retrieval input. Serial authenticity, crash-spanning exactly-once delivery,
cross-boot uniqueness, and real Daphnis telemetry remain unimplemented.

ADR-0023 implements the T-0033 kernel-owned metadata-shadow lifecycle.
Completion consumption retains the exact binding and descriptor until an
explicit one-shot commit or rollback. `EXECUTED` alone cannot commit; the seed
requires a separate injected kernel approval and revalidates every READ/WRITE
object generation, visible version, and range. All outputs must be exact
successor versions and multi-output publication prevalidates every target
before changing any visible version. Conflicting writers, cancellation, stale
bindings, missing approval, and replay fail closed.

ADR-0031 completes T-0085's bounded byte-shadow seed. Each object owns at most
512 visible bytes; admission snapshots referenced bytes, Data authority stages
only exact consumed-completion WRITE ranges, Program approval requires complete
coverage and freezes the shadow, and finalization publishes bytes with exact-
successor versions only after whole-transaction revalidation. Rollback,
cancellation, conflict, missing approval, and replay preserve visible bytes and
zero the shadow. The QEMU graph path stages its real GEMM output and validates
the checksum again from the committed backing.

This is still a volatile, single-hart, copy-based kernel seed. It provides no
general allocator, real Daphnis device, DMA/cache ordering, persistent recovery,
multi-hart atomicity, U-mode byte API, or hardware evidence. Queued cancellation
discards undispatched state; dispatched cancellation is sticky and a late
`EXECUTED` observation cannot commit.

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
- neural representation、GAN/AAE、ANN;
- cross-hardware learned transfer;
- multi-objective Pareto policy;
- transactional database and distributed Experience。

## Verification status

The original Gate 0 acceptance suite contains nine tests covering the Python
loop, host-executable Sonatine Microkernel task/capability/IPC logic, and the
isolated debug-build contract. The current host acceptance suite contains 61
tests. On 2026-08-11 all 61 passed on macOS with Python 3.14.6; they include
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
  maintenance-mode verification facility. Sonatine Gate 2 is complete on QEMU
  emulation evidence; this is not physical-hardware isolation evidence.
