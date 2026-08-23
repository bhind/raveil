# ADR-0060: Weekly Codex usage has a hard cost stop

Status: Accepted
Date: 2026-08-24
Task: T-0119
Supersedes: ADR-0051 only for its exhaustive incident list; ADR-0059 only where planning bands otherwise leave token/resource continuation discretionary

## Context

ADR-0051 makes incident-free execution continuous, and ADR-0059 prevents a
story-point forecast from idling available AI delivery lanes. Neither decision
defines a precise stop at the owner's weekly Codex service limit. A vague
instruction to "watch usage" can continue expensive work after the owner has
little weekly capacity left, confuse daily and weekly windows, or claim
monitoring when the reading is unavailable.

This is a cost-control boundary, not a productivity estimate or research
result. It must be exact enough to behave consistently at five percent and to
fail closed when current weekly telemetry cannot be established.

## Options considered

1. Treat weekly usage as advisory and let the Project Manager decide case by
   case. This is flexible but does not protect the owner's cost boundary.
2. Stop at five percent or less. This spends less capacity but contradicts the
   requested strict meaning of "below five percent."
3. Stop only below five percent, verify the weekly window, and fail closed for
   new costly work when telemetry is unavailable. This preserves the exact
   boundary and makes monitoring claims auditable.

## Decision

Adopt option 3 as HCI-09.

Use only a current Codex account rate-limit reading whose
`windowDurationMins == 10080`. Compute:

```text
remaining = 100 - usedPercent
```

When `remaining < 5`, do not start a new task, subagent, long-running build or
verification, remote update, or merge. Preserve the smallest safe receipt for
already-running work when interrupting immediately would lose evidence, start
no downstream work, and notify the owner. Exactly five percent remaining may
continue cautiously, with a fresh check before every new costly boundary.

Check before a new task, subagent, or long-running job, and after a task before
pulling the next item. If telemetry is unavailable, stale, malformed, or cannot
be verified as the 10,080-minute weekly window, do not claim that the guard is
being monitored and do not start new costly work until visibility is restored
or the owner supplies a current UI reading. A verified current reading with
`remaining >= 5` resumes otherwise-authorized work without a ceremonial owner
acknowledgement.

Consuming reset credits, purchasing capacity, changing a service plan, or
bypassing the guard requires separate explicit owner authority under HCI-06.
Records may include observation time, weekly window, used percentage, and
remaining percentage. They must not include account IDs, credentials, secrets,
or reset-credit identifiers.

## Rationale

The exact arithmetic distinguishes five percent from below five percent. The
fixed weekly-window identity prevents a daily reading from authorizing work.
Failing closed for new costly actions protects the owner when monitoring is not
trustworthy while still allowing evidence already in flight to reach a safe,
minimal receipt.

## Consequences

- Weekly service capacity can stop otherwise incident-free execution.
- SP, WIP, task status, evidence class, experiments, and research or hardware
  gates do not change when the guard fires.
- The owner is notified on a stop, but a normal weekly reset or verified
  reading of at least five percent clears it without an acknowledgement loop.
- Buying or resetting capacity is never inferred from this decision.
- No account or credential identifier enters canonical project records.

## Verification and supersession

`tests.test_experiment.AgentBoundaryTests` checks the HCI identifier, arithmetic,
threshold boundary, weekly-window identity, unavailable-telemetry behavior,
and prohibition on unapproved reset-credit use across repository and workflow
instructions.

This decision supplements ADR-0051 by adding HCI-09 to its previously
exhaustive list. It narrows ADR-0059 only by making this weekly cost guard a
hard stop independent of the non-binding SP planning bands. All other parts of
ADR-0051 and ADR-0059 remain accepted.
