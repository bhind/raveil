# ADR-0051: Continuous work stops only on human-confirmation incidents

Status: Accepted
Date: 2026-08-20
Task: T-0110
Related: ADR-0009, ADR-0026, T-0044, T-0107

## Context

Raveil's evidence and authority rules require human ownership of project scope,
scientific freezes, gate decisions, destructive actions, and remote
publication. Treating every status update, ordinary failure, local commit, or
accepted implementation boundary as another approval point nevertheless
creates avoidable idle time and makes long agent sessions depend on continuous
human presence.

The opposite rule, "continue unless blocked," is too vague. It can hide scope
growth, post-data experiment changes, repeated recovery loops, user-work
damage, unapproved cost, or remote side effects. The repository therefore needs
an exhaustive, inspectable boundary between continuous local execution and a
human-owned decision.

## Decision

After the owner authorizes a bounded task, continuous local execution is the
default. Agents may investigate, edit assigned files, make local atomic
commits, run tests and candidate-independent smokes, obtain read-only reviews,
reconcile required records, and advance to the next already-accepted slice
without waiting for acknowledgement. Progress reports are non-blocking.

Only these Human-confirmation incident classes pause the affected action:

1. `HCI-01`, unapproved scope, authority, P0, architecture, or project-line
   expansion;
2. `HCI-02`, a first claim-bearing experiment freeze or collection, post-data
   scientific change, EXP conclusion, or gate decision;
3. `HCI-03`, destructive work, immutable-evidence replacement, or an
   unapproved remote mutation or publication;
4. `HCI-04`, evidence identity, oracle, resource, matrix, raw/derived, seal, or
   evidence-class ambiguity that cannot be resolved inside the frozen rules;
5. `HCI-05`, overlap with user-owned or ownership-unknown work;
6. `HCI-06`, unapproved external cost, credentials, uploads, publication, or
   material source/license/provenance/IP-risk expansion;
7. `HCI-07`, the same root-cause class failing twice, more than two recoveries
   at one boundary, a required third recovery manifest, no bounded in-scope
   fix, an estimate above twice its evidence-backed value, or an unapproved
   attempt above six host hours or 20 GiB of new artifacts; and
8. `HCI-08`, a material design fork affecting contract, comparison fairness,
   specialization, backend strategy, reversibility, or cost by about twofold.

The detailed triggers, non-incidents, report shape, and progress cadence are
canonical in `AGENTS.md` and `docs/WORKFLOW.md`. An owner may explicitly grant
a narrower one-time or task-scoped authorization, but an agent may not infer
broader permission from this continuous-work default.

When an HCI occurs, the agent stops only the affected mutation or collection,
preserves evidence, continues safe read-only diagnosis, and asks one concrete
question containing the incident ID, authority, options, recommendation,
impacts, and exact approval required. It does not switch to a different
implementation P0 while waiting.

## Non-incidents

Ordinary build, elaboration, syntax, parser, wiring, test, or deterministic
tool failures are not HCIs when the root cause is identified and the correction
stays inside the assigned files and frozen scientific boundary. Neither are
isolated worktrees, local branches and commits, regression tests, mandatory
record updates, read-only review, candidate-independent smokes, or the first
bounded operational recovery.

Sandbox approval and external-system permission remain independent enforcement
boundaries. This ADR does not authorize an action forbidden by the execution
environment, an accepted ADR, repository authority, or an explicit owner
instruction.

## Consequences

Work no longer pauses for ceremonial acknowledgement. Human attention is
reserved for irreversible, authority-changing, evidence-sensitive, expensive,
remote, destructive, or genuinely branching decisions. Quantified recovery
and resource thresholds prevent the open-ended repair loops previously seen in
physical-evidence commissioning.

The policy does not change any experiment result, gate, implementation P0,
performance claim, remote-publication rule, or Experience authority boundary.
