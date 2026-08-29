# ADR-0069: Owner-visible review precedes Sprint review Done

Status: Accepted

Date: 2026-08-29

## Context

The first S-0001 Saturday review command set ran successfully, but the review
ceremony was moved to `Done` before the owner saw and interpreted the runnable
increment. That conflated executable evidence with human review acceptance.
The subsequent hands-on Garden review also exposed a useful product gap: the
validated variant metadata was present, but the difference between a
materialized baseline and a fused implementation plan was not explained in
the interface.

Repository evidence remains authoritative for implementation and research
facts, but the Sprint review ceremony exists to let the owner inspect the
increment, ask questions, and decide what is accepted or carried. Neither
Project metadata nor a successful command can substitute for that interaction.

## Decision

Keep the Sprint review ceremony non-Done until the Project Manager has:

1. run the recorded demo at an identified revision and environment;
2. shown the actual output or visible interface to the owner;
3. explained the visible behavior, failures, evidence class, non-claims, and
   remaining scope in terms of what the owner can inspect;
4. collected owner feedback and classified each item as a defect, new
   feature/Product Backlog item, research question, or transient observation;
5. routed every durable item to an existing stable task or a newly allocated
   monotonic T-ID and, when appropriate, a GitHub Issue or Project Backlog
   item; and
6. received an explicit `Accept`, `Conditional Accept`, `Carry`, or `Reject`
   disposition from the owner.

`Conditional Accept` may close the ceremony only after each condition has an
explicit tracked destination. It does not mean the condition is implemented,
and it does not close the destination task. `Carry` and `Reject` preserve the
review as non-Done until the recorded follow-up or re-review boundary is met.

This owner-visible boundary applies to the Sprint review ceremony. It does not
weaken repository acceptance evidence, reopen already completed task items, or
let the owner-facing ceremony accept an ADR, RFC, EXP, roadmap gate, evidence
class, or performance claim by itself.

## Consequences

- A runnable demo is a review candidate, not owner acceptance.
- The Project review outcome records the owner's exact disposition and linked
  conditions before status changes to `Done`.
- Review feedback becomes actionable project memory instead of disappearing
  in conversation or being mislabeled as a defect.
- Reviews may take an additional interaction, but a truthful pending state is
  preferred to premature closure.
- T-0135 retains the first condition from this rule: Garden needs a bounded
  baseline-versus-fused explanation while remaining read-only.

## Non-claims

This workflow decision establishes no delivery-speed improvement, product
acceptance, research result, Graph performance, FPGA, ASIC, silicon,
publication, or product-readiness claim.
