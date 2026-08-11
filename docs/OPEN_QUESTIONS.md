# Open questions

Last updated: 2026-08-11

These items are intentionally unresolved. A conversation hypothesis does not
become implementation authority until an Accepted ADR or reproducible EXP
resolves it.

## Native execution

- ADR-0020 fixes the bounded job/completion envelope. ADR-0021 fixes only a
  boot-scoped, kernel-owned ObjectManifest table and ring seed. Persistent
  object lifecycle, graph encoding, memory consistency, exception semantics,
  reset uniqueness, and device transport remain open.
- ADR-0022 fixes QEMU completion ingestion as segregated cold evidence. What
  acknowledgement/retry and durable boot identity are required for
  crash-spanning exactly-once real-device telemetry remain open.
- ADR-0023 fixes single-hart metadata-version finalization and cancel-wins
  behavior. How should byte-shadow storage, cache/DMA ordering, verifier
  identity, reset recovery, and persistent multi-object atomicity work?
- Which dependencies and alias facts can admission prove without making compile
  or verification cost impractical?
- Where is the measured boundary between static, elastic dataflow, stream, and
  hybrid Daphnis Execution Subsystem organizations?
- How large should the RISC-V core's OoO machinery be, if any?
- Which regions remain on RISC-V or bounded dynamic tiles: pointer chasing,
  interpreters, JITs, branch-heavy control, exceptions, and unpredictable
  traversal?
- Can Daphnis handle variable latency without recreating a large centralized
  scoreboard, replay system, runahead engine, or OoO window?

## Experience and policy

- Does Experience generalize frequently enough to amortize its search and
  verification cost?
- Which consolidation method best retains ranking reversals, rare failures, and
  negative-transfer boundaries under a fixed online budget?
- How should evidence age across software, compiler, firmware, and hardware
  changes?
- When should retrieval abstain rather than transfer?
- How are latency, energy, memory, tail risk, and correctness combined:
  weighted score, constraints, or Pareto selection?
- How should the Adaptive Council allocate proposer and reviewer budgets without
  majority-vote failure or policy monoculture?
- What access pattern and scale, if any, justify an Experience Processing Unit?

## Measurement

- Under what new workload and candidate-separation pilot should Experience
  research resume after fixed-C and pinned TVM both falsified the Gate 1 5%
  transfer hypothesis?
- Which Transformer or other AI workload is small enough to reproduce yet
  repeated enough to demonstrate useful Experience transfer?
- What threshold makes Negative Transfer Rate unacceptable?
- How should semantic and numerical equivalence be tested for approximate AI
  workloads?

## Kernel and platform

- After human evaluation of the Native Interactive CLI, which concrete missing
  operation or isolation property, if any, warrants further Sonatine shell
  expansion rather than another Native userspace increment?

- After the ADR-0024 GNU/Linux userspace MVP, which measured property, if any,
  justifies promoting Sonatine, a Linux kernel adapter, RISC-V, or another
  specialized authority path to a release prerequisite?

- Parse the QEMU device tree or retain an explicit fixed-machine contract?
- ADR-0018 fixes the pre-VirtIO seed as two bounded root nodes, pointer-free
  scalar I/O, immutable initramfs, and volatile RamFS. Arbitrary paths,
  copyin/copyout, and per-node authority remain future design.
- ADR-0015 fixes Gate 2 delegation as attenuated, non-recursive leaf grants.
  ADR-0016 retires a flat capability slot before its generation can wrap.
  Which derivation-tree, cascading-revocation, and endpoint object-lifetime
  semantics are needed before Daphnis rings are exposed to U-mode?
- After T-0030 fixes JobDescriptor and CompletionRecord, which Linux transport
  should follow the ADR-0019 userspace harness: a kernel adapter, vhost-user,
  VirtIO, PCI, or another owned boundary? DMA/IOMMU/IRQ/reset remain undecided.
- ADR-0030 uses one coarse Data-producer authority domain and volatile
  boot-scoped Program/Graph registries. Before untrusted multi-user or device
  exposure, which per-object capability, persistent identity, revocation-tree,
  reset, and signed-admission rules are required?
- ADR-0031 fixes the current object backing at 512 bytes and single-hart
  copy-based publication. Which allocator, DMA/cache ordering, device reset,
  persistent recovery, and multi-hart publication protocol should replace this
  seed before real-device exposure?
- Does the installed IntelliJ C/C++ plugin expose a genuine remote GDB run
  configuration? The observed UI has not established this.

## Ecosystem

- After the T-0101 allowlisted command-graph slice, which additional shell
  grammar and tools provide enough real workload coverage to justify their
  authority and portability cost? General `sh -c`, arbitrary executable
  lookup, command substitution, and ambient environment inheritance remain
  unresolved, not implied follow-ups.
- After human evaluation of T-0099's executable bounded workspace CLI, which
  T-0100 strong
  isolation backend should become required for release: Linux Landlock plus
  descriptor-relative resolution, a mount-namespace sandbox, an OCI/VM worker,
  or a packaged macOS App Sandbox helper? Application-level containment alone
  is not an answer for hostile-input isolation.
- ADR-0032 fixes only one static linalg fixture and pinned IREE compiler. Which
  additional dialects, tensor signatures, import-record evolution, and
  sandboxed compiler distributions are justified before a general frontend?
- What immutable environment receipt, base-image digest, and OS resource
  limits are required before the pinned compiler adapter may process anything
  beyond repository-owned allowlisted sources?
- Which upstream components should be integrated, wrapped, progressively
  replaced, or rejected?
- What measured threshold—performance, memory, energy, variance, security, or
  adaptability—justifies replacing a mature upstream implementation?
