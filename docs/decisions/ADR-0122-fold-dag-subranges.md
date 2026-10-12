# ADR-0122: bounded producer subranges in local MF01 DAGs

Status: Proposed
Date: 2026-10-11
Task: T-0219
Context: ADR-0107 simulation maturity; Proposed ADR-0120/ADR-0121

## Problem

Whole-result links force a consumer to reference every producer chunk. Two
256-word producers need four READ references before any destination, exceeding
the existing four-reference job ABI even when the consumer needs only128 words
from each. A useful bounded continuation is explicit input intervals.

## Local candidate

`raveil.fold-dag.v2` accepts an earlier producer either as the existing whole
`{"from":"name"}` link or as `{"from":"name","offset":128,"length":128}`.
Offsets/lengths are uint32 word units. A linked length is positive, equals the
consumer buffer length, and fits the producer's logical output. Literals can
still have zero length if unused by the MF01 program. V1 retains its old grammar,
wire encoding, full-result admission and saved preview.

Wire version2 carries `(producer, offset, length)` as three little-endian uint32
fields per operand, followed by the unchanged MF01 request. Literals carry
UINT32_MAX, zero, and their consumer length. Header/CRC/footer and whole-plan
admission are retained; maximum envelope size is23,368 bytes for eight jobs.
Unknown versions, mismatched lengths and noncanonical literal offsets reject.

The host and C planner union touched `(producer,chunk)` identities across both
operands. Unique READ chunks plus destination chunks must fit four references.
Allocation still retains the WHOLE producer until its last consumer, preserves
all producer versions and pins the designated output. This avoids introducing
partial reclamation or independently versioned logical slices.

The guest declares full512-byte READ references for touched slots; authority
therefore remains conservative at object granularity. It materializes only the
requested word segments with `job_submission_read`, splitting at128-word chunk
boundaries. It then emits the unchanged MF01 request and retains pre-publication
semantic checking, rollback, failure halt and saved evidence reconstruction.
Object count/size, job references, eight-job bound and RTL source are unchanged.

## Evidence and limits

Acceptance and exact commands belong in STATUS and the dated log after running.
No new authority ABI, physical transport, concurrency, loop, spill mechanism,
performance or Groq advantage is claimed. Range views, chunk accounting and
liveness are established techniques; this is a practical implementation extension.
Canonical/public adoption of this local candidate remains pending.
