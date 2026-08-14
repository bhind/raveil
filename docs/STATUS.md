# Current status

Last updated: 2026-08-12
Development state: `unreleased`
Latest feature release: `v0.0000000000001` (`10^-13`), immutable historical seed
Current Pre-release: `v0.0000000000002`, T-0092 Sonatine operator demo,
published from `d59873cb8e27bf033b32a2a72d2fa3d04576dc79`
Current corrective Pre-release: `v0.0000000000003`, T-0096 interactive
control fix, published from `c8002cf4d87e6a0a907f9327dc42cce2c90e9673`
Current Native Pre-release: `v0.0000000000004`, T-0099 Native CLI workspace,
published from `3cfb13c762b51291d08d519126286aad078df7a1`
Current Command Graph Pre-release: `v0.0000000000005`, T-0101 Native Command
Graph, published from `8ba6c17794d27913b6c8f2b5318be6f6296488ac`.
Current Native CLI Pre-release: `v0.0000000000006`, T-0102 bounded Tab
completion, published from `5f3d8d0d0a3a609af7ffc25a8be40aeb78bf6524`.
Current Native showcase Pre-release: `v0.0000000000007`, T-0103 synthetic
Command Graph walkthrough, published from
`a3befaa94b74700ced444e7384057f2c1a43c4e1`.

この文書は構想ではなく、現行treeで実装されている範囲だけを記録します。

## Development workflow support

Repository-scoped Project Manager, three Implementer, Tester, Performance
Reviewer, Security Reviewer, Researcher, and Librarian role definitions are
present. The read-only Librarian plus `raveil-context-librarian` skill rank a
small task-specific reading packet instead of loading all project records.
The Librarian is named Vreji and also reports prior-art similarity and IP-risk
gaps under ADR-0014 while remaining unable to decide infringement, legal
clearance, freedom to operate, or implementation approval.
Task-governance, Gate 0 evidence, and remote-release skills remain available.
These govern development workflow only; local IDEA/MCP endpoints and personal
Codex runtime configuration remain ignored.
The agent call-sign catalog is also local-only under ignored `.codex/` state;
the root `AgentNames.md` is absent and explicitly ignored. Historical releases
that already contained it remain immutable provenance.

ADR-0026 adds lightweight defect governance. Existing experiment failures,
negative results, regression tests, and logs remain authoritative evidence;
`docs/FAILURE_KNOWLEDGE.md` indexes reusable prevention lessons, and the GitHub
bug template captures actionable defects without making Issues project
authority. Same-branch corrected defects do not require issue-tracker churn.

Gate 0 is complete, so tracked work now uses a dedicated
`<type>/<record-id>-<short-slug>` lowercase branch.

## Delivery-line state

The manufacturing line resumed for the sole P0 T-0086 after T-0087
reconciliation. ADR-0024 makes a
GNU/Linux userspace graph vertical slice the next delivery line without
discarding any current artifact. Sonatine Microkernel (Sonatine), the Linux harness,
shared job/object/completion contracts, job rings, completion telemetry,
Experience infrastructure, EXP-0003 evidence, and metadata-shadow finalization
remain implemented and preserved.

T-0086 is implemented by selective port onto the T-0087 milestone state. The
donor branch was not merged, so none of its deletions or stale records entered
the result.

## GNU/Linux userspace graph MVP

T-0098 adds `python3 -m raveil shell` as the primary human-facing Native
userspace path. One explicit session owns the current graph, canonical variant
slate, proposal, execution result, and local command history while delegating
all authority to the existing GraphCompiler, AnalyticalPredictor,
Miroirs/Pavane-backed GraphExecutor, and NativeCBackend. Invalid order,
malformed arguments, duplicate execution, and overwrite fail without a
traceback. Results retain `raveil.graph-mvp-result/v1` and remain host-
correctness development evidence only.

T-0099 adds `--workspace PATH` and fixes one existing real directory as the
session's virtual `/`. Bounded `pwd`, `cd`, `ls`, `cat`, `stat`, `mkdir`, and
exclusive `write` commands share one `NativeWorkspace`; graph result files use
the same virtual path boundary. Parent traversal, symlink components, broken
links, special files, excessive paths/files/listings, root replacement, and
overwrite fail closed without exposing host absolute paths. The existing
GraphCompiler, adviser, Miroirs/Pavane-backed GraphExecutor, NativeCBackend,
baseline-first rule, commit/rollback, and result v1 remain unchanged.

This is application-level workspace containment and host-correctness evidence,
not hostile-code isolation. T-0100 remains open for descriptor-relative and
platform-enforced worker isolation. Sonatine and its shell are unchanged.

T-0101 adds a separate strict `CommandGraphProgram` rather than reusing tensor
graphs for shell work. The Native CLI now supports direct `run`, deterministic
`graph compile`, command `graph show`, baseline-first `graph execute --compare`,
balanced development `graph benchmark`, and exclusive `graph result`. The
bounded grammar covers quoted argv, pipelines, redirection, success/sequence
edges, and owned `|||` join-fanout over hash-bound allowlisted host tools.
Direct and DAG executors use equal workspace snapshots, controlled environments,
resource limits, and concurrency; exact stdout/status/output agreement gates
publication. Failure, timeout, stale identity, undeclared mutation, and output
collision remain uncommitted. Existing GEMM behavior and schemas are unchanged.

The manual `cat | grep | wc` demo returned `2` through real host tools and exact
direct/graph agreement. Its four-repetition timing is development/non-claim;
EXP-0004 remains Planned; the smoke sets `crossover_evaluated=false` and makes
no performance claim.
The current direct interpreter buffers pipeline stages, so benchmark records
mark ordinary-pipeline and scheduling claims ineligible; EXP-0004 retains the
concurrent OS-pipeline baseline as required future measurement work.

T-0102 adds host readline/libedit Tab completion without changing dispatch or
authority. Completion candidates are limited to documented commands, graph
subcommands/options, the fixed Command Graph tool allowlist, and bounded
virtual-workspace paths. Symlinks and host paths are omitted; completed input
still passes through the existing parser, workspace checks, and guarded graph
flow. Completion is ephemeral host usability, not expansion, arbitrary PATH
lookup, persistence, or an OS isolation boundary.

T-0103 adds `python3 -m raveil showcase list|prepare|run|mutate`: a synthetic
16/32/64-way independent ordinary `sort` fan-out, plus a four-small-file
control. It prints nodes/edges/critical path, hash-bound direct-argv admission,
exact semantic output manifest hash, sequential and equal-concurrency direct
baselines, DAG construction/execution/end-to-end intervals, observed
parallelism, and baseline-first evaluation cost separately. Its first run
executes all nodes; a deterministic one-input replacement then reuses only
showcase cache artifacts whose complete node recipe/tool identity, active input
SHA-256, and payload SHA-256 all match, while separately direct/Graph-validating
the changed node. The cache is intentionally outside `CommandGraphExecutor`:
the output states `production_reuse=not-implemented`, and T-0104 owns any
production design. Experience is explicitly not connected to this command
surface and remains advice-only. This is host-development-smoke only; EXP-0004
remains Planned and no timing line is a performance, scheduling, hardware, or
special-ISA claim.

The showcase now prints an explicit abstraction warning: whole host
tools/processes are conceptual nodes, far above the intended native
operation/dependency/effect/object graph. It does not test dependency discovery,
OoO replacement, cache hierarchy, pipeline, ISA encoding, area, or energy, and
its memoization is not evidence that Graph is required. RFC-0004 is only a
proposal for the correctly ordered Chisel RTL/simulation study. T-0105 now has
unmodified Rocket functional execution. T-0042 separately has a bounded static
Graph RTL smoke and a minimal BOOM RISC-V functional execution, but no matched
CPU comparison or performance evidence exists.
ADR-0046 now narrows T-0042's remaining implementation order without changing
that fact: the next required slice is the controlled Rocket/BOOM/Graph
connection to one proved-equal owned resource boundary with quiescent-window
and complete lifecycle accounting. Exhaustive CPU token lifecycle hardening is
deferred to T-0106 and no longer gates T-0042 or T-0044. Existing ADR-0045
diagnostics remain bounded functional evidence; no general semantic-initiator,
performance, CPU, ISA, FPGA, or silicon claim has been promoted.
The roadmap now separates the completed T-0105 generic Chisel/RISC-V substrate
from T-0057 prior-art/IP boundary plus Graph-contract definition and T-0042
Graph RTL implementation. T-0057 phase A now has a non-authoritative,
locator-backed matrix covering conventional OoO, EPIC, TRIPS/EDGE, WaveScalar,
DySER and
spatial-CGRA classes. It finds high mechanism similarity and records preliminary
WaveCache and EDGE-family patent hits as unreviewed; it establishes neither
novelty, infringement nor freedom to operate. ADR-0039 later accepts only the
RFC-0005 bounded static candidate for repository-owned RTL simulation; no
product Graph ISA or architecture has been accepted. This is a
planning/research
correction, not a CPU experimental result. T-0105 includes a
functional tooling smoke: under an explicit linux/amd64 Docker environment on
the Apple Silicon host, Chisel 7.2.0 emitted SystemVerilog for an owned four-bit
counter and Verilator 4.038 executed the C++ harness to
`CHISEL-SMOKE-V1 status=OK cycles=10 value=8`. This is emulated-host tooling and
RTL functional evidence only. No RISC-V core, Graph RTL, CPU comparison, or
performance evidence has run in that owned-counter path.
T-0105 also has a local ignored external Rocket Chip checkout at
`749a3eae9678bc70b029c5b9091fae33fad539c4`, the gitlink selected by Chipyard
1.11.0. Its fixed Chisel, CDE, and HardFloat submodules are fetched by the owned
revision-checking helper. An owned fixed Git/Nix/Docker wrapper now elaborates
the unmodified Rocket `DefaultSmallConfig`, builds the unmodified
`DefaultConfig` Verilator emulator, and requires all 16 official `rv64mi-p`
tests to pass with no failed logs. The verified run exited 0 and reported Nix
2.13.3, Mill 0.11.1/OpenJDK 19.0.2, Rocket's Scala 2.13.12/Chisel 5.1.0,
CIRCT firtool 1.56.1, Verilator 5.012, clang 11.1.0, CMake 3.26.4, Ninja 1.11.1,
and DTC 1.7.0 on emulated Linux amd64 under an Apple Silicon Docker host.
ADR-0038 fixes the ignored-source, immutable-container, locked Git-flake and
selected-package boundary. It deliberately avoids the upstream mutable Python
shell hook, excludes generated output from Nix input identity, and keeps a
version-matched Nix-store, Mill `out/`, and Mill/Coursier user-cache volume set
so foreign or vanished absolute paths cannot be silently reused. The
user-facing `./hardware/chisel/run-rocket-reference.sh` path completed both a
clean build/execution and a second separate-container cached rerun with the
required 16/0 marker.

This closes T-0105 as RTL functional/simulation substrate evidence only. The
result is not a cycle comparison, performance or energy measurement, area or
timing estimate, Graph RTL result, OoO-removal result, FPGA result, silicon
result, or CPU/ISA advantage. ADR-0039 now satisfies the T-0057B acceptance gate
for the narrow T-0042 simulation slice; T-0044 remains the later matched
comparison.

T-0057B now has an Accepted contract in RFC-0005. ADR-0039 authorizes, for
repository-owned RTL simulation only, an operation-level uint32 five-point
stencil lowered at installation to a
fixed-cycle schedule over bounded resources. The candidate has an internal
simulation interface, disjoint read-only/private-output objects, no runtime
token store, alias speculation, general LSU, rename, ROB, or architectural
block commit, and an ordinary RV64IM fallback. It defines configuration
identity, invalidation, exact semantic checking, complete configuration/staging
accounting, interruption behavior, and numerical no-go thresholds centered on
energy rather than speed.

The updated T-0057 matrix maps the draft to TRIPS/EDGE, WaveScalar, DySER,
EPIC/VLIW, and CGRA prior art. Similarity remains high, especially for installed
static configuration, hybrid fallback, and private-output publication. The
three patent discoveries remain unreviewed and fail-closed. The 2026-08-12
feature-to-document review records inspected claim locators and excluded
features without making a legal conclusion. ADR-0039 then admitted only the
fixed static slice for T-0042 functional validation; T-0044 measurement remains
separately gated.

T-0042 now implements the first owned RFC-0005 functional slice. The
`raveil.static-region/v1` compiler deterministically emits five `LOAD_U32`, four
`ADD_U32`, and one `STORE_U32` nodes plus nine SSA edges, affine object effects,
a six-phase logical schedule, one-read/one-add/one-write resources, zero runtime-ready
slots, and the ADR-0039 exclusion set. An independent validator recomputes the
graph, schedule, object, effect, bound, and fallback invariants. Canonical
descriptor SHA-256 is
`d4bf9395a510385f42ba4a193ae2c747f308ad502a8fe807843ed19c2fa4d1e2`.
The validator also rejects unknown fields, alternate schedules, altered effect
kinds, and any dynamic-issue resource request rather than treating a different
descriptor as compatible with the fixed RTL.

The owned Chisel `StaticStencilRegion` binds the first 64 hash bits as a
configuration tag and now reaches separate input and private-output instances
of the ADR-0043 request/response scratchpad for staging, execution, and
validation. It applies the fixed logical schedule over all 256 output points and has no
runtime dependency queue, token store, rename, ROB, general LSU, commit
frontier, or issue-mode switch. Cancellation clears output validity; restart
begins the fixed schedule from point zero.

The user-facing `./hardware/chisel/run-static-stencil-rtl.sh` path completed in
linux/amd64 Docker emulation on the Apple Silicon host. Chisel 7.2.0 emitted
SystemVerilog and Verilator 4.038 checked two complete invocations with distinct
inputs against an independently implemented C++ oracle: all 512 output words
and both checksums matched. A third invocation cancelled after 17 execution
cycles left `outputValid=0`, and a subsequent full restart passed. The fixed
schedule asserted 3,072 interface-accounted execution cycles per complete invocation, below the
8,192 functional bound.

The first compile failed because the Chisel utility import for `switch/is` was
missing. The first executable RTL then disagreed with the oracle at output 15
because a four-bit column plus one wrapped before assignment to a five-bit
wire. Adding the import and widening row/column slices before addition fixed
both failures; the independent full-output check is retained.

This is RTL simulation-functional evidence only. The cycle count is a schedule
correctness assertion, not comparative performance. No Rocket/BOOM comparison,
energy, area, timing, OoO-removal, FPGA, silicon, CPU/ISA, novelty,
non-infringement, or FTO claim follows. T-0057 is complete as contract/prior-art
and functional-schema validation.

T-0042 now also has the implementation-neutral
`raveil.simulation-adapter/v2` functional boundary. It fixes the descriptor,
workload semantics, disjoint private scratchpad model, useful-operation counts,
implementation identity, completion state, and installation/staging/execution/
completion/validation/publication accounting fields without importing Rocket
or BOOM types. ADR-0041 corrects the v1 ambiguity between semantic validity and
matched resources: every observation now reports its actual memory model,
resource-match verification, and matched-comparison readiness. Exact validation
rejects unknown fields, mismatched semantic counts, publication before
authority, an asserted total while any phase is unknown, or a match claim for
anything other than the required fixed-latency banked scratchpad. Common v2
adapter SHA-256 is
`56dbe3f2ab479233eb5e4fe1c79eb06e07458b42ea77acebb471a101afd24c1e`.

The Graph smoke now emits validated records for complete, cancelled, and
restart invocations. All are deliberately `accounting_complete=false` with
`total_cycles=null`: installation, completion, and publication costs are not
yet available. The reported 3,072 execution, 648 staging, and 512 validation
cycles therefore cannot be added or compared as an end-to-end result.
They also declare `memory_model=owned-private-scratchpads`,
`resource_match_verified=false`, and `matched_comparison_ready=false`; this RTL
has not yet been resource-matched to either CPU control.
T-0042 now has semantic stencil records for Rocket, BOOM normal, BOOM's
serialize-dispatch diagnostic, and the Graph RTL behind this boundary. It
remains open for a separately verified matched scratchpad adapter; T-0044
remains the matched measurement task.

ADR-0044 now adds the first CPU-side translation target without pretending it
is that matched scratchpad. A repository-owned Chipyard overlay removes the
inherited subsystem scratchpad from dedicated Rocket and BOOM configurations
and attaches a 32-bit, maximum-one-outstanding TileLink manager at
`0x08000000`, with a phase/counter control page at `0x08010000`, to the
uncached peripheral bus. The manager implements logic for `Get`, `PutFull`, and
`PutPartial`, byte masks, response backpressure, invalid phase-write denial,
source/size response routing, and aggregate software-declared phase counts.
This placement is deliberately observable and resource-unmatched; initiator
attribution, equal ports/arbitration/buffering, and common-memory promotion
remain unverified. The same phase-fenced workload now passes through both the
Rocket and BOOM CPU paths as described below.
The elaboration runner therefore reports execution not run, resource matching
false, comparison readiness false, and performance not measured.
This is not yet the ADR-0043 common-contract CPU adapter: the phase begins as a
software-declared label and does not provide owned semantic initiator metadata.

The owned manager now also passes a direct, monitor-enabled TileLink RTL
simulation. Protocol V4's raw bounded client issued 30 legal negotiated
transactions and
verified `PutFull`, two `PutPartial` byte-mask patterns, readback, invalid
phase-write denial, D-channel backpressure stability, maximum-one-outstanding
backpressure including same-source reuse rejection, reset phase, selected
aggregate counters, expected/unexpected source-class conservation,
accepted-to-completed phase correlation, and D response
`param`/`size`/`source`/`sink`/`denied`/`corrupt` metadata. This closes the
manager-local protocol corner-case bootstrap only. No CPU instruction executed;
phase remains software-declared, initiator attribution and the ADR-0043 common
contract remain open, and resource matching, comparison readiness, fixed
end-to-end latency, performance, energy, and area remain unverified.
Unlike V2, whose expected range covered every client source, V4 uses the
half-open classifier range `[1,3)`: in-range traffic completed 3/3 and deliberate
boundary sources 0 and 3 completed as unexpected 4/4. Requests from this raw
client, which has no DCache-origin request field, completed with DCache-origin
accepted/completed 0/0 and non-DCache-origin 7/7. This is a negative control
for manager-local classification and A/D conservation only, not evidence of CPU
execution, target-ELF semantic initiator identity, or loader/debug exclusion.
A second test-only top now drives the origin field true on every upstream raw
request and then removes that field at an explicit diplomacy adapter before the
same manager. The same 30-transaction driver completed with origin 0/0 and
non-origin 7/7, showing that negotiated metadata loss fails closed through A/D
accounting. This models field removal only; it is not an execution of a real
FESVR, loader, or debugger path and does not close semantic attribution.

The same owned manager now passes one phase-fenced CPU workload through both
the dedicated `RaveilOwnedRocketConfig` and `RaveilOwnedSmallBoomConfig`
Verilator systems. The identical bare-metal RV64 ELF read reset phase zero,
performed full-word and two byte-lane writes through `0x08000000`, selected
execution phase two through `0x08010000`, and checked the resulting data plus
aggregate accepted/completed and per-phase counters. Both independently
decoded signatures matched
`11223344`, `5522aa44`, `cafebabe`, phase 2, accepted/completed 8/8,
installation reads/writes 2/3, and execution reads/writes 2/1. This upgrades
both CPU paths for this bounded workload to `rtl-simulation-functional`. The
shared runner admits only those two named configurations and keeps separate
content-addressed simulator volumes; its payload hash covers the overlay, ELF
source, linker script, source-map verifier, signature verifier, and shared
runner, while the marker separately identifies the CPU/configuration. Exact
generated-graph verification identifies the DCache-MMIO client ranges at the
manager as `[8224,8256)` for Rocket and `[8288,8320)` for BOOM, disjoint from
the `[0,8192)` SimTSI/FESVR serial range. Runtime audit registers latch the
accepted data A-channel source and software-declared phase until D completion.
Both CPU runs observed expected-client accepted/completed 8/8,
unexpected-client 0/0, in-range final sources, and final accepted/completed
phases 2/2. A repository-owned adapter immediately after each DCache adds a
one-bit structural request field before the tile master Xbar. The pinned Xbar
is patched ephemerally to preserve negotiated request fields while applying
their declared false defaults to clients without the field. CPU signature V3
extends the retained 22-word prefix to 30 words; both CPUs observed structural
DCache-origin accepted/completed 8/8, non-DCache-origin 0/0, final origin
sources inside their config-specific ranges, and final origin phases 2/2.
The manager latches the field at A acceptance and holds it with source and
software phase until D completion. These config/Xbar/fragmenter-dependent
source IDs establish a
TileLink client class, not an ISA identifier or proof that the target ELF was
the semantic initiator. The structural bit proves only that the request crossed
the DCache-local adapter; it does not identify an instruction, PC, ELF, or
exclude untested loader/debug DCache activity. Matching signatures prove
semantic agreement for this one workload only. The evidence does not implement
ADR-0043 owned semantic initiator
metadata, establish equal resources, isolate OoO, or support a performance,
energy, area, OoO-removal, FPGA, or silicon claim.
The ADR-0043 common-contract adapter remains open.

The shared CPU runner now also executes a dedicated loader-path negative probe
in each pinned configuration. Its ELF contains one four-byte writable
`PT_LOAD` at the owned data page and keeps code, signature, and `tohost` in
main RAM; exact `readelf` and symbol checks fail closed on layout drift, and
the simulator invocation contains no `+loadmem` override. Before the CPU
accesses the page, the manager observes two accepted/completed requests from
the `[0,8192)` serial class, DCache-origin 0/0, and non-origin 2/2. The two
requests are the pinned FESVR transport's aligned read/write sequence, not a
one-request-per-segment invariant. After the CPU reads the loaded word, totals
are 3/3, with DCache-origin 1/1, non-origin still 2/2, and the final origin
source in the configuration-specific DCache range. This is bounded functional
RTL evidence for the tested SimTSI/FESVR PT_LOAD path followed by a structural
DCache crossing in the same simulation. Source and origin metadata do not
prove the target ELF's semantic initiator, and Debug SBA, other loader/debug
paths, durable semantic attribution, and matched resources remain open.

A dedicated repository-owned DMI harness now exercises one concrete Debug
System Bus Access path in both pinned CPU configurations. Exact generated
graphs place the Debug client at `[8192,8224)`, with Rocket DCache MMIO at
`[16416,16448)` and BOOM DCache MMIO at `[16480,16512)`. In each bounded RTL
run, an 8-bit Debug SBA write of `0xa5` completed as unexpected/non-DCache
origin 1/1 at software phase zero; the subsequent CPU read completed as
expected/DCache origin 1/1, bringing aggregate accepted/completed to 2/2.
Request source and phase were retained from A acceptance through D completion.
This establishes generated-topology and runtime TileLink client-class
classification for the tested path only. It does not halt/resume the hart,
prove an instruction, PC, target-ELF semantic initiator, or exclude every
loader/debug path. Resources remain unmatched and no performance, power, area,
OoO, FPGA, silicon, novelty, non-infringement, patent-clearance, or FTO claim
follows.

The regular CPU and PT_LOAD signatures now also feed a fail-closed
cross-workload audit. Rocket reused exact DCache source 8224 and BOOM reused
8288 across two distinct ELF binaries with different payload/semantic
signatures. This executable counterexample shows that DCache source and origin
class do not carry a unique ELF semantic identity. It narrows the next step to
a separately decided CPU-side witness with replay/flush/commit semantics; it
does not itself provide that witness.

ADR-0045 now fixes that next attribution policy without claiming its
implementation. CPU-owned, non-software-writable tokens name candidate memory
operations before DCache request acceptance; Rocket binds a bounded sequence
to the corresponding EX/MEM PC and epoch, while BOOM uses sequence/epoch as
identity and ROB index plus branch mask only as lifecycle context. Exhaustion
or wrap alias fails closed. Replay retains one token, reset advances its epoch,
loader/FESVR/Debug traffic cannot mint it, and kill, exception, rollback, stale
epoch, or duplicate outcome fails closed. Load attribution requires both
successful memory response and architectural retirement; store attribution
requires retirement, CPU-specific store authorization, and owned-manager D
completion. A post-A exception does not cancel transport and any later side
effect is reported as a lifecycle violation.

A repository-owned standalone Chisel observer now makes that lifecycle policy
executable against synthetic events before any pinned-core hook. Its
assert-enabled `linux/amd64` RTL simulation accepted 21 tokens and conserved
them as 3 committed loads, 1 committed store, and 17 noncommitted outcomes. It
separately recorded 8 core attempts, 1 core replay, 1 DCache retry, A/D counts
of 7/7, 5 retirements, 1 store authorization, 2 unknown inputs, and 8
violations. Positive load/store cases and pre-A kill, post-A exception,
reset-outstanding, stale epoch, stripped/untagged metadata, duplicate token and
outcome, invalid completion, D error, and sequence exhaustion negatives passed.
An exact-schema verifier rejected missing fields, changed counters, and
duplicate markers and checked terminal conservation. Review found and the RTL
regression closed one invalid-completion promotion bug by requiring the event
that completes the existing ADR-0045 load/store conjunction to itself be a
valid D-completion, retirement, or store-authorization transition.
The event source remains synthetic: pinned Rocket execution, CPU signal
binding, target-ELF semantic initiator attribution, the BOOM probe, common
bridge connection, resource matching, matched comparison, and performance are
all still unimplemented or unverified.

A separate pinned Rocket request/response/WB diagnostic now observes the exact
`0x08000100` workload at the `RocketCore` DCache boundary. It allocates only
when a request is accepted, captures that request's DCache tag, matches the
load data response separately, and observes exception-free WB by PC and
load/store kind. The bounded RTL run records one first-attempt store and one
first-attempt load, two retirements, one matched load response, and the exact
two-word signature. This is partial `rtl-simulation-functional` evidence only:
the DCache-local tag is not a durable token, store WB is not store
authorization or owned-manager completion, and replay, kill, redirect,
exception, reset/epoch, BOOM lifecycle, common-bridge admission, semantic
initiator identity, resource matching, and performance remain unverified.

The pinned Rocket diagnostic now also closes one bounded same-cycle
accepted-request/redirect outcome. A first owned-address load completes as
sequence 1 and supplies a data dependency before a deliberately taken branch
places an owned-address store on the wrong path. The store request is accepted
while the older branch resolves as a MEM-stage direction misprediction. The
diagnostic records `allocate/request/kill` with `promotion=blocked` as sequence
2, then requires a second load's response plus WB as sequence 3. The wrong-path
store has no WB retirement, and the two loads both observe `0xc5686cac` in the
exact run. This is post-request redirect bookkeeping and differential readback
for that simultaneous case, not pre-request-kill coverage, proof of DCache S1
cancellation or TileLink A/D completion, general absence of a memory side
effect, multi-live-token support, durable token transport, semantic initiator
identity, resource matching, or performance evidence.

The same exact redirect workload now has a separate pinned Rocket DCache-fate
diagnostic. One cycle after the accepted sequence-2 request, the Rocket-facing
S1 record directly reports `s1_kill=1` and `s2_kill=0`; its sequence, PC,
address, and local DCache tag match the existing killed request. An independent
owned-manager monitor records exactly two successful `Get` A/D pairs for the
before/after loads, with sources 8240 and 8224 inside the exact generated
Rocket manager range `[8224,8256)`, and records no `Put` for the probed address.
Both loads observe `0x682513da`. This is bounded `rtl-simulation-functional`
evidence for a Rocket-local request/S1 correlation and separate manager-local
A/D source correlations in that exact log. No token is carried from Rocket
through DCache/TileLink, so it is not semantic-initiator attribution, general
transport cancellation or side-effect proof, resource matching, or a
performance, power, area, OoO, FPGA, silicon, novelty, non-infringement,
patent-clearance, or FTO result. Pre-request kill, later-cycle kill/exception,
replay, reset/epoch, multi-live-token operation, and the BOOM lifecycle probe
remain open.

A fourth pinned Rocket diagnostic now covers one distinct later post-request
exception boundary. An exact misaligned load at `0x08000101` is accepted at
the Rocket DCache request interface, and the retained Rocket-local PC and tag
match a later WB misaligned-load exception with cause 4, `ma_ld=1`,
`take_pc_wb=1`, and `promotion=blocked`. Aligned loads before and after the
trap both return `0x682513da`; the trap handler verifies `mcause`, `mtval`, and
`mepc` and resumes exactly once. This is bounded `rtl-simulation-functional`
evidence for a Rocket-local accepted-request/WB-exception correlation. It is
not a post-TileLink-A exception, does not carry a token through DCache or
TileLink, and does not prove general rollback, side-effect absence, semantic
initiator identity, resource matching, or performance. Pre-request kill,
post-A exception/rollback, replay, reset/epoch, multi-live-token operation,
and the remaining BOOM lifecycle cases remain open.

The first pinned BOOM lifecycle diagnostic now covers one positive load at the
BOOM LSU boundary. For the exact `0x08000100` load, a repository-owned sequence
correlates one accepted LSU DCache request, its matching DCache response, and
one architecturally valid ROB commit. The bounded trace reports PC
`0x80000010`, ROB index 4, LDQ index 0, response/signature value `0xdaab9780`,
and `promotion=eligible`. Sequence is the identity; ROB/LDQ indices, branch
mask, and lane remain context only. No token is carried through DCache or
TileLink, and this does not prove target-ELF semantic initiator identity, store
authorization, replay/kill/exception/reset behavior, complete BOOM lifecycle,
resource matching, OoO effects, or performance. Those claim boundaries remain;
ADR-0046 routes the general lifecycle cases to T-0106 while T-0042 remains open
for the controlled common-resource and complete-accounting slice.

A second pinned BOOM diagnostic now covers one deterministic but narrower
negative ordering. At the exact `0x08000101` misaligned-load addrgen candidate,
an LSU-local repository sequence retains the PC and ROB/LDQ context, correlates
the following LSU misaligned-load exception, then observes one matching DCache
request accepted after that exception but before the later global ROB rollback
state. The exact trace has no matching response or architectural commit, and
the faulting ROB entry does not appear in a rollback row (`matching_rbk=0`).
This is bounded `rtl-simulation-functional` evidence for the exact BOOM-local
`candidate -> exception -> request -> rollback-state` order only. Because the
exception precedes request acceptance, it is not the still-required
post-request exception/cancellation case; absence of a response in this trace
does not prove transport cancellation or general side-effect absence. The
sequence is not carried through DCache or TileLink; general rollback, semantic
initiator identity, store authorization, replay/reset behavior, resource
matching, OoO effects, and performance remain unproven.

A third pinned BOOM diagnostic now covers one exact store-authorization path.
At PC `0x8000001c`, a repository-local sequence correlates architecturally
valid ROB retirement and the matching STQ committed transition with one
accepted DCache store request, one store response/succeeded transition, and
the later STQ clear. The exact context is ROB index 7, STQ index 3, branch mask
0, and lane 0. Independently, the owned-manager audit records one successful
`PutFullData`/`AccessAck` pair at `0x08000100` with source 8304 and one
successful readback `Get`/`AccessAckData` pair with source 8288; the software
readback equals `0x51a7c0de`. This is bounded `rtl-simulation-functional`
evidence for a BOOM-local authorization/request/response/clear correlation and
a separate manager-local A/D source correlation. The repository sequence is
not carried through DCache or TileLink, so same-token owned-manager D
completion, complete store attribution, semantic initiator identity, general
store behavior, resource matching, OoO effects, and performance remain
unproven.

A fourth pinned BOOM diagnostic now covers one cacheable, CPU-local
post-request redirect. The exact wrong-path `lwu` at PC `0x80000048` and DRAM
scratch address `0x80010000` produces one accepted LSU DCache request, its
matching response, and a later branch-mask kill with no matching architectural
commit. The repository sequence remains identity; PC, ROB index 17, LDQ index
0, branch mask 1, and lane 0 are bounded validation context. The owned PBUS
manager is not exercised, no token crosses DCache or TileLink, and no
post-TileLink-A cancellation, transport side-effect absence, semantic
initiator, same-token manager completion, general rollback, resource matching,
OoO effect, or performance result follows.

A fifth pinned BOOM diagnostic now carries the repository-owned token for the
exact committed store at PC `0x8000001c` across the BOOM DCache request and
uncached TileLink A metadata. The owned manager latches `{valid=1, epoch=1,
sequence=1}` with the exact `PutFullData` acceptance at `0x08000100`, retains
it across backpressure, and emits the same token with the successful
`AccessAck` D completion and source 8304. The BOOM-local authorization,
request, response, and STQ-clear ledger uses the same epoch/sequence, and
software readback remains `0x51a7c0de`. Absent producers default the negotiated
fields to invalid/zero, malformed fields classify invalid, and verifier
mutations reject missing, altered, duplicated, denied, or source-mismatched
records. This is bounded `rtl-simulation-functional` transport-correlation
evidence for one pinned BOOM store only. Epoch 1 is diagnostic and fixed;
reset/redirect advancement, stale/duplicate/exhaustion behavior, replay,
multi-live tokens, BOOM loads, Rocket parity, post-A rollback, loader/FESVR/
Debug negatives, CPU-side consumption of manager D, common-bridge promotion,
semantic initiator identity, resources, OoO effects, and performance remain
unproven.

A sixth pinned BOOM diagnostic now exercises the negotiated default-invalid
case live. It advertises the three token fields at the BOOM DCache client but
deliberately omits LSU token minting and I/O-MSHR token assignment. The same
committed store still completes its owned-manager `PutFullData`/`AccessAck`
pair and software readback, while the manager observes `{valid=0, epoch=0,
sequence=0}` unchanged at A and D and classifies both records unknown. This is
bounded `rtl-simulation-functional` evidence that one absent producer becomes
the explicit negotiated default and does not promote semantic attribution,
without denying the underlying transaction. It does not test stripping after a
valid producer, malformed nonzero metadata, stale epochs, duplicate/exhausted
tokens, reset with work outstanding, replay/source reuse/backpressure, untagged
loader/FESVR/Debug traffic, BOOM loads, Rocket parity, CPU-side D consumption,
common-bridge promotion, semantic initiator identity, resources, OoO effects,
or performance.

T-0042 now also has a standalone post-fragmenter TileLink-to-owned-contract
bridge before CPU integration. The bridge accepts negotiated `Get`, `PutFull`,
and `PutPartial` requests, translates them into an upstream-type-free owned
request carrying write/address/data/mask plus explicit adapter-supplied
initiator and lifecycle phase, and retains TileLink source/size until the owned
response is consumed on D. An independent owned target holds response data,
error, operation, initiator, and phase under backpressure and asserts
accepted/completed conservation. The assert-enabled pinned Chipyard/Verilator
harness passed six requests with full and two partial writes, both byte masks,
readback, deterministic range denial, single-outstanding request blocking, D
backpressure, source/size routing, and initiator/phase correlation at 6/6.
The exact rerun verified the content-addressed assembly checksum before
reproducing the same marker. This proves the mechanical bridge and explicit
metadata handoff only: the harness supplies the initiator/phase inputs, neither
CPU is connected, semantic CPU/ELF identity remains unproven, and resources
remain unmatched. No performance, power, area, OoO, FPGA, silicon, novelty,
non-infringement, patent-clearance, or FTO conclusion follows.

The narrower pinned-source candidate is now implemented diagnostically:
repository-owned Rocket and BOOM hooks insert the adapter immediately after
each DCache and before the shared tile master crossbar. Runtime positive paths
and the raw-client absence plus explicit field-stripping negative paths verify
field retention and fail-closed false classification in these bounded
harnesses. A concrete SimTSI/FESVR PT_LOAD probe now additionally observes
serial-class traffic as non-origin before one tagged CPU read in the same run.
This structurally separates that tested transport path from the observed CPU
class, but it still cannot identify a particular ELF instruction, PC, or
semantic intent, and it does not test every loader/debug path. Selecting a
durable ADR-0043 semantic metadata assignment boundary requires later policy,
negative tests, and a new decision if the field is promoted beyond ADR-0044
diagnostics.

ADR-0040 now pins the BOOM control source. Chipyard tag 1.11.0 at
`ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1` selects BOOM
`9459af0c1f6847f8411622dac770ac78fe10847c`; the initial configuration is
`chipyard.SmallBoomConfig`. The ignored detached checkouts are clean, origin
and parent gitlink checks pass, and BOOM's BSD-3-Clause plus SiFive Apache-2.0
notice hashes are fixed in `boom-pin.env`.

Source inspection verifies chicken CSR `0x7c1` mask `0x8`. Its bit-3
`disableOOO` diagnostic makes dispatch wait for an empty ROB/LSU, but does not
remove rename, ROB, issue, physical-register, or LSU structures. It is now
named `boom-ooo-disabled-diagnostic`/`serialize-dispatch`, never an in-order or
structurally stripped BOOM. `verify-boom-reference.sh` emits a successful
source-verification marker.

The owned BOOM bootstrap now initializes only explicit public Chipyard
gitlinks, compiles the 56-source BOOM Scala project, and elaborates
`chipyard.SmallBoomConfig` through the integrated Chipyard generator. The
successful functional marker confirms non-empty FIRRTL and annotations with a
`BoomCore`; emitted parameters include one-wide decode, three issue ports, a
32-entry ROB, three 8-entry issue windows, 52 integer physical registers, and
8/8 load/store queues. These are configuration/elaboration facts, not measured
costs. The elaboration wrapper uses a digest-pinned Temurin 17 base but unlocked
APT and Maven resolution, so it is not a measurement environment.

The separate functional-simulator path pins a Miniforge linux/amd64 base,
Chipyard's lean simulator lockfile and hash, Verilator 5.020, RISC-V GCC 12.2.0,
DTC 1.6.1, CIRCT firtool 1.61.0 and the installed firtool binary hash. It uses
explicit public parent gitlinks and read-only source mounts. The first owned
workload executed on `chipyard.SmallBoomConfig`: an RV64 ELF summed 1 through
16, stored and loaded the result, checked 136, and signalled success through
`tohost`. Verilator reached its normal finish and emitted
`BOOM-FUNCTIONAL-SMOKE-V1 status=OK`.

This is a minimal RTL simulation-functional execution, not the RFC-0005 Graph
workload and therefore not a common-adapter record. The conda-lock reader
bootstrap remains an unlocked package solve, and the upstream CIRCT downloader
is accepted only after validating the installed binary hash. No performance,
energy, area, timing, OoO comparison, Graph comparison, FPGA, or silicon result
follows.

The same simulator also executed the identical workload after the tracked ELF
set CSR `0x7c1` mask `0x8`, read the bit back, and failed closed to a non-success
`tohost` code if the readback was absent. The diagnostic run completed normally
with `BOOM-SERIALIZE-DISPATCH-SMOKE-V1 status=OK`,
`diagnostic=serialize-dispatch`, and `structures=retained`. This proves only
functional execution under that CSR setting; it neither proves which dynamic
instructions overlapped nor measures any latency, energy, area, or benefit.
This minimal diagnostic does not by itself supply a semantic stencil record or
matched comparison boundary.

BOOM normal and serialize-dispatch modes now also execute the RFC-0005 semantic
five-point stencil rather than only the minimal sum smoke. One tracked RV64
fallback initializes 324 deterministic uint32 words, computes all 256 outputs,
and exposes the private output range through FESVR's signature boundary. A
separate Python parser validated every word against the repository-owned oracle;
both modes produced checksum `0000007f11ba2640`. Their validated adapter v2
records identify `boom-ooo` and `boom-ooo-disabled-diagnostic`, but report
`memory_model=cache-backed-variable-latency`, all lifecycle cycles unknown,
resource matching false, and comparison readiness false. This is semantic
functional evidence, not the RFC-0005 isolation comparison.

The pinned `chipyard.RocketConfig` Verilator simulator now executes the same
tracked C/assembly stencil and validates the same 256-word FESVR signature
against the same independent oracle. It also produced checksum
`0000007f11ba2640` and emitted a validated `rocket-in-order` adapter v2 record.
That record is likewise cache-backed, has every lifecycle cycle unknown, and
sets resource matching and comparison readiness false. All required control
identities now have semantic functional records; the common fixed-latency
banked scratchpad/resource boundary remains unimplemented and unverified.

ADR-0042 now records one intermediate shared-memory prototype. Pinned
`AbstractConfig` gives both CPU controls the same 64 KiB, one-bank subsystem
TileLink RAM at `0x08000000`. A separate linker keeps code and `tohost` in the
normal `0x80000000` region while placing the 324 input words and private 256
output words at `0x08000000` and `0x08000510`. Rocket, BOOM normal, and the
serialize-dispatch diagnostic all completed from this placement and again
matched the 256-word oracle with checksum `0000007f11ba2640`. Their v2 records
use `memory_model=shared-tilelink-banked-scratchpad-unverified-latency`; all
cycle fields remain unknown and both resource matching and comparison readiness
remain false. Common addressable TLRAM is a functional bridge, not proof of
fixed latency, matched CPU paths, or a Graph-side common adapter.

T-0042 now also has a passive TLRAM endpoint observer. Separate non-tracing
Verilator models bind below the bank-local TileLink fragmenter and match each
accepted single-beat A request to its completed D response by source ID. In the
pinned Rocket, BOOM normal, and serialize-dispatch diagnostic runs, all three
signatures remained correct and each observer reported 296 completed beats,
all classified as reads: 162 in the input range, 128 in the private-output
range, and 6 elsewhere;
all observed endpoint intervals were one cycle with no unmatched response,
premature source reuse, or pending request. No write beat was observed, and the
boundary cannot attribute initiator or lifecycle phase. These are run-local
functional diagnostics only. They do not prove fixed end-to-end CPU latency,
exercise a comparable write path, match the Graph storage, or change either
resource matching or comparison readiness from false.

ADR-0043 now establishes a Raveil-owned local scratchpad transaction boundary
before either side is adapted. `OwnedFixedLatencyScratchpad` has one request
and response stream, at most one outstanding transaction, explicit read/write,
byte mask, initiator and lifecycle phase, deterministic range errors,
backpressure, and accepted/completed/stall/pending counters. Its assert-enabled
emitted RTL passed a standalone Verilator harness covering reads, writes,
partial writes, request/response stalls, attribution, and rejection. A response
is available one module-local cycle after acceptance and remains stable until
consumed. The static Graph region is now connected through disjoint input and
private-output instances: two full runs each accepted 1,280 execution reads and
256 execution writes, matched all 512 host-oracle outputs in total, and passed
cancel/drain/restart. The CPU controls remain unconnected, fixed end-to-end
latency is not claimed, and resource matching plus comparison readiness remain
false.

ADR-0025 implements one OS/ISA-neutral owned `GraphProgram` and
`ExecutionContract` for bounded GEMM and GEMM+bias+ReLU graphs. A fixed
structural compiler emits a unique baseline-first slate; an analytical adviser
either proposes an admitted variant or abstains. The executor always runs and
semantically validates the trusted baseline first, compares a proposed result
against both its reference checksum and the baseline, and then records explicit
commit or rollback. Invalid baselines fail closed.

The `graph-mvp` CLI compiles the existing native-C adapter with strict C11,
executes the vertical slice, and exclusively creates a segregated
`raveil.graph-mvp-result/v1` JSON result. The result is host-correctness
evidence, not Experience, MeasurementRecord, completion telemetry, silicon
performance, or energy evidence.

T-0090 makes backend choice explicit. `native` remains the default.
`sonatine-qemu` accepts one bounded GEMM of at most 8x8x8 through a versioned
128-byte pointer-free request loaded into the fixed QEMU RAM contract. Sonatine
validates it, reuses JobDescriptor, ObjectManifest, rings, CompletionRecord,
approval, and metadata finalization, then emits one request-bound result frame.
The host rejects missing, duplicate, stale, malformed, unknown, unapproved,
timeout, or nonzero-exit results. Its evidence class is fixed to
`qemu-emulation-correctness`, and latency is deliberately absent.

The verified 8x8 GEMM path runs the trusted baseline, produces the same exact
checksum as the native backend, and records explicit adviser abstention. QEMU
`EXECUTED` is not sufficient: semantic validity is exposed only after exact
checksum agreement plus Sonatine approval/finalization.

T-0041 now gives `GraphVariant`, `MemoryPlan`, and `OptimizationProposal`
strict v1 schemas with exact-key deserialization. Variants bind the owned
program and execution-contract identities; proposals additionally bind the
complete ordered candidate set. The executor rejects stale or malformed
lineage before invoking a backend. The bounded host-memory plan remains
descriptive and is not resource-enforcement or performance evidence.

T-0043 makes the named Miroirs and Pavane boundaries executable in the same
OS/ISA-neutral frontend. Miroirs rejects any graph, contract, variant slate, or
proposal that differs from the canonical owned compiler output before a backend
call. Pavane independently regenerates the deterministic `int32` inputs,
executes the bounded `int64` GEMM or GEMM+bias+ReLU reference, computes the
owned FNV-1a checksum, and compares both baseline and candidate observations to
that expected value. Backend-supplied `semantic_valid` and reference checksums
cannot approve a self-consistent wrong result. Semantic approval remains
independent of selection timing, so the timing-free Sonatine/QEMU baseline
continues to support explicit abstention.

T-0040 adds the first pinned upstream compiler import under ADR-0032. The
adapter admits only the repository-authored 8x8x8 i32-input/i64-accumulation
GEMM fixture, verifies its strict manifest and SHA-256, checks
`iree-base-compiler` package 3.11.0 and exact compiler revision, bounds the
subprocess and private VMFB, and emits only the existing canonical
`GraphProgram` plus a separate pointer-free `raveil.graph-import/v1`
provenance sidecar. The imported graph then follows the
unchanged Miroirs, baseline-first, Pavane, proposal/abstention, and explicit
commit/rollback path. No MLIR/IREE object or VMFB enters an owned public
contract.

The GNU/Linux arm64 container compiled the real fixture and completed the
native graph demo with explicit abstention and an exact valid baseline. This is
compiler/import and host correctness only. IREE runtime execution, general
MLIR import, optimization quality, latency, energy, FPGA, ASIC, and silicon
remain non-claims.

The native result adapter and Sonatine serial adapter now also reject
non-canonical scalar encodings, wrong JSON types, missing fields, negative
latency, zero cookies, and invalid binding ranges. These checks are correctness
boundaries only and create no performance or hardware claim.

The completed tree passed the full local test suite plus RV64 release/debug,
DWARF, U-mode shell, telemetry replay, and graph differential checks. A Linux arm64 container
also passed the 29 focused graph/backend tests and actual QEMU/native
differential. These are host and emulation correctness results only.

Sixteen focused tests pass on native macOS and in a Debian 12 arm64 GNU/Linux
container. The real Linux smoke ran baseline then candidate and chose rollback
because the candidate did not improve that development run. This is functional
control-loop evidence only. Sonatine and all prior artifacts remain unchanged.

## Executable track A: Sonatine Microkernel RV64 seed

QEMU RISC-V `virt`向けのfreestanding kernel seedがあります。

T-0034 adds an executable Four-plane write firewall under ADR-0030. Program,
Graph, Data, and Experience use distinct capability object types and exact
type/right/owner/generation checks. Fixed boot-scoped registries seal full
Program identities and Program-bound Graph identities. The normal job path
requires Data authority for object registration, submission, and metadata
publication; separate Program authority gates injected semantic approval;
Experience authority admits only a bounded consumed-completion observation.

The public job authority header no longer exposes unguarded registration,
submission, approval, or finalization functions. Host tests exercise all 16
plane-capability/operation combinations, identity mismatch, wrong owner,
attenuated delegation, and revoked-handle denial. QEMU smoke executes the same
guarded path. This is a single-hart volatile kernel policy seed, not physical
plane isolation, persistent authority, per-object least privilege, DMA/IOMMU,
or hardware evidence.

Implemented:

- RV64 machine-mode entry、one hart、fixed 128 MiB memory contract;
- versioned `qemu-virt-rv64-v1` platform contract with pinned QEMU `virt`,
  `rv64` CPU, 128 MiB RAM, one hart, no firmware, and compile/test assertions
  tying the fixed MMIO/RAM assumptions to the launch configuration;
- Sv39 page-table construction with a supervisor-only 128 MiB kernel identity
  map, an explicit non-executable user window, page-walk validation, and an
  aligned `satp` root; current M-mode execution does not yet enforce the maps;
- transient U-mode init/fault probes followed by a persistent scripted U-mode
  shell copied into separate U/R/X code and U/R/W stack pages, with RAM-only
  PMP admission and trusted kernel-stack trap entry through `mscratch`; the
  retained M-mode diagnostic shell is not entered by the normal boot path;
- fail-closed U-mode trap disposition: an illegal-instruction probe and unknown
  syscalls return through trusted kernel-stack control and ABI state to the
  diagnostic kernel instead of resuming or hanging;
- a persistent scripted U-mode shell task with current-task-bound console,
  clock, and scalar endpoint syscalls; no user-provided task/owner identity,
  `CONTROL` operation, kernel pointer, or arbitrary user pointer crosses the
  syscall veneer;
- a line-oriented `raveil-u> ` U-mode command shell with an eight-byte
  task-owned scalar buffer, CR/LF/CRLF handling, empty-line suppression,
  backspace/delete editing, fail-closed overflow recovery, explicit unknown
  command errors, and `help`, `info`, `ticks`, `ipc`, `fs`, and `exit`;
- a T-0092 native operator demo adding `ls`, `cat`, `echo`, `write`, `stat`,
  `jobs`, `run`, `cancel`, and `result`; VFS commands use the real bounded
  nodes, while graph commands require a distinct non-delegable demo capability
  and reuse the bound job/completion, Experience-observation, byte-shadow,
  independent fixed-GEMM semantic comparison, approval, commit, cancellation,
  and rollback seams;
- an exact bounded `RAVEIL-SONATINE-DEMO-V1` frame with monotonic sequence and
  a strict host `sonatine-demo` runner. The runner binds repository revision,
  kernel and input SHA-256, fixed transcript, QEMU/Python versions, every frame,
  final state, semantic result, checksum, and exit status into one exclusively
  published `raveil.sonatine-demo-result/v1` JSON record;
- command state that remains intact across real CLINT preemption without
  passing a line pointer to the kernel; the only added console operation emits
  one seven-bit scalar byte after current-task and capability validation;
- T-0096 correction removes per-preemption UART prose from normal
  operation and treats ETX as an operator request for the same current-task-
  checked shutdown used by `exit`; local and fresh-clone QEMU verification
  passed and v0.0000000000003 is published as a Pre-release;
- non-blocking U-mode console reads that return `WOULD_BLOCK` instead of
  polling in M-mode with interrupts masked; M-origin faults take a distinct
  fail-stop path, and seed shutdown is restricted to the scheduler-registered
  U-mode init task;
- one shared 272-byte M/U trap frame preserving x1-x31, interrupted `sp`,
  `mepc`, and `mstatus`, with `mscratch` bound to the running context's trusted
  kernel-stack top;
- `.bss` initializationと16 KiB boot stack;
- NS16550A polled console;
- 4 KiB bitmap physical-page allocator;
- owner、type、rights、generationを持つ64-entry capability table;
- `init`と`idle`のfixed kernel task records;
- an RV64 callee-saved context frame and independent 4 KiB idle stack, with a
  verified cooperative `init -> idle -> init` round trip;
- CLINT 100 Hz timer-driven preemption that switches `init -> idle -> init`
  from a live U-mode shell to M-mode idle and back to the same user frame;
- a non-reentrant timer-dispatch guard that rejects nested scheduling without
  changing the incoming frame/PC, incrementing the tick, or performing another
  context selection;
- capability-checked four-message IPC endpoint;
- queued IPC blocking/retry state transitions with operation-specific wake-up,
  distinct denied/invalid results, and ready-only task selection;
- `CONTROL`-authorized capability delegation to non-recursive leaf grants with
  nonempty attenuated rights and independent generation-checked revocation;
- kernel-derived smoke evidence for forged, wrong-owner, and send-only receive
  capability rejection, followed by a valid endpoint round trip;
- a two-node VFS with immutable initramfs `/hello`, volatile bounded RamFS
  `/scratch`, filesystem root capabilities, and pointer-free byte I/O from the
  persistent U-mode shell before and after CLINT preemption;
- fail-closed capability generation exhaustion that retires a slot instead of
  wrapping an old handle back into validity;
- CLINT 100 Hz machine timerとinteger register trap frame;
- a retained legacy `raveil>` M-mode diagnostic shell implementation that is
  no longer entered by the normal smoke boot path;
- `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, `reboot` commands;
- release `-Os` build and isolated `DEBUG=1` `-Og -g3` build;
- `make debug` QEMU GDB server and `make gdb` command-line client entry
  points;
- Docker build context exclusion for host artifacts and a clean container
  release build;
- local Gate 0 CI script for host tests, release/debug RV64 builds, DWARF
  inspection, and QEMU smoke. Hosted CI/CD is intentionally not configured。

Not implemented:

- S-mode kernel execution;
- PMP policy;
- persistent scheduling of multiple user contexts;
- persistent multi-user blocking scheduler execution, cancellation, and
  fairness;
- capability derivation trees and cascading revocation;
- device-tree memory discovery;
- real Daphnis Execution Subsystem device, MMIO/DMA/IRQ transport, and
  U-mode-facing submission path.

## Linux driver-development harness

Linux is implemented as a non-authoritative development/transport-validation
host under ADR-0019. The tree contains a Raveil-owned fixed-width v1 PING/NOP
ABI, a pure-C one-inflight contract core, and Linux-only unprivileged
`SOCK_SEQPACKET` daemon/client sources. The daemon uses a mode-0600 socket under
`XDG_RUNTIME_DIR`, accepts one client, verifies `SO_PEERCRED` against its own
UID, rejects partial/version/size/flags/opcode-invalid messages, and copies no
user pointer into the contract.

The protocol core is host-tested. A Debian bookworm arm64 Docker build compiled
the Linux-only daemon/client with GCC 12.2.0 and `-Werror`; a UID/GID 65534
container smoke used a private mode-0700 runtime tmpfs, verified socket mode
0600, completed PING, and verified normal socket cleanup. This is Linux
container correctness, not a kernel driver, real Daphnis device, JobDescriptor,
DMA/MMIO/IRQ path, performance result, Experience writer, or Sonatine
replacement.

## Shared job/completion contracts

ADR-0020 is implemented as a platform-neutral strict-C11 contract and
validator. JobDescriptor v1 is a fixed 320-byte, four-object envelope with
opaque identities, nonzero resource ceilings, generation/version/range/effect
references, and fail-closed reserved/unused slots. CompletionRecord v1 is a
fixed 176-byte observation carrying job ID plus execution epoch, sequence, and
cookie claims; T-0031 must enforce their trusted issuance, equality, and
one-shot consumption. Executed outputs must exactly match WRITE objects and
advance versions.

These validators establish structural correctness only. No executable path yet
resolves descriptor IDs as caller capabilities, commits output, or writes
telemetry to Experience. Linux PING/NOP remains a separate transport envelope.

ADR-0021 implements the kernel-internal T-0031 seed: an exact 64-byte
ObjectManifest v1 validator, fixed eight-entry boot-scoped object table,
four-entry submission and completion rings, and four-entry inflight ledger.
Admission checks ID, generation, visible version, bounds, and permitted effect.
Sonatine issues boot-scoped epoch/sequence/cookie bindings; wrong, stale, or
duplicate completions fail closed and valid completions are consumed once.
Host tests and a QEMU kernel smoke cover the state machine. The rings are
single-hart and kernel-owned; they are not Linux, U-mode, shared-memory, DMA,
MMIO, IRQ, hardware, or performance evidence. `EXECUTED` does not change the
visible object version or commit data.

ADR-0022 implements the T-0032 emulation telemetry seed. After successful
one-shot completion consumption, Sonatine emits one bounded versioned UART
frame with binding, observed status/detail/output versions, and QEMU machine
timer ticks spanning the kernel smoke path from manifest construction through
completion consumption. This is not execution latency. The host CLI ingests
only this frame into a separate mode-0600,
single-writer, hash-chained append-only cold journal with raw-log provenance and
full-history duplicate detection. Source/backend/evidence/platform are fixed to
Sonatine/QEMU/emulation and cannot be overridden by guest data. Re-ingesting the
same source is idempotent.

Completion telemetry is not `ExperienceRecord`, `MeasurementRecord`, semantic
validity, commit evidence, silicon performance, energy evidence, or active
retrieval input. Serial authenticity, crash-spanning exactly-once delivery,
cross-boot uniqueness, and real Daphnis telemetry remain unimplemented.

ADR-0023 implements the T-0033 kernel-owned metadata-shadow lifecycle.
Completion consumption retains the exact binding and descriptor until an
explicit one-shot commit or rollback. `EXECUTED` alone cannot commit; the seed
requires a separate injected kernel approval and revalidates every READ/WRITE
object generation, visible version, and range. All outputs must be exact
successor versions and multi-output publication prevalidates every target
before changing any visible version. Conflicting writers, cancellation, stale
bindings, missing approval, and replay fail closed.

ADR-0031 completes T-0085's bounded byte-shadow seed. Each object owns at most
512 visible bytes; admission snapshots referenced bytes, Data authority stages
only exact consumed-completion WRITE ranges, Program approval requires complete
coverage and freezes the shadow, and finalization publishes bytes with exact-
successor versions only after whole-transaction revalidation. Rollback,
cancellation, conflict, missing approval, and replay preserve visible bytes and
zero the shadow. The QEMU graph path stages its real GEMM output and validates
the checksum again from the committed backing.

This is still a volatile, single-hart, copy-based kernel seed. It provides no
general allocator, real Daphnis device, DMA/cache ordering, persistent recovery,
multi-hart atomicity, U-mode byte API, or hardware evidence. Queued cancellation
discards undispatched state; dispatched cancellation is sticky and a late
`EXECUTED` observation cannot commit.

## Executable track B: bounded Experience seed

Python標準ライブラリだけで、次の閉ループがあります。

- immutable JSONL cold evidence;
- fixed-limit active Experience;
- repeated exact observationのaggregation;
- invalid、negative transfer、strong improvementを優先するtail retention;
- workload/hardware/shape/memory distanceによるnearest retrieval;
- typed candidate ranking;
- trusted baseline first measurement;
- deterministic analytical ToyDaphnis backend;
- cold/warm HCR benchmark。

Gate 1 measurement infrastructure is also implemented:

- versioned BenchmarkManifest, EnvironmentSignature, MeasurementRecord,
  PolicySelection, and PolicyOutcome Python contracts;
- a common `MeasurementBackend.measure(context, candidate)` protocol;
- a committed six-workload powermetrics pilot manifest plus a separate
  24-holdout full manifest separating lineage, shape, working set, and operator
  composition;
- a native C adapter for GEMM, GEMM+bias+ReLU, and two-stage MLP with
  deterministic `int32` inputs, `int64` accumulation, and reference checksum;
- baseline-first, seeded randomized candidate schedules with five repetitions
  for the non-claim pilot and at least 15 for the full experiment;
- a tracked fixed-argument C helper and helper-only non-interactive
  sudo/powermetrics boundary; runtime root-ownership, non-symlink, and
  non-writable-path checks; standalone manifest-aware preflight; a minimum three
  CPU-power samples per measured window; a sampler-readiness barrier that
  excludes exactly its startup observation while preserving later samples
  already buffered in the same read; an explicitly synchronized fake-sampler
  regression that does not infer sample count from elapsed sleep time;
  thermal-stability checks; and same-Mac relative energy calculation;
- an optional, command-recorded between-workload cooldown that idles for a
  configured minimum and requires two consecutive valid thermal preflights;
  measurement-window thermal changes still fail closed and cooldown evidence is
  appended to the run bundle; the same recovery boundary follows backend
  preparation before the first measurement;
- paired-bootstrap, latency/energy HCR, joint NTR, full-history quality-gap,
  active-memory, equal-budget, and retrieval-p95 analysis functions;
- repetition-aware hierarchical-bootstrap sensitivity intervals, per-candidate
  energy-variation and normalized time-block drift diagnostics, plus start/end
  battery, available CPU-frequency, and system-load measurement context;
- fail-closed policy evidence analysis requiring an exact manifest-wide
  cold/bounded/full-history/FIFO/reservoir/random matrix, unique rows, matching
  run/manifest/budget/candidate provenance, preregistration before measurement,
  and summary values recomputed from raw measurements;
- a production policy-plan path that reads a sealed, disjoint-workload source
  run and generates equal-budget cold, full-history, bounded, FIFO, reservoir,
  and random candidate slates; target runs copy the plan before measurement and
  analysis automatically emits slate-bound outcomes;
- a committed 24-workload fixed-C history manifest with distinct IDs, lineage,
  and shapes but the same ten-candidate contract as the target holdouts;
- a target active-memory limit of 64 summary records versus 240 full-history
  records, fixed from source-only simulation before any target measurement;
- per-policy HCR, energy-HCR, coverage, calibration error, NTR, retrieval p95,
  measurement budget, active-memory maximum, and cold-evidence counts;
- `experiment run`, `analyze`, `seal`, and `sync` CLI lifecycle;
- ignored local research bundles with SHA-256/size manifests, immutable sealing,
  rclone immutable copy/download verification, overwrite refusal, and a
  completion marker copied last; mutable writes resolve and remain inside their
  own RUN-ID directory rather than merely the shared artifact root;
- a completed non-claim fixed-C sampler pilot with 90/90 valid semantic and
  measurement records, all nominal thermal samples, minimum power-sample count
  three, and a sealed Google Drive-verified bundle;
- a completed 24-workload fixed-C history-source run with 3,600/3,600 valid
  silicon measurement records, zero checksum mismatches, all nominal thermal
  observations, three-to-fourteen CPU-power samples per window, and a sealed,
  Google Drive-verified bundle;
- a completed first fixed-C target policy run with 3,600/3,600 valid silicon
  measurements and a complete 144-row pre-registered policy matrix; bounded
  retained 64 versus 240 full-history summaries and reduced retrieval p95, but
  its cold-relative median latency and energy improvements were both zero, so
  the Gate improvement and bootstrap criteria did not pass;
- a completed independent fixed-C target rerun with cooldown boundaries,
  3,600/3,600 valid semantic and silicon measurements, all measurement windows
  `Nominal`, a sealed and Google Drive-verified bundle, and the same zero median
  latency/energy improvement conclusion; its joint NTR was 12.5%, so the fixed-C
  Gate hypothesis failed independently;
- a pinned official Apache TVM 0.25.0.post1 / TVM FFI 0.1.12 Apple Silicon
  adapter that lowers the same int32/int64 workload and candidate contracts,
  commits constrained schedules to a MetaSchedule JSON database, queries them
  back before compilation, and passes a 60-kernel semantic/database-reuse smoke;

Not implemented or not yet evidenced:

- real graph IR and equivalence proof;
- a Gate-passing fixed-C policy result;
- system installation and post-`sudo -k` verification of the root-owned
  powermetrics helper and helper-only sudoers rule;
- neural representation、GAN/AAE、ANN;
- cross-hardware learned transfer;
- multi-objective Pareto policy;
- transactional database and distributed Experience。

## Verification status

The original Gate 0 acceptance suite contains nine tests covering the Python
loop, host-executable Sonatine Microkernel task/capability/IPC logic, and the
isolated debug-build contract. The current host acceptance suite contains 152
tests. On 2026-08-12 all 152 passed in 53.363 seconds on macOS with Python
3.14.6; one opt-in real-QEMU integration was skipped. The same
`scripts/ci-local.sh` run completed RV64 release/debug/DWARF builds, normal and
interrupt QEMU smoke, completion replay, Sonatine graph execution, and
native/QEMU semantic checksum differential with exit status 0. The suite now
also checks the Rocket wrapper's executable entrypoints, pin agreement,
immutable environment and volume-name boundary, and functional-only/non-claim
marker. This is implementation and emulation
regression verification, not EXP-0003 or Rocket performance evidence.

On the T-0022 policy-integrity worktree, `scripts/ci-local.sh` passed with exit
status 0: all 40 host tests, clean RV64 release/debug builds, DWARF checks, and
QEMU smoke. The ignored emulation smoke-log SHA-256 was
`314c185549dfd5e11e48f467320ac871e3862960bdb4d02d40ba86c909c0475f`.

On the sampler-readiness-corrected 2026-08-08 Gate 1 pilot worktree,
`scripts/ci-local.sh` passed: all 33 host tests, clean RV64 release/debug builds,
DWARF checks, and QEMU smoke completed with exit status 0. The QEMU portion is
emulation regression evidence only.

On the T-0068 least-privilege-helper worktree, `scripts/ci-local.sh` passed with
exit status 0: all 38 host tests, clean RV64 release/debug builds, DWARF checks,
and QEMU smoke. The ignored emulation smoke-log SHA-256 was
`c222caea0fdc41b0b3992a7772ddde6db99e2a693d915afff36283ffa73e018b`.

The artifact-creating environment did not contain QEMU or a RISC-V cross
compiler. On 2026-08-08, a user-operated Apple Silicon/Homebrew environment
successfully produced `sonatine/build/sonatine.elf` with the
`riscv64-elf-` toolchain. `file` identified it as a 64-bit RISC-V ELF, and
`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain` symbols.

On 2026-08-08 the native Homebrew path performed a clean release build, a
separate debug build, release QEMU smoke, and command-line GDB verification.
The release ELF contains no DWARF debug sections. The debug ELF contains
`.debug_info` and `.debug_line`; GDB 17.2 connected to QEMU 11.0.3,
installed a `kmain` breakpoint, and stopped at `src/kernel.c:25` with source
lines available.

Exact commands, tool versions, Git base revision, console output, and ignored
raw-log hashes are recorded in `EXP-0002`. A clean no-cache Docker build and
Docker-contained QEMU smoke also passed. Public commit `3347087` was then
cloned into a fresh directory: all nine tests, release and debug builds, DWARF
checks, and QEMU smoke passed. The same checks pass through
`scripts/ci-local.sh`. A GitHub Actions workflow briefly ran once during Gate 0
work before the local-only policy was clarified; it was then removed, and no
hosted CI/CD remains configured. A public-tree scan found no generated
evidence, build output, IDE state, credentials, or machine-local absolute
paths. Gate 0 is complete.

The installed IntelliJ 2026.2 C/C++ plugin exposes `Remote Debug`
(`CLion_Remote`) for attaching to an existing QEMU GDB stub. The configuration
type and required fields were inspected, but no claim of a completed
IDE-driven attach is made.

## Non-claims

- ToyDaphnis cycle values are analytical scaffolding, not accelerator performance.
- QEMU correctness would not establish FPGA/ASIC timing or isolation security.
- The Four-plane architecture, Rust/C++ split, Miroirs Graph Compiler, Pavane Semantic Oracle,
  Boléro Experience Runtime, Ondine Object Memory Subsystem, La Valse Optimization Subsystem,
  Scarbo Verification Subsystem, and native Daphnis Execution Subsystem are intended architecture, not all present
  in this minimal tree.
- No claim of removing general-purpose OoO hardware has been demonstrated.
- No Gate 1 latency or energy improvement is claimed. Independent fixed-C and
  pinned TVM target executions both produced zero median latency and energy
  improvement and exceeded the joint NTR limit. Their sealed bundles were
  immutably copied to Google Drive and download-verified. Gate 1 is closed as a
  falsified preregistered 5% hypothesis; the measurement system remains a
  maintenance-mode verification facility. Sonatine Gate 2 is complete on QEMU
  emulation evidence; this is not physical-hardware isolation evidence.
