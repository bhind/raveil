# ADR-0061: Independent delivery lanes require live coordination

Status: Accepted
Date: 2026-08-24
Task: T-0122
Partially supersedes: ADR-0059 only for limiting tracked-file mutation to one lane;
ADR-0056 only for the default visible Project fields

## Context

The private GitHub Project has preserved dependencies, roles, evidence classes,
review outcomes, and 17 merged pull-request increments. Its live readback on
2026-08-24 contained 38 items and 37 fields: 25 Backlog, 11 Done, one Ready,
one Blocked, and no In Progress item. The only Ready item was the Sprint review,
while T-0044/S13 was correctly Blocked before EXP-0011 allocation because the
seven common memory macros lacked required Liberty and LEF views.

At the same time, local worktrees contained completed or partial simulation-MVP
branches that had no current Project card and did not descend from current
main. In particular, the T-0113/T-0114 branches contain useful clean-replayed
implementation, but they forked 41 current-main commits earlier and include
stale planning records. The board therefore worked as an audit ledger but not
as a reliable pull surface, while uncoordinated worktrees made activity look
more parallel than it was.

ADR-0059 allowed one mutation item plus review lanes. The owner directed Raveil
to use genuinely independent sessions where safe and to restore the runnable
simulation-first MVP without stopping the separate T-0044 research boundary.

## Decision

Retain the Project delivery WIP limit of two, but permit both items to mutate
tracked files only when all of the following are recorded before work starts:

1. each item has a distinct T-ID or independently acceptable child slice;
2. each has its own clean worktree, dedicated branch, named mutation owner,
   exact file allowlist, artifacts, tests, acceptance command, and evidence
   class;
3. their mutable files and generated or raw evidence paths do not overlap;
4. neither item's correctness, claim, or rollback depends on the other's
   unmerged result; and
5. the Project Manager can integrate and verify each PR independently.

If any condition fails, the work is one serial item. Canonical STATUS, TODO,
ROADMAP, OPEN_QUESTIONS, ADR/RFC/EXP, and dated-log edits remain owned and
integrated by one Project Manager lane. PR functional acceptance, record
reconciliation, review-thread resolution, and merge remain serial even when
implementation overlaps in elapsed time. Reviewers and Testers stay
non-authoritative and may not convert parallel output into completion.

The live Project card is required coordination metadata for active mutation.
Synchronize it at branch start, first atomic commit, PR creation, Review,
Blocked, and merge. A local worktree or branch without a matching Ready, In
Progress, Review, or Blocked item is donor material or provenance, not active
WIP. Existing donor branches are never merged wholesale merely because they
contain completed work; reusable code is reconstructed on current authority.

Use these ten fields as the default visible execution surface: Title, Status,
Priority, Parent T-ID, Owner Role, Depends On, Sprint, Story Points, Demo
Command, and Evidence Class. Retain populated historical fields and their data,
but hide them from the default Kanban unless refinement or review needs them.
Do not delete fields until a Project JSON snapshot exists and a separate
governance change removes every canonical dependency on them.

Create T-0122 as the first simulation-first Graph device MVP on current main.
It may reconstruct the functional code from the clean-replayed unmerged
T-0113 commit `f5ea057`, but uses task-neutral public ABI names and current
records. Its mutation lane owns only new contract, runtime, Verilator wrapper,
runner, and test files; the existing Static Graph compiler/oracle/core and all
T-0044 measurement and physical files are read-only dependencies.

T-0044 remains the independent Research lane. S13 stays Blocked before data.
A read-only S14 may inventory compatible public macro views or an exactly
matched common standard-cell memory option. Any external dependency adoption,
memory-denominator change, EXP allocation/freeze, or candidate collection still
requires the applicable Human-confirmation incident and cannot be inferred from
available WIP capacity.

After T-0122 passes, T-0123 may reconstruct the bounded generated-schedule,
affine, and two-DAG progression from the T-0114 donor commits. It is serial
after T-0122, not a concurrent attempt to build on an unmerged ABI.

## Consequences

Raveil can overlap independent Product and Research work without allowing two
agents to edit one coherent change or bypass the serial acceptance boundary.
The board becomes a concise live pull surface while keeping its detailed
historical data. Worktree count no longer substitutes for current status.

The current two-lane state is one T-0122 mutation item plus one T-0044 read-only
unblocking item. T-0044 does not start another physical mutation while S13 is
blocked. A later second mutation requires the same explicit independence audit.

No prior prototype, task, experiment, performance result, FPGA result, or gate
is promoted by this decision. T-0122 begins as implementation work; its donor
receipts are reusable evidence candidates, not current-main acceptance.
