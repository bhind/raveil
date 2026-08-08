# RFC-0001: Native explicit dependency/effect graph machine

Status: Proposed
Date: 2026-08-08

## Problem

A sequential register load/store stream hides dependency, alias, and effect
knowledge that may already be known upstream. A conventional high-performance
core then spends energy and area reconstructing that knowledge through rename,
issue, speculation, queues, and replay on every execution.

Replacing x86 with a conventional RISC-V instruction stream does not by itself
remove this problem. The relevant boundary is sequential register ISA versus an
explicit graph/effect execution contract.

## Proposal

Work submitted to the Daphnis Execution Subsystem (Daphnis) is a sealed graph carrying:

- explicit data and control dependencies;
- object-scoped READ, WRITE, and external effects;
- object versions and bounded address ranges;
- resource contracts;
- preferred placement, route, and MemoryPlan;
- semantic and numerical constraints;
- ProgramIdentity, parent lineage, and target hardware signature.

For example, two object reads and one object write can be admitted as:

```text
Object A READ ----+
                  +--> ADD --> Object C WRITE
Object B READ ----+
```

Admission proves allowed effects and object independence before installation.
The encoding does not prescribe exact cycles. Hardware handles readiness,
backpressure, arbitration, token movement, and physically variable completion.

## Dynamic islands

Pointer chasing, highly data-dependent traversal, JIT/interpreter execution,
exceptions, and unpredictable control may remain on RISC-V or use bounded
dynamic tiles. The goal is to stop imposing general dependency discovery on
structured repeated computation, not to deny dynamic uncertainty.

## Alternatives

- Conventional RISC-V only: simple contract, but preserves repeated dynamic
  discovery in hot structured code.
- Classic VLIW: exposes scheduling but is brittle under variable latency and
  hardware-width changes.
- Fully dynamic dataflow: flexible, but risks expensive token matching and
  scheduling machinery.
- Static/elastic/stream hybrid: leading comparison set, not yet selected.

## Authority and safety

AI cannot emit installable state directly. Miroirs Graph Compiler (Miroirs) validates structure;
Program/Execution contracts validate effects; resource certificates bound
usage; Pavane Semantic Oracle (Pavane) or another trusted path checks semantics; Sonatine Microkernel (Sonatine) installs,
measures, commits, or rolls back.

## Required experiments

1. Define a minimal versioned graph/effect schema and alias/object rules.
2. Translate one repeated CPU or tensor workload and preserve a trusted
   fallback.
3. Compare encoding/configuration overhead, readiness machinery, memory traffic,
   latency, energy proxy, and tail behavior against sequential and VLIW-like
   baselines.
4. Isolate an irregular subgraph and measure fallback/island boundary cost.
5. Demonstrate that dynamic support does not recreate a general centralized OoO
   structure.

## Open questions

The exact encoding, verifier complexity, memory consistency rules, exception
model, dynamic-island ABI, and static/elastic/stream split remain unresolved.
