# ADR-0068: Sprint review and retrospective run on Saturday

Status: Accepted
Date: 2026-08-29
Supersedes: the Sunday ceremony timing used by the ADR-0056 workflow; ADR-0056
remains authoritative for the Project coordination boundary

## Context

Raveil's seven-day Iterations run Monday through Sunday. The operational
workflow originally scheduled the executable review, demo, and retrospective
on Sunday. That left no bounded recovery or record-reconciliation interval
before the next Monday planning boundary. On 2026-08-29 the owner selected
Saturday as the recurring review day.

This is a cadence decision only. It must not change what counts as executable
evidence, who may accept work, when a task or research gate closes, or the
configured Monday-through-Sunday Iteration dates.

## Decision

Run the normal executable Sprint Review, demo, and Keep/Problem/Try
retrospective on Saturday in the Project's operating timezone.

Keep each GitHub Sprint Iteration Monday through Sunday. Use Sunday only as a
bounded recovery and handoff buffer:

- reconcile canonical records and live Project state exposed by Saturday's
  review;
- retain and diagnose a failed Saturday demo;
- perform an already-authorized bounded correction and explicit re-review when
  it remains inside the same task and evidence boundary; or
- prepare Ready work for Monday planning.

Do not pull new closing-Sprint scope merely because Sunday remains inside the
Iteration. Work not accepted by the Saturday review, or by a bounded Sunday
re-review of the same reviewed item, carries explicitly into the next Sprint.
Monday remains the planning and pull boundary; Wednesday remains the correction
review.

## Consequences

- The regular review happens one day before Iteration end, leaving a truthful
  recovery and record-synchronization window.
- Saturday remains an evidence review, not an automatic task, ADR, EXP, gate,
  or evidence-class transition.
- Sunday recovery cannot rewrite Initial SP, hide a failed demo, broaden scope,
  or treat Project metadata as acceptance evidence.
- Existing Sprint Iteration dates and historical review records remain intact.
- The current S-0001 review card moves to Saturday 2026-08-29; later review
  cards follow the Saturday within their configured Iteration.
