# ADR-0120: Whole-plan reference and lifetime admission for MF01 DAGs

Status: Proposed
Date: 2026-10-11
Task: T-0216 local candidate
Context: ADR-0107; Proposed ADR-0118 and ADR-0119

## Simpler common rule

Use the existing authority limits instead of adding special merge hardware or
widening the ABI. Each result uses ceil(logical_words/128)512-byte objects.
For each node: unique linked READ objects + destination WRITE objects <=4.
Deduplicate shared producer inputs. Two128-word producers to256 words fits1+1+2;
256+128 to128 words fits2+1+1;256+256 to any output needs at least5 and rejects.
Literal inputs retain the existing frozen boot-data boundary.

## Whole-plan lifetime allocation

A graph contains1..8 uniquely named topological jobs and one named output. Each
input is a literal array or exact earlier producer; linked length must equal the
producer's logical output. Compute last consumer for every producer, pin the
named output through session end, and allocate each destination's one/two chunks
from lowest-numbered free slots. A slot is free only if unowned or last_use<i;
current READs cannot alias destination writes. Reject the entire graph before
session initialization/dispatch if any reference or allocation fails. Allocation
is conservative and fixed regardless of execution outcome.

Register eight512-byte objects once. Reclamation changes logical ownership only;
never unregister/reset authority or object versions between nodes. Source identity
records success and per-chunk(object ID,generation,version). Destination chunks
can have unequal version histories. Each successful finalize increments each
written object from its own current version, preserving every other byte/version.
Full destination chunks are explicitly zero-padded replacement. Every linked
array is materialized by guest job_submission_read after take and before
completion. Host SSA/model verification does not grant guest authority.

A failed node creates no result. A dependent node stops before submission, rather
than consuming old contents or another successful result. Framed faults may allow
independent later nodes; lost framing halts the remaining graph. The designated
output may already be available despite a later unrelated failure; availability
is reported separately from processed count, per-job success and halt state.
A failed designated output has no fallback. Historical receipt bytes survive
object reuse; historical object versions do not become newly readable live results.

## Protocol and evidence

DAG boot header is32 bytes: uint32 magic0x51444631/version1/size/count,
uint64 epoch, uint32 output-index/reserved0. Each child has two uint32 source
indices (UINT32_MAX means literal), followed by the existing bridge envelope.
Linked payload arrays must contain only zero placeholders. CRC/end0x44454e44
complete the40-byte overhead; maximum23,240 bytes. Full C and host admission
reconstruct the same plan independently.

State frames contain READ/WRITE slot masks, all eight versions, all4,096 bytes
and empty queues/ledger checks. DAG alone uses a bounded16,384-byte host line
limit because8,192 hex payload characters plus header exceed the older8,192-byte
bound. Existing callers retain their default bound. Captured guest-derived inputs,
RTL evidence, response binding, phase order, allocations, padding, rollback,
terminal dependency block and designated output are revalidated before atomic
receipt publication. Evidence class: host-mediated-QEMU-RTL-dag-functional.
The read-only --check preview reports static admission, never execution evidence.

## Limits and claims

Bounded predeclared sequential uint32 DAG, not concurrent/out-of-order execution,
spilling, unrestricted graph/control flow, persistent RTL service or a QEMU device.
Resource fields bound unique object references, not measured literal storage,
interpreter scratch/runtime or RTL timing. UART and simulator/cleanup watchdogs
retain their distinct bounds. Host tools, guest C semantics and authority remain
trusted; hashes/CRC are integrity checks, not authenticated provenance. No
hardware, performance, energy, novelty, patent or Groq advantage is established.
Liveness allocation and static dependencies alone are not novelty claims.
This Proposed local candidate changes no accepted ADR or public task/gate state.
