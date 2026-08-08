# Raveil vision

Status: research thesis
Last updated: 2026-08-08

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
2. Keep RISC-V as the permanent boot, control, exception, admission, trusted
   baseline, and irregular-work fallback architecture.
3. Explore a Daphnis execution plane that may use static, elastic dataflow,
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

- Under the same target measurement budget, bounded Experience improves
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
- The minimal Sonatine seed is not yet a secure multi-user operating system.
