# EXP-0007: Fixture-owned input staging boundary

Status: In progress
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

This record allocated EXP-0007 before implementation or data. It does not
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

## Implemented boundary and pre-freeze evidence

The shared provider is instantiated in both `StaticStencilRegion` and the
Rocket/BOOM owned-memory manager. It owns no memory or oracle state, uses the
existing single request/response ingress, permits one outstanding write, and
emits the accepted address/data for all 324 words. Its final response-consume
is the sole execution release, and the final ordered validation response is
the sole rearm. The CPU fixture kernel contains neither the formula nor input
stores; an empty compiler memory barrier prevents cross-invocation C
optimization without adding a CPU runtime fence or disabling lawful
within-invocation load reuse.

The new resource SHA-256 is
`87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7`.
The verifier reconstructs input hashes from the accepted RTL trace and rejects
bad bytes, order, count, overlap, release cycles, rearm, pending state, resource
identity, lifecycle ordering, or inherited collector modes. The focused
Python/source suite passed 74/74. A pre-freeze linux/amd64 Docker/Verilator
Graph run passed four fresh inputs with 648 provider cycles, 3,072 execution
cycles, one completion cycle, 512 validation cycles, 4,233 total cycles, and
1,536 execution transactions each. These values establish implementation
behavior only and are not commissioning data or a performance claim.

The first CPU elaboration attempt failed before simulation because the held-A
assertion directly named optional token fields that the standard fixture
configs do not negotiate. The replacement implementation iterates every
actually negotiated `BundleMap` user field and snapshots it generically; it
therefore checks the complete present payload without inventing absent fields
or weakening future metadata checks. After that correction, pre-freeze
one-input Rocket, BOOM, and diagnostic BOOM runs each exited zero. Rocket and
BOOM both observed the 648-cycle provider window, 800 execution reads, 256
execution writes, zero pending or unexplained traffic, and oracle-matching
output; BOOM's execution window was 22,170 cycles and the diagnostic
serialize-dispatch window was 70,911 cycles. These qualification values are not
EXP-0007 data. The failed builds are not data and their obsolete source hashes
are not freeze authority.

For later invocations, lifecycle staging begins at the preceding validation
rearm and includes candidate-visible control progress until provider release;
the nested provider window begins at its trigger and is exactly 648 cycles.
This preserves all cycles instead of hiding CPU loop/control work. The final
manifest must keep both meanings separate.

The Graph toolchain SHA binds the pinned base image, version strings, and
Dockerfile recipe, but the inherited Dockerfile still uses floating apt
packages and a download without a byte checksum. EXP-0007 therefore calls it
recipe/version identity, not complete toolchain byte identity. This limitation
must remain explicit in the frozen manifest and final eligibility finding.

## Frozen pre-registration

Implementation authority is
`8e96d24188df9ab83eb7ed0f700b4db914174c33`. Before any EXP-0007 commissioning
data, `benchmarks/manifests/t0044-fixture-owned-staging-v1.json` was frozen at
SHA-256
`c9b0f9d307421cfd611978c4e221d84faeb939f0630c4b9818180630c5f26c57`.
It fixes the complete primary plus diagnostic matrix, fresh input versions,
one-process/one-reset/one-install session contract, all phase meanings,
required traffic and activity fields, median estimator, exact-or-bootstrap 95%
interval rule with 100,000 resamples and seed base 7007, stop conditions,
identity drift rules, and the recipe-identity limitation. Frozen run IDs are
`20260814T115314Z-8e96d24-commission1` and
`20260814T115314Z-8e96d24-commission4`.

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
