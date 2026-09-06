# ADR-0094: Candidate-bound delegated product acceptance

Status: Accepted
Date: 2026-09-06
Task: T-0162
Related: ADR-0014, ADR-0051, ADR-0058

## Context

The human owner requested Librarian audit, delegated Product Owner approval,
and continuous incident-free delivery. Repeating a human approval at every
ordinary revision confuses project acceptance with execution permissions.

## Decision

The Librarian audits the exact candidate read-only and reports concerns and
gaps, not legal clearance or authority. Relevant specialist reviews remain
required. The delegated Product Owner accepts or rejects the audited task
candidate only within the human owner's recorded, current delegation.
The primary Project Manager independently verifies scope, evidence, records
and remote state and retains integration responsibility under ADR-0058.
If one agent holds multiple roles, disclose that; do not invent independent
approval or a human GitHub review. Call signs stay in the local-only catalog.

Bind the audit, acceptance and PM verification receipt to the repository,
task, exact commit/tree/base and intended action. A changed candidate needs
renewed review and acceptance, not renewed human consent, while delegation
remains current and PM revalidates scope and all HCI boundaries.

Before push, verify local evidence and known remote constraints. Unpublished
head checks are unavailable, not passed. After push, read back that exact
head and its checks. Before merge, require ADR-0058's clean mergeability,
required checks, resolved threads, records and technical acceptance.

Project approval never overrides execution review, sandbox rules, GitHub
protection, credentials or paid-resource authority. Preserve a runtime denial;
do not alter security policy, switch agents, or substitute indirect commands
to defeat it. Continue independent authorized work, not equivalent retries.
Seek the missing external authorization through the normal approval mechanism.

## Consequences

Ordinary accepted work proceeds without ceremonial human checkpoints.
All scope, evidence, legal/provenance, cost, destructive and gate incidents
remain human-owned. Task acceptance does not accept the weekly Sprint Review.
This decision defines a project procedure, not an execution-permission system
or proof of operational automatic approval. It does not authorize replaying
the previously rejected T-0161 publication action.
