# ADR-0117: Guest-issued MF01 execution through a host UART broker

Status: Proposed
Date: 2026-10-11
Task: T-0213 local candidate
Context: ADR-0107; Proposed ADR-0114, ADR-0115 and ADR-0116

## Purpose and scope

Continue local simulation work beyond separately compared QEMU/RTL execution.
Sonatine issues a job, the host executes the existing unchanged RTL simulator,
and Sonatine compares returned values before approving/publishing output. This
is functional coupling via a trusted host broker, not a QEMU MMIO device or a
shared-memory bus implementation. One job per guest boot is the explicit bound.
No public Issue, accepted ADR, gate transition, hardware spend or performance
claim is implied by this unpublished candidate.

## Protocol and authority

Boot envelope magic0x51464632 selects the bridge; other fields, CRC and full MF01
capacity follow ADR-0116. Magic0x51464631 retains software-only execution. After
admission and job_submission_take, the guest emits one DISPATCH-V1 line: request
ID, epoch, sequence, cookie, output count and the complete frozen envelope in hex.
The broker requires an exact match with its boot snapshot before invoking the
existing captured-input Verilator execution and transaction verification path.

Response bytes are little endian: uint32 magic0x46525231/version1; uint64
request ID/epoch/sequence;16-byte cookie;uint32 count/status;count uint32 output
words;CRC32 over all preceding bytes. Status0 means successful execution; it
cannot grant approval. Size60+4*count is bounded to1084 bytes. Each hex character
is sent only after the guest grants one UART credit ('>'). Invalid characters,
wrong size/binding/status/CRC or missing data reject the exchange. The guest uses
CLINT mtime directly because this boot path precedes timer_init. Its full receive
budget is60 seconds of the fixed QEMU10MHz timebase; this is not a timing claim.
The host UART watchdog defaults90 wall seconds. The existing RTL container has
its separate240-second process bound and cleanup bounds; the UART watchdog does
not interrupt that synchronous call or promise a90-second end-to-end bound.

The guest computes the admitted MF01 C reference and compares EVERY returned word
before posting EXECUTED, staging any output, Program approval and one finalize.
Thus the host's response status cannot bypass semantic approval. Both output
objects remain at version1/zero bytes on rejection; success produces version2
and checked data. Bound fault completion is posted/taken before rollback. A state
frame additionally checks no inflight/shadow/completion slots remain.

The trusted base includes the C reference, Sonatine authority and host tooling.
Guest input data are frozen kernel boot memory, not capability input objects;
existing placeholder resource counters do not meter actual C or RTL work.
No learned/retrieved proposal grants authority. CRC and local hashes provide
integrity checks, not authentication of a hostile peer or signed provenance.

## Evidence lifecycle

Host freezes input, kernel and boot request, captures dispatch/response/credit
wire and raw stdout/stderr, retains the full RTL record, then validates before
sealing a receipt. Verification reconstructs the same computation, exact response
or explicit test injection, final binding and phase order:
dispatch -> credits -> stable-state -> result. Duplicate/moved frames, mismatched
final cookies and relabeled evidence are rejected. QEMU is terminated and reaped
on failures; uncertain RTL cleanup stays unsealed via existing adapter behavior.

A separate lifecycle probe injects the actual successful response from a previous
terminated guest into a fresh boot of the same computation; it must reject the
old binding. Another probe expires the real host deadline and checks QEMU is
reaped, with no success receipt. These are one-session/reboot properties, not
asynchronous RTL reset, live multi-job cancellation or multi-hart isolation.

## Remaining boundary

No new QEMU device model, DMA, AXI, asynchronous reset, general floating point,
standard-IR import, physical performance/energy or Groq advantage is established.
The next coupling extension must specify a concrete need (persistent sessions,
real memory/device interface or cancellation), rather than treating this UART
prototype as evidence for those properties. Hardware acquisition remains deferred.
