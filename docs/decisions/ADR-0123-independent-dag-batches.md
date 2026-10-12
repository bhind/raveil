# ADR-0123: bounded independent DAG batches over the coupled executor

Status: Proposed
Date: 2026-10-11
Task: T-0220
Context: ADR-0107; Proposed ADR-0120/ADR-0121/ADR-0122

## Workload and existing boundary

An owned24x24 uint32 three-by-three box-sum image can be decomposed into nine8x8
outputs, each using a10x10 halo, three affine views and fold extent3. MF01 supports
these computations, but the coupled DAG entry exposes one designated result from
at most eight jobs per guest. Existing project_tiling already assembles bounded
rectangular grids over the earlier standalone RTL path; it does not capture the
Sonatine/RTL coupled evidence or produce its capability/snapshot checks.

## Local candidate

A `raveil.dag-batch.v1` source has1..16 unique named `items`, each containing one
existing `dag`. Each DAG independently passes existing whole-plan admission. A
single source snapshot, kernel and runtime are captured before any execution.
The host invokes the existing executor sequentially, once per independent item.
No cross-item links, object migration or larger guest session is implied.

All children complete -> publish all named outputs together. The first sealed
incomplete child -> stop and publish an incomplete parent with `outputs:null`,
even if that child retains an available pinned output. Unexpected exceptions,
interrupts before publication and uncertain cleanup leave an unsealed parent.
The pending-file/hard-link publication point never overwrites an existing record.

Saved inspection reconstructs exact input/kernel/runtime bindings and verifies
every child. Physical child directories and saved rows must be the declared
ordered prefix; every child before the last must be complete. An incomplete child
is last and no later directory may exist. A short all-success prefix is invalid.
Parent outputs and status are reconstructed from these checks rather than trusted.
History and comparison revalidate evidence without launching executables.

## Resource accounting

The source is bounded to4MiB, with16 independent sessions and128 total jobs at
most. Existing per-DAG bounds and ordinary tree snapshot defaults remain intact.
The parent inventory has a separate128MiB/16,384-entry ceiling. Per-call tree
limits are exact positive integers with these finite global ceilings.

Only the three parent seal files (`record.json`, `record.sha256`, `.record.pending`)
are excluded before inventory budget accounting; they must still be regular
bounded files. Nested child records remain counted and hashed. Exclusion is not
allowed during snapshot copying. This prevents a near-cap parent becoming
unreadable merely because atomic publication added its own manifest.
Generated execution evidence exceeding the ceiling remains unsealed; the limit
is not a promise that arbitrary128-job traces always fit.

## Scope and evidence

CLI: batch-check / batch-run / batch / batches / batch-diff. Names, source order,
output names/shapes and common executables are checked for saved comparison.
The box-sum script is an owned workload demonstration; batch execution is generic
over admitted DAGs. Assembly checks every global coordinate against an independent
full-grid formula, including boundaries and uint32 wrap. It is host composition,
not a larger guest, guest cross-session dependency or new RTL executor.

Exact outcomes are recorded in STATUS and the dated log after execution. This
local proposal changes no accepted public architecture, guest/authority ABI,
RTL, hardware acquisition, performance gate or novelty claim.
