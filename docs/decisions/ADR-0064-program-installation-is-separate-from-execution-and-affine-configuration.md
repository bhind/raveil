# ADR-0064: Program installation is separate from execution and affine configuration

Status: Accepted
Date: 2026-08-25
Task: T-0123
Related: ADR-0039, ADR-0063, T-0122

## Context

T-0123/S02 changes bounded shape and stride through
`raveil.graph-device-install-abi/v1`, whose accepted payload window is exactly
16 words. It still runs one five-point state machine. S03 must execute
semantically different acyclic DAGs without changing the T-0122 execution ABI,
silently enlarging the accepted affine ABI, regenerating RTL per Graph, or
selecting a hardwired machine by Graph name or identity.

The earlier T-0114 donor used a 64-word combined configuration transport. That
record and layout are not current authority: reconstructing it by changing the
accepted 16-word v1 contract would invalidate S02 receipts and ABI continuity.

## Decision

Keep `raveil.graph-device-abi/v1` and
`raveil.graph-device-install-abi/v1` byte-identical. Add a third, task-neutral,
fixed-width, little-endian, pointer-free, word-addressed
`raveil.graph-device-program-install-abi/v1`. Its separate 32-word payload owns
only one program identity and at most 16 instructions over eight 32-bit value
registers. It uses the same idle-only, sequential clear/write/commit lifecycle
and one-outstanding transport rule as the affine installer.

The operation and address alphabet is frozen to:

- `LOAD_U32` from center, north, south, west, or east of the current installed
  affine coordinate;
- modular `ADD_U32` of two already-defined value registers;
- one final `STORE_U32` to the installed private-output coordinate.

The installer rejects unsupported or reserved encodings, undefined operands,
out-of-range registers or selectors, missing or non-final stores, nonzero
unused words, partial or misordered writes, and mutation while execution or
owned memory is active. Device reset restores the factory five-point program.
Execution starts only while both affine and program installers are installed
and fault-free. A failure in either transaction therefore cannot publish a
partially paired configuration.

Repository-owned external JSON descriptors, rather than names embedded in the
compiler, define the first three Graphs:

1. baseline 16-by-16 five-point;
2. compact 8-by-8 horizontal three-point;
3. baseline 16-by-16 vertical three-point.

The compiler validates the same schema and topologically lowers every file; it
does not choose semantics by Graph name. One elaborated sequential interpreter
decodes only installed opcodes and fields and admits at most one active
invocation and one outstanding memory request. The compact case deliberately
changes both the existing affine profile and installed instruction sequence.

The independent oracle walks the external DAG directly. The generic software
fallback interprets the compiled instruction words. Neither may reuse the
other's evaluated values. Exact output words, checksums, accepted transaction
addresses, store data, cancellation, reset/restart, source and ABI identities,
and one shared RTL export are bound into an append-once receipt.

## Consequences

- S02 clients and receipts retain both existing owned ABI identities.
- Future transport adapters may expose execution, affine installation, and
  program installation as separate apertures without leaking Chisel,
  Verilator, Linux, or vendor types into a contract.
- The program digest is evidence identity, not cryptographic device
  authentication. Host finalization, trace comparison, and private-output
  validation remain mandatory before publication.
- Passing S03 establishes bounded multi-DAG RTL-simulation functionality only.
  It does not establish arbitrary Graph support, a dynamic scheduler,
  variable-latency execution, useful performance, resource equality, FPGA,
  ASIC, silicon, novelty, patent clearance, or freedom to operate.
- Adding an opcode, selector, register, instruction, outstanding request, or
  changing any owned ABI requires a later reviewed decision.

## Supersession

ADR-0063 remains authoritative for execution and affine installation. This ADR
adds the separate program-installation boundary for S03; it does not rewrite
or supersede either accepted ABI.
