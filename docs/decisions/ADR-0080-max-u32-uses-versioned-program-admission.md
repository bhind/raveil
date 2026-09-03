# ADR-0080: MAX_U32 uses versioned program admission

Status: Accepted
Date: 2026-09-03
Task: T-0143

## Context

T-0140 through T-0142 establish runtime compilation, one-request simulation
and sealed host admission for a bounded Graph language containing only loads,
unsigned wrapping addition and one final store. The fixed five-neighbor
selectors and affine profiles already express a stencil, but addition alone
does not demonstrate a useful nonlinear computation family.

Read-only Librarian, Researcher and Security reviews compared multiplication,
minimum/maximum and comparison/select alternatives. Multiplication adds a
material datapath and overflow contract without a constant mechanism;
comparison/select needs predicates or another operand form; adding both
minimum and maximum violates the one-opcode scope. Unsigned maximum fits the
existing register word and expresses five-neighbor morphological dilation.
These are design-selection facts, not novelty or freedom-to-operate findings.

The existing program payload embeds version 1 in word 1, while the dynamic
request and sealed bundle also name v1 semantics. Silently admitting a new
opcode under those identities would create version confusion even though the
separate program-install transport aperture does not need to change.

## Decision

Add exactly one opcode: `MAX_U32`, opcode 4. It reads the existing source-A
and source-B register fields and writes their unsigned 32-bit maximum to the
existing destination field. It is a fixed-schedule register operation in the
functional RTL contract and adds no memory request, selector, predicate,
constant, branch, loop or scheduler. This is not measured or physical latency
evidence.

Define explicit version-2 program semantics. Version 1 continues to admit
exactly LOAD_U32, ADD_U32 and STORE_U32 with byte-identical encoding and
digest. Version 2 admits those operations plus MAX_U32. The compiler emits v2
only when the descriptor contains MAX_U32. The fixed dynamic host request and
sealed manifest/envelope also use explicit v2 identities for a v2 program.
Python verification, the C++ request reader, C++ fallback and Chisel installer
accept only exact supported request/program version pairs and reject v1 plus
opcode 4, cross-version pairs and unknown opcodes before model construction or
AXI transcript creation.

The `graph_device_program_install_abi_v1` contract remains the transport and
installation ABI: its register map, payload window, identities and 16 KiB
relative aperture do not change. The execution and affine-install ABIs also
remain v1. Newly generated v1 requests and sealed bundles remain verifiable
and replayable under the new implementation; old sealed bundles may still
fail their deliberately exact compiler/source identity check from ADR-0079.

The acceptance descriptor computes an unsigned maximum over center, north,
south, west and east using five loads, four MAX_U32 operations and one final
store. Independent descriptor oracle, transport-neutral C++ fallback and RTL
output must agree, including signed-order discriminators such as
`0x80000000` versus `0x7fffffff`, equal operands, zero and UINT32_MAX.

## Consequences

The bounded Graph path can express one nonlinear morphological/dilation family
without increasing instruction capacity, live registers, affine shape,
address selectors, memory concurrency or execution authority. Every old v1
program remains an exact backward-compatibility regression.

Malformed versions, opcodes, reserved bits, padding, digests, undefined
operands and store placement fail closed before the simulator/AXI boundary;
UIO conversion remains a no-open, no-map, no-MMIO plan. Security and
Performance Reviewers must approve the exact remote implementation head.

Evidence for an actual MAX_U32 simulator replay is RTL Simulation Functional.
Sealing, verification and UIO dry-run remain separately Host Functional.
Instruction and transaction counts are conformance facts; performance is not
measured. No general Graph, CGRA/VLIW, device/UIO, timing, area, energy,
KV260/FPGA, novelty, patent, legal-clearance, ASIC or silicon result follows.
