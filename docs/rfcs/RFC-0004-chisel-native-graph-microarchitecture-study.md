# RFC-0004: Chisel native-graph microarchitecture comparison and transition path

Status: Proposed
Date: 2026-08-11

## Problem

The released T-0103 showcase uses whole host tools/processes as nodes. It is a
useful control-plane illustration but does not test RFC-0001's operation-level
dependency/effect/object graph, CPU frontend work, OoO structures, cache or
pipeline behavior, area, energy, or an ISA. Extending that demo before testing
the microarchitecture hypothesis reverses the necessary research order.

## Proposed design

T-0105 first bootstraps a generic pinned Chisel RTL research environment and
simulator, proves a trivial owned circuit, and attempts one unmodified RISC-V
reference execution. This tooling smoke may precede Graph design because it
does not select or implement a Graph mechanism. T-0057 then freezes one minimal
owned native graph/effect schema and one structured repeated kernel with a
trusted RISC-V fallback. Only then does T-0042 create the owned Graph adapter in
that environment. Chisel constructs hardware; Verilator or another recorded
simulator executes the generated RTL.

Use RISC-V as the first research control because the Chisel ecosystem provides
configurable in-order Rocket and OoO BOOM references. BOOM's documented
OoO-disabled diagnostic may supply a same-core ablation, but it does not replace
a separately configured in-order baseline. Neither core is called ARM-equivalent.

Compare at least:

1. scalar/pipelined in-order RISC-V;
2. conventional RISC-V OoO;
3. same-core OoO-disabled diagnostic where reproducible;
4. static explicit-graph execution;
5. elastic or stream graph execution;
6. hybrid graph plus RISC-V fallback.

Keep workload semantics, compiler inputs, cache hierarchy, memory latency and
bandwidth, functional resources, clock/technology assumptions, and correctness
checks matched or disclose every difference. Measure cycles and useful work;
instruction fetch/decode; branch events; rename, ROB, issue and LSU activity;
I/D-cache and memory traffic; graph configuration, ready/token queues and
backpressure; fallback crossings; synthesized area/timing and energy proxies.
Report one-time installation cost and repeated-run amortization separately.

Only after a graph organization survives that comparison should a transition
prototype evaluate an attached coprocessor interface, custom RISC-V extension,
programmable fabric, or separate ASIC plane. Existing ARM hosts can then test a
software/hybrid executor, but host measurements cannot attribute effects to
OoO, cache, or pipeline internals and cannot establish parity with a current
commercial ARM core.

## Alternatives

- Continue tool/process Command Graph work first: fast to demonstrate but does
  not answer the CPU thesis.
- Build a new CPU from scratch: maximum control, excessive bootstrap and
  verification risk before the graph contract is stable.
- Compare only against a stripped in-order core: useful ablation but an unfair
  primary baseline; conventional OoO must remain in the matrix.
- Start from an ARM core: commercially relevant, but a reproducible open,
  configurable, matched research baseline is not presently established.

## Safety and authority boundaries

Upstream Chisel, Rocket, BOOM, Chipyard, and simulator code remains an external
pinned dependency or read-only reference behind Raveil-owned schemas and
adapters. Exact versions, licenses, notices, source-reuse boundaries, published
mechanisms, patent/standards gaps, and toolchain provenance require Vreji and
Project Manager review before adoption. Open-source availability is not patent
clearance or freedom to operate. No upstream type becomes a Raveil contract.

Simulation, synthesis estimate, FPGA, and silicon evidence remain separate.
Experience is excluded from the first comparison so graph-organization effects
are isolated; it may later advise among already admitted variants.

## Experiments required

1. Schema/semantic-oracle differential tests for one repeated kernel.
2. Matched in-order/OoO/OoO-disabled sanity comparison.
3. Static/elastic/stream/hybrid graph ablation.
4. Cache, memory, width, queue, fallback-rate, and repetition-count sweeps.
5. RTL synthesis estimates with identical library and constraint reporting.
6. Only then, FPGA validation and a separately authorized transition backend.

## Open questions

- Which kernel exposes dependency-discovery cost without predetermining a win?
- Which BOOM/Rocket/Chipyard versions and licenses form a reproducible packet?
- What graph-ready machinery avoids recreating a centralized OoO window?
- Which cache and functional-unit budgets constitute a fair area-normalized
  comparison?
- Is the first transition an attached engine, ISA extension, programmable
  fabric, or separate execution subsystem?
