# ADR-0058: Incident-free pull requests merge immediately

Status: Accepted
Date: 2026-08-23
Supersedes: ADR-0051 HCI-03 and ADR-0057 only for the per-PR merge-confirmation requirement

## Context

ADR-0051 made every remote PR merge a Human-confirmation incident. ADR-0057
then required every `main` change to use a pull request but retained that
per-merge acknowledgement. The owner now authorizes continuous integration of
verified PRs when no substantive incident exists. Requiring another ceremonial
confirmation after the bounded work, evidence, diff, and mergeability have all
passed creates idle time without protecting an additional authority boundary.

This does not authorize direct `main` pushes or weaken any scientific,
destructive, evidence, cost, credential, legal, or user-work boundary.

## Decision

Give the Project Manager standing authority to merge an incident-free pull
request immediately. Before merge, verify all of the following:

1. The PR contains only the authorized coherent change and descends from its
   named authority or has reconciled the current `main` descendant.
2. Required tests, replay commands, record checker, and `git diff --check` pass
   at the recorded revision in proportion to the change.
3. STATUS, TODO, ROADMAP, OPEN_QUESTIONS, ADR/RFC/EXP, and the dated log are
   reconciled where required.
4. GitHub reports the PR mergeable, required checks pass, and review threads
   are resolved.
5. No ADR-0051 HCI class applies, including gate or EXP authority, evidence
   ambiguity, user-work overlap, destructive action, scope fork, external cost,
   credentials, legal risk, or repeated failure.

When all five conditions hold, merge without another acknowledgement. When any
condition fails, preserve the PR and evidence, continue safe diagnosis, and
request the exact missing authority only if the condition is an HCI.

## Consequences

- Verified PRs no longer idle for ceremonial merge approval.
- Direct push to `main` remains technically blocked with no bypass actor.
- Remote branch deletion is not implied by merge and remains a separate
  destructive action.
- A merge does not by itself complete a task, accept a gate, conclude an EXP,
  promote evidence, publish a benchmark, or authorize the next scope.
- ADR-0051 remains authoritative for every HCI except the unconditional
  classification of an otherwise incident-free PR merge as HCI-03.
- ADR-0057 remains authoritative for PR-only `main` integration and branch
  protection; only its per-merge human acknowledgement is superseded.
