# Raveil project records

## Completed common-source execution path — local T-0236

Use [the common array guide](guides/ARRAY_PROGRAM.md) and
[completion/replay checklist](guides/GENERALIZATION_COMPLETION.md). The same source
now passes actual QEMU/RTL through automatic partitioning, failure/retry and saved
inspection. [STATUS](STATUS.md) and [October12 log](log/2026-10-12.md) separate
functional facts from publication state and future product work.

## Automatically partitioned array programs — local T-0235

Phase-one scope and all implementation decisions are fixed in
[ADR-0132](decisions/ADR-0132-materialized-array-program.md).
The [common-input guide](guides/ARRAY_PROGRAM.md) describes the editable source,
automatic materialization, CLI and failure/capture boundaries. See [status](STATUS.md)
for verified UT completion and [TODO](../TODO.md) for the separate next integration
phase. This is local work under ADR-0107; public adoption remains separate.

## Shared signed transform proposal

T-0234 proposes v5 sharing under unchanged numerical/backend limits. See
[ADR-0131](decisions/ADR-0131-versioned-shared-signed-transforms.md), [status](STATUS.md)
and [the prepared local usage](guides/PROJECT_WORKSPACE.md#proposed-shared-signed-transforms).
Host and actual v5 execution verification are complete after owner-directed
continuation. See `artifacts/research/T-0234/resumed-01/`; public adoption is separate.

## Generated signed interaction checks

T-0229 continues with optional signed32 generated workloads on the existing backend.
See [status](STATUS.md), [the generated-check command](guides/PROJECT_WORKSPACE.md#generated-signed-coordinate-checks)
and the local `artifacts/research/T-0229/generated-01/` packet.

## Signed ordering continuation — T-0229 resumed

[Status](STATUS.md), [numeric contract](decisions/ADR-0130-source-signed-ordering-legalization.md),
[workspace guide](guides/PROJECT_WORKSPACE.md#explicit-signed-ordering-local-t-0229)
and [evidence log](log/2026-10-11.md) cover the explicitly approved local continuation.
Former validation hold is resolved; public adoption remains separate.

## Fresh coupled verification — T-0233

[Status](STATUS.md), [remaining adoption](../TODO.md) and
[October11 commands/evidence](log/2026-10-11.md) record eight new existing-unsigned
flows through QEMU/RTL, including failure, fresh retry and tile-plan equivalence.
See [EXP-0002](experiments/EXP-0002-sonatine-rv64-reproducibility.md) for reused
runtime identity and the functional evidence boundary.

## Local cumulative reproduction — T-0232

[Status](STATUS.md), [verification commands](log/2026-10-11.md) and
[remaining adoption](../TODO.md) record291 host tests from a clean canonical archive
plus the T-0231 patch, and recursive verification of36 saved grid/flow parent paths.
Production source and architecture are unchanged; held T-0229 is excluded.

## Local strict proof-reader correction — T-0231

[Status](STATUS.md), [remaining adoption](../TODO.md),
[workspace guide](guides/PROJECT_WORKSPACE.md#strict-saved-proof-readers-local-t-0231)
and [October11 evidence](log/2026-10-11.md) cover host-only corrections and129 retained
proof rereads. This follows T-0230 without incorporating held T-0229 semantics.

## Local rejection-path correction

T-0230 repairs malformed-source and impossible saved-count diagnostics in the
existing MF01 path. See [status](STATUS.md), [remaining adoption](../TODO.md) and
[the October11 evidence log](log/2026-10-11.md). Its T-0228 base is independent of
the separately held T-0229 numerical proposal.

## Latest local candidate: whole-flow partition advice — T-0228

[Current state](STATUS.md), [advice contract](decisions/ADR-0129-separable-flow-partition-advice.md)
and [workspace planning](guides/PROJECT_WORKSPACE.md#flow-partition-advice-local-t-0228)
cover link-preserving finite planning through existing admission.

## Latest local candidate: dependent grid-source flows — T-0227

[Current state](STATUS.md), [flow contract](decisions/ADR-0128-dependent-grid-source-flows.md)
and [workspace commands](guides/PROJECT_WORKSPACE.md#dependent-grid-source-flows-local-t-0227)
describe source-level composition through existing grid execution.

## Latest local validation: generated coordinate combinations — T-0226

[Current state](STATUS.md) and [replay commands](guides/PROJECT_WORKSPACE.md#generated-coordinate-checks-local-t-0226)
cover generated formula comparisons and selected coupled execution.

## Latest local candidate: fold then pointwise map — T-0225

[Current state](STATUS.md), [source contract](decisions/ADR-0127-post-reduction-map-source.md)
and [workspace guide](guides/PROJECT_WORKSPACE.md#post-reduction-maps-local-t-0225)
describe v3 composition through existing DAG jobs. Public adoption remains separate.

## Latest local candidate: admitted uniform tiles — T-0224

[Current state](STATUS.md), [selection contract](decisions/ADR-0126-admitted-uniform-tile-advice.md)
and [workspace planning](guides/PROJECT_WORKSPACE.md#admitted-tile-planning-local-t-0224)
cover finite tile advice over the existing compiler. Public adoption remains separate.

## Latest local verification: cumulative reproduction — T-0223

[Current state](STATUS.md) and [native evidence](experiments/EXP-0002-sonatine-rv64-reproducibility.md)
record clean-archive cumulative-patch verification. Functional contracts remain
the T-0222/T-0221 proposals; canonical/public adoption is separate.

## Latest local candidate: affine grid coordinates — T-0222

[State](STATUS.md) and [coordinate contract](decisions/ADR-0125-affine-grid-coordinate-maps.md)
cover explicit output shapes and independently shaped affine inputs over the
existing MF01 executor. This is a local candidate, with public adoption separate.

## Latest local candidate: source-preserving MF01 grids — T-0221

[Current state](STATUS.md), [source contract](decisions/ADR-0124-source-preserving-mf01-grids.md)
and [workspace workflow](guides/PROJECT_WORKSPACE.md#source-preserving-mf01-grids-local-t-0221)
describe the bounded grid compiler and captured coupled execution. Local evidence
and canonical/public adoption remain separate.

## Latest local candidate: independent DAG composition — T-0220

[Current state](STATUS.md), [batch contract](decisions/ADR-0123-independent-dag-batches.md)
and [workspace commands](guides/PROJECT_WORKSPACE.md#independent-dag-batches-local-t-0220)
cover the latest local prototype. Public/canonical adoption remains separate.

## Latest local candidate: bounded result subranges — T-0219

See [current implementation](STATUS.md),
[range contract](decisions/ADR-0122-fold-dag-subranges.md) and
[the executable workflow](guides/SONATINE_AFFINE_FOLD.md#bounded-producer-subranges-local-t-0219).
This local candidate includes T-0218 strict saved-proof correction and T-0217
workspace capture. These unpublished candidates are separate from canonical main.

## Local affine-fold workspace candidate — T-0211

The [workspace guide](guides/AFFINE_FOLD_WORKSPACE.md) describes check/run/saved
inspection/diff over a reusable MF01 executable. Proposed
[ADR-0115](decisions/ADR-0115-affine-fold-workspace-candidate.md) binds snapshots,
transaction validation and container cleanup. This local candidate depends on
T-0210 and is not canonical main or an accepted/public delivery item.

## Local affine map/fold candidate — not integrated

T-0210 / Proposed [ADR-0114](decisions/ADR-0114-bounded-affine-map-fold-candidate.md)
widens the standalone RTL region to two inputs, affine views and reductions.
See the [guide](guides/AFFINE_FOLD_CANDIDATE.md) and
[Groq comparison boundaries](research/reviews/T-0210-generality-and-groq.md).
This archived review checkout is not the canonical main implementation.

## General rectangular grids

T-0208/#296 implements the owner-approved rectangular grid interface.
See [status](STATUS.md), [ADR-0112](decisions/ADR-0112-general-bounded-grid-kernels.md)
and the [guide](guides/PROJECT_WORKSPACE.md#rectangular-grids-and-editable-kernels).

Current priority: [simulation maturity before hardware](decisions/ADR-0107-simulation-maturity-before-hardware.md).
T-0204/#286 records the owner-approved correction. T-0197/#266 implements two
named results from one frozen input, with all-or-incomplete parent publication
under [ADR-0108](decisions/ADR-0108-bounded-project-result-composition.md).
See [the workspace guide](guides/PROJECT_WORKSPACE.md) and [current evidence](STATUS.md).
T-0205/#288 / ADR-0109 adds saved named-parent comparison after input/computation
edits. [T-0206/#290](research/reviews/T-0206-simulation-maturity.md) verifies the
five bounded maturity criteria. The subsequent owner-directed software continuation
delivers [T-0186 pinned MLIR import](guides/STANDARD_IR_IMPORT.md) for GEMM+bias+ReLU
on the owned CPU path. The owner then explicitly approved T-0207/#294:
[bounded32x32 tiling](guides/PROJECT_WORKSPACE.md#run-a32x32-grid-through-four-rtl-tiles)
through unchanged16x16 RTL requests (ADR-0111). T-0188 no-install host/budget inventory separately needs
actual Windows facts, with no purchase/tool install. The [T-0183 contract](research/reviews/graph-multiple-output-contract.md)
remains its planning provenance. Chisel/Verilator checks RTL; QEMU checks supported
Sonatine software. Their current project backends are separate.
T-0188/#194 host facts are now the next planning dependency; unfinished
T-0189/#195 physical work still requires qualified tools and a reviewed target.
Windows/Vivado facts do not block independent software development.
Retain the [offline board bundle](guides/FPGA-BOARD-BUNDLE.md), S01–S04 results
and [memory diagnosis](research/reviews/T-0189-memory-feasibility.md) for later
physical work. The [budgeted FPGA packet](research/reviews/T-0203-budgeted-fpga-path.md)
is historical planning, not the current next pull.

Retained earlier research context: [ADR-0103](decisions/ADR-0103-work-reduction-precedes-new-execution-hardware.md),
[RFC-0007](rfcs/RFC-0007-immutable-function-work-reduction.md), and the
[T-0199 restart review (historical filename)](research/reviews/2026-09-23-T-0197-research-restart.md).
The [T-0200 pinned workload and exact-oracle packet](research/reviews/T-0200-immutable-affine-workload.md)
records the pinned host-functional entry result.
[T-0201 compiler controls](research/reviews/T-0201-fixed-parameter-controls.md)
adds the matched ordinary runtime/fixed portfolio.
[T-0202 candidate matrix](research/reviews/T-0202-candidate-matrix.md) records
seven source-backed dispositions: no new mechanism selected, known CSE retained.
The [28-claim audit](research/reviews/2026-09-20-T-0057-atomic-claim-matrix.md)
is retained with its original checkout scope; the September 23 review explains
which proposals are deferred. TODO's current focus governs the next pull.

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
| [project workspace](guides/PROJECT_WORKSPACE.md), [Command workload examples](guides/PROJECT_WORKLOADS.md), [bounded Graph workload examples](guides/GRAPH_WORKLOADS.md), [Native Command Graph](guides/NATIVE_COMMAND_GRAPH.md), [showcase guide](guides/NATIVE_COMMAND_GRAPH_SHOWCASE.md), [T-0042 small-start packet](guides/T-0042-SMALL-START.md), and [task start phases](guides/TASK-START-PHASES.md) | Playable project use, Native operation, bounded execution packets, and WIP timing | editing/rerunning a project, trying synthetic workloads, running demos, executing T-0042, or deciding whether unfinished work may start |
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

Local candidate workflow: [Sonatine affine fold](guides/SONATINE_AFFINE_FOLD.md) (T-0212, Proposed ADR-0116; emulation and separate RTL comparison).
