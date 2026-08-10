# ADR-0015: Gate 2 uses attenuated leaf capability delegation

Status: Accepted
Date: 2026-08-10

## Context

T-0015 requires blocking IPC and capability delegation before Sonatine has a
persistent multi-user scheduler. The existing seed has a depth-four endpoint
queue, a fixed task table, and generation-checked capability slots, but it does
not define delegation, blocking, or revocation-tree behavior. Allowing a grant
to amplify or re-delegate authority would violate the Gate 2 capability
boundary; pretending that the current flat table provides cascading revocation
would also be unsafe.

## Options considered

- Permit unrestricted capability copies and rely on callers to select rights.
- Add a derivation tree and cascading revocation before completing Gate 2.
- Introduce a deliberately limited, rights-attenuating leaf grant and retain
  derivation-tree revocation as an explicit future design question.

## Decision

A capability owner may delegate only when its source capability includes
`CONTROL`. The delegated capability:

- names the same object and a nonzero target task;
- carries a nonempty subset of the source rights;
- never carries `CONTROL`, so it cannot be used for another delegation;
- receives its own generation-checked table slot and may be revoked directly;
- remains valid if the source capability is later revoked.

Endpoint authority follows capabilities rather than creator identity: a valid
`RECEIVE` grant permits its owner to receive. The queued IPC boundary returns
distinct success, blocked, denied, and invalid results. An authorized send to
a full queue or receive from an empty queue marks the caller blocked; the
opposite successful operation wakes one matching waiter in lowest-task-ID
order. Invalid arguments and denied authority fail immediately and never
change task state. Message pointers and failed sends are not retained, so a
woken caller must retry the operation.

## Rationale

This policy makes authority attenuation testable now without inventing an
unverified derivation graph. Distinct IPC results keep authorization failures
separate from scheduling state. Deterministic wake-up is sufficient for the
fixed eight-task Gate 2 seed and does not claim fairness or production
scheduling behavior.

## Consequences

- Parent revocation is deliberately non-cascading. Callers must revoke leaf
  grants individually.
- Derivation trees, cascading revocation, cancellation, interruption, fairness,
  and endpoint object-lifetime policy remain unresolved before Daphnis rings
  are exposed to U-mode. ADR-0016 later resolves flat capability-slot
  generation wrap by retiring exhausted slots.
- Blocking is a state transition plus retry contract. End-to-end blocking
  between persistent U-mode tasks still depends on the later user-task slice.
- A future change that adds recursive delegation or changes revocation and
  wake-up authority must supersede this ADR.

## Verification

Host tests must cover empty/full blocking and wake-up, denied/invalid
fail-closed behavior, deterministic task state, rights attenuation, forbidden
`CONTROL` delegation, owner isolation, and direct leaf revocation. QEMU smoke
must continue through timer preemption and the capability-checked loopback.
