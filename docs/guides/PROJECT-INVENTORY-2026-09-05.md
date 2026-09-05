# Project inventory — 2026-09-05

This is a dated PM audit receipt, not a second live board. Task: T-0151 / [Issue #115](https://github.com/bhind/raveil/issues/115). Authority: canonical `82b196cb6093aceed5be06d19162660fd20a01f4`, executable code/tests, current records and the owner's explicit inventory request. No EXP/Gate conclusion or new Done is awarded.

## Target and snapshot

- Actual repository linkage and account Project discovery identify only [Raveil Weekly Sprints](https://github.com/users/bhind/projects/1), private Project #1. No alternate Project needs selection.
- Initial bounded full inventory: 81 items; the concurrent daily session added S-0002 during this audit. 79 historical PRs were inventoried before the two new candidate PRs. All remote branches and 248 local branch refs were inspected by identity; existence alone does not establish active work.
- Reread after registration/backlog repair: 97 visible items, Done=52, Backlog=40, Blocked=2, In Progress=2, Ready=1. This precedes later Review retries and concurrent daily updates; live Project wins for current coordination.
- Authorized GitHub authentication works with repo/project scopes. Weekly Codex account reading: 10080-minute window, 55% used / 45% remaining; no cost guard stop.

## Applied and preserved

- issue-create: `https://github.com/bhind/raveil/issues/116`.
- issue-create: `https://github.com/bhind/raveil/issues/117`.
- draft-create: `{'tid': 'T-0091', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwPY'}`.
- draft-create: `{'tid': 'T-0063', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwQA'}`.
- draft-create: `{'tid': 'T-0068', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwQg'}`.
- draft-create: `{'tid': 'T-0069', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwQ4'}`.
- draft-create: `{'tid': 'T-0071', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwRw'}`.
- draft-create: `{'tid': 'T-0073', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwSY'}`.
- draft-create: `{'tid': 'T-0018', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwS8'}`.
- draft-create: `{'tid': 'T-0025', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwTM'}`.
- draft-create: `{'tid': 'T-0050', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwT0'}`.
- draft-create: `{'tid': 'T-0051', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwUQ'}`.
- draft-create: `{'tid': 'T-0052', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwU4'}`.
- draft-create: `{'tid': 'T-0053', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwVg'}`.
- draft-create: `{'tid': 'T-0054', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwWI'}`.
- draft-create: `{'tid': 'T-0042', 'id': 'PVTI_lAHOAGTqgs4BhMtczg5iwWs'}`.
- archive-duplicate: `PVTI_lAHOAGTqgs4BhMtczg5Ak-I`.

- Corrected deferred T-0100/T-0055/T-0056/T-0058/T-0059/T-0104 priority to Icebox; T-0044 Epic and Blocked S13 to P2 behind the workspace. Original estimates and evidence remain. Added canonical record links to historical draft cards without claiming new acceptance.
- Preserved closed #83 and its evidence; linked it to #81 and archived only its duplicate T-0132/S07 card. #81 remains the single visible execution item.
- Published existing T-0148 candidate as [Draft PR #118](https://github.com/bhind/raveil/pull/118) and dependent T-0149 candidate as [Draft PR #119](https://github.com/bhind/raveil/pull/119). The latter targets the former branch and deliberately has no main-closing reference yet. Publication does not prove acceptance.

## Scope, identity and completion gaps

- T-0106/ADR-0046 already mean conditional CPU attribution hardening and controlled-run scope. The workspace donor is properly T-0149/local ADR-0085. Donor remains intact.
- Local workspace TODO uses T-0150 for a UIO source-scan failure, while real #114 already assigns T-0150 to Garden feedback. New monotonic T-0152/#117 owns the defect; candidate records must be remapped at PR integration.
- Owner keeps original broad T-0042 research unfinished. Accepted ADR-0046 and main TODO close only a narrowed controlled-run slice. The new deferred T-0042 scope card preserves both facts, with T-0106/T-0044 retaining existing implementation children. This discrepancy is not resolved by changing evidence or calling the workspace Done. PM reconciles scope before research resumption.
- T-0148 has a local checked TODO but no integrated main acceptance. Its exact RTL receipts and prior reviews need verification for PR #118; the omitted StaticStencilRegion.scala packet path is a single program-version wire, directly inspected in the candidate diff.
- T-0149 already contains CLI/tests/launcher on local candidate 31262f1; the original root initial-draft description is historically accurate but stale for that candidate. The exact diff also includes NativeWorkspace.mkdir(mode) and the underscore-named PROJECT_WORKSPACE guide; Issue packet corrections are in the pending sync list below.
- Daily T-0151 implementation is concurrently dirty in a separate worktree. This inventory does not edit or accept it, install its scheduler, or close #115. Its own completion requires dry-run/idempotence/error tests and actual local registration/rehearsal.

## Done evidence inspection

For existing Done items, inspect the retained task record and matching merged PR below. A PR URL is integration evidence, not a substitute for its tests. Historical draft evidence varies: missing precise locators are listed as unresolved verification gaps. This inventory grants no new Done and does not rerun historical RTL or research experiments.

| Full item | Integration/evidence locator | Inventory disposition |
|---|---|---|
| S-0001 — Sprint review, runnable demo, and retrospective | PR #61 | Separate ceremony; owner acceptance is not inferred by this audit. Concurrent daily session owns disposition. |
| T-0116 — Establish weekly sprint governance | [TODO](https://github.com/bhind/raveil/blob/main/TODO.md), [STATUS](https://github.com/bhind/raveil/blob/main/docs/STATUS.md) | Completion candidate / precise receipt linkage requires PM verification; status alone is not proof. |
| T-0106/S01 — [Systems] Preserve BOOM stripped-after-valid negative | PR #11 | Retained historical evidence pointer; no new acceptance. |
| T-0117/S01 — [Experience] Garden TUI read-only graph browser | PR #6 | Retained historical evidence pointer; no new acceptance. |
| T-0117/S02 — [Tester] Garden deterministic demo and terminal acceptance | PR #7 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S08 — [Chisel] Minimal integrated Graph/Rocket physical top | PR #9 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S10 — [Measurement] Integrated physical contract readiness validator | PR #12 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S09 — [Tester] Integrated top clean structural and oracle verification | [TODO](https://github.com/bhind/raveil/blob/main/TODO.md), [STATUS](https://github.com/bhind/raveil/blob/main/docs/STATUS.md) | Completion candidate / precise receipt linkage requires PM verification; status alone is not proof. |
| T-0118 — Calibrate AI role-lane capacity | PR #8; PR #8 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S11 — [Measurement] Integrated identity and denominator contract | PR #13 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S12 — [Measurement] Typed estimator and evidence-seal contract | PR #13; PR #14; PR #15 | Retained historical evidence pointer; no new acceptance. |
| T-0120 — Build the multi-pane Garden workspace | PR #16 | Retained historical evidence pointer; no new acceptance. |
| T-0122/S00 — [PM] Authorize two-lane simulation-first delivery | PR #18 | Retained historical evidence pointer; no new acceptance. |
| T-0122/S01 — [Chisel] Reconstruct the simulation-first Graph device MVP | PR #20 | Retained historical evidence pointer; no new acceptance. |
| T-0122/S02 — [Tester] Clean runtime-to-Pavane acceptance | PR #20 | Retained historical evidence pointer; no new acceptance. |
| T-0044/S14 — [Librarian] Read-only common-memory strategy inventory | PR #19 | Retained historical evidence pointer; no new acceptance. |
| T-0123/S01 — [Chisel] Generated schedule trace equivalence | PR #24 | Retained historical evidence pointer; no new acceptance. |
| T-0123/S02 — [Chisel] Install bounded affine configurations | PR #24; PR #25; PR #25 | Retained historical evidence pointer; no new acceptance. |
| T-0123/S03 — [Chisel] Execute external bounded DAGs | PR #25; PR #26 | Retained historical evidence pointer; no new acceptance. |
| T-0125 — Present the bounded Graph-device Playable | [PR #31](https://github.com/bhind/raveil/pull/31) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0126 — Make GitHub Project an executable work queue | [PR #30](https://github.com/bhind/raveil/pull/30) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0127 — Enforce the Project queue contract in every agent role | [PR #34](https://github.com/bhind/raveil/pull/34) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0128/S01 — Admit one accepted Graph submission | [PR #38](https://github.com/bhind/raveil/pull/38); [PR #37](https://github.com/bhind/raveil/pull/37) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0128/S02 — Execute one selected Graph on RTL simulation | [PR #41](https://github.com/bhind/raveil/pull/41); [PR #40](https://github.com/bhind/raveil/pull/40) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0128/S03 — Expose selected RTL execution through the top-level CLI | [PR #44](https://github.com/bhind/raveil/pull/44); [PR #43](https://github.com/bhind/raveil/pull/43) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0129 — Replay verified RTL transactions in the Graph-device CLI | [PR #46](https://github.com/bhind/raveil/pull/46) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0130 — Make GitHub Project sprint state truthful and fail closed | [PR #49](https://github.com/bhind/raveil/pull/49) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0131 — Make the Raveil sprint cycle a reusable operator skill | [PR #53](https://github.com/bhind/raveil/pull/53) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S01 — Prove the Graph-device AXI4-Lite control boundary | [PR #64](https://github.com/bhind/raveil/pull/64) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0133 — Move the recurring Sprint Review to Saturday | [PR #57](https://github.com/bhind/raveil/pull/57) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0134 — Require owner-visible Sprint review before Done | [PR #61](https://github.com/bhind/raveil/pull/61) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0135 — Explain materialized versus fused plans in Garden | [PR #67](https://github.com/bhind/raveil/pull/67) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0136 — Pull the next Sprint immediately after accepted review | [PR #66](https://github.com/bhind/raveil/pull/66) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0093 — Materialize one validated graph snapshot as a read-only directory | [PR #70](https://github.com/bhind/raveil/pull/70) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0137 — Separate task integration review from weekly Sprint Review | [PR #73](https://github.com/bhind/raveil/pull/73) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S02 — Install affine and program payloads through AXI4-Lite | [PR #76](https://github.com/bhind/raveil/pull/76) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S03 — Execute one bounded Graph through AXI4-Lite | [PR #79](https://github.com/bhind/raveil/pull/79) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S07 — Integrate the ordered S04-S07 AXI/UIO/RTL-export stack | [PR #82](https://github.com/bhind/raveil/pull/82) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S08 — Admit bounded runtime requests without rebuilding the Linux runner | [PR #86](https://github.com/bhind/raveil/pull/86) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S09 — Run two admitted requests through one AXI4-Lite simulator binary | [PR #88](https://github.com/bhind/raveil/pull/88) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0132/S10 — Expose the two-request runtime simulator through the operator CLI | [PR #90](https://github.com/bhind/raveil/pull/90) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0138 — Freeze the RFC-0004/S01 KV260 transition feasibility packet | [PR #92](https://github.com/bhind/raveil/pull/92) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0139 — Add a read-only KV260 readiness preflight | [PR #94](https://github.com/bhind/raveil/pull/94) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0140 — Execute a non-catalogue bounded Graph through one reusable simulator | [PR #96](https://github.com/bhind/raveil/pull/96) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0141 — Run one fan-out dynamic Graph through the reusable simulator | [PR #98](https://github.com/bhind/raveil/pull/98) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0142 — Seal, verify, and dry-run one dynamic request | PR #98; PR #100 | Retained historical evidence pointer; no new acceptance. |
| T-0143 — Add one versioned MAX_U32 Graph opcode | [PR #102](https://github.com/bhind/raveil/pull/102) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0144 — Explain bounded Graph execution in read-only Garden | [PR #104](https://github.com/bhind/raveil/pull/104) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0145 — Hand verified sealed dynamic Graphs to the Linux UIO runner | [PR #109](https://github.com/bhind/raveil/pull/109) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0146 — Keep a rolling P0 delivery horizon | [PR #108](https://github.com/bhind/raveil/pull/108) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| T-0147 — Make merged task closeout atomic | [PR #111](https://github.com/bhind/raveil/pull/111) | Retain historical Done; integrated PR exists; task-specific verification remains in canonical record. |
| S-0002 — Sprint review, runnable demo, and retrospective | [TODO](https://github.com/bhind/raveil/blob/main/TODO.md), [STATUS](https://github.com/bhind/raveil/blob/main/docs/STATUS.md) | Separate ceremony; owner acceptance is not inferred by this audit. Concurrent daily session owns disposition. |

## Unfinished task and item map

Unstarted/未着手 uses Backlog or fully refined Ready. Explicit conditional/deferred/保留 uses Backlog with a recorded restart trigger. Completion candidates stay Review/Blocked until evidence and integration pass. No new work is committed merely by the inventory.

| T-ID/item | Link | State / priority / owner | Dependency or next action |
|---|---|---|---|
| T-0106/S05 — [Security Reviewer] Non-CPU traffic exclusion review | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Security Reviewer | T-0106 start trigger; T-0106/S04 |
| T-0106/S03 — [Tester] BOOM pinned clean reproduction and failure audit | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Tester | T-0106 start trigger; T-0106/S02 |
| T-0106/S02 — [Systems] BOOM malformed-token and epoch negative matrix | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Systems Implementer | T-0106 start trigger; T-0106/S01 evidence carry-in |
| T-0106/S04 — [Systems] BOOM replay, source-reuse, and backpressure identity | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Systems Implementer | T-0106 start trigger; T-0106/S02; T-0106/S03 |
| T-0106/S07 — [Systems] BOOM load attribution and post-A rollback | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Systems Implementer | T-0106 start trigger; T-0106/S06 |
| T-0106/S06 — [Systems] Rocket same-token store parity | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Systems Implementer | T-0106 start trigger; T-0106/S04; T-0106/S05 |
| T-0044/EPIC — Matched CPU and Graph organization comparison | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Project Manager | T-0042/S10 |
| T-0044/S00 — [Librarian] Mechanism and IP-risk delta packet | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Librarian | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S05 — [Performance Reviewer] Statistics, fairness, and claim audit | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Performance Reviewer | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S03 — [Tester] Clean reproducibility pilot and confounder audit | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Tester | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S02 — [Measurement] Common record collector and runner | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Measurement Implementer | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S01 — [Performance Reviewer] Preregister matched-comparison contract | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Performance Reviewer | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S04 — [Systems] Execute matched Rocket, BOOM, and Graph comparison | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Systems Implementer | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| RFC-0004/EPIC — Custom RISC-V after FPGA evidence | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | Useful KV260 evidence and a specific residual problem |
| T-0100/S02 — [Systems] Linux strong-sandbox vertical slice | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Systems Implementer | T-0100/S01 |
| T-0100/S01 — [Security Reviewer] Native workspace threat model and backend choice | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Security Reviewer | Human evaluation of Native workspace |
| T-0044/S06 — [Researcher] Evidence synthesis and no-go or continue memo | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Researcher | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0044/S07 — [Project Manager] Gate decision and record reconciliation | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Project Manager | Re-refine against EXP-0010 and ADR-0048/ADR-0049; do not execute as written |
| T-0104/EPIC — Production CommandGraph incremental reuse | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | T-0042; T-0044 |
| T-0056/S01 — [Systems] FPGA Experience retrieval prototype | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Systems Implementer | T-0055/S01; explicit FPGA access approval |
| T-0059/S01 — [Experience] Reproducible small-Transformer Experience demo | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Experience Implementer | T-0058/S01 |
| T-0058/S01 — [Experience] Reuse-weighted optimization ROI model | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Experience Implementer | T-0044/S07 |
| T-0055/S01 — [Measurement] ANN and near-memory access profile | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Measurement Implementer | Stable Experience schemas |
| T-0121 — Render Garden programs as directed graphs | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Experience Implementer | T-0120 complete; existing validated Garden snapshot |
| T-0044/S13 — [Measurement] Bind and run EXP-0011 integrated physical matrix | [item](https://github.com/users/bhind/projects/1) | Blocked / P2 / Measurement Implementer | T-0044/S12 complete; HCI-02 authorized; common seven-macro Liberty/LEF views unavailable |
| T-0148 — Add versioned signed relative loads to the simulation Graph path | [item](https://github.com/bhind/raveil/issues/113) | In Progress / P0 / Chisel Implementer | T-0143 |
| T-0150 — Make Garden fusion changes visible at a glance | [item](https://github.com/bhind/raveil/issues/114) | Ready / P1 / Experience Implementer | T-0135; T-0144 completed |
| T-0151 — Reconcile daily Project delivery without owner reminders | [item](https://github.com/bhind/raveil/issues/115) | In Progress / P0 / Project Manager | T-0147 completed; independent of T-0148 |
| S-0003 — Review: Graph generality and visual fusion demo | [item](https://github.com/users/bhind/projects/1) | Backlog / unset / Project Manager | T-0148 accepted increment; T-0150 visual explanation; no automatic acceptance |
| T-0149 — Deliver the editable shell-first Raveil workspace | [item](https://github.com/bhind/raveil/issues/116) | Blocked / P0 / Experience Implementer | T-0148 candidate integration; T-0152 regression disposition |
| T-0152 — Reconcile the UIO no-device source-scan regression | [item](https://github.com/bhind/raveil/issues/117) | Backlog / P1 / Systems Implementer | T-0145; coordinate with T-0149 acceptance |
| T-0091 — After the GNU/Linux userspace graph MVP and owned v1 artifact lineage remain regression-clean, port the same bounded graph control loop to ReactOS as a non-auth | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Systems Implementer | P3 future planned; canonical TODO trigger; PM refinement before start |
| T-0063 — Reconsider GitHub-hosted CI/CD only when the project has multiple contributors and its owner has explicitly approved the cost and operating policy | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0068 — Install and verify the ADR-0010 root-owned powermetrics helper and helper-only `NOPASSWD` sudoers entry after the tracked implementation and tests pass | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Measurement Implementer | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0069 — Pilot RFC-0003 reference management with the nine existing research sources: verify exact versions, authorship, rights/access status, correction or retraction s | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Librarian | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0071 — Reduce immutable research-bundle remote object count and sync latency without weakening per-file SHA-256/size attestation, overwrite refusal, downloadable verif | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Measurement Implementer | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0073 — Extend pre-seal sensitive-data inspection beyond selected text suffixes, reject broader credential-key forms, validate external rclone config ownership/permissi | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Security Reviewer | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0018 — Add VirtIO block and evaluate a simple persistent filesystem such as FAT32; keep production-OS compatibility out of this gate | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Systems Implementer | P3 future planned; canonical TODO trigger; PM refinement before start |
| T-0025 — Preserve and analyze failed and boundary variants, not only winners | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0050 — Tail-preserving bounded coreset experiment | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0051 — Negative-transfer-aware retrieval and calibrated abstention | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0052 — Graph/hardware contrastive representation | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0053 — Multi-policy periodic review of stale local optima | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0054 — Cross-hardware transfer with a small target measurement budget | [item](https://github.com/users/bhind/projects/1) | Backlog / Icebox / Project Manager | P4 optional/triggered; canonical TODO trigger; PM refinement before start |
| T-0042 — 保留: unfinished broad research; preserve controlled-run evidence | [item](https://github.com/users/bhind/projects/1) | Backlog / P2 / Project Manager | Scope reconciliation; T-0106 restart trigger; T-0044 common-memory inputs |

## Branch inventory

Remote linked/merged PR identity is the review/integration locator. A branch with no active item is retained donor/provenance or an unclaimed candidate, never automatic execution authority. Stale branches are not deleted.

| Local branch | Tip | Corresponding PR or task disposition |
|---|---|---|
| `build/t-0042-boom-elaboration` | `06f3317` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `build/t-0042-boom-functional-smoke` | `107a28f` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `build/t-0042-pinned-boom-reference` | `fdf1f97` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `build/t-0092-demo-release` | `c88eda7` | No PR in captured inventory; retained/unclaimed; T-0092 |
| `build/t-0092-sonatine-demo-release` | `ac8dffa` | No PR in captured inventory; retained/unclaimed; T-0092 |
| `build/t-0105-chisel-riscv-substrate` | `ba89390` | No PR in captured inventory; retained/unclaimed; T-0105 |
| `build/t-0105-rocket-smoke` | `d6ab7d6` | No PR in captured inventory; retained/unclaimed; T-0105 |
| `build/t-0112-kv260-axi-export` | `5d53a8a` | No PR in captured inventory; retained/unclaimed; T-0112 |
| `chore/t-0044-integrate-mainline` | `95fff31` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `chore/t-0126-project-dispatch` | `d9ac17e` | [MERGED #30](https://github.com/bhind/raveil/pull/30) |
| `chore/t-0127-agent-queue-enforcement` | `a029720` | [MERGED #34](https://github.com/bhind/raveil/pull/34) |
| `chore/t-0130-project-hygiene` | `e34b3a8` | [MERGED #49](https://github.com/bhind/raveil/pull/49) |
| `chore/t-0151-daily-project-reconciliation` | `86ed048` | Existing separate dirty daily implementation; #115 remains unfinished |
| `docs/adr-0045-cpu-semantic-witness` | `3a1b56d` | No PR in captured inventory; retained/unclaimed; no task ID |
| `docs/adr-0046-t-0042-small-start` | `cb2d56b` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `docs/adr-0048-t0044-evidence-promotion` | `db407bf` | No PR in captured inventory; retained/unclaimed; no task ID |
| `docs/adr-0049-cgra-substrate-boundary` | `4690e95` | No PR in captured inventory; retained/unclaimed; no task ID |
| `docs/adr-0054-sim-first-reference-aware-mvp` | `a1602a8` | No PR in captured inventory; retained/unclaimed; no task ID |
| `docs/adr-0058-incident-free-pr-merge` | `ef0403f` | [MERGED #5](https://github.com/bhind/raveil/pull/5) |
| `docs/adr-0061-two-lane-sim-first` | `f461d0d` | [MERGED #18](https://github.com/bhind/raveil/pull/18) |
| `docs/rfc-0003-reference-management` | `9d069be` | No PR in captured inventory; retained/unclaimed; no task ID |
| `docs/t-0010-microkernel-first` | `f59959e` | No PR in captured inventory; retained/unclaimed; T-0010 |
| `docs/t-0044-s11-project-count` | `b002e3a` | [MERGED #14](https://github.com/bhind/raveil/pull/14) |
| `docs/t-0065-drive-status-clarification` | `1cecbce` | No PR in captured inventory; retained/unclaimed; T-0065 |
| `docs/t-0068-powermetrics-install-proof` | `e018d43` | No PR in captured inventory; retained/unclaimed; T-0068 |
| `docs/t-0069-x86-compatibility` | `e98b6e0` | No PR in captured inventory; retained/unclaimed; T-0069 |
| `docs/t-0079-linux-first-kernel` | `91d8e4b` | No PR in captured inventory; retained/unclaimed; T-0079 |
| `docs/t-0081-gnu-linux-oss-first` | `929721e` | No PR in captured inventory; retained/unclaimed; T-0081 |
| `docs/t-0083-persistent-u-shell` | `e655bdd` | No PR in captured inventory; retained/unclaimed; T-0083 |
| `docs/t-0087-delivery-line-reconciliation` | `b6f1af9` | No PR in captured inventory; retained/unclaimed; T-0087 |
| `docs/t-0088-failure-issue-governance` | `52b1f02` | No PR in captured inventory; retained/unclaimed; T-0088 |
| `docs/t-0091-reactos-portability` | `a786c5e` | No PR in captured inventory; retained/unclaimed; T-0091 |
| `docs/t-0092-sonatine-shell-demo-plan` | `c83e91f` | No PR in captured inventory; retained/unclaimed; T-0092 |
| `docs/t-0093-closeout` | `5b6bfea` | [MERGED #71](https://github.com/bhind/raveil/pull/71) |
| `docs/t-0093-graph-directory-view-plan` | `eb55a0e` | No PR in captured inventory; retained/unclaimed; T-0093 |
| `docs/t-0094-daphnis-software-mvp` | `18543cc` | No PR in captured inventory; retained/unclaimed; T-0094 |
| `docs/t-0099-native-cli-workspace` | `f45e358` | No PR in captured inventory; retained/unclaimed; T-0099 |
| `docs/t-0106-s01-sprint-closeout` | `289080d` | [MERGED #11](https://github.com/bhind/raveil/pull/11) |
| `docs/t-0106-software-graph-evaluation` | `3555f0d` | No PR in captured inventory; retained/unclaimed; T-0106 |
| `docs/t-0107-project-readme` | `4690e95` | No PR in captured inventory; retained/unclaimed; T-0107 |
| `docs/t-0108-project-readme` | `2569efe` | No PR in captured inventory; retained/unclaimed; T-0108 |
| `docs/t-0109-component-boundaries` | `e5264ff` | No PR in captured inventory; retained/unclaimed; T-0109 |
| `docs/t-0110-human-confirmation-incidents` | `648eea4` | No PR in captured inventory; retained/unclaimed; T-0110 |
| `docs/t-0111-chisel-mainline` | `aa7253d` | No PR in captured inventory; retained/unclaimed; T-0111 |
| `docs/t-0112-kv260-physical-slice` | `21c2432` | No PR in captured inventory; retained/unclaimed; T-0112 |
| `docs/t-0116-pr-only-main` | `7eb3e56` | [MERGED #4](https://github.com/bhind/raveil/pull/4) |
| `docs/t-0116-weekly-sprint-governance` | `2a03c92` | No PR in captured inventory; retained/unclaimed; T-0116 |
| `docs/t-0118-ai-capacity-model` | `3f8bb90` | [MERGED #8](https://github.com/bhind/raveil/pull/8) |
| `docs/t-0119-weekly-usage-guard` | `8430c6b` | [MERGED #10](https://github.com/bhind/raveil/pull/10) |
| `docs/t-0125-playable-closeout` | `cd5aa04` | [MERGED #33](https://github.com/bhind/raveil/pull/33) |
| `docs/t-0127-agent-queue-closeout` | `e0d1d72` | [MERGED #35](https://github.com/bhind/raveil/pull/35) |
| `docs/t-0128-s01-closeout` | `6f95e48` | [MERGED #38](https://github.com/bhind/raveil/pull/38) |
| `docs/t-0128-s02-closeout` | `2d72464` | [MERGED #41](https://github.com/bhind/raveil/pull/41) |
| `docs/t-0128-s03-closeout` | `9202c42` | [MERGED #44](https://github.com/bhind/raveil/pull/44) |
| `docs/t-0129-closeout` | `da301db` | [MERGED #47](https://github.com/bhind/raveil/pull/47) |
| `docs/t-0130-final-record-fix` | `9f6c3d3` | [MERGED #51](https://github.com/bhind/raveil/pull/51) |
| `docs/t-0130-project-hygiene-closeout` | `5655e9c` | [MERGED #50](https://github.com/bhind/raveil/pull/50) |
| `docs/t-0131-closeout` | `2cf5413` | No PR in captured inventory; retained/unclaimed; T-0131 |
| `docs/t-0131-sprint-operator-closeout` | `e2536bb` | [MERGED #54](https://github.com/bhind/raveil/pull/54) |
| `docs/t-0132-s02-closeout` | `ee419f6` | [MERGED #77](https://github.com/bhind/raveil/pull/77) |
| `docs/t-0132-s03-closeout` | `70fa617` | [MERGED #80](https://github.com/bhind/raveil/pull/80) |
| `docs/t-0132-s07-closeout` | `49c9b0c` | [MERGED #84](https://github.com/bhind/raveil/pull/84) |
| `docs/t-0133-saturday-review-closeout` | `3d98957` | [MERGED #58](https://github.com/bhind/raveil/pull/58) |
| `docs/t-0133-saturday-sprint-review` | `ec04b4a` | [MERGED #57](https://github.com/bhind/raveil/pull/57) |
| `docs/t-0135-closeout` | `98b3c69` | [MERGED #68](https://github.com/bhind/raveil/pull/68) |
| `docs/t-0136-immediate-post-review-pull` | `795732a` | [MERGED #66](https://github.com/bhind/raveil/pull/66) |
| `docs/t-0137-closeout` | `4dfc875` | [MERGED #74](https://github.com/bhind/raveil/pull/74) |
| `docs/t-0144-closeout` | `e3dcbf6` | [MERGED #105](https://github.com/bhind/raveil/pull/105) |
| `docs/t-0147-postmerge-closeout` | `959fd7e` | [MERGED #112](https://github.com/bhind/raveil/pull/112) |
| `docs/t-0151-project-inventory` | `82b196c` | This isolated PM inventory receipt; #115 remains unfinished |
| `feat/t-0010-platform-contract` | `5b900b6` | No PR in captured inventory; retained/unclaimed; T-0010 |
| `feat/t-0010-rv64-platform-contract` | `623e9d4` | No PR in captured inventory; retained/unclaimed; T-0010 |
| `feat/t-0011-sv39-address-spaces` | `f6c7ddd` | No PR in captured inventory; retained/unclaimed; T-0011 |
| `feat/t-0012-user-mode-init` | `0560f1d` | No PR in captured inventory; retained/unclaimed; T-0012 |
| `feat/t-0013-context-switch` | `db696b6` | No PR in captured inventory; retained/unclaimed; T-0013 |
| `feat/t-0014-timer-preemption` | `f592dd5` | No PR in captured inventory; retained/unclaimed; T-0014 |
| `feat/t-0015-blocking-ipc` | `13f6dde` | No PR in captured inventory; retained/unclaimed; T-0015 |
| `feat/t-0017-vfs-ramfs` | `6660076` | No PR in captured inventory; retained/unclaimed; T-0017 |
| `feat/t-0022-policy-comparison` | `51ef48c` | No PR in captured inventory; retained/unclaimed; T-0022 |
| `feat/t-0030-job-completion-contracts` | `1b24cbf` | No PR in captured inventory; retained/unclaimed; T-0030 |
| `feat/t-0031-sonatine-job-rings` | `dc08148` | No PR in captured inventory; retained/unclaimed; T-0031 |
| `feat/t-0032-completion-telemetry` | `2bf5656` | No PR in captured inventory; retained/unclaimed; T-0032 |
| `feat/t-0033-shadow-commit-rollback` | `f121995` | No PR in captured inventory; retained/unclaimed; T-0033 |
| `feat/t-0034-four-plane-authority-enforcement` | `312a2e4` | No PR in captured inventory; retained/unclaimed; T-0034 |
| `feat/t-0034-four-plane-write-authority` | `f121995` | No PR in captured inventory; retained/unclaimed; T-0034 |
| `feat/t-0040-pinned-mlir-import` | `e84aedb` | No PR in captured inventory; retained/unclaimed; T-0040 |
| `feat/t-0041-owned-graph-contracts` | `93c675b` | No PR in captured inventory; retained/unclaimed; T-0041 |
| `feat/t-0042-boom-serialize-dispatch` | `90799d0` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-boom-token-handoff` | `7521d20` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-common-resource-integration` | `528fbe2` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-common-scratchpad-prototype` | `81fa791` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-common-sim-adapter` | `56753ea` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-cpu-memory-adapter` | `d11c002` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-graph-memory-adapter` | `1f53fe2` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-owned-mapper-adapter` | `e84aedb` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-owned-memory-interface` | `f838e81` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-riscv-stencil-adapter` | `0bd311b` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-rocket-stencil-functional` | `a237052` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-small-start` | `0f4be3b` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-static-graph-rtl` | `797c48f` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-tl-owned-contract-bridge` | `d86a3c9` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0042-tlram-latency-observer` | `a560aad` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `feat/t-0043-miroirs-pavane-seed` | `93c675b` | No PR in captured inventory; retained/unclaimed; T-0043 |
| `feat/t-0043-miroirs-pavane-semantic-oracle` | `894ecf8` | No PR in captured inventory; retained/unclaimed; T-0043 |
| `feat/t-0044-g1a-graph-memory-client` | `5de53c9` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `feat/t-0044-g1b-common-owned-memory-top` | `5775ff5` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `feat/t-0044-g1c-common-lifecycle-controller` | `5775ff5` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `feat/t-0044-integrated-physical-top` | `78a6dca` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `feat/t-0044-s08-integrated-top` | `af8d279` | [MERGED #9](https://github.com/bhind/raveil/pull/9) |
| `feat/t-0044-s10-contract-readiness` | `0f4c5b1` | [MERGED #12](https://github.com/bhind/raveil/pull/12) |
| `feat/t-0068-powermetrics-helper` | `f75802d` | [MERGED #2](https://github.com/bhind/raveil/pull/2) |
| `feat/t-0074-hierarchical-bootstrap` | `f24f01e` | No PR in captured inventory; retained/unclaimed; T-0074 |
| `feat/t-0076-evidence-mvp` | `c795391` | No PR in captured inventory; retained/unclaimed; T-0076 |
| `feat/t-0077-online-slate-executor` | `ebf490d` | No PR in captured inventory; retained/unclaimed; T-0077 |
| `feat/t-0079-tvm-meta-schedule` | `fdd49b2` | No PR in captured inventory; retained/unclaimed; T-0079 |
| `feat/t-0083-persistent-u-shell` | `fb369f0` | No PR in captured inventory; retained/unclaimed; T-0083 |
| `feat/t-0084-linux-driver-harness` | `cd809dd` | No PR in captured inventory; retained/unclaimed; T-0084 |
| `feat/t-0085-byte-shadow-publication` | `d016905` | No PR in captured inventory; retained/unclaimed; T-0085 |
| `feat/t-0086-linux-graph-mvp` | `d39d0d1` | No PR in captured inventory; retained/unclaimed; T-0086 |
| `feat/t-0086-linux-graph-mvp-port` | `6d2ba13` | No PR in captured inventory; retained/unclaimed; T-0086 |
| `feat/t-0089-u-mode-command-shell` | `bce3fe6` | No PR in captured inventory; retained/unclaimed; T-0089 |
| `feat/t-0090-sonatine-graph-backend` | `4ad6eb2` | No PR in captured inventory; retained/unclaimed; T-0090 |
| `feat/t-0092-sonatine-demo-runner` | `3582f73` | No PR in captured inventory; retained/unclaimed; T-0092 |
| `feat/t-0092-sonatine-shell-demo` | `dabea20` | No PR in captured inventory; retained/unclaimed; T-0092 |
| `feat/t-0093-graph-directory-snapshot` | `64ca94b` | [MERGED #70](https://github.com/bhind/raveil/pull/70) |
| `feat/t-0094-daphnis-software-mvp` | `844b508` | No PR in captured inventory; retained/unclaimed; T-0094 |
| `feat/t-0098-native-interactive-cli` | `14cdb1c` | No PR in captured inventory; retained/unclaimed; T-0098 |
| `feat/t-0099-native-cli-workspace` | `3cfb13c` | No PR in captured inventory; retained/unclaimed; T-0099 |
| `feat/t-0101-command-graph-native-demo` | `5321d18` | No PR in captured inventory; retained/unclaimed; T-0101 |
| `feat/t-0102-native-shell-completion` | `abd4fd7` | No PR in captured inventory; retained/unclaimed; T-0102 |
| `feat/t-0103-command-graph-showcase` | `2faa648` | No PR in captured inventory; retained/unclaimed; T-0103 |
| `feat/t-0106-project-workspace` | `7c38a36` | Dirty historical donor; unrelated T-0042 and agent edits plus untracked project.py preserved |
| `feat/t-0112-kv260-m1-identity` | `ba30b42` | No PR in captured inventory; retained/unclaimed; T-0112 |
| `feat/t-0112-kv260-m1-integration` | `743d0bb` | No PR in captured inventory; retained/unclaimed; T-0112 |
| `feat/t-0112-kv260-relative-aperture` | `73cbd7c` | No PR in captured inventory; retained/unclaimed; T-0112 |
| `feat/t-0113-sim-first-mvp` | `c30c44e` | No PR in captured inventory; retained/unclaimed; T-0113 |
| `feat/t-0114-affine-install-abi` | `3b9dba5` | No PR in captured inventory; retained/unclaimed; T-0114 |
| `feat/t-0114-generated-schedule` | `f785e71` | No PR in captured inventory; retained/unclaimed; T-0114 |
| `feat/t-0114-multi-dag-executor` | `21275e3` | No PR in captured inventory; retained/unclaimed; T-0114 |
| `feat/t-0115-tiny-graph-simulation-mvp` | `0216a0d` | No PR in captured inventory; retained/unclaimed; T-0115 |
| `feat/t-0117-garden-read-only-browser` | `9da4b76` | [MERGED #6](https://github.com/bhind/raveil/pull/6) |
| `feat/t-0120-garden-multipane-workspace` | `1dee19d` | [MERGED #16](https://github.com/bhind/raveil/pull/16) |
| `feat/t-0121-garden-graph-canvas` | `d59bbc7` | No PR in captured inventory; retained/unclaimed; T-0121 |
| `feat/t-0122-graph-device-mvp` | `2b86e0c` | [MERGED #20](https://github.com/bhind/raveil/pull/20) |
| `feat/t-0123-bounded-affine` | `f48bd46` | [MERGED #25](https://github.com/bhind/raveil/pull/25) |
| `feat/t-0123-bounded-generality` | `999a283` | [MERGED #24](https://github.com/bhind/raveil/pull/24) |
| `feat/t-0123-multi-dag` | `dcbd1d7` | [MERGED #26](https://github.com/bhind/raveil/pull/26) |
| `feat/t-0125-graph-device-playable-implementation` | `8e6182b` | [MERGED #31](https://github.com/bhind/raveil/pull/31) |
| `feat/t-0128-s01-operator-admission` | `a6d27eb` | [MERGED #37](https://github.com/bhind/raveil/pull/37) |
| `feat/t-0128-s02-selected-rtl-execution` | `82dd302` | [MERGED #40](https://github.com/bhind/raveil/pull/40) |
| `feat/t-0128-s03-top-level-rtl-cli` | `2e91372` | [MERGED #43](https://github.com/bhind/raveil/pull/43) |
| `feat/t-0129-verified-rtl-trace-demo` | `c6a3422` | [MERGED #46](https://github.com/bhind/raveil/pull/46) |
| `feat/t-0131-sprint-operator-skill` | `bcb6bbf` | [MERGED #53](https://github.com/bhind/raveil/pull/53) |
| `feat/t-0132-s01-axi4lite-control` | `ed7f2e2` | [MERGED #64](https://github.com/bhind/raveil/pull/64) |
| `feat/t-0132-s02-axi-install` | `23538c9` | [MERGED #76](https://github.com/bhind/raveil/pull/76) |
| `feat/t-0132-s03-axi-execution` | `6cf910e` | [MERGED #79](https://github.com/bhind/raveil/pull/79) |
| `feat/t-0132-s04-axi-selected` | `0b248ed` | No PR in captured inventory; retained/unclaimed; T-0132 |
| `feat/t-0132-s05-axi-request` | `2e470b8` | No PR in captured inventory; retained/unclaimed; T-0132 |
| `feat/t-0132-s06-linux-uio-transport` | `2f58aff` | No PR in captured inventory; retained/unclaimed; T-0132 |
| `feat/t-0132-s07-rtl-export` | `a6e7fa2` | [MERGED #82](https://github.com/bhind/raveil/pull/82) |
| `feat/t-0132-s08-dynamic-admission` | `32fc1d1` | [MERGED #86](https://github.com/bhind/raveil/pull/86) |
| `feat/t-0132-s09-runtime-sim-demo` | `d65c480` | [MERGED #88](https://github.com/bhind/raveil/pull/88) |
| `feat/t-0132-s10-runtime-pair-cli` | `d70fe7d` | [MERGED #90](https://github.com/bhind/raveil/pull/90) |
| `feat/t-0135-garden-fusion-explanation` | `11745c6` | [MERGED #67](https://github.com/bhind/raveil/pull/67) |
| `feat/t-0139-kv260-readiness-preflight` | `76ee64a` | [MERGED #94](https://github.com/bhind/raveil/pull/94) |
| `feat/t-0140-dynamic-program-sim` | `5b73f49` | [MERGED #96](https://github.com/bhind/raveil/pull/96) |
| `feat/t-0141-single-dynamic-graph` | `038c45c` | [MERGED #98](https://github.com/bhind/raveil/pull/98) |
| `feat/t-0142-sealed-dynamic-request` | `fe7bea7` | [MERGED #100](https://github.com/bhind/raveil/pull/100) |
| `feat/t-0143-max-u32` | `a7315a0` | [MERGED #102](https://github.com/bhind/raveil/pull/102) |
| `feat/t-0144-garden-execution-explanation` | `b31b0fa` | [MERGED #104](https://github.com/bhind/raveil/pull/104) |
| `feat/t-0145-sealed-dynamic-uio-handoff` | `4acebac` | [MERGED #109](https://github.com/bhind/raveil/pull/109) |
| `feat/t-0148-project-dynamic-graph` | `31262f1` | No PR in captured inventory; retained/unclaimed; T-0148 |
| `feat/t-0148-relative-load-v3` | `bf81269` | [Draft PR #118](https://github.com/bhind/raveil/pull/118); existing candidate, exact evidence review next |
| `feat/t-0149-project-workspace` | `31262f1` | [Draft PR #119](https://github.com/bhind/raveil/pull/119); blocked dependency and record/regression disposition |
| `fix/t-0016-fault-boundaries` | `2940742` | No PR in captured inventory; retained/unclaimed; T-0016 |
| `fix/t-0021-powermetrics-privilege` | `70522ef` | No PR in captured inventory; retained/unclaimed; T-0021 |
| `fix/t-0022-bounded-limit` | `874c84a` | No PR in captured inventory; retained/unclaimed; T-0022 |
| `fix/t-0022-policy-outcome-integrity` | `5599838` | No PR in captured inventory; retained/unclaimed; T-0022 |
| `fix/t-0042-estimate-discipline` | `ae606de` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `fix/t-0072-bundle-write-boundary` | `8695ff7` | No PR in captured inventory; retained/unclaimed; T-0072 |
| `fix/t-0073-fixed-sync-snapshot` | `fdd49b2` | No PR in captured inventory; retained/unclaimed; T-0073 |
| `fix/t-0075-powermetrics-readiness-recurrence` | `b0d76cb` | No PR in captured inventory; retained/unclaimed; T-0075 |
| `fix/t-0075-powermetrics-readiness-test` | `5aef588` | No PR in captured inventory; retained/unclaimed; T-0075 |
| `fix/t-0078-powermetrics-test-timing` | `0151b94` | No PR in captured inventory; retained/unclaimed; T-0078 |
| `fix/t-0096-sonatine-interactive-exit` | `a6f6f84` | No PR in captured inventory; retained/unclaimed; T-0096 |
| `fix/t-0097-agent-names-local-only` | `8298fbc` | No PR in captured inventory; retained/unclaimed; T-0097 |
| `fix/t-0116-populate-product-backlog` | `2d1af89` | No PR in captured inventory; retained/unclaimed; T-0116 |
| `fix/t-0116-sprint-governance-integration` | `8ac41af` | No PR in captured inventory; retained/unclaimed; T-0116 |
| `fix/t-0124-immutable-simulator-image` | `13628e9` | [MERGED #21](https://github.com/bhind/raveil/pull/21) |
| `fix/t-0137-sprint-review-boundary` | `74b1f27` | [MERGED #73](https://github.com/bhind/raveil/pull/73) |
| `fix/t-0146-p0-auto-replenishment` | `3a6f29c` | [MERGED #108](https://github.com/bhind/raveil/pull/108) |
| `fix/t-0147-atomic-project-closeout` | `249ac9d` | [MERGED #111](https://github.com/bhind/raveil/pull/111) |
| `main` | `18543cc` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0003-gate1-measurement` | `e7b89ee` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0003-history-evidence` | `dde3106` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0003-powermetrics-pilot` | `8daaf7c` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0003-target-result` | `e99e6e5` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0004-simulator-first` | `ffb38d4` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0008-static-full-campaign` | `7eba963` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0009-static-physical-proxy` | `6b159bd` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0010-common-timing-screen` | `e975d90` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/exp-0011-integrated-physical` | `8d84787` | [MERGED #17](https://github.com/bhind/raveil/pull/17) |
| `research/exp-0012-runtime-matched-logic-diagnostic` | `f335f21` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/rfc-0004-boundary-aware-experience` | `594d582` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/rfc-0006-static-generalization-ladder` | `273712c` | No PR in captured inventory; retained/unclaimed; no task ID |
| `research/t-0042-debug-sba-path` | `757ad23` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `research/t-0042-loader-debug-path` | `e98339c` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `research/t-0042-rocket-lifecycle-observer` | `94e8071` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `research/t-0042-semantic-initiator-boundary` | `8b6d1c3` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `research/t-0042-semantic-witness` | `064995e` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `research/t-0044-common-memory-closure` | `9fa38e9` | [MERGED #23](https://github.com/bhind/raveil/pull/23) |
| `research/t-0044-common-stdcell-memory` | `311824f` | [MERGED #22](https://github.com/bhind/raveil/pull/22) |
| `research/t-0044-exp-0008-evidence-promotion` | `8d31936` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-exp-0011-measurement-contract` | `2c04a11` | [MERGED #15](https://github.com/bhind/raveil/pull/15) |
| `research/t-0044-exp-0011-prefreeze` | `4227183` | [MERGED #13](https://github.com/bhind/raveil/pull/13) |
| `research/t-0044-integrated-logic-diagnostic` | `199ea38` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-integrated-timing-memory-boundary` | `f335f21` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-repeated-invocation-boundary` | `1812a67` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-s14-memory-strategy-inventory` | `ad59739` | [MERGED #19](https://github.com/bhind/raveil/pull/19) |
| `research/t-0044-specialized-integrated-mvp` | `0c96236` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-staging-initiator-boundary` | `a92b27b` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0044-static-pilot` | `493c186` | No PR in captured inventory; retained/unclaimed; T-0044 |
| `research/t-0052-experience-prior-art` | `b6ffb9a` | No PR in captured inventory; retained/unclaimed; T-0052 |
| `research/t-0052-prior-art-review` | `152979d` | [MERGED #1](https://github.com/bhind/raveil/pull/1) |
| `research/t-0057-native-graph-simulation` | `3446508` | No PR in captured inventory; retained/unclaimed; T-0057 |
| `research/t-0057-prior-art-matrix` | `8a93700` | No PR in captured inventory; retained/unclaimed; T-0057 |
| `research/t-0057b-native-graph-contract` | `c5de820` | No PR in captured inventory; retained/unclaimed; T-0057 |
| `research/t-0080-gate1-completion` | `8e2f93c` | No PR in captured inventory; retained/unclaimed; T-0080 |
| `research/t-0138-kv260-transition` | `3e627e4` | [MERGED #92](https://github.com/bhind/raveil/pull/92) |
| `test/t-0042-boom-load-lifecycle` | `725f47e` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-misaligned-rollback` | `d5889ac` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-owned-memory-smoke` | `85a9ea3` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-postrequest-redirect` | `00368f1` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-store-authorization` | `377a927` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-token-default-invalid` | `7c38a36` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-boom-token-stripped-after-valid` | `7c38a36` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-cpu-source-attribution` | `9c83583` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-dcache-origin-audit` | `0b58cdf` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-origin-sideband-negative` | `4b07523` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-owned-tl-protocol` | `205dedc` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-rocket-owned-memory-smoke` | `69d0ef1` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-rocket-postrequest-exception` | `69df120` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-rocket-postrequest-redirect-negative` | `e3a0158` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-rocket-redirect-dcache-fate` | `ba6bd82` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-rocket-request-retire-witness` | `a89f7b7` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0042-s01-boom-token-stripped-after-valid` | `9e94b0e` | No PR in captured inventory; retained/unclaimed; T-0042 |
| `test/t-0083-fast-development-loop` | `5437375` | No PR in captured inventory; retained/unclaimed; T-0083 |
| `test/t-0106-s01-boom-stripped-token-carry-in` | `fde054d` | [MERGED #3](https://github.com/bhind/raveil/pull/3) |
| `test/t-0117-garden-terminal-acceptance` | `2f8281f` | [MERGED #7](https://github.com/bhind/raveil/pull/7) |

## Exact checks and pending synchronization

- `gh project item-list 1 --owner bhind --limit 1000 --format json`, field-list with limit 100, repository Project discovery, all Issue/PR lists and paginated remote branches: successful initial inventory. Bounded counts do not hit the selected limits.
- `python3 scripts/project_queue.py audit`: passed before repair, two active delivery items, zero pullable Ready; this alone does not inspect historical Done evidence or enforce all TODO coverage.
- `python3 -m unittest tests.test_graph_device_uio_dry_run`: exit 1, three tests/one failure, canonical 82b196c, macOS arm64/Python 3.14.6. The blanket source ban rejects a descriptor-safe repository-directory open; whether its replacement proves the boundary is T-0152 acceptance, not an inventory conclusion.
- `project_queue.py review 113 --pr 118`: dry-run passed. First `--apply` failed during its fresh Project read with GraphQL API quota exhaustion, before status mutation. At 2026-09-05 the GraphQL endpoint reported 83/5000 remaining and reset 06:53:54 UTC. REST rate_limit gave inconsistent 5000 remaining and is not used to bypass the GraphQL failure.
- Pending at that failed boundary: canonical Review transition for #113; candidate linkage/allowlist/verified-baseline additions to #113/#116/#117; final readback and README inventory summary. Retry after GraphQL budget recovery using current state, not a stale overwrite. Git push and Draft PR #119 creation nevertheless succeeded and are recorded separately.
- No permissions are missing. The temporary blocker is API quota; preserve unpublished changes and do not represent them as applied.

## Next consumption

PM reviews the already-published predecessor #118, dispositions the independently reproduced #117 regression and reconciles #119 candidate records, then delivers the editable T-0149 workspace through main. Keep one primary implementation. #115 daily scheduler proceeds only in its separate operations scope; conditional research stays deferred.

## Read-boundary correction and recovered operations

The small explicit-field Project read succeeded despite the stock CLI read
failing on quota. PM registered a bounded queue-read correction in #115 before
editing. The same canonical ProjectQueue now reads cursor-paginated items and
normalizes only queue fields, refusing partial or changing counts, duplicate
identities/cursors/fields and API errors. It preserves all lifecycle guards.
The first real read rejected GitHub's repeated built-in Title field; an
identical content/field title is now allowed and a mismatch still fails closed.
Forty-seven queue tests pass; live audit --check-branch passes with two active
items and one pullable Ready. No new task started from that Ready card.

Issue #113/#116/#117 candidate-linkage, allowlist and verified-baseline additions
were successfully applied using small requests within the remaining quota.
The initially failed operations above remain provenance, not current failure
claims. The final status transition/readback is recorded below.

The targeted Done evidence review additionally resolves T-0116's locator to
canonical commit 8ac41af, which its Review Outcome records. T-0044/S09 is
explicitly absorbed into S08 at zero Current SP under STATUS and SPRINTS; its
original three Initial SP remain. It is an absorbed evidence outcome, not a
second executed test or an independently earned delivery. No evidence-free
new Done was found or awarded. Remaining historical receipt checks are listed
as verification limits, not proof that past acceptances were false.

## Final verified readback — 2026-09-05 06:45 UTC / 15:45 JST

Canonical queue `audit --check-branch` passes. The explicit reader returns all
97 visible items and 38 work-item Issues. No unfinished T-ID in this branch's
TODO is missing from the Project. Visible counts: Done 52, Backlog 40,
Blocked 2, Review 1, Ready 1, In Progress 1. Counts are a dated observation;
independent concurrent work may change them after this receipt.

| Item | Verified state | Concrete next action |
|---|---|---|
| [T-0148 / #113](https://github.com/bhind/raveil/issues/113) | Review / P0, successfully moved by the unchanged canonical review transition | Exact-head [PR #118](https://github.com/bhind/raveil/pull/118) evidence and record verification |
| [T-0149 / #116](https://github.com/bhind/raveil/issues/116) | Blocked / P0 | Resolve predecessor integration, #117 regression disposition and candidate record corrections in [PR #119](https://github.com/bhind/raveil/pull/119) |
| [T-0150 / #114](https://github.com/bhind/raveil/issues/114) | Ready / P1, refined by the concurrent daily session | Remain the prepared Garden follow-up behind the primary workspace |
| [T-0151 / #115](https://github.com/bhind/raveil/issues/115) | In Progress / P0 | Integrate this bounded inventory correction; finish and verify the separate daily scheduler before parent Done |
| [T-0152 / #117](https://github.com/bhind/raveil/issues/117) | Backlog / P1 | Correct the independently reproduced no-device boundary regression with a meaningful acceptance test |

The initially failed status and Issue-linkage operations have now succeeded;
there is no remaining unapplied Project status write from this inventory.
The API failure/retry history remains above. T-0044/S13 is still Blocked by
missing reviewed common-memory Liberty/LEF inputs; Measurement/PM own the
pre-data release condition. T-0042 broad research stays deferred with the
explicit narrowed-scope discrepancy; no workspace outcome resolves it.

Independent Tester initially rejected malformed schema IDs/options that could
pass preflight. The corrected reader validates all field/option identities and
unique names before edits, with a start() negative asserting zero mutations.
Final focused verification: 47 queue + 4 agent tests, exit 0; record checker
and diff check pass. Independent clean-environment run of the same 51 tests
passes, log SHA-256
`26ba8d1468e62ebe1cf2a29144335017b4cb98edcb8465e3e8cba53b6dcb946f`.
Host: macOS 26.5.1 arm64, Python 3.14.6. Final weekly usage reading: 10080
minutes, 65% used / 35% remaining. Evidence is Host Functional only.

## Integration and post-merge synchronization

[PR #121](https://github.com/bhind/raveil/pull/121) integrated this PM inventory
and required session-sync/read-boundary correction as canonical
`75bf2757016debdfc8aa2fabcfffa5b584277ce5`. Exact candidate `01a427c` passed
independent review; canonical code/governance blobs match the tested candidate.
At this pre-#120 snapshot the broad T-0151 daily scheduler remained unfinished in
[PR #120](https://github.com/bhind/raveil/pull/120). Preserve both record sets
during its later integration; this inventory does not accept that scheduler.

The first post-merge #115-body receipt read failed because the GraphQL quota
was already exhausted. No update was represented as successful. Pending delta:
merged #121/main hash and the remaining #120 boundary. Permission is sufficient;
retry follows the reported 15:53:54 JST reset. This is distinct from the
already-successful T-0148 Review synchronization.

Post-reset reconciliation succeeded: GitHub reported 4928 remaining, the fresh
#115 integration receipt and #116 published-candidate/70-test receipt were
applied, and canonical `audit --check-branch` passed. The post-merge pending
body update above is resolved. Remaining blockers are product/research
acceptance conditions, not missing GitHub permission or an unapplied inventory
write. At that snapshot parent T-0151 still required its separate daily scheduler acceptance; the subsequent #120 integration is reconciled below.

## Subsequent concurrent daily closeout

PR #120 then merged at `9e3a405`. Its code and both histories were retained when
resolving the #122 record conflict. The inventory PM independently verified
the canonical daily-script hash against the successful 32-update live receipt,
the actual LaunchAgent configuration/last exit 0, and its successful no-repeat
15:55:15 JST receipt. All 68 combined daily/queue/agent tests pass. Current
main's T-0151 completion is therefore retained on inspected evidence; the
earlier unfinished-parent descriptions above are dated pre-#120 observations.
The canonical queue audit now passes with one active review item and one
pullable Ready. No extra primary implementation was started.

The legacy #99/PR #100 native closing-reference association is still absent
from GitHub's API even after normalizing the PR's 18 literal newline escapes
and preserving its existing closing reference. This remaining metadata gap is
explicit; canonical T-0142/PR #100 evidence is linked and no historical event
is synthesized. Broad T-0042 scope reconciliation and T-0149 predecessor/
regression acceptance remain separate, unfinished work.
