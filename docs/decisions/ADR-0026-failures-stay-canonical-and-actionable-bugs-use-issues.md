# ADR-0026: Failures stay canonical and actionable bugs use GitHub Issues

Status: Accepted
Date: 2026-08-11

## Context

Raveil already preserves failed experiment bundles, negative results, rejected
decisions, regression tests, and chronological debugging observations. These
records are strong evidence, but reusable operational lessons are scattered.
The project also needs visible defect coordination without turning every
transient development failure into issue-tracker administration.

GitHub Issues is useful for ownership, discussion, and cross-session defect
tracking. It is not suitable as the only source of truth because repository
records must remain available with the code and immutable release history.

## Decision

Raveil uses three connected but distinct records:

1. experiments and raw evidence preserve scientific failures and negative
   results;
2. `docs/FAILURE_KNOWLEDGE.md` preserves short, reusable lessons from
   non-obvious failures and rejected approaches;
3. GitHub Issues coordinates actionable software defects that outlive the
   current branch or require explicit ownership.

Create or retain a GitHub bug issue when at least one condition applies:

- it remains unresolved at branch or milestone closeout;
- it is user-visible, recurrent, or a release blocker;
- it risks security, authority, data integrity, evidence integrity, or loss;
- it crosses components, owners, environments, or requires external follow-up;
- its fix is deliberately deferred.

Do not require an issue for a transient failed command, a defect found and
fixed with a regression test in the same coherent branch, an expected
fail-closed rejection, a negative research result, or a speculative feature.
Promote those only when they meet an escalation condition above.

Material actionable work retains a canonical T-ID in TODO. A GitHub Issue
references that T-ID and relevant ADR/EXP/log/evidence; it does not replace
TODO, STATUS, an experiment record, or a security disclosure process. Issue
creation may be batched at progress review or milestone closeout and must not
block a safe local fix merely because GitHub access is unavailable.

Close an issue only after the fix is merged into the intended integration
branch, relevant regression tests pass, and canonical records are reconciled.
Closing an invalid or duplicate report records the reason and canonical
locator. Sensitive vulnerabilities, credentials, personal data, and unsafe
exploit detail do not belong in a public issue. Neither do internal URLs or
hostnames, absolute user paths, unpublished artifact contents, copied
third-party text or figures, patent claims, or standards-draft text. Follow
`SECURITY.md` and use an approved private channel when in doubt.

## Consequences

- The repository remains the durable authority; GitHub Issues is the defect
  coordination view.
- Routine development stays lightweight because same-branch fixes do not
  require issue churn.
- Recurring lessons become searchable without copying raw logs or replacing
  their evidence records.
- Milestone review includes issue triage and failure-knowledge promotion.
- Hosted CI/CD remains disabled; this decision enables issue tracking only.

## Verification and supersession

T-0088 supplies the failure-knowledge index, issue template, workflow routing,
and initial lessons from existing records. A later ADR is required to make an
external tracker authoritative or to automate external issue creation.
