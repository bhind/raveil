# ADR-0102: bounded local compiled simulator reuse

Status: Accepted
Date: 2026-09-19
Task: T-0196 / Issue #263
Context: T-0187; ADR-0074, ADR-0075, ADR-0090, ADR-0101

Owner-authorized through T-0187 / T-0196; functional verification is recorded in
the September 19 log. No wall-clock improvement is claimed.

## Decision

Opt-in `RAVEIL_SIMULATOR_REUSE=1` may reuse only a locally built dynamic
simulator and its build provenance. The default and `=0` retain fresh builds.
This is a cooperative local development optimization, not a signed binary
distribution channel, hostile-user sandbox, result cache or daemon.

Identity includes the complete conservative sealed-source inventory, new cache
code/scripts, all four generated headers, the reviewed immutable Docker image
ID, and a content digest of the readonly Scala dependency volume. Source paths
are repository-owned, never selected by a Graph. The dependency digest is
checked inside the execution container before and after use. Source identity is
rechecked before publication. Changed identity is a miss, not stale reuse.
The canonical identity JSON itself is retained in the bundle; its SHA-256 is
the key. The container compares it with the host's freshly constructed identity
before use, along with actual source/ABI manifests and current toolchain text.
Build command, top and flags are bound through the full runner-source digest.
Bundle inventory binds simulator/RTL/provenance byte lengths and digests.

Dependency identity is a sorted relative-path/type/mode/size/content manifest:
at most 2,048 entries, 4,096-character paths, 256 MiB per file and 512 MiB total.
Reject links, hardlinks, special files, unreadable members, tab/newline names
and observed metadata changes. File contents and directory paths are included;
root absolute location is not. Before/after digests must equal the staged
identity. The existing dependency volume has 436 regular files, about 157 MiB,
and no symlinks. This remains a cooperative filesystem consistency check, not
a defense against adversarial same-user mutation between filesystem calls.

The host owns a mode-0700 cache below repository artifacts, with at most eight
entries, each at most 16 MiB of payload plus an 8 KiB manifest allowance.
Entries contain only the simulator, source/RTL/ABI
manifests, toolchain text and a strict hash/size manifest. No request, input,
output or execution receipt is eligible. Reject symlinks, hardlinked files,
unexpected members, oversized files and digest mismatches. Corruption fails
closed; absence or a full cache falls back to an ordinary build. Explicit
fresh-build mode can bypass an unusable cache without deleting it.

Serialize publication with a cooperative host lock, stage in a private sibling,
then atomically rename without replacing an existing entry. Incomplete entries
are never hits. Do not automatically evict or recursively delete old entries.
The exclusive flock covers the final-name absence check and rename; all writers
use this lock and no stale lock is stolen. Existing final names are validated
or rejected, never overwritten. Non-cooperating writers are outside this local
same-user contract; no claim of a portable hostile-writer rename primitive.
Copy validated members into a fresh retained session; verify copied hashes.
The container compares reused source/ABI manifests with those constructed from
its current source copies before executing the binary in offline Docker.

Every invocation independently prepares/admit-checks the request, executes RTL
and the C++ fallback, tests malformed-request rejection, and verifies all 256
output words against the Python oracle. Reuse never means execution reuse.
A versioned reuse marker reports zero elaborations/builds honestly; old V1
markers retain their original meaning. A separate build-reuse receipt records
identity and hit/miss without changing the existing execution receipt schema.
The host rejects a hit marker unless it actually staged the matching bundle.

## Consequences and acceptance

Hashing dependencies and copying bundles add overhead; no elapsed speedup is
claimed. Cold-build and warm-zero-build operation counts, fresh changed outputs,
old-program compatibility, identity invalidation, corruption, boundedness and
concurrent publication must be tested before completion. Retained evidence is
RTL Simulation, not FPGA/silicon measurement. Existing sealed UIO admission
does not widen. No network pull, new image, daemon or paid resource is needed.

T-0183 multi-output and T-0186 standard-IR work follow this bounded increment;
cache expansion is not a prerequisite to generalization.
