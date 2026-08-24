# Task start phases and work-in-progress handling

Status: active planning guide
Date: 2026-08-24
Authority: TODO task assignments, ROADMAP gates, accepted ADRs

## Purpose

Prevent unfinished branches, sunk effort, interesting side projects, or broad
hardening checklists from displacing the smallest experiment that tests the
current thesis. A TODO checkbox states whether a task is complete; its phase
states when work may begin.

## Phases

- **P0 — immediate:** at most two explicitly independent delivery items under
  ADR-0061; otherwise the single default implementation focus.
- **P1 — next:** begins only after P0 passes its recorded exit contract.
- **P2 — result-conditioned:** begins only after a named go result or separately
  accepted product requirement.
- **P3 — future planned:** intended work without a start date. The Project
  Manager selects and promotes it after the critical research decision.
- **P4 — optional/triggered:** no default start. It may become mandatory when
  its explicit trigger occurs, but remains dormant until then.

The canonical task-to-phase mapping is the table at the top of `TODO.md`.

## Work-in-progress limit

Only one coherent P0 implementation task is active by default. ADR-0061 permits
a second mutation item only when both items have disjoint task or child-slice,
worktree, branch, owner, exact file allowlist, artifacts, tests, acceptance,
and evidence paths and neither depends on the other's unmerged result.
Canonical record integration, acceptance, and merge remain serial. Read-only
review, reproducibility checks, and bounded blocker investigations do not
consume this two-item delivery limit.

Existing partial work is handled as follows:

1. Preserve verified commits, failure evidence, and exact source locators.
2. Do not merge, finish, or expand a partial branch solely because it exists.
3. Map its remaining work to the owning task and phase.
4. Leave unverified local modifications explicitly non-authoritative.
5. Resume only after the task is promoted or when a bounded action is necessary
   to preserve otherwise-lost evidence.

For the current reset, T-0122 is the mutation P0 for the simulation-first Graph
device MVP. T-0044/S13 remains Blocked before EXP-0011 data; only the read-only
S14 physical-input strategy inventory may overlap T-0122. T-0123 follows
T-0122, and unfinished stripped/malformed token diagnostics remain P2 T-0106.
Preserved branches do not re-enter the critical path without promotion.

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
