# ADR-0104: Remove weekly Codex quota gating

Status: Accepted
Date: 2026-09-26
Task: T-0199 / Issue #268
Supersedes: ADR-0060's weekly quota guard and HCI-09 only

## Authority and decision

The owner explicitly instructed: 「週間残量はもう気にしなくて良い。」
This is an ongoing change, not a fabricated usage reading or a one-run waiver.
Weekly remaining quota, low quota, unavailable telemetry and its freshness are
no longer task-start, delegation, build, remote-update or merge conditions.
Do not ask the owner for quota percentages or pause authorized work for them.

## Boundaries retained

This removes an internal workflow stop. It does not buy capacity, authorize
paid reset credits, change service plans, bypass platform/environment limits,
expand task scope, waive review, alter WIP, or change a scientific gate.
All other HCI and permission boundaries remain. Actual resource observations
may be retained without credentials or account identifiers; never invent
usage data. ADR-0060 and past stops remain historical records.

## Integration

Update AGENTS, WORKFLOW, SPRINTS and active Sprint-operator instructions in
the same change. Historical ADRs/logs remain unchanged. The current owner
instruction applies immediately while this record is integrated by PR.

Current implementation boundary: prose follows this decision, but removal of
the existing daily-sync executable gate, PM agent config and corresponding
tests awaits the explicit scope confirmation requested after automatic
approval rejection. The September 26 log preserves the exact pending patch.
