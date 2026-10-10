# ADR-0111: Bounded spatial tiling preserves the existing RTL contract

Status: Accepted
Date: 2026-10-10
Task: T-0207 / Issue294

## Context

After T-0186/PR293, the owner explicitly directed continuation in response to
the exact32x32/four16x16 registration-and-implementation request. This resolves
the prior automatic-review scope rejection. T-0184's completed pressure study
identified host tiling as a later separate contract. This decision supplies that
contract; it does not reopen T-0184 or alter T-0197 named-result composition.

## Decision

Admit exactly a32x32 row-major grid of1024 uint32 words through
`raveil.grid-input/v1` with exact schema/rows/columns/words fields. Freeze the
input before execution. The computation is one fixed five-point sum (center,
north,south,west,east) modulo2^32. Values outside the full grid are zero.

Execute four16x16 children, row-major origins(0,0),(0,16),(16,0),(16,16).
Each child receives an18x18 input snapshot including its one-cell halo. Internal
seams always read the original full-grid neighbors, never zero padding or another
tile's output. Stage all four input snapshots plus one fixed v2 descriptor before
any child executes. Keep the existing10-instruction expression, eight-register
limit,324-word input/256-word output, ABI and RTL unchanged.

Use four sequential existing Project.run invocations, each with normal input,
compiler, independent oracle, C++ fallback and RTL checks. Reuse the existing
private child verifier with a per-tile input hash; do not pass the global input
hash as a child identity. Require the same simulator/RTL/source identity across
all four children. Build reuse is optional; no result caching is introduced.

## Publication and inspection

Use separate `tilings/` attempts and plan/result schemas. Do not expand the
one/two-child composition schema or route tile parents through its public API.
Every attempt has a fresh identity; freeze inputs/descriptors, retain private
children, and revalidate all inputs and children before publication. Assemble
1024 words from validated child output only; check every cell against a separate
full-grid reference that does not use halo staging. Saved readers regenerate
halos from the frozen full input and repeat these checks.

The final atomic no-overwrite hardlink of `record.json` is the publication point.
A successful record contains the complete1024-word output and its packed hash.
An incomplete record has `output=null`; no separate public assembled output file
is written. Cancellation between children or immediately before publication
never yields a published success. Interrupted sealing may retain a private pending
record and hash but no readable published result. This promises visibility, not
fsync/crash durability, multi-writer authentication or hostile-host isolation.
Inspection/history validate saved evidence without rerunning; tampered/unsealed
parents are rejected or labelled unverified. Retry creates a new attempt.

## Limits and acceptance

Host tests cover padding/seams, modular arithmetic, shape/type/path rejection,
frozen snapshots, failed/cancelled children, build drift, publication and tamper.
An actual source-bound RTL demo must compare both original and edited grids
against an independent1024-cell scalar calculation, preserve the old snapshot,
and retain a between-child cancellation attempt. Host fault injection remains
labelled separately from RTL execution; it is not in-flight device cancellation.

No arbitrary-size tiler, arbitrary expression, temporal/multi-pass decomposition,
shared tile arithmetic, performance benefit, QEMU integration, FPGA or silicon
claim follows. No new tools, device, purchase or performance experiment is needed.
