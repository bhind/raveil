# ADR-0040: BOOM reference is a pinned control, not a candidate

Status: Accepted
Date: 2026-08-12

## Context

RFC-0004 requires an ordinary OoO control and permits a same-core
OoO-disabled diagnostic when reproducible. The existing Rocket reference is
the gitlink selected by Chipyard 1.11.0, but BOOM was not yet fetched or fixed
as a repository-owned dependency boundary. Treating a current BOOM checkout or
an unrelated prebuilt image as equivalent would break source and toolchain
identity before functional execution.

The pinned source exposes a BOOM chicken CSR bit named `disableOOO`. Its use in
the core waits for an empty ROB and LSU before dispatching the next instruction.
It does not remove the ROB, rename maps, issue queues, physical registers, or
LSU from the generated design. The diagnostic is therefore useful for a
same-core serialization observation, not as an area ablation or an in-order
core replacement.

## Decision

Use Chipyard tag 1.11.0 at
`ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1` as the parent source coordinate.
Its BOOM gitlink fixes `riscv-boom/riscv-boom` at
`9459af0c1f6847f8411622dac770ac78fe10847c`. Begin with
`chipyard.SmallBoomConfig`; do not call it resource-matched to Rocket or the
owned static executor until cache, memory, functional-resource, and lifecycle
boundaries are explicitly adapted.

Keep Chipyard and BOOM as ignored, clean, detached external checkouts. The
owned fetch and verification scripts must check origins, revisions, the parent
gitlink, exact license hashes, the selected configuration, chicken CSR address
`0x7c1`, mask `0x8`, and the source path that consumes `disableOOO`. Retain the
upstream BSD-3-Clause and `LICENSE.SiFive` Apache-2.0 notices. Do not copy BOOM
implementation into owned candidate RTL.

Call the CSR mode `boom-ooo-disabled-diagnostic` or `serialize-dispatch`; never
call it an in-order BOOM, stripped OoO core, structural ablation, or proof that
OoO hardware can be removed. Rocket remains the separate in-order control.

This decision pins source only. A BOOM RTL smoke requires a separately owned,
immutable build wrapper and exact transitive dependency verification. Do not
use an unofficial prebuilt container as evidence authority. Functional source
verification and later RTL execution remain non-performance evidence.

## Consequences

The project now has an exact BOOM source coordinate and an honest interpretation
of its diagnostic. It does not yet have BOOM elaboration or instruction
execution, a common scratchpad, complete lifecycle accounting, matched resource
budgets, or a comparison result.

T-0042 remains open for the immutable BOOM build/execution path and common
adapter records. T-0044 remains gated and must not treat the diagnostic as an
area or energy proxy for removing OoO structures. License verification is not
patent clearance, non-infringement, or freedom to operate.
