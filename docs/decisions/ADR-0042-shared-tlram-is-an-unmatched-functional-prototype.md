# ADR-0042: Shared TileLink RAM is an unmatched functional prototype

Status: Accepted
Date: 2026-08-12

## Context

RFC-0005 requires Rocket, BOOM, and the static Graph candidate to use the same
fixed-latency banked scratchpad interface before an isolation comparison.
ADR-0041 prevents semantic success from being treated as resource matching.

Pinned Chipyard's `AbstractConfig` already attaches one 64 KiB subsystem
TileLink RAM scratchpad at `0x08000000`. Both `RocketConfig` and
`SmallBoomConfig` inherit it. This is a smaller functional bridge than creating
separate tile-internal scratchpad fragments, and it avoids the Rocket-only
`WithScratchpadsOnly` rewrite.

The inherited device is not proof of the RFC boundary. Its `TLRAM` advertises a
minimum latency, not constant end-to-end CPU latency. Rocket and BOOM retain
different LSU/cache request paths, while the TileLink fragmenter, buffers,
crossbar, bus coupling, arbitration, and response path may add bubbles or
replay. The owned Graph RTL also still uses distinct register-vector private
storage rather than this interface.

## Decision

Use the inherited subsystem scratchpad only as a T-0042 functional prototype.
Keep code, control data, and `tohost` at `0x80000000`; place only the 324-word
input and private 256-word output at the shared scratchpad base. Require exact
ELF symbol placement and independent validation of all output words on Rocket,
BOOM, and the retained-structure BOOM diagnostic.

Extend the adapter v2 observation vocabulary with
`shared-tilelink-banked-scratchpad-unverified-latency`. This value always keeps
`resource_match_verified=false` and `matched_comparison_ready=false`. The
adapter schema and canonical contract bytes remain v2 because its fields and
required comparison model do not change; only an additional honest actual-
memory state is admitted.

Do not call this prototype fixed-latency, resource-matched, a Graph memory
adapter, or performance evidence. Promotion requires an owned common interface,
cycle assertions proving invariant request-to-response behavior, matched ports
and arbitration, emitted-RTL inspection, complete lifecycle accounting, and a
separately authorized T-0044 measurement contract.

## Consequences

The prototype can show whether both CPU controls access the same pinned
subsystem memory device with the same workload and semantics. It removes the
normal external-DRAM/cache-backed placement as one functional confounder, but
does not remove core-internal memory-system differences or match the Graph RTL.

An upstream `minLatency=1`, successful signature, common address, or common
configuration fragment cannot set resource matching true. No performance,
energy, area, timing, FPGA, silicon, novelty, patent, or freedom-to-operate
claim follows.
