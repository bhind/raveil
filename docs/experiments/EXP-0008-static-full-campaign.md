# EXP-0008: Static Graph nested-prefix latency/traffic campaign

Status: In progress
Evidence class: RTL simulation latency/traffic campaign
Date: 2026-08-14
Task: T-0044
Authority: RFC-0004, RFC-0005, ADR-0039, ADR-0046, ADR-0047, EXP-0007

## Falsifiable question

Under one common fixture-owned staging boundary, equal owned resources, and
one installed candidate session, does the static Graph executor retain a
practical correct-latency advantage over matched Rocket and BOOM across the
nested 1/4/16/64/256 fresh-input prefixes, without oracle, traffic,
accounting, identity, or execution-window failure?

## Scope and pre-data state

EXP-0008 is the separately preregistered campaign authorized by EXP-0007's
`advance`. It does not modify or reuse EXP-0007 performance values. The prior
record supplies only frozen common-boundary and stable-identity expectations.
No EXP-0008 RTL data exists yet.

Primary candidates are static Graph, Rocket in-order, and BOOM OoO. BOOM
serialize-dispatch remains diagnostic-only and is not an "OoO-disabled CPU".
Secondary matched-operation/load ablation is not activated. VLIW/CGRA,
elastic, stream, hybrid, energy, synthesis timing, area, FPGA, silicon,
general semantic attribution, and Experience selection remain out of scope.
T-0044 cannot close from this experiment.

## Session and nested-prefix contract

Each candidate runs inputs 1 through 256 in one simulator process, one reset,
one installation, and one artifact, without reload, reboot, re-elaboration, or
result/intermediate reuse. Seed equals invocation index. Prefixes 1, 4, 16,
64, and 256 are derived from that one ordered session; they are not five
separate builds and repeated deterministic execution is not another sample.
The inference unit is the fresh-input version.

All six lifecycle phases, the nested 648-cycle fixture-provider window,
execution traffic and bytes, accepted/completed/pending state, stalls,
backpressure, useful operations, current activity fields, configuration,
source, artifact, toolchain, resource, contract, input, oracle, and output
identities are recorded. Missing CPU frontend or rename/ROB/issue/LSU
instrumentation is `unavailable`, never numeric zero.

## Estimator and 95% interval

Candidate execution cycles use the median across the ordered fresh-input
prefix. An observed-input invariant receives an exact interval; otherwise the
record uses 100,000 percentile-bootstrap median resamples with frozen seeds.
Candidate comparisons are paired by invocation. Execution reports the median
of same-input Graph/CPU ratios with a paired-bootstrap interval.

RFC-0005 correct latency is the ratio of cumulative six-phase Graph cycles to
cumulative six-phase Rocket cycles at each prefix. Its paired bootstrap holds
the first invocation, including each candidate's one-time installation and
distinct initial staging boundary, fixed once and resamples paired later-
invocation vectors. Prefixes 1/4/16 are descriptive only;
64 and 256 are claim-bearing only for the bounded latency rule over this finite
deterministic seed schedule, not an unbounded workload population.

## Frozen decision rules

Any oracle/resource/traffic/accounting/source/config/toolchain/artifact/
session/matrix/window/restart/provider order/release/rearm/input/prefix failure
fails closed and produces no performance report. At prefix 64:

1. RFC-0005 latency no-go triggers if the upper 95% bound of cumulative
   correct-latency Graph/Rocket ratio is greater than 1.05.
2. Configuration break-even fails if cumulative six-phase Graph cycles have
   not become no greater than Rocket by invocation 64.
3. Either condition yields `early-no-go`; otherwise latency/traffic may
   `advance-partial` to the missing T-0044 dimensions.

The session continues through 256 after the latency evaluation so all frozen
prefixes remain available. Latency/traffic alone cannot establish go. Energy,
timing, area, IP disposition, and the missing organizations remain explicitly
unevaluated; their absence is not a pass.

## Raw, derived, and operational boundary

The collector writes one append-once 256-input raw log per matrix member,
exact command/environment/exit/wall-clock metadata, and the frozen manifest.
One separate derived report contains all five prefix summaries and paired
intervals; a raw seal binds it. A failed run receives an append-once failure
record and failed-raw seal and its RUN-ID is never reused.

Before collection the worktree must be clean, the implementation authority an
ancestor, pinned Chipyard/Rocket Chip revisions exact, and at least 5 GiB free.
Each raw candidate log is capped at 2 GiB. The collector waits at most 120
operations-only seconds for the terminal marker after Docker CLI return, then
scans marker cardinality once. Host wall-clock is operational information only.
The inherited Graph toolchain hash remains recipe/version identity because
the Dockerfile has floating apt packages and an unchecksummed scala-cli
download; it is not complete toolchain-byte identity.

## Implementation before freeze

The new `raveil.t0044_campaign` module leaves the sealed EXP-0007 collector
unchanged, verifies a full 256-input session with its existing strict parser,
derives all nested prefixes, computes paired execution and correct-latency
intervals, applies the frozen 64-input threshold, suppresses full observation
duplication in the derived report, and preserves failed raw evidence. Tests
cover account-16 parser scaling, nested-prefix derivation, positive and
early-no-go decisions, terminal-marker draining, failed-run sealing, and
EXP-0007 immutability. The implementation commit and machine-readable
manifest must be frozen before any campaign command runs.

## Frozen pre-registration

Implementation authority is
`fb8e95aca23da021918ed22d8798134d5ca99c5e`. Before any EXP-0008 RTL data,
`benchmarks/manifests/t0044-fixture-campaign-v1.json` was frozen at SHA-256
`2e2b71097bb88acf60904d17ce87ec6ec4399eaf1795a45c14542ee39f7d6359`.
The single RUN-ID is `20260814T130018Z-4368066-campaign256`. The manifest fixes
the full matrix, ordered 256-input session, five nested prefixes, fresh-input
inference unit, first-invocation-fixed paired bootstrap, 100,000 resamples,
64-input latency and break-even rules, all fail-closed conditions, identity
expectations, raw/derived separation, failure sealing, disk/log/drain limits,
and toolchain-byte limitation. No campaign command ran before this freeze.

## Estimate

EXP-0007's two complete collections used 508.863150 operations-only seconds.
The initial EXP-0008 estimate is 1--3 hours for implementation and freeze,
2--6 hours for the warm-cache 256-input matrix, and 1--2 hours for verification
and records, for 4--11 hours total at medium confidence. Cold cache rebuild may
add 1--3 hours. BOOM serialize simulation and Rocket raw trace volume dominate
the uncertainty; none of this wall-clock is CPU performance evidence.

## First collection incident and recovery boundary

The frozen RUN-ID completed the static Graph, Rocket, and primary BOOM
256-input sessions. The diagnostic BOOM serialize-dispatch session then exited
124 during invocation 115 because the shared CPU runner retained a hardcoded
3,600-second simulator timeout. This is an operational abort, not an oracle,
resource, traffic, accounting, or execution-window failure. The collector
produced no derived performance report and sealed the failed raw directory.
That RUN-ID will not be reused.

Recovery changes only the operational timeout. The runner retains 3,600
seconds as its default and accepts an explicit positive timeout; recovery fixes
10,800 seconds before retry data. RTL, the ELF workload, account, inputs,
estimator, intervals, thresholds, and decision rules do not change. A separate
recovery manifest binds the failed seal and all three completed primary raw
hashes. Those deterministic primary sessions are imported unconditionally and
are not rerun or counted as new samples. Only the diagnostic-only serialize
session is recollected under a new RUN-ID. The recovery implementation,
manifest, expected diagnostic identity, and replay command must be committed
and frozen before that session begins.

Recovery implementation authority is
`1c6160bda7325f039ef88ca1efcc50eb3a572916`. Build-only identity collection
completed without RTL execution: diagnostic source SHA-256 is
`f88406f8148fa70d0eb72757653c48476e17063dcc21967b20794b3b19228bfb`,
configuration SHA-256 is
`fa81ec09ac5d3c4f9a93a5fe08e8b8e9256e9fb86b1bf8b03351a79875c0a381`,
and the build-only ELF artifact is
`b0f152028d3543997c8e9508289c60f95cf73b166dc3115a032ca6c1a43a89d4`.
The failed raw seal is
`88fe79590c3ea98129d57363920686b084fb10b45e2a9c5fc0b53db3f3bc8726`.
Before retry data, recovery manifest
`t0044-fixture-campaign-recovery-v1.json` is frozen at SHA-256
`c9226d05f348c740801b7cbceb673514495c3f5fc15c1192629f31b2f58a1eb6`
with RUN-ID `20260814T153738Z-0203248-campaign256-recovery`.

The recovery simulator command subsequently completed all 256 inputs at exit
zero, but the first post-processing attempt raised an `AttributeError` because
the new recovery adapter passed `variant, path` to the existing
`parse_variant_log(path, variant, account)` API. Raw collection was already
complete and no log was rerun or modified. A focused regression fixes only this
adapter argument order before deriving and sealing the same raw directory.
The runtime session artifact is independently bound as
`1b097009c39e773b0c567ceafded69be95be11d5b0210141d300423467edea4b`;
the frozen policy never treats a separate build-only artifact as byte-equal
session evidence.
