# ADR-0027: Owned graph artifacts bind lineage before execution

Status: Accepted
Date: 2026-08-11

## Context

ADR-0025 established the GNU/Linux userspace graph MVP and named
`GraphVariant`, `MemoryPlan`, and `OptimizationProposal` as Raveil-owned
artifacts. The first slice constructed them in process, but did not yet give
all three strict, independently round-trippable schemas or bind a proposal to
the exact program, execution contract, and candidate set it was allowed to
advise.

Without those bindings, a stale or malformed proposal could be confused with
the current compilation even though the baseline-first and semantic checks
would still limit the final result. T-0041 closes that structural gap without
expanding proposal authority.

## Decision

Raveil owns versioned `GraphVariant`, `MemoryPlan`, and
`OptimizationProposal` v1 JSON-compatible schemas. Deserialization requires
the exact key set, schema identifier, bounded integer and enum values, valid
SHA-256 identities, and internally consistent materialization choices.

Every `GraphVariant` carries the SHA-256 identities of its `GraphProgram` and
`ExecutionContract` plus a validated `MemoryPlan`. Every proposal carries those
same identities and a digest of the complete ordered candidate set. The
executor validates all three bindings before invoking any backend. Unknown,
stale, malformed, or cross-compilation proposals fail closed and cause no
candidate execution.

The analytical predictor remains advisory. It may rank an admitted candidate
or abstain, but cannot change the trusted baseline, candidate slate, structural
checks, semantic comparison, or explicit commit/rollback decision established
by ADR-0025.

The v1 `MemoryPlan` describes only bounded host-memory materialization for the
current fixed GEMM families. It is descriptive contract data, not proof of
allocation enforcement, resource certification, hardware placement, latency,
energy, or silicon behavior.

## Consequences

- Contract values remain OS/ISA-neutral and contain no Python, native-C,
  Linux, compiler, or other upstream-owned public type.
- Results contain complete owned variant and memory-plan records rather than
  implicit in-process objects.
- T-0041 does not complete the full Gate 4 compiler, pinned workload import,
  ResourceCertificate, semantic-oracle, or hardware exploration work.
- Existing Sonatine, Linux harness, job/object/completion contracts, rings,
  telemetry, Experience, EXP-0003, T-0086, and metadata-shadow finalization
  remain unchanged in authority and scope.

## Verification

Acceptance requires strict round-trip tests, rejection of unknown fields and
invalid memory-plan combinations, rejection of stale candidate-set lineage
before any backend call, the T-0086 regression cases, and an actual GNU/Linux
container execution whose output carries the v1 schemas and exact program and
contract identities. Evidence is host correctness only and creates no
performance or hardware claim.
