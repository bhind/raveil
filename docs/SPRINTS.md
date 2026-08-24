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

ADR-0059 retains eight story points as a lower-bound planning reference rather
than an execution ceiling. The provisional committed capacity is 13 SP per
week and the warm stretch range is 13--21 SP. At most two items
may be in `IN_PROGRESS` or `REVIEW` combined. Prefer one active mutation item
and one independent review or acceptance item; a Playable and Research item may
overlap only when ownership and evidence paths are independent. Operations is
temporary supporting work, not a third pillar. A task retains its stable T-ID
and remains authoritative in `TODO.md`.
The sprint board may describe a smaller acceptance slice but never redefine
the task or silently mark it complete. The Project also records seven-day
`Sprint` Iterations, `Initial SP`, current `Story Points`, `Pillar`, `Owner
Role`, `Support Roles`, `Parent T-ID`, `Depends On`, `Priority`, `Work Type`,
`Demo Command`, `Evidence Class`, `Estimate Review`, `Estimate Change Reason`,
`Forecast Sprint`, `Forecast Date`, `Forecast Confidence`, `Review Outcome`,
`Retro Action`, `AI Estimate`, `Observed Cycle`, `Agent Tier`, `Role Packets`,
and `Resource Use`.

Capacity is empirical and lane-based. Forecast from accepted-slice cycle time
for the mutation, test, review, and serial PM-integration lanes, plus current
dependencies and warm/cold environment state. Eight SP is an under-utilization
alarm when a week closes at or below it without a dependency, HCI, or external
blocker; 13 SP is the provisional committed load; 13--21 SP is a warm stretch
range. Reaching either forecast never stops otherwise authorized work. At the
upper range, re-estimate WIP, lane load, and token/resource budget before
pulling more work. Carry-over is explicitly recommitted without rewriting
Initial SP.

ADR-0060 adds a separate service-cost guard that is not expressed in SP. Check
current weekly Codex usage before pulling a new task, assigning a subagent, or
starting a long-running job, and at the next task boundary. A verified weekly
remaining value below five percent stops new work; exactly five percent may
continue cautiously. Missing or unverifiable weekly telemetry fails closed for
new costly work. `Resource Use` may record the observation time, 10,080-minute
window, used percentage, and remaining percentage, but never account IDs,
credentials, secrets, or reset-credit identifiers.

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

Raveil has one serial Project Manager integration and acceptance lane, one
low-reasoning tracked-file mutation lane, one low-reasoning Tester lane, up to
two read-only reviewer lanes, one medium Librarian lane as needed, and one
high-reasoning Researcher only at evidence milestones. Project Manager,
implementers, Tester, reviewers, Researcher, and Librarian are responsibility
boundaries, not additive full-time people. Specialist work overlaps only when
file ownership and evidence boundaries are independent; final records,
acceptance, PR review comment, and merge remain serial.

Review and ceremony work receives SP only when it produces an independently
accepted artifact required by the parent. Forecast ranges use observed
accepted-slice cycle time by lane and remain ranges rather than single-date
promises for low-confidence research. Reaching a Sprint's forecast SP total is
not a pause condition.

The first provisional weekly service forecast is:

| Role lane | Warm weekly forecast | Scheduling meaning |
|---|---:|---|
| coherent tracked-file mutation | 3--5 packets | one low-reasoning owner at a time |
| Tester | 5--8 acceptance packets | clean replay after each accepted mutation slice |
| PM integration, records, PR, merge | 5--8 PR packets | serial acceptance bottleneck |
| read-only review | 4--8 bounded reviews collectively | at most two parallel; tier follows risk |
| Librarian | demand-triggered | bounded authority/provenance packet, not continuous load |
| Researcher | evidence-milestone only | non-authoritative synthesis, not Sprint FTE |

These are resource-allocation forecasts, not measured productivity claims.
Record accepted SP, packets by role, observed cycle time, warm/cold state,
blocked time, and token/resource consumption separately. Recalibrate the
13--21 SP band after two closed Sprints. Do not sum specialist lanes as FTE;
the largest required lane load and the serial PM lane bound the forecast.

Committed `Sprint` Iterations currently cover S-0001 through S-0006. Later work
uses `Forecast Sprint`, `Forecast Date`, and `Forecast Confidence`; this avoids
presenting an uncommitted research sequence as an Iteration promise. The
retained dependency forecast is:

| Window | Intended outcome | Confidence |
|---|---|---|
| S-0002, through 2026-09-06 | T-0117 first read-only Garden TUI and terminal acceptance | medium |
| S-0001, through 2026-08-30 | T-0044 integrated prerequisite plus readiness, identity/denominator, typed contract validation, and the three-SP S13 pre-data physical-input pause; owner-priority T-0120 Garden multi-pane refinement; 50 Current SP after absorbed S09 is counted as zero | low |

The original Project forecast incorrectly attached deferred token-lifecycle
hardening to completed T-0042 and also replanned T-0044 latency/traffic work
already covered by EXP-0005 through EXP-0010. The bounded stripped-token work
already active in S-0001 is retained as T-0106 evidence carry-in, but it does
not satisfy T-0106's start trigger. All later token-hardening and stale T-0044
planning items return to `Unscheduled` until refinement against canonical
authority. The newly refined T-0044/S08 integrated prerequisite moved from its
low-confidence S-0003 forecast into S-0001. Its already-performed clean replay
absorbs S09 at Current SP zero, S10 adds five Current SP for the readiness
validator, S11 adds eight for the identity/denominator boundary, and S12 adds
eight for the typed physical estimator and evidence protocol. The resulting
50-SP Sprint is above the 13--21 warm planning band; it is an observed
owner-authorized over-band delivery after the weekly service window recovered,
not evidence that later T-0044 work fits the Sprint or a new capacity forecast.
No later forecast date is inferred from the removed sequence.
S13 retains Initial SP 13 but records Current SP 3 because its fixed
missing-physical-input stop fired before allocation, collector implementation,
or cold P&R. The blocked remainder is not treated as delivered capacity.

Custom RISC-V remains Icebox until FPGA evidence identifies a concrete residual
problem. It has neither SP nor a calendar date.

## Story-point calculation

Points express relative AI delivery risk, not hours, agent count, individual
productivity, or research value. Weekly capacity uses a separately calibrated
SP band plus role-packet and resource observations. Calculate a raw score at
planning:

```text
raw = implementation + uncertainty + verification + environment
```

| Factor | Allowed score | Meaning |
|---|---:|---|
| implementation | 1–4 | number and coupling of bounded mutation packets |
| uncertainty | 0–3 | unknown contract, mechanism, or failure surface |
| verification | 0–2 | independent tests, clean reproduction, review, and evidence work |
| environment | 0–2 | cold builds, hardware, vendor tools, emulation, or external setup |

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
scope, or observed AI execution packet. Also record separate warm/cold ranges
for edit, verification, and PM integration plus the dominant role lane. Points
are not awarded partially: an item is either accepted as `Done` or it is not.

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
