# ADR-0021: Sonatine owns boot-scoped bounded job rings

Status: Accepted
Date: 2026-08-11

## Context

ADR-0020 defines non-authoritative JobDescriptor and CompletionRecord bytes but
leaves ObjectManifest lifecycle, admission state, completion binding, and
replay protection to T-0031. Linux remains non-authoritative under ADR-0019.
No Daphnis MMIO, DMA, interrupt, shared-memory, or reset contract exists yet.

## Decision

ObjectManifest v1 is an exact-size 64-byte little-endian metadata record. It
names a 64-bit object ID, generation, visible version, byte length, permitted
READ or READ|WRITE effects, and volatile or immutable backing class. It carries
no pointer, physical address, capability handle, path, or operating-system
type. Structural validation is not authority.

The T-0031 seed keeps a fixed eight-entry object table, four-entry submission
ring, four-entry completion ring, and four-entry inflight ledger inside
Sonatine. Registration is boot-scoped, rejects duplicate IDs, and provides no
delete or slot reuse. Job admission copies exact structures and checks every
reference against object ID, generation, visible version, range, and permitted
effect. Object IDs and manifest generations are not capability handles or
capability-table generations.

Sonatine issues each admitted job a boot-scoped nonzero execution epoch,
monotonic sequence, and deterministic opaque cookie. The cookie binds and
correlates state; it is neither secret nor cryptographic authority. A
completion is accepted only when the entire binding matches the inflight
ledger and the ADR-0020 validator accepts it. Posting and consuming are each
one-shot; malformed, stale, mismatched, duplicate, full, and empty operations
fail without consuming pending work. Consumed slots are zeroed.

An `EXECUTED` completion remains an observation. T-0031 does not update object
versions, publish output, commit, roll back, cancel, or write Experience.
Those remain T-0032/T-0033. Rings are single-hart, kernel-owned data structures
and are not exposed to U-mode or Linux. Cross-boot uniqueness, shared-memory
ordering, reset, DMA, MMIO, IRQ, and device transport require later decisions.

## Consequences

The repository gains an executable authority-state seed without pretending a
real Daphnis device exists. Linux may compile the shared manifest validator but
cannot issue trusted bindings or mutate Sonatine state. A later U-mode or
device-facing submit path must resolve caller capabilities out of band; 64-bit
object IDs must never be truncated into current 32-bit capability object IDs.

## Verification

Strict-C11 host tests cover malformed manifests, object-table admission,
generation/version/range/effect rejection, FIFO and bounded backpressure,
binding mismatches, duplicate/replay rejection, one-shot consumption, slot
reuse, and unchanged visible versions. QEMU boot runs a kernel-internal smoke
and emits a distinct emulation-only marker.
