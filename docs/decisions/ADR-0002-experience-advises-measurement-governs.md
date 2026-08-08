# ADR-0002: Experience advises; measurement governs commit

Status: Accepted
Date: 2026-08-07

## Context

History, heuristics, solvers, and learned systems can be wrong or transfer
poorly. Letting a proposal source certify itself would collapse the safety
boundary.

## Decision

Experience may retrieve, rank, and propose. A candidate must pass contract,
capability, resource, structural, semantic/numerical, measurement, and rollback
boundaries before production commit. A trusted baseline remains available.

## Consequences

Learned components stay off the authority path. Target measurement consumes
budget but creates auditable evidence. The current Python Tuner implements only
the baseline-first and target-measurement subset; it does not prove graph
semantics.
