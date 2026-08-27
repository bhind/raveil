# ADR-0066: Active Project work requires a Sprint and truthful live metadata

Status: Accepted
Date: 2026-08-27
Task: T-0130
Extends: ADR-0056, ADR-0061, and ADR-0065

## Context

ADR-0065 made the GitHub Project a reliable real-Issue execution queue. The
Issue, branch, owner, demo, evidence class, PR, and closed/Done lifecycle worked
through T-0129. The weekly-planning surface nevertheless drifted: T-0127
through T-0129 had no Sprint value, the Project README stopped at T-0126, the
canonical STATUS item count remained 47 while the live Project held 52 items,
and a non-pullable Sprint-review Draft remained `Ready` and P0 while TODO said
no P0 was selected. The fail-closed audit did not reject a missing Sprint.

The primary repository worktree also remained a dirty historical T-0042 branch.
Its user-owned work is valid provenance, but using its stale TODO and STATUS as
the normal current-main entry point creates avoidable coordination ambiguity.

## Decision

Every real `work-item` moved to `In Progress` or `Review` must carry a nonempty
GitHub Project `Sprint` Iteration in addition to ADR-0065's existing execution
fields. `scripts/project_queue.py start` requires `--sprint TITLE`, resolves
that title uniquely against the Project's configured current or future
Iterations before any remote edit, writes the Iteration with all other
metadata, and writes `In Progress` last. Unknown, duplicate, unavailable, or
wrong-type Sprint configuration fails before any mutation. The live audit
rejects an active work item without Sprint.

Keep historical Draft cards, but do not leave a Draft in `Ready` unless it is a
truthful pullable planning packet. The non-pullable S-0001 review Draft returns
to `Backlog`; T-0044/S13 remains `Blocked` provenance. Real mutation still
requires a real Issue.

At each queue-governance closeout, reconcile the Project README current pull,
live item/field counts in STATUS, TODO P0 state, open Issues and PRs, and Project
lifecycle. Count changes are coordination observations, not productivity
claims. Sprint assignment does not promote evidence or imply that forecast SP
was delivered within a human work week.

Use a clean current-main clone or worktree as the normal operator entry point.
A dirty historical worktree remains preserved and is never reset, stashed,
overwritten, or treated as current authority merely because it is the original
filesystem root.

## Consequences

The Project now fails closed when active work is absent from the weekly cadence,
and its human-facing README and Ready column can be trusted without reading
stale Draft cards as active work. A task may still be scheduled into a future
configured Iteration when its dependencies permit; Sprint is coordination, not
task or evidence authority.

This changes development governance only. It establishes no delivery-speed,
parallelism, Graph, performance, research, FPGA, ASIC, silicon, product, or
publication result.
