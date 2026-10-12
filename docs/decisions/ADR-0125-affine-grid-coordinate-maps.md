# ADR-0125: explicit output shape and affine input-coordinate maps

Status: Proposed
Date: 2026-10-11
Task: T-0222
Context: ADR-0107; Proposed ADR-0114/ADR-0124

## Concrete source restriction

Existing MF01 computes rectangular matrix products and transpose, but the v1
grid source forces equal input dimensions and identity output-to-input row and
column maps. Thus the source-preserving coupled workflow cannot express those
already-supported computations. Generalize the coordinate mapping rather than
introducing workload-specific executors or increasing hardware resource bounds.

## Local v2 contract

`raveil.mf01-grid/v2` adds root `shape:[rows,columns]`, each 1..64, independently
of the one or two input grids. Each input remains validated as grid-input/v2,
with its own 1..64 dimensions and complete uint32 contents. V2 views contain
exactly input, offset, row, column and step. Offset components are -63..63;
row/column/step vector components are exact integers 0..63.

For output coordinate (r,c) and reduction iteration k, input coordinates are:

`offset + r*row + c*column + k*step`.

All other v1 map/fold, source-size, instruction, register, tile-count, tile-shape
and packed-input bounds are retained. V1 continues to require equal input grids
and implicitly uses row=(1,0), column=(0,1), with no new fields accepted. V1's
lowered batches, placements and saved proof contract remain byte-compatible.

## Lowering and independent reference

At tile origin (R,C), compute each view's own origin
`offset + R*row + C*column`. With nonnegative vectors, its rectangle endpoints
occur at local (0,0,0) and (height-1,width-1,extent-1). Union those rectangles per
input, reject over 324 words, and sample the complete logical rectangle under
the original input's zero/clamp/wrap rule. Do not crop it to physical input bounds.

For union origin (rmin,cmin) and width W, use:

- base = (origin_row-rmin)*W + origin_column-cmin;
- output-row stride = row_row*W + row_column;
- output-column stride = column_row*W + column_column;
- reduction stride = step_row*W + step_column.

Zero inactive strides and retain existing MF01 admission. No new guest, RTL,
capability reference, object slot or numeric operation is introduced. The untiled
oracle separately evaluates original coordinate expressions; boundary and linear
index calculations use each selected input's dimensions, not output dimensions.
Existing saved parents recompile and bind these shapes/maps through the same
source/lowering/child proof checks; no parent schema change is needed.

## Workloads and limits

Matrix multiply uses A row=(1,0), column=(0,0), step=(0,1); B row=(0,0),
column=(0,1), step=(1,0); multiply map and sum fold. Owned fixtures establish
compatible contraction dimensions explicitly. General sampling with a boundary
rule does not itself assert that a user program is mathematically a matrix product.
Transpose swaps row/column vectors. Zero vectors support broadcasting, and
non-unit vectors support strided sampling.

This remains a bounded two-dimensional uint32 affine source, not arbitrary tensor
rank, signed strides, dependent tile stages, dynamic control flow or automatic
tile search. Affine maps, matrix tiling and broadcasting are known methods and
are not novelty claims. Functional acceptance does not establish physical speed,
energy, Groq advantage or public adoption. Evidence is retained in STATUS/log.
