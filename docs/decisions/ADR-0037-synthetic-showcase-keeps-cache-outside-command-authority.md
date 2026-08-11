# ADR-0037: Synthetic showcase keeps derived-artifact cache outside command authority

Status: Accepted
Date: 2026-08-11

## Context

T-0103 must let an operator see why an independent file-processing graph can
help while preserving the baseline-first, semantic, and advice-only boundaries
of ADR-0025 and ADR-0036. A demonstration that labels arbitrary old output as
"reused" would make an unverifiable performance story; embedding a persistent
cache into `CommandGraphExecutor` without a lineage and invalidation design
would silently expand production authority.

## Decision

T-0103 uses a synthetic, deterministic `sort` fan-out and a separate
showcase-only derived-artifact cache. A reusable cache payload binds the
complete CommandNode recipe and hash-bound tool identity, active input SHA-256,
and its own payload SHA-256. Every changed node is rerun through the existing
direct-versus-Graph semantic comparison before a cache payload is created.
Unchanged nodes may be displayed as reused only after all three bindings are
rechecked.

The cache does not enter `CommandGraphExecutor`, `CommandGraphProgram`,
Experience, measurement records, admission, scheduling, semantic validation,
commit authority, or EXP-0004. Baseline-first work remains displayed as
evaluation cost. The command surface states `production_reuse=not-implemented`
and T-0104 owns a future production design.

## Consequences

- The demonstration can honestly show initial execution, deterministic
  one-input invalidation, and verified reuse without claiming a deployed
  incremental executor.
- Experience remains advice-only and deliberately unconnected to this surface.
- Sequential and equal-concurrency direct baselines stay separate from the DAG
  candidate; no worker-count difference becomes a Graph claim.
- The ordinary host ISA remains the execution substrate. No special ISA, FPGA,
  ASIC, or silicon claim enters this decision.

## Verification

Acceptance requires deterministic initial and post-mutation tests proving
16 executed then 1 executed/15 reused/1 invalidated, exact semantic comparison
for executed nodes, cache-payload rehashing, the small-overhead control, and a
human CLI transcript. EXP-0004 remains Planned.
