# ADR-0133: Versioned admitted array fusion

Status: Proposed
Date: 2026-10-14
Task: T-0237 (local candidate; remote registration awaits authentication)
Context: ADR-0107, ADR-0132, EXP-0002 functional evidence

## Problem and authority

The owner directs continued implementation toward useful workloads. T-0236
completed the bounded integer-array workflow, not general practical readiness.
Its v1 materializer emits a whole-plane pass for every scalar operation and fold
iteration, even though the existing backend admits multi-operation maps and folds.
This duplicates captures and dispatches and can reject otherwise admitted work.
No hardware acquisition, numerical-type expansion or scientific claim is authorized
by this correction. Primary owns the local implementation; read-only reviews are
advice. GitHub currently returns 401 and the CLI reports invalid authentication.

## Decision for the candidate

Add explicit `raveil.array-program/v2`, retaining the exact v1 planner/binder and
saved receipt interpretation. The source grammar and numerical semantics are
unchanged. V2 selects the deterministic policy
`whole-stage-then-single-output-blocks/v1`:

1. Validate every declared input, stage, node, dependency and post-map, including
   declarations that are not on a requested output path.
2. On zero-filled structural inputs, try the unchanged whole stage as grid/v5.
   Try 16x16 first; if it does not fit, use the existing finite 256-tile planner.
   Keep fold extent, coordinates, boundary and post order. Existing backend
   instruction/register/rectangle admission remains final. Prefer the fused
   candidate only when its tuple(session count, materialized words, pass count)
   is no worse than scalar materialization.
3. Otherwise generate the original scalar sequence and greedily combine
   contiguous, same-shape operations into a single-output block. Try at most 15
   scalar operations; extra input loads and signed lowering still undergo actual
   backend admission. Permit at most one externally live result. Stage results
   form cuts; computations are neither dropped nor duplicated. An internal
   identity load can become `add_imm 0` with identical uint32 meaning.
4. Blocks bind at most two inputs, drawn from verified predecessor planes or
   the original affine gathers. The host gathers words; it does not calculate
   production arithmetic. This is not device-resident data movement.
5. Recompute dependencies, requested-output pinning and last uses after grouping.
   Rebind every child from the captured source and verified producers, using the
   existing coordinator and strict saved-reader path. No returned object alone
   authorizes dependent execution or publication.

Do not store data-dependent tile proposal hashes in the structural plan. The
existing captured source/hash binds actual input words. Saved v2 plans include
the policy identifier, choices and costs; future policy changes need a new
compatible interpretation rather than silently recompiling old captures.

## Explicit accounting

Existing limits remain: 128 source nodes, 8 stages/inputs/views/outputs, 64x64 grids,
128 final passes/sessions, 32,768 materialized output words, 65,536 conservative
logical plane words and 128 MiB / 16,384-entry captures. Source grammar admission
does not promise aggregate admission. Fused post maps produce two jobs per tile,
so session count and job count are separate.

V2 `work_words` counts every generated backend job's output words, including
the internal post-map producer. It does not count one whole fold as one arithmetic
operation. A separate `scalar_evaluations` counts original scalar nodes for every
output/fold coordinate, accumulator combinations and post nodes; its explicit
ceiling is 1,048,576. This is a source-level logical bound, excluding generated
prefix loads and signed legalization; it is not measured device work or latency.

Logical live storage counts original literals, retained planes, full bound input
copies, all packed tile/job inputs, job result planes and the separately assembled
full output. It is not a Python RSS or total verifier-memory bound. Capture byte
and entry reservations remain estimates followed by hard inventory checks.
Runtime copies are counted per backend job (`1 + passes + jobs`), kernel copies
per session (`1 + passes + sessions`). Reserve 64 KiB/pass plus 128 KiB/job and
64 entries/pass plus 32 entries/job in addition to all runtime-tree entries.
V1 defaults jobs to sessions and retains its exact previous accounting.
Both corrected byte and entry preflight must reject over-budget sources before
creating an attempt; a post job cannot share its runtime-copy allowance with
the fold producer.

## Validation and remaining work

Required: v1 plan/binding and saved-receipt compatibility; independent formulas
and generated mixed-stage checks; long/dead/fanout blocks; signed overflow and
post-fold ordering; exact resource rejection; data-independent planning; captured
source/plan tampering; failure with output suppression and fresh retry; actual
QEMU/RTL execution and saved reread without process creation.

The useful regression envelope includes 17x19 by 64 reduction, 32x32 by 8 reduction,
64x64 maps with 24 nodes, and linked block/transpose stages. These are concrete
functional workloads, not a universal practical-use definition. Fusion is a
known compilation technique; no novelty, measured speedup or Groq advantage is
claimed. Floating point, general model import, dynamic control, larger shapes,
device-resident execution and product hardening remain unfinished work.

## Local verification — 2026-10-14

Primary verified 307 distinct UT and revision02 actual QEMU/RTL acceptance:
13 workloads, two intended post-job failures and two successful retries; all
17 sealed parents revalidate without execution. Both failed trees are preserved.
The 75 sessions contain 80 jobs, 78 approved; successful parents publish 5,856
words. Revision01 remains separate provenance before job-aware capture budgeting.
Exact commands, source hashes and raw receipts are in the local T-0237 packet.
This verifies the candidate contract; proposed status and public integration
remain pending authentication and the canonical Issue/Project/PR workflow.
