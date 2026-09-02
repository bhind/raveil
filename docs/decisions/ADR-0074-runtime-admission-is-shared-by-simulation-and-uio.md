# ADR-0074: Runtime request admission is shared by simulation and UIO

Status: Accepted
Date: 2026-09-02
Task: T-0132/S09

## Context

ADR-0073 removed request-specific compilation from the Linux UIO runner, but
the accepted AXI4-Lite simulator still received Graph ID and seed as trusted
process arguments. Its outer runner also emitted and compiled the same RTL for
each request. That path proved per-request semantics, but it did not demonstrate
that simulation and later UIO consume the same runtime request boundary or that
one compiled executable can serve more than one admitted request.

Broadening the frozen catalogue, Graph language, RTL, ABI, or board scope is
not required to close this software-only discontinuity.

## Decision

The AXI4-Lite Verilator bridge must accept only a request-root path. Before it
creates an AXI transcript or constructs the simulated device, it calls the
same `admit_graph_device_request` implementation as the Linux UIO runner. The
admitted Graph ID and uint32 seed alone enter unchanged `run_selected_dag`.
Graph ID and seed are no longer separately trusted command-line fields.

The existing one-request CLI remains supported. A bounded demo additionally
prepares two different catalogue request roots, emits RTL twice, builds one
Verilator executable once, and invokes that exact executable for both roots.
Each request retains an independently finalized private receipt and oracle. A
third corrupted request is rejected before an AXI transcript can be created.

The demo is a single-build proof, not a persistent cache or daemon. Generated
simulators and evidence remain ignored, private, disposable local artifacts.

## Consequences

Simulation and Linux UIO now share one request-admission implementation and
one frozen catalogue interpretation. The demo directly proves that request
selection is runtime data rather than simulator-build authority, while keeping
the current CLI behavior and evidence finalizer intact.

This remains `rtl-simulation-functional` evidence. Reusing a binary inside one
local demo does not establish startup or performance improvement, production
cache integrity, adversarial filesystem-race resistance, real UIO operation,
ARM-board compatibility beyond the already recorded build, FPGA behavior,
resource or timing results, ASIC feasibility, or general Graph support.
