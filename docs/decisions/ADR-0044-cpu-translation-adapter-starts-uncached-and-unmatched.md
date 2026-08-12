# ADR-0044: The first CPU translation adapter is uncached and unmatched

Status: Accepted
Date: 2026-08-12

## Context

ADR-0043 defines an owned, attributed local scratchpad contract and connects
the static Graph region to private instances. The next T-0042 step is to show
that the pinned Rocket and BOOM systems can reach a Raveil-owned TileLink
manager without editing either upstream core. That is a translation and
integration question, not yet the RFC-0005 equal-resource comparison.

The inherited 64 KiB memory-bus TLRAM is cacheable through the inclusive-cache
path. Replacing it directly with a manager advertised as idempotent is not a
valid TileLink topology: the inclusive cache tries to add coherent acquire
support while the manager remains non-cacheable. Advertising the new manager
as cacheable would elaborate, but CPU stores and refills could then be hidden
by caches and would not establish the owned request-level accounting needed by
ADR-0043.

## Decision

Add a repository-owned Chipyard overlay that removes the inherited scratchpad
configuration and exposes a 32-bit, maximum-one-outstanding TileLink manager at
the same data base `0x08000000`, plus a bounded control page at `0x08010000`.
For the first adapter milestone, attach this manager to the uncached peripheral
bus. An access to this mapped region is intended to traverse the owned manager,
which keeps the translation boundary observable, but CPU execution remains
unverified and the topology deliberately does not match the Graph memory
resource or the former memory-bus path.

The manager accepts post-fragmenter `Get`, `PutFull`, and `PutPartial`
transactions, preserves TileLink source and size into the response, supports
byte masks, may deny invalid phase-register writes, and holds each response
until D-channel consumption. Its control page supplies a software-declared
lifecycle phase and aggregate per-phase read/write counters. This phase is an
adapter label, not proof of the actual initiator or of CPU-only activity.
The overlay is not yet an ADR-0043 common-contract adapter: it neither carries
owned initiator/phase metadata in each request and response nor establishes
correlated CPU attribution.

First require exact Rocket and BOOM RTL elaboration from the pinned Chipyard
checkout in an ephemeral source copy. Elaboration evidence must report program
execution not run, initiator attribution unverified, resource matching false,
comparison readiness false, and performance not measured. A later CPU
functional smoke must exercise full and partial writes, masks, invalid phase
rejection, D-channel backpressure, phase fences, counters, and workload output
before this is called a functional CPU adapter. It must also determine how to
separate CPU activity from any loader, debug, or recovery master.

Do not promote this peripheral-bus adapter to the RFC-0005 common memory. A
later design must match CPU and Graph ports, arbitration, buffering, memory
semantics, staging, attribution, and complete lifecycle accounting before
T-0044 measurement may begin.

## Consequences

The uncached step is intentionally slower and structurally different from the
candidate comparison resource. Its purpose is to make translation behavior
testable without cache effects, not to produce a favorable benchmark. A
successful elaboration proves only that the pinned Rocket and BOOM topologies
can contain the owned manager.

Moving the manager to a memory bus, making it cacheable, adding more outstanding
transactions, or deriving initiator identity requires new functional evidence
and may require a superseding decision. No latency, throughput, energy, area,
timing, FPGA, silicon, OoO-removal, novelty, non-infringement, or freedom-to-
operate conclusion follows.

The overlay reuses pinned Chipyard/Rocket Chip TileLink and diplomacy APIs
under their recorded licenses; it copies no external Graph/dataflow RTL or
compiler mechanism. Generic TileLink translation, byte masks, MMIO phase
registers, and transaction counters are established interface engineering and
are not a novelty basis. Existing patent-family, transitive-license, and FTO
gaps remain unreviewed.
