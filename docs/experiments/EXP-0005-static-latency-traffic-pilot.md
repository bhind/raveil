# EXP-0005: Static Graph latency and traffic pilot

Status: Completed
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

The preregistration commit is `d932b304cdf75910da1cff708f7a1c2540a4fdbb`
and the collection source commit is
`6733c44b9ae1b934fcce30c50f24d8d2654f002f`. The successful RUN-ID is
`20260814T053159Z-6733c44-pilot2`. All 16 commands exited zero. The sealed raw
directory, derived report, and their hashes are:

- `artifacts/research/EXP-0005/20260814T053159Z-6733c44-pilot2/raw/`;
- `artifacts/research/EXP-0005/20260814T053159Z-6733c44-pilot2/derived/report.json`,
  SHA-256 `4e24e4f6a396ba9887503e36c359802226fb12f5e1152dc455b281ca5bd9effa`;
- `artifacts/research/EXP-0005/20260814T053159Z-6733c44-pilot2/raw-seal.json`,
  SHA-256 `a314a2e3196e72fcd2fe8f445972d87691e69c8218d8a1e8583e72783354958b`.

The four input hashes and four independent-oracle/output hashes are distinct
by seed. For each seed, all matrix members have the same input, oracle,
observed output, descriptor, contract, adapter, and resource hashes. Every
oracle comparison passes; the common resource SHA-256 is
`16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748`.
The report cross-verifies resource equality, complete matrix membership,
same-meaning windows, quiescence, traffic conservation, and zero unaccounted
or pending execution traffic.

All four fresh inputs produced the same deterministic cycle and traffic
vectors, so the frozen exact-value rule applies. The four identical cycle
observations are reproducibility across distinct input versions, not four
independent reruns of one input. No bootstrap interval is constructed.

| Candidate | Role | Execution cycles (each of 4) | Rocket-relative ratio | Reads / writes | Total transactions |
|---|---|---:|---:|---:|---:|
| static Graph | primary | 3,073 | 0.210177 | 1,280 / 256 | 1,536 |
| Rocket in-order | primary | 14,621 | 1.000000 | 800 / 256 | 1,056 |
| BOOM OoO | primary | 21,892 | 1.497298 | 800 / 256 | 1,056 |
| BOOM serialize-dispatch | diagnostic only | 70,898 | 4.849053 | 800 / 256 | 1,056 |

For this bounded execution window, Graph takes 4.758x fewer cycles than Rocket
and 7.124x fewer than BOOM while admitting 1.455x as many memory transactions
as either CPU. These are RTL-simulation pilot observations, not CPU/ISA,
energy, timing, area, FPGA, ASIC, or silicon conclusions. BOOM
serialize-dispatch retains rename, ROB, issue, and LSU structures and is not an
“OoO-disabled CPU”.

| Candidate | Installation | Staging | Execution | Drain/completion | Validation | Publication | End-to-end total |
|---|---:|---:|---:|---:|---:|---:|---:|
| static Graph | 0 | 648 | 3,073 | 1 | 512 | 0 | 4,234 |
| Rocket in-order | 44,630 | 3,865 | 14,621 | 410 | 16,513 | 0 | 80,039 |
| BOOM OoO | 44,761 | 4,208 | 21,892 | 425 | 16,513 | 0 | 87,799 |
| BOOM serialize-dispatch | 45,137 | 22,288 | 70,898 | 498 | 16,513 | 0 | 155,334 |

Every candidate performs 1,280 useful loads, 1,024 useful adds, 256 useful
stores, and 256 outputs. Graph converts each useful load into one owned-memory
read; optimized CPU code legally reuses loads and emits only 800 owned-memory
reads. All candidates emit 256 writes. Read/write byte counts are 5,120/1,024
for Graph and 3,200/1,024 for each CPU. Admitted and completed counts agree;
request-stall and response-backpressure cycles are zero. Graph reports 3,072
schedule-active cycles plus one launch cycle. Current CPU frontend and
rename/ROB/issue/LSU counters remain unavailable and are not imputed as zero.

### Fairness and claim eligibility

The unequal traffic is explained and remains a primary design result. The CPU
baselines retain lawful load reuse, the admitted Graph schedule retains five
loads per output, and neither CPU is weakened. The primary result is therefore
eligible as a bounded execution-latency/traffic pilot. No matched-load
secondary ablation was needed or activated.

End-to-end reuse amortization is not eligible. These fresh-process runs repeat
CPU installation while Graph is elaboration-installed. Before expanding to
the 1/4/16/64/256 invocation accounts, one installed configuration must accept
repeated fresh inputs without simulator reboot and apply one lifecycle meaning
to every candidate. This is the experiment's only pause point.

Decision: **pause**. The pilot does not decide RFC-0005 go, cannot decide its
numerical no-go below 64 fresh inputs, and remains partial because energy,
synthesis timing, area, and the remaining Graph organizations are absent.
No architecture invariant or accepted design boundary changes, so this result
updates EXP/governance records without rewriting accepted ADR-0046.

### Run history and estimate reconciliation

The first RUN-ID, `20260814T053015Z-6733c44-pilot1`, is retained as failed raw
evidence. Graph seed 1 exited zero, then Rocket exited one because the dedicated
worktree did not expose the already pinned Chipyard checkout at the wrapper's
expected ignored `external/` locator. No measurement claim uses that run.

The successful matrix took 0.608 hours of operations wall-clock from first
command start to last command end. The first fresh-input account exposed the
cold source rebuild: Rocket took 12.05 minutes and BOOM 12.95 minutes; after
that, individual warm runs took about 0.64--1.14 minutes. This updated the
post-first-run completion estimate to tens of minutes for the remaining matrix
plus a bounded record/verification pass. Wall-clock remains operational
planning evidence only. The actual parser defect was found only after all 16
runs: fixed-width RTL decimal padding was rejected. Commits `9205350` and
`a8eed2f` add strict whitespace parsing and resumable single-use sealing without
changing raw logs or the frozen manifest.

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
