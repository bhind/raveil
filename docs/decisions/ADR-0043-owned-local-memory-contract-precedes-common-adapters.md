# ADR-0043: An owned local memory contract precedes common CPU/Graph adapters

Status: Accepted
Date: 2026-08-12

## Context

RFC-0005 requires Rocket, BOOM, and the static Graph candidate to use the same
fixed-latency banked scratchpad interface before T-0044 may compare them.
ADR-0041 separates functional correctness from resource matching, and
ADR-0042 keeps the inherited subsystem TLRAM as an unmatched functional
prototype.

The passive TLRAM observer found a one-cycle interval at the bank-local
post-fragmenter endpoint in one pinned run, but it cannot identify whether a
request came from CPU execution or FESVR recovery, cannot label a lifecycle
phase, and did not observe a write beat. The owned Graph RTL has only private
register-vector storage and no request/response protocol. Connecting either
side directly to another inherited bus would therefore preserve the ambiguity
rather than define the comparison boundary.

## Decision

Introduce a Raveil-owned, implementation-neutral local scratchpad transaction
contract before writing CPU or Graph adapters. Its first implementation is a
single-client, maximum-one-outstanding module with:

- decoupled request and response valid/ready handshakes;
- explicit read/write operation, word address, 32-bit data, and four-bit byte
  mask;
- bounded initiator and lifecycle-phase attribution carried into the response;
- deterministic error responses for out-of-range or disallowed operations;
- accepted, completed, request-stall, response-stall, and pending accounting;
- one-cycle response availability after request acceptance, with response
  fields held stable until consumption.

The one-cycle statement is a module-local RTL protocol property. It is checked
with emitted-RTL assertions and a Verilator functional harness, but it is not
an end-to-end CPU or Graph latency measurement. The first module remains
`resource_match_verified=false` and `matched_comparison_ready=false`.

Adapt the static Graph region to this contract next, using disjoint input and
private-output bank instances and preserving validation-before-publication.
Then adapt the pinned CPU controls to the same contract with explicit staging,
execution, completion, and validation attribution. Only a later proof of
identical ports, arbitration, buffering, latency, functional resources, and
complete lifecycle accounting may promote the memory model to the RFC-0005
matched state.

## Consequences

The contract makes read/write coverage and source/phase attribution testable
without importing TileLink, Rocket, BOOM, or another upstream type into the
owned boundary. It also gives the Graph and CPU paths a common target while
allowing their adapters to be implemented and rejected independently.

The initial one-outstanding implementation is intentionally conservative and
may reduce throughput. It is not a claim that one port, one-cycle local
response, or this arbitration policy is optimal. Changing to multiple
outstanding requests, variable latency, dynamic scheduling, or a different
bank/port organization requires a superseding decision and renewed mechanism-
specific prior-art/IP review.

Generic ready/valid plumbing, banked scratchpads, byte masks, and transaction
accounting are established interface engineering and are not a novelty basis.
No external Graph/dataflow RTL or compiler implementation is copied. Existing
TRIPS/EDGE, WaveScalar, DySER/CGRA, patent-family, transitive-license, and
freedom-to-operate gaps remain unreviewed; this decision provides no patent or
legal clearance.
