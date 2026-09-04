# ADR-0082: A rolling P0 horizon prevents idle delivery

Status: Accepted

Date: 2026-09-04

## Context

ADR-0070 starts an already-Ready successor immediately after review and
retrospective, but it does not require a successor to exist. After T-0144, the
canonical Project and records truthfully contained no active P0 and no Ready
item. The Sprint operator therefore reported the missing pull and stopped even
though bounded product work remained identifiable from current code and
records.

Technical integration must not be delayed by planning, but an empty delivery
horizon must also not become a generic idle state. Automatically selecting a
material product fork, paid or licensed action, device access, or an invariant
change would exceed Project Manager authority.

## Decision

When evidence and dependencies permit, Raveil maintains:

1. one active P0 delivery item;
2. one completely prepared P1/Ready successor; and
3. one forecast Backlog candidate for the following boundary.

The Project Manager checks the horizon no later than the active P0 task Review
boundary. The ordinary queue audit remains non-blocking for technical
integration. A separate `--require-horizon` check reports failure when no
complete P1/Ready successor exists; that result starts bounded refinement and
does not make an otherwise accepted implementation PR unmergeable.

`scripts/project_queue.py prepare` is the sole transition from a linked
Backlog work-item Issue to a prepared successor. It validates the complete
Issue packet, preserves any existing `Initial SP`, writes P1 and all required
metadata first, and moves Status to Ready last. The existing `start` transition
later promotes P1 to P0 and moves Status to In Progress last.

If the horizon is empty, the Project Manager reads current executable gaps and
canonical records, de-duplicates TODO, ranks at most three bounded candidates,
and prepares exactly one unambiguous successor under existing authority. A
material strategic fork, cost, license, device action, invariant change,
weekly-usage stop, or other HCI is returned to the owner as one concrete
question. An empty queue alone is neither completion nor permission to wait.

## Consequences

- Delivery planning overlaps the end of the current task without overlapping
  coherent implementation files or serial PM integration.
- Ready means a complete P1 successor rather than an unvalidated wish or draft.
- The system can detect and replenish an empty horizon, but it cannot silently
  decide a product strategy that exceeds current authority.
- Sprint Review remains a weekly owner-visible ceremony and does not gate
  ordinary task integration or successor preparation.
- This is Host Functional governance only. It does not establish a measured
  delivery-speed improvement or autonomous product authority.
