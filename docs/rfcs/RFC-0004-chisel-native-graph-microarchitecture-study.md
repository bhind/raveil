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
does not select or implement a Graph mechanism.

T-0057 has two ordered phases. Phase A records a locator-backed direct-prior-art
matrix and preliminary patent/IP triage covering at least conventional OoO,
EPIC/VLIW, TRIPS/EDGE, WaveScalar, DySER and spatial CGRA designs. Phase B then
freezes one minimal owned native graph/effect schema and one structured repeated
kernel with a trusted RISC-V fallback. Only after both phases are reviewed does
T-0042 create the owned Graph adapter in that environment. Chisel constructs
hardware; Verilator or another recorded simulator executes the generated RTL.

The matrix separates comparison controls from mechanisms proposed for adoption.
An in-order core, an OoO core and valid diagnostics are controls chosen to
falsify the Raveil hypothesis; they are not copied architecture designs.
Explicit dependency graphs, compiler-created atomic blocks, direct
producer-consumer targets, resident graph instructions, static spatial routes,
token readiness, local memories and hybrid CPU fallback are already prior-art
mechanism classes. No RFC-0004 text may imply that those classes are Raveil
novelty.

Use RISC-V as the first research control because the Chisel ecosystem provides
configurable in-order Rocket and OoO BOOM references. BOOM's documented
OoO-disabled diagnostic may supply a same-core ablation, but it does not replace
a separately configured in-order baseline. Neither core is called ARM-equivalent.

Compare at least:

1. scalar/pipelined in-order RISC-V;
2. conventional RISC-V OoO;
3. same-core OoO-disabled diagnostic where reproducible;
4. static explicit-graph execution;
5. an independently sourced or faithfully reproduced VLIW/CGRA-like control;
6. elastic or stream graph execution;
7. hybrid graph plus RISC-V fallback.

Keep workload semantics, compiler inputs, cache hierarchy, memory latency and
bandwidth, functional resources, clock/technology assumptions, and correctness
checks matched or disclose every difference. Measure cycles and useful work;
instruction fetch/decode; branch events; rename, ROB, issue and LSU activity;
I/D-cache and memory traffic; graph configuration, ready/token queues and
backpressure; fallback crossings; synthesized area/timing and energy proxies.
Report one-time installation cost and repeated-run amortization separately.

ADR-0049 adds a non-reinvention gate after the already frozen static-candidate
experiments. The current source-coded stencil FSM is a specialized accelerator
reference, not a configurable CGRA or general Graph executor. Any successor
that loads schedules, routes operations over configurable functional units, or
fires nodes from readiness enters existing VLIW/CGRA/dataflow mechanism classes
and must be named and compared accordingly. It cannot advance from a fixed-FSM
result alone.

The gate requires one source/revision/license/provenance-verified public
configurable control, at least three semantically distinct graphs through one
candidate interface without Chisel/RTL regeneration, the same owned
contract/effect/fallback behavior on CPU and configurable backends, and complete
compiler/configuration/PPA accounting. If a reviewed existing backend supplies
the execution mechanism without losing the contract lifecycle, custom hardware
is no-go and Daphnis uses that backend behind an adapter.

Only after a graph organization survives that comparison should a transition
prototype evaluate an attached coprocessor interface, custom RISC-V extension,
programmable fabric, or separate ASIC plane. Existing ARM hosts can then test a
software/hybrid executor, but host measurements cannot attribute effects to
OoO, cache, or pipeline internals and cannot establish parity with a current
commercial ARM core.

The candidate itself is not yet selected. T-0057 must state node granularity,
dependency/alias producer, ISA visibility, memory ordering, precise exception
and commit semantics, cancellation/rollback, resource bounds, configuration
identity and invalidation, fallback, semantic oracle, and a no-go rule. It must
also explain how graph-ready state differs from merely renaming a ROB, issue
window, scoreboard or replay mechanism. Until then, “static”, “elastic”,
“stream” and “hybrid” are alternatives to investigate, not implementation
instructions.

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

Existing frontends and interchange/compiler infrastructure are the default
entry path. Raveil may add thin identity, effect, object/version, resource,
provenance, validation, and backend-lowering passes, but the study must not
make a new Raveil-only source language, forked optimizer, or end-to-end closed
toolchain a prerequisite when an adapter can preserve the owned contract.
Kernel/OS admission and publication authority stay outside configurable
hardware; a mapper result or hardware completion is evidence, not authority.

Simulation, synthesis estimate, FPGA, and silicon evidence remain separate.
Experience is excluded from the first comparison so graph-organization effects
are isolated; it may later advise among already admitted variants.

The T-0057 review identified high technical similarity to TRIPS/EDGE,
WaveScalar and DySER, plus preliminary patent-family hits around WaveCache,
explicit-dataflow commit/precise exceptions and multi-modal EDGE instruction
issue. Those results are discovery metadata only, not legal conclusions.
Direct adoption of those mechanisms is blocked until the exact proposed feature
is compared with source and patent claims and the Project Manager records the
required disposition. Qualified legal review is required before any conclusion
beyond research-context similarity or before an FTO claim.

## Experiments required

1. Complete T-0057 phase A prior-art and IP-risk review; this is research input,
   not an experiment result.
2. Accept a falsifiable T-0057 phase B schema/comparison contract and stopping
   rule before Graph RTL or performance collection.
3. Schema/semantic-oracle differential tests for one repeated kernel.
4. Matched in-order/OoO/OoO-disabled sanity comparison.
5. Public VLIW/CGRA/dataflow control reproduction with separate source-license
   and patent/IP status.
6. Three-graph no-RTL-regeneration configurability and CPU/backend contract
   parity test.
7. Static/elastic/stream/hybrid graph ablation only for admitted candidates.
8. Cache, memory, width, queue, fallback-rate, and repetition-count sweeps.
9. RTL synthesis estimates with identical library and constraint reporting.
10. Only then, FPGA validation and a separately authorized transition backend.

## Open questions

- Which kernel exposes dependency-discovery cost without predetermining a win?
- Which contract-lifetime and authority properties remain useful after the
  execution substrate is treated as an existing CGRA/VLIW/dataflow mechanism?
- Which public configurable implementation is the smallest reproducible,
  license-reviewable T-0044 control and possible adapter backend?
- Which BOOM/Rocket/Chipyard versions and licenses form a reproducible packet?
- What graph-ready machinery avoids recreating a centralized OoO window?
- Which cache and functional-unit budgets constitute a fair area-normalized
  comparison?
- Is the first transition an attached engine, ISA extension, programmable
  fabric, or separate execution subsystem?
