# ADR-0012: Policy selection is pre-registered evidence

Status: Accepted
Date: 2026-08-09

## Context

Gate 1 measures every candidate to build offline oracle evidence, but an online
policy must not see that oracle before selecting a candidate. A
`PolicyOutcome` containing both a selected candidate and oracle metrics cannot
by itself prove when or how selection occurred. Incomplete holdout coverage,
duplicate rows, or unattested numeric summaries could otherwise produce a
plausible Gate result.

## Options considered

- trust externally produced `PolicyOutcome` JSONL;
- infer selections retrospectively from the measured winner;
- keep selection and measured outcome as separate, bound records and reject any
  incomplete or inconsistent matrix.

## Decision

Gate-evaluable analysis requires two distinct artifacts:

- `PolicySelection` contains no target-oracle values and binds policy,
  workload, selected candidate, measurement budget, source-evidence cutoff,
  registration time, experiment, and manifest SHA-256;
- `PolicyOutcome` binds the resulting run and measured values.

For every manifest workload there must be exactly one `cold`, `bounded`, and
`full-history` selection and outcome. Missing, duplicate, unknown, late,
wrong-manifest, wrong-budget, wrong-run, or unregistered-candidate evidence
fails closed. Analysis recomputes baseline, selected, and offline-oracle
latency/energy medians from `MeasurementRecord` data rather than trusting
submitted summary values.

The selection registration time must precede the first target measurement.
This is a local experiment-contract check, not a claim of adversarial remote
timestamp attestation. Sealing and immutable remote verification preserve the
resulting evidence after analysis.

## Rationale

Separating selection from outcome makes oracle access explicit and testable.
Exact matrix validation prevents a small favorable subset or silent duplicate
overwrite from satisfying aggregate thresholds.

## Consequences

- Existing full-run bundles without both artifacts remain incomplete.
- T-0022 still needs a production path that generates the preregistered policy
  matrix without target measurements.
- Pilot runs remain non-claim measurements and do not require policy evidence.
- Any stronger adversarial attestation scheme requires a later decision.

## Verification and supersession

Tests cover complete matrices, missing/duplicate/unknown outcomes, RUN-ID and
budget mismatch, valid preregistration, duplicate selections, and measured
metric tampering. A later selection protocol must preserve oracle isolation or
explicitly supersede this ADR.

