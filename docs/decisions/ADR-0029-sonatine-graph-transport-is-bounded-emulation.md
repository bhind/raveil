# ADR-0029: Sonatine graph transport is bounded emulation

Status: Accepted
Date: 2026-08-11

## Context

ADR-0025 established the GNU/Linux graph MVP with a replaceable native backend.
T-0090 connects that same frontend to Sonatine without making console prose an
implicit API, duplicating JobDescriptor/CompletionRecord, requiring a kernel
driver, or treating QEMU timing as hardware evidence.

## Decision

The graph CLI selects `native` or `sonatine-qemu` explicitly. The native POSIX
C adapter remains the default and retains its existing result behavior.

The Sonatine adapter writes one exact 128-byte little-endian
`raveil_graph_request_v1` to a temporary file. QEMU's loader places it at the
reserved `0x87ff0000` address in the fixed 128 MiB `virt` RAM contract. The
request contains no pointer, path, descriptor, Linux type, physical object
handle, or authority token. It carries version, size, flags, bounded GEMM
dimensions, candidate kind, request ID, and truncated owned identities.

Sonatine validates the envelope, constructs the existing JobDescriptor and
ObjectManifest, submits and consumes the existing rings and CompletionRecord,
computes the bounded exact-integer GEMM seed, and requires explicit shadow
approval and finalization. `EXECUTED` alone is insufficient. Only then does it
emit one bounded `RAVEIL-GRAPH-RESULT-V1` serial frame bound to request, job,
epoch, sequence, cookie, checksum, reference, and approval.

The host parser accepts exactly one frame with the exact field set. Missing,
duplicate, stale, malformed, unknown, unapproved, rejected, nonzero-exit, and
timeout results fail closed. Guest console diagnostics and completion telemetry
remain separate and cannot satisfy the graph parser.

The v1 backend supports only GEMM with dimensions 1 through 8. It returns no
latency. The analytical adviser therefore abstains for the accepted 8x8 seed;
if a future proposal is exercised without a valid selection timing source, the
graph loop rolls back rather than treating emulation duration as performance.

## Consequences

- GraphProgram, ExecutionContract, GraphVariant, proposal, structural/semantic
  checks, baseline-first execution, and explicit result selection remain owned
  frontend behavior.
- Native and Sonatine compute the same deterministic baseline checksum in the
  differential smoke.
- QEMU loader and serial are replayable transport mechanisms, not authority.
- No shared memory protocol, DMA, MMIO device, kernel driver, new ISA, FPGA,
  ASIC, or silicon path is required.
- Evidence is fixed to `qemu-emulation-correctness`; no latency, energy, or
  hardware-performance claim is created and EXP-0003 remains unchanged.

## Verification

Acceptance requires C ABI validation, strict host parser tests for malformed,
duplicate, stale, unknown, unapproved, timeout and parse failures, unchanged
native graph regressions, actual QEMU baseline execution through the existing
job/completion/finalization path, native-versus-QEMU checksum equality, full
repository regression, and a GNU/Linux container build and one-command demo.
