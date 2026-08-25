# ADR-0062: Simulator execution requires a verified tagless receipt

Status: Accepted
Date: 2026-08-25
Task: T-0124

## Context

An independent replay of the bounded BOOM stripped-token test invoked
run-owned-cpu-memory-smoke.sh, whose ordinary execution path unconditionally
ran docker build with tag raveil-boom-functional-sim:v1. At
2026-08-24 05:46:35 JST that path replaced the shared tag. Other BOOM,
Rocket, integrated Graph, and RTL-export runners consumed the same mutable
name, so fixing only the command that exposed the incident would leave another
producer able to recreate it.

The first diagnosis also called the stable digest
9009a923ce82...fdaf822 an image ID. Direct inspection on the admitted Docker
29.6.2 and Buildx 0.35.0 environment established a more precise graph:

- 9009a923...fdaf822 is the stable linux/amd64 OCI payload manifest;
- the Buildx provenance attestation makes the loaded runtime descriptor an
  OCI image index whose digest changes between builds;
- the loaded runtime index, containerimage.digest, iidfile, and Docker
  descriptor digest agree on this admitted containerd-backed image store; and
- the Docker Config view and RootFS layer list remain stable across those
  changing provenance-bearing index digests.

The functional payload did not change in the observed incident. The failure
was an evidence-authority and side-effect defect: ordinary verification
mutated a shared reference, and the identity vocabulary did not distinguish
runtime index, payload manifest, Config, and RootFS.

## Decision

The BOOM functional simulator Dockerfile has one explicit build command:
hardware/chisel/build-boom-functional-sim-image.sh. It builds without a tag
and may resolve only the already pinned base-image dependency. It must parse
the actual Buildx descriptor digest, media type, size, and build reference;
bind the exact runtime OCI index and exact linux/amd64 payload manifest from
the same BuildKit record; and verify the locally loaded image's exact ID,
descriptor, platform, Config view, and RootFS layer list.

After successful verification, the builder publishes a receipt under
artifacts/boom-functional-sim-images/<runtime-sha256>/receipt. The
digest-named directory is append-only: an existing path is an error. Only
after that publication may the builder atomically replace the ignored
artifacts/boom-functional-sim-image.current convenience pointer. The pointer
is not evidence authority. The verifier resolves it to the immutable receipt,
rechecks the full local boundary, and prints only the exact runtime digest.

Every ordinary runner that previously produced or consumed
raveil-boom-functional-sim:v1 must call the verifier before its first
container and execute only the returned digest. Ordinary runners may not
build, tag, pull, or use the former shared name. A bootstrap container may use
network access where the existing pinned toolchain preparation requires it;
subsequent simulation and validation containers use network none.

The receipt deliberately depends on its local BuildKit history record. If that
record or exact loaded index is absent, verification fails closed and the
explicit builder must run again on that host. Cross-host portability requires
a separately reviewed OCI layout/archive boundary; it is not inferred here.

## Consequences

- A normal RTL replay can no longer silently replace the shared BOOM
  functional simulator tag.
- Provenance-bearing runtime indexes may vary without hiding payload, Config,
  or RootFS drift.
- Earlier receipts remain available under their runtime digest when the local
  current pointer advances.
- Garbage collection of the corresponding BuildKit record intentionally makes
  the local receipt unusable rather than weakening verification.
- The old chronological log remains immutable. Current records correct its
  category error by retaining 9009a923...fdaf822 as a payload manifest, not
  a provenance-bearing runtime index.
- This decision changes no EXP result, performance value, resource equality,
  physical result, FPGA, ASIC, silicon, or semantic attribution claim.
