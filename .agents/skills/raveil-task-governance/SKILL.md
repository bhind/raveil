---
name: raveil-task-governance
description: Govern Raveil changes and progress reviews by mapping work to stable tasks and gates, collecting issue candidates, applying the source-of-truth order, selecting STATUS/TODO/ROADMAP/OPEN_QUESTIONS/ADR/EXP/log updates, and checking closeout evidence. Use for material code or documentation changes, status/progress requests, issue triage, task kickoff, and completion review.
---

# Raveil Task Governance

## Kickoff

1. Read `AGENTS.md` and route records through `docs/README.md`.
2. Inspect `git status/diff`, relevant code/tests, STATUS, and TODO.
3. Identify the existing T-ID, roadmap gate, and related ADR/RFC/EXP. State
   explicitly when none applies.
4. Classify the request as implementation fact, decision, proposal, experiment,
   environment observation, or documentation-only organization.

## Progress and issue audit

1. Compare code/tests with STATUS before trusting plans or logs.
2. Separate verified completion candidates, actionable new issues, blockers,
   dependencies, stale records, and missing evidence.
3. Search TODO before proposing a task. Give a new issue an ID candidate only
   after the primary agent confirms it is actionable and not duplicated.
4. Use a read-only reviewer subagent for an independent audit when the scope is
   broad. Treat its output as a proposal, not authority.

## Record routing

- implemented and verified fact → STATUS;
- actionable work or execution state → TODO;
- gate condition or state → ROADMAP;
- unresolved design → OPEN_QUESTIONS or RFC;
- accepted invariant, boundary, or dependency → new ADR;
- measurement or performance claim → EXP;
- dated observation → log.

Documentation-only reorganization does not change STATUS unless it also changes
an implementation fact. Preserve analytical, simulated, emulated, FPGA, and
silicon evidence as separate classes.

## Closeout

1. Run `python3 scripts/check_records.py` from this skill directory.
2. Run proportionate code/tests and record exact commands, exit status,
   environment, versions, and raw-log hash when relevant.
3. Reconcile STATUS, TODO, ROADMAP, OPEN_QUESTIONS, relevant ADR/RFC/EXP, and
   the dated log.
4. Mark a task complete or change a gate only from verified repository evidence.
5. Keep learned, retrieved, conversation, and subagent output as advice. The
   primary agent owns identifiers, tracked-file edits, and final conclusions.
