# ADR-0016: Contain user faults and reject timer dispatch re-entry

Status: Accepted
Date: 2026-08-10

## Context

Gate 2 requires the diagnostic shell to remain observable after U-mode and
timer activity. The seed previously printed a non-ecall U-mode trap and then
spun forever inside the trap handler. Timer interrupts are normally masked by
machine trap entry, but the dispatch boundary had no explicit or testable rule
for accidental nested entry.

## Options considered

- Panic or spin on any U-mode fault and rely only on hardware interrupt masks.
- Resume the faulting instruction and permit nested timer scheduling.
- Terminate the current U-mode probe back to the kernel and reject nested timer
  dispatch without mutating tick or context state.

## Decision

Unexpected U-mode exceptions and unknown U-mode syscalls are contained by
recording a diagnostic and returning through the existing kernel-return path.
They are never resumed at the faulting PC. The trusted return address,
callee-saved registers, `gp`, and `tp` are restored from the kernel stack; no
U-mode-controlled register determines M-mode control flow or kernel ABI state.
The current bootstrap has no
persistent user-task lifecycle, so containment returns control to the M-mode
diagnostic kernel rather than claiming per-task recovery.

Machine-timer dispatch is explicitly non-reentrant. A nested entry observed
while the outer timer dispatch is active is counted and rejected: it returns
the incoming frame and PC unchanged and does not acknowledge another tick,
select another context, or overwrite saved task frames. The outer dispatch
releases the guard after context selection.

Capability slots never wrap a generation back to an earlier value. Revoking a
slot at generation 65,535 retires that slot permanently; future allocations
move to another slot. Unknown right bits and invalid object identities are
rejected at creation. This supersedes ADR-0015 only where it left generation
wrap policy unresolved.

## Consequences

- A deliberate illegal-instruction U-mode probe must return to the kernel, then
  the normal timer-preemption and shell smoke must complete.
- Unknown syscalls fail closed instead of hanging the machine.
- The guard is a correctness backstop, not evidence that QEMU or hardware
  actually delivered a nested machine-timer interrupt.
- Persistent user-task termination, fault delivery, restart policy, and
  multicore/per-hart interrupt guards remain future work.
- Generation exhaustion reduces the fixed table capacity rather than allowing
  a stale handle to regain authority.

## Verification

Host tests cover write/exit/unknown/fault trap dispositions and a callback-based
timer dispatch seam: forced re-entry must preserve frame/PC and invoke neither
tick nor context selection. Capability tests cover ordinary stale slot reuse,
full 16-bit generation exhaustion and slot retirement, rights escalation,
forged handles, and invalid endpoint objects. QEMU smoke uses an illegal
instruction after deliberately corrupting U-mode `ra`, `s0`-`s11`, `gp`, and
`tp`, then
requires the fault marker, kernel return marker, timer preemption, IPC, and the
subsequent shell.
