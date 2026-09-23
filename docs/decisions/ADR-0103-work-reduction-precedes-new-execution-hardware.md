# ADR-0103: Establish work reduction before choosing new execution hardware

Status: Accepted
Integration: local research-priority decision; remote integration pending
Date: 2026-09-23
Task: T-0199; follow-up T-0200; related T-0057, T-0044, T-0183, T-0186
Authority: owner's September 23 instruction to reconsider direction, update
repository/backlog and resume work following the Groq/prior-art discussion.
Supersedes: ROADMAP's September 19 next-pull ordering for research priority only.
No accepted execution contract, scientific threshold or historical EXP is superseded.

## Context

Explicit dependencies, static scheduling, regional reuse, resource feedback,
selective revalidation, dataflow and partial evaluation have substantial prior
art. The September 20 audit is preserved against its original `7c38a36` tree;
it is not an audit of every implementation subsequently present at `ecf5655`.
The latter is this change's cached mainline base. In particular, later Graph
generality, OpenASIP and EXP-0008/0009/0010 evidence must not be erased by
copying older STATUS or TODO files over current records.

The conversation produced several competing suggestions without establishing
a mechanism-specific advantage. Treating all of them as the next priority
would reproduce the fragmented work the owner rejected. Fewer scheduling
overheads, fewer semantic operations, fewer boundary bytes and lower measured
latency are different outcomes.

## Decision

Retain immutable semantics/numerical contracts, explicit graphs and effects,
owned objects, independent admission and advice-only Experience. Center the
next bounded research question on `P_W = specialize(F, W)`: can declared
immutable information reduce the work of the same function, beyond strong
existing optimizations, at an acceptable complete cost?

This selects a research question, not a new invention, model, optimizer,
instruction set, matrix encoding or chip. Exact partial evaluation, common
subexpressions, constant-matrix synthesis and tensor superoptimization are
baselines. A stored input snapshot is not permission to specialize future
invocations on those input values. Weight changes invalidate specializations;
floating-point reassociation and quantization require explicit numeric terms.

Use this sequence:

1. Preserve an executable known-optimization control and inventory the actual
   current input/constant boundary. T-0199 starts this read-only diagnostic.
2. T-0200 pins one representative immutable-parameter workload, provenance,
   numerical contract and ordinary strong baselines before selecting a new
   mechanism. Reuse T-0186's import investigation where relevant rather than
   inventing another framework integration task.
3. Identify a residual mechanism and compare it to the strongest applicable
   published/standard approach with equal information and search budget.
4. Only a surviving reduction justifies mapping/complete-cost evaluation and
   any proposed Daphnis change. Both baseline and candidate receive equivalent
   frontend transformations. Software-only benefit does not justify hardware.

Prior region/buffer, installed-control/lookup and other five-option proposals
remain preserved alternatives, not concurrent P0s. Experience research stays
result-conditioned; EXP-0003's negative result is not reversed. Existing
editable workspace functionality remains a usable substrate. No new CPU
hardening, ASIC/FPGA, capacity expansion or broad port is added to this path.

## Backlog and integration boundary

T-0199 / Issue #268 integrates the owner-selected planning/preflight work.
T-0200 is the single research successor. T-0183 planning is already complete;
its separate T-0197 / #266 implementation and T-0186 stay deferred. The latter
may become a dependency only if the workload requires it. T-0195/0196 remain
complete; T-0044 and T-0106 retain their triggers.

September 26 integration reconciliation: latest main is `bdfac7f`; remote
access is restored. The September 23 local research IDs collided with live
T-0197 / #266 and are now T-0199/T-0200. Original filenames/logs/receipts remain
provenance. This corrects identity and delivery state, not the accepted research
question. ADR-0104 records the owner's separate removal of quota gating.
No scientific threshold or accepted runtime contract changes.

## Consequences and rejection criteria

No claim follows merely from a graph, cache, proof, compiler, AI policy or
combination being present. A hand-picked toy reduction is commissioning only.
Reject the hardware direction if an equally optimized conventional backend
captures the benefit, or if encoding, configuration, storage, fan-out, traffic,
verification and amortization consume the savings. A failed mechanism stays
recorded; do not automatically switch to a new chip proposal.

## Verification

[RFC-0007](../rfcs/RFC-0007-immutable-function-work-reduction.md) specifies the
unresolved scientific boundary. The [restart review](../research/reviews/2026-09-23-T-0197-research-restart.md)
records the current-tree diagnostic and source inventory. Production compiler,
schemas, admission, oracle, RTL and device boundaries are unchanged.
