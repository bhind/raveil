# Raveil gated roadmap

Status: planning record
Last updated: 2026-08-09

Gates are evidence requirements, not calendar promises. Passing a later-looking
prototype does not waive an earlier correctness or reproducibility gate.

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

State: **In progress**

The replayable pilot/full manifests, environment/measurement/policy schemas, 24
native-C holdouts, checksum harness, analysis functions, and immutable
raw-bundle lifecycle are implemented. A non-claim powermetrics pilot must
validate sampling and thermal stability before the full run. That pilot now
passes with a sealed and remotely verified bundle; a preceding sampler-startup
failure is also preserved. No Gate 1 performance dataset exists. Compare cold prior,
full-history nearest neighbor, bounded
Experience, FIFO, reservoir, and random under lineage, shape, working-set, and
composition holdouts. Report latency/energy HCR, NTR, coverage, calibration,
budget, retrieval cost, storage, and evidence class.

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

State: **Planned**

Make the platform contract explicit or parse the device tree; add Sv39, U-mode
`init`, context switching, timer preemption, blocking capability IPC, and
fault tests.

Exit: the current shell remains observable from U-mode and survives preemption
without a capability bypass.

Filesystem and command-prompt growth follows this kernel line: a minimal VFS,
RamFS/initramfs, then—after the isolation/scheduling base is credible—VirtIO
block and a simple persistent filesystem such as FAT32. This is a staged
direction, not an implemented feature or production-OS compatibility promise.

## Gate 3 — connect authority and evidence

State: **Planned**

Define JobDescriptor, ObjectManifest, and CompletionRecord; add
submission/completion rings; append measured telemetry to Experience; implement
shadow execution, cancellation, commit, and rollback; enforce Four-plane write
authority.

## Gate 4 — one owned adaptive graph path

State: **Planned**

Import one pinned real workload behind an adapter; define Raveil-owned
GraphVariant, MemoryPlan, OptimizationProposal, and ResourceCertificate; add
Miroirs Graph Compiler structural validation and Pavane Semantic Oracle differential checking; compare static,
elastic, stream, and hybrid execution models.

An AI-compute demonstration may then test a small Transformer, including
prefill/decode and memory-regime variants, if Gate 1 results justify it.

## Post-Gate-4 compatibility track — bounded x86-64 frontend

State: **Planned; blocked on owned semantic and graph contracts**

After RFC-0001's semantic IR, effect/object rules, `ExecutionContract`, and
fallback boundary are stable, validate RFC-0003 incrementally: a tiny x86-64
instruction subset, region cache, Experience-aware promotion, a bounded Linux
userspace subset, then x86 memory-order differential tests. Windows and broad
desktop compatibility remain out of scope. This track does not change Gate 1
or claim current x86 execution support.

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
