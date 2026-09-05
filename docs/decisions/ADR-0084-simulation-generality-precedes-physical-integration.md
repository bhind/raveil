# ADR-0084: Versioned relative loads advance simulation generality before physical integration

Status: Accepted
Date: 2026-09-05
Task: T-0148
Related: ADR-0039, ADR-0064, ADR-0077, ADR-0080

## Context

The owner directed Raveil to finish the compiler-to-RTL path in simulation
before returning to UIO, KV260, FPGA or physical comparison work. The current
dynamic path compiles external DAGs and runs one generic RTL image, but every
`LOAD_U32` still selects one of five hardwired locations: center, north,
south, west or east. This prevents a descriptor from expressing diagonals and
leaves the strongest configurability claim dependent on a fixed stencil
alphabet.

The existing program-installation payload has a 32-bit instruction word,
16-instruction capacity and eight value registers. `LOAD_U32` uses three
selector bits in versions 1 and 2. A table with those bits could name only
eight entries, while a complete 3-by-3 neighborhood has nine coordinates. A
new table installer and AXI namespace would also expand the transport surface
before proving that indirection is useful.

## Decision

Keep descriptor schema v1 and program/request versions 1 and 2 byte-identical.
Add descriptor schema v2 and program/request version 3 for direct signed
relative loads. A version-3 `LOAD_U32` encodes:

- opcode in bits 31:28;
- destination register in bits 27:25;
- signed two's-complement row delta in bits 24:20;
- signed two's-complement column delta in bits 19:15;
- zero in reserved bits 14:0.

Version 3 initially admits only row and column deltas in `[-1, 1]`. This
matches the existing one-cell input halo and makes all nine 3-by-3 coordinates,
including center, representable without another installer or ABI aperture.
Version 1 and 2 continue to interpret bits 24:22 as the fixed five selectors
and require their remaining load bits to be zero. `MAX_U32` remains version-2
or version-3 only. All existing execution, affine-installation and
program-installation transport ABIs remain byte-identical.

T-0148 accepts one exact 16-instruction program using the eight non-center
neighbors: eight loads, seven unsigned maxima and one store. A nine-input
binary reduction would require 18 instructions and is therefore outside the
unchanged capacity; that limit must be reported rather than hidden. The
descriptor oracle, independently validated C++ fallback and RTL output must be
byte-equal through the existing one-build AXI4-Lite Verilator runner.

Simulation-first is now the product critical path until bounded Graph
generality has explicit, runnable discriminators. Physical integration stays
preserved but unscheduled; no simulation result promotes FPGA or silicon
evidence.

The existing sealed/UIO projection remains limited to program versions 1 and
2. Sealing rejects version 3 before creating a bundle; this task does not
extend the physical handoff merely because the simulator accepts relative
loads.

## Consequences

- The first address-generalization slice changes program semantics without
  adding a device register namespace, memory concurrency or scheduler.
- The same RTL image can consume v1 fixed-selector, v2 `MAX_U32`, and v3
  signed-relative programs through versioned fail-closed admission.
- A full nine-input reduction still needs either more instructions or a
  higher-arity operation. That is a later discriminator, not implicit scope.
- Direct relative coordinates are conventional stencil/address-generation
  machinery and are not claimed as novelty. No external implementation is
  copied; CGRA or stencil prior art remains a comparison obligation under
  ADR-0014 and ADR-0049.
- Passing T-0148 establishes RTL Simulation Functional correctness only.
  It establishes no performance, area, timing, energy, arbitrary Graph,
  CGRA/VLIW differentiation, production safety, FPGA, ASIC or silicon result.
- A version-3 descriptor cannot be sealed for the current UIO projection and
  fails before any sealed transport directory is materialized.

## Supersession

ADR-0064 and ADR-0080 remain authoritative for the v1/v2 program and transport
boundaries. This ADR adds v3 semantics and changes the immediate roadmap order;
it does not supersede the retained physical requirements in ADR-0039,
ADR-0071, ADR-0072 or ADR-0076.
