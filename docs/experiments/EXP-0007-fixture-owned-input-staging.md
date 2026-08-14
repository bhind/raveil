# EXP-0007: Fixture-owned input staging boundary

Status: Completed
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

After the first frozen end-to-end matrix completed, the remaining estimate was
updated to 1--3 hours at medium-to-high confidence for the four-input run,
record reconciliation, and regression checks. The two complete collections
used 508.863150 operations-only wall-clock seconds in total: 181.392233 seconds
for account one and 327.470917 seconds for account four. This host time is not
CPU performance evidence.

## Completed commissioning evidence

The frozen runs are:

- account one RUN-ID `20260814T115314Z-8e96d24-commission1`, derived-report
  SHA-256 `2310f9a9ee662c2e37873de392f38ecef657bab7d766c9b9282b80f52767f62a`,
  and raw-seal SHA-256
  `5abb2b90281218690647c4b6dc7f4a8f0be6a7a06c4aa849c8308ebc4d314fce`;
- account four RUN-ID `20260814T115314Z-8e96d24-commission4`, derived-report
  SHA-256 `fb7f5e1e3b3a070ca13582e6daf13940df4c04129f539d917dc1c196a2d49320`,
  and raw-seal SHA-256
  `4c6d105861dd6030d38976d90fdacb8c9db52e249cac3be9300aaf7a12ce2c54`.

Both collections ran at freeze commit
`790ed61b45f51cdb2642b46c0259fb1e1da41443` on an Apple Silicon host operating
the pinned `linux/amd64` Docker/Verilator paths. Chipyard was
`ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1` and Rocket Chip was
`749a3eae9678bc70b029c5b9091fae33fad539c4`. Every one of the eight candidate
commands exited zero. Raw logs, command arguments, selected environment, exit
codes, byte counts, wall-clock operations data, and hashes are under each
RUN-ID's `raw/`; derived reports are separate under `derived/` and are bound by
the raw seals.

Every one of inputs 1--4 has a distinct input hash and oracle-matching output
hash on every candidate. Each session has exactly one process, reset,
installation, and artifact, with zero reloads. Cross-account source,
configuration, toolchain, contract, resource, and input-one output identities
pass. Account one and account four are separately compiled bounded-session
artifacts and their artifact hashes are therefore bound per session rather
than asserted equal across accounts.

### Primary latency and traffic

Cycles below are exact RTL-simulation counts for four ordered fresh inputs, not
independent repeats of one deterministic input. The median 95% interval is the
frozen 100,000-resample percentile bootstrap for input-varying candidates and
an exact observed-input invariant for Graph. At four inputs it is descriptive
commissioning evidence, not population inference. `Total@4` sums all lifecycle
phases and includes the one-time installation.

| Candidate | Execution cycles, inputs 1--4 | Median (95% interval) | Execution traffic/input | First-input I/S/E/C/V/P | Total@4 |
| --- | --- | --- | ---: | --- | ---: |
| Static Graph | 3,072 / 3,072 / 3,072 / 3,072 | 3,072 (exact) | 1,536 | 0 / 648 / 3,072 / 1 / 512 / 0 | 16,932 |
| Rocket in-order | 14,594 / 14,539 / 14,539 / 14,539 | 14,539 (14,539--14,594) | 1,056 | 46,186 / 648 / 14,594 / 16 / 4,360 / 0 | 124,561 |
| BOOM OoO | 21,889 / 21,893 / 21,893 / 21,893 | 21,893 (21,889--21,893) | 1,056 | 46,285 / 648 / 21,889 / 14 / 6,631 / 0 | 163,128 |

The median execution-window ratios are 4.733x Rocket/Graph and 7.127x
BOOM/Graph. They are bounded pilot observations, not an RFC-0005 go decision.
Each input reports 1,280 useful loads, 1,024 adds, 256 useful stores, and 256
outputs. Graph admits/completes 1,280 reads plus 256 writes (5,120/1,024 bytes);
each CPU lawfully reuses loads and admits/completes 800 reads plus 256 writes
(3,200/1,024 bytes). Every candidate also admits/completes 324 fixture staging
writes through the same ingress in an exact 648-cycle nested provider window.
Pending, unexplained traffic, request stalls, and response backpressure are
zero. Graph records 3,072 schedule-active cycles; CPU frontend and
rename/ROB/issue/LSU activity remain unavailable and are not imputed as zero.

Later CPU lifecycle staging is 677--719 cycles for Rocket and 682--683 cycles
for BOOM because it deliberately begins at the preceding validation rearm and
includes candidate control progress before the identical 648-cycle provider
window. Graph has no analogous loop work and remains at 648 cycles. The common
provider itself, its memory traffic, and its release boundary are equal; the
visible outer staging difference is retained rather than normalized away.

### Diagnostic only

BOOM serialize-dispatch records 70,789 / 70,774 / 70,774 / 70,774 execution
cycles, median 70,774 with descriptive interval 70,774--70,789, 1,056 execution
transactions per input, and `Total@4` 396,308 cycles. It is a same-core
diagnostic only, is not an "OoO-disabled CPU", and does not replace either
primary CPU. The secondary matched-operation/load ablation was not activated.

### Immutable identities

The common fixture contract SHA-256 is
`64b14ad77baba722a0e9f5d6c7403783c07fcfd49c1b7c96cca1b7406be84861` and the
common resource SHA-256 is
`87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7`.
Account-four identities are:

| Candidate | Source SHA-256 | Configuration SHA-256 | Artifact SHA-256 | Toolchain SHA-256 |
| --- | --- | --- | --- | --- |
| Static Graph | `739ed0e3a4dcdff546761d337261a2b2b67f49911224fb982307e01f702d38fd` | `f007981d5a593ccc7c7c34d0a498179be8fe55881472cb55af2a0dbd989267e1` | `6537049559af77cdcab213b17edd13e04719b60e22e71c9457b730f94d4758af` | `2009341570a17fbe47fb9600be97eec8fa50b1dceba0b04357c2eb01fe947037` |
| Rocket in-order | `44430323d4e62ba2b48c0a8f611536740cfd4dc4dc4a8a5e1cd806abb447e65d` | `d6e3bfcedf2b9ec1a688469c2f0171fe704dac1bc85423dbeb21a65aaae5fcd2` | `0c03d451542bc1b5f29f3025de336cad0520a27adcfb20e68bfe8b323aeb6486` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |
| BOOM OoO | `ccc85c069dc760fca23609ca804b1e8e3737e3eb7404c7b79162b3af74ea774a` | `ae6a2f9479b3d96f8fc24870b44f10e630b08a17ddcb8ec256a4a9dd4f1e9ab0` | `02d347e54fef7c3ec6bd9f50ed70da7f2de97da12d92725b1e66c00e4fbbec45` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |
| BOOM serialize diagnostic | `812f2127cddf6afe2116006e3fa2361b1dfffa1b59f29151439b5c33d197e336` | `9dee2b77536883bcb1030d1f6f5d439f46202a10c14bd5ead1973f11813fba7c` | `ef3dc87b299bd24419f2e298ea5f9cf32af9d712ae4318c5ff9e2bdbc7802e9d` | `ae2488b8904a8f6246a11df60be85bc08e965c3aee0518c976319bc34d448eee` |

The Graph toolchain identity limitation frozen above remains: it is a pinned
recipe/version identity, not proof of every installed package byte.

### Fairness and terminal decision

The common fixture-owned initiator removes EXP-0006's staging asymmetry without
adding a port, bank, request buffer, candidate polling path, or CPU
weakening. The primary execution window now has the same meaning, preserves
lawful CPU load reuse, and exposes Graph's extra 480 transactions per input as
a schedule/design result. Dynamic traffic inequality is explained and does
not make the primary comparison ineligible. Secondary ablation is unnecessary
for this commissioning decision.

The result is still **partial / RTL-simulation pilot**: four fresh inputs are
below RFC-0005's 64-input numerical-no-go floor, no latency/traffic pilot can
establish go, and energy, synthesis timing, area, VLIW/CGRA, elastic, stream,
and hybrid candidates are absent. T-0044 remains open.

**Decision: `advance` — the complete 1/4/16/64/256 measurement may proceed
under a separately frozen campaign record; EXP-0007 itself authorizes no such
data and decides neither RFC-0005 go nor numerical no-go.**

## Exact collection and clean-checkout replay

The exact argv, selected environment, timestamps, and exit code zero for every
candidate are sealed in each RUN-ID's `raw/commands.jsonl`. The equivalent
top-level collection commands are:

```sh
RAVEIL_REPO=/path/to/clean-raveil-worktree
RAVEIL_CHIPYARD_SOURCE=/path/to/pinned-chipyard
python3 -m raveil.t0044_fixture collect \
  --repo "$RAVEIL_REPO" \
  --run-dir "$RAVEIL_REPO/artifacts/research/EXP-0007/20260814T115314Z-8e96d24-commission1" \
  --manifest "$RAVEIL_REPO/benchmarks/manifests/t0044-fixture-owned-staging-v1.json" \
  --chipyard-source "$RAVEIL_CHIPYARD_SOURCE" \
  --account 1
python3 -m raveil.t0044_fixture collect \
  --repo "$RAVEIL_REPO" \
  --run-dir "$RAVEIL_REPO/artifacts/research/EXP-0007/20260814T115314Z-8e96d24-commission4" \
  --manifest "$RAVEIL_REPO/benchmarks/manifests/t0044-fixture-owned-staging-v1.json" \
  --chipyard-source "$RAVEIL_CHIPYARD_SOURCE" \
  --account 4
```

For clean replay, check out freeze commit `790ed61b45f51cdb2642b46c0259fb1e1da41443`
in a new worktree, provide Chipyard at the pinned revision with Rocket Chip at
its pinned revision, verify a clean status including untracked files, and run
the commands above with new empty RUN-ID directories. Never overwrite the
sealed RUN-IDs. Compare the new raw seals and reports as reproducibility
evidence; do not count an identical-input deterministic replay as another
fresh-input sample.

## Closeout verification

The focused fixture/repeated/pilot/controlled/owned-memory/static-region suite
passed 82 tests, and the separately requested controlled-run suite passed 10.
The T-0042 three-way replay first exited one because the dedicated worktree had
no default external dependency checkout, then exited one when only Chipyard
was supplied and the separate Rocket Chip source remained absent. With both
pinned external paths explicitly supplied, the same replay exited zero and
returned `comparison_eligible=true`, resource equality and traffic conservation
true, `dynamic_memory_traffic_equal=false`, `semantic_initiator=not-proven`,
and `t0044_measurement_claim_ready=false`. This is a legacy T-0042 functional
regression, not EXP-0007 performance data; its old initiator field does not
override the fixture evidence.

The closeout commands were:

```sh
python3 -m unittest tests.test_t0044_fixture tests.test_t0044_repeated \
  tests.test_t0044_pilot tests.test_controlled_run \
  tests.test_owned_memory_boundary tests.test_static_region -v
python3 -m unittest tests.test_controlled_run -v
RAVEIL_CHIPYARD_SOURCE=/path/to/pinned-chipyard \
RAVEIL_ROCKET_CHIP_SOURCE=/path/to/pinned-rocket-chip \
  ./hardware/chisel/run-controlled-three-way-stencil.sh
python3 .agents/skills/raveil-task-governance/scripts/check_records.py
git diff --check
git merge-base --is-ancestor ae606de HEAD
```
