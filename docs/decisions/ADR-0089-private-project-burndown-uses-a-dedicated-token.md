# ADR-0089: Private Project burndown uses a dedicated token

Status: Accepted
Date: 2026-09-05
Task: T-0158

## Context

GitHub Projects standard Insights provides current charts and historical burn
up, but its public API exposes saved-view mutations and no saved-chart or
ideal-line mutation for the private user-owned Raveil Project. GitHub's
repository-scoped `GITHUB_TOKEN` cannot access user Projects. Publishing
snapshots in the public repository or Pages would expose private metadata.

## Decision

Keep standard Insights first. Add one bounded daily Action that reads Project
#1 through a dedicated `RAVEIL_PROJECT_TOKEN` secret and updates exactly one
private Draft named `Raveil iteration burndown`. The script retains at most 180
aggregate daily snapshots and renders issue-count and Story-Point ideal/actual
Mermaid lines plus Status, completion, and Work Type composition. It copies no
title, body, evidence, or credential into workflow output or repository files.

The token has only the Project permission needed to query and update the user
Project. Repository checkout has `contents: read`; the workflow receives no
contents write, pull-request, issue, deployment, package, or identity
permission. The confirmed Project number is a `RAVEIL_PROJECT_NUMBER`
repository variable. Missing configuration fails closed.

The Action runs at 10:00 UTC (19:00 Asia/Tokyo) and may be invoked manually.
It is reporting automation, not build/test/release CI/CD, and does not satisfy
T-0063's trigger for general hosted CI/CD. Repository records and executable
evidence remain authoritative.

## Consequences

- The ideal line and snapshots remain private beside the sprint board.
- A dedicated secret must be installed before scheduled runs can succeed; no
  secret value enters Git, logs, generated Markdown, or the Project Draft.
- GitHub-hosted work is bounded to one five-minute job daily.
- Counts are coordination observations, not productivity, performance,
  acceptance, EXP, or Gate evidence.
- Partial inventory, ambiguous Sprint/Draft, or malformed history fails without
  changing prior history.
