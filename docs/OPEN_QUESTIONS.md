# Open questions

## Current integration state

PR302/51cb51d and Project Done resolve T-0242 publication. T-0243 implements the
already chosen packaging route without a new runtime or architectural boundary.
Functional acceptance now passes; only routine PR integration remains. Array commit
and report publication remain separate, with saved-view recovery for the latter.


## Image command decisions — T-0243

Use explicit existing kernel/runtime paths and a fresh output directory. Reuse the
foreground execution/cleanup path and verify saved results before rendering. No
new architectural decision is required for this packaging successor; prior ADR
statuses and EXP conclusions remain unchanged.


## Host inventory decisions — T-0242

Proposed ADR-0137 fixes descriptor-relative traversal without caching or skipped
semantic validation. The implementation and ordinary failure handling require no
new user choice. OS descriptor availability limits unusually deep trees; hostile
concurrent-host isolation remains out of scope. EXP-0014 determines the bounded
operating-cost result; it now passes the frozen retention criteria on all inputs.
No local design decision remains. Project scope recovered on October18 through
the owner-completed device flow, and Issue300 is admitted in S-0008. Only routine
verified integration remains; no new device or physical-performance decision is implied.

## T-0241 bounded decision resolved

The owner-authorized image demonstration/comparison is complete. Both frozen
per-input engineering criteria pass under the declared simulation policy. Retain
fusion for this bounded workflow and close EXP-0013; no additional owner decision
is needed for its local acceptance. Generality expansion is frozen. Practical CPU
replacement, generality across memory policies, physical feasibility and novelty
remain unestablished; they are not automatically converted into follow-on tasks.

## Data preparation decisions — T-0240

Proposed ADR-0136 fixes headerless decimal CSV, explicit u32/i32 input conversion,
literal-only target selection, fixed computation shape and new-file publication.
Local UT and actual import/edit/run/diff acceptance pass. No user clarification
is pending for this implementation. Automatic computation
reshape, arbitrary model import and new arithmetic types remain separate work.

## Foreground stop semantics — T-0239

Proposed ADR-0135 fixes this implementation's stop and commit race decisions; no
additional owner decision is needed; local UT/runtime acceptance now passes. Guest-clock
and host-monotonic deadlines remain distinct. Hard real-time cancellation, crash
recovery and native Windows remain outside this cooperative foreground change.

## Operational delivery — T-0238

Prepared backend snapshots, prerequisite diagnostics and JSON/CSV extraction have
explicit decisions in Proposed ADR-0134. No further user choice is needed for
implementation/UT/relocated functional acceptance. GitHub auth remains the external
publication dependency, not a local execution blocker. Kernel hashes alone do not
prove ABI compatibility; the relocated actual example has now passed, including
input editing, two-output diff and saved-only JSON/CSV. No operational question
remains for this bounded prepared-workspace contract; broader numeric/application
requirements and physical/performance work remain separate.


## Practical scope and fusion — T-0237

The scalar-materialization bottleneck is addressed by explicit v2 whole-stage
and single-output block compilation, not by raising backend instruction/register
limits. Source-level evaluation accounting and generated output-word accounting
are separate. Host gathering and repeated captured child execution still exist.

Application-level useful-size, latency, memory and numerical requirements remain
to be established for a chosen use; completing this compiler change will not by
itself settle them. Floating point, general importer/control support and device-
resident execution remain future scope. Current concrete external dependency:
GitHub CLI reports invalid authentication, so Issue/Project/PR synchronization
requires reauthentication. Local implementation and the stated fusion acceptance
are complete: 307 UT and 17 sealed QEMU/RTL parents. Broader application requirements
remain open; this closes the fusion implementation question only.

## Common-source QEMU/RTL question resolved — T-0236

The question of whether ADR-0132's generated pass compositions work through actual
QEMU/RTL is resolved for the declared contract and recorded acceptance corpus.
No implementation question remains for this supported common-source functional
workflow. Future floating point, dynamic control, model/IR import, optimized
execution and product hardening are separate roadmap work rather than an excuse
to leave the current path unverified. Issue #298 carries cumulative integration;
older public-adoption questions below describe the pre-integration state; neither simulation nor publication establishes physical performance.

## Phase-one implementation decisions resolved locally — T-0235

ADR-0132 fixes source grammar, numerical semantics, coordinate/fold/post order,
partitioning, lifetimes, static resource admission, capture limits, failure/retry,
compatibility and UT acceptance. No further user choice is needed to finish the
local implementation and UT. Future questions (outside that endpoint) are whether
what measured costs justify fusion/persistent execution and which later numeric/import/control
features serve real workloads. Capture reservation cannot guarantee arbitrary
future log sizes; hard inventory rejection remains explicit. Public adoption is
an integration dependency, not an unresolved algorithmic decision.

## T-0234 runtime scope resolved locally

The owner directed continuation immediately after the exact T-0234/V5 approval
question. New functional QEMU/RTL checks and source-version proof binding now pass;
local runtime approval is resolved. Public/canonical adoption remains separate.

Sharing may lengthen register lifetimes; ordinary admission can reject v5.
No universal v4-to-v5 admission guarantee, runtime benefit or physical result is
claimed. The five-node demonstration contains a redundant second maximum; the
separate modular branch covers meaningful original/translated-value reuse. The
new evidence is bounded functional validation rather than arbitrary-program proof.

## Signed coordinate coverage — T-0229 continuation

The unsigned-only generated harness gap is resolved locally by opt-in signed32
sources. All 24 boundary/fold/post/input-count categories have actual representatives
whose result depends on signed semantics and every declared input. The sampled
corpus is bounded to shapes up to 8x8 and fold extent 4; it does not establish
arbitrary-program correctness. Operation-placement observability holds across the
suite, not every category. Outside coordinates alone do not prove boundary-mode
sensitivity. Production scope and public adoption remain unchanged.

## Signed numerical validation resolved locally — T-0229 resumed

Explicit owner approval resolved the earlier automatic-review hold. V4 signed
max/ReLU now pass203 selected host tests,14 actual coupled sessions, semantic-rewrite
rejection and legacy saved compatibility. Public/canonical adoption remains open.
Negative JSON literals, signed reduction, saturation, floating point and widened
accumulation are not supported by this contract. Existing machine words and modular
arithmetic remain explicit; finite tests do not prove all programs or performance.

## Fresh execution after validation fixes — local T-0233

Resolved locally: current strict readers accept newly generated coupled evidence,
and a failed eight-stage flow can be retried from the beginning without altering
the failed capture. Receipt-derived counts confirm planner-selected execution.
Resuming partial guest state, new numerical semantics, physical performance and
public adoption are not established. The earlier T-0229 approval dependency has since been resolved and its local
validation completed in the resumed packet.

## Reproduction coverage — local T-0232

Resolved for the selected existing unsigned candidate: its144-file patch reproduces
from canonical and291 existing host checks pass. Changed-test discovery alone
missed Sonatine C authority/syntax and legacy project helper consumers; those checks
are now explicitly included in the reproduction record. Thirty-six saved parent
paths revalidate, but include one copied baseline. Full-repository testing,
new RV64/RTL rebuild and numerical T-0229 validation are not claimed by this task.
Public adoption remains pending; this is compatibility evidence, not novelty proof.

## Saved-proof review — local T-0231

Resolved in the local candidate: legacy JSON duplicate/type coercion, malformed
incomplete build identity and chain processed-count diagnostics. Existing valid
retained receipts pass. The reproduced mutations concern representation and
metadata; they do not establish acceptance of numerically wrong UART results.
Public adoption remains open; T-0229 local approval and validation are resolved.
These results neither prove all proof readers correct nor expand numeric support.

## Rejection-path review — local T-0230

Malformed DAG types and impossible saved processed counts previously escaped as
Python TypeError/AttributeError/IndexError. Typed admission and declared-count
checks now turn these into normal rejection. No successful false publication was
found. This finite correction does not prove every arbitrary corrupted proof has
a bounded diagnostic; it preserves the existing cooperative-files threat model.
T-0229 signed-ordering validation subsequently completed under explicit owner approval.

## Whole-flow partition advice limits — local T-0228

The separable objective covers total sessions then initial packed input words.
Linked inputs count in per-stage packing. The objective excludes intermediate
writes/copies, repeated fold/post accesses, artifacts, execution time and memory lifetime
across a streaming implementation. Output shapes are fixed independently of tiles;
future shape-dependent programs or overlapping stages would invalidate this proof
and require a new decision. Existing storage failures may remain after admission.

## Dependent grid-source flow limits — local T-0227

The candidate supports1..8 whole-grid stages with at most16 total coupled sessions;
all successful stage grids are assembled before a dependent stage begins. There is
no inter-tile streaming, overlapping execution, dynamic control flow or float/signed
arithmetic. Fixed compute admission does not guarantee evidence fits the unchanged
128MiB/16,384-entry capture limit: excess capture remains unsealed. Current sources
use at most2 jobs/session (32 total), not the underlying128-job batch envelope.

## Generated-combination coverage — local T-0226

Do affine packing, tile assembly and post-reduction semantics remain consistent
when coordinates and uint32 edge values vary together? Deterministic generated
checks pass for1,000 sources (989 with an admitted partition) and24 coupled
representatives. Initial false-green handling and weak selection were found and
corrected. Generated shapes are at most8x8 and fold extent4; existing resource
boundary fixtures remain separate. Passing finite generated cases cannot prove all admitted
programs correct, nor establish support beyond the declared source/resource limits.

## After post-reduction mapping — T-0225

The local v3 source composes one fold with one pointwise map over each tile's
committed result. It cannot read neighboring tiles or add independently shaped
global inputs to the post stage. Multiple dependent tiled stages, arbitrary source
DAG partitioning and dynamic control flow remain separate questions. Static tile
selection measures original packed-input words, not all intermediate traffic or
hardware latency. No broad tensor-language or vendor-advantage claim follows.

## Tile choice after T-0224

Finite host planning now searches all 1..16 uniform tile shapes locally. It can
recover an existing legal partition but cannot make an infeasible source fit.
The ranking counts sessions and packed words; actual latency, energy and optimum
hardware scheduling remain unmeasured. Sparse packing, nonuniform partitions,
signed strides, dependent tiles and dynamic control flow remain separate questions.
The planner emits ordinary explicit source and never authorizes execution.

## Cumulative integration boundary — T-0223

Source reconstruction from canonical archive plus the cumulative patch reproduces
all candidate hashes and selected changed tests. Native rebuild is byte-identical.
Offline RTL reproduces 14 source/emitted/binary/toolchain files byte-for-byte;
nine coupled parents pass. This local
acceptance does not imply public Issue/Project/PR adoption; the prior explicit
public-action approval hold remains separate. No new architecture is selected by
a reproducibility check.

## Affine input coordinates — T-0222

V2 removes T-0221's equal-input-shape and unit-output-grid-stride restrictions
locally: every view specifies its own row/column/fold map, and each input keeps
its own boundary dimensions. Signed coordinate strides remain unsupported, while
signed offsets and zero vectors allow shifted sampling and broadcasting.
Conservative rectangle packing can still reject sparse maps whose actual samples
would fit. Automatic tile selection, dependent multi-stage tiles and dynamic
control flow remain separate workload-driven questions. No general tensor language
or formal proof of arbitrary source semantics is claimed.

## After source-preserving grid lowering — T-0221

T-0221 locally resolves the T-0220 source-provenance gap: the complete original
grids/program, deterministic placements/lowering, nested coupled evidence and an
untiled coordinate oracle are bound and rechecked. Remaining constraints are
equal-sized inputs, unit output-grid stride, nonnegative fold steps, rectangular
halo packing up to 324 words per input, at most 16 independent tiles and existing
integer MF01 operations. Dependent tiled stages, automatic tile selection, sparse
packing and dynamic dimensions are not implemented. These require a concrete
blocked workload rather than a blanket claim of generality. First consolidate
the cumulative candidate and its compatibility evidence; public adoption is still
separate from local functional acceptance.

## After independent DAG composition — T-0220

Host batches support1..16 independent sessions and128 jobs in total; each guest
still has the existing limits. This does not move live objects between sessions
or partition a dependent graph. The image script proves an owned box-sum workload;
a general source compiler should preserve original grids/program, deterministic
layout/lowering, nested evidence, and an independent full-grid oracle. Fixed
sample scripts alone do not provide that source-level workflow.

## After bounded subrange links — T-0219

Explicit intervals now avoid unnecessary READ references locally. Whole producer
objects remain live/version-checked until the last consumer, so subrange support
does not solve live-capacity exhaustion. Graphs remain1..8 predeclared jobs with
one pinned final output. An extension to graph size, partial reclamation or spill
needs an actual blocked workload and independent failure/ownership evidence.
The full512-byte READ capability for each touched chunk is intentionally broader
than its materialized segment. No asynchronous device transport or physical
cost measurement has been added. Prior-art novelty claims remain unsupported.

## After T-0218 proof correction

Numeric-type and duplicate-key ambiguity in standalone session/chain/DAG proofs
is locally corrected. Wider schema/path/authenticity audits remain outside this
bounded repair. T-0219 resolves the bounded-subrange question locally: only touched chunks count
as READ references, while full-producer liveness remains conservative. Remaining
workload/live-capacity questions are recorded above; cross-chunk reads and resource
admission now agree in host planning, C decoding and guest snapshot materialization.

## Remaining boundary after T-0217 workspace integration

The separate DAG CLI is now connected to the existing project workflow locally,
including frozen input/kernel/runtime capture and saved comparison. Interrupts
or cleanup uncertainty stay unsealed; live device cancellation is not inferred.
Canonical/public adoption of the reviewed local candidate chain remains pending.
No unbounded graph, dynamic control-flow/loop support, spilling, asynchronous
transport reset, physical implementation or Groq performance comparison has run.
Future mechanisms need a concrete workload/measurement question; adding another
executor is not justified by the completed workspace integration itself.

## Remaining boundary after T-0216 DAG admission

Distinct-producer joins now work when unique READ chunks plus WRITE chunks fit
four references and all live results fit eight512-byte slots. Exact four-reference
layouts and pre-dispatch capacity rejection are locally verified. The designated
output remains pinned, while expired intermediate object identities become
historical receipts. All nodes must be predeclared in topological order, maximum8.

Next usability work is workspace integration of this existing executor and saved
records. Larger graphs, spilling/tiling to satisfy reference pressure, arbitrary
control flow, interactive streams, independent reset/cancellation and physical
cost remain separate questions. Static dependencies, liveness allocation and
bounded admission are established methods, not standalone novelty claims.

## Fan-in and intermediate lifetimes after T-0215

One distinct producer per job is locally implemented, including two logical input
arrays referencing the same producer. Full256-word read plus full256-word write
uses all four references. Two full-sized producers plus any destination cannot
fit that ABI. Smaller results may permit distinct producers by referencing only
needed512-byte chunks, but their allocation/lifetime/alias policy must be admitted
before execution. A bounded deterministic planner is the next candidate; widening
limits or silently overwriting live results is not accepted. Literal inputs remain
boot data and physical cost/transport/reset remain separate questions.

## Result dependencies after sequential sessions — T-0214

Bounded persistent-authority sessions are locally implemented and tested; earlier
one-job limits below describe T-0213. Session inputs are still independent frozen
boot data. A useful next candidate must make a named producer's committed output
a capability-declared snapshot input, reject failed/stale producers without
falling back to last success, and preserve four-reference/512-byte-object limits.
Two output banks appear feasible from source inspection; this is a design proposal,
not executed dependency evidence. Interactive sessions, concurrent work, a
persistent RTL process and independent reset/cancellation remain unimplemented.

## UART coupling boundary — T-0213

Guest-issued RTL execution and guest comparison before publication are now
locally demonstrated through a paced host UART broker.42 captured runs verify
protocol order and final completion binding. Actual replay across separate boots
and host deadline cleanup are tested. Remaining: persistent job sessions,
independent reset/late memory responses, live cancellation and a real MMIO/memory
interface. The one-boot prototype must not be treated as those mechanisms.

## Local MF01 emulation boundary — T-0212

The earlier provisional128-word QEMU subset is unnecessary: existing authority
already supports two512-byte outputs in one atomic finalize. T-0212 verifies
full256-word cases and partial second objects. This resolves the capacity question
without changing object limits. Inputs remain boot-time kernel data. A future
QEMU/RTL device must specify ownership, reset/drain, stale responses, private
memory and approval timing; separate agreeing executions establish none of these.
The current host oracle runs after guest commit. Resource placeholders do not
meter interpreter time or kernel scratch. Public adoption remains pending.

## Local adapter evidence and remaining boundary

T-0211 now connects admitted MF01 regions to project snapshots, private outputs,
read-only inspection and same-build comparison.37 retained runtime executions
pass their expected success/incomplete dispositions. A separate CLI check follows
the same path. Six coordinated synchronous core/responder reset-and-retry cases now pass.
Remaining: independently reset/stale-response transport behavior, QEMU/AXI
coupling, floating point/standard IR and physical cost evaluation. Cleanup uncertainty
leaves an unsealed run; it must never be treated as a completed result. Local
file hashes are not hostile-host authenticity. Public adoption remains pending.

Read-only next-step audit: current Sonatine/QEMU uses a128-byte GEMM-only v1
request and returns checksums; it neither accepts MF01/external arrays nor
connects to RTL. `SONATINE_OBJECT_MAX_BYTES` is512, versus a maximum MF01
output of1024bytes. A distinct request/output framing and an explicit object
capacity/chunking decision are prerequisites. A <=128-word guest software
interpreter would be a bounded semantic differential, not a full-capacity
replacement or co-simulation. No such implementation or capacity choice is
accepted here. Preserve GEMM v1 and existing authority/finalization boundaries.

## Local affine map/fold candidate boundary

T-0210 demonstrates direct two-input affine maps and bounded reductions in
standalone RTL. Integration into project snapshots/private output publication,
QEMU/AXI transport and standard IR lowering is still open. Floating point,
negative/data-dependent indexing, arbitrary loops and multiple outputs remain
unsupported. Coordinated mid-transaction reset has not been tested. Liveness
requires eventual memory acceptance/response; finite seeded stalls do not prove
all possible interleavings. Area/timing and full-cost comparisons are unknown.
Groq novelty/advantage is unresolved, not implied by increased Raveil coverage.
The exact candidate remains Proposed and unpublished; no historical gate passed.

## General grid contract and remaining limits

Owner-approved T-0208/#296 / ADR-0112 implements the dimension/kernel/boundary
contract. Each dimension is1..64;
existing bounded per-cell operations and one-pass uint32 semantics are explicit;
floating point, arbitrary-radius neighborhoods, multi-input/output, global
reductions, loops and QEMU coupling remain outside this candidate. Actual
generalized RTL acceptance passes three shapes/all boundary modes and edits;
host-only maximum-size coverage must not be promoted to physical performance
or all-size RTL evidence.

## Simulation maturity — current priority, ADR-0107

- T-0197 / ADR-0108 now specifies/version-controls the parent plan/result,
  frozen input/child descriptors and all-or-incomplete publication. Its actual
  execution acceptance is recorded in the October10 log. T-0205/#288 / ADR-0109 implements
  named-parent edit/compare workflow; ordinary single-run
  diff cannot compare child runs held in different private parent projects.
- T-0206/#290 verifies the five bounded criteria with actual and revalidated
  evidence, not the policy change alone. Wider instruction/shape support, a
  QEMU/RTL device interface and physical performance remain separate questions.
- T-0207 / ADR-0111 fixes and verifies one32x32 five-point spatial tiling
  contract: original/edited grids and host-boundary cancellation pass actual RTL
  acceptance, with exact evidence in the October 10 log.
  Arbitrary dimensions/expressions, multi-pass grids, throughput and physical
  fit remain separate; the four-child parent does not widen named composition.
- QEMU and RTL are separate current backends. Any necessary integration needs
  a bounded interface task, not an assumption that co-simulation exists.
- Windows/tool and board facts remain unknown but no longer block current
  implementation. Resource-fit and RAM-backend decisions remain later.

## Budgeted FPGA path — deferred until simulation maturity

- What Windows version/architecture, RAM, disk and installed tools are actually
  available? T-0188/#194 owns staged inventory; no FPGA is currently owned.
- What all-in acquisition can fit the owner's remaining monthly resources after
  existing Codex expense? Spend zero until a concrete quote/choice exists.
- Can the freshly reproduced RTL close in the selected free-tier tool on one
  affordable board? T-0189/#195 owns physical clock/reset/address/design closure.
  S01/ADR-0106 resolves the offline wrapper contract and S02/#279 now verifies
  full workload execution/recovery in simulation. S03/#282 resolves generic
  Yosys parsing/structural closure, with fresh functional regressions; FPGA
  mapping, resource fit and timing remain unknown. The OOC Tcl remains unverified
  by Vivado; qualified Windows/tool observations are a later hardware-stage dependency.
- Does the resettable register-array scratchpad cause actual mapped resource
  pressure? [S04 diagnosis](research/reviews/T-0189-memory-feasibility.md) locates
  the storage and compatibility obligations, but no RAM inference/fit or rewrite
  has been established. Vendor reports, not generic counts, decide priority.
- Which currently sealed graphs commission the first board, and what concrete
  parity gap prevents the third meaningful workload? Simulator features are not
  automatically UIO-authorized features.
- Where is end-to-end CPU/FPGA break-even after staging, installation, execution,
  validation and recovery? Pin representative inputs and a new measurement plan
  after functional closure; no novelty prerequisite applies to this prototype.


## Immutable-function questions — retained, no longer the entry gate

- T-0202 selects no new mechanism from seven concrete proposals. Known
  same-column CSE saves1,877 products but adds index/representation costs in
  the analyzed format. What specifically new search/transform algorithm, if
  any, justifies reopening? Family membership neither proves all algorithms
  known nor provides a difference by itself.
- Broader pair/scaled-form CSE, sparse full-rank factorizations and alternative
  bases remain unsearched. These are limitations of the bounded screen, not
  implicit next tasks or evidence of novelty. An exact workload/contract change
  requires its own rationale; no approximation inherits the current contract.
- How will a later evaluation acquire representative activation provenance and
  validate full-model quality? Current eight inputs are synthetic, parameter
  and input holdouts remain untouched, and finite tests are not universal proof.
- Before timing, how will library/build/threading/dispatch, warm/cold costs,
  specialization code/data and replacement costs be sealed under a new EXP?
- No residual treatment survived the current novelty screen. Published
  implementations were source-reviewed, not executed or defeated; stronger
  known-method performance comparisons remain absent.
- Do reduced operations also reduce complete execution cost after parameter,
  configuration, storage, physical movement and lifecycle overhead? The T-0199
  probe reduces neither its installation payload nor logical memory traffic.
- Does any benefit remain when the same transformed function is run on a strong
  conventional/Groq-like backend? If not, do not infer a hardware contribution.
- Integration: T-0199/T-0200/T-0201 are merged/Done; T-0202 is merged/Done through PR275. Weekly quota telemetry is no longer required.
  S-0005 ceremony date/disposition remains open after owner-directed deferral;
  task integration must not invent ceremony acceptance.

[ADR-0103](decisions/ADR-0103-work-reduction-precedes-new-execution-hardware.md)
sets the research order. T-0183 is complete; ADR-0107 restores T-0197 / #266 as next; T-0186 remains later product work; old next-pull
references below are preserved context, not competing active priorities.

T-0183 proposes obtaining two named results by composing existing single-output
Graphs with one frozen input and all-or-incomplete parent publication. This
does not share child arithmetic or widen STORE authority. T-0197 owns the new
runtime/record contract in ADR-0108; hardware multi-STORE remains deferred.

T-0196 resolves whether a compiled simulator can serve changed Graphs without
rebuilding: the actual cold/warm functional check passes. Wall-clock benefit
is still unknown: bounded dependency hashing/copying adds overhead. Do not
claim faster interaction from build counts alone or expand this into an open-
ended measurement project. Next user-program decisions remain T-0183/T-0186.

T-0187 selects a bounded compiled-binary reuse successor, T-0196, following
explicit owner continuation. Exact identity, dependency cache, safe publication,
hit/miss receipts and fallback require its implementation ADR and tests.
The planning decision adds neither runtime caching nor a daemon. Existing
two-request batching does not remove per-edit rebuilds after an old run exists.

T-0193 / ADR-0100 resolves initial saved-run sharing as explicit preview-bound
selected-file derivatives. Authenticated replay, archive import, automatic
privacy redaction and hostile-concurrency isolation remain out of scope.
T-0194 checks a derivative's self-contained consistency only; source hashes
remain unverified labels, not an authenticity or replay resolution.

- T-0191 remote-location question resolved 2026-09-19: the separately
  authorized recollection is copied to the existing private research-data
  destination and download-verified. Historical bundle availability below
  remains a provenance limitation, not a claim of recovery.

- T-0191 / EXP-0012 evidence availability (2026-09-18): can the historical
  hash-matching raw bundles be recovered from an existing private backup?
  Local run/RTL receipt verification fails. Otherwise a separately authorized,
  newly identified collection is needed; it cannot replace historical evidence.

Last updated: 2026-09-26

These items are intentionally unresolved. A conversation hypothesis does not
become implementation authority until an Accepted ADR or reproducible EXP
resolves it.

## Simulation-first device path

- T-0182 / ADR-0101 resolves the T-0181 opcode choice as unsigned GE_IMM_U32,
  descriptor v5/program v6/request v7, simulation only. Threshold-plus-cross-
  dilation fits 15/16 instructions without conditional effects. Old versions
  still reject the opcode. Full-width/source-free constants, saturating
  subtraction and general SELECT remain deferred; implementation verification
  is recorded separately in STATUS.

- ADR-0093 resolves saved project observation through a separate in-memory
  Garden view. Full provenance export/authentication remains separate: the
  project view does not invent missing identities or mint an execution seal.

- ADR-0097 selects unsigned 22-bit ADD_IMM_U32 for T-0173. Full-width or
  source-free constants remain unresolved, as do predicates and larger shapes.
  Program v5 / request v6 do not expand sealed UIO admission.

- ADR-0090 selects bounded explicit user input for T-0160. Full-width constants,
  predicates, arbitrary dimensions and larger windows remain separate choices;
  accepting input data does not make the language or hardware unbounded.
  Explicit-input sealing/UIO admission remains out of scope.

- S07 proves that the current unbased AXI4-Lite top can be exported twice to a
  byte-identical, source-bound SystemVerilog closure. T-0138 narrows the
  tentative target to KV260, Ubuntu Server 24.04 arm64 and license-free Vivado
  ML Standard 2025.1 on a supported Windows 11 x86-64 host. The exact
  clock/reset, absolute address, device-tree/UIO binding, bitstream/deployment
  identity, target package availability and recovery procedure remain
  unresolved. Checks 1--7 in the T-0138 packet and the ADR-0039 Project
  Manager/legal review must pass before FPGA implementation or evidence.

- ADR-0076 defines a no-device-open observation for Linux aarch64, the KV260
  model, FPGA-manager state and one exact UIO map. It does not answer whether
  Ubuntu 24.04 actually exposes those leaves on the owner's board. That target
  capability remains unverified until the physical owner runs the preflight;
  a PASS still does not select the overlay/load route or authorize FPGA work.

- ADR-0073 resolves only request-specific Linux runner rebuilding for the
  frozen three-Graph catalogue. Whether a production request bundle should use
  descriptor-relative open files, an immutable sealed directory, or another
  mechanism to close the admission metadata/read and runtime validation/reopen
  races remains unresolved; S08 does not claim adversarial filesystem-race
  resistance.

- ADR-0074 proves only that one locally compiled simulator can consume two
  requests through the shared admission boundary. Whether a persistent warm
  simulator cache or service is worth its invalidation, isolation, and receipt
  complexity remains unresolved; S09 deliberately does not introduce one or
  claim a measured startup improvement.

- ADR-0075 exposes exactly two ordered requests through the operator CLI. The
  trigger and contract for a larger batch, concurrent requests, a long-lived
  simulator process, or a persistent compiled cache remain unresolved. S10
  must not turn the fixed pair into an accidental scheduler or performance
  claim.

- ADR-0084 selects the first address-generality discriminator: descriptor v2
  and program/request v3 directly encode signed row/column deltas in each load,
  bounded to the existing one-cell halo. T-0148 must prove all eight non-center
  3-by-3 neighbors on one unchanged-capacity executor while retaining v1/v2
  bytes and semantics. Whether to increase the 16-instruction capacity, add a
  higher-arity reduction, admit a wider halo, or add constants/predicates is
  unresolved. Nine loads plus eight binary reductions plus one store cannot
  fit the current capacity. T-0148 now passes this bounded discriminator; it
  does not resolve those next language choices.

- ADR-0077 selects the next discriminator: a repository-authored Graph absent
  from the three-entry catalogue must compile at runtime and produce oracle-
  equal output through the same simulator binary as one catalogue Graph,
  without RTL or device-ABI change. T-0140 does not resolve how descriptors
  become authorized production inputs, how a dynamic envelope is sealed for
  Linux UIO, or what language/opcode/affine expansion would be useful.
- ADR-0078 resolves only the unnecessary catalogue companion for one dynamic
  simulation request. It preserves the two-request proof and every existing
  compiler/RTL/ABI/opcode/profile/capacity bound. Descriptor authorization,
  immutable sealing, filesystem-race closure and a dry-run conversion toward
  the Linux/UIO adapter remain unresolved and require a separate accepted host
  admission/transport decision before any device access.
- ADR-0079 and T-0142 now resolve the local host-admission portion: one exact
  descriptor/source snapshot is sealed, verified into retained bytes and
  replayed without descriptor reinterpretation, while a pure UIO plan stops
  before `open`, `mmap` or MMIO. They do not authorize a device run or answer
  which single additional opcode is useful.
- ADR-0080 and T-0143 select only unsigned `MAX_U32` for one five-neighbor
  dilation discriminator. Program, dynamic-request and sealed v2 admission is
  explicit, while the transport/install ABI v1 and existing v1 program bytes
  remain unchanged. Whether any later opcode, predicate, constant, selector,
  schedule or broader Graph language is useful remains unresolved and requires
  a separate discriminator and decision.
- ADR-0081 and T-0144 answer only how the accepted bounded lowering and retained
  execution identities are projected in a read-only Garden view. The compiler
  owns the trace and Garden has no execution or promotion authority. Whether a
  future explanation artifact should be emitted directly beside every sealed
  replay, receive a durable signature, or cover a broader Graph language
  remains unresolved and requires separate authority and threat-model work.
- ADR-0083 and T-0145 resolve only the software handoff from an ADR-0079-
  verified sealed-v2 request through a private projection and fake register
  transport. The compiled ARM64 C++ adapter has no device opener at all. Real
  KV260 device access, an unbypassable verified-bytes-to-opener handoff, target
  package and overlay identity, recovery, and whether the projected request
  lifetime needs a stronger same-privilege threat model remain unresolved for
  a separately authorized physical task.
- T-0128/S02 answers only how one S01-admitted frozen descriptor and seed
  map onto the existing program/config/execution ABIs in RTL simulation. It
  does not broaden the three accepted identities or answer the generality
  question. T-0128/S03 now exposes that exact lower-level
  selected runner through the same top-level CLI without changing the ABI and
  revalidates marker, path, raw evidence, and receipt. PR #43 made this bounded
  answer canonical. No accepted discriminator yet authorizes a larger Graph
  catalogue, selector/opcode/window boundary, scheduler, or generally
  installable claim.

## Project inventory scope and evidence gaps

- The owner retains original broad T-0042 research as unfinished, while
  accepted ADR-0046/main TODO close a narrower controlled-run result. The
  Project scope card is deferred, with T-0106/T-0044 as the existing remaining
  outcomes. PM must reconcile the intended remaining scope before any research
  resumption; neither workspace delivery nor this audit closes that question.
- T-0149, T-0148 predecessor, T-0148 editable-Graph continuation and T-0151
  are integrated on main. Independent edits are
  preserved, the UIO defect is canonical T-0152, and the Graph decision's
  colliding local ADR-0086 is explicitly reconciled as ADR-0087. Historical Done draft cards have varying
  evidence locators; the inventory records missing receipts rather than
  certifying them from their status alone.


## Native execution

- ADR-0020 fixes the bounded job/completion envelope. ADR-0021 fixes only a
  boot-scoped, kernel-owned ObjectManifest table and ring seed. Persistent
  object lifecycle, graph encoding, memory consistency, exception semantics,
  reset uniqueness, and device transport remain open.
- ADR-0022 fixes QEMU completion ingestion as segregated cold evidence. What
  acknowledgement/retry and durable boot identity are required for
  crash-spanning exactly-once real-device telemetry remain open.
- ADR-0023 fixes single-hart metadata-version finalization and cancel-wins
  behavior. How should byte-shadow storage, cache/DMA ordering, verifier
  identity, reset recovery, and persistent multi-object atomicity work?
- RFC-0005 fixes at least 10% total dynamic-energy-proxy improvement, no more
  than 5% correct-latency regression, break-even by 64 invocations, and at most
  25% incremental Rocket-core area as later no-go thresholds. EXP-0005 now
  freezes the fresh-input inference rule, paired estimator, repetitions, 95%
  interval construction, and latency/traffic stop rules before pilot data.
  EXP-0008 now resolves the bounded 64/256-input latency/traffic campaign with
  `advance-partial-latency-traffic`; ADR-0050's immutable remote promotion is
  now complete for both sealed RUNs, with download checks, marker readbacks,
  and a tracked 20-file receipt. This durability result does not resolve the
  matched synthesis/energy/area boundary or full T-0044 organization matrix.
- Where is the measured boundary between static, elastic dataflow, stream, and
  hybrid Graph Execution Subsystem organizations?
- How large should the RISC-V core's OoO machinery be, if any?
- Which regions remain on RISC-V or bounded dynamic tiles: pointer chasing,
  interpreters, JITs, branch-heavy control, exceptions, and unpredictable
  traversal?
- If the fixed-latency RFC-0005 candidate fails, is that a no-go for the initial
  path or sufficient evidence to draft a separately reviewed variable-latency
  mechanism? Elastic token/readiness machinery is not authorized by RFC-0005.
- ADR-0049 fixes that a loadable schedule, configurable route/FU array, or
  token-ready successor is evaluated as existing VLIW/CGRA/dataflow mechanism,
  not Raveil novelty. Which source-, revision-, license-, provenance-, and
  IP-risk-reviewed public implementation is the smallest faithful T-0044
  control and possible Daphnis adapter? T-0044/S00 now retains OpenASIP v2.2 as
  the sole bounded feasibility-spike candidate, not an adopted adapter. Can a
  pinned Linux build execute three distinct programs on one frozen ADF/RTL
  identity while exposing full program/configuration costs and preserving a
  Raveil-owned effect/fallback boundary? Public access or an OSS license alone
  is not patent clearance. EXP-0012 answers only the frozen-ADF simulator and
  Raveil publication/fallback portions positively, and records a normalized
  generated-VHDL identity plus bounded TPEF/load diagnostics. Cooperative
  cancel-wins is proven at the lifecycle publication boundary. The corrected
  PID-bearing Docker observer now witnesses real compiler/execution-ttasim
  process cancellation and container absence. Durable evidence, independent
  final acceptance and patent/FTO questions remain open; this does not show
  simulated instruction progress before cancellation.
  Accepted lifecycle receipts now project only reviewed results and the
  canonical private-receipt identity; this does not resolve those remaining
  questions or authorize publication of the private raw receipt.
- Which three semantically distinct operation graphs provide the smallest
  no-RTL-regeneration test of temporal configurability, memory behavior, and
  contract parity without expanding into a general OoO/dataflow engine?
- Can one pinned Chisel/Chipyard environment support a fair matched comparison
  among Rocket in-order, BOOM OoO, BOOM's same-core serialize-dispatch diagnostic,
  and an owned explicit-graph tile without inheriting upstream authority or
  comparing unequal cache/memory/functional resources? ADR-0046 answers the
  bounded resource-connection part for Rocket, BOOM, and static Graph: the
  strict controlled run proves the canonical owned tuple equal, preserves the
  exact oracle, brackets quiescent windows, and conserves all admitted traffic.
  EXP-0005 resolves the bounded primary execution-window fairness question:
  Graph admits 1,536 transactions because its fixed schedule issues five loads
  per output, while each optimized CPU admits 1,056 because lawful software
  load reuse reduces 1,280 useful loads to 800 manager reads. The difference
  is visible, neither CPU is weakened, and the execution-latency/traffic pilot
  is eligible. EXP-0006 now proves that one installed configuration accepts
  four repeated fresh inputs without simulator reboot for every candidate,
  including exact installation and invocation accounting. The remaining
  single measurement-boundary question is narrower: what same-meaning
  initiator should generate or admit each fresh input when CPU generation is
  candidate-local but Graph generation is testbench-side? Until that staging
  boundary is resolved, end-to-end amortization and the 256-input campaign are
  paused. ADR-0047 resolves the intended controlled-measurement architecture as
  a fixture-owned, phase-exclusive provider. The implementation now holds the
  CPU's first input load with its complete TileLink payload stable, admits no
  candidate request before final provider response, and adds no port, request
  buffer, bank, or polling protocol. Focused negative tests and a Graph
  four-input RTL run pass. Frozen EXP-0007 complete 1/4 commissioning verifies
  the same boundary on Graph, Rocket, BOOM, and diagnostic BOOM and closes this
  staging-initiator question. The separately preregistered 1/4/16/64/256
  campaign and the remaining T-0044 organizations/physical metrics stay open.
  EXP-0008 now freezes the nested-prefix and paired-latency analysis before
  data. Its first collection preserved all completed primary sessions but hit
  a hardcoded operational timeout in the diagnostic column; a hash-bound retry
  of that diagnostic completed and the full matrix is sealed. The bounded
  latency/traffic question is now answered in favor of continuing: the
  64-input upper correct-latency bound is 0.2086002 and break-even is input 1.
  Energy, timing, area, IP disposition, and the
  missing organizations remain open even if latency does not trigger no-go.
  ADR-0048 resolves only the next measurement order: first run a same-library
  partitioned Graph/Rocket area/timing lower-bound screen, then design an
  integrated fallback/common-memory/activity boundary if it survives. EXP-0009
  has commissioned the toy synthesis/STA toolchain and frozen its partitioned
  Graph/Rocket manifest, but bounded Graph attempts paused before synthesis
  because the common black-box partition was not Yosys-visible under the frozen
  `m:` selection form. A pinned-tool probe now establishes named-module
  selection, single instances, and verified black-box attributes for both
  common modules; this collector-only repair still
  requires a recovery-v4 freeze and complete Graph/Rocket run. The candidate
  matrix has no area/timing datum. The valid
  whole-system dynamic-energy composition remains an
  open question.
  Recovery-v4 Graph `run-005` preserved the named cut through mapping but
  failed its library-unaware post-map integrity check before any report. Toy
  probes isolate a collector-only Liberty/OpenSTA compatibility fix; until its
  replacement freeze produces the complete Graph/Rocket matrix, both the
  physical lower-bound and whole-system composition remain unresolved.
  Recovery-v5 then produced sealed raw reports but no eligible derived result,
  because OpenSTA inferred the two intentional common modules instead of
  reading explicit declarations. Recovery-v6 must make those cut declarations
  exact and visible before either physical question can advance.
  Recovery-v6 now yields a complete Graph-partition estimate, but Rocket
  `run-008` fails before synthesis on Yosys-incompatible packed-array syntax.
  The remaining narrow question is whether the pinned upstream
  `ENABLE_YOSYS_FLOW=1` emission, with byte-identical shared elaboration and
  only `disallowPackedArrays` added, can complete the Rocket partition under a
  single fresh Graph/Rocket manifest. Until then no area ratio, timing
  comparison, or whole-system composition is eligible.
  The first physical build shows identical normalized shared inputs and module
  sets, but the export checker itself needs one exact-root/order normalization
  recovery before this question can be tested by synthesis.
  That normalized export now passes the packed-array inventory and pinned
  Yosys pre-synthesis checks. Whether the complete paired physical matrix
  passes remains open pending recovery-v7 freeze and fresh runs.
  Recovery-v7 now freezes the exact policy and identities; the question moves
  to the fresh paired synthesis outcome, with no prior result import allowed.
  Wrong-directory `run-009` is explicitly ineligible; the outcome question is
  unchanged after moving exact RTL identity validation before Docker launch
  and mounting only its independently reverified private snapshot.
  Recovery-v8 freezes that boundary; only its fresh paired outcome can answer
  the remaining physical-screen question.
  Its Rocket raw run exposed a report-parser assumption rather than an RTL or
  timing outcome. The question therefore remains open until the exact frozen
  top is selected unambiguously and both partitions rerun under one recovery.
  Recovery-v9 now freezes that selection; the unresolved fact is the fresh
  paired physical outcome, not parser behavior.
  The v9 outcome resolves area-screen plumbing but not timing comparability:
  Graph meets and Rocket misses the same 20 ns target. The one remaining
  physical question is which frozen timing boundary can make the fallback
  partition eligible without weakening either candidate or changing resources.
  EXP-0010 narrows the test to one fixed 40 ns follow-up selected after the
  20 ns pause. Whether both unchanged partitions meet that single common target
  remains unresolved until its manifest is frozen and fresh runs complete.
  The manifest content is now frozen at `a09a641...b76ef`; only the fresh
  same-manifest outcome remains unresolved.
  EXP-0010 resolves the single 40 ns follow-up positively. The 20 ns outcome is
  unchanged. The remaining physical question is the integrated composition:
  fallback, Graph, common memory/fixture, adapters/interconnect, clocks, and
  placement/routing must be present before any whole-system conclusion.
  T-0044/S08 now answers only the elaboration and functional-structure part:
  one top contains the fixed Graph core, Rocket fallback, common fixture and
  owned memory, selector, cache/interconnect, and common clock/reset boundary;
  a matched Rocket-only closure passes the same structural checks. The open
  question is whether an independently reviewed, pre-data-frozen integrated
  physical experiment can account for every included and excluded component,
  preserve fair memory/interconnect/fallback and I/O constraints, close the
  hierarchy, and retain any area/timing advantage. Placement/routing and energy
  remain unmeasured.
  The S08 fairness review makes that question executable: the future manifest
  must normalize common clock endpoints and reset semantics, enumerate the
  identical common subgraph and every allowed Graph/selector delta, bind macro
  Liberty/LEF plus PVT/RC treatment, and freeze the estimand, overhead ledger,
  seeds/repetitions, uncertainty, and raw seal. Equal port names and macro
  counts alone are insufficient. The unequal but explained Graph/Rocket
  dynamic traffic must remain a reported design result rather than an equality
  assertion.
  S14 found no verified public view set for the exact seven macros and no
  already qualified standard-cell substitute. The next unresolved choice is
  whether to propose and validate an OpenRAM-generated identical seven-view set
  or to pre-data refreeze both candidates around one common standard-cell
  memory implementation; neither path is authorized yet.
  S11 makes those identity, denominator, oracle, traffic, physical-condition,
  and non-claim declarations machine-checkable in an unallocated v2 document.
  S12's unallocated v3 contract now fixes paired physical-flow seeds 101 and
  202, typed absolute and incremental area plus 40 ns timing estimators,
  explicitly unavailable statistical intervals, fixed decision thresholds,
  and ADR-0050-strength failure/recovery/evidence sealing. It does not resolve
  the declarations against real P&R artifacts. The exact available
  macro/standard-cell/tech/RC/floorplan inputs and their hash-bound manifest
  remain open. HCI-02 was authorized, and the first exact inventory resolved
  the standard-cell, technology, and RC inputs but found zero required Liberty
  timing or LEF geometry/pin views for each of the seven memory macros in the
  pinned public image. Matching GDS files are also absent, but that is
  supplemental to the P&R pause. The boundary is now narrower: obtain and review a compatible common
  macro-view set, pre-data refreeze a common standard-cell memory
  implementation, or pause the custom integrated physical line. Any choice
  must apply identically to both candidates and must not use placeholder or
  zero-area blackboxes.
  S15 answers whether one repository-owned common source can reproduce the
  seven macro type signatures and tested functional semantics and survive
  pre-mapping collection: yes, for 28 counted Verilator checks and seven fresh
  one-memory/no-blackbox Yosys tops. S16 further answers the real-hierarchy and
  evidence-chain parts: both candidates resolve all eleven exact instances
  with complete clock/mask connectivity, identical Rocket identity and clock
  policy, zero reachable blackboxes, and an independently replayed sealed
  runtime/contract/bundle chain. It does not answer the physical question.
  Which reviewed common Liberty/LEF view set and identical future mapping
  procedure can eliminate every `$mem*` cell without destroying the fair
  physical denominator or the integrated advantage? That remains the single
  S13 resume boundary before EXP-0011 allocation or claim-bearing data.
  The earlier
  source survey found
  no existing upstream config that proves this boundary: Rocket's tile-internal
  `WithScratchpadsOnly` does not match BOOM, while the shared subsystem
  TileLink banked scratchpad now passes the exact stencil on both controls but
  at that stage still needed an owned adapter and explicit proof of ports, buffering,
  arbitration, fixed latency, and equivalence to the Graph storage boundary.
  The passive TLRAM observer found one-cycle bank-local intervals for all 296
  read beats in each pinned control run, but no write beat and no initiator or
  lifecycle attribution. Which owned boundary can expose those missing facts
  without altering the compared machines? ADR-0043 answers only the local
  protocol half with an owned one-outstanding attributed scratchpad target.
  The Graph side now reaches disjoint logical regions in one physical owned
  instance for functional staging, execution, validation, and
  cancel/drain/restart. The strict controlled adapters now reach that boundary
  with equal ports, buffering, arbitration, staging, operation width, and phase
  accounting without changing the frozen workload or core microarchitectures.
  ADR-0044 answers the preceding
  translation step: an observable, uncached peripheral-bus manager can be
  added to dedicated Rocket and BOOM configurations, but it is deliberately
  resource-unmatched. Its direct monitor-enabled TileLink harness now verifies
  the manager-local legal Get/Put/mask/denial/backpressure/metadata paths, but
  bypasses the CPUs. The same phase-fenced ELF now reaches the manager through
  both Rocket and BOOM and validates identical expected data and aggregate
  counters. Exact generated graphs and runtime A/D audit registers now
  distinguish the config-specific DCache-MMIO TileLink client class from the
  SimTSI/FESVR serial range and observe only the expected class for the eight
  data transactions. That source class is not semantic proof that the target
  ELF initiated each transaction and is not ADR-0043 owned initiator metadata.
  A standalone TileLink-to-owned bridge now proves the mechanical handoff of
  explicit initiator/phase metadata plus source/size response correlation, but
  its harness supplies the metadata and neither CPU is connected. How should a
  CPU-side boundary assign durable semantic initiator attribution, separate
  loader/FESVR/debug activity, and fail closed beyond topology-dependent source
  IDs? The common point immediately after each DCache and before the shared
  tile master Xbar is now instrumented by repository-owned Rocket and BOOM
  hooks. A one-bit request field is retained through manager-local A/D
  correlation: both CPU smokes observe origin 8/8 and an untagged raw client
  observes origin 0/0. A test-only marked raw client now also drives origin
  true before an adapter removes the field; the manager observes origin 0/0,
  proving fail-closed metadata loss. A dedicated four-byte writable PT_LOAD
  now exercises one real pinned SimTSI/FESVR transport path: its pre-CPU
  serial-class traffic is origin 0/0 and non-origin 2/2, while the subsequent
  CPU read adds one tagged DCache-origin completion. This proves a bounded
  transport negative and structural DCache origin only, not complete
  loader/debug exclusion. One concrete repository-owned DMI-to-Debug-SBA write
  now completes as non-DCache origin in both CPU configurations before a tagged
  CPU read. Which remaining DCache-local loader/debug traffic must fail closed,
  and what additional durable witness is required to distinguish DCache origin
  from a particular target-ELF instruction? What later topology makes both CPU
  and Graph use equal memory resources without hiding traffic in caches?
  The regular and PT_LOAD workloads now form an executable counterexample:
  distinct ELF hashes and semantics reuse exact DCache source 8224 on Rocket
  and 8288 on BOOM. Therefore any accepted witness must add owned identity and
  replay/flush/commit rules rather than reinterpret the existing source/origin.
  ADR-0045 fixes CPU-owned token, epoch, replay, kill, exception, reset, and
  commit rules. A bounded pinned Rocket probe now validates accepted request,
  DCache-tag capture, separately matched load response, and WB retirement for
  one positive store/load workload. One bounded negative additionally records
  an accepted wrong-path store and blocks its promotion on a simultaneous
  older-branch MEM redirect, with matching completed loads before and after the
  probe. A separate exact-config run now directly correlates that Rocket
  request to following-cycle `s1_kill=1` and independently observes only the
  two before/after load A/D pairs at the owned manager. It does not carry the
  Rocket token into TileLink. A fourth pinned run correlates one accepted
  misaligned load with its later WB exception and exact trap recovery, but does
  not observe a corresponding TileLink A or post-A rollback. The one-entry
  Rocket observer still does not validate multi-token operation, pre-request
  kill, post-A exception/rollback, replay, reset/epoch, durable transport-token
  correlation, store authorization, complete owned-manager lifecycle, or
  semantic initiator identity. A first pinned BOOM positive now correlates one
  exact LSU DCache load request, response, and architecturally valid ROB commit
  by repository sequence; ROB/LDQ indices and branch mask are context only. It
  does not carry that sequence into TileLink. A separate BOOM negative now
  correlates one exact misaligned-load
  candidate with its LSU exception, a matching DCache request accepted after
  the exception, and later global ROB rollback state while requiring no
  matching response or architectural commit; the faulting entry is not a
  matching rollback row. Because exception precedes request acceptance, it does
  not close post-request exception handling. A second BOOM negative now
  correlates one cacheable wrong-path LSU DCache request and response with a
  later branch kill and zero matching commit, but does not exercise the owned
  PBUS manager or post-A transport. The remaining question is which
  epoch/reset-aware authority can safely promote the now-observed BOOM-local
  store token transport. One fixed-epoch diagnostic carries
  `{valid, epoch, sequence}` through DCache/TileLink and retains the same token
  from owned-manager Put A to D without promoting ROB/STQ/source context. Still
  open are stale/duplicate/exhausted token rejection, reset with outstanding
  work, replay/source reuse/backpressure, malformed nonzero metadata,
  untagged loader/FESVR/Debug traffic, BOOM load and Rocket parity, CPU-side D
  consumption, and the boundary that may drive `InitiatorCpu`. One negotiated
  absent-producer negative now observes invalid/zero at manager A/D and blocks
  attribution without blocking the store; it does not answer those remaining
  questions. ADR-0046 resolves the sequencing question: none of these remaining
  general-attribution cases gates the controlled-run T-0042/T-0044 slice.
  One bounded T-0106 carry-in now clears a known-valid token to invalid/zero
  before TileLink A and verifies unknown classification, transaction completion,
  and store readback. It answers only value-clearing after one fixed producer;
  physical field removal and the other lifecycle cases remain open.
  T-0106 retains the open design question of how Rocket and BOOM obtain direct,
  non-synthetic signals before general semantic promotion into the ADR-0043
  bridge, but it begins only after T-0044 survival or an accepted product need.
- ADR-0040 fixes BOOM's source coordinate and proves its `disableOOO` mode only
  serializes dispatch while retaining ROB, rename, issue, and LSU structures.
  Which separately synthesized structural ablation, if any, is scientifically
  valid without turning BOOM into a different and unfair core?
- Which transition boundary should follow a successful simulation: a
  RoCC-like attached engine, a standard/custom RISC-V extension, a programmable
  accelerator fabric, or a separate ASIC plane? None is selected yet.
- Which intended jurisdictions and concrete proposed features require a
  qualified claim-to-feature patent review before moving beyond research
  simulation? Preliminary WaveCache and EDGE-family hits are unreviewed and
  cannot support an FTO conclusion.

## Experience and policy

- Does Experience generalize frequently enough to amortize its search and
  verification cost?
- Which consolidation method best retains ranking reversals, rare failures, and
  negative-transfer boundaries under a fixed online budget?
- How should evidence age across software, compiler, firmware, and hardware
  changes?
- When should retrieval abstain rather than transfer?
- How are latency, energy, memory, tail risk, and correctness combined:
  weighted score, constraints, or Pareto selection?
- How should the Adaptive Council allocate proposer and reviewer budgets without
  majority-vote failure or policy monoculture?
- What access pattern and scale, if any, justify an Experience Processing Unit?

## Measurement

- Under what new workload and candidate-separation pilot should Experience
  research resume after fixed-C and pinned TVM both falsified the Gate 1 5%
  transfer hypothesis?
- Which Transformer or other AI workload is small enough to reproduce yet
  repeated enough to demonstrate useful Experience transfer?
- What threshold makes Negative Transfer Rate unacceptable?
- How should semantic and numerical equivalence be tested for approximate AI
  workloads?

## Kernel and platform

- After human evaluation of the Native Interactive CLI, which concrete missing
  operation or isolation property, if any, warrants further Sonatine shell
  expansion rather than another Native userspace increment?

- After the ADR-0024 GNU/Linux userspace MVP, which measured property, if any,
  justifies promoting Sonatine, a Linux kernel adapter, RISC-V, or another
  specialized authority path to a release prerequisite?

- Parse the QEMU device tree or retain an explicit fixed-machine contract?
- ADR-0018 fixes the pre-VirtIO seed as two bounded root nodes, pointer-free
  scalar I/O, immutable initramfs, and volatile RamFS. Arbitrary paths,
  copyin/copyout, and per-node authority remain future design.
- ADR-0015 fixes Gate 2 delegation as attenuated, non-recursive leaf grants.
  ADR-0016 retires a flat capability slot before its generation can wrap.
  Which derivation-tree, cascading-revocation, and endpoint object-lifetime
  semantics are needed before Daphnis rings are exposed to U-mode?
- After T-0030 fixes JobDescriptor and CompletionRecord, which Linux transport
  should follow the ADR-0019 userspace harness: a kernel adapter, vhost-user,
  VirtIO, PCI, or another owned boundary? DMA/IOMMU/IRQ/reset remain undecided.
- ADR-0030 uses one coarse Data-producer authority domain and volatile
  boot-scoped Program/Graph registries. Before untrusted multi-user or device
  exposure, which per-object capability, persistent identity, revocation-tree,
  reset, and signed-admission rules are required?
- ADR-0031 fixes the current object backing at 512 bytes and single-hart
  copy-based publication. Which allocator, DMA/cache ordering, device reset,
  persistent recovery, and multi-hart publication protocol should replace this
  seed before real-device exposure?
- Does the installed IntelliJ C/C++ plugin expose a genuine remote GDB run
  configuration? The observed UI has not established this.

## Ecosystem

- T-0105 deliberately closes its functional substrate on fixed linux/amd64
  emulation. Before T-0044 performance work, should the matched Rocket/BOOM/
  owned-Graph environment remain emulated amd64, move to a pinned native-arm64
  CIRCT build, or use a dedicated amd64 host? That choice must be made in the
  comparison contract and cannot reuse T-0105 timing as evidence.

- Which additional context-sensitive completions, if any, justify more parser
  coupling after T-0102? Persistent history, fuzzy completion, arbitrary PATH
  lookup, shell expansion, and external completion scripts remain outside the
  current bounded Native CLI.

- After the T-0101 allowlisted command-graph slice, which additional shell
  grammar and tools provide enough real workload coverage to justify their
  authority and portability cost? General `sh -c`, arbitrary executable
  lookup, command substitution, and ambient environment inheritance remain
  unresolved, not implied follow-ups.
- After T-0149 completes the first editable project loop, which operator
  friction most prevents a third run: recipe authoring, Graph explanation,
  output inspection, run selection, or the Native/Sonatine boundary? The next
  product slice must follow observed hands-on use rather than adding commands
  speculatively.
- T-0148/S02 connects authoring to the dynamic RTL path. Which observed limit
  should the next Graph increment address first: the 16-instruction ceiling,
  a missing arithmetic operation, seed-only input data, or simulator startup
  latency? Selection requires hands-on evidence; this slice authorizes no
  broader opcode set, input protocol, persistent cache or capacity change.
- T-0155 addresses observed authoring-order friction through ADR-0088's stable
  topological scheduling. The existing sixteen-instruction/eight-register
  limits remain; selection among different valid schedules to reduce register
  pressure is a separate future question requiring an actual rejected workload.
  T-0184 now supplies actual rejection probes, but their register failures
  include unreachable values and do not establish intrinsic register demand.
  Advisory preflight hints are selected; capacity/reuse/tiling remain undecided.
  T-0195 implements those hints without changing acceptance. The subsequent
  owner-approved ADR-0101 separately authorizes T-0182 comparison work, not
  register/capacity changes.
- Should local run history eventually gain human labels, a compact content
  diff, export/import, or garbage collection? T-0149 retains exact bounded
  snapshots and hashes only. It is deliberately neither a production cache nor
  a signed evidence store.
- T-0157 selects unsigned multiplication as the next bounded arithmetic
  extension. Immediate constants, signed/saturating arithmetic, multiply-add
  fusion, timing/area optimization and additional operators remain separate
  requirements; this slice only admits the low 32 bits of two uint32 operands.
- T-0103 demonstrates only immutable-by-name showcase cache entries. What
  durable artifact lineage, tool/environment/policy/workspace invalidation,
  atomic output publication, cache budget/eviction, concurrent safety, and
  measurement boundary are sufficient for T-0104 production
  CommandGraphExecutor reuse without making Experience authoritative?
- After human evaluation of T-0099's executable bounded workspace CLI, which
  T-0100 strong
  isolation backend should become required for release: Linux Landlock plus
  descriptor-relative resolution, a mount-namespace sandbox, an OCI/VM worker,
  or a packaged macOS App Sandbox helper? Application-level containment alone
  is not an answer for hostile-input isolation.
- ADR-0110 extends ADR-0032 to two exact static linalg fixtures: GEMM and
  GEMM+bias+ReLU. T-0186 verifies real compiler admission and owned native
  correctness, not VMFB runtime equivalence or general lowering. Which
  additional dialects, tensor signatures, import-record evolution, and
  sandboxed compiler distributions are justified before a general frontend?
- What immutable environment receipt, base-image digest, and OS resource
  limits are required before the pinned compiler adapter may process anything
  beyond repository-owned allowlisted sources?
- If BOOM simulator images later require cross-host replay rather than an
  explicit rebuild on each admitted host, should T-0124's local
  BuildKit-history receipt be replaced by a validated OCI layout/archive that
  retains the complete index-to-manifest-to-config/layer digest and size
  graph? The current receipt deliberately fails closed when its local build
  record is absent and is not portable evidence.
- Which upstream components should be integrated, wrapped, progressively
  replaced, or rejected?
- What measured threshold—performance, memory, energy, variance, security, or
  adaptability—justifies replacing a mature upstream implementation?
