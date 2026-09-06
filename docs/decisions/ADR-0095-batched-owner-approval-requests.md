# ADR-0095: Batch routine owner approval requests

Status: Accepted
Date: 2026-09-06
Task: T-0164
Related: ADR-0051, ADR-0058, ADR-0094

## Context

The owner finds repeated per-commit approval prompts disruptive and requested
routine requests once daily with up to ten items, while development continues.
Runtime denials cannot be eliminated by project approval procedures.

## Decision

The primary PM consolidates routine approval requests into at most one
unsolicited packet per Asia/Tokyo calendar day, with at most ten candidate-
bound items. Carry overflow in dependency/priority order; do not wait to fill
the packet. Owner-requested reviews and substantive HCI escalation are exempt
from cadence, not from authorization requirements.

Keep pending candidates and exact operations in affected Issues, with audit,
delegated acceptance, PM verification, dependencies and a last-request receipt.
Only explicit approval of named items permits the corresponding operations,
subject to runtime review. Changed exact-head-only candidates require an
updated request; silence or elapsed time never grants permission.

Continue independent authorized local work while publication waits, within
existing WIP and dependency rules. Do not retry denied operations, treat an
unmerged dependency as integrated, or create scope merely to avoid idleness.
Real incidents still escalate promptly. Preserve a truthful blocked state
when no permitted independent work remains.

## Consequences

This changes routine request timing, not ADR-0094 authority, runtime policies,
review checks, research gates, or Sprint Review acceptance. It does not install
an approval-batching scheduler or notification system; existing Project
maintenance scheduling is unchanged. Each active session reads the last receipt
before prompting, preventing workers from independently repeating requests.
