# ADR-0023: Shadow finalization publishes versions only after approval

Status: Accepted
Date: 2026-08-11

## Context

T-0031 retains admitted jobs through completion observation, but `EXECUTED`
cannot publish object state. T-0033 needs an explicit commit, cancellation, and
rollback state machine before any device or user-facing authority exists.
The current ObjectManifest table contains metadata only and has no object byte
backing or semantic oracle.

## Decision

Every admitted job has a full kernel-owned binding: job ID, boot epoch,
execution sequence, and 128-bit cookie. Completion consumption moves the exact
descriptor, binding, observed completion, and cancellation bit into a fixed
shadow-finalization slot instead of releasing all state. Job IDs cannot be
reused while either execution or shadow state remains active.

`EXECUTED` is insufficient to commit. A separate kernel-internal approval call
must match the full binding. The current smoke and host tests inject this
approval; they do not establish semantic correctness or implement Pavane.
Rejected, cancelled, faulted, unapproved, or explicitly rolled-back shadows
cannot publish versions.

Before commit, Sonatine revalidates every READ and WRITE reference against the
current object ID, generation, visible version, range, and length. Every output
must be the exact successor `expected_version + 1`; version overflow fails.
All references and all outputs are checked before any mutation, then all WRITE
versions are published in a non-failing second phase. On the current
single-hart, kernel-only, non-reentrant seed this provides before/after API
visibility. It is not SMP, DMA, cache-coherence, or persistent atomicity.

Cancellation is sticky. A queued cancellation retires kernel execution state
and its stale ring entry is skipped. A dispatched or observed cancellation
allows terminal accounting but permanently forbids approval and commit. A late
`EXECUTED` observation after cancellation therefore rolls back. Finalization is
one-shot; wrong or stale bindings and repeated terminal operations fail closed.

The T-0033 shadow contains descriptor, completion, and proposed version
metadata only. Rollback means discarding never-published version observations;
it does not restore bytes because no byte backing is published by this seed.
T-0085 owns fixed byte backing and byte-shadow publication. T-0043 owns a real
semantic oracle, and T-0034 owns plane write authorities.

## Consequences

Two jobs may optimistically target one visible version; at most the first valid
approved commit wins and the other conflicts without partial publication.
Multi-output commits are all-or-nothing for visible metadata. Gate 3 remains
Planned because byte shadows, semantic approval, capability-authorized callers,
and Four-plane write authority are absent.

## Verification

Host tests cover no-approval rollback, explicit approval and one-shot commit,
queued and dispatched cancellation, late execution after cancellation, stale
writer conflict, exact-successor versions, and a two-output conflict where
neither output partially publishes. QEMU smoke exercises injected approval,
metadata commit, queued cancellation, and explicit rollback, labelled as
emulation correctness only.
