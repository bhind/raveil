# ADR-0127: pointwise mapping after a committed grid reduction

Status: Proposed
Date: 2026-10-11
Task: T-0225
Context: ADR-0107; Proposed ADR-0120/ADR-0124/ADR-0125/ADR-0126

## Concrete semantic gap

Existing grid source maps each reduction term and then folds. Matrix-product bias
or a threshold on the final sum cannot generally be moved into that per-term map:
adding seven per term differs from adding seven after the sum. Existing bounded
DAGs already support the required committed producer dependency; expose it in
source without changing the executor or authority path.

## Local v3 source

`raveil.mf01-grid/v3` retains all v2 fields and requires exactly one additional
`post` object with exactly `nodes` and `result`. It uses the existing MF01 SSA
operations and program/register/immediate limits. Its only compiler-defined view
is `reduced`, reading the corresponding cell of the completed tile. There is no
post-stage global input, neighborhood access or second reduction in this version.
V1/v2 do not accept post fields and keep identical lowering and numerical behavior.

Each tile lowers into an existing `raveil.fold-dag.v1`:

1. `reduce`: the original affine map/fold and literal packed inputs.
2. `result`: the same output shape, extent 1, sum fold, lengths [tile_words,0],
   a contiguous `reduced` view and inputs [{"from":"reduce"},[]].

Inactive strides are zero. The whole DAG passes existing admission before any
execution. The intermediate remains live through the second job's reads, and
distinct slots hold the final result. At 256 words, the second job needs two READ
and two WRITE references, fitting the unchanged four-reference/eight-slot limits.
Only `result` is designated/pinned; the intermediate is never a fallback output.

## Semantics and saved evidence

First complete the original uint32 fold, then execute post nodes in order, with
uint32 wrap after each arithmetic operation and unsigned comparisons. The untiled
oracle evaluates the post nodes over the original-coordinate folded scalar; it
does not consume lowered post instructions or device intermediate arrays.

Failed reduction prevents dependent dispatch. Failed post leaves final output
unavailable even if reduce committed. Existing batch/grid wrappers stop and expose
no complete grid output in either case. Unexpected errors remain unsealed.
Saved reconstruction recompiles the exact frozen source into both jobs and verifies
the nested dependency/guest/RTL evidence before assembling the final grid.

The tile planner naturally admits both jobs. Its packed_input_words metric retains
the original source-input packing definition and excludes intermediate READ/WRITE
traffic. It is not a total-traffic or latency estimate. Execution never trusts
planner metadata; the explicit v3 source is re-admitted as usual.

## Scope

This is one pointwise post stage per independent tile using existing DAG authority.
It is not arbitrary multi-stage graph partitioning, inter-tile communication,
dynamic control flow, a new RTL operation, a novelty claim or Groq superiority.
No performance experiment, physical hardware, public adoption or gate changes.
Exact host, QEMU/RTL and saved-proof results belong in STATUS and the dated log.
