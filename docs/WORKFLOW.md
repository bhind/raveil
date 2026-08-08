# Development and research workflow

Last updated: 2026-08-08

## Before a change

1. Read `AGENTS.md` and use `docs/README.md` to select relevant records.
2. Inspect Git status and preserve unrelated user changes.
3. For tracked work, create a dedicated branch named
   `<type>/<record-id>-<short-slug>` in lowercase kebab-case. Types are `feat`,
   `fix`, `research`, `docs`, `test`, `build`, and `chore`; use the primary
   lowercase `t-`, `exp-`, `adr-`, or `rfc-` ID. Example:
   `research/exp-0003-gate1-measurement`. Read-only review does not require a
   new branch.
4. Read executable code/tests first, then STATUS and TODO. Load only the ADR,
   architecture, roadmap, EXP, question, or log records selected by the
   document router for this task.
5. Classify the proposed work as an implementation fact, decision, hypothesis,
   experiment, or environment observation.

## During a change

- Keep external types behind Raveil-owned versioned adapters.
- Keep Experience outside authority and preserve a trusted baseline/rollback.
- Allocate task, ADR, EXP, and RFC identifiers monotonically.
- Do not erase rejected approaches or failed results.
- Exclude credentials, generated logs, build products, IDE-local state, and
  absolute machine paths.

## Codex agents and skills

The repository provides narrow Codex agents in `.codex/agents/` and reusable
workflows in `.agents/skills/`. Use `raveil-context-librarian` first for broad
or unfamiliar tasks: it ranks a small reading packet from headings, search
hits, code symbols, and tests without loading every record. The primary still
reads the selected authoritative sections before editing.

- The Project Manager is primary and owns classification, assigned file
  ranges, canonical records, functional requirements review, integration,
  verification, and gate decisions.
- Experience, Systems, and Measurement Implementers edit only explicitly
  assigned, non-overlapping file ranges. They never edit canonical records.
- The Tester edits no tracked file and records clean reproduction evidence.
- Performance and Security Reviewers are read-only and may review their
  separate risk surfaces in parallel after testing.
- The Researcher writes only
  `docs/research/reviews/<date>-<EXP>-<stage>.md`. Its memo is advice and never
  changes STATUS, TODO, ROADMAP, OPEN_QUESTIONS, ADR, RFC, EXP, or logs.
- The Librarian is read-only and owns context routing only. It does not decide
  facts, identifiers, gates, or claims.
- Do not allow concurrent changes to one coherent file set. The Project
  Manager performs final integration and canonical record reconciliation.
- `raveil-task-governance` applies the record and evidence checklist to any
  material Raveil change. `raveil-gate0-evidence` applies the specific
  Sonatine Microkernel Gate 0 collection procedure.
- `raveil-remote-release` audits release readiness and permits remote tag and
  Release publication only after explicit owner approval. It never enables
  hosted CI/CD; current validation runs through `scripts/ci-local.sh`.

### Research execution order

1. Project Manager fixes Gate, T-IDs, acceptance criteria, and named file
   ownership.
2. Implementers work in parallel only when file ranges do not overlap.
3. Tester reproduces in a clean environment.
4. Performance and Security Reviewers inspect their risk surfaces in parallel.
5. Researcher synthesizes evidence and findings into a non-authoritative memo.
6. Project Manager reviews functional requirements, de-duplicates and assigns
   issues, updates canonical records, and decides continue/pivot/pause/stop.

Research review is milestone-driven, not scheduled automation. It is required
at EXP planning, pilot completion, full-dataset completion, a native-C/TVM
contradiction, a performance/security finding, and before a Gate decision. A
memo contains the hypothesis, evidence inventory, data quality, problems,
results, non-claims, implications, counterevidence, issue candidates, next
goals, and a `continue`, `pivot`, `pause`, or `falsified` recommendation.

### Progress reviews

Run a progress review at task kickoff, before declaring completion, and when
the user requests status or issue triage.

1. Compare code/tests and `git status/diff` with STATUS.
2. Map the requested work to an existing T-ID, gate, and related EXP/RFC/ADR.
3. Search TODO before proposing a new task; allocate an ID only after the
   primary agent confirms it is actionable and not duplicated.
4. Report completed candidates, newly discovered issues, blockers,
   dependencies, stale records, and missing verification separately.
5. Update tracked records only after evidence is verified:
   implementation facts → STATUS; actions → TODO; gates → ROADMAP; unresolved
   design → OPEN_QUESTIONS/RFC; measurements → EXP; chronology → dated log.
6. Run the governance record checker and relevant tests before closeout.

The read-only Performance and Security Reviewers return paths, commands,
evidence class, findings, and unresolved risks; the Project Manager owns all
completion decisions and identifiers. There is no always-running progress
agent and no automatic external issue-tracker write.

Project agent files are shared. Local `.codex/config.toml` remains ignored so
IDE endpoints, personal approvals, and per-user concurrency limits never enter
the repository. Users may set `agents.max_concurrent_threads_per_session = 2`
in that local file when they want the recommended cap.

## Required records

| Change | Required update |
|---|---|
| material implementation | STATUS and TODO |
| invariant, boundary, dependency, accepted architecture | new ADR |
| benchmark or performance statement | EXP with raw evidence location |
| unresolved design question | OPEN_QUESTIONS |
| intended component relationship | ARCHITECTURE |
| chronological context or environment observation | dated log |

Accepted ADRs are superseded, not silently rewritten. Analytical, simulated,
emulated, FPGA, and silicon evidence are never merged into one claim.

## Verification record

Before declaring completion, record:

- exact commands and exit status;
- Git revision;
- relevant tool versions and platform;
- test counts and skipped checks;
- raw-log path/hash when appropriate;
- remaining non-claims and unverified assumptions.

Use the templates in [`templates/`](templates/).

## Commit messages

Use one atomic commit for one independently reviewable change. Split unrelated
implementation, experiment, decision, or workflow work before committing.

Use this format:

```text
type(scope): imperative summary

Optional rationale and boundary notes.

Records: STATUS, TODO, ADR-000N, EXP-000N, RFC-000N, log/YYYY-MM-DD, or none
Evidence: exact validation command(s), result, and evidence class; or not run
```

Allowed `type` values are `feat`, `fix`, `docs`, `test`, `build`, `chore`, and
`research`. Use a short component or record family for `scope` (for example,
`sonatine`, `experience`, `records`, or `governance`). Keep the subject in
English imperative form without a trailing period. `Records` and `Evidence`
are required trailers so history preserves the relevant project memory and the
strength of the claim.
