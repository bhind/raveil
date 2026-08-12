# ADR-0039: Bounded static region is simulation-only

Status: Accepted
Date: 2026-08-12

## Context

T-0057A found high prior-art similarity to TRIPS/EDGE, WaveScalar, DySER,
EPIC/VLIW, and spatial CGRA mechanisms. RFC-0005 then proposed one much narrower
candidate: an operation-level five-point stencil lowered to a fixed schedule,
with disjoint scratchpad objects and normal RV64IM fallback. T-0042 cannot begin
until the Project Manager records accept, revise, or stop and fixes the
mechanism-specific IP boundary.

The user directed the project to continue. This direction accepts research
execution, not a novelty, patent, product, or performance claim.

## Decision

Accept RFC-0005 only for bounded repository-owned RTL functional simulation.
T-0042 may implement the exact fixed-schedule stencil candidate behind an
internal test interface.

The candidate must not include runtime dependency-ready or token issue, direct
consumer-target instruction fields, wave identifiers or wave-ordered memory,
dynamic alias speculation, a general LSU, register rename, ROB, commit
frontier, precise mid-region restart, multiple issue modes, custom ISA, or
candidate-local OoO/in-order switching. Fault or cancellation invalidates an
unpublished output; software restarts the RV64IM fallback from the beginning.

Implementation is repository-owned and must not copy external Graph/dataflow
RTL or compiler source. Rocket and BOOM remain separately pinned comparison
controls, not candidate implementation sources or switchable candidate modes.

The T-0057B feature-to-document review remains non-legal and fail-closed. It
records differences from inspected claims but establishes no claim
construction, non-infringement, legal status, license, research exemption, or
freedom to operate. FPGA, silicon, product use, commercial distribution,
external implementation reuse, or any excluded mechanism requires a new
Project Manager review and qualified legal escalation.

## Consequences

RFC-0005 becomes Accepted and T-0042 may start. T-0057 remains open until the
schema and executor receive functional evidence; T-0044 remains a separate
measurement task and no performance collection is authorized by this ADR.

The first T-0042 evidence may prove only deterministic RTL behavior and exact
agreement with an independent software oracle. It cannot support energy,
latency, area, OoO-removal, CPU, ISA, FPGA, silicon, novelty, or patent claims.

Any implementation pressure that requires an excluded dynamic mechanism is a
no-go under RFC-0005, not permission to expand the design.
