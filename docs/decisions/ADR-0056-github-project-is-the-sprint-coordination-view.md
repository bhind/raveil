# ADR-0056: GitHub Project is the sprint coordination view

Status: Accepted
Date: 2026-08-23
Supersedes: ADR-0055

## Context

ADR-0055 accepted a repository-native Markdown sprint board and validator. The
owner then selected GitHub Projects as the preferred visible Kanban surface.
Keeping both as live boards would duplicate status, estimates, and review
outcomes and create reconciliation work with no product or research value.

GitHub Project state must remain coordination metadata. It cannot replace
Raveil's executable evidence, stable T-IDs, canonical records, research gates,
or evidence classifications.

## Decision

Use the private, repository-linked `Raveil Weekly Sprints` GitHub Project as
the sole live sprint board. Use seven-day GitHub Iterations, retained initial
and current Fibonacci story points, a mid-sprint estimate correction with a
dated reason, a runnable review demo, and a short retrospective.

Default committed capacity is eight points and WIP is limited to two items
until closed-sprint evidence supports recalibration. Project items retain the
stable T-ID in their title. `TODO.md` remains authoritative for task scope and
completion; ROADMAP, ADR, RFC, and EXP rules remain authoritative for gates,
decisions, and claims. Research review remains milestone-driven.

Every sprint attempts a runnable increment. Failure is valid when the last
working baseline and exact failing boundary are shown honestly. A sprint demo
never changes an evidence class by itself.

## Consequences

- The Markdown board and validator proposed by ADR-0055 are not adopted as a
  second live sprint surface.
- Weekly work has one visible goal, capacity, WIP limit, executable review, and
  retrospective surface.
- Story points expose estimation error but are not hours, productivity
  rankings, or research importance.
- Unfinished work is re-estimated and recommitted without partial credit.
- Project items may trigger governance or research review, but cannot close
  tasks, accept decisions, conclude experiments, or pass gates without the
  required repository verification and record reconciliation.
- The Project begins private. Public visibility requires a separate owner
  decision and review of draft research context.
- Calendar-triggered agent execution remains optional external tooling. The
  owner or primary agent initiates each weekly ceremony against the Project.
