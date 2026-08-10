# ADR-0018: The filesystem seed uses bounded scalar capability operations

Status: Accepted
Date: 2026-08-10

## Context

T-0017 needs useful U-mode filesystem behavior without unchecked user pointers
or per-open capability exhaustion.

## Decision

The MVP VFS exposes immutable initramfs `/hello` and volatile writable RamFS
`/scratch`. Storage is static, each file is limited to 64 bytes, nodes are
never deleted or reused, and failed writes do not extend a file. Symlinks,
mounts, descriptors, rename, unlink, relative paths, persistence, and POSIX
compatibility are absent.

The init task receives filesystem-root capabilities. Syscalls derive identity
from `task_current()`, resolve `CAP_OBJECT_FILESYSTEM`, and transfer only a
node ID, bounded offset, and one byte in registers. No user path, buffer,
kernel pointer, owner ID, or task ID crosses the boundary. READ and WRITE are
the only valid filesystem-capability rights. VFS independently rejects writes
to initramfs.

## Consequences

Arbitrary lookup, larger transfers, per-node authority, object reuse,
persistence, and VirtIO remain later work. QEMU results are emulation
correctness evidence only.

## Verification

Host tests cover lookup, traversal rejection, immutable reads, RamFS
write/read, bounds, failed-write non-mutation, and deterministic reset. QEMU
smoke performs filesystem operations before and after real preemption and
checks kernel-derived denial markers.
