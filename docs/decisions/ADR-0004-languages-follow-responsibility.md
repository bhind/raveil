# ADR-0004: Languages follow responsibility

Status: Accepted
Date: 2026-08-07

## Context

A Rust-everywhere rule would increase integration cost with compiler, QEMU,
Verilator, MLIR, and CGRA ecosystems. Avoiding Rust entirely would leave useful
type and ownership guarantees unused in high-integrity policy code.

## Decision

- Rust `no_std`: small trusted invariants such as capability rights,
  ExecutionContract admission, and GraphVariant lifecycle.
- C++20: host runtime, compiler/model orchestration, transforms, and adapters.
- Python: optimization research, experiments, and analysis.
- Chisel/Scala: generated Daphnis RTL.
- stable versioned C ABI: Rust/C++ boundary.

The bootstrap C kernel and Python seed do not supersede this intended split.

## Consequences

No language is selected for prestige or uniformity. Each boundary needs explicit
ownership, schemas, build support, and cross-platform verification.
