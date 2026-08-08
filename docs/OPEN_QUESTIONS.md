# Open questions

Last updated: 2026-08-08

These items are intentionally unresolved. A conversation hypothesis does not
become implementation authority until an Accepted ADR or reproducible EXP
resolves it.

## Native execution

- What is the versioned encoding of the explicit dependency/effect/object
  contract proposed in RFC-0001?
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

- Will the pinned TVM MetaSchedule adapter reproduce the fixed-C Gate 1
  conclusion, or expose a benchmark-specific transfer result?
- Do the calibrated roughly 400 ms native-C windows consistently yield at least
  three stable powermetrics CPU-power samples across every pilot candidate, or
  must the windows increase again before the full dataset?
- Which Transformer or other AI workload is small enough to reproduce yet
  repeated enough to demonstrate useful Experience transfer?
- What threshold makes Negative Transfer Rate unacceptable?
- How should semantic and numerical equivalence be tested for approximate AI
  workloads?

## Kernel and platform

- Parse the QEMU device tree or retain an explicit fixed-machine contract?
- Which minimal VFS/RamFS/initramfs interface should precede VirtIO/FAT32?
- Which capability derivation and revocation semantics are needed before
  Daphnis rings are exposed to U-mode?
- Does the installed IntelliJ C/C++ plugin expose a genuine remote GDB run
  configuration? The observed UI has not established this.

## Ecosystem

- Which upstream components should be integrated, wrapped, progressively
  replaced, or rejected?
- What measured threshold—performance, memory, energy, variance, security, or
  adaptability—justifies replacing a mature upstream implementation?
