# ADR-0121: Captured DAG execution in the project workspace

Status: Proposed
Date: 2026-10-11
Task: T-0217 local candidate
Context: ADR-0107; Proposed ADR-0120

## Reuse one executor

Add project dag-check/dag-run/dag/dags/dag-diff around the existing
fold_dag.preview/run/verify path. No second guest or RTL executor, ABI, schedule,
capability boundary or hardware mechanism is introduced. Capture one inputs/
JSON file containing the complete admitted graph/literals/links. Names are confined
JSON filenames; duplicate fields, links, special files and oversized input reject.
The explicit1MiB input bound admits eight literal-heavy jobs that can exceed the
older single-fold64KiB text bound. Existing16MiB/1024-entry evidence limits remain.

Read/admit source and kernel, verify runtime identity, allocate a fresh dags/ID,
then freeze exact input bytes, kernel bytes and a private runtime snapshot. Execute
only from these captured sources. Bind source digest, static admission preview,
kernel digest and runtime manifest identity. Later source edits cannot affect the
attempt. Saved inspection uses the frozen sources and does not require the current
kernel, original build, QEMU or Docker.

## Evidence/publication

The parent validates the existing full child DAG receipt, confirms exact captured
session/kernel/build, inventories all nested files and derives parent status.
All nodes approved/completed with no halt means succeeded. Otherwise incomplete;
a pinned output may still be separately available. An unavailable designated
output has no fallback. Compare only two verified available outputs with the same
kernel/runtime identity, output name and shape, and display both execution statuses.
Compare logical values, not random request IDs/epochs or object-version counters.

Validate exact scalar types for counters and designated output metadata/uint32
words. Canonical structured comparison binds derived preview/session/output fields;
Python numeric equality alone must not accept floats as integer evidence or integers
as booleans. File/hash consistency is not authenticity against a cooperative host
that rewrites all evidence; it still rejects inconsistent or malformed proofs.

Write pending payload and hash, then hard-link to record.json with no overwrite.
That link is the publication point. Interruption before publication, execution
exceptions and uncertain cleanup leave unsealed diagnostics. Interruption after
the link returns/revalidates the already published record. History scans actual
record directories and verifies every sealed entry; it does not trust a mutable
index. The existing DAG executor owns process/container cleanup. No new live
cancellation callback or cancellation guarantee is implied.

## Scope

Same bounded predeclared sequential MF01 DAG and linked-input authority as
ADR-0120. Literal inputs remain frozen boot data. Preview is static admission;
actual records are host-mediated-QEMU-RTL-dag-functional; saved comparisons are
saved-functional-comparison. Unit-test child fixtures are not actual execution.
No timing/hardware/novelty/Groq advantage claim or public task/gate transition.
This is a Proposed local usability candidate, not canonical accepted architecture.
