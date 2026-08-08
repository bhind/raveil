# ADR-0006: Own contracts; use and progressively replace upstreams

Status: Accepted
Date: 2026-08-07

## Context

Rebuilding compilers, solvers, simulators, and hardware tools before validating
the thesis would delay evidence. Allowing upstream types to define the public
architecture would make authority and replacement dependent on third parties.

## Decision

Use IREE/MLIR, TVM, CGRA projects, OR-Tools, QEMU, Verilator, Chipyard,
OpenROAD, and similar tools behind adapters. Raveil owns versioned identities,
contracts, graph/object/memory/proposal/certificate/evidence/job/completion
schemas. Record revision, license, target signature, and measurement method.

## Consequences

An upstream replacement must pass semantic, contract, fault, and replay gates
and show a measured reason such as performance, memory, energy, variance,
security, or adaptability. Upstream types do not leak into the public contract.
