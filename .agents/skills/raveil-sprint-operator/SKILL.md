---
name: raveil-sprint-operator
description: Operate Raveil's weekly Sprint lifecycle and rolling P0 horizon by auditing the live GitHub Project, replenishing a bounded successor before delivery becomes idle, enforcing authority, usage, WIP, and evidence boundaries, and routing kickoff, continuation, correction, review, closeout, or next-pull work through the canonical queue. Use for Sprint planning, Sprint status, backlog replenishment, task pull, mid-Sprint correction, executable review, retrospective, and Sprint handoff. Do not use it to accept research claims or override repository records.
---

# Raveil Sprint Operator

Run one repeatable control loop around the repository's existing authority. This
skill coordinates work; it does not create a second task database or a second
GitHub Project mutation implementation.

## Establish authority

1. Use `raveil-task-governance`, read `AGENTS.md`, and route current records
   through `docs/README.md`.
2. Read `docs/SPRINTS.md`, the weekly-sprint section of `docs/WORKFLOW.md`,
   `TODO.md`, `docs/STATUS.md`, and the relevant executable code/tests.
3. Work from a clean current-`main` clone or isolated task worktree. Preserve a
   dirty historical root as donor/provenance only.
4. Name the current Sprint, authority commit, T-ID or bounded `/Sxx` slice,
   roadmap/ADR/RFC/EXP context, owner, file allowlist, acceptance command,
   evidence class, stop rule, and non-claims. State explicitly when a context
   class does not apply.

## Daily operating entry

Run `python3 scripts/project_daily.py` daily at 19:00 Asia/Tokyo through the
installed local scheduler, and inspect the retained receipt. `--apply` is
limited to factual GitHub event metadata and the marked Project daily README
section after a fresh weekly usage check. The report separates actual
Issue/PR dates from Sprint assignment and technical acceptance; lifecycle
anomalies require the canonical queue. Daily maintenance never substitutes
for immediate accepted-task closeout or explicit owner ceremony approval.

## Select one operating phase

- **Audit/status:** read the live Project, run the queue audit, and report the
  Sprint goal, active WIP, blocked work, evidence gaps, and one next pull. Do
  not mutate Project or repository state.
- **Kickoff/planning:** verify the weekly usage guard, Definition of Ready,
  Sprint Iteration, capacity, dependency order, and two-item mutation WIP.
  Require a real `work-item` Issue and a complete independence packet before
  starting tracked mutation.
- **Continue/checkpoint:** re-audit the active Issue, Sprint, full T-ID, branch,
  owner, and allowlist before resuming. Reconcile drift at the smallest safe
  boundary; do not broaden the packet to keep an agent busy.
- **Correction:** compare committed work with evidence. Preserve `Initial SP`,
  change current `Story Points` only with a dated reason, and split, carry, or
  remove scope without rewriting history.
- **Task review/integration:** validate the exact-head PR, allowlist, tests,
  records, mergeability, and technical acceptance; transition through the
  canonical review command, merge, reconcile the task records, and run the
  canonical completion command only after the Issue is closed. The completion
  command records review outcome, observed cycle, and resource use before
  moving `Status=Done` last. Do not stop continuous Sprint delivery for a
  per-task owner demo unless the owner or a task-specific risk gate explicitly
  requires one. Task `Done` never accepts the weekly Sprint Review ceremony.
- **Horizon replenishment:** by the current P0 Review boundary, run the
  pullable-Ready horizon check. If it is empty, continue technical integration
  and immediately refine one bounded successor from canonical code and records.
  Prepare one unambiguous successor as P1/Ready; escalate only a material
  strategic fork or an existing HCI. An empty horizon is work, not an idle
  result.
- **Weekly Sprint Review:** at the scheduled ceremony, select and run the
  Sprint's representative runnable outcome or outcomes, show and explain them
  to the owner, route durable feedback, and obtain the explicit ceremony
  disposition. This is the ADR-0069 owner-visible boundary.
- **Retrospective/next pull:** record one `Keep`, one observed `Problem`, and at
  most one bounded `Try`. Recheck usage, WIP, dependencies, readiness, and the
  prepared successor before pulling the next item.

For phase-specific commands, receipts, and stop rules, read
[references/sprint-cycle.md](references/sprint-cycle.md) before any remote or
tracked mutation. For a read-only status request, its audit section is enough.

## Non-negotiable boundaries

- `scripts/project_queue.py` is the sole queue-transition implementation.
  Never reproduce `prepare`, `start`, `review`, or `complete` transitions with
  ad hoc GraphQL.
- Only the primary Project Manager may perform Project transitions or use
  `--apply`. Other roles validate their named packet and report evidence.
- Run the current 10,080-minute HCI-09 usage check before a new task, subagent,
  or long-running job and at the next-task boundary. Missing or stale telemetry
  fails closed; below five percent remaining starts no new costly work.
- GitHub remains coordination metadata. Executable code/tests, STATUS, accepted
  ADRs, TODO/ROADMAP, and EXP records retain their documented authority order.
- A Sprint demo, points total, Project status, agent report, or retrospective
  never closes a T-ID, accepts an ADR/RFC, concludes an EXP, passes a gate, or
  promotes simulation to FPGA or silicon evidence.
- Task PR review and weekly Sprint Review are different control points. Merge
  technically accepted tasks continuously; aggregate their user-visible
  outcomes at the weekly ceremony. Never turn every task merge into an
  owner-attendance gate or treat one task acceptance as Sprint acceptance.
- Command success never accepts the Sprint review ceremony. Keep it non-Done
  until the owner sees the result, receives an evidence-grounded explanation,
  durable feedback is routed, and the owner explicitly chooses `Accept`,
  `Conditional Accept`, `Carry`, or `Reject`. Every conditional acceptance
  item must have a stable tracked destination before ceremony closeout.
- Apply all HCI classes before destructive, remote, claim-bearing, paid,
  credentialed, gate-changing, or materially forked work.
- Do not return an idle, waiting, finished, or no-next-work receipt merely
  because P0 and Ready are empty. Run bounded replenishment first. A stop is
  valid only for the weekly usage guard, an HCI, an exact external dependency,
  or a genuine strategic fork that the current authority cannot decide.

## Required handoff

Return a compact phase receipt containing:

- Sprint title and dates, authority commit, branch, and T-ID;
- weekly usage reading and timestamp, without account identifiers;
- live Project audit result and active WIP;
- commands run, exit status, environment, and evidence class;
- accepted, carried, blocked, dropped, and unverified scope;
- any HCI with the preserved safe state; and
- exactly one recommended next action.
