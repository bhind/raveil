# ADR-0075: Operator runtime pair stays inside the frozen catalogue

Status: Accepted
Date: 2026-09-02
Task: T-0132/S10

## Context

ADR-0074 proved with a fixed shell demo that one compiled AXI4-Lite simulator
can execute two request roots through the shared runtime-admission boundary.
The operator-facing CLI still exposed only one request per invocation, so
trying the reusable-binary behavior required knowing the internal script and
its hard-coded request pair.

A persistent simulator cache, daemon, arbitrary-size batch, or broader Graph
catalogue is not necessary to expose the proven behavior honestly.

## Decision

Add `graph-device run-pair` to the existing top-level CLI. It accepts exactly
two repeated `--graph` and `--seed` pairs. Both pairs must pass the existing
byte-frozen catalogue admission before the lower runner or Docker can start.

The lower S09 demo becomes parameterized for exactly those two ordered pairs.
After it returns, the CLI does not trust its success marker alone. It confines
the reported session path to the repository artifact root, independently
revalidates each append-once request receipt in order, requires both receipts
to bind the one marker-named simulator SHA-256, and confirms the deliberately
rejected request produced no AXI transcript and did produce a diagnostic.

The rendered result names each admitted Graph and seed, oracle success, common
simulator identity, rejection-before-AXI, evidence class, and the explicit
absence of performance measurement.

## Consequences

An operator can now exercise the smallest reusable-simulator MVP from one
documented CLI without editing a fixture or trusting build output. The command
still performs one build per pair invocation and supports exactly two requests.

This is `rtl-simulation-functional` evidence only. It makes no startup,
throughput, performance, persistent-cache, production-isolation, real-UIO,
FPGA, resource, timing, ASIC, silicon, general-Graph, or product-readiness
claim.
