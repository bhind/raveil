# ADR-0030: Four-plane writes require distinct capabilities

Status: Accepted
Date: 2026-08-11

## Context

ADR-0001 assigns Program, Graph, Data, and Experience different ownership, but
the executable Sonatine seed previously exposed kernel-internal object
registration, job admission, semantic approval, metadata publication, and
telemetry emission without caller capability checks. The fixed capability table
also had no plane-specific object types.

## Decision

Sonatine uses four distinct capability object types for Program admission,
Graph installation, Data production/publication, and Experience observation
admission. Program and Graph roots carry `CONTROL`; Data and Experience roots
carry `CONTROL|WRITE` and may delegate only attenuated, non-recursive `WRITE`
leaves under ADR-0015. A capability object ID names the bounded authority domain,
never a 64-bit Data object or 128-bit Program/Graph identity.

Program identities are installed once into a fixed boot-scoped registry. Graph
identities are installed once and bound to an already installed Program.
Submission requires the exact installed Program/Graph pair plus Data producer
authority. Data authority is required for object registration and metadata
publication. Program authority is separately required for the injected trusted
semantic approval. Experience authority admits only a bounded consumed-
completion observation; it cannot approve or publish Data and does not promote
the host completion journal into active Experience.

The unguarded job mutation primitives become file-local functions in the same
translation unit as the authority module. Focused core state-machine tests see
explicit test-only wrappers only when compiled with
`SONATINE_JOB_AUTHORITY_TESTING`; production builds export only the
capability-taking plane API. Caller identity is an explicit kernel task ID in
this boot-scoped seed; no new U-mode syscall accepts caller-supplied identity or
capability-table mutation.

## Consequences

- Wrong-owner, wrong-type, wrong-right, forged, stale, and revoked handles fail
  before the protected mutation.
- Full Program/Graph identities and 64-bit Data IDs remain in kernel-owned
  registries/contracts and are never truncated into capability object IDs.
- The current Data capability is a coarse plane-producer authority, not a
  per-object least-privilege grant.
- Program/Graph installation from the validated fixed graph loader remains a
  trusted boot-adapter seed; it is not signature or supply-chain admission.
- Registries and the Experience ledger are fixed, volatile, single-hart, and
  reset with the kernel. There is no persistent authority, derivation tree,
  DMA/IOMMU isolation, SMP proof, active Experience promotion, or hardware
  performance evidence.
- T-0085 still owns byte backing and byte-shadow publication. Gate 3 remains
  planned until that data path and remaining device/lifetime boundaries exist.

## Verification

Acceptance requires an exhaustive four-plane operation matrix, identity and
registry checks, wrong-owner/type/right tests, attenuated delegation and stale
revocation tests, capability-authorized metadata commit with visible-version
invariance on denial, restricted and capacity-bounded consumed-completion
admission, absence of raw mutation entry points from the production link
interface, QEMU smoke through the normal graph path, and the full repository
regression suite.
