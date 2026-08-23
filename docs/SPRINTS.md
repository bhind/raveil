# Weekly sprint governance

Status: active project workflow

Raveil uses the private
[`Raveil Weekly Sprints`](https://github.com/users/bhind/projects/1) GitHub
Project to limit work in progress, expose estimation errors, and produce a
runnable increment every week. Project items coordinate work; they never
override executable evidence, stable T-IDs, ROADMAP gates, accepted ADRs, or
EXP contracts.

## Cadence

The normal sprint runs Monday through Sunday.

- Monday, planning: choose one sprint goal, calculate initial story points,
  commit no more than current capacity, and name the exact demo path.
- Wednesday, correction review: compare the board with actual work, preserve
  every initial estimate, record changed points and reasons, and split or
  remove scope when capacity is exceeded.
- Sunday, review and demo: run the increment from a recorded command and
  environment, inspect acceptance evidence, and move only verified work to
  `DONE`.
- Sunday, retrospective: record one useful observation in each of `Keep`,
  `Problem`, and `Try`. At most one process-improvement action enters the next
  sprint so process work cannot consume the product.

Research reviews remain milestone-driven under `docs/WORKFLOW.md`. A weekly
sprint review may expose evidence or trigger a research review, but it cannot
promote an EXP, close a Gate, or turn simulation into FPGA or silicon evidence.

## Board and WIP

The GitHub Project's `Sprint Board` view is the execution Kanban. The filtered
`Product Backlog` table shows only Backlog items with priority, forecast,
points, owner/support roles, parent, and dependencies. The Kanban states are:

```text
Backlog -> Ready -> In Progress -> Review -> Done
                         |            |
                         +-> Blocked <-+
```

The solo-development default is eight committed story points and at most two
items in `IN_PROGRESS` or `REVIEW` combined. Prefer one active Playable item and
one active Research item; Operations is temporary supporting work, not a third
pillar. A task retains its stable T-ID and remains authoritative in `TODO.md`.
The sprint board may describe a smaller acceptance slice but never redefine
the task or silently mark it complete. The Project also records seven-day
`Sprint` Iterations, `Initial SP`, current `Story Points`, `Pillar`, `Owner
Role`, `Support Roles`, `Parent T-ID`, `Depends On`, `Priority`, `Work Type`,
`Demo Command`, `Evidence Class`, `Estimate Review`, `Estimate Change Reason`,
`Forecast Sprint`, `Forecast Date`, `Forecast Confidence`, `Review Outcome`,
and `Retro Action`.

Capacity is empirical. Keep eight points for the first three closed sprints,
then set the next capacity from the median completed points of those sprints.
Do not inflate capacity to absorb unfinished work. Carry-over is re-estimated
and explicitly recommitted.

## Product Backlog and refinement

The Product Backlog is not an inventory of aspirations. Order it by dependency,
priority, expected user or research value, and risk reduction. Keep at least the
next two sprints decomposed into independently acceptable slices. Further work
may remain an unpointed epic until refinement makes its outcome, boundary, and
entry conditions concrete.

A Project slice keeps its parent stable T-ID and uses a `/SNN` suffix only as a
coordination label. It does not allocate a new canonical record identifier or
silently narrow the parent task. Parent epics receive no story points. Count SP
only on child slices that can be accepted independently, preventing duplicate
velocity when implementation, testing, and review appear under one parent.

Refinement happens before Monday planning and whenever a newly discovered
dependency invalidates the next two sprints. A refined item records:

- one observable outcome and bounded non-goals;
- one owner role and the support roles needed for completion;
- parent T-ID, predecessors, evidence class, and priority;
- initial SP and the factors that dominate the estimate;
- a runnable demo or evidence command, even when the command is a planned path;
- committed Sprint or forecast Sprint/date plus confidence.

## Definition of Ready and Done

An item may move from `Backlog` to `Ready` only when its parent T-ID, outcome,
dependencies, owner/support roles, initial SP, evidence class, acceptance
boundary, demo/evidence command, and relevant non-claims are explicit. A
blocked external approval or hardware dependency must also be visible.

An item moves to `Done` only when the increment or evidence command ran at a
recorded revision and environment, acceptance was reviewed, failures and
non-claims remain visible, and required canonical records were reconciled.
Reviewer advice, prose, partial SP, and a green subagent report are insufficient.

## Role and capacity plan

Raveil currently has one human integration and acceptance lane. Project
Manager, Systems, Experience, Measurement, Tester, Performance, Security,
Researcher, and Librarian are responsibility boundaries, not nine independent
full-time people. Specialist work may overlap only when file ownership and
evidence boundaries are independent; final integration remains serial.

Allocate the weekly eight-point pilot capacity across accepted delivery slices,
not across every role that touches them. Review and ceremony work receives SP
only when it produces an independently accepted artifact required by the
parent. After three closed sprints, use median completed SP as the next planning
capacity and retain a range rather than a single-date promise for low-confidence
research.

Committed `Sprint` Iterations currently cover S-0001 through S-0006. Later work
uses `Forecast Sprint`, `Forecast Date`, and `Forecast Confidence`; this avoids
presenting an uncommitted research sequence as an Iteration promise. At the
initial eight-point assumption, the dependency forecast is:

| Window | Intended outcome | Confidence |
|---|---|---|
| S-0002, through 2026-09-06 | T-0117 first read-only Garden TUI and terminal acceptance | medium |
| S-0003 to S-0006, through 2026-10-04 | BOOM negative matrix, replay/backpressure, Rocket parity, BOOM load/post-A rollback | medium, then low |
| S-0007 to S-0008, through 2026-10-18 | common CPU/Graph adapter, resource review, T-0042 readiness, prior-art delta, comparison contract | low |
| S-0009 to S-0011, through 2026-11-08 | T-0044 runner, clean pilot, matched execution, reviews, and gate decision | low |
| S-0012, through 2026-11-15 | KV260 feasibility only after an explicit continue decision | conditional, low |

Custom RISC-V remains Icebox until FPGA evidence identifies a concrete residual
problem. It has neither SP nor a calendar date.

## Story-point calculation

Points express relative delivery risk, not hours, individual productivity, or
research value. Calculate a raw score at planning:

```text
raw = implementation + uncertainty + verification + environment
```

| Factor | Allowed score | Meaning |
|---|---:|---|
| implementation | 1–4 | size and number of owned changes |
| uncertainty | 0–3 | unknown design, mechanism, or failure surface |
| verification | 0–2 | tests, clean reproduction, review, and evidence work |
| environment | 0–2 | hardware, vendor tools, emulation, or external setup |

Map the sum to Fibonacci points:

| Raw | SP |
|---:|---:|
| 1 | 1 |
| 2 | 2 |
| 3–4 | 3 |
| 5–6 | 5 |
| 7–9 | 8 |
| 10 or more | 13; split before commitment |

Wednesday review changes `Story Points`, never `Initial SP`. Every change
records its date and concrete `Estimate Change Reason`, such as a newly
discovered authority boundary, toolchain setup, missing test seam, or reduced
scope. Points are not awarded partially: an item is either accepted as `Done`
or it is not.

## Runnable increment and demo

Every sprint names at least one command that exercises a real increment. A
demo can be a TUI interaction, host executable, QEMU boot, RTL simulation,
validator, or deterministic replay. Slides, prose, mock output, and an
unreproduced subagent report do not satisfy the demo contract.

The review records:

- exact command, revision, environment, and exit status;
- what visibly changed since the prior sprint;
- acceptance evidence and evidence class;
- non-claims and remaining risks;
- accepted, rejected, carried, and dropped scope.

If the intended increment does not run, demonstrate the last working baseline
and the exact failing boundary. The sprint can be unsuccessful without hiding
the failure.

## Retrospective

The retrospective is short and operational. Record:

- `Keep`: one practice that reduced time, cost, risk, or confusion;
- `Problem`: one observed impediment, not a person or vague complaint;
- `Try`: one bounded change for the next week, with an owner and observable
  completion condition.

Retrospective text is not implementation or experiment evidence. Durable
actions receive or reuse a T-ID and enter `TODO.md`; transient observations
stay in the GitHub Project item.

## Commands

Read back the Project without a browser with:

```sh
gh project view 1 --owner @me --format json
gh project field-list 1 --owner @me --format json
gh project item-list 1 --owner @me --format json
```

The Project begins private. Making it public is a separate owner decision
because draft research items may contain incomplete or easily misread evidence
boundaries.
