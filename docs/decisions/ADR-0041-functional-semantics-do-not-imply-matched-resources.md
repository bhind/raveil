# ADR-0041: Functional semantics do not imply matched resources

Status: Accepted
Date: 2026-08-12

## Context

RFC-0005 requires Rocket, BOOM, and the static candidate to use the same
fixed-latency banked scratchpad for an isolation comparison. Cache-backed or
variable-latency memory is explicitly a later control, not a silent substitute.

The first `raveil.simulation-adapter/v1` contract placed the required scratchpad
model at contract level but did not require each observation to report its
actual memory model or whether matching had been verified. That was adequate
for the owned static-Graph functional smoke alone, but it could allow a normal
cache-backed Rocket or BOOM run to look resource-matched merely because its
semantic output agreed. Chipyard's existing `WithScratchpadsOnly` fragment also
rewrites Rocket tile parameters only; it cannot be assumed to adapt BOOM.

## Decision

Replace the active functional boundary with
`raveil.simulation-adapter/v2`. Preserve v1 in Git history and its dated log; do
not reinterpret old records as v2.

Every v2 observation reports `memory_model`, `resource_match_verified`, and
`matched_comparison_ready`. The accepted memory-model vocabulary distinguishes
owned private candidate scratchpads, cache-backed variable-latency CPU memory,
and the RFC-0005 matched fixed-latency banked scratchpad. Resource matching may
be true only for the last model. Matched-comparison readiness may be true only
when resource matching and all lifecycle accounting phases are complete.

Semantic validity remains independent: a functionally correct CPU fallback may
emit a v2 observation with unmatched memory and readiness false. Such a record
is useful functional evidence but cannot enter T-0044 comparison statistics.
No adapter field may infer matching from a configuration name, a successful
program exit, or common ISA semantics.

## Consequences

The current static-Graph smoke is explicitly
`memory_model=owned-private-scratchpads`, with resource matching and comparison
readiness false. Normal cache-backed Rocket/BOOM functional executions, if
added, must identify themselves as cache-backed and remain comparison-ineligible.

T-0042 may proceed with semantic workload and adapter integration without
pretending the T-0044 hardware boundary exists. A separate owned adapter must
give Rocket and BOOM the required scratchpad semantics and verify latency,
ports, functional resources, and lifecycle accounting before readiness can
become true. This ADR authorizes no performance measurement and changes no
patent/IP disposition.
