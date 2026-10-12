# ADR-0128: Compose bounded grid sources through verified whole-grid results

Status: Proposed
Adoption: local candidate; public adoption pending
Date: 2026-10-11
Task: T-0227
Context: accepted ADR-0107; Proposed ADR-0123/0124/0125/0127

## Problem

One map/fold and its pointwise post map do not express two matrix products, or
transpose/square branches that join in a later product. Adding a dedicated source
feature for each pairing hides the common requirement: a later admitted program
reads the verified output of an earlier admitted program.

## Candidate contract

`raveil.mf01-flow/v1` has exactly `schema`, `stages`, `outputs`. There are1..8
unique named stages, each with exactly `name`, `source`. A source is an existing
v1/v2/v3 grid source; its inputs are inline grid objects or exact `{"from":"name"}`
links. Names use existing confined project names. Outputs are1..8 unique existing
stage names, in requested result order. Unknown producers, malformed links and
cycles reject. Every declared stage executes, including stages not designated as
an output. Ready stages are selected in lexicographic name order, one at a time;
authoring order is not execution order.

Before any attempt, stage shapes and existing program/resource admission are
computed in dependency order using shaped zero placeholders for linked inputs.
Existing grid admission is value-independent; original inline words are still
validated. V1 shape is inferred from resolved inputs; v2/v3 use explicit shape.
At most16 coupled sessions and128 underlying jobs are admitted in aggregate;
current sources imply at most32 jobs because a tile uses one or two jobs.
No automatic partition change occurs. Original sources and explicit tiles remain
visible. This layer neither creates a new guest object nor relaxes MF01 limits.

## Execution and evidence

Freeze the original source, one kernel and one verified runtime before executing.
Materialize a linked input from the previous stage's verified committed whole-grid
output. Each stage uses the existing project grid runner; every child is reloaded,
its frozen source compared byte-for-byte with the derived source, and its nested
batch's kernel/build identities compared with the parent before its output can
feed another stage. Saved reads repeat those checks without execution.

The capture records the exact scheduled prefix. A first incomplete stage stops
all later stages, including independent ones. Parent outputs are present only
when every scheduled stage succeeds. Already sealed child results remain available
as diagnostics; the parent does not undo their receipts. Exceptions, interrupts,
uncertain cleanup and evidence-capacity failures leave the parent unsealed.
Parent records publish last with existing no-overwrite hard-link semantics.

Existing input4MiB and evidence128MiB/16,384-entry caps remain. Compute admission
alone is not a reservation for artifact storage: multiple stage runtime snapshots
can exceed capture capacity, which must fail without a completed parent record.

## Limits and evidence

This is bounded host orchestration with whole-grid materialization, not hardware
streaming or parallel stage execution. No inter-stage latency/speed/energy claim,
physical result or novelty/Groq advantage follows. It does not add signed/floating
arithmetic, dynamic control flow, sparse gathers or stages outside existing grid
source versions. Tests must include direct multi-product and branching formulas,
invalid later stage rejection before execution, failed-middle stop, altered valid
child rejection before downstream use, coordinated proof rebinding, executable
mismatch, saved reads without processes and actual QEMU/RTL execution.
