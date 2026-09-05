# ADR-0089: Graph multiplication is explicit versioned uint32 arithmetic

Status: Accepted
Date: 2026-09-05
Task: T-0157
Related: ADR-0084, ADR-0087, ADR-0088

## Context

Dependency scheduling makes bounded Graph descriptors easier to author, but
ADD and MAX alone cannot express a product of two input values. The owner
requested another Graph generalization. A multiplication operation is a
concrete arithmetic extension that can be checked against the existing
descriptor oracle, encoded fallback and offline RTL execution path.

## Decision

Descriptor schema `raveil.graph-device-dag/v3` selects program and dynamic
request version 4. It admits `MUL_U32` as opcode 5 using the binary operation
encoding: destination bits 27:25, source A bits 24:22, source B bits 21:19,
and zero reserved bits 18:0. It computes `(a * b) mod 2^32` with unsigned
operands. This is a product of two value nodes, not an immediate constant.

Version 4 retains version 3's signed relative LOAD encoding and existing
ADD, MAX and final STORE semantics. Older descriptor/program/request versions
retain their bytes and cannot admit opcode 5. New descriptors can reuse
ADR-0088's dependency scheduling and compiler-owned trace validation.

The Python oracle, encoded software fallback, C++ admission/fallback, Chisel
installer and execution core must agree before acceptance. Widen the internal
program-version signal to three bits where required for version 4; the
installed program payload and execution/install MMIO layouts do not change.
Retain the sixteen-instruction and eight-register limits and current input,
output and affine bounds.

Garden's separately admitted explanation versions and sealed UIO support do
not expand in this slice. Unsupported versions continue to fail closed there.
The shared runner's new contract source identities are included in both its
manifest and the sealed path's expected inventory; equality checks are retained.
The editable project dynamic simulation path is the first supported entry.

## Verification and consequences

Check zero, one, maximum operands, overflow, invalid version and reserved-bit
admission. Run a version-4 multiplication Graph and a version-3 control through
one newly built offline simulator and compare full outputs with descriptor
oracle and C++ fallback. Retain new source/RTL/simulator identities and raw
artifacts separately from previous runs.

The combinational multiplication changes the circuit. Passing simulation
establishes functional agreement, not frequency, area, energy or performance.
Timing closure, FPGA mapping and alternative multiplier microarchitectures
require their own subsequent tasks and evidence. This decision makes no
research-gate or physical-device claim.
