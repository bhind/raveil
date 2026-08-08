# Raveil gated roadmap

Status: planning record
Last updated: 2026-08-08

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

State: **Planned**

Replace ToyDaphnis with one replayable measured backend. Compare cold prior,
full-history nearest neighbor, bounded Experience, FIFO, reservoir, and random
under lineage, shape, memory, and composition holdouts. Report HCR, NTR,
coverage, calibration, budget, retrieval cost, storage, and evidence class.

Exit: bounded Experience improves at least one honest holdout without
unacceptable negative transfer.

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
