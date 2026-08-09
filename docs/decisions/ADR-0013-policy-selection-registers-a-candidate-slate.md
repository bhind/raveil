# ADR-0013: Policy selection registers a candidate slate

Status: Accepted
Date: 2026-08-09

## Context

ADR-0012 separates pre-measurement selection from measured outcomes, but its
initial record named one selected candidate while the Gate 1 measurement budget
is three. The final winner cannot honestly be known before measuring the
policy's budgeted candidates.

## Options considered

- pre-register one claimed winner and ignore the remaining budget;
- choose a winner retrospectively from every measured candidate;
- pre-register an ordered, fixed-size candidate slate containing the trusted
  baseline, then select the best measured member under a registered objective.

## Decision

`PolicySelection` v2 registers a unique candidate slate whose length equals the
manifest measurement budget. The trusted baseline is always included. Target
measurement may choose the slate member minimizing the geometric mean of its
latency and energy ratios to baseline. The offline oracle remains the best of
the exhaustive candidate matrix and cannot alter the slate.

Gate 1 compares cold priority, full history, bounded tail-preserving retention,
FIFO, deterministic streaming reservoir, and deterministic uniform-random
retention. Every policy uses the same candidate budget. Selection records also
carry retrieval latency, active/cold evidence sizes, predicted latency/energy
ratios, and abstention so T-0024 metrics can be derived without retrospective
policy metadata.

A selection source and target must share backend, evidence class, and candidate
set, while workload IDs must be disjoint. A source run is sealed before it can
produce a target plan; each selection records its source RUN-ID and sealed
bundle SHA-256. The target runner copies the plan into its bundle before
candidate measurement.

## Rationale

Candidate slates preserve equal-budget comparison and separate proposal quality
from target measurement. Disjoint source/target identities prevent an exact
target result from entering its own proposal history.

## Consequences

- ADR-0012's pre-registration and complete-matrix requirements remain; its
  singular-candidate wording is superseded by the v2 slate.
- A first full source/history run may have no policy plan and cannot produce a
  Gate conclusion. A later disjoint target run consumes the generated plan.
- Actual fixed-C, independent-repeat, and TVM datasets are still required.
- The joint winner objective is a Gate 1 experiment rule, not a universal
  production multi-objective policy.

## Verification and supersession

Tests cover six equal-budget policies, bounded/FIFO/reservoir/random memory
limits, source/target identity separation, slate-bound outcomes, and per-policy
coverage/calibration/resource metrics. A different winner objective or adaptive
budget requires a later ADR.
