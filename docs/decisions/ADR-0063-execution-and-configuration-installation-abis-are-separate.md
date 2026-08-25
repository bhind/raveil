# ADR-0063: Execution and configuration-installation ABIs are separate

Status: Accepted
Date: 2026-08-25
Task: T-0123

## Context

T-0122 fixed a task-neutral Graph-device execution ABI around control, status,
324 input words, 256 private output words, and artifact/configuration identity.
T-0123/S01 preserved that byte layout while observing the fixed executor's
accepted memory requests. S02 must admit more than one bounded affine
shape/stride configuration without turning execution registers into a
partially written configuration store or silently changing the accepted ABI.

The fixed physical windows also constrain the meaning of a smaller shape. A
compact active region cannot fill all 256 output words. Publishing stale words
from an earlier invocation would violate the private-output boundary even when
the active values were correct.

## Decision

`raveil.graph-device-abi/v1` remains byte-identical and continues to own only
execution control, status, staging, private-output validation, and identity
readback. T-0123/S02 adds a separate fixed-width, little-endian, pointer-free,
word-addressed configuration-installation ABI. It accepts an ordered bounded
payload only while execution and owned memory are idle. Clear, sequential
write, and commit form one fail-closed installation transaction; incomplete,
misordered, out-of-range, identity-mismatched, or busy-time mutation faults and
cannot authorize execution.

The first admitted profiles are the existing 16-by-16 output with input/output
row strides 18/16 and a compact 8-by-8 output with strides 10/8. Both retain
the 324-word input and 256-word private output windows. Reset restores the
baseline configuration and zeros the simulation scratchpad. Each nonbaseline
run resets before installation, so every inactive private-output word is known
zero before output-valid can authorize the complete fixed window.

The implementation identity/configuration tag remains distinct from the
installed configuration digest. The existing execution ABI keeps its fixed
configuration-identity words unchanged. Only the separate installation ABI
exposes the live installed digest, so installation state cannot silently
change the meaning of an execution register. The same elaborated executor RTL
consumes the installed affine bounds and strides; selecting a profile does not
regenerate RTL or branch on a graph name.

S02 does not install or consume the S01 generated schedule. It parameterizes
only the existing five-load/four-add/one-store stencil executor. Multi-DAG
execution remains S03.

## Consequences

- Future AXI4-Lite or UIO adapters may map the two owned ABIs separately without
  exposing Chisel, Verilator, Linux, or vendor types inside either contract.
- Reset-based inactive-tail clearing is accepted only for this RTL-simulation
  functional slice. Its physical cost and suitability are unmeasured.
- A future implementation that preserves configuration across reset or avoids
  clearing the full private window requires a later reviewed boundary.
- The separate ABI does not authorize general Graph installation, dynamic
  scheduling, variable-latency issue, or graph-specific RTL.
- No performance, resource, physical, FPGA, ASIC, silicon, or T-0044 conclusion
  follows from this decision.
