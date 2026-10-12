# ADR-0118: Bounded sequential MF01 guest sessions

Status: Proposed
Date: 2026-10-11
Task: T-0214 local candidate
Context: ADR-0107; Proposed ADR-0114 through ADR-0117

## Scope and admission

Admit1..8 distinct nonzero request IDs in a single boot envelope. A24-byte header
contains uint32 magic0x51534631/version1/size/count and uint64 nonzero epoch.
Existing bridge envelopes follow, then CRC32 and end0x53454e44. Maximum23,168
bytes. Validate every child and both levels of integrity before any session
initialization or dispatch; a malformed later child rejects the entire bundle.
CRC is an integrity check, not authentication.

## Authority and publication

After existing bootstrap diagnostics, initialize job authority and plane registries
exactly once. This clears the diagnostic Experience entry so the session owns all
8 existing ledger slots. Capability handles and boot diagnostics remain intact.
Install program/graph and register two512-byte objects at generation/version1.
Do not reset between jobs, including rejection. Each submission consumes a unique
sequence and one ledger entry. Epoch remains constant and each response binds
request ID, epoch, sequence and cookie.

Each job stages both full512-byte objects with zero padding beyond logical output.
Both versions increment once on success. This is deliberate replacement policy;
the existing authority correctly writes only declared ranges and does not itself
zero unreferenced tails. Guest C checks every RTL value before completion/staging/
approval. On a completely received invalid response, record bound fault, rollback,
check unchanged entire1,024 bytes and versions, then continue. On lost framing
(invalid character, timeout, truncation), rollback then halt without attempting
UART resynchronization. Authority/cleanup uncertainty also halts. No rejected
named result is silently substituted by a last success.

## Evidence

State frames disclose entire256-word output, version, ledger and empty authority
queues. Host verification independently reconstructs padding, rollback, phase
order, exact binding and unchanged RTL build/options/computation. Every processed
job has a distinct retained RTL record. Unexecuted jobs after framing loss have
no job record. Saved validation executes neither QEMU nor RTL. Preseal verification
must pass before atomic receipt publication; cleanup uncertainty stays unsealed.
The evidence class is host-mediated-QEMU-RTL-session-functional.

## Limits

Predeclared sequential independent inputs; not an arbitrary interactive stream,
result-dependent DAG, concurrent execution or persistent RTL process. Each job
uses the existing simulator invocation. Inputs remain kernel boot data and
placeholder runtime/scratch counters do not meter work. The host UART watchdog
and simulator/cleanup bounds remain separate as in ADR-0117. No asynchronous
reset, live cancellation, DMA/MMIO/AXI, timing, FPGA, silicon or Groq advantage.
No accepted ADR or public task state changes through this local packet.
