# ADR-0059: AI role lanes govern execution capacity

Status: Accepted
Date: 2026-08-24
Task: T-0118
Supersedes: ADR-0056 only for the fixed eight-SP capacity and post-sprint capacity calculation

## Context

ADR-0056 introduced an eight-point weekly pilot around one human integration
lane. That was a useful initial forecast, but it mixed three different things:
relative delivery risk, elapsed agent execution, and the serial human-owned
integration boundary. Treating the sum of story points as a hard weekly stop
left available specialist lanes idle and made a fast, verified AI-delivered
slice appear to consume a full human-week budget.

Raveil already assigns distinct implementer, tester, reviewer, librarian,
researcher, and Project Manager responsibilities. Capacity needs to describe
those actual lanes while keeping task, evidence, and merge authority serial and
inspectable.

## Decision

Keep the GitHub Project as the sole live sprint board and retain the two-item
delivery WIP limit. Retain Fibonacci story points, but use them only as an
AI-relative delivery-risk index. Story points do not represent hours, a weekly
execution quota, agent count, or permission to stop. Preserve every Initial SP;
change Current SP only with a dated, evidence-backed reason.

Use these execution lanes:

| Lane | Default concurrency | Tier | Boundary |
|---|---:|---|---|
| Project Manager / integration | 1 | high | scope, records, acceptance, PR comment, and merge stay serial |
| tracked-file mutation | 1 coherent item | low implementer | one named owner and exact file allowlist; no concurrent edits to one change |
| tester | 1 | low | runs after an implementation slice; edits no tracked files |
| read-only review | at most 2 | high only when the risk requires it | independent security, performance, or final-PR review |
| librarian | 1 as needed | medium | bounded context and provenance packet only |
| researcher | 1 at evidence milestones | high | non-authoritative memo only; no continuous participation |

Experience, Measurement, Systems, and Chisel implementers use low reasoning by
default. Chisel has a dedicated role rather than silently expanding the native
C/Sonatine/RISC-V/QEMU Systems role. The Tester also uses low reasoning.
Project Manager, security and performance reviewers, and milestone Researcher
retain high reasoning. This tiering changes development cost and scheduling
only; no model output gains build, selection, evidence, task, or gate authority.

Each estimate separates AI edit/implementation, verification/reproduction,
and PM integration/review/records. It records warm and cold ranges, the
dominant role lane, observed cycle time when available, and invalidation
conditions. Weekly forecasts use completed accepted-slice cycle time by lane
and current dependency/WIP state. Reaching a forecast SP total never stops
otherwise authorized work; only dependencies, the WIP lane, or an ADR-0051 HCI
does.

The first evidence-backed correction preserves Initial SP and changes Current
SP for T-0117/S01 from 5 to 3 and T-0117/S02 from 3 to 2. S01 required one
bounded implementation packet plus independent terminal-safety review; S02 was
a clean replay and record closeout. T-0116 and T-0106/S01 remain unchanged
until a comparable item-level execution record justifies correction.

## Consequences

- The historical eight-SP Sprint assignments remain provenance, not an
  execution ceiling or a reason to idle an available lane.
- WIP remains two delivery items, normally one mutation and one review or
  acceptance item.
- Low-cost agents perform bounded implementation, parsing, test, and mechanical
  inventory work; high-cost agents are reserved for authority and risk review.
- Parallel agents do not become additive FTE and cannot bypass the serial PM
  integration boundary.
- Capacity calibration uses actual accepted cycle-time observations instead of
  the median of self-assigned completed points.
- This decision changes no implementation P0, research gate, EXP conclusion,
  evidence class, performance claim, or remote-publication authority.
