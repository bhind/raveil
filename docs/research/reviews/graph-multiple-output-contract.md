# T-0183: two useful results before multiple hardware STOREs

Date: 2026-09-19
Status: technically accepted planning decision; no runtime or ABI change
Authority: owner-requested generalization sequence, following T-0187/T-0196
Evidence class: Planning with host compiler/oracle contract vectors

## Concrete pressure and decision

The existing sensor-energy-bias workload computes `(x*x + 17) mod 2^32`.
A user wanting both uncorrected `raw = x*x mod 2^32` and `biased` must currently
run two single-output Graphs. Merely adding a second STORE is rejected by the
current compiler. This is useful multi-result pressure, not evidence that the
hardware needs multiple effects per Graph immediately.

Select a separately scoped **two-result host composition** increment first.
Keep one final STORE per child, independent private output buffers and existing
oracle/fallback/RTL checks. Expose a logical result set only after both pass.
Do not widen the instruction installer, output window, or STORE encoding now.

| Alternative | Benefit | Main cost / consequence |
| --- | --- | --- |
| Two manual current runs | Works now, no boundary change | User must match inputs and handle partial success |
| Bounded host result-set composition (selected next) | Named outputs, same-input guarantee, one logical success boundary; backend-independent | Two executions duplicate common arithmetic; no shared compute speedup |
| Versioned two-STORE hardware Graph | Could compute common `x*x` once | New output routing/ranges, ABI, installer, oracle/fallback and partial-failure rules across every backend |

T-0196 can avoid recompilation between the children, not the duplicated input
staging/execution/validation. Neither composition nor multiple STOREs solves
instruction/register capacity automatically. For this tiny expression the
generalization benefit is usable named results, not a performance claim.

## Proposed composition contract (not implemented)

- Exactly one or two declared named outputs. Zero outputs and more than two
  reject before any child execution. One output may use the existing path;
  two use distinct child runs. Names match ASCII `[a-z][a-z0-9_-]{0,30}`
  (1-31 bytes), compared exactly; no case folding or Unicode normalization.
  Empty, duplicate, path/control/non-ASCII and overlong names reject. There are
  no reserved names: labels are values in an ordered `outputs` array, never
  parent field keys. Element zero maps to private child slot zero and element
  one to slot one; each element binds its name, child run ID and result hash.
  Names never select filesystem paths or output addresses.
- Freeze the input once and bind both child descriptors and the shared input
  hash in a parent plan before starting. Do not reread live input between runs.
- `raw` and `biased` each own a separate 256-word private buffer; active region
  is 64 words for this 8x8 example, inactive words remain zero. No aliases,
  overlapping writes, append operations or user-selected output addresses.
- Execute in deterministic declared order initially; do not introduce parallel
  runtime scheduling. Ordering changes no mathematical result for pure children.
- Publish a parent success record only after both children pass their existing
  independent Python oracle, C++ fallback and RTL checks. The parent's named
  outputs reference immutable child results with input/descriptor/output hashes.
- On second-child failure/cancellation, retain the first child's valid evidence
  and the failed attempt for diagnosis, but never publish a complete result
  set. No rollback of already-saved private child history is promised or needed.
  No external side effects are admitted. Reattempt is a new parent attempt.
- Cancellation before the first child starts produces no successful children;
  cancellation between children produces an incomplete parent; cancellation
  after execution but before parent publication still produces no complete set.
- Garden/history must distinguish child success from parent completeness.
  Neither a partially written directory nor one successful child is acceptance.

## Verification boundary and deferred extension

`tests/test_graph_multiple_output_contract.py` preserves actual current
zero/two-STORE rejection and checks two admitted single-output Graphs against
independent scalar formulas, including wraparound and inactive words. These
are planning host tests, not a new C++/RTL multi-output execution claim.

A successor implementation requires a new accepted ADR, explicit parent
record/version schema and failure-injection tests before runtime changes.
Do not silently add a group flag to `project run`. Revisit a two-STORE ISA
extension only after the composed workload shows an important duplicated-work
cost, with matched resources and complete end-to-end evidence. FPGA and ASIC
remain later backend gates, not prerequisites for this useful software step.
