# Raveil project records

This directory is the single entry point for Raveil's current design,
implementation state, evidence, and project memory.

## Start here

For ordinary work, read only:

1. executable code and tests relevant to the request;
2. [STATUS](STATUS.md) for what is implemented and verified;
3. [TODO](../TODO.md) for actionable work;
4. the task-specific records routed below.

History and archived conversations are not onboarding requirements.

## Source-of-truth order

When records disagree, fix the weaker record using this order:

1. executable code and tests;
2. [STATUS](STATUS.md);
3. [accepted ADRs](decisions/README.md);
4. [ARCHITECTURE](ARCHITECTURE.md);
5. [ROADMAP](ROADMAP.md) and [TODO](../TODO.md);
6. chronological logs;
7. history and archived source material.

## Document router

| Record | Authority and purpose | Read or update when |
|---|---|---|
| [STATUS](STATUS.md) | current implementation and verified facts | inspecting or changing executable behavior |
| [SCOPE](SCOPE.md) | current-version boundary | changing the minimum release boundary |
| [TODO](../TODO.md) | stable-ID actionable work | starting, discovering, blocking, or completing work |
| [ROADMAP](ROADMAP.md) | long-term gates and exit conditions | a gate condition or state changes |
| [VISION](VISION.md) | research thesis and intended outcome | the central hypothesis changes |
| [PRINCIPLES](PRINCIPLES.md) | accepted project invariants | adopting or superseding a principle |
| [ARCHITECTURE](ARCHITECTURE.md) | intended components and boundaries | an architectural relationship changes |
| [EXPERIENCE](EXPERIENCE.md) | Experience model and evaluation rules | retrieval, retention, policy, or metrics change |
| [OPEN_QUESTIONS](OPEN_QUESTIONS.md) | unresolved decisions | a question appears or is resolved |
| [GLOSSARY](GLOSSARY.md) | canonical terminology | introducing or renaming a concept |
| [WORKFLOW](WORKFLOW.md) | record, review, and agent process | changing project operations |
| [SPRINTS](SPRINTS.md) | weekly task board, story points, runnable review, and retrospective | planning or closing a weekly sprint |
| [failure knowledge](FAILURE_KNOWLEDGE.md) | reusable observed failure lessons and prevention | debugging, recurrence, and milestone review |
| [ADRs](decisions/README.md) | accepted or rejected decisions | changing an invariant, boundary, or dependency strategy |
| [RFCs](rfcs/README.md) | substantial proposals without authority | developing an unresolved architecture proposal |
| [experiments](experiments/README.md) | reproducible evidence and claims | measuring or making a performance claim |
| [research references](references/README.md) | draft external-source identity, provenance, and project-authored synopses | citing papers, manuals, talks, or whitepapers |
| [project workspace](guides/PROJECT_WORKSPACE.md), [Native Command Graph](guides/NATIVE_COMMAND_GRAPH.md), [showcase guide](guides/NATIVE_COMMAND_GRAPH_SHOWCASE.md), [T-0042 small-start packet](guides/T-0042-SMALL-START.md), and [task start phases](guides/TASK-START-PHASES.md) | Playable project use, Native operation, bounded execution packets, and WIP timing | editing/rerunning a project, running demos, executing T-0042, or deciding whether unfinished work may start |
| [history](history/DESIGN-EVOLUTION.md) | non-normative design evolution | investigating why the direction changed |
| [archive](archive/README.md) | frozen provenance material | investigating original discussion context only |

## Record rules

- Implementation changes update STATUS and TODO.
- Completed or newly discovered work updates TODO.
- Accepted architecture changes create a new ADR; accepted ADRs are superseded,
  not silently rewritten.
- Measurements and performance claims update an EXP record.
- Unresolved choices stay in OPEN_QUESTIONS or an RFC.
- Chronological observations go in `log/YYYY-MM-DD.md`; promote lasting facts
  into the appropriate canonical record.
- Keep analytical, simulated, emulated, FPGA, and silicon evidence separate.

Identifiers are monotonic: `T-0001`, `ADR-0001`, `EXP-0001`,
`RFC-0001`. Do not reuse abandoned identifiers.

Record templates live in [`templates/`](templates/). The weekly task board is
the GitHub Project routed through [`SPRINTS`](SPRINTS.md), not a second
Markdown source of task truth.

## Progress and agent workflow

The primary agent owns task classification, task-ID allocation, tracked-file
edits, completion decisions, and final record consistency.

Repository-scoped workflows live in [`.agents/skills/`](../.agents/skills/)
and task-specific roles in [`.codex/agents/`](../.codex/agents/). Use the
read-only Librarian to select a minimal context packet and the Performance or
Security Reviewer for an independent audit when useful; findings are proposals.
A subagent never marks a task complete, changes a gate, accepts an ADR, or
concludes an experiment.

Run the governance workflow at task kickoff and closeout. The detailed process
is in [WORKFLOW](WORKFLOW.md). Use the repository-scoped
`raveil-sprint-operator` skill for the repeatable weekly audit, kickoff,
continuation, correction, review, closeout, retrospective, and next-pull loop.
Remote publication uses `raveil-remote-release`; hosted CI/CD remains disabled
by policy.

## Project operations receipts

[2026-09-05 Project inventory](guides/PROJECT-INVENTORY-2026-09-05.md) records
an initial reconciliation and remaining evidence/scope gaps. Live coordination
stays in [GitHub Project #1](https://github.com/users/bhind/projects/1), with
mandatory session updates under ADR-0086 and WORKFLOW.
