# EXP-0007: Fixture-owned input staging boundary

Status: Planned
Evidence class: RTL simulation pilot
Date: 2026-08-14
Task: T-0044
Authority: RFC-0004, RFC-0005, ADR-0039, ADR-0046, ADR-0047, EXP-0006

## Falsifiable question

Can one fixture-owned, phase-exclusive provider stage fresh inputs 1--4 for
static Graph, Rocket in-order, BOOM OoO, and diagnostic-only BOOM
serialize-dispatch through an equal single-ingress resource, release each
candidate exactly once after the 324th response, preserve existing execution
semantics and optimizations, and remove EXP-0006's staging-initiator asymmetry?

## Scope and pre-data state

This record allocates EXP-0007 before implementation or data. It does not
reuse, amend, or reinterpret EXP-0006 raw evidence. The implementation commit,
machine-readable manifest, estimator, inference unit, exact accounts, interval
rule, environment identity, and final manifest SHA-256 must be frozen here
after code/tests exist and before any commissioning command runs.

Only the staging-initiator pause point is in scope. The primary and diagnostic
matrix, RFC-0005 workload, execution window, CPU load reuse, Graph execution
schedule, output validation, one process/reset/installation/no-reload session,
and fail-closed evidence layout remain as in EXP-0006. No 256-input campaign,
secondary ablation, Graph load-reuse change, VLIW/CGRA, elastic, stream,
hybrid, energy, synthesis timing, area, FPGA, ASIC, silicon, or Experience
selection is authorized.

## Required implementation evidence before freeze

- identical provider formula and invocation order for all candidates;
- 324 ascending full-word writes, accepted=completed, pending=0;
- one physical ingress and phase-exclusive provider/candidate selection;
- candidate request held or rejected before release, with no lost/duplicated
  request and exactly one execution release;
- provider cannot access output, execution, validation, or publication;
- existing execution traffic remains Graph 1,536 and each CPU 1,056 unless a
  separately reviewed source change explains otherwise;
- output bytes match the independent oracle for every input;
- source/config/artifact/toolchain/provider/contract/resource/input/output
  identities are immutable and machine-readable;
- negative tests fail on overlap, early candidate acceptance, missing or
  duplicate staging write, nonascending address, output access, pending at
  release, or identity drift.

## Stop and transition rule

Fail closed on any required-evidence failure, oracle/resource mismatch,
unexplained traffic, accounting gap, source/config drift, incomplete matrix,
or execution-window change. Passing implementation tests authorizes only a
new pre-data freeze. Passing the frozen 1/4 commissioning can yield `advance`
to the separately identified repeated campaign, `pause` at one remaining
fairness boundary, or `early no-go` on semantic/resource failure. It cannot
decide RFC-0005 go or numerical no-go.

## Estimate

The kickoff estimate is 3--7 hours for decision, implementation, unit and
negative RTL tests, plus 10--45 minutes for a warm-cache complete commissioning
at medium-low confidence. A newly invalidated CPU elaboration/build cache may
add 1--3 hours. The highest uncertainty is holding and releasing the first CPU
request without adding a port, buffer, lost request, or candidate-specific
polling protocol.
