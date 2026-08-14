# ADR-0047: Fixture-owned input staging precedes the repeated campaign

Status: Accepted
Date: 2026-08-14

## Context

EXP-0006 proves that static Graph, Rocket, BOOM, and diagnostic BOOM can each
consume four ordered fresh inputs in one simulator process with one reset, one
installation, no artifact reload, exact output oracles, equal owned execution
resources, and complete lifecycle accounting. Its execution-window latency and
traffic view is eligible. The repeated campaign remains paused because its
staging initiator is not implementation-neutral.

The Graph host computes all 324 input words before simulated time advances and
then drives the owned staging interface. The CPU ELF computes each word and
stores it through the candidate core, DCache, and TileLink path. Relabelling
those stores, omitting their cycles, or adding dummy Graph cycles would not
make the work or initiator equal. Adding a Graph-only input generator would
instead add unmatched arithmetic and control resources.

RFC-0005 requires identical input/output staging through the fixed-latency
owned boundary and includes staging in repeated end-to-end accounts. The
measurement fixture, not a candidate, therefore must own fresh-input
generation and staging for every candidate.

## Decision

T-0044 adopts one bounded fixture-owned input-staging provider for the next
repeated-input commissioning:

1. The provider is outside candidate execution and outside the semantic
   oracle. It generates exactly the frozen 324 uint32 words for invocation
   versions 1 through 256 and cannot read candidate output, execution state, or
   oracle output.
2. One candidate invocation request starts staging. The provider issues exactly
   324 ascending full-word writes to owned words `[0,324)`. Each request accepts
   once, completes once under the existing one-module-local-cycle response
   rule, and leaves no pending request.
3. A phase-exclusive mux selects either the provider or candidate at the same
   single physical owned ingress. They can never overlap. It adds no second
   memory port, request buffer, response buffer, outstanding slot, bank, or
   runtime arbitration policy.
4. The final staging response is the only release edge. Before it, CPU/Graph
   data traffic cannot be accepted. After it, the provider cannot issue until
   the next invocation boundary. The existing execution-window start/end edges
   and lawful CPU load reuse remain unchanged.
5. Provider identity, input formula, invocation order, mux/exclusivity,
   accepted/completed counters, port/capacity/buffer/bank/arbitration fields,
   and release rule enter a new common contract and resource identity.
6. CPU installation retains the observed loader writes. Input generation and
   324 staging stores are removed from the CPU ELF; the fixture does not hide
   them in installation, loader, FESVR, Debug, or direct memory mutation.
7. Any provider/candidate overlap, candidate data request accepted before
   release, provider request outside staging, nonascending/missing/duplicate
   write, output access, pending request at release, or identity drift fails
   closed.

This is a controlled research fixture, not a general DMA engine, product input
path, semantic-initiator mechanism, cache, or Graph execution feature. It is
not included in the Graph candidate alone; the same bounded function and
resource contract apply to every primary and diagnostic member.

## Rejected alternatives

- Graph-only candidate-local generation adds unmatched multiplier, shift,
  register, and control resources.
- Treating CPU staging stores as Control by metadata leaves the CPU as their
  real executor and retains candidate-specific instruction cycles.
- Omitting CPU preparation or inserting fake Graph delay hides work rather
  than matching it.
- Loader/FESVR or direct-memory preload hides repeated staging in installation
  or bypasses owned traffic accounting.
- A second candidate-visible port, DMA, buffer, or scratchpad changes the
  compared resource tuple.

## Consequences

EXP-0006 remains immutable completed pilot evidence and its `pause` decision
remains valid for that implementation. EXP-0007 owns the new fixture boundary,
implementation authority, pre-data manifest, negative tests, and replacement
1/4 commissioning. No 1/4/16/64/256 campaign starts until that commissioning
proves the new provider, common resource identity, release edge, oracle, and
full matrix.

The fixture may reduce CPU staging cycles because synthetic input generation
no longer runs on the core. That is an intended removal of measurement-harness
asymmetry, not CPU weakening or a performance conclusion. All phase vectors
must be reported anew. Energy, synthesis timing, area, other Graph
organizations, and general initiator security remain out of scope.

## Implementation note

The accepted boundary is implemented for EXP-0007 with common resource identity
`87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7`.
Actual accepted input words, provider start/release, and validation rearm are
raw evidence rather than verifier-generated assumptions. For invocations after
the first, lifecycle staging includes the interval from the preceding rearm to
release; the nested provider window is separately fixed at 648 cycles. This
keeps candidate control progress in end-to-end accounting while preserving a
common provider boundary. The implementation note is not commissioning data;
EXP-0007 subsequently froze and passed the complete 1/4 matrix. EXP-0008 then
passed the same provider/order/release/rearm/resource boundary for all 256
fresh inputs in each primary and diagnostic session. This verifies the accepted
boundary in RTL simulation; it does not extend the decision to a product DMA,
general semantic initiator, energy, synthesis timing, area, or other Graph
organizations.
