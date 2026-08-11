# Raveil gated roadmap

Status: planning record
Last updated: 2026-08-11

Gates are evidence requirements, not calendar promises. Passing a later-looking
prototype does not waive an earlier correctness or reproducibility gate.

## Current research reset and delivery focus

State: **T-0105 Chisel/RISC-V substrate bootstrap; CPU thesis remains untested**

The first Experience measurement campaign began before the CPU/ISA thesis,
matched controls, observation points, and candidate microarchitecture were
fixed. Its negative evidence remains valid for its narrow preregistered
Experience hypothesis, but it cannot answer whether low-level explicit-graph
execution can simplify or outperform an in-order or OoO CPU. More measurement
or process-demo work would repeat that ordering error.

The corrected critical path is:

1. **T-0105 — reproducible substrate:** pin Chisel and an RTL simulator,
   elaborate and simulate a trivial owned circuit, then execute one unmodified
   RISC-V reference configuration. This proves tooling only and may precede
   Graph-schema work.
2. **T-0057A — direct-prior-art boundary:** inventory conventional OoO,
   EPIC/VLIW, TRIPS/EDGE, WaveScalar, DySER and spatial-CGRA mechanisms with
   exact locators, counterevidence and preliminary patent/IP triage. This may
   reject mechanisms; it does not authorize adoption.
3. **T-0057B — hypothesis and contract:** only after 0057A, freeze one low-level
   operation, dependency, effect, alias, object, memory-order, commit, fallback,
   semantic-oracle and no-go contract; choose a workload that does not
   predetermine a win.
4. **T-0042 — owned RTL adapter:** implement the smallest admitted Graph
   execution model behind owned types in the pinned environment.
5. **T-0044 — matched comparison:** compare in-order RISC-V, conventional OoO,
   valid same-core diagnostic ablations, and static/elastic/stream/hybrid Graph
   organizations with matched semantics, cache/memory, functional resources,
   and correctness checks.
6. **Transition only after survival:** evaluate an attached engine, custom
   RISC-V extension, programmable fabric, or separate ASIC plane. ARM-hosted
   software is transition/product evidence, not evidence about hidden CPU
   internals.

No performance campaign begins before its comparison contract,
instrumentation, confounders, and stopping rule are recorded. Smoke tests may
establish build and functional correctness only. Simulation, synthesis
estimates, FPGA results, and silicon measurements remain separate evidence
classes.

The Native CLI, T-0103 synthetic tool/process showcase, Sonatine, and EXP-0003
remain preserved artifacts. T-0104 production tool-cache work and further
shell growth are deferred while the critical path above is tested. Sonatine
remains a later OS/capability backend unless evidence makes it necessary.

## High-priority demo extension — Sonatine native operator shell

State: **T-0092 complete (QEMU emulation correctness)**

T-0092 turns the existing U-mode command prompt, two-node capability VFS, and
bounded Sonatine graph lifecycle into one visible operator demo. The target
surface is `ls`, `cat`, `echo`, `write`, `stat`, `jobs`, `run`, `cancel`, and
`result`. Filesystem output must be derived from VFS state. Graph commands must
report real bounded lifecycle states and may use only a fixed built-in demo job;
`cancel` must never report success without a real transition or an explicit
`EMPTY`/`TOO_LATE` result.

Ciste implements and freezes the Sonatine/QEMU serial contract first. Lifri may
then add a host-side runner that launches the pinned QEMU command, drives the
fixed transcript, validates versioned machine-readable frames, and writes one
exclusive replayable JSON record. The record is QEMU emulation correctness,
not performance or production evidence.

This work reuses current owned code only. BusyBox remains an optional external
GPLv2 reference and is not imported or linked for this slice. No ELF loader,
fork/exec, pipe, signal, tty, general argv/environment, POSIX compatibility,
arbitrary user pointer, new Gate claim, or RK3588 replacement enters T-0092.
The exact ownership, acceptance transcript, and sequential handoff prompts are
in [`guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md`](guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md).

The completed slice uses a distinct current-task-bound demo broker capability,
real two-node VFS operations, and one fixed 2x2 integer GEMM lifecycle through
the existing job, completion, Experience-observation, byte-shadow approval,
commit, cancellation, and rollback seams. A strict host runner accepts only the
18 expected versioned frames and exclusively publishes one
`raveil.sonatine-demo-result/v1` record bound to the kernel and input hashes.
This closes the operator demo only; it does not advance Gate 3 or Gate 4.

## Queued visibility side project — graph directory view

State: **T-0093 planned; non-blocking**

T-0093 exposes one validated graph snapshot as an ordinary read-only host
directory so a person can inspect program, contract, node, variant,
memory-plan, proposal, selection, and result relationships with `find`, `tree`,
and `cat`. The materializer consumes only strict existing v1 artifacts, emits a
root manifest with source and output hashes, uses deterministic collision-free
names, and refuses stale lineage, symlinks, traversal, nonempty targets, and
overwrite.

The first slice is a generated inspection artifact, never an authority or
database. It does not mount FUSE, expose a writable graph filesystem, add a
Sonatine VFS namespace, execute a graph, ingest Experience, or make a
performance/security claim. A live `/graphs` namespace requires a later ADR
covering snapshot consistency, capability visibility, lifecycle, and
write-back prohibition; T-0093 deliberately does not pre-decide it.

## Post-MVP side project — ReactOS portability probe

State: **Planned; non-blocking**

T-0091 preserves a ReactOS user-mode port as the first deliberately non-POSIX
host probe after the GNU/Linux MVP. It tests whether the same Raveil-owned v1
graph artifacts and guarded baseline/proposal/abstention/verification/rollback
loop survive an NT-compatible OSS environment without moving OS-specific types
into the owned contracts.

Entry requires the current GNU/Linux/macOS host regressions and exact v1
artifact-lineage tests to remain green. The first probe runs in an isolated
x86/x64 virtual machine because ReactOS documents itself as Alpha-quality and
recommends virtual-machine or non-sensitive test hardware. It may use a direct
Win32 CLI; a message-mode named-pipe adapter is optional and a kernel driver is
out of scope.

Exit requires a pinned ReactOS build and architecture, reproducible cross-build
command, one bounded graph run with trusted baseline-first semantics, semantic
checksum and explicit commit/rollback or abstention, fail-closed unsupported
API/candidate behavior, and replayable environment/result records. All results
are VM host-correctness and portability evidence only. They do not advance a
Gate, establish production Windows compatibility or isolation, reverse
EXP-0003, or substitute for the separate GNU/Linux/AArch64/RK3588 direction.

The port should depend only on documented Win32 interfaces or independently
implemented adapters. ReactOS is GPL-2.0-licensed; implementation kickoff must
revalidate the exact upstream version, license/provenance boundary, and any
source-reuse or IP-review gaps before importing code.

## Gate 0 — independently reproducible minimum seed

State: **Completed**

- all nine host/Python acceptance tests pass from a clean clone;
- release and explicit debug Sonatine Microkernel builds are reproducible;
- debug ELF contains line and debug information;
- native macOS or Docker QEMU smoke transcript is recorded in EXP-0002;
- command-line GDB attaches and stops at `kmain`;
- local CI covers Python, host C, freestanding RV64 build, and QEMU smoke;
- no generated evidence, build output, IDE state, secrets, or local absolute
  paths are committed.

Verified on 2026-08-08: clean native release/debug builds, separated release
and debug flags, DWARF `.debug_info`/`.debug_line`, release QEMU smoke,
command-line GDB stop at `kmain`, clean Docker build and Docker-contained QEMU
smoke. A fresh clone of public commit `3347087` passed all nine tests and both
build modes plus smoke. The same checks are available through
`scripts/ci-local.sh`; hosted CI/CD is intentionally deferred until the project
has multiple contributors and explicit cost approval. The public-tree hygiene
scan found no generated evidence, build output, IDE state, credentials, or
machine-local paths. The actual IntelliJ `Remote Debug` type was verified;
IDE-driven attachment is not a Gate 0 claim.

## Gate 1 — real Experience boundary

State: **Falsified (closed negative)**

The replayable pilot/full manifests, environment/measurement/policy schemas, 24
native-C holdouts, checksum harness, analysis functions, and immutable
raw-bundle lifecycle are implemented. A non-claim powermetrics pilot must
validate sampling and thermal stability before the full run. That pilot now
passes with a sealed and remotely verified bundle; a preceding sampler-startup
failure is also preserved. A sealed and remotely verified 24-workload history
source dataset and a first target policy comparison exist. The first target
run failed the 5% latency/energy improvement and positive bootstrap-lower-bound
criteria. The independent fixed-C rerun confirmed zero median latency/energy
improvement and additionally exceeded the NTR limit, so fixed-C now provides a
reproduced negative conclusion rather than a passing result. The pinned TVM
history/target execution reproduced zero median improvement and exceeded the
joint NTR limit, with immutable remote verification. The preregistered 5%
hypothesis is therefore falsified; this is not a claim that Experience is
universally ineffective. Compare cold prior, full-history nearest
neighbor, bounded Experience, FIFO, reservoir, and random under lineage, shape,
working-set, and composition holdouts. Report latency/energy HCR, NTR, coverage,
calibration, budget, retrieval cost, storage, and evidence class.

Exit requires all of the following in EXP-0003:

- every candidate passes its semantic reference checksum;
- bounded Experience improves holdout median latency and same-Mac estimated
  energy by at least 5% versus cold, and both paired-bootstrap 95% lower bounds
  exceed zero;
- a regression greater than 2% counts as negative transfer and joint NTR is at
  most 5%;
- bounded selection-quality degradation versus full history is at most 2% for
  both latency and energy;
- active memory remains within its limit and bounded retrieval p95 is below
  full history on large evidence;
- immutable local/Google Drive content verification completes, and an
  independent execution reaches the same conclusion;
- the fixed-C contract is repeated through a pinned official apache-tvm
  MetaSchedule adapter. A conclusion conflict triggers research review and
  keeps the Gate open.

## Gate 2 — minimal isolated Sonatine Microkernel slice

State: **Complete (QEMU emulation correctness)**

Make the platform contract explicit or parse the device tree; add Sv39, U-mode
`init`, context switching, timer preemption, blocking capability IPC, and
fault tests.

Exit: the current shell remains observable from U-mode and survives preemption
without a capability bypass.

T-0083 met this exit with a persistent scripted U-mode shell, real CLINT
`U -> idle -> U` resumption, current-task-derived syscall identity, and
kernel-derived rejection evidence for forged, wrong-owner, and insufficient
rights capabilities. This does not claim physical RISC-V isolation, S-mode,
multi-user fairness, or performance.

Filesystem and command-prompt growth follows this kernel line: a minimal VFS,
RamFS/initramfs, then—after the isolation/scheduling base is credible—VirtIO
block and a simple persistent filesystem such as FAT32. This is a staged
direction, not an implemented feature or production-OS compatibility promise.

T-0017 supplies the first step as a bounded two-node, pointer-free VFS seed.
VirtIO and persistent storage remain T-0018.

T-0089 completes the next command-prompt growth step without reopening Gate 2:
the persistent U-mode task now accepts bounded command lines, survives
preemption with partially entered input, and retains current-task capability
authority. This remains QEMU emulation correctness, not a new isolation or
performance claim.

T-0090 supplies a narrow explicit Sonatine/QEMU backend connection for the
existing userspace graph loop. It reuses Gate 3 job/completion/finalization
artifacts and Gate 4 owned frontend contracts, but supports only an 8-or-smaller
GEMM correctness seed with no timing. Gate 3 and full Gate 4 remain planned;
this adapter by itself did not provide byte-shadow or Four-plane authority.
T-0034 and T-0085 now supply those separate kernel seeds, but not a general
compiler, real device path, or performance completion.

## Gate 3 — connect authority and evidence

State: **Planned**

Remaining specialized-authority work is preserved but paused until the
userspace MVP exposes a concrete requirement. Existing T-0030 through T-0033
artifacts remain valid.

The T-0084 Linux harness is pre-Gate transport scaffolding only. It validates
the owned ABI envelope without claiming a JobDescriptor, device, or authority
path and therefore does not advance Gate 3 state.

T-0030 provides the bounded shared JobDescriptor/CompletionRecord schema, and
T-0031 provides a kernel-internal ObjectManifest/object-table/ring seed with
boot-scoped replay protection. T-0032 adds segregated append-only QEMU
completion telemetry without promoting it to active Experience. Gate 3 remains
Planned until byte-shadow execution, semantic verification, and Four-plane
write authorities are executable. T-0033 now supplies only the kernel-owned
metadata-shadow finalization and cancellation seed.

T-0034 supplies the boot-scoped Four-plane capability firewall and guarded
normal graph path, T-0043 supplies bounded semantic verification, and T-0085
supplies fixed byte-shadow publication. Gate 3 remains Planned because real
device transport/lifetime, persistent recovery, and non-seed authority
integration are still absent.

Define JobDescriptor, ObjectManifest, and CompletionRecord; add
submission/completion rings; append measured telemetry to Experience; implement
shadow execution, cancellation, commit, and rollback; enforce Four-plane write
authority.

## Gate 4 — one owned adaptive graph path

State: **T-0086 narrow vertical slice complete; full Gate remains planned**

Import one pinned real workload behind an adapter; define Raveil-owned
GraphVariant, MemoryPlan, OptimizationProposal, and ResourceCertificate; add
Miroirs Graph Compiler structural validation and Pavane Semantic Oracle differential checking; compare static,
elastic, stream, and hybrid execution models.

An AI-compute demonstration may then test a small Transformer, including
prefill/decode and memory-regime variants, if Gate 1 results justify it.

T-0086 intentionally precedes the full exit: it proves the product control
loop on an existing OS/ISA and replaceable native backend. It does not require
a new kernel, ISA, driver, FPGA, or complete graph compiler.

The verified slice now covers owned graph/contract construction, trusted
baseline-first execution, candidate proposal or abstention, structural and
checksum semantic validation, explicit candidate selection or rollback, and
segregated host-correctness evidence on GNU/Linux. It does not satisfy the
remaining full Gate 4 compiler, workload, resource-certificate, or semantic
oracle scope.

T-0041 additionally makes `GraphVariant`, `MemoryPlan`, and
`OptimizationProposal` strict versioned artifacts and rejects stale program,
contract, or candidate-set lineage before backend execution. This closes the
owned schema slice only; the Gate state and remaining exit scope are unchanged.

T-0043 supplies executable Miroirs structural admission and an independent
Pavane deterministic integer reference for the two bounded MVP graph families.
Native and Sonatine observations must match the owned expected checksum;
semantic approval is not inferred from backend self-report or timing. This
closes the current semantic-oracle slice, while full Gate 4 remains planned for
the pinned real-workload import, mapper/resource boundary, and broader compiler
scope.

T-0040 adds one pinned real-workload import under ADR-0032. A bounded,
repository-authored MLIR GEMM fixture is validated by IREE 3.11.0 and reduced
to the existing owned `GraphProgram` plus a strict provenance record before
the unchanged guarded graph loop runs. This closes the single-workload import
slice only; the mapper/resource-certificate and broader compiler scope keep
full Gate 4 planned.

## Gate 5 — hardware exploration

State: **T-0105 substrate bootstrap; Graph hardware evidence not yet started**

Profile stable software access patterns before considering an Experience
Processing Unit, FPGA fabric, or ASIC. Hardware claims require separate
simulation, FPGA, and silicon experiment records.

RFC-0004 proposes the pre-FPGA foundation. T-0105 may establish the generic
Chisel/simulator/RISC-V substrate independently; T-0057 must first bound direct
prior art and IP risk, then freeze the owned low-level Graph contract before
T-0042 implements any Graph RTL. T-0044 then uses
matched RISC-V configurations under a common cache, memory, workload,
functional-resource, and correctness envelope. Rocket/BOOM remain candidate
references, not adopted product code, ARM equivalents, or proof that OoO can
be removed.

## No calendar claim

Early discussion estimated weeks for a shell/RamFS seed and roughly one to one
and a half months of concentrated work for a persistent QEMU prototype. Those
were rough feasibility estimates, not commitments, and production compatibility
would be substantially larger.
