# ADR-0035: Bounded Native workspace precedes platform-enforced sandboxing

Status: Accepted
Date: 2026-08-11

## Context

T-0098 provides an interactive Native graph session but its `result PATH`
uses ordinary host paths. A human-facing MVP needs familiar minimum file
inspection without turning the session into a general shell. A real
`chroot(2)` is privileged or platform-dependent, and an application path jail
does not by itself contain hostile native compiler or executor processes.
Requiring the final cross-platform sandbox before evaluating the CLI would
also delay the current delivery objective.

## Decision

T-0099 first adds one explicit capability-style workspace root and bounded
`pwd`, `cd`, `ls`, `cat`, `stat`, `mkdir`, and exclusive `write` operations.
All user paths remain beneath the selected root and fail closed on traversal,
link escape, special files, excessive size, or overwrite. The existing guarded
graph compiler, adviser, executor, validation, and result schemas remain the
only graph authority. This layer may be described as chroot-like workspace
containment, never as an OS security boundary.

T-0100 separately evaluates and implements platform-enforced isolation behind
the same workspace interface. Linux candidates include descriptor-relative
resolution, `openat2`, Landlock, and mount namespaces. macOS candidates include
a container or VM worker and a signed App Sandbox helper. Strong mode must fail
closed when its selected backend is unavailable, separate read-only inputs
from writable work/output, and isolate compiler/executor execution.

## Consequences

The first human demo stays small and requires no root privilege. It gains
useful file inspection but does not accept arbitrary commands, pipes,
redirection, deletion, network access, or GNU/POSIX compatibility claims.
Untrusted graph/compiler inputs remain out of scope until T-0100 supplies and
tests an enforceable boundary. Platform backends may provide different
mechanisms, but release documentation must state their verified guarantees
rather than imply equivalence.
