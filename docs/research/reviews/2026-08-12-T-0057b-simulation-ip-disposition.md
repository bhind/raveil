# T-0057B simulation-only IP disposition

Status: Non-authoritative engineering review
Date: 2026-08-12
Task: T-0057
Decision context: RFC-0005, ADR-0039
Evidence class: patent-document and prior-art triage; not legal advice

## Scope

This review compares only the bounded installed static region proposed by
RFC-0005 with the three patent documents already discovered by T-0057A. It
supports a Project Manager decision about a repository-owned research
simulation. It is not a patent search, claim construction, infringement
analysis, validity opinion, legal-status verification, license, research-use
exemption, or freedom-to-operate conclusion.

The inspected pages are Google Patents discovery records. Their displayed
status, family, ownership, and expiry fields explicitly disclaim legal
analysis. Those fields remain unverified.

## Fixed candidate features

The accepted-for-review candidate has exactly one issue organization:

- compiler-emitted operation graph lowered before execution to one
  cycle-indexed fixed schedule;
- no runtime dependency-ready issue, token matching, target-instruction fields,
  issue-window mode switching, register rename, ROB, general LSU, or commit
  frontier;
- one affine uint32 five-point stencil over disjoint read-only input and
  private-output scratchpad ranges;
- no wave number, wave-ordered memory, atomics, MMIO, coherent shared write, or
  precise mid-region restart;
- cancellation or fault invalidates the private output and restarts the normal
  RV64IM fallback from the beginning;
- no upstream Graph/dataflow RTL or compiler source copied into the owned
  implementation.

Changing any item requires a new prior-art/IP review before implementation.

## Feature-to-document triage

### US7490218B2, *Building a wavecache*

Inspected locator: claims 1, 10, 21, and dependent claims on the discovery
page. The reviewed independent-claim text centers on a dataflow computing
device without a program counter, autonomous processing elements, waves and
wave-number tags, wave-ordered memory, and transitions between ordered and
unordered memory execution. The description also discusses instructions
remaining in processing elements across invocations.

RFC-0005 does not define waves, wave tags, autonomous dataflow firing,
wave-ordered memory, or ordered/unordered memory transitions. Its fixed
schedule and affine iteration controller are not represented as a WaveCache.
However, the inspected patent is related to US7657882B2 and other WaveScalar
material not claim-charted here. Resident-configuration similarity therefore
remains an adoption hazard. The discovery page displays US7490218B2 as
fee-related expired, but that status is not independently verified and does not
resolve related rights or other jurisdictions.

Disposition: do not implement WaveScalar firing, waves, wave memory, PE operand
tag matching, or dynamic placement. Static configuration remains
`unreviewed`, not cleared.

### US10824429B2, *Commit logic and precise exceptions in explicit dataflow graph execution architectures*

Inspected locator: claims 1, 7, and 14. The claim text describes a block-based
processor ISA, dependency evaluation and ready issue, a commit frontier, and in
one claim saved transient state used to resume after an exception. The
discovery page displays a US active status and related EP/PCT applications;
none was independently verified.

RFC-0005 has no block-based product ISA, dependency-ready scheduler, commit
frontier, individual architectural instruction commit, saved transient Graph
state, or mid-region resume. The executor writes only a private output; trusted
host control either publishes that object after independent validation or
invalidates it and runs RV64IM from the beginning.

Disposition: do not add dependency-ready issue, partial commit, a commit
frontier, defunct-instruction handling, or precise Graph resume. Private-output
completion remains `unreviewed`, not cleared.

### WO2015069583A1 and US9547496B2, *Energy efficient multi-modal instruction issue*

Inspected locator: WO claims 1, 3, and 6 and the linked US-family record. The
claim text describes choosing or switching between issue modes, including
in-order and OoO logic, based on block metadata, an identifier, or another
characteristic. The WO page displays ceased status, while the linked US record
displays active status and EP/CN family entries. Those statuses are not legal
conclusions.

RFC-0005 implements one fixed static executor. It does not retain two Graph
issue units, choose a mode from metadata, switch between OoO and in-order issue,
or clock-gate an OoO issue unit based on a region characteristic. Rocket/BOOM
are separate experimental controls, not modes inside the candidate processor.

Disposition: do not implement runtime issue-mode selection or candidate-local
OoO/in-order switching. The family remains `unreviewed`, not cleared.

## Literature similarity and missing searches

DySER remains high technical similarity for a compiler-selected repeated
region, static functional-unit routing, and retained host processor. No
definitive DySER patent-family search has been completed. EPIC/VLIW, TRIPS/EDGE,
WaveScalar, CGRA, loop-accelerator, HLS, scratchpad, private-buffer publication,
and static-schedule patent landscapes are not exhaustively searched.

Open-source and academic publication licenses do not grant a patent license.
Independent repository authorship does not itself establish non-infringement.

## Engineering disposition

Proceed only with a bounded, non-product, repository-owned RTL simulation of
the exact RFC-0005 candidate. Keep all output labelled simulation-functional
and performance-not-measured. Do not publish an FTO, novelty, safety, silicon,
or product-readiness claim.

Stop and re-review before any custom ISA, direct consumer targets, runtime
dataflow firing, wave memory, multi-modal issue, precise Graph exceptions,
partial architectural commit, variable-latency elastic scheduler, FPGA,
silicon, commercial distribution, or external implementation reuse.

Qualified legal review remains required before a conclusion beyond this
engineering research boundary.
