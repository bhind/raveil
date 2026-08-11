# ADR-0028: U-mode shell keeps bounded scalar state

Status: Accepted
Date: 2026-08-11

## Context

ADR-0017 established a persistent U-mode shell whose syscall identity comes
from the current scheduled task. Its first executable form dispatched one
input byte per command. Growing it into a human command line must not introduce
an unchecked user pointer, kernel-side polling loop, caller-supplied task ID,
or capability bypass.

## Decision

The T-0089 shell owns an eight-byte ASCII command buffer, length, overflow
state, and CRLF state in the U-mode task's saved scalar registers. The kernel
continues to return one nonblocking console byte at a time. It never receives
the line buffer or dereferences a user address.

CR, LF, and CRLF terminate a command. An empty line is ignored. Backspace and
delete remove one buffered byte. Printable input beyond eight bytes sets a
sticky overflow state; the shell discards that command at the next terminator,
prints an explicit error, clears its state, and returns to the prompt.

The public command set is `help`, `info`, `ticks`, `ipc`, `fs`, and `exit`.
Unknown commands report an error and continue. A fixed `selftest` diagnostic is
reserved for the noninteractive QEMU smoke and exercises register restoration
and kernel-derived capability denials.

The only new syscall operation writes one bounded seven-bit scalar byte through
the existing console capability. All command operations still derive caller
identity from `task_current()` and resolve their own console, clock, endpoint,
or filesystem capability. Capability creation, `CONTROL`, arbitrary pointers,
addresses, task IDs, and owner IDs remain outside the user ABI.

## Consequences

- `make -C sonatine run` provides a normal `raveil-u> ` command prompt.
- The line buffer naturally survives timer preemption as task context state.
- The retained M-mode diagnostic shell remains separate and is not entered by
  the normal boot path.
- This is QEMU emulation-correctness evidence. It is not physical isolation,
  multi-user scheduling, performance, energy, FPGA, ASIC, or silicon evidence.
- No external line-editing implementation or library is copied or linked.

## Verification

QEMU smoke must split one command across real timer preemption, execute all
public commands, cover CR/LF/CRLF and an empty line, edit a command with delete,
recover from overflow, reject an unknown command, preserve forged/wrong-owner/
rights-escalation denials, exercise VFS before and after preemption, and exit
through the current U-mode task. Host/source regressions must retain the scalar
ABI and forbid the old single-character smoke sequence.
