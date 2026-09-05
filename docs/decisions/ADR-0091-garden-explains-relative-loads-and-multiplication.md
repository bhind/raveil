# ADR-0091: Garden explains relative loads and multiplication

Status: Accepted
Date: 2026-09-06
Task: T-0159
Related: ADR-0081, ADR-0084, ADR-0089

## Decision

Extend ADR-0081's read-only explanation admission to existing program versions
3 and 4. Keep both explanation and compiler-owned lowering trace schema v1:
their version field already discriminates the supported instruction encoding.
This supersedes the old v1/v2-only Garden admission limit, not its authority.

For v3/v4 LOAD, require exactly row_delta and column_delta integers in [-1,1],
excluding booleans. Validate their signed five-bit fields at bits 24:20 and
19:15 against the retained instruction, including all reserved bits. Copy
addresses into immutable mappings. Old v1/v2 named selectors remain unchanged.
MUL_U32 is permitted only in v4, computes the unsigned product modulo 2^32,
and uses the existing binary-register encoding. V4 need not contain MUL:
descriptor schema v3 always emits program v4. V2 still requires MAX.

Show relative offsets, the input-word address formula and wraparound product
semantics beside the selected retained instruction. Keep identity, topology,
register-lifetime, framing, agreement, path and non-claim checks. Garden does
not import the compiler, regenerate results or gain execution/device authority.

## Verification and non-claims

Host tests use compiler-generated traces with explicitly synthetic envelope
identities to exercise parser/rendering behavior; these are not retained RTL
results and must not be exported as execution evidence. Rehashed invalid
addresses, versions, reserved bits and source registers must fail closed.
The unchanged retained v2 fixture remains the actual evidence-reference demo.
No new RTL run, performance claim, UIO support, hardware gate or Sprint
ceremony acceptance follows from this presentation change.
