# RFC-0005: Bounded installed static graph region

Status: Accepted
Date: 2026-08-12
Task: T-0057 phase B
Decision: ADR-0039; bounded repository-owned RTL simulation only

## Purpose and non-claim

This RFC is the first falsifiable low-level Graph contract. ADR-0039 authorizes
only its bounded repository-owned RTL simulation. Neither record selects a
product ISA or claims novelty, performance, energy, area, cost, non-infringement,
or freedom to operate.

The T-0103 Command Graph is not an implementation prototype for this RFC. Its
nodes are host tools or processes; this RFC's nodes are integer and memory
operations below the ISA/software-tool boundary.

## Hypothesis

For one bounded, repeated, affine integer kernel, a compiler can construct and
admission can verify an operation/dependency/effect graph once. Installation
can lower that graph to a fixed schedule that is reused with new input bytes.
The resulting executor may reduce repeated fetch, decode, rename, wakeup, and
issue activity while retaining exact semantics and a normal RV64IM fallback.

The initial candidate deliberately does not attempt general control flow,
dynamic alias discovery, speculative memory issue, token matching, or precise
mid-region architectural exceptions. If those mechanisms are required for the
admitted kernel, the candidate is rejected rather than expanded into a general
OoO engine.

This is an engineering hypothesis about a complete bounded contract lifetime.
Explicit graphs, static scheduling, spatial execution, resident configuration,
attached accelerators, and CPU fallback are prior art and are not proposed as
Raveil inventions.

## Candidate boundary

The candidate is a **bounded installed static region** behind an internal
simulation interface. It is neither a complete CPU nor a custom RISC-V ISA.
The first implementation, if authorized, has these fixed limits:

- one acyclic graph template with at most 64 operation nodes and 128 value or
  effect edges;
- one active invocation and one installed template;
- unsigned 32-bit integer loads, stores, and modular addition only;
- affine addresses over declared object ranges;
- a fixed-cycle schedule over matched integer and scratchpad resources;
- no branch, indirect address, atomics, volatile access, MMIO, coherent shared
  write, system call, floating point, or self-modifying code;
- a declared `max_cycles` no greater than 8,192 for one invocation.

Installation lowers the graph to a cycle-indexed schedule. Execution therefore
has pipeline valid bits and backpressure at the command boundary, but no
content-addressable wakeup, age selection, register rename, speculative issue,
replay queue, reorder buffer, or general load/store queue. There is no runtime
dataflow token store. A later elastic or variable-latency candidate requires a
new contract and IP review; it is not an incremental implementation detail.

## Exact first workload

The only phase-B workload is a single-pass five-point stencil:

```text
input:  A[18][18] as uint32
output: B[16][16] as uint32

B[y - 1][x - 1] =
    A[y][x] + A[y - 1][x] + A[y + 1][x]
            + A[y][x - 1] + A[y][x + 1]  (modulo 2^32)

for y = 1..16, x = 1..16, in row-major semantic order
```

The kernel has 256 output points and no reduction-order ambiguity. It is
intentionally memory-heavy and does not predetermine a Graph win. Each measured
repetition uses a new deterministic input version; neither output bytes nor
intermediate values may be memoized. The descriptor is reused, not the result.

The graph template contains five `LOAD_U32` nodes, four `ADD_U32` nodes, and one
`STORE_U32` node per logical output instance. The bounded iteration controller
instantiates that template over the 16 by 16 affine domain. Address-generation,
loop-control, configuration, and command-completion logic are explicit
accounting categories even when they are not operation nodes.

## Construction and admission

A deterministic compiler pass constructs the graph from a canonical typed SSA
loop representation. A hand-authored graph is not installable. The compiler
emits:

- operation opcode, width, signedness, and modular arithmetic semantics;
- value edges from the unique SSA producer to each consumer input;
- affine address expressions and object/range references for every memory
  operation;
- READ or WRITE effect and required capability for every object access;
- iteration domain, schedule-resource requirements, and maximum cycles;
- schema, compiler, target, and semantic-oracle identities.

The compiler is not trusted to establish safety. An independent admission
validator rejects cycles, missing producers, multiple producers, out-of-range
accesses, unsupported operations, resource overcommit, schedule collisions,
unbounded execution, and any undeclared effect. It recomputes the graph and
effect invariants without using performance data or Experience advice.

## Alias and memory contract

`A` is a read-only input object. `B` is an exclusive, initially unpublished
output object. Admission requires distinct object identities, disjoint physical
scratchpad ranges, exact byte bounds, and unique output addresses. These facts
are checked again when an invocation binds concrete object versions.

The initial executor has no dynamic alias predictor or memory disambiguator.
An unknown or false alias fact, non-affine address, shared writable mapping, or
range mismatch rejects the invocation before start and executes the RV64IM
fallback from the beginning. It is not repaired by speculation or replay.

The isolation comparison gives Rocket, BOOM, and the candidate the same fixed-
latency banked scratchpad interface and counts identical input/output staging.
A separate end-to-end account includes installation, staging, execution,
completion, validation, and publication. Cache-backed and variable-latency
memory are later controls, not silently substituted into this contract.

## Completion, interruption, and publication

The executor cannot modify architectural registers or a published object. It
writes only the private `B` range. On normal completion it reports the private
output version and checksum to trusted host control. The host semantic oracle
must approve the result before the object-version table publishes it.

Cancellation, interrupt request, watchdog expiry, internal error, or failed
validation invalidates the private output and publishes nothing. Software may
then run the RV64IM fallback from the beginning. No partially produced output
is observable, and no graph-machine state is exposed as a precise architectural
restart point. Interrupt latency and discarded work are measured explicitly.

This private-output protocol is not EDGE block-atomic architectural commit and
does not implement a general precise-exception mechanism. That distinction is
an intended narrow boundary, not a patent-clearance conclusion.

## Identity and invalidation

`configuration_id` is SHA-256 over the canonical descriptor bytes, including
schema, operations, dependencies, effects, affine domain, fixed schedule,
resource contract, compiler identity, oracle identity, and target signature.
It does not include input or output data and is not a result-cache key.

Any changed canonical field creates a new identity. An invocation additionally
binds concrete object identities, versions, byte ranges, and capabilities.
Those bindings are checked but do not mutate the installed descriptor. Target,
schema, compiler, validator, or oracle changes invalidate installation.

One-time installation and every reuse are reported separately. Results at
repetition counts 1, 4, 16, 64, and 256 must include configuration and staging
amortization rather than presenting executor-only timing or energy.

## Trusted fallback and oracle

The fallback is a normal RV64IM row-major implementation of the exact modular
kernel. A small host reference computes the same semantics independently. In
functional testing every candidate output must equal both references byte for
byte for boundary patterns, deterministic generated inputs, cancellation, and
rejected-binding cases.

The fallback is part of the first system and therefore remains in total area,
static-power, and cost accounting. An attached candidate cannot support a die-
shrink or lower-cost claim merely by reporting its active island separately.

## Matched controls and accounting

T-0044 must compare at least Rocket in-order, BOOM OoO, a reproducible BOOM
OoO-disabled diagnostic, the proposed static executor, and an admitted
VLIW/CGRA-like control. Workload bytes, arithmetic, scratchpad ports and
latency, functional-unit count, clock and technology assumptions, staging,
compiler optimization level, correctness checks, and repetition counts are
matched or the difference is disclosed.

Report separately:

- correct cycles and useful operations;
- fetch/decode/register, rename/ROB/issue/LSU, and Graph schedule/control
  activity;
- scratchpad and external-memory traffic;
- installation, staging, execution, drain, validation, and fallback cost;
- whole-system and partitioned synthesized area, timing, and static/dynamic
  energy proxies;
- interrupt/cancel latency and discarded work.

Simulation, synthesis estimates, FPGA, and silicon remain distinct evidence
classes. No Apple Silicon or other host timing is evidence about CPU internals.

## Pre-registered no-go rule

The numerical values below are engineering decision thresholds, not measured
facts. They may be changed only before T-0044 data collection, with a recorded
reason and superseding contract.

The candidate is no-go if any of these occurs:

1. any accepted invocation differs from either semantic reference;
2. implementing the admitted workload requires general rename, associative
   wakeup/age selection, speculative alias recovery, a ROB, or a general LSU;
3. at 64 fresh-input invocations, the upper bound of the recorded 95% interval
   for total dynamic-energy-proxy ratio versus matched Rocket is greater than
   0.90, after installation, staging, completion, and validation;
4. at the same point, the upper bound of the 95% interval for correct-latency
   ratio versus Rocket is greater than 1.05;
5. configuration does not break even by 64 invocations, or a claimed benefit
   depends on reusing result bytes, hiding fallback, omitting staging, or giving
   the candidate unmatched memory or functional resources;
6. the candidate cannot meet the same synthesis timing constraint, or its
   incremental logic area exceeds 25% of the matched Rocket core area;
7. the mechanism-specific IP review keeps an adopted feature blocked.

Failure is retained as useful evidence. No automatic pivot to elastic tokens,
larger regions, result caching, or a custom ISA is allowed after a no-go.

## Prior-art and IP disposition

Primary-source review establishes that compiler-formed explicit dependencies,
bounded blocks, direct consumer communication, resident dataflow instructions,
static routes, phase reuse, and attached CPU accelerators already exist. In
particular:

- TRIPS/EDGE is close prior art for bounded compiler graphs, direct
  dependencies, memory-order identifiers, and block commit;
- WaveScalar is close prior art for resident instruction graphs and data-driven
  firing;
- DySER is close prior art for compiler-extracted repeated regions, statically
  routed functional units, and a retained conventional processor;
- EPIC/VLIW and spatial CGRAs are prior art for compiler scheduling and fixed
  resource mappings.

This draft avoids direct-consumer ISA fields, runtime token firing, wave memory
ordering, multi-modal issue selection, and graph-side architectural precise
commit. It still uses a resident static configuration and a hybrid fallback,
so technical similarity remains high. Avoidance is not non-infringement.

US7490218B2, US10824429B2, and WO2015069583A1 remain discovery-only patent
risks. Their claims, families, legal status, jurisdictions, ownership,
licensing, expiry, and applicability have not been reviewed. No Graph RTL may
copy external RTL/compiler source, and this RFC is not implementation
clearance. A concrete claim-to-feature review and, before use beyond bounded
research simulation, qualified legal advice remain required.

## Recorded review outcome

The Project Manager must record one of three outcomes:

1. accept this narrow research contract and a mechanism-specific IP disposition
   for simulation only;
2. revise it before any measurement or RTL; or
3. stop the CPU/Graph path as no-go.

ADR-0039 records outcome 1 for bounded repository-owned RTL simulation only.
T-0057 remains open through functional validation, and T-0042 may implement
only this contract. T-0044 measurement remains separately gated.
