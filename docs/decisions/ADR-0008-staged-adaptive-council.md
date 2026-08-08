# ADR-0008: Staged multi-policy Adaptive Council

Status: Proposed
Date: 2026-08-08

## Context

A linear progression in which heuristics are simply replaced by increasingly
expensive learned systems wastes easy opportunities and risks policy
monoculture. Local optimization can also become stale.

## Proposal

Use layered proposers and reviewers:

- immediate heuristics and cached exact reuse;
- measured local search and bandit/Bayesian policies;
- learned cost/representation models;
- LLM structural or meta-level proposals;
- periodic independent review of stable local choices.

Budget consultation using expected future reuse and saved time minus search,
verification, storage, and risk cost. Do not use majority voting. Decide
separately what runs now, what dissenting candidate receives shadow testing,
and which proposer earns later compute budget. Store minority evidence.

## Required evidence before acceptance

- comparison against a single-policy baseline under a fixed total optimizer
  budget;
- calibration and negative-transfer results;
- reviewer cost and frequency;
- a case where dissent or periodic review improves a stale choice;
- authority remains with contract checks, target measurement, and rollback.

## Open consequences

Council state, proposer identities, budget accounting, and anti-correlation
measures require owned schemas. No production LLM is authorized by this RFC.
