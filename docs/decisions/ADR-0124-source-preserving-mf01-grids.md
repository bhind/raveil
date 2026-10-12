# ADR-0124: source-preserving bounded MF01 grid lowering

Status: Proposed
Date: 2026-10-11
Task: T-0221
Context: ADR-0107; Proposed ADR-0114/ADR-0123

## Problem

T-0220 can capture independent coupled DAG sessions, but its box-sum example
constructs low-level inputs in a script. Saved execution alone does not explain
which original grids, global neighborhood rules or placements produced a result.
A useful editable workflow must bind those source semantics to the existing
execution proof without introducing another guest or RTL execution mechanism.

## Local source and lowering

`raveil.mf01-grid/v1` contains exactly schema, inputs, tile, boundary and kernel.
Inputs are one or two existing grid-input/v2 objects with equal 1..64 row/column
dimensions and uint32 words. Tile dimensions are 1..16; at most 16 independent
tiles are admitted. Boundary is zero, clamp or wrap.

Kernel fields are extent (1..64), fold (sum/max), views, nodes and result. Each
of 1..8 named views identifies input 0/1, a signed row/column offset (-63..63)
and nonnegative fold step (0..63). At output coordinate (r,c), fold iteration k
reads (r+offset_row+k*step_row,c+offset_column+k*step_column). Map nodes retain
existing MF01 load/add/mul/max/add_imm/ge_imm semantics and instruction/register
limits; arithmetic and sum wrap at uint32. No new opcode or numeric type exists.

For each tile/input, union the rectangular coordinate ranges of its views over
all fold iterations. Reject a rectangle larger than 324 words before packing.
Sample that rectangle under the global boundary rule, then translate views into
its local linear offsets/strides. Zero inactive row, column and fold strides.
Compile and resource-admit every single-job DAG before allocating an execution.
The whole source file is bounded by the existing batch 4 MiB limit.

## Source-bound publication

The grid parent freezes original source, exact derived batch bytes and a placement
plan. One existing batch captures kernel/runtime and all independent children.
A successful parent assembles nonoverlapping rectangles covering every output
cell and compares a separate untiled scalar oracle using original coordinates.
The oracle shares source admission but consumes no lowered buffers/instructions.
It is independent of the tiling calculation, not a formal semantic proof.

Incomplete child batches expose no grid output. Unexpected exceptions, uncertain
cleanup and interrupts before publication remain unsealed. A pending file and
no-overwrite hard link provide the existing atomic publication boundary.

Saved inspection re-parses and recompiles the frozen original source, requires
exact lowering and placement, exactly one matching child batch, matching captured
input bytes and child receipt hash, all nested proofs, and reconstructed output.
Inventories use existing bounded batch accounting. History and comparisons launch
no executable. Comparison requires complete grids of equal dimensions and common
kernel/runtime identities; source, program and tile layout may differ.

## Limits and evidence

This is host composition of independent tiles with equal-sized input grids,
nonnegative fold steps, uint32 operations and conservative rectangle packing.
Dependent stages, sparse packing, automatic tile choice, dynamic shape/control
flow and cross-session object movement are outside the candidate. Ordinary static
tiling, affine views and reduction are established techniques, not novelty claims.
Exact host and actual QEMU/RTL functional outcomes belong in STATUS and the dated
log. No accepted architecture, authority ABI, physical performance experiment,
hardware budget, Groq advantage or public adoption changes with this proposal.
