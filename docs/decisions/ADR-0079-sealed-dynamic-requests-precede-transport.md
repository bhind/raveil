# ADR-0079: Sealed dynamic requests precede transport

Status: Accepted
Date: 2026-09-03
Task: T-0142

## Context

ADR-0077 and ADR-0078 compile repository-relative descriptors into a fixed,
pointer-free dynamic host request and execute it through RTL simulation. The
compiler, request reader and finalizer still use pathname-based files at
different times. A descriptor or request root can therefore change between
validation, hashing and use. The retained request directory also mixes inputs
with later execution evidence and is not a replayable immutable identity.

ADR-0071 separately defines Linux UIO as a non-authoritative relative
transport, while ADR-0076 requires a read-only target observation before any
later device access. Neither decision authorizes a dynamic descriptor to reach
UIO or permits a preflight observation to replace opened-object revalidation.

## Decision

Add a local sealed dynamic-request bundle above every execution transport. The
creator reads the descriptor once as a bounded regular file without following
symlinks. Those exact in-memory bytes are parsed, validated, compiled, hashed
and retained as the descriptor snapshot. The bundle fixes the descriptor,
complete program and affine payloads, uint32 seed, fixed request and input
payloads, generated headers, ABI identities and a sorted compiler/source
identity manifest.

The canonical manifest enumerates the exact closed file set with byte counts
and SHA-256 identities. Its own digest names the bundle. Creation refuses every
existing destination and creates leaves exclusively without following links.
The seal marker containing the manifest digest is written last. A partially
created directory is never accepted as sealed.

Verification opens the trusted repository artifact parent and descends by
directory descriptor. It rejects absolute or escaping names, unexpected or
missing entries, symlinks, non-regular leaves, size/hash/schema mismatch,
source-identity drift and any change observed while reading. It returns a
bounded in-memory verified request; callers do not regain pathname authority.

Replay never parses or compiles the retained descriptor snapshot. It creates a
new exclusive private execution root, materializes only the verified bytes
needed by the existing dynamic simulator, and keeps output, transcript and
receipt outside the sealed bundle. The replay receipt additionally binds the
sealed manifest and bundle identities. The sealed tree must remain byte- and
inventory-identical before and after replay.

Add a pure Linux/UIO dry-run conversion for a verified bundle. It validates the
unchanged relative 16 KiB aperture and execution, affine and program namespace
bounds and emits a deterministic plan identity. It may validate only the
canonical `/dev/uioN` syntax; it must not instantiate `UioRegisterIo`, call
`open` or `mmap`, access registers, create a device transcript, or treat the
T-0139 preflight as stable authority. Success explicitly reports
`device_opened=0`, `mmap=0` and `mmio=0`. A future device task must still pass
the T-0139 observation and ADR-0071 opened-object revalidation.

## Consequences

One compiled request can be verified and replayed without depending on mutable
descriptor interpretation or executing from a sealed directory. Mutation and
identity failures stop before the simulator or UIO boundary. The same sealed
identity can feed host-functional plan inspection and a separately labelled
RTL simulation replay.

Filesystem permissions are an accidental-write guard, not a claim of durable
immutability against a same-privilege adversary. Safety comes from fd-relative
verification, consuming retained verified bytes and refusing path reopens.
Remote durability, credentials and publication are outside this decision.

Sealing, verification, mutation rejection, exclusive creation and dry-run
conversion are Host Functional evidence. Oracle/fallback/RTL equality after
replay is separately RTL Simulation Functional. No target PASS, UIO execution,
device capability, performance, timing, area, energy, KV260/FPGA function,
general Graph, production security, novelty, patent, legal clearance, ASIC or
silicon result follows. Chisel RTL, device ABIs, opcode/selector/capacity,
affine profiles and the UIO implementation remain unchanged.
