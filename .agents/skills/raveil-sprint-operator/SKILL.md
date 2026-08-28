---
name: raveil-sprint-operator
description: Operate Raveil's weekly Sprint lifecycle by auditing the live GitHub Project, enforcing authority, usage, WIP, and evidence boundaries, and routing kickoff, continuation, correction, review, closeout, or next-pull work through the canonical queue. Use for Sprint planning, Sprint status, task pull, mid-Sprint correction, executable review, retrospective, and Sprint handoff. Do not use it to accept research claims or override repository records.
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
- **Review/closeout:** validate the exact-head PR and recorded acceptance,
  transition through the canonical review command, run the executable Sprint
  demo, reconcile records, and verify closed-Issue/`Done` agreement after merge.
- **Retrospective/next pull:** record one `Keep`, one observed `Problem`, and at
  most one bounded `Try`. Recheck usage, WIP, dependencies, and readiness before
  pulling the next item.

For phase-specific commands, receipts, and stop rules, read
[references/sprint-cycle.md](references/sprint-cycle.md) before any remote or
tracked mutation. For a read-only status request, its audit section is enough.

## Non-negotiable boundaries

- `scripts/project_queue.py` is the sole queue-transition implementation.
  Never reproduce `start` or `review` transitions with ad hoc GraphQL.
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
- Apply all HCI classes before destructive, remote, claim-bearing, paid,
  credentialed, gate-changing, or materially forked work.

## Required handoff

Return a compact phase receipt containing:

- Sprint title and dates, authority commit, branch, and T-ID;
- weekly usage reading and timestamp, without account identifiers;
- live Project audit result and active WIP;
- commands run, exit status, environment, and evidence class;
- accepted, carried, blocked, dropped, and unverified scope;
- any HCI with the preserved safe state; and
- exactly one recommended next action.
