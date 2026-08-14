# ADR-0046: Controlled-run matched comparison precedes token hardening

Status: Accepted
Date: 2026-08-14

## Context

T-0042 exists to make the first bounded Rocket, BOOM, and static-Graph RTL
comparison possible. The functional workload, independent oracle, common
record schema, owned local-memory contract, CPU translation target, structural
traffic classifiers, and one positive BOOM store-token transport witness now
exist. No matched comparison has run because the CPU and Graph paths still do
not share a proved-equal resource boundary.

ADR-0045 correctly rejects TileLink source, DCache origin, software phase, and
request acceptance as general semantic identity. It then made complete
CPU-specific token lifecycle coverage a prerequisite for connecting the common
adapter. That ordering is appropriate for an untrusted, multi-client product
runtime, but it is stronger than the first controlled RTL experiment needs.
Continuing to enumerate replay, reset, epoch, duplicate, exception, loader, and
Debug cases before resource matching would optimize the diagnostic boundary
instead of testing the Graph microarchitecture hypothesis.

## Decision

T-0042 returns to a small-start exit contract. It closes when one reproducible
RTL-simulation path demonstrates all of the following:

1. Rocket, BOOM, and the admitted static Graph candidate execute the same
   frozen RFC-0005 workload and pass the same independent semantic oracle.
2. Their measured execution regions use one implementation-neutral owned
   memory contract with explicitly equal port count, request capacity,
   buffering, arbitration, byte width, and module-local response rule.
3. A deterministic harness establishes quiescence before the execution window,
   brackets its start and end, and rejects or marks comparison-ineligible any
   run containing unaccounted traffic in that window.
4. The common record contains complete installation, staging, execution,
   completion, validation, and publication accounting, immutable input/source/
   configuration identities, and an explicit resource-match result.
5. Attribution remains honest and bounded: controlled-run membership may
   identify traffic for this exact experiment, but no per-operation token,
   source ID, origin bit, PC, or software marker is promoted into a general
   semantic-initiator or security claim. Unknown or mixed traffic fails closed
   to a comparison-ineligible record.

T-0042 does not require new coverage for reset with outstanding work, stale or
duplicate epochs/tokens, sequence exhaustion, every replay path, every
post-request exception or post-A rollback, arbitrary ELF identity, general
loader/FESVR/Debug exclusion, multi-live-token operation, or complete Rocket/
BOOM lifecycle-signal parity. Existing evidence remains retained and may be
reused; these cases no longer gate the first matched comparison.

T-0106 owns that deferred hardening. It may begin only after T-0044 shows that
the candidate survives the first matched comparison, or after a separately
accepted product requirement introduces untrusted or concurrent initiators.
T-0106 preserves ADR-0045's token and fail-closed lifecycle semantics.

This decision supersedes ADR-0045 only where ADR-0045 made exhaustive token
lifecycle coverage a prerequisite for T-0042 closure, common-adapter
connection, or T-0044 entry. ADR-0045 remains authoritative for any later
claim of general CPU semantic attribution. ADR-0043's resource-equality
requirements and ADR-0041's separation of semantic correctness from matched
resources remain unchanged.

## Consequences

The next implementation work is the smallest CPU/Graph connection to the
ADR-0043 owned resource boundary plus complete controlled-window accounting.
It is not another token-negative diagnostic. A partially implemented
hardening test may be retained as evidence, but finishing it is optional and
must not delay the common-resource slice.

T-0044 may start immediately after the five T-0042 exit conditions pass. Its
first result remains RTL-simulation evidence only. No CPU, ISA, performance,
power, area, FPGA, silicon, novelty, infringement, patent-clearance, or FTO
claim follows from this sequencing decision.

