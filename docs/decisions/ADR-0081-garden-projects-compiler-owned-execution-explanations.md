# ADR-0081: Garden projects compiler-owned execution explanations

Status: Accepted
Date: 2026-09-03
Task: T-0144

## Context

T-0140 through T-0143 compile and execute bounded dynamic Graph descriptors
while binding program, request, ABI, simulator, trace, oracle, fallback and
output identities. Those machine-facing artifacts are reviewable, but a human
must currently correlate the descriptor, encoded words, register allocator,
affine configuration and execution receipt across separate files.

Garden already accepts `raveil.garden-snapshot/v1` and presents one owned
Graph/variant slate without execution or decision authority. Reinterpreting a
dynamic descriptor or reconstructing register allocation inside Garden would
create a second compiler and allow the presentation layer to disagree with the
program that actually ran. Reading a live sealed or simulator directory would
also couple the view to mutable execution paths and broaden its filesystem
authority.

## Decision

Preserve `raveil.garden-snapshot/v1` unchanged and add a separate, bounded
`raveil.garden-dynamic-explanation/v1` input. The bounded Graph-device compiler
owns a deterministic lowering trace as part of its compile result. Each trace
entry carries the descriptor node and dependencies, operation and exact
encoded instruction word, assigned value register, definition and last-use
positions, release position, and fan-out consumers. The compiler validates the
trace against the same instruction words and program SHA-256 before returning
it.

The explanation input binds that compiler-owned trace to the descriptor,
program and request identities and to retained source/compiler, ABI, affine,
RTL, toolchain, simulator, AXI trace, oracle, fallback and output identities.
It explicitly classifies the displayed execution evidence, records equality of
oracle/fallback/RTL output, states `performance=not-measured`, and labels
`polls=` as a bounded termination diagnostic rather than cycles or time.

Garden performs strict schema, count, text, identifier, digest, dependency,
instruction, register/lifetime, fan-out, affine, agreement and non-claim
validation. It only projects the accepted trace; it does not allocate
registers, lower nodes, compile a descriptor, execute a program, invoke a
subprocess, or read a sealed/execution tree. Fixture loading remains a bounded
no-follow regular-file operation and rejects symlinks or path escape before
rendering.

The tracked acceptance fixture is a deterministic explanatory snapshot of the
accepted T-0143 cross-dilation result. It retains prior evidence identities;
Garden does not regenerate, promote or strengthen them. T-0144 acceptance is
Host Functional only.

## Consequences

An operator can inspect descriptor topology, fan-out, encoded instructions,
register lifetime and release, affine configuration, execution identity and
agreement evidence in one deterministic read-only view. The compiler remains
the single lowering authority, and inconsistent or tampered explanations fail
closed before display.

The existing Garden view and Graph-device execution paths remain compatible.
Chisel RTL, the C++ executor, device/request/install ABIs, opcode and selector
alphabets, affine profiles, register/instruction capacities, sealed replay and
Linux/UIO behavior do not change.

The displayed instruction, register and transaction relationships are
conformance facts, not measurements. No cycle, latency, throughput, area,
energy, performance, UIO/device, KV260/FPGA, ASIC/silicon, arbitrary/general
Graph, CGRA/VLIW, novelty, patent, freedom-to-operate, legal-clearance or
product-readiness result follows. Garden remains unable to execute, approve,
mutate, promote evidence, close work, or change Project/gate state.
