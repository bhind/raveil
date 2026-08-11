# ADR-0031: Byte shadows freeze before atomic publication

Status: Accepted
Date: 2026-08-11

## Context

ADR-0023 made metadata versions transactional, but Sonatine had no owned data
bytes. A successful finalization could advance a visible version without
publishing the bytes whose semantics had been approved. T-0085 closes that
narrow executable gap without changing the pointer-free ObjectManifest,
JobDescriptor, or CompletionRecord wire schemas.

## Decision

Each boot-scoped object-table slot owns at most 512 visible bytes. Registration
copies an exact initial image or creates an explicitly zeroed image; it never
retains a caller pointer. A manifest larger than the fixed bound fails before
table mutation.

Admission snapshots every referenced object into the full execution binding.
Trusted-core execution reads only that snapshot. After a structurally valid
completion is consumed, Data authority may stage bytes only into the exact
WRITE range of that full job/epoch/sequence/cookie binding. Overlap, missing
coverage, wrong range, stale binding, cancellation, or mutation after approval
fails closed.

Program approval validates complete staging for every WRITE range and freezes
that invariant and the byte shadows. Finalization then revalidates every READ
and WRITE object, generation, visible version, range, output identity, and
exact-successor version. Only after all checks succeed does a non-failing phase copy
all output bytes and publish all successor versions. Rollback, cancellation,
unapproved execution, and conflict zero the complete shadow slot and leave
visible bytes and versions unchanged.

The current read helpers are trusted-core copy-out operations, not U-mode or
device APIs. The public owned contracts remain pointer-free. Atomic visibility
is limited to the current single-hart, non-reentrant kernel API; no SMP, DMA,
cache-coherence, persistence, or reset guarantee is implied.

## Consequences

- `EXECUTED`, completion ingestion, or Program approval alone cannot publish
  bytes.
- The fixed 512-byte bound covers the current 8x8 int64 graph result but is not
  a general allocator or a production object-size commitment.
- Data capability gates registration, staging, and final publication. Program
  capability remains a separate semantic-approval condition; Experience
  admission remains an observation and cannot mutate bytes.
- Object bytes and versions are published together on the current bounded seed.
  Physical device buffers, DMA-safe lifetime, persistent recovery, and
  multi-hart synchronization remain future work.

## Verification

Acceptance requires exact-copy and oversize registration tests, stable snapshot
reads, wrong-plane/owner/binding/range and overlapping-write rejection,
incomplete and post-approval write rejection, byte invisibility before commit,
byte-preserving rollback/conflict/cancellation, multi-output failure atomicity,
slot zeroization, QEMU byte commit/rollback smoke, native-versus-QEMU semantic
differential, production-symbol review, and the full repository regression.
