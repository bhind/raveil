# ADR-0057: Main integration requires pull requests

Status: Accepted
Date: 2026-08-23

## Context

Raveil already required dedicated task branches, but remote integration could
still advance `main` by direct push after one-off approval. That bypassed the
stable review surface the owner now requires and made the remote enforcement
weaker than the repository workflow.

The repository currently has one human integration owner. Requiring an approval
from a different account would deadlock routine integration without improving
the recorded diff, discussion, or evidence boundary.

## Decision

Every change to `main` must arrive through a GitHub pull request from a
dedicated change branch. Direct push to `refs/heads/main` is prohibited.

Activate the repository `main` ruleset with no bypass actors. Require a pull
request, require review threads to be resolved, and block branch deletion and
non-fast-forward updates. Keep the mandatory approving-review count at zero
while there is only one human integration owner. This preserves the PR diff,
discussion, checks, and merge record without requiring impossible self-review.

For an already authorized bounded task, pushing its dedicated branch and
creating or updating its PR are ordinary integration steps. Merging the PR
remains a human-authority remote action under ADR-0051 and `docs/WORKFLOW.md`.

## Consequences

- Agents and humans cannot bypass review history with a direct `main` push.
- Force pushes and deletion of `main` are rejected.
- Open PRs may be prepared without repeated ceremonial approval after the
  bounded task and remote target are authorized.
- An unresolved review thread blocks merge.
- Zero required approvals is a single-owner operational setting, not permission
  for an agent to merge. Add a positive approval count only when an independent
  human reviewer is available and the owner accepts the resulting requirement.
- Releases, tags, publication, and PR merge retain their existing authority and
  evidence rules.
