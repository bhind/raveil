# ADR-0017: Persistent U-mode syscalls bind authority to the current task

Status: Accepted
Date: 2026-08-10

## Context

T-0083 closes the missing Gate 2 vertical slice: the earlier U-mode payload
returned before timer scheduling, while the interactive diagnostic shell ran
in M-mode. Existing internal IPC functions accept task IDs, so exposing them
directly as syscalls would let a caller claim another task's identity. Separate
partial U-mode and full machine-timer trap paths also could not safely preserve
and resume a persistent user context.

## Options considered

- Keep the shell in M-mode and treat the earlier transient U-mode probe as the
  Gate 2 boundary.
- Expose existing kernel APIs and accept task/owner identity from user
  registers.
- Use one kernel-owned full trap frame and a narrow syscall veneer whose caller
  identity always comes from the current scheduled task.

## Decision

Sonatine uses one 272-byte trap frame for machine and user origins. It stores
x1 through x31, interrupted x2, `mepc`, and `mstatus` on the current context's
trusted kernel stack. While a context runs, `mscratch` contains that context's
kernel-stack top. Trap return restores only the scheduler-selected frame; user
registers never choose the return frame, privilege, PC, or kernel stack.

The fixed Gate 2 scheduler owns one persistent U-mode `init` context and one
M-mode idle context. CLINT interrupts save the outgoing frame, select only a
READY peer, and later restore the original user frame. This is a single-user
vertical slice, not a general multi-user scheduler.

The U-mode syscall ABI uses `a7` for the operation, `a0` and `a1` for bounded
scalar arguments, and `a0` for the result. It never accepts a caller task or
owner ID. The kernel derives identity from `task_current()` and verifies that
the task is RUNNING before resolving capabilities. U-mode receives only:

- non-blocking console read/write through a console capability; an empty read
  returns `WOULD_BLOCK` so U code, rather than an interrupt-masked kernel loop,
  owns retry policy;
- clock read through a clock capability;
- scalar endpoint send/receive through existing endpoint rights;
- logging of a fixed diagnostic event set;
- seed exit restricted to the scheduler-registered U-mode init task.

Capability creation, delegation, revoke, `CONTROL`, allocator access, global
capability/task dumps, kernel pointers, and arbitrary user pointers are not
syscalls. The current fixed-message veneer avoids retaining or dereferencing
user pointers. A denied or forged handle cannot change caller identity.

M-origin synchronous faults never use the U-mode fault disposition; they take
a distinct fail-stop diagnostic path. When the sole U-mode shell exits, the
QEMU seed writes the test finisher after
marking that current task STOPPED. This is an emulation lifecycle boundary, not
a general reboot authority or production shutdown policy.

## Consequences

- The scripted U-mode prompt can run commands before and after real CLINT
  preemption and can exercise forged, wrong-owner, and rights-escalation denial.
- The legacy M-mode diagnostic shell implementation remains in the tree for
  debugging, but the normal smoke boot path no longer enters it.
- Pointer-bearing syscalls require a later checked copyin/copyout design using
  validated user mappings; direct M-mode dereference of a user VA is forbidden.
- Multiple persistent users, blocked-syscall continuation, fairness, per-task
  address spaces/PMP, fault restart, and general shutdown remain future work.
- Experience remains advice and has no authority over identity, frames,
  capability issuance, scheduler selection, or trap return.

## Verification

Host tests verify the trap-frame size/offsets and accessors for every x1-x31
slot. Source checks require full register save/restore and current-task identity
derivation; QEMU sentinels dynamically cover representative live registers and
the subsequent capability-handle use, not every assembly slot independently.
QEMU smoke must show a U-mode command, both directions of a real CLINT switch,
register sentinel survival and user resumption, all three kernel-derived
capability denials,
a valid endpoint round trip, a post-preemption clock command, and orderly
current-task exit. These results are emulation correctness evidence only.
