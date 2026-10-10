# ADR-0112: Bounded rectangular grids with editable kernels

Status: Accepted
Date: 2026-10-10
Task: T-0208 / Issue296

## Context and authority

The owner requested further generalization after T-0207. Public Issue creation
was rejected by automatic approval review because the exact expanded scope
required approval before publication. The owner subsequently approved the exact
reviewed scope and Issue/PR/main integration. Issue296 adopts the tested local
candidate. ADR-0111 remains authority for existing v1 records.

## Contract

A `raveil.grid-input/v2` has exact schema/rows/columns/words keys, each dimension
an integer in1..64, and exactly rows*columns uint32 words. Bound JSON to128KiB
(to admit worst-case64x64 pretty JSON). Keep the existing v1 fixed32x32 contract.
A `raveil.grid-kernel/v1` JSON (at most16KiB) has exact schema/graph_id/nodes keys.
Its nodes use the existing v5 operations: LOAD_U32 with relative offsets -1..1,
ADD_U32, MAX_U32, MUL_U32, ADD_IMM_U32, GE_IMM_U32 and one final STORE_U32.
Existing compiler validation,16-instruction/eight-register capacity and unsigned
22-bit immediate restrictions apply. Lower the kernel to a full16x16 v5 Graph;
no RTL, ABI or compiler change. Arithmetic wraps modulo2^32 after each operation.

Choose one global boundary: zero, clamp (nearest edge), or wrap (periodic).
Freeze full input, kernel and boundary before any child. Tile origins are
row-major steps of16. Each18x18 halo reads from the original full grid according
to the global boundary, including the unused portions of partial edge tiles.
Run and validate all256 words of each child. Crop only at assembly to the exact
valid rows/columns of each tile; at most16 children. Compare every assembled
cell with a separate full-grid dependency interpreter that does not stage tiles
or reuse compiler scheduling. Forward references and duplicate operands retain
DAG semantics; the existing compiler first rejects cycles/invalid references.

## Records and failure semantics

New plan/result schemas v2 bind kernel bytes, descriptor, dimensions, boundary,
origins, valid extents, all halos, child identities and exact output dimensions.
Regenerate these on saved reads. Keep exact v1 schemas/behavior for old callers
without --kernel; require v2 input when a kernel is explicitly supplied.
Reuse existing private child validation and same-build checks. Publish all valid
output words only in the final atomic record; incomplete output is null. Retain
fresh attempts, between-child cancellation and last-publication checkpoint.
No fsync/crash-durability or hostile-host authenticity promise is added.

`tile-check` admits and displays shape/boundary/instruction/tile counts without
execution or writes. `tile-diff` compares validated complete saved grids with
matching shape/build; it reports input/kernel/boundary/output changes and never
executes. Both live input and kernel edits affect only a new run.

## Acceptance and limits

Cover shapes1x1,1x64,64x1,17x19,64x64 and other nonmultiples; all opcodes,
boundaries, modular-before-comparison behavior, DAG order, admission/resource
limits, tamper, cancellation/failure/retry and v1 regression. Execute multiple
shapes/kernels/boundaries through actual cached local RTL simulation, with
independent scalar formulas, an edited kernel and retained cancellation.

This is one-input/one-output, one-pass, bounded uint32 spatial execution. It is
not arbitrary tensors/languages, multi-pass scheduling, a larger physical core,
QEMU coupling, FPGA execution, novelty or speed/energy evidence. No new tool,
external source adoption, installation or hardware purchase is needed.
