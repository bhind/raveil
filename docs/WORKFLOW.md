# Development and research workflow

Last updated: 2026-08-29

## Before a change

1. Read `AGENTS.md` and use `docs/README.md` to select relevant records.
2. Inspect Git status and preserve unrelated user changes.
3. Check the canonical start-timing table in `TODO.md`. Do not start or resume
   implementation outside P0 merely because a branch, patch, local change, or
   unfinished milestone exists. Promotion follows
   `docs/guides/TASK-START-PHASES.md` and requires a dated trigger record.
4. Every newly active P0 task or independently acceptable child slice uses one
   real GitHub Issue labelled `work-item`, linked to Project #1. Its title
   contains the stable T-ID; its body records authority, dependencies, mutation
   owner and allowlist, acceptance command, evidence class, and non-claims.
   Historical DraftIssue cards remain intact, but a DraftIssue cannot authorize
   new mutation. GitHub remains coordination metadata rather than task or
   evidence authority.
5. For tracked work, create a dedicated branch named
   `<type>/<record-id>-<short-slug>` in lowercase kebab-case. Types are `feat`,
   `fix`, `research`, `docs`, `test`, `build`, and `chore`; use the primary
   lowercase `t-`, `exp-`, `adr-`, or `rfc-` ID. Example:
   `research/exp-0003-gate1-measurement`. Read-only review does not require a
   new branch.
6. From that branch, dry-run `python3 scripts/project_queue.py start ISSUE
   --owner-role ROLE --sprint S-NNNN --story-points SP --demo COMMAND
   --evidence-class CLASS`,
   repeat it with `--apply`, and then run `python3 scripts/project_queue.py
   audit --check-branch`. `start` fails closed on a mismatched T-ID, closed or
   unlabeled Issue, missing field, or non-matching branch; the post-transition
   audit proves that the branch now has a matching active Project Issue. Pass
   `--depends-on` explicitly; child-slice Issues such as `T-0123/S03` use a
   branch segment such as `t-0123-s03` so two slices cannot collapse to one
   parent identity.
7. Push only the dedicated change branch and integrate it through a GitHub pull
   request. Never push directly to `refs/heads/main`.
8. Read executable code/tests first, then STATUS and TODO. Load only the ADR,
   architecture, roadmap, EXP, question, or log records selected by the
   document router for this task.
9. Classify the proposed work as an implementation fact, decision, hypothesis,
   experiment, or environment observation.

## During a change

- Keep the implementation work-in-progress limit at two independently
  acceptable P0 items under ADR-0061. Each requires a distinct T-ID or bounded
  child slice, worktree, branch, mutation owner, file allowlist, artifacts,
  tests, and evidence path. If either item needs the other's mutable files or
  acceptance result, they are one serial item, not parallel work. Read-only
  reviews and bounded evidence preservation do not consume this delivery WIP.
  Canonical records, PR acceptance, and merge remain one serial Project Manager
  lane.
- Project status is a lifecycle assertion, not a retrospective note. `Ready`
  means the packet is pullable; `In Progress` means its named owner and branch
  are active; `Review` means an open PR contains `Closes #ISSUE`; `Blocked`
  retains the exact blocker; merge closes the Issue and `Done` must agree with
  that closed state. Run `python3 scripts/project_queue.py audit` at kickoff,
  PR review, and closeout. The audit rejects active DraftIssue cards, open
  `work-item` Issues missing from the Project, more than two active delivery
  items, lifecycle/T-ID disagreement, and missing visible execution fields.
  ADR-0066 includes Sprint among those required active fields. `start` resolves
  the named configured Iteration before any remote write and records it before
  moving status last; an unknown or missing Sprint fails closed.
- Treat eight SP as an under-utilization lower-bound check, 13 SP as the
  provisional committed weekly capacity, and 13--21 SP as the warm stretch
  range. Do not stop authorized work merely because a forecast SP total was
  reached; at the upper range re-check WIP, lane load, and token/resource
  budget before pulling more work.
  ADR-0059 treats SP as relative AI delivery risk and schedules actual work by
  dependency, two-item delivery WIP, and role-lane availability. ADR-0060
  independently forbids starting new costly work when verified weekly Codex
  usage remaining is below five percent.
- Keep external types behind Raveil-owned versioned adapters.
- Keep Experience outside authority and preserve a trusted baseline/rollback.
- Allocate task, ADR, EXP, and RFC identifiers monotonically.
- Do not erase rejected approaches or failed results.
- Exclude credentials, generated logs, build products, IDE-local state, and
  absolute machine paths.

## Continuous execution and human-confirmation incidents

ADR-0051 makes continuous local execution the default after the owner has
authorized a bounded task. Investigation, assigned edits, local atomic commits,
tests, candidate-independent smokes, reviews, required record reconciliation,
and the next accepted slice proceed without an acknowledgement checkpoint. A
status report is non-blocking. This default does not enlarge task scope,
authority, external access, or scientific claims.

An agent pauses only the affected mutation or evidence collection when one of
the following exhaustive Human-confirmation incident classes occurs. Safe
read-only diagnosis and already-authorized non-overlapping verification may
continue while the incident is reported.

### HCI-01: scope or authority expansion

Confirmation is required before changing the authorized goal, promoting or
replacing P0, starting a second implementation P0, changing a trusted contract
or authority invariant, introducing a new top-level subsystem, or moving to a
new ISA, FPGA, ASIC, silicon, product-deployment, or other unapproved project
line. A learned system, retrieved result, LLM, backend, or subagent never gains
admission, semantic, publication, evidence, or gate authority through this
workflow.

### HCI-02: irreversible experiment or gate boundary

Confirmation is required immediately before the first claim-bearing manifest
freeze or candidate-data collection for a new experiment; before changing a
scientific field after candidate data exists; and before declaring an EXP or
roadmap `advance`, `pause`, `pivot`, `falsified`, `go`, `no-go`, or gate-state
change. Drafting the experiment, implementing its harness, and
running candidate-independent toolchain or functional smokes may continue.

An operational-only correction that preserves every frozen scientific field
may continue after the failed attempt is retained, unless HCI-07 applies.

### HCI-03: destructive or remote action

Confirmation is required before deleting, overwriting, resetting, force-
checking-out, force-pushing, rewriting history, moving tags, discarding or
stashing user work, or replacing immutable evidence. It is also required before
issue-state mutation, tag or Release publication, package
publication, or external benchmark publication unless the owner already
authorized that exact remote action and target.

For an already authorized bounded change, pushing its dedicated branch and
creating or updating its pull request are the required integration path and do
not create a separate HCI. Direct push to `main` is prohibited even when the
change is otherwise authorized. The repository ruleset has no bypass actor,
requires a pull request, blocks deletion and non-fast-forward updates, and
requires review threads to be resolved.

ADR-0058 provides standing authority to merge an incident-free PR immediately.
Before merge, the primary must verify the intended diff, current authority
ancestry, recorded acceptance commands, required record reconciliation, clean
GitHub mergeability, required checks, and resolved review threads. The merge
must not change a gate or EXP conclusion, publish a release or benchmark, hide
an evidence ambiguity, overlap user work, delete the remote branch, or trigger
any other HCI class. Any such condition pauses the merge; absence of a condition
allows it without a separate acknowledgement checkpoint.

Creating an isolated local worktree, local branch, local atomic commit, ignored
build product, or new append-only local artifact is not an HCI.

### HCI-04: evidence-integrity ambiguity

Confirmation is required when source, authority, toolchain, manifest, resource,
oracle, matrix, raw seal, result seal, or evidence-class identity cannot be
reconciled without changing the frozen boundary; valid and invalid evidence can
no longer be separated; a raw artifact would need editing or selective
omission; or a pass would require weakening a fail-closed check. Preserve the
failed material and do not reinterpret it.

An ordinary fail-closed test with an identified implementation defect is not an
HCI. Correct it inside the assigned files, add a regression where appropriate,
and continue.

### HCI-05: user-work overlap

Confirmation is required when the authorized change would edit, move, rebase,
merge, resolve, stash, or discard uncommitted work owned by the user or another
agent. The mere existence of such work is not an HCI: create a clean isolated
worktree and continue. Unexpected modifications in that clean worktree become
an HCI when their ownership cannot be established.

### HCI-06: cost, credentials, publication, or legal-risk expansion

Confirmation is required before purchasing hardware, cloud capacity, API
credits, software, or licenses; exceeding an approved service plan; using
personal credentials, secrets, private endpoints, or owner accounts; uploading
unpublished material outside an approved immutable destination; or adopting an
external dependency with unresolved material source, license, redistribution,
provenance, patent, or standards risk. Read-only inventory may continue. No
agent declares patent clearance, freedom to operate, production security, or
commercial readiness.

### HCI-07: repeated blocker or resource overrun

The first bounded operational failure is not an HCI. Retain it when required,
diagnose it, add the narrow correction and regression, and retry if the
scientific boundary is unchanged. Confirmation is required when the same root-
cause class fails twice consecutively, two recovery attempts have already been
made at one boundary, a third recovery manifest would be required, no bounded
fix remains inside assigned files, the current estimate exceeds twice its last
evidence-backed value, or an unapproved attempt is expected to exceed six host
hours or 20 GiB of new local artifacts.

### HCI-08: material design fork

Confirmation is required when viable alternatives materially change a public
contract, physical-resource denominator, comparison fairness, specialization
versus generality, existing-backend versus custom-hardware dependency, cost by
approximately twofold or more, or reversibility. Naming, refactoring, internal
helper structure, equivalent tool-compatibility corrections, and other
reversible choices are not HCIs; select the simplest adequate option and
continue.

### HCI-09: weekly Codex usage guard

The weekly cost guard uses a current Codex account rate-limit reading only when
its weekly `windowDurationMins == 10080`. Calculate
`remaining = 100 - usedPercent`; never substitute Sprint SP, daily limits,
reset credits, account balances, or an estimate.

When `remaining < 5`, pause before starting a new task, spawning or assigning a
subagent, starting a long-running build or verification, updating a remote
work item or pull request, or merging. Exactly five percent remaining is not
below the threshold and may continue cautiously, with another reading before
each new costly boundary. Work already running may proceed only far enough to
retain the smallest safe receipt when immediate interruption would lose
evidence. Start no downstream work and notify the owner of the observed weekly
window, used percentage, remaining percentage, and preserved state.

Check the guard before every new task, subagent, or long-running job, and again
after completing a task before pulling the next item. If telemetry is
unavailable, stale, malformed, or cannot be verified as the 10,080-minute
weekly window, do not claim active monitoring and do not begin a new costly
action; fail closed until visibility is restored or the owner supplies a
current UI reading. A current reading with `remaining >= 5` clears this
incident without a ceremonial acknowledgement. Consuming reset credits,
purchasing capacity,
changing a service plan, or bypassing the threshold remains HCI-06 and requires
separate explicit owner authority. Project records may retain observation time,
window, used percentage, and remaining percentage, but never account IDs,
credentials, secrets, or reset-credit identifiers.

This guard controls service cost and continuation only. It does not change SP,
WIP, task status, evidence class, experiment state, or a research or hardware
gate.

### Incident report and progress cadence

An HCI report contains:

1. incident ID and one-sentence trigger;
2. authority commit, branch, and affected files or artifacts;
3. completed work and preserved evidence, including hashes when relevant;
4. why current authority is insufficient;
5. two or at most three mutually exclusive options;
6. a recommendation with scope, evidence, cost, and schedule impact; and
7. one exact authorization question.

Do not ask an open-ended status question. Stop only the affected action and do
not begin a different implementation P0 while waiting. In the absence of an
HCI, continue and send concise non-blocking updates after an atomic commit or
acceptance boundary and at least hourly during an interactive long-running
operation. Do not invent work merely to keep an agent active.

## Duration estimates and authority freshness

Before giving a user or Project Manager a duration estimate:

1. Name the exact T-ID, authority commit, exit conditions, and explicit
   non-goals. A scope change invalidates every earlier estimate.
2. Classify every exit condition as already verified, reusable with no code
   change, configuration/wrapper work, new implementation, or unresolved.
3. Inspect the actual working tree, relevant modules/tests, available warm and
   cold build paths, and the observed delivery rate of the current execution
   environment. Do not infer effort from the task title or superseded scope.
4. Run the cheapest representative command that exposes build/cache state, or
   state exactly why it was not run.
5. Estimate edit, verification, and integration/review effort separately. Give
   warm and cold wall-clock ranges, confidence, and invalidation conditions.
6. Record the basis with `docs/templates/ESTIMATE-TEMPLATE.md`. Do not publish a
   calendar estimate whose inventory or evidence fields are blank.

After any accepted scope, dependency, base-commit, cache, owner, or execution-
environment change, recompute the estimate before repeating it.

Before declaring a branch complete, identify the latest named authority commit
and run:

```sh
git merge-base --is-ancestor <authority-commit> HEAD
```

Exit 0 is necessary but not sufficient for completion. A nonzero exit makes the
branch an implementation candidate pending integration and re-verification;
do not mark TODO, STATUS, ROADMAP, ADR, or EXP complete from that branch.

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
- The Librarian, Vreji, is read-only and owns context routing plus prior-art
  similarity and IP-risk inventory/escalation under ADR-0014. Vreji separates
  copyright/access from patent or standards licensing and reports `unreviewed`
  gaps; it does not decide facts, identifiers, gates, claims, infringement,
  legal clearance, freedom to operate, or implementation approval.
- Do not allow concurrent changes to one coherent file set. The Project
  Manager performs final integration and canonical record reconciliation.
- Use at most two low-reasoning implementers for separately authorized,
  non-overlapping mutation packets, then one low-reasoning Tester per accepted
  packet. Up to two read-only high-reasoning reviewers may run in
  parallel only when the security, performance, or final-PR risk warrants it.
  The Librarian is medium read-only, and the high-reasoning Researcher runs only
  after an evidence milestone. Chisel work uses its dedicated implementer and
  does not silently expand the Systems role.
- `raveil-task-governance` applies the record and evidence checklist to any
  material Raveil change. `raveil-gate0-evidence` applies the specific
  Sonatine Microkernel Gate 0 collection procedure.
- `raveil-sprint-operator` applies the repeatable weekly audit, kickoff,
  continuation, Wednesday correction, executable review, closeout,
  retrospective, and next-pull loop. It calls `project_queue.py` rather than
  duplicating queue transitions and returns one stable phase receipt.
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

### Weekly sprints

Use the GitHub Project cadence in [`SPRINTS.md`](SPRINTS.md) to cap work in
progress and require a runnable increment. Reference stable T-IDs, calculate
initial story points at planning, and retain every estimate revision with a
dated reason. Run planning on Monday, correction review on Wednesday, and the
executable review plus retrospective on Saturday. Sunday is a bounded recovery,
record-reconciliation, and Monday-handoff buffer, not the normal ceremony or a
license to pull new closing-Sprint scope.

Use `raveil-sprint-operator` for every Sprint status, kickoff, continuation,
correction, review, closeout, retrospective, and next-pull boundary. The skill
standardizes the audit and handoff receipt while this workflow, `SPRINTS.md`,
the canonical records, and `project_queue.py` retain authority.

ADR-0069 makes the owner-visible review interaction a separate fail-closed
boundary from command success. Keep the Sprint review ceremony non-Done until
the actual output or interface has been shown and explained, durable feedback
has been classified and routed, and the owner has explicitly selected
`Accept`, `Conditional Accept`, `Carry`, or `Reject`. A conditional acceptance
requires a stable destination for every condition; it does not mark those
follow-ups complete.

Maintain an ordered Product Backlog, not only the current Sprint. The live pull
surface uses only Title, Status, Priority, Parent T-ID, Owner Role, Depends On,
Sprint, Story Points, Demo Command, and Evidence Class. Retain richer historical
fields but keep them out of the default execution view unless a review needs
them. Synchronize the Project when a branch starts, reaches its first atomic
commit, opens a PR, enters review, blocks, or merges. A worktree without a
matching live Project item is preserved provenance or a donor, not active WIP.
Keep the Project README current through the latest Done item, keep its current
pull consistent with TODO, and move a non-pullable Draft out of `Ready`.
Refine at least the next two sprints into independently acceptable slices with one owner
role, support roles, dependencies, priority, evidence class, initial SP, and a
demo or evidence command. Apply the Definition of Ready and Definition of Done
in `SPRINTS.md`. Do not assign SP to both an epic and its children, and do not
treat the configured agent roles as additional human FTE. Committed Iterations
and low-confidence forecast dates remain visibly separate.

Use a clean current-main clone or worktree as the normal operator entry point.
Preserve dirty historical roots as donor/provenance worktrees; never reset,
stash, or treat their stale records as current authority merely because they
occupy the original repository path.

The sprint board is a coordination view, not task or evidence authority.
`TODO.md` still owns task scope and execution state, and research review remains
milestone-driven. A sprint demo, completed points, or retrospective cannot by
itself close a T-ID, pass a ROADMAP gate, accept an ADR/RFC, conclude an EXP, or
promote analytical, simulated, emulated, FPGA, or silicon evidence.

Read back the current board before review:

```sh
gh project view 1 --owner @me --format json
gh project field-list 1 --owner @me --limit 100 --format json
gh project item-list 1 --owner @me --limit 100 --format json
```

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

## Failure and defect triage

Use ADR-0026's three layers:

- EXP/raw bundles for scientific failures and negative results;
- `docs/FAILURE_KNOWLEDGE.md` for short reusable prevention lessons;
- GitHub Issues for actionable software defects that need ownership beyond the
  current coherent branch.

Fix a small defect immediately when it is safe and in scope. If it is fixed on
the same branch with a regression test, record material context in the dated
log but do not create an issue solely for ceremony. Create or retain an issue
when the defect survives closeout, recurs, blocks a release, affects users,
crosses owners/components, threatens security or evidence integrity, or is
deliberately deferred.

At progress and milestone review:

1. de-duplicate against open GitHub Issues and TODO;
2. assign a monotonic T-ID to material actionable work;
3. link the issue to its T-ID and safe evidence rather than copying raw data;
4. promote only reusable, evidence-backed lessons to failure knowledge;
5. close the issue only after integration, regression verification, and record
   reconciliation.

At an owner-visible Sprint review, classify UI and product feedback before
creating work. Behavior that violates an accepted contract is a defect; a
missing capability outside the accepted contract is a new feature or Product
Backlog item; an untested mechanism or claim is a research question; and a
nonrecurring interaction note may remain a transient review observation.
De-duplicate durable work against TODO and open Issues before allocating the
next monotonic T-ID.

GitHub Issues is a coordination view, not project authority. The `work-item`
label serves active P0 delivery as well as retained cross-owner defects. If
GitHub is unavailable, record the T-ID and candidate locally, but do not begin
new tracked-file mutation until the real Issue and Project item can be created
and audited. Negative experiments, expected fail-closed behavior, transient
command errors, and speculative features are not bugs by themselves.

Never put sensitive security detail, credentials, internal URLs/hostnames,
absolute user paths, unpublished artifact contents, third-party text/figures,
patent claims, or standards-draft text in a public issue. Follow `SECURITY.md`
and escalate privately to the owner/Project Manager; Vreji inventories IP risk
but does not provide legal clearance.

## Verification record

Before declaring completion, record:

- exact commands and exit status;
- Git revision;
- relevant tool versions and platform;
- test counts and skipped checks;
- raw-log path/hash when appropriate;
- remaining non-claims and unverified assumptions.

Before requesting final PR review, run
`python3 scripts/project_queue.py review ISSUE --pr PR --apply`. It validates
that the open PR head carries the same T-ID and that the body closes the Issue,
then moves the item to `Review`. After merge, verify the closed Issue, `Done`
Project status, and canonical record reconciliation; Project state never closes
a task by itself.

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

## Feature releases and milestone tags

- A feature release is an immutable, owner-approved integration point with a
  defined scope, acceptance evidence, reconciled records, and a `v...` tag.
  The current decimal version sequence increments its final unit; an existing
  release tag is never moved or reused.
- Completed delivery milestones also receive an immutable annotated Git tag,
  even when they are not feature releases. Use
  `milestone/<record-id>-<short-slug>`, for example
  `milestone/t-0087-delivery-line-reconciled`.
- A milestone tag identifies the verified closeout commit. It does not imply a
  public release, performance result, Gate passage, or remote publication.
- Create a tag only after relevant tests, the governance record checker, and
  record reconciliation pass. Record the tag in the dated log.
- Remote tag or GitHub Release publication still requires the
  `raveil-remote-release` workflow and explicit owner approval.
