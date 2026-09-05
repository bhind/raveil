# ADR-0090: Explicit Graph input snapshots are simulation-only

Status: Accepted
Date: 2026-09-06
Task: T-0160
Related: ADR-0085, ADR-0087, ADR-0089

## Context

Graph descriptors now compose relative loads, addition, maximum and unsigned
multiplication, but the editable execution path still generates all input from
a seed. The owner requests further generality. Bounded user data enables an
editable input/run/diff loop without new instructions or memory boundaries.

## Decision

Add project-recipe/v2 for graph-device with exact schema/kind/descriptor/input
fields. Input is a confined JSON basename under inputs/. It contains an exact
`raveil.graph-input/v1` object with `words`, exactly 324 unsigned 32-bit integers.
Reject booleans, floats, duplicate/unknown fields, invalid sizes/ranges and input
over 64 KiB. Keep project-recipe/v1 and seed generation unchanged.

Use only copied project input bytes. Bind raw and packed little-endian input
to the run; validate returned bytes/receipt before success. Retain earlier
inputs/results. This is cooperative local development, not hostile isolation.

Dynamic request v5 means explicit input, not program v5. It contains existing
program v1--v4 in the unchanged 1584-byte request. Its seed field must be zero,
an internal execution-slot identifier. Legacy request v1--v4 still require
matching program version and deterministic input. The 324 embedded words,
request-input.bin and selected runtime input file must agree. Preserve the
deterministic seed-1 calibration. For the unchanged runtime, explicit input
occupies inputs/seed-0.bin; user-facing text must label snapshot provenance.

Projected UIO requires request header v2 as well as program v2; a v5 envelope
carrying program v2 must not cross that boundary. Sealed admission, Garden,
opcodes, RTL, MMIO, profiles and capacities do not expand. Include the contract
in shared runner/sealed source inventories, preserving exact equality.

## Acceptance and non-claims

Verify malformed/tampered input rejection, unchanged seed requests, C++
explicit admission/UIO rejection, project edit/run/diff/history behavior and
real offline RTL output equality with descriptor oracle and fallback. Mocked
adapter tests are host-functional, never RTL evidence. No hardware performance,
production isolation, external-source adoption or research-gate claim.
Constants and flexible dimensions remain separate future design questions.
