# ADR-0086: Project inventory and session synchronization are required

Status: Accepted
Date: 2026-09-05
Task: T-0151
Related: ADR-0056, ADR-0061, ADR-0065, ADR-0066, ADR-0082

## Context

The owner requires actual Project upkeep, not an intention to update later.
The historical dirty root predates the current queue policy. Current main,
local candidate branches and live Issues allocate different meanings to the
same suggested identifiers. T-0149 exists locally with no Project item;
local T-0150 denotes a UIO regression while live T-0150 is Garden feedback.
Thirteen unfinished canonical tasks lack a card; some conditional research
priorities still imply immediate delivery and two cards represent T-0132/S07.
An API audit succeeds using authorized network access despite an earlier
sandbox-only authentication failure. Automatic completion is not justified.

## Decision

Jitro / the primary Project Manager must maintain GitHub Project #1 as the
mandatory day-to-day coordination surface synchronized with canonical records.
The source-of-truth order is unchanged. This decision adds required initial
inventory and before-start, same-session discovery/scope, immediate-blocker,
review, verified-completion and session-closeout checkpoints to ADR-0065.
A daily scheduler is supplementary; every work session has the same obligation.

Reuse existing fields. Every full T-ID or explicitly accepted child outcome
has one execution card with outcome, state, priority, owner, acceptance,
dependencies/blockers, Issue/PR/branch, canonical/evidence links and next action.
Deferred ideas/conditional research may be historical draft cards with explicit
restart conditions; they are not committed or Ready. Approved execution must
be registered first, using a real Issue and canonical queue transitions.

Default to one primary product implementation, now the editable Raveil working
environment. ADR-0061's two-independent-item maximum remains a safety ceiling;
this decision neither starts a second product lane nor changes research gates.
Preserve the broad unfinished T-0042 research concern, its dirty donor files,
and its explicitly conditional successors separately from workspace delivery.
The accepted ADR-0046 controlled-run evidence is not erased or promoted to
broad research completion. Scope disagreement must remain visible pending an
explicit reconciliation, rather than silently rewriting an accepted ADR.

Before archive/merge of duplicate cards, retain both histories and identify the
survivor. No existing item is deleted. Verify executable acceptance, tests,
records and integration before Done; neither conversation, Project metadata,
local candidate checkbox nor subagent report is sufficient. When evidence is
missing, retain a named gap and next verification action without granting Done.

If GitHub is inaccessible, retain a dated target/operation/error/permission,
unapplied delta and recovery receipt, continue independent authorized work,
and retry when access returns. A sandbox network failure must not be reported
as a confirmed credential failure before checking the authorized boundary.

## Consequences

AGENTS, WORKFLOW and task-governance carry the required checkpoints to later
agents. The inventory guide is a dated evidence receipt, not a second live
board. The existing queue remains the sole implementation of its supported
lifecycle transitions. No new architecture, performance claim, EXP conclusion,
Gate transition, paid infrastructure or release authority follows.
