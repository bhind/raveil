# Raveil Sprint cycle

Use this reference only for the current operating phase. Repository records and
`scripts/project_queue.py --help` remain authoritative if an example drifts.

## Read-only audit and status

From a clean current-main clone or the active task worktree, capture:

```sh
git status --short --branch
git rev-parse HEAD
python3 scripts/project_queue.py audit
python3 scripts/project_queue.py audit --require-horizon
gh project view 1 --owner @me --format json
gh project field-list 1 --owner @me --limit 100 --format json
gh project item-list 1 --owner @me --limit 100 --format json
```

Resolve the configured Iteration dates from the Project rather than guessing
from the calendar. Compare the live pull with `TODO.md` and `docs/STATUS.md`.
Report separately:

- committed and active work;
- Ready work that is actually pullable;
- Blocked work with its exact blocker;
- closed Issues or merged PRs whose Project/records disagree;
- worktrees with no active real-Issue packet; and
- missing acceptance or evidence.

Do not repair state during a status-only request unless the user also authorized
the mutation.

The ordinary audit may pass with an empty horizon so technical integration is
never delayed. `--require-horizon` is the replenishment trigger: zero complete
P1/Ready successors requires immediate refinement, not an idle handoff.

## Kickoff and immediate next pull

1. Read current weekly Codex telemetry. It is valid only when the window is
   10,080 minutes. Record timestamp, used percentage, and `100 - used` remaining.
2. Choose one Sprint goal and one executable demo. Order candidates by current
   P0 authority, dependencies, user/research value, and risk reduction.
3. Confirm that no more than two independently acceptable mutation items would
   be active and that their files, artifacts, tests, and evidence do not overlap.
4. Check Definition of Ready in `docs/SPRINTS.md`. Create or refine one real
   `work-item` Issue with the full packet before assigning mutation. Prepare
   the successor through the canonical transition, which writes metadata before
   `Ready` and keeps it P1:

```sh
python3 scripts/project_queue.py prepare ISSUE \
  --owner-role ROLE \
  --depends-on DEPENDENCIES \
  --sprint S-NNNN \
  --story-points SP \
  --demo COMMAND \
  --evidence-class CLASS
python3 scripts/project_queue.py prepare ISSUE \
  --owner-role ROLE \
  --depends-on DEPENDENCIES \
  --sprint S-NNNN \
  --story-points SP \
  --demo COMMAND \
  --evidence-class CLASS \
  --apply
```

5. Create the dedicated branch/worktree, then dry-run and apply the canonical
   start command. `start` promotes the prepared P1 successor to P0 and moves
   status last:

```sh
python3 scripts/project_queue.py start ISSUE \
  --owner-role ROLE \
  --depends-on DEPENDENCIES \
  --sprint S-NNNN \
  --story-points SP \
  --demo COMMAND \
  --evidence-class CLASS
python3 scripts/project_queue.py start ISSUE \
  --owner-role ROLE \
  --depends-on DEPENDENCIES \
  --sprint S-NNNN \
  --story-points SP \
  --demo COMMAND \
  --evidence-class CLASS \
  --apply
python3 scripts/project_queue.py audit --check-branch
```

`start` writes metadata before moving status last. A failure leaves the item
non-active; inspect and correct the named boundary rather than bypassing it.

## Continuation and atomic checkpoints

Before resuming an existing branch, run:

```sh
python3 scripts/project_queue.py audit --check-branch
git status --short --branch
git diff --check
```

Verify that the Issue is open, `In Progress` or `Review`, in the configured
Sprint, and still matches the full T-ID, owner, allowlist, acceptance, stop
rule, and evidence class. At each atomic commit record the exact command and
result locally; Project status does not advance merely because a commit exists.

Before the current item enters Review, run the horizon check. If it reports no
pullable successor, begin the replenishment procedure below without delaying
the current item's technical acceptance.

If a safe bounded correction stays inside the packet, add the regression and
continue. Apply HCI-04/HCI-07 when evidence identity cannot be reconciled or the
same root-cause class reaches the retry boundary. Do not start unrelated work
while waiting on an HCI.

## Rolling horizon replenishment

Maintain, when evidence and dependencies permit:

- one active P0 delivery item;
- one completely prepared P1/Ready successor; and
- one forecast Backlog candidate for the following boundary.

Replenish no later than the active P0 Review boundary:

1. Run the ordinary queue audit and `audit --require-horizon`.
2. If one pullable Ready item exists, retain it. Do not manufacture another
   mutation merely to fill a number.
3. If none exists, read current executable gaps, STATUS, TODO, ROADMAP and
   OPEN_QUESTIONS; de-duplicate existing tasks; and rank at most three bounded
   candidates by dependency, user/research value, and risk reduction.
4. If one candidate is unambiguous under current authority, allocate or refine
   its real Issue packet, link it to the Project, use `prepare`, and rerun the
   horizon check. Candidate discovery may use read-only low-cost agents, but PM
   retains the task decision and records.
5. If candidates imply materially different product direction, cost, license,
   device action, an invariant change, or another HCI, preserve the ranked
   packet and ask the owner one concrete question. Continue safe read-only
   work; do not report generic waiting.
6. A missing candidate is itself a bounded planning problem. It is not evidence
   that delivery is complete.

This process never delays merging an otherwise accepted PR. Replenishment and
technical integration are separate control paths; final PM record edits remain
serial.

## Wednesday correction

Read the same audit surface and compare actual accepted packets, remaining work,
blocked time, warm/cold state, and resource use with the plan.

- Never change `Initial SP`.
- Change current `Story Points` only with a dated `Estimate Change Reason`.
- Carry unfinished work explicitly; do not award partial points.
- Split work only when each child has an independently acceptable outcome and
  non-overlapping authority packet.
- Keep committed Iterations distinct from `Forecast Sprint` and forecast dates.
- Above the 13--21 SP warm band, recheck lane load and resource usage; the band
  is not itself a stop condition.

Project field edits are PM-owned remote mutations. Read IDs from the current
Project schema; never hard-code retained field or option IDs in repository
instructions.

## Task PR review and integration

Before `Review`, verify the PR head is the task head, the PR body closes the
real Issue, the diff stays in the allowlist, tests and records are current, and
all review threads are resolved. Then dry-run and apply:

```sh
python3 scripts/project_queue.py review ISSUE --pr PR
python3 scripts/project_queue.py review ISSUE --pr PR --apply
python3 scripts/project_queue.py audit --check-branch
```

Run the task's acceptance/evidence commands at the reviewed revision. An
incident-free PR may merge under ADR-0058 after the primary verifies the
intended diff, current authority ancestry, acceptance, records, mergeability,
checks, and review threads. After merge, verify that the Issue is closed, then
dry-run and apply the canonical completion transition:

```sh
python3 scripts/project_queue.py complete ISSUE --pr PR \
  --review-outcome 'EXACT TECHNICAL ACCEPTANCE AND NON-CLAIMS' \
  --observed-cycle 'OBSERVED DELIVERY CYCLE; LABEL UNSEALED TIME' \
  --resource-use 'ENVIRONMENT, USAGE READING, AND EXTERNAL RESOURCES'
python3 scripts/project_queue.py complete ISSUE --pr PR \
  --review-outcome 'EXACT TECHNICAL ACCEPTANCE AND NON-CLAIMS' \
  --observed-cycle 'OBSERVED DELIVERY CYCLE; LABEL UNSEALED TIME' \
  --resource-use 'ENVIRONMENT, USAGE READING, AND EXTERNAL RESOURCES' \
  --apply
python3 scripts/project_queue.py audit
```

`complete` requires the merged PR to close the matching work-item Issue,
preflights all evidence fields, writes them first, and moves `Status=Done`
last. It is idempotent after Done. Automation or Project metadata alone never
proves task completion.

Do not require the owner to attend or accept a demo for every ordinary task.
Continue integrating technically accepted tasks through the Sprint unless the
owner or an explicit task-specific risk gate requires a separate human review.
Task merge or task `Done` does not accept the weekly Sprint Review ceremony.

Run `audit --require-horizon` before or alongside this boundary. A failure
starts replenishment but does not make an otherwise valid implementation PR
unmergeable.

## Executable weekly Sprint Review

At the scheduled weekly ceremony, choose the representative runnable outcome
or outcomes from the integrated Sprint work. Run the recorded demo at an
identified revision and capture command,
revision, environment, exit status, evidence class, visible change, failures,
and non-claims. Prose or mock output is not a runnable increment. If the new
increment fails, demonstrate the last accepted baseline and the exact failing
boundary without calling the item Done.

Command success creates a review candidate only. Show the owner the actual
output or visible interface and explain what each relevant result proves, what
it does not prove, and what remains unfinished. Let the owner exercise a
human-facing Playable when practical. Classify feedback as defect, new
feature/Product Backlog item, research question, or transient observation;
de-duplicate durable feedback and route it to a stable task and Issue or
Backlog item as appropriate.

Keep the Sprint review ceremony non-Done until the owner explicitly chooses
`Accept`, `Conditional Accept`, `Carry`, or `Reject`. A `Conditional Accept`
may close the ceremony only after every condition has a tracked destination;
it neither implements nor completes that destination. Record the disposition,
conditions, and links in `Review Outcome` before moving status last.

## Saturday closeout, retrospective, and handoff

1. Reconcile STATUS, TODO, ROADMAP, OPEN_QUESTIONS, relevant ADR/RFC/EXP, and
   the dated log from verified repository evidence.
2. Run the task-governance record checker, relevant tests, `git diff --check`,
   and the live queue audit. Keep exact commands and exit codes.
3. Update the private Project README through the latest owner-accepted `Done`
   review and latest repository-accepted task item; do not conflate the two.
4. Record accepted, rejected, carried, and dropped scope. Retain failures and
   all evidence-class non-claims.
5. Record exactly one `Keep`, one evidence-backed `Problem`, and one bounded
   `Try`. Create or reuse a T-ID only when `Try` is durable actionable work; at
   most one process action enters the next Sprint.
6. Recheck the HCI-09 weekly usage guard and rolling horizon. Select one next
   pull only from work whose canonical trigger, dependencies, Definition of
   Ready, Sprint, and WIP boundaries are satisfied.

7. When the owner accepted the review and Keep/Problem/Try are recorded, run
   the kickoff dry-run and apply immediately for that one ready item.
   Do not wait for Monday solely because the next Iteration's reporting date
   has not begun.

If there is no pullable item, enter rolling horizon replenishment. Return to the
owner only for a material strategic fork, an HCI, the verified usage stop, or an
exact external dependency after bounded candidate discovery. Never convert an
empty queue into a generic idle or finished handoff. A closed Sprint may still
be unsuccessful; truthful failure remains a valid review outcome.

## Sunday recovery and remaining preparation

Sunday is not the normal review day. Use it to reconcile records and Project
state exposed on Saturday, preserve a failed demo, perform an already-
authorized bounded correction followed by an explicit re-review, or prepare
work that was not ready at closeout. Do not add scope to the already-reviewed
Sprint. Ready next-Sprint work should already have been pulled immediately
after accepted review and postmortem.

## Phase receipt

Use this stable handoff shape:

```text
Phase / Sprint:
Authority / branch / T-ID:
Usage window / observed-at / remaining:
Project audit / active WIP:
Commands and exit status:
Evidence class:
Accepted / carried / blocked / dropped:
HCI or none:
Next action:
```
