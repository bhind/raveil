# ADR-0129: Separable finite partition advice for whole-grid flows

Status: Proposed
Date: 2026-10-11
Task: T-0228
Context: ADR-0107; Proposed ADR-0126/0128
Adoption: local candidate; public adoption pending

## Problem and scope

Explicit tiles can reject an otherwise executable composition, or request more
sessions than needed. A general source adviser should preserve program semantics,
links and execution authority while finding an admitted bounded partition.

## Candidate decision

Separate exact structural/link/topological validation from requested-partition
compilation. In dependency order, resolve only linked inputs to shaped zero grids
and use the existing256-choice per-grid tile planner. Inline values and requested
tile types remain validated. Copy only the selected tile into a deep copy of the
original linked stage. Preserve authoring order, output order, links and every
non-tile source field. Never publish a materialized zero-input probe as the source.
Finally compile the entire selected flow through ordinary admission.

Each stage's output shape is fixed independently of tiles and input values.
All links carry complete assembled grids, with no required tile alignment between
stages. Thus each stage's session-count minimum is independent: their sum is the
minimum total across these bounded uniform partitions. Among those minima, the
same independence makes the sum of initial packed-input words minimal. Existing
per-stage nominal-size tie-breaks are deterministic. If summed minimum sessions
exceed16, no other combination in this search space can meet that bound.

Preview is read-only. Optional output creates a new confined JSON source with
no overwrite; original sources remain unchanged. Execution consumes that ordinary
source and repeats admission. Advice JSON is never execution authority.

## Limits

The packed-word objective counts initial input packing once per stage tile,
including linked inputs. It excludes post-job accesses, repeated loads within a
fold, intermediate writes/copies, retained evidence size, latency, energy and
physical resources. With existing sources at most2 jobs/session makes
the128-job ceiling nonbinding under16 sessions. Future source versions or streaming
stage connections may invalidate separability and require a new decision. Existing
4MiB input and128MiB/16,384-entry evidence limits remain unchanged. No performance,
Groq superiority or novelty claim follows from static session reduction.

Evidence must include independent small geometry enumeration, invalid-partition
rescue, aggregate infeasibility, value/author-order invariance, exact non-tile
preservation, read-only/no-execution/no-overwrite behavior and actual selected
execution compared with direct formulas and retained equivalent captures.
