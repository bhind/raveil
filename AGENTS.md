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

Push only dedicated change branches. Every change to `main` must arrive through
a GitHub pull request; never push directly to `refs/heads/main`. The active
repository ruleset applies this requirement without an owner or agent bypass,
blocks branch deletion and non-fast-forward updates, and requires review threads
to be resolved. Creating or updating the pull request for an already authorized
bounded change is the normal integration step. Merging it still requires the
incident-free merge audit defined in `docs/WORKFLOW.md`. ADR-0058 gives standing
authority to merge a verified PR immediately when that audit finds no
Human-confirmation incident. Direct `main` push remains prohibited.

## Agent orchestration

The primary agent owns task classification, tracked-file integration, final
verification, and the STATUS/TODO/ADR/EXP/log consistency check. A subagent is
an advisor, never an authority for a Raveil fact, decision, or measurement
claim.

- Delegate independent read-heavy work such as code or record exploration,
  test-log analysis, evidence review, and diff review whenever it reduces the
  primary context load. A named Implementer may also own tracked-file mutation
  for one active real GitHub `work-item` Issue when ADR-0061's independence
  packet fixes its clean worktree, branch, exact file allowlist, artifacts,
  tests, evidence path, and stop rule before editing begins.
- Do not delegate concurrent edits to the same coherent change. At most two
  mutation owners may run concurrently, and their files, generated artifacts,
  tests, evidence, correctness, and rollback must be disjoint. The primary
  keeps task classification, canonical-record edits, final integration,
  verification, PR acceptance, and merge serial.
- Require each subagent to return paths, commands, evidence class, findings,
  and unresolved risks in a concise summary.
- Use the repository skills in `.agents/skills/` when their trigger matches.
  They supplement these repository rules; they do not supersede them.
- A progress review is read-only until the primary agent verifies each finding.
  Newly discovered work is de-duplicated against TODO before a new monotonic ID
  is allocated.
- Before assigning a mutation owner, require the real Issue and Project item to
  be `In Progress`; before accepting a PR, require the same item to be `Review`.
  Use `scripts/project_queue.py` to audit or perform these transitions. Draft
  cards and unmatched branches are planning, donor material, or provenance,
  not active mutation authority.
- Use one low-reasoning mutation owner for one coherent tracked-file change,
  one low-reasoning Tester after the slice, and at most two read-only reviewers
  in parallel. Reserve high reasoning for Project Manager authority, security
  or performance risk review, and evidence-milestone research synthesis.
- Story points are relative AI delivery risk, not hours. Use eight SP as the
  under-utilization lower-bound check, 13 SP as the provisional committed
  weekly capacity, and 13--21 SP as the warm stretch range. These planning
  bands are not hard stops: authorized work continues while its dependency,
  WIP, resource-budget, and ADR-0051 Human-confirmation boundaries remain
  satisfied. ADR-0060 is an independent cost guard: do not start new work when
  verified weekly Codex usage remaining is below five percent. Record
  role-packet counts and resource use separately from SP.

## Continuous execution and human confirmation

Within an owner-authorized task, agents continue through investigation, local
editing, local commits, tests, review, record reconciliation, and the next
accepted slice without waiting for acknowledgement. A progress update is
informational and does not pause work. ADR-0051 defines the exhaustive classes
of **Human-confirmation incident** (HCI) that require a stop:

- new scope, authority, P0, architecture, or gate direction outside the
  accepted task;
- the first claim-bearing experiment freeze or collection, a post-data change
  to scientific fields, or a gate/EXP conclusion;
- destructive work, user-work overlap, remote push/merge/publication, or use of
  credentials and paid resources not already authorized;
- evidence identity, oracle, resource, raw/derived, seal, or evidence-class
  ambiguity that cannot be resolved without weakening the frozen boundary;
- adoption with unresolved material license, redistribution, provenance, or
  IP-risk implications;
- a material design fork, more than two recoveries at one boundary, the same
  root-cause class failing twice, or an unapproved resource/estimate overrun.
- verified weekly Codex usage remaining below five percent, or unavailable,
  stale, malformed, or ambiguous weekly telemetry before a new costly action.

For the ADR-0060 weekly guard, use only a current Codex account reading whose
weekly window is 10,080 minutes. Compute `remaining = 100 - usedPercent`.
Exactly five percent remaining may continue cautiously; below five percent
must pause before a new task, subagent, long-running build or verification,
remote update, or merge. Preserve the smallest safe receipt for work already
running, start no downstream work, and notify the owner. If the reading is
unavailable or cannot be verified as current weekly telemetry, do not claim
that the guard is being monitored and do not start a new costly action. A
verified reading of at least five percent resumes ordinary authorized work.
Using reset credits, purchasing capacity, changing a service plan, or bypassing
the guard requires separate explicit owner authority. Never record account IDs,
credentials, secrets, or reset-credit identifiers in project records.

Ordinary build and test failures, bounded fixes inside assigned files,
regression tests, local branches/worktrees/commits, candidate-independent
smokes, required record updates, and read-only reviews are not HCIs. Preserve a
failed artifact when required, fix the bounded defect, and continue. When an
HCI occurs, stop only the affected mutation or collection, continue safe
read-only diagnosis, and ask one concrete question with the incident ID,
authority, preserved evidence, options, recommendation, and exact approval
needed. Never use this rule to bypass sandbox approval, repository authority,
or an explicit owner instruction.
