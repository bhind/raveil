# Raveil Sprint cycle

Use this reference only for the current operating phase. Repository records and
`scripts/project_queue.py --help` remain authoritative if an example drifts.

## Read-only audit and status

From a clean current-main clone or the active task worktree, capture:

```sh
git status --short --branch
git rev-parse HEAD
python3 scripts/project_queue.py audit
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

## Kickoff and Monday planning

1. Read current weekly Codex telemetry. It is valid only when the window is
   10,080 minutes. Record timestamp, used percentage, and `100 - used` remaining.
2. Choose one Sprint goal and one executable demo. Order candidates by current
   P0 authority, dependencies, user/research value, and risk reduction.
3. Confirm that no more than two independently acceptable mutation items would
   be active and that their files, artifacts, tests, and evidence do not overlap.
4. Check Definition of Ready in `docs/SPRINTS.md`. Create or refine one real
   `work-item` Issue with the full packet before assigning mutation.
5. Create the dedicated branch/worktree. Put the Project item in `Ready`, then
   dry-run and apply the canonical start command:

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

If a safe bounded correction stays inside the packet, add the regression and
continue. Apply HCI-04/HCI-07 when evidence identity cannot be reconciled or the
same root-cause class reaches the retry boundary. Do not start unrelated work
while waiting on an HCI.

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

## PR review and executable Sprint review

Before `Review`, verify the PR head is the task head, the PR body closes the
real Issue, the diff stays in the allowlist, tests and records are current, and
all review threads are resolved. Then dry-run and apply:

```sh
python3 scripts/project_queue.py review ISSUE --pr PR
python3 scripts/project_queue.py review ISSUE --pr PR --apply
python3 scripts/project_queue.py audit --check-branch
```

Run the Sprint's recorded demo at the reviewed revision and capture command,
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

An incident-free PR may merge under the standing authority in ADR-0058 after
the primary verifies the intended diff, current authority ancestry, acceptance,
records, mergeability, checks, and review threads. After merge, verify that the
Issue is closed and Project status is `Done`; automation or Project metadata
alone never proves task completion.

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
6. Recheck the HCI-09 weekly usage guard. Select one next pull only from work
   whose canonical trigger, dependencies, Definition of Ready, Sprint, and WIP
   boundaries are satisfied.

If there is no pullable item, finish with the exact missing trigger rather than
inventing work. A closed Sprint may be unsuccessful; truthful failure is a valid
review outcome.

## Sunday recovery and Monday preparation

Sunday is not the normal review day. Use it only to reconcile records and
Project state exposed on Saturday, preserve a failed demo, perform an
already-authorized bounded correction followed by an explicit re-review, or
prepare Ready work for Monday. Do not add new closing-Sprint scope. Anything
not accepted on Saturday or through that bounded re-review carries explicitly.

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
