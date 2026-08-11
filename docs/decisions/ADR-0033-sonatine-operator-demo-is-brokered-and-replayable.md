# ADR-0033: Sonatine operator demo is brokered and replayable

Status: Accepted
Date: 2026-08-11

## Context

T-0092 makes the existing U-mode shell visibly operate Raveil VFS and graph
state. The demo must not turn a console grant into Program, Graph, Data, or
Experience authority, trust human console prose, fabricate a semantic result,
or promote QEMU output into performance evidence.

## Decision

The U-mode task receives a distinct, non-delegable
`CAP_OBJECT_DEMO_AUTHORITY` control capability. Every demo syscall derives the
current task, resolves that exact broker object and its console or filesystem
capability, and accepts only one fixed scalar command. General paths, argv,
user pointers, task IDs, owner IDs, descriptors, and graph bytes do not cross
the syscall boundary.

Filesystem commands use the existing immutable `/hello` and volatile
`/scratch` objects. Job commands use one fixed 2x2 integer GEMM and the existing
Program/Graph installation, Data admission, bound submission/completion,
Experience-observation, byte-shadow, approval, commit, cancellation, and
rollback APIs. Completion alone is insufficient: the kernel computes the GEMM,
independently constructs its expected result, compares the exact checksum, and
only then approves and commits. Ring pressure reports retryable `BUSY`; ledger
failure rolls back and becomes terminal `FAULT`.

Trusted kernel code emits only the exact bounded frame:

```text
RAVEIL-SONATINE-DEMO-V1 command=<fixed> seq=<u64> status=<fixed> job=<u64> state=<fixed> semantic=<0|1> checksum=<16-hex>
```

The host runner accepts the exact 18-frame transcript with canonical scalar
encoding, strictly increasing sequence, consistent job binding, and the fixed
independent completed checksum. It bounds kernel input, process output,
stderr, time, and command sizes; rejects unknown versions and malformed,
duplicate, stale, missing, late, prose-only, timeout, or nonzero-exit results;
and exclusively publishes one strict `raveil.sonatine-demo-result/v1` JSON
record. The record binds repository revision, kernel and input hashes, logical
QEMU command, tool versions, every accepted frame, final state, checksum, and
exit status.

## Consequences

The demo is replayable QEMU emulation-correctness evidence and remains
separate from completion telemetry, active Experience, MeasurementRecord, and
the userspace graph result. Human UART prose and the JSON record grant no
authority. The fixed commands are not POSIX/coreutils compatibility.

This decision adds no ELF loader, process model, general filesystem namespace,
shared memory, DMA, MMIO driver, persistent disk, real Daphnis device, or
performance, latency, energy, FPGA, ASIC, or silicon claim. It does not advance
Gate 3 or Gate 4 and does not reinterpret EXP-0003's falsified conclusion.

## Verification

Host C tests cover owner/object/right denial, VFS no-partial-write behavior,
busy, empty, stale, complete, cancel, too-late, repeat-result, ring pressure,
Experience-ledger fault rollback, and preserved preexisting authority state.
Python tests cover exact schema/parser behavior, bounded subprocess and file
handling, no-overwrite publication, wrong checksum and version rejection, and
an opt-in real-QEMU transcript. Local CI retains release/debug RV64, DWARF,
shell/preemption/capability, telemetry, graph differential, and QEMU smoke.
