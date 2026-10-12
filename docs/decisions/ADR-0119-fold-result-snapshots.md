# ADR-0119: Named committed results as MF01 snapshot inputs

Status: Proposed
Date: 2026-10-11
Task: T-0215 local candidate
Context: ADR-0107; Proposed ADR-0118

## Contract

A predeclared1..8-job chain accepts literal arrays or `{"from":"earlier-name"}`
for either logical input. Both links must name the same producer. Linked length
must equal that producer's logical output count, excluding zero padding. Names
must be unique and links backward. Boot bytes use chain magic0x51434631/version1,
24-byte header as in ADR-0118, then uint32 producer-index/input-mask plus each
existing bridge envelope; footer CRC/end0x43454e44. No-link index is UINT32_MAX,
mask0. Linked inputs are zero placeholders; nonzero placeholders reject.
Maximum23,232 bytes. Entire admission precedes initialization/dispatch.

## Snapshot and publication authority

Register four512-byte objects as two banks. A literal-only job writes the bank
opposite the last successful destination. A linked job reads the exact producer's
bank and writes the other bank. Both destination objects are full zero-padded
replacement. Bank versions are independent: e.g.(2,1)->(2,2)->(3,2).
Remember producer success, bank, version and logical count. An unavailable or
overwritten producer halts before allocating sequence/ledger entry; no fallback.
An older producer in a still-current bank remains usable.

After plane_job_submit_bound/job_submission_take, read the two source objects
through job_submission_read. Copy the logical prefix into either/both linked
arrays, re-encode the derived envelope and issue it to the broker. There are two
unique READs and two WRITEs, never duplicated READs or READ|WRITE aliases.
Compute the guest C reference from these derived inputs before semantic approval.
Finalize preserves source bytes/version and atomically publishes both destination
objects. Fault rollback preserves both entire banks. Fully received bad responses
permit a later explicit retry against the still-valid source. Framing loss halts.

Input resources count1,024 uniquely referenced object bytes even when both
logical arrays reuse them. This does not meter duplicated interpreter buffers,
literal arrays or runtime work. Literal inputs remain frozen kernel boot data.
Capability/snapshot enforcement is claimed only for linked object inputs.
Experience remains observation, not authority. Host SSA comparison is an
independent checker of the guest-derived request, never a source of guest input
or publication authority. CRC/hashes are integrity checks, not authentication.

## Evidence and bounds

Retain frozen chain/plan/envelope/kernel, every guest-derived request, raw protocol
and independent RTL record. Verify exact source bank, both bank contents/versions,
phase order, completion binding, named dependency availability and terminal block.
The class is host-mediated-QEMU-RTL-chain-functional. Failed dependencies have
no dispatch/RTL receipt. Revalidation runs no simulator. Receipt publication is
atomic after verification; uncertain cleanup stays unsealed.

Sequential, predeclared, one distinct producer/job, at most8 jobs. Not a general
fan-in graph, interactive server, persistent RTL process, live cancellation,
independent reset, MMIO/DMA/AXI or measured hardware implementation. Existing
separate watchdog/RTL cleanup bounds remain. No novelty/Groq/performance claim.
Proposed only; canonical/public task state and accepted ADRs are unchanged.
