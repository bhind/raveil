# ADR-0055: Weekly sprints coordinate work but do not promote evidence

Status: Superseded
Date: 2026-08-23
Superseded by: ADR-0056

## Context

Raveil has stable task IDs, gated research records, dedicated branches, and
milestone reviews, but no fixed short cadence for limiting concurrent work,
revising estimates, or demonstrating an executable increment. The project is
primarily developed by one owner with constrained time and money, so prolonged
work without a visible checkpoint has high opportunity cost.

A sprint board must not become a second source of task truth or allow a weekly
ceremony to promote an implementation, measurement, or Gate without evidence.

## Decision

Use one-week repository-native sprints with a Markdown task board, Fibonacci
story points, a mid-sprint estimate correction, a runnable review demo, and a
short retrospective. Default committed capacity is eight points and WIP is
limited to two items until closed-sprint evidence supports recalibration.

The board references stable T-IDs. `TODO.md` remains authoritative for task
scope and completion, and ROADMAP/ADR/EXP rules remain authoritative for gates,
decisions, and claims. Initial estimates are immutable observations; revisions
record the new estimate, date, and reason. Research review remains
milestone-driven rather than being replaced by the weekly cadence.

Every sprint must attempt a runnable increment. Failure is a valid review
result when the last working baseline and exact failing boundary are shown
honestly. A sprint demo never changes an evidence class by itself.

## Consequences

- Weekly work has a visible goal, capacity, WIP limit, executable review, and
  retrospective improvement.
- Story points expose estimation error but are not converted into hours,
  productivity rankings, or research importance.
- Unfinished work is re-estimated and recommitted; it receives no partial
  completion credit.
- Sprint records can trigger normal governance or research review, but cannot
  close tasks, accept decisions, conclude experiments, or pass gates without
  the existing required verification and record reconciliation.
- Calendar-triggered automation remains optional external tooling. The
  repository workflow is complete and executable without a hosted service.
