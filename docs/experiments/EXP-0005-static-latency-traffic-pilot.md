# EXP-0005: Static Graph latency and traffic pilot

Status: In progress
Evidence class: RTL simulation pilot
Date: 2026-08-14
Task: T-0044
Authority: RFC-0004, RFC-0005, ADR-0039, ADR-0046, integration commit
`528fbe28a0dcdfbab65d4ae2995c0876857e053a`
Manifest: `benchmarks/manifests/t0044-static-latency-traffic-pilot-v1.json`
Frozen manifest SHA-256:
`8f51b9947a635c39641a36a5d6e17321a82b38cbcc26f034069e0c1a908e3aa3`

## Falsifiable pilot question

Under the same RFC-0005 semantics and proved-equal owned memory/resource
contract, does the static Graph Executor show a practically relevant exact
execution-cycle or traffic difference from Rocket in-order and BOOM OoO that
is coherent enough to justify the full 1/4/16/64/256 campaign?

This pilot cannot establish the RFC-0005 go or numerical no-go. It remains
partial even if successful because energy, synthesis timing, area, the
VLIW/CGRA-like control, and elastic/stream/hybrid candidates are not measured.
T-0044 therefore stays open.

## Frozen comparison contract

Primary comparison keeps the high-level semantics, memory boundary, port
count, response latency, request capacity, buffering, arbitration, operation
width, and functional resources fixed. Each candidate may use its lawful
implementation optimizations. CPU load reuse is not disabled, Graph's extra
loads are not hidden, and neither CPU is intentionally weakened.

The primary matrix is static Graph, Rocket in-order, and BOOM OoO. BOOM with
serialize-dispatch is a retained-structure same-core diagnostic only and must
not be called an “OoO-disabled CPU”. No secondary operation/load-count ablation
is active. If the primary traffic result later needs decomposition, a secondary
diagnostic must remain separately labelled and cannot replace a primary
baseline.

## Frozen workload and execution boundary

Each sample is the RFC-0005 18x18-input, 16x16-output uint32 five-point stencil.
The exploratory fresh-input versions are deterministic seeds 1, 2, 3, and 4.
Output bytes and intermediates are never reused; only the descriptor may be
reused.

The execution window starts immediately after the final staging response
drains and before any candidate-specific launch or post-staging execution work.
It ends immediately after the final output-write response completes and before
completion bookkeeping. The Graph launch cycle is inside execution. A run
fails closed if this edge meaning cannot be asserted for every matrix member.

## Estimator, inference unit, repetitions, and interval

The checkpoint reports accounts of one and four fresh inputs. For each
candidate it preserves the exact per-input cycle and traffic vectors plus
median, minimum, and maximum. Candidate/Rocket ratios are paired by input and
summarized by their median.

If cycles depend on input version, the inference unit is the fresh input and a
paired percentile-bootstrap 95% interval uses 100,000 resamples from Python's
MT19937 with seed 5005. If all input versions produce the same deterministic
cycle count, the report gives the exact value and replay count without
pretending identical RTL reruns are independent samples. Any 1/4-input
interval is exploratory and not claim-bearing.

## Measurements and availability

Record execution-window cycles; all six lifecycle phases and end-to-end total;
useful load/add/store/output counts; admitted/completed reads, writes, and
bytes; stall and backpressure cycles; configuration, source, artifact,
toolchain, contract, resource, input, oracle, and output hashes. Preserve
currently instrumented frontend, rename/ROB/issue/LSU, and Graph
schedule/control activity. An unavailable activity counter is `null` with a
reason, never an imputed zero. Simulator wall-clock is operations metadata
only and is not CPU performance evidence.

## Stop and decision rules

Fail closed on oracle mismatch, resource inequality, unexplained traffic,
missing required accounting, source/config drift, incomplete pilot matrix, or
different execution-window meaning. Unequal dynamic traffic is not itself a
failure; its cause and interpretation must be reported, but an unexplained
fairness boundary makes the primary result claim-ineligible.

Below 64 fresh inputs this experiment cannot declare the RFC-0005 numerical
no-go. A latency/traffic pilot cannot declare go. The checkpoint ends with one
of `advance`, `pause`, or `early no-go`, while the evidence remains explicitly
partial/pilot.

## Raw evidence and derived report

Raw evidence is written only under ignored
`artifacts/research/EXP-0005/<RUN-ID>/raw/`; derived tables and analysis use the
sibling `derived/` directory. Each sealed run binds commands, environment,
exit codes, source/config/toolchain hashes, and every raw byte hash. A new run
gets a new RUN-ID; raw evidence is never overwritten after sealing.

## Results

No EXP-0005 data existed when this record and manifest were frozen. The
experiment status is in progress only because implementation and collection
follow the immutable preregistration; it is not an unfrozen plan.

## Instrumentation implementation (after freeze, before collection)

The clean-checkout collector is `python3 -m raveil.t0044_pilot collect`; its
exact invocation is documented in `hardware/chisel/README.md`. It refuses an
existing RUN-ID or dirty tracked tree, runs all four variants for seeds 1--4,
captures per-command environment/exit/wall-clock metadata, separates raw and
derived files, and seals raw sizes and SHA-256 hashes. The CPU workload now
binds its deterministic seed at compile time; BOOM serialize-dispatch uses the
same core configuration and explicit CSR diagnostic macro. Graph includes its
one launch cycle in the frozen execution boundary. Owned-boundary request
stall and response-backpressure cycles are explicit markers on both paths.
