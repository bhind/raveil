# ADR-0032: Pinned MLIR import stays behind owned lineage

Status: Accepted
Date: 2026-08-11

## Context

T-0040 needs one real upstream compiler path without allowing MLIR/IREE types,
paths, handles, or compiler acceptance to become Raveil execution authority.
`GraphProgram` v1 already owns the admitted bounded graph shape, but does not
record source and tool provenance.

## Decision

Import one repository-authored static 8x8x8 i32-input/i64-accumulation GEMM
MLIR fixture through an isolated, pinned `iree-base-compiler` 3.11.0 adapter.
The adapter verifies an allowlisted bounded manifest and source digest, checks
the exact compiler version and full revision, invokes `iree-compile` without a
shell on a private copy of the verified source, bounds diagnostics, time, and
output size, and returns only:

- the existing canonical Raveil `GraphProgram`; and
- a separate strict, pointer-free `raveil.graph-import/v1` provenance sidecar.

The expected wheel distribution hashes are pinned for GNU/Linux arm64,
GNU/Linux x86-64, and macOS universal development artifacts. The sidecar
distinguishes that expected digest from the observed compiler-entrypoint
digest; hash-locked installation is verified by the isolated environment or
container build rather than inferred from the entrypoint alone. The produced
VMFB remains private disposable adapter state. Its digest records the observed
compiler artifact but does not make that artifact a Raveil public contract.
The sidecar also records the exact manifest digest and bounded source/tool
license identifiers.

The imported graph still passes the unchanged Miroirs canonical-slate check,
trusted baseline first, Pavane's independent deterministic reference,
candidate advice or abstention, and explicit commit or rollback. Compiler
success does not grant semantic, measurement, Experience, or commit authority.

## Consequences

This closes the single pinned-workload import slice. It is not a general MLIR
parser or IREE runtime backend and supports no dynamic shapes, arbitrary
dialects, external resources, plugins, or user compiler flags. It establishes
compiler/import correctness on the tested host only; it does not establish
IREE runtime correctness, optimization quality, latency, energy, FPGA, ASIC,
silicon, or full Gate 4 completion.

The compiler remains a trusted upstream dependency installed by the
hash-locked environment/container. The sidecar's entrypoint digest is an
observation, not proof of every loaded compiler-library byte, and the current
adapter's output-size checks are acceptance bounds rather than containment of
a malicious local compiler. Stronger package environment sealing, immutable
base-image pinning, and OS-level process/output limits remain follow-up work
before accepting untrusted toolchains.

Changing the admitted source family, compiler distribution, public import
schema, or upstream-type boundary requires a later decision and new evidence.
