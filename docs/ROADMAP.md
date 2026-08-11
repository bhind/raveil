# Raveil gated roadmap

Status: planning record
Last updated: 2026-08-11

Gates are evidence requirements, not calendar promises. Passing a later-looking
prototype does not waive an earlier correctness or reproducibility gate.

## Current delivery focus

State: **T-0086 userspace vertical slice complete**

T-0086 was the sole restart P0. It ports the preserved userspace
graph prototype onto current main and demonstrates one owned graph through
baseline, proposal or abstention, structural/semantic checks, commit or
rollback, and evidence output on GNU/Linux. It must preserve every existing
Sonatine Microkernel, Linux harness, contract, telemetry, Experience, and
experiment artifact.

This is an allowed narrow Gate 4 vertical slice under ADR-0024. It does not
claim Gate 3 completion, custom-hardware performance, or a Gate 1 reversal.

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
this adapter is emulation integration evidence, not byte-shadow, Four-plane
authority, general compiler, or performance completion.

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

## Gate 5 — hardware exploration

State: **Blocked by evidence, not implementation difficulty**

Profile stable software access patterns before considering an Experience
Processing Unit, FPGA fabric, or ASIC. Hardware claims require separate
simulation, FPGA, and silicon experiment records.

## No calendar claim

Early discussion estimated weeks for a shell/RamFS seed and roughly one to one
and a half months of concentrated work for a persistent QEMU prototype. Those
were rough feasibility estimates, not commitments, and production compatibility
would be substantially larger.
