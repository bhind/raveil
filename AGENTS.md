# Repository instructions

These rules apply to every change in this repository, including work performed
by coding agents.

## Start here

Before changing Raveil, use [`docs/README.md`](docs/README.md) as the document
router. Read the relevant executable code/tests, `docs/STATUS.md`, and
`TODO.md`; load ADR, architecture, experiment, or workflow records only when
the task requires them.

Files under `docs/history/` and `docs/archive/` are provenance, not current
implementation or decision authority.

## Preserve project memory

Raveil's documentation is part of the implementation. Do not change code,
architecture, scope, or research claims without updating the corresponding
Markdown records in the same commit.

Use these records:

- implementation state: `docs/STATUS.md`;
- actionable work: `TODO.md`;
- long-term gates: `docs/ROADMAP.md`;
- architecture: `docs/ARCHITECTURE.md`;
- unresolved questions: `docs/OPEN_QUESTIONS.md`;
- architectural decisions: `docs/decisions/ADR-*.md`;
- experiments and performance claims: `docs/experiments/EXP-*.md`;
- chronological context: `docs/log/YYYY-MM-DD.md`.

## Required update rules

1. Any material implementation change updates `docs/STATUS.md`.
2. Completed or newly discovered work updates `TODO.md`.
3. A change to an invariant, boundary, dependency strategy, or accepted design
   creates a new ADR. Never silently rewrite an accepted ADR; supersede it.
4. A benchmark or performance claim creates or updates an experiment record.
5. Analytical, simulated, emulated, FPGA, and silicon results must be labelled
   separately. Never present ToyDaphnis or model output as measured hardware
   performance.
6. Failed experiments and rejected decisions remain in Git history and in their
   records. They are evidence, not clutter.
7. Experience remains advice, never authority. No learned or retrieved proposal
   may bypass contract, capability, resource, semantic, measurement, and
   rollback boundaries.

## Source-of-truth order

When documents disagree, resolve them in this order and then fix the stale
document:

1. executable code and tests;
2. `docs/STATUS.md`;
3. accepted ADRs;
4. `docs/ARCHITECTURE.md`;
5. `docs/ROADMAP.md` and `TODO.md`;
6. chronological logs.

## Record identifiers

- tasks: `T-0001`;
- decisions: `ADR-0001`;
- experiments: `EXP-0001`;
- proposals: `RFC-0001`.

Allocate identifiers monotonically. Do not reuse deleted or abandoned numbers.

## Completion standard

Before declaring work complete, run the relevant tests, record the exact
commands and environment, update the documents above, and distinguish verified
facts from hypotheses and plans.

At task kickoff, identify the existing T-ID, roadmap gate, and EXP/RFC/ADR
context or state explicitly that none applies. At closeout, reconcile STATUS,
TODO, ROADMAP, OPEN_QUESTIONS, relevant ADR/EXP, and the dated log. Do not mark
work complete from conversation or subagent output alone.

## Branch workflow

Gate 0 is complete. Make every tracked implementation or record change on a
dedicated branch after inspecting `git status`; read-only review may remain on
the current branch. Name branches `<type>/<record-id>-<short-slug>` using
lowercase kebab-case. Allowed types are `feat`, `fix`, `research`, `docs`,
`test`, `build`, and `chore`; use the primary lowercase `t-`, `exp-`, `adr-`, or
`rfc-` identifier (for example,
`research/exp-0003-gate1-measurement`). Keep one coherent change per branch and
do not discard unrelated uncommitted work when creating or switching branches.

## Agent orchestration

The primary agent owns task classification, tracked-file integration, final
verification, and the STATUS/TODO/ADR/EXP/log consistency check. A subagent is
an advisor, never an authority for a Raveil fact, decision, or measurement
claim.

- Delegate only independent, read-heavy work such as code or record
  exploration, test-log analysis, evidence review, and diff review.
- Do not delegate concurrent edits to the same coherent change. Assign one
  named owner for every tracked-file mutation and keep the final integration in
  the primary thread.
- Require each subagent to return paths, commands, evidence class, findings,
  and unresolved risks in a concise summary.
- Use the repository skills in `.agents/skills/` when their trigger matches.
  They supplement these repository rules; they do not supersede them.
- A progress review is read-only until the primary agent verifies each finding.
  Newly discovered work is de-duplicated against TODO before a new monotonic ID
  is allocated.
