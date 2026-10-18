# ADR-0135: Foreground array execution control

Status: Proposed
Date: 2026-10-17
Task: T-0239 (local candidate; remote registration pending)
Context: ADR-0107, ADR-0132, ADR-0133, ADR-0134; EXP-0002 functional evidence.
Authority: owner directs continued implementation to practical local use.

## Decision and scope

Add a scoped foreground execution controller for array-run. Existing source,
compiler, numerical, capture and saved-proof schemas remain unchanged. The CLI
optionally accepts a finite 0.01..86400 second monotonic execution budget and
progress on stderr. The prepared application enables progress. Stdout retains
only the final verified result; progress never grants output authority.

SIGINT and SIGTERM set a sticky stop request. Checkpoints stop new dispatch and
unwind owned processes before returning 130 or 143. A dedicated BaseException
prevents the legacy standalone fold adapter from translating an array stop into
an ordinary incomplete child return. Deadline expiry returns 124. No automatic
fallback, in-place repair, resume or reuse of partial results is permitted.
Retries create fresh attempts. Errors identify the allocated attempt when known.

The whole-run budget starts before prepared-backend verification. Filesystem
inventory, parent/pass/session/job boundaries, UART reads and Docker waits
observe the control. A 15 second QEMU version probe is bounded and reaped. During
coupled RTL execution the current UART host deadline also applies, so it cannot
silently acquire a fresh 240 second allowance. The independent guest-clock
protocol deadline remains unchanged and is not asserted equal to host wall time.

Execution limits are cooperative, not hard real-time termination. One bounded
compiler operation or filesystem call may delay a checkpoint. Mandatory cleanup
continues after the requested deadline: the Docker client wait/removal each have
30 second bounds, and QEMU terminate/kill waits each have two second bounds.
Repeated signals cannot interrupt cleanup while the foreground controller owns
signal handlers. Failed cleanup stays an explicit uncertainty and cannot seal
parent success. Docker writes its creation acknowledgement to a private host-only CID file outside
container mounts. The client is reaped before that file is checked. If neither
successful client completion nor a valid creation acknowledgement was observed,
removal must positively acknowledge the exact named container. Mere absence is
insufficient: a submitted creation request may still be pending in the daemon. Such uncertainty
returns failure (2), including when a stop triggered the cleanup. Original signal handlers and context are restored on every exit.
SIGKILL and host/process crashes cannot provide these cooperative guarantees.

The parent checks cancellation immediately before its atomic record link. Before
that checkpoint, an observed request denies publication; after the atomic link,
the committed record wins and is fully reread before display. A request racing
the final checkpoint/link may observe completed work. A committed saved result is
never revoked or rewritten. Progress and stop diagnostics are not saved proof.
No persistent verification cache or reduced recursive validation is introduced.

## Acceptance

Require focused UT for finite budgets, signal restoration, repeated cancellation,
UART/RTL waits, version-probe reaping, cleanup uncertainty, no partial output,
pre/post-commit races and immutable fresh retry. Re-run affected current and
legacy proof-reader tests. Actual QEMU/RTL acceptance must cover successful run,
stop during live execution, deadline expiry, cleanup and fresh retry, plus saved
reads with subprocess creation denied. Record exact commands and retained failed
trees. Host fixtures and functional execution are separate evidence classes.

No hardware purchase, runtime installation, numeric/ISA extension, vendor
advantage, application throughput or physical performance claim is included.
