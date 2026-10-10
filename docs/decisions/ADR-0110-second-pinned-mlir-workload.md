# ADR-0110: A second pinned MLIR workload uses the existing owned graph

Status: Accepted
Date: 2026-10-10
Task: T-0186 / Issue185

## Context

The owner requests continued software/simulation implementation after T-0206.
The existing T-0186 backlog explicitly asks for one additional owned workload
through the pinned import boundary. GraphProgram already admits gemm_bias_relu;
RTL descriptors have different numeric semantics and are a separate backend.

## Decision

Extend ADR-0032's one-fixture restriction to exactly two digest-bound fixtures.
Keep the original GEMM source byte-for-byte. Add an owned static signature:
`(tensor<8x8xi32>, tensor<8x8xi32>, tensor<8xi64>) -> tensor<8x8xi64>`.
Signed-extend both matrix inputs to i64, accumulate their products from zero,
add bias by column, then take signed maximum with zero. Use existing standard
linalg/arith operations; no custom dialect. This maps to the already-admitted
`GraphProgram.create("gemm_bias_relu", 8, 8, 8)`.

Select a source pin by validated family, and require that family's exact digest
and byte count. Family/shape/source substitution fails before compiler execution.
An arbitrary edited MLIR source, even with a recomputed manifest hash, is not
admitted. This is exact-fixture mapping, not parsing or lowering compiler output.
The compiler version/revision/distribution pins and both public schemas remain
unchanged. Importer implementation version becomes2 for both fixtures.

Native replay uses bounded inputs for which every product, partial sum and bias
addition fits signed i64. No full-range i32/i64 arithmetic equivalence is claimed:
MLIR fixed-width arithmetic and overflowing signed C are not interchangeable.
Current execution still uses the existing generated inputs, baseline-first check,
independent Pavane reference and policy/rollback path. Custom replay cases are
acceptance harness inputs, not a new user-input API.

## Evidence and consequences

Actual pinned compiler acceptance and owned native/Python differential correctness
are separate checks. Compiler success does not execute the VMFB, prove IREE runtime
equivalence, grant execution authority, or establish general MLIR import. There is
no new RTL/QEMU lowering, hardware fit, timing, novelty or superiority claim.
Reuse the existing offline local tool image; no dependency installation or update.
ADR-0032's remaining lineage, source/tool trust and isolation limits still apply.

Primary references consulted for independently authored fixture syntax:
[MLIR Linalg](https://mlir.llvm.org/docs/Dialects/Linalg/#linalggeneric-linalggenericop)
and [MLIR Arith](https://mlir.llvm.org/docs/Dialects/ArithOps/#arithmaxsi-arithmaxsiop).
These are ordinary existing operations, not a novel mechanism; actual acceptance
is tested against the pinned compiler, not inferred from current documentation.
No upstream implementation is copied or dependency license scope changed.
