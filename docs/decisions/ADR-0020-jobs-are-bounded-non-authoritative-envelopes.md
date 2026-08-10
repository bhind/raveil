# ADR-0020: Jobs and completions are bounded non-authoritative envelopes

Status: Accepted
Date: 2026-08-11

## Context

T-0030 needs one Raveil-owned contract shared by Linux adapters and the future
Sonatine/Daphnis path. RFC-0001 does not yet fix a graph ISA, memory model, or
device transport, and Linux is non-authoritative under ADR-0019.

## Decision

JobDescriptor v1 is an exact-size 320-byte little-endian structure. It contains
opaque job/program/graph/ExecutionContract/target identities, four explicit
nonzero resource bounds, and at most four object references. Each reference
has object ID, claimed generation, expected version, bounded range, and exactly
one READ or WRITE effect. Duplicate object-generation pairs, zero or overflowing
ranges, unknown effects, insufficient byte budgets, nonzero reserved data, and
unused nonzero slots fail closed.

CompletionRecord v1 is an exact-size 176-byte observation. It carries job ID,
execution epoch, sequence, and an opaque 128-bit cookie. Those fields are
reserved for Sonatine issuance and stateful enforcement in T-0031.
Executed output versions must correspond exactly to WRITE objects and advance
their expected versions. Rejected, cancelled, and fault completions carry no
outputs. Structures contain no pointer, OS type, path, FD, PID, physical
address, capability handle, or variable tail.

IDs and cookies are correlation/binding values, not standalone authority or
cryptographic authenticity. Stateless validation checks their form, not
issuance, monotonicity, equality, or one-shot consumption. A valid descriptor
is not admitted; valid `EXECUTED` is not committed, semantically approved, made
visible, or written to Experience. Sonatine separately resolves caller capabilities, object
existence/size/version, resources, replay, cancellation, and commit/rollback.

## Consequences

Linux and host tools can validate the same owned bytes without owning meaning.
The four-object seed requires a new schema version if expanded. ObjectManifest
and table lifecycle remain T-0031. Graph encoding, rings, transport, DMA, and
telemetry remain later work.

## Verification

Strict C11 host tests pin sizes and offsets and exercise valid high-bit-ID
roundtrips plus malformed headers, identities, resources, objects, effects,
ranges, reserved slots, statuses, cookies, and output versions. The Linux
verification image compiles the same validator with GCC and `-Werror`.
