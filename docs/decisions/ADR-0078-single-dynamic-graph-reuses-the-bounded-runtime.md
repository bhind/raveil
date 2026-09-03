# ADR-0078: A single dynamic Graph reuses the bounded simulation runtime

Status: Accepted
Date: 2026-09-03
Task: T-0141

## Context

ADR-0077 proves that one catalogue descriptor and one non-catalogue descriptor
can configure the existing Graph-device executor through one generated and
compiled simulator. Its operator command and both shell runners require exactly
two requests. That cardinality is useful for proving simulator reuse, but it
also forces an operator who wants to execute one newly compiled Graph to supply
an unrelated catalogue Graph.

The missing operator behavior does not require another request schema, runner,
simulator, Graph catalogue entry, opcode, selector, affine profile, capacity,
RTL module or device ABI. Nor does it require a persistent simulator service or
a Linux/UIO transport decision.

## Decision

Add `graph-device dynamic-run` for exactly one repository-relative descriptor
and one uint32 seed. The descriptor must be outside the frozen catalogue. It is
validated and compiled before the lower runner starts, using the same bounded
compiler, fixed host request and existing baseline or compact affine profile as
ADR-0077.

Keep `dynamic-run-pair` byte- and behavior-compatible. Generalize the existing
outer and in-container dynamic shell runners only enough to accept either one
request root named `request-1` or the existing ordered `request-1` and
`request-2` siblings. The lower runner emits RTL once, builds one simulator
once, and invokes it once per admitted request. No third cardinality or
concurrent execution is accepted.

The single command requires the RTL output, independent descriptor oracle and
transport-independent C++ program fallback to be byte-equal. Its append-once
receipt binds the descriptor, compiled program, fixed request, generated source
snapshot, ABI, RTL, toolchain, simulator, complete AXI transcript, oracle,
fallback and output identities. Malformed request evidence must be rejected
before constructing the Verilated model or creating an AXI transcript.

The single-run marker reports structural functional facts only: one request,
one RTL emission, one simulator build and one invocation. `polls=` remains a
host termination diagnostic and is not a cycle, time, latency or throughput
measurement.

## Consequences

An operator can execute one bounded non-catalogue Graph without carrying an
unrelated catalogue request, while the pair command continues to prove reuse
across two programs. The additional fan-out fixture exercises five
simultaneously live values and repeated use of an intermediate without changing
the compiler or execution alphabet.

Descriptor sealing, hostile filesystem-race resistance and Linux/UIO
conversion remain a separate decision. This task does not add a cache, daemon,
batch scheduler, dynamic scheduling, variable latency, loop, branch, DMA or
coherence behavior.

Evidence remains RTL Simulation Functional only. Instruction and live-value
counts are compiler conformance facts, not performance measurements. This
decision establishes no general-Graph, performance, timing, area, energy, UIO,
KV260, FPGA, ASIC, silicon, product-readiness, novelty, patent or legal-clearance
claim.
