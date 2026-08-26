# ADR-0065: Active Project work uses real Issues and a fail-closed queue

Status: Accepted
Date: 2026-08-26
Task: T-0126
Partially supersedes: ADR-0056 and ADR-0061 only for active-item representation
and lifecycle synchronization

## Context

ADR-0061 requires every mutation lane to have a live Project item and permits
two independently acceptable implementations. The Project nevertheless
regressed to after-the-fact bookkeeping. Most cards were DraftIssues, so they
had no native Issue assignment, branch/PR closing relationship, or open/closed
lifecycle. T-0124 merged without a Project item. T-0123/S03 merged through PR
#26 while the Project README and canonical planning records still described it
as pending review. At the next readback, the only new active implementation,
T-0125, was In Progress but remained a DraftIssue.

The repository rules also contradicted the accepted execution model.
`docs/WORKFLOW.md` and ADR-0061 allowed two named, disjoint mutation owners,
while `AGENTS.md` limited all subagent delegation to read-heavy work. The more
restrictive instruction kept mutation and integration in one Project Manager
context even when the accepted independence test passed.

GitHub Project cannot start Codex sessions, transfer context, lock files, or
decide research direction. It can become a reliable pull surface only when its
items are addressable work objects and repository tooling checks the lifecycle
instead of relying on manual retrospective edits.

## Decision

Keep GitHub Project #1 as coordination metadata and keep TODO, STATUS, ROADMAP,
ADR, RFC, EXP, code, tests, and evidence authoritative. Retain historical Draft
cards without mass conversion or deletion. Every newly active P0 task or
independently acceptable child slice must instead use one real repository Issue
with the `work-item` label and a stable T-ID in its title. The Issue body fixes
the authority revision, dependency, named mutation owner, exact allowlist,
acceptance command, evidence class, stop rule, and non-claims before mutation.

Use this lifecycle:

1. `Backlog` and `Ready` are unclaimed planning states. `Ready` means the full
   start packet is pullable.
2. A named owner claims the Issue from its matching T-ID branch and moves it to
   `In Progress` before editing tracked files.
3. The final pull request carries the same T-ID, contains `Closes #ISSUE`, and
   moves the Project item to `Review`.
4. Merge closes the Issue. `Done` is valid only when the real Issue is closed
   and the Project Manager has reconciled canonical records. Project closure
   never proves task, evidence, experiment, or gate completion by itself.
5. `Blocked` records the exact external or HCI boundary. A blocked historical
   Draft card may remain as provenance, but it cannot be resumed as mutation;
   resumption first creates a real `work-item` Issue.

Add `scripts/project_queue.py`. Its default transition mode is read-only;
`--apply` is required for remote mutation. `start` validates Issue label/state,
branch/T-ID identity, and the visible execution fields before moving a card to
`In Progress`. `review` validates the open PR, matching head T-ID, and closing
reference before moving it to `Review`. `audit` fails on an open `work-item`
Issue missing from the Project, an active Draft card, lifecycle or Parent-T-ID
disagreement, missing execution fields, a task branch without a matching active
Issue, or more than two `In Progress` plus `Review` delivery items.

Reconcile `AGENTS.md` with ADR-0061. The primary may delegate tracked-file
mutation to a named Implementer only after the complete independence packet and
real active Issue exist. At most two such owners run concurrently, with no
overlap in files, artifacts, tests, evidence, correctness, or rollback. Task
classification, canonical-record edits, final verification, PR acceptance,
and merge remain one serial Project Manager lane.

T-0125 Issue #27 and T-0126 Issue #28 are the migration seeds. Do not convert
all historical Draft cards. The default Project view still uses ADR-0061's ten
fields; layout changes that the API cannot express remain a one-time UI action,
not a second board.

## Consequences

Active work is now claimable and auditable across sessions. A branch or
worktree no longer appears active merely because it exists, and the same Issue
connects the task packet, Project state, discussion, PR, and merge lifecycle.
Two independent implementers can work concurrently without weakening the
serial authority boundary.

The queue does not choose the next research hypothesis, manufacture task
independence, or replace human/PM integration. Serial ABI dependencies remain
serial. GitHub outages stop new mutation claims but do not erase local evidence
or make GitHub authoritative. Existing historical Draft cards and populated
fields remain preserved.

This decision changes development coordination only. It creates no executable
Graph capability, research conclusion, performance result, FPGA/ASIC/silicon
evidence, gate decision, or publication authority.
