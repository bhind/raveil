# Raveil vision

## Current objective — affordable implementation and measurement

The owner's September27 direction prioritizes a reproducible single-board FPGA
demonstrator within an individual budget. Novelty versus Groq may remain modest.
Implement the existing contracts, measure useful work and total lifecycle cost,
and publish honest limitations. A losing CPU comparison is still informative.
[ADR-0105](decisions/ADR-0105-budgeted-fpga-demonstrator.md) replaces the earlier
novelty-first prototype gate; the long-term thesis and prior negative evidence
remain. One board and existing PCs bound the near-term resource scale.


## Earlier research question — retained for later work

Retain the original thesis below: preserve verified execution knowledge over
computation's lifetime. The next test is whether immutable semantic information
can remove execution work, beyond strong existing compiler optimizations,
before choosing a new execution mechanism. This is a hypothesis under
[ADR-0103](decisions/ADR-0103-work-reduction-precedes-new-execution-hardware.md),
not a claim that partial evaluation, explicit graphs, reuse or their combination
is new. [RFC-0007](rfcs/RFC-0007-immutable-function-work-reduction.md) defines
what must be pinned before a mechanism-specific experiment.

Groq's established scheduling, resident memory, reusable kernels and partitioning
are controls. The separate region/buffer and five-execution-principle proposals
are deferred. A software-only benefit remains a valid outcome and is not a
justification for custom hardware. Experience advises search; it cannot certify
semantics or manufacture an advantage. EXP-0003's preregistered 5% hypothesis
was falsified under its tested conditions; this direction does not reverse it.

Status: research thesis
Last updated: 2026-09-23

## Thesis

> A conventional CPU repeatedly reconstructs execution knowledge from a
> sequential stream. Raveil tries to preserve, verify, accumulate, and reuse
> that knowledge across the lifetime of computation.

Raveil is an AI-adaptive computing system. An immutable semantic program and
its execution contract remain the authority. Optimizers propose executable
graphs, memory plans, and hardware mappings; trusted components verify and
measure them; successful and failed trials become reusable Experience.

The intended advantage is not that one AI invocation always discovers the
fastest implementation. It is that recurring workloads can amortize search,
verification, and specialization over future executions.

## Research objectives

1. Preserve explicit dependency, effect, object, resource, and numerical
   information instead of forcing hardware to rediscover it from a sequential
   instruction stream on every execution.
2. Keep authority contracts independent of OS and ISA. Start with GNU/Linux
   userspace and existing CPUs; retain RISC-V/Sonatine as a measured
   specialized authority and irregular-work option rather than an MVP
   prerequisite.
3. Explore a Daphnis Execution Subsystem (Daphnis) that may use static, elastic dataflow,
   stream, or hybrid organization according to measurements.
4. Make optimization history a first-class plane: reusable, bounded online,
   append-only as cold evidence, auditable, and aware of failures.
5. Keep learned systems outside the authority boundary. AI proposes; trusted
   contracts, capabilities, measurements, and rollback govern production.

## Economic objective

Optimization effort is allocated by expected return, conceptually:

```text
future reuse × saved time
  - search cost
  - verification cost
  - storage cost
  - operational and correctness risk
```

Hot, stable computation may justify aggressive search and eventual hardware
specialization. Warm computation is optimized opportunistically. Cold or
archival computation should normally use the generic fallback.

## Initial high-value domain

AI workloads are a likely proving ground because they contain repeated graph
structure, recurring shape and memory regimes, large execution counts, and
important tensor/KV-cache movement. Candidate studies include separate
prefill/decode variants, MoE routing and residency, cross-model subgraph
transfer, and a small Transformer whose behavior can be compared before and
after Experience accumulates.

These are research directions, not implemented features of
`v0.0000000000001`.

## Success conditions

- A future, separately justified Experience study would need to show that,
  under the same target measurement budget, bounded Experience improves
  Headroom Capture Rate over a cold policy on honest holdouts.
- Negative transfer, tail failure, retrieval cost, and storage remain
  controlled as cold evidence grows.
- Every installed variant remains attributable to a semantic identity,
  contract, lineage, measurement environment, and rollback path.
- Structured hot regions avoid unnecessary general dynamic dependency
  discovery without claiming that physically variable timing disappears.
- Static, elastic, stream, and hybrid execution are selected by reproducible
  evidence rather than architectural preference.

## Non-goals and non-claims

- Raveil does not claim that general-purpose OoO execution is obsolete.
- Exact cycle scheduling is not the native contract; hardware still handles
  readiness, backpressure, token movement, and variable latency.
- ToyDaphnis output is analytical scaffolding, not measured hardware speed.
- QEMU evidence is emulation evidence, not FPGA, ASIC, or silicon evidence.
- The minimal Sonatine Microkernel seed is not yet a secure multi-user operating system.
