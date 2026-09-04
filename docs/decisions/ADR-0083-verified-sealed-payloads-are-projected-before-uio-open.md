# ADR-0083: Verified sealed payloads enter a no-device adapter before UIO wiring

Status: Accepted
Date: 2026-09-04
Task: T-0145

## Context

ADR-0079 verifies a sealed dynamic request below a trusted artifact parent and
returns retained in-memory bytes. ADR-0071's Linux UIO backend can map an
explicit `/dev/uioN`, but connecting a new pathname-driven dynamic executable
directly to that opener would let a caller bypass the Python verifier with a
self-attested projection. Letting C++ parse the sealed directory itself would
instead regain pathname authority and duplicate only part of the seal,
inventory, source and payload validation.

The smallest T-0145 step must prove the handoff and complete register
transaction path without opening a real device. It must also keep descriptor
interpretation, board access, device deployment and performance outside the
slice.

## Decision

Only the existing ADR-0079 Python verifier accepts a sealed bundle. After it
has returned retained verified bytes, the handoff creates an exclusive private
session and request directory through the existing descriptor-relative
creation helpers. It materializes only the fixed request, selected and seed-one
inputs, independent oracle, generated ABI headers and a canonical
`seal-binding.json`. The original sealed tree remains byte- and
inventory-identical.

The first callable handoff requires an injected runner and has no production
default that opens a device. This allows Host Functional tests to prove that a
valid verified request is passed exactly once and that malformed, drifted,
symlinked, escaping, unsealed or source-inconsistent input invokes the runner
zero times. It does not make the UIO dry-run executable.

The Linux C++ component is a no-device host adapter. It accepts a supplied
`RegisterIo&` and a `VERIFIED_REQUEST_ROOT`; it has no `UioRegisterIo`, device
path, opener, mapping or MMIO primitive. Its projected-request reader is
deliberately not a second seal verifier: it repeats wire-image, version,
affine, input, oracle and canonical binding checks as defense in depth, but the
preceding Python verification remains the authority. Missing, malformed,
extra-field, linked or mismatched projection data fails before the injected
register transport is used. The sealed source identity covers both this
adapter and the Python handoff module.

Add a transport-neutral `run_dynamic_dag` overload for the already admitted
program, input and oracle. It retains the existing reset, affine install,
program install, input stage, start, bounded poll and output-read order, then
requires every output word to equal the supplied independent oracle. A fake
`RegisterIo` proves the complete transaction path, order and oracle rejection.

The Linux ARM64 adapter object may be compiled warning-free but is not connected
to or executed against a real backend in this task. No test or demonstration
opens or maps `/dev/uioN`, issues MMIO, invokes a board tool, or treats target
preflight as durable authority. A future real-device task must define an
unbypassable in-process or inherited-data handoff, pass T-0139, and repeat
ADR-0071's opened-object identity and exact 16 KiB map checks before wiring
`UioRegisterIo` to this adapter.

## Consequences

The accepted boundary connects the verified sealed dynamic payload to the same
three transport interfaces used by simulation while keeping real device
transport absent. Version-1 behavior, the RTL, the three ABI wire formats,
the relative 16 KiB aperture, opcode and selector sets, affine profiles,
register and instruction capacities, and single-invocation policy do not
change.

The result is Host Functional handoff and fake-transport evidence plus an
ARM64 build receipt. It is not a real UIO, KV260, FPGA, RTL-simulation,
performance, timing, area, energy, product-readiness, production-security,
novelty, patent, freedom-to-operate, ASIC or silicon result.
