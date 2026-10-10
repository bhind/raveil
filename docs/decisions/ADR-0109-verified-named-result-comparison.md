# ADR-0109: Compare verified named results without executing them again

Status: Accepted
Date: 2026-10-10
Task: T-0205 / Issue288
Authority: continuous simulation implementation under ADR-0107; the prepared
successor closes the edit/run/inspect/compare gap after T-0197 / ADR-0108.

## Decision

Add `project composition-diff OLD NEW`. Both attempts belong to the selected
project and must be complete, with all existing parent/child/oracle checks
passing. Match outputs by their unique names, independent of child order.
Require identical name sets, output rows/columns/stride and simulator, RTL and
source build identities. Reject incompatible or incomplete attempts; never
silently compare a subset or treat incompatible data as unchanged.

Inputs and descriptors may differ: those are the edits the operation explains.
Show their frozen hashes, output hashes, common build identities, changed input
word count and per-name changed active-cell count plus first changed coordinate
and before/after values. The existing validator ensures inactive output words
are zero; compare the verified active text values rather than truncating raw
unvalidated data. Output is bounded by two names and one first difference per
name. No automatic numerical tolerance or speed interpretation is introduced.

Capture and validate both parents, compute the report, then revalidate before
returning it. A changed record during capture fails closed. Do not execute,
rebuild, rewrite, export or repair either attempt. This is the existing
cooperative local-integrity boundary, not authenticated provenance or a hostile
concurrent-writer guarantee. Existing single-run diff remains unchanged.

## Acceptance and evidence

Host tests cover identical/edited data, reordered labels, incompatible labels,
layout/build differences, incomplete/unsealed/tampered artifacts, concurrent
cooperative drift, CLI compatibility and no execution/writes. An actual cached
RTL demo creates A, edits input and one descriptor, creates B, compares named
outputs, checks scalar expected changes and verifies A remains unchanged.
Read-only comparison is Host Functional; fresh child execution is RTL Simulation.
No hardware, timing, shared arithmetic or QEMU/RTL integration claim is made.
The combined ADR-0107 maturity review remains a separate evidence decision.
