# ADR-0096: Bound retained metadata reads by the project snapshot budget

Status: Accepted
Date: 2026-09-06
Task: T-0168

## Context

A native logs run with 230 extra tiny inputs succeeds but produces a 72,407-byte
record. The retained-record reader rejects it at the unrelated command-text
limit of 64 KiB, leaving history and diff unusable.

## Decision

Allow trusted callers of NativeWorkspace.read_text to specify an explicit
positive integer byte maximum, with a hard ceiling of 16 MiB enforced by the
helper itself. Default command and recipe reads stay at 64 KiB.
Only the retained record.json caller selects the existing project snapshot
budget of 16 MiB. Keep path validation, regular-file checks, no-follow opening,
bounded descriptor reads, UTF-8 validation, checksum and artifact verification.
No recipe, shell command or external request may select this internal bound.

## Options considered

Globally increasing command text limits unnecessarily changes unrelated input
admission. Rejecting ordinary extra input files solely because their metadata
exceeds the command text limit makes the editable workspace unnecessarily
fragile. An unbounded record read is rejected.

## Consequences and verification

This repairs the demonstrated record-size mismatch; it does not promise every
maximum-size input tree fits the final run snapshot. Existing aggregate byte
and entry budgets still apply, including generated artifacts. No new execution
authority, isolation claim, backend or performance claim is introduced.
Actual native execution must yield readable history and an input diff above
64 KiB. Oversized metadata must fail before content reading; default command
limits, exact bounds, symlinks and checksum tampering remain tested.
