# ADR-0088: Graph dependencies determine execution order

Status: Accepted
Date: 2026-09-05
Task: T-0155
Related: ADR-0064, ADR-0081, ADR-0084, ADR-0087

## Context

The editable Graph workspace exposes dependency edges, but the compiler
previously rejected references to nodes listed later in the same descriptor.
Moving an independent load below its consumer therefore made an otherwise
valid DAG fail admission. The owner requested a bounded Graph generalization
alongside independently scoped workspace usability work.

## Decision

Validate the complete bounded node set and dependency references, then schedule
it topologically. Among ready nodes choose the earliest original descriptor
position. Already topologically ordered descriptors retain their instruction
order, allocation and encoded bytes. Different authoring orders need not
produce identical instruction bytes; their arithmetic results must agree.

Keep a single syntactically final STORE, and reject operands referring to that
STORE, unknown identifiers, duplicate identifiers and dependency cycles.
Forward references to value-producing nodes are admitted. The four existing
operations, sixteen-instruction capacity, eight registers, memory windows,
affine profiles and device ABIs retain their existing bounds.

The compiler-owned trace remains one entry per descriptor node. Entry index,
definition index, consumer positions, live ranges and release positions refer
to the emitted schedule. Node identifiers and the canonical hash of the
original descriptor preserve the authoring identity. Validate the trace against
the deterministic schedule and exact encoded instructions before returning it.
The existing trace schema remains sufficient; no trace field is removed.

The direct descriptor oracle evaluates the dependency schedule with its
existing node arithmetic, independently of register allocation and instruction
decoding. It shares dependency scheduling with the compiler; permutation tests
against previously admitted descriptors provide an additional check against
common scheduling mistakes. This is not a new independent RTL observation.

## Consequences

Users can move value nodes in an editable JSON Graph without manually restoring
execution order. The scheduler is deterministic, not a search for an optimal
schedule: an order can still exceed the existing live-register limit. Dead-node
elimination, CSE, capacity changes and additional operations are deferred.

This supersedes the earlier implicit requirement that descriptor list order
itself be executable. ADR-0081's compiler-owned explanation authority and
ADR-0087's exact snapshot/receipt binding remain in force. Host compiler tests
do not establish new RTL, performance or physical-device results.
