# ADR-0070: The next Sprint may start immediately after accepted review

Status: Accepted
Date: 2026-08-29
Task: T-0136
Partially supersedes: ADR-0068's Monday-only planning and pull boundary

## Context

ADR-0068 moved the executable Sprint Review and retrospective to Saturday but
retained Monday as the next pull boundary. After completing S-0001, this left a
ready product slice idle for calendar reasons even though the owner-visible
review, Keep/Problem/Try retrospective, task closeout, usage guard, dependency,
and WIP checks had all passed. The owner rejected that idle interval and
required the next Sprint to begin immediately after review and postmortem.

## Decision

Keep GitHub Iteration dates Monday through Sunday for reporting, but do not use
the calendar boundary as an execution wait. After a Sprint review receives an
explicit owner acceptance and its retrospective/postmortem records Keep,
Problem, and Try, the Project Manager immediately evaluates one next pull.

The next item may enter its configured next Sprint immediately when all normal
guards pass: current HCI-09 usage, complete real-Issue independence packet,
Definition of Ready, satisfied dependencies, a clean dedicated branch, Sprint
metadata, and the two-item WIP/ownership limit. The canonical queue dry-run and
`--apply` transition remain mandatory. Review acceptance does not waive any of
these guards or make an unready item runnable.

If no item is ready, the Sprint closes truthfully and Sunday remains available
for recovery, reconciliation, or preparation. Monday remains the regular
planning checkpoint for work not already pulled after review; it is no longer
an artificial wait for ready work.

## Consequences

- Accepted review and postmortem become the earliest next-pull boundary.
- Project Iteration dates remain useful reporting buckets even when execution
  crosses their nominal calendar edge.
- A failed, carried, conditional, or unaccepted review cannot trigger the next
  pull until its own closeout conditions are satisfied.
- This process decision does not accept product or research evidence, change a
  Gate, measure delivery speed, or weaken task, evidence, cost, or authority
  controls.
