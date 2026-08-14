# Task start phases and work-in-progress handling

Status: active planning guide
Date: 2026-08-14
Authority: TODO task assignments, ROADMAP gates, accepted ADRs

## Purpose

Prevent unfinished branches, sunk effort, interesting side projects, or broad
hardening checklists from displacing the smallest experiment that tests the
current thesis. A TODO checkbox states whether a task is complete; its phase
states when work may begin.

## Phases

- **P0 — immediate:** the single default implementation focus.
- **P1 — next:** begins only after P0 passes its recorded exit contract.
- **P2 — result-conditioned:** begins only after a named go result or separately
  accepted product requirement.
- **P3 — future planned:** intended work without a start date. The Project
  Manager selects and promotes it after the critical research decision.
- **P4 — optional/triggered:** no default start. It may become mandatory when
  its explicit trigger occurs, but remains dormant until then.

The canonical task-to-phase mapping is the table at the top of `TODO.md`.

## Work-in-progress limit

Only one coherent P0 implementation task is active by default. Parallel work is
limited to read-only review, reproducibility checks, or a separately recorded
independent blocker investigation. A second implementation branch requires a
dated decision naming why it cannot wait and what resource owns it.

Existing partial work is handled as follows:

1. Preserve verified commits, failure evidence, and exact source locators.
2. Do not merge, finish, or expand a partial branch solely because it exists.
3. Map its remaining work to the owning task and phase.
4. Leave unverified local modifications explicitly non-authoritative.
5. Resume only after the task is promoted or when a bounded action is necessary
   to preserve otherwise-lost evidence.

For the current reset, the controlled common-resource T-0042 slice is P0. Any
unfinished stripped/malformed token diagnostic belongs to P2 T-0106. It may be
retained, but it must not delay or re-enter the T-0042 critical path.

## Promotion record

Before promoting a task into P0, record:

- the exact trigger and evidence locator;
- satisfied dependencies and remaining assumptions;
- one owner and a bounded first deliverable;
- exit, stop, and rollback rules;
- the previous P0 disposition;
- affected TODO, ROADMAP, ADR/RFC/EXP, and dated-log records.

Conversation, an existing branch, or agent availability is not promotion
authority. A result-conditioned task that fails its trigger remains dormant;
do not fill the schedule with it merely because capacity is available.
