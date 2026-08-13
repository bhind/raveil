# Intended Raveil architecture

Status: intended architecture; only the subset in
[`STATUS.md`](STATUS.md) is implemented
Last updated: 2026-08-08

## Four-plane adaptive Harvard model

| Plane | Contents | Write authority |
|---|---|---|
| Program | immutable semantics, ExecutionContract, RISC-V fallback | trusted build and admission |
| Graph | sealed GraphVariant, placement, route, MemoryPlan | privileged installer |
| Data | versioned objects and streams | capability-authorized producers; never executable |
| Experience | measurements, failures, lineage, policy state | restricted producers under Sonatine Microkernel |

An AI advisor writes none of these planes directly. It emits a versioned,
allow-listed OptimizationProposal.

## Trusted flow

```text
semantic program + ExecutionContract
              |
              +------------------------> trusted RISC-V/Pavane Semantic Oracle baseline
              |
        typed proposal
              |
       Miroirs Graph Compiler structural checks
       contract/capability/resource checks
       semantic or numerical verification
              |
       sealed GraphVariant + MemoryPlan
              |
       target measurement / shadow run
              |
       commit or rollback
              |
       Experience evidence + lineage
```

The trusted computing base includes Sonatine Microkernel authority, capability checks,
Program Plane contracts, the structural verifier, the semantic oracle, the
installer, and the Daphnis Execution Subsystem plane firewall. Learned models, LLMs, heuristic
mappers, external solvers, and unadmitted candidate graphs are fallible.

## Native execution contract

ADR-0034 places a thin Native Interactive Session above the existing owned
frontend. The Session stores workflow state and command history but has no
admission, semantic, measurement, or commit authority: GraphCompiler,
MiroirsStructuralValidator, PavaneSemanticOracle, GraphExecutor, and
NativeCBackend retain those responsibilities. Host terminal types do not enter
an owned graph or result schema.

ADR-0035 places a `NativeWorkspace` below the Session. One existing real host
directory is fixed at startup and appears as virtual `/`. Bounded file commands
and result publication use virtual paths, reject parent traversal, symlink
components, special files, excessive sizes, and overwrite, and reveal no host
absolute path. This is portable application-level containment only; T-0100
retains descriptor-relative and platform-enforced isolation work.

ADR-0036 adds a separate command-graph vertical slice above that workspace.
A bounded shell-subset parser emits a versioned `CommandGraphProgram` with
declared file or stream dependencies; it does not reinterpret the existing
tensor `GraphProgram`. Direct baseline and graph execution use controlled argv
for allowlisted OSS tools, validate stdout, outputs, exit status, and failure
propagation before comparison, and keep construction, execution-only, and
end-to-end timing distinct. T-0101 is ordinary host-work evaluation, not a
general shell or a substitute for T-0100 isolation.

`CommandGraphCompiler` owns parsing and strict schemas; `DirectCommandExecutor`
and `CommandGraphExecutor` share the same fixed tool registry, workspace
snapshot, environment, resource policy, and concurrency cap. `|||` denotes a
bounded join-fanout, while `|`, `&&`, and `;` retain stream, success, and
sequence edges. `CommandGraphResult` permits publication only after exact
semantic agreement. `CommandBenchmarkResult` is segregated development-smoke
evidence and cannot authorize a graph result or change EXP-0004 by itself.

ADR-0037 adds a separate T-0103 operator showcase above this execution path.
It invokes the existing compiler/registry/comparison machinery for a synthetic
independent `sort` fan-out and displays sequential plus equal-concurrency
direct controls before the DAG candidate. Its immutable-by-name cache payloads
bind node recipe/tool identity, active input hash, and payload hash; changed
nodes are again direct/Graph checked. This cache is not a
`CommandGraphExecutor` capability, does not modify command records or
publication authority, and is not Experience. The current Native host runs the
same ordinary ARM64/x86-64 instructions as other host processes; any observed
effect is software work avoidance or scheduling, not a Raveil ISA/ASIC effect.

The Native input adapter installs one readline/libedit completer. Its pure
candidate function enumerates only fixed commands, graph subcommands/options,
allowlisted tool names, and `NativeWorkspace` virtual paths. Path completion
uses the same bounded lexical directory view, omits symlinks, and never returns
host absolute paths. Completion grants no authority: dispatch reparses and
revalidates every resulting line normally.

### GNU/Linux userspace vertical slice

ADR-0025 instantiates the smallest complete control loop as owned Python
records plus a replaceable strict-C11 native adapter. `GraphProgram` and
`ExecutionContract` define the admitted graph, the compiler emits a sealed
bounded variant slate, and an analytical proposal remains advice. Baseline-first
execution, structural checks, checksum comparison against the trusted baseline,
and explicit commit/rollback remain authoritative host mechanisms.

The result is a segregated host-correctness record. It is not automatically
promoted into Experience or measurement evidence. GNU/Linux is the first
integration environment, but no Linux type appears in the owned graph contract;
the same module runs on macOS.

T-0090 adds a second explicit adapter without changing this frontend. The
Sonatine/QEMU path loads a Raveil-owned fixed request envelope into the reserved
top of the QEMU `virt` RAM contract, then accepts exactly one bounded serial
result. Sonatine translates the envelope into the existing JobDescriptor,
ObjectManifest, rings, CompletionRecord, approval, and metadata-finalization
path. Loader bytes and UART text are transports, never authority. Backend types
do not enter GraphProgram, GraphVariant, MemoryPlan, or proposal schemas.

The adapter carries no selection timing and is always labelled
`qemu-emulation-correctness`. Native and QEMU baseline checksums are compared,
but this does not establish physical RISC-V behavior or performance.

T-0092 adds a separate interactive demonstrability boundary under ADR-0033.
The persistent U-mode shell sends only a fixed scalar command plus a distinct
demo-broker capability. Kernel code derives the current task, performs real
VFS or bounded job-state transitions, independently checks the fixed GEMM
result, and emits a fixed-order `RAVEIL-SONATINE-DEMO-V1` frame. A bounded host
runner validates the exact 18-frame transcript and publishes a strict
`raveil.sonatine-demo-result/v1` record. Human console prose, Experience,
completion telemetry, and the record itself grant no authority.

T-0043 instantiates the frontend's named verification stages. Miroirs compares
the admitted artifacts with the canonical `GraphCompiler` output and exact
program, contract, candidate-set, and proposal bindings before execution.
Pavane is a separate deterministic owned reference executor: it regenerates
the fixed integer inputs and expected checksum without trusting a backend's
reference field. Pavane decides semantic equivalence only; proposal advice,
timing-based selection, Sonatine finalization, and evidence classification stay
outside the oracle.

ADR-0030 makes the Four-plane write split executable inside Sonatine. Four
non-interchangeable capability types guard immutable Program admission,
Program-bound Graph installation, Data registration/publication, and bounded
Experience observation admission. Full artifact identities stay in fixed
kernel registries; the capability object ID denotes only the authority domain.
The public plane API composes with the existing job rings and metadata-shadow
finalizer, while their raw mutation primitives remain internal trusted-core
implementation details.

ADR-0031 extends that finalizer with fixed kernel-owned object bytes. Admission
captures stable input snapshots; a consumed completion may receive only bounded
Data-authorized WRITE-range staging; Program approval freezes complete shadows;
and finalization publishes all staged bytes and exact-successor versions only
after every object and range revalidates. The contract remains pointer-free and
the atomicity claim is limited to the single-hart kernel API.

The long-term Graph Execution Subsystem direction remains a sealed explicit
graph/effect contract rather than only a conventional sequential register
instruction stream. A native job should carry:

- explicit data and control dependencies;
- explicit read, write, and external effects;
- object-bounded memory access and versions;
- resource requirements and limits;
- preferred placement, route, and memory plan;
- semantic and numerical constraints.

RFC-0001 leaves static, elastic, and variable-latency organizations open.
ADR-0039 accepts a deliberately narrower first candidate: RFC-0005 lowers one
ten-operation stencil graph to an exact six-phase logical schedule before
execution. That simulation-only candidate has no runtime token movement,
dependency-ready issue, rename, ROB, general LSU, commit frontier, or issue-mode
switching. A later timing-dynamic organization requires a new contract and IP
review; it is not implied by this first RTL.

## RISC-V and Graph Execution Subsystem

RISC-V/Sonatine is a preserved semantic/control/fallback and specialized
authority architecture for boot, exceptions, irregular code, capabilities,
object management, admission, and recovery. Under ADR-0024 it is not an MVP
prerequisite and must earn primary-path status through a bounded comparison.
It is not native Graph machine code.

The Graph Execution Subsystem is connected through owned job/object/completion
contracts. Static,
elastic dataflow, stream, and hybrid organizations remain comparison
candidates. Dynamic islands or RISC-V fallback handle pointer chasing,
interpreters, unpredictable traversal, and other graph-hostile regions.

T-0042 now supplies the first owned operation-level RTL slice. A deterministic
Python compiler emits the RFC-0005 stencil descriptor; an independent validator
recomputes its acyclic dependencies, affine READ/WRITE effects, disjoint-object
requirements, resource limits, fixed schedule, exclusions, and RV64IM fallback
declaration. Chisel binds the descriptor's configuration tag to separate input
and private-output scratchpads and executes five loads, four modular uint32
adds, and one store over 256 points. Cancellation clears output validity;
normal completion grants only a private result for independent host-oracle
checking. This is RTL functional simulation, not a product ISA, general Graph
executor, matched CPU comparison, or hardware-performance result.

ADR-0042 uses the pinned subsystem TileLink RAM inherited by Rocket and BOOM as
an intermediate functional bridge. Only the fallback's input and private output
are linked there; code and completion control remain in normal memory. This
common addressable device removes cache-backed buffer placement as one
functional confounder, but its TileLink/LSU paths are not constant-latency proof
and the Graph RTL still has different private storage. The active adapter must
therefore report the intermediate memory model as latency-unverified and refuse
resource matching.

The T-0042 latency observer is a passive diagnostic boundary below the
`ScratchpadBank` fragmenter and directly above its TLRAM request/response
ports. It keys accepted A beats and completed D beats by TileLink source ID and
exports only run-local counts and observed intervals. This placement makes
single-beat endpoint correspondence checkable, but intentionally excludes the
CPU LSU, cache, upstream buffering/arbitration, initiator identity, lifecycle
phase, and Graph storage. Observing one cycle there therefore cannot promote
the inherited TLRAM prototype to a fixed-latency common architecture.

ADR-0043 introduces the next, owned boundary below future CPU and Graph
adapters. The first `OwnedFixedLatencyScratchpad` is a single-client,
maximum-one-outstanding request/response module with explicit operation,
address, data, byte mask, initiator, lifecycle phase, error, backpressure, and
transaction accounting. It makes a response available one module-local cycle
after acceptance and holds it until consumption. The emitted RTL and functional
Verilator harness assert this local protocol only. The static Graph region is
connected, but CPU controls are not, so this module remains an unmatched
adapter target rather than the RFC-0005 common memory implementation. The static Graph
adapter now uses disjoint input and private-output bank instances; later
CPU adapters must prove equivalent ports, arbitration, buffering, and lifecycle
accounting before any resource-match promotion.

ADR-0044 defines the first CPU translation adapter as an intentionally
unmatched intermediate boundary. Dedicated Rocket and BOOM configurations
remove the inherited subsystem scratchpad and add a Raveil-owned 32-bit
TileLink manager at the same data base, but attach it to the uncached
peripheral bus. This prevents cache residency from hiding manager transactions
while the adapter contract is being debugged. A software-written phase
register labels subsequent aggregate traffic; it does not identify the actual
initiator. Successful RTL elaboration can prove topology/type compatibility
only. A separate raw TileLink harness now verifies the manager's negotiated
Get/Put, byte-mask, denial, response-hold, one-outstanding, response-metadata,
reset-phase, and bounded-counter behavior with the upstream monitor enabled.
It bypasses both CPUs, so CPU execution, semantic initiator attribution,
end-to-end ordering, resource matching, and all measurement remain separate
follow-ups. It also verifies manager-local expected/unexpected source-class
conservation and preservation of the A-accepted software phase through D
completion under backpressure.
Protocol V4 deliberately makes the classifier's negative path executable. Its
raw client has source IDs `[0,4)`, while the expected range is `[1,3)`; sources
0 and 3 therefore exercise the two boundaries and conserve unexpected
accepted/completed counts at 4/4, while expected traffic conserves at 3/3.
Re-presenting the pending source under D backpressure is rejected. The same
untagged raw client completes all seven legal data requests as structural
DCache-origin 0/0 and non-origin 7/7. These are manager-harness invariants, not
observations of either CPU or FESVR.
A separate test-only topology advertises and drives DCache-origin true at its
raw client, then removes the request field at a diplomacy adapter before the
manager. Reusing the same 30-transaction protocol driver produces origin 0/0
and non-origin 7/7, so absent downstream metadata is classified false and held
consistently from A acceptance to D completion. The topology is a transport
loss model, not a loader/debug implementation or semantic-initiator witness.

The first CPU execution path is a shared bare-metal functional smoke with thin
Rocket and BOOM entrypoints. Identical RV64 load/store and `fence iorw,iorw`
instructions access the owned PBUS manager's data and control pages, and the
same host verifier checks data, phase, and aggregate counters. Both generated
systems produce the same decoded signature for this bounded workload. An exact
graph verifier checks the DCache-MMIO range before execution: `[8224,8256)` for
Rocket and `[8288,8320)` for BOOM after fragmenter expansion, disjoint from the
`[0,8192)` serial range. The manager latches each accepted data request's
TileLink source and software-declared phase and uses them at D completion;
runtime registers separately count expected and unexpected source classes.
Both runs observed expected 8/8, unexpected 0/0, in-range final sources, and
final phases 2/2. This proves that each CPU can execute the intended mapped
path, preserve this workload's semantics, and use the generated DCache-MMIO
client class. TileLink source numbering is config/Xbar/fragmenter-dependent
and does not prove the target ELF was the semantic initiator. The adapter still
does not carry ADR-0043 owned initiator metadata, isolate the effect of OoO, or
make the peripheral topology resource-equivalent to the Graph memories.
Common-contract and matched comparison work remains separate.

The next T-0042 prerequisite is now executable as a standalone bridge. A real
post-fragmenter TileLink manager converts negotiated `Get`, `PutFull`, and
`PutPartial` A beats into an upstream-type-free owned request and converts the
owned response back to D. TileLink source/size stay in the bridge; operation,
address, data, byte mask, explicit initiator, phase, error, and backpressure
cross the owned boundary. The test target implements the same maximum-one-
outstanding request/response shape and asserts conservation and response
stability. This separates translation mechanics from the unresolved policy
that assigns trustworthy CPU/loader/debug initiator identity. The standalone
harness supplies that metadata directly, so its successful correlation is not
semantic CPU attribution and does not alter ADR-0044's unmatched deployed
manager or establish equal CPU/Graph resources.

Attribution therefore has two distinct implemented diagnostic evidence layers.
A final
manager-side TileLink source range is a generated config/Xbar/fragmenter client
class only. Repository-owned hooks now insert a one-bit request field after each
DCache and before the tile master crossbar. A pinned ephemeral Xbar patch
preserves negotiated request fields and initializes absent client fields from
their declared false defaults; it is hash-checked against exact pre/post pinned
sources. The manager latches the bit at A acceptance and uses the retained bit
only for its internal D-completion accounting. Rocket and BOOM each observe
origin 8/8 and non-origin 0/0 for the bounded workload, while the untagged raw
client and the explicit field-stripping topology each observe origin 0/0 and
non-origin 7/7. This establishes structural
DCache-boundary crossing and distinguishes the separate SimTSI/FESVR master in
these harnesses without treating final source numbering as semantic identity.
The regular CPU smoke and PT_LOAD probe provide a direct counterexample to
such promotion: their ELF hashes and semantic signatures differ, but their
final tagged DCache source is identical within each configuration (8224 on
Rocket and 8288 on BOOM). A fail-closed cross-workload verifier requires that
equality and distinctness together. This is negative evidence about the
current metadata boundary, not a replacement semantic witness.
ADR-0045 assigns the replacement candidate at the CPU lifecycle boundary. A
non-software-writable token names one candidate operation across replay attempts
and is scoped by a redirect/reset epoch; exhaustion or alias fails closed.
Rocket correlates sequence with the matching EX/MEM PC, operation, and epoch;
BOOM uses sequence/epoch as identity and ROB index plus branch mask only as
lifecycle context. The
normalized result distinguishes issue attempts, A/D transport completion, and
architectural commit. Loads require response plus retirement, stores require
retirement plus CPU-specific store authorization and actual completion, and killed, exceptional,
rolled-back, stale, duplicated, loader, FESVR, Debug, or untagged traffic cannot
be promoted. A post-A exception cannot cancel transport; a later side effect is
an explicit lifecycle violation. These are accepted design invariants. A
standalone repository-owned Chisel ledger now exercises them with synthetic
events, a single-live-token state machine, exact marker verification, and
fail-closed invalid-transition tests. It is a contract harness, not a CPU
boundary: it has no pinned Rocket input, performs no CPU execution, and cannot
mint a semantic witness for the ADR-0043 bridge. The full CPU-specific probes
remain unimplemented and the harness does not alter the unmatched memory
topology.
A first pinned Rocket diagnostic is deliberately narrower than the full
ADR-0045 ledger. It allocates on an accepted `io.dmem.req`, captures the local
DCache request tag, observes the matching load data response independently of
WB, and correlates WB by PC and operation kind. This is a bounded
request/response/WB smoke, not a durable token carried through DCache or
TileLink. It does not cover replay, kill, redirect, exception, reset epoch,
store authorization, owned-manager D completion, or semantic initiator
identity, and therefore cannot feed the common bridge or establish matched
resources.
The same pinned hook now handles one narrower redirect outcome: when the exact
owned-address request is accepted in EX while an older taken branch asserts
`take_pc_mem`, it emits an explicit killed-token event, blocks promotion, and
advances the diagnostic sequence. The bounded workload completes a load before
the probe and another after it; an explicit dependency prevents the one-entry
observer from accepting the probe while the first load remains open. Both
loads observe the same non-magic value in the exact run. The observer retains a
load until both WB and its matching response have appeared, and rejects an
overlapping candidate rather than silently reassigning the live entry. That
earlier diagnostic establishes only the observed same-cycle post-request
bookkeeping and bounded
differential readback; it does not establish multi-token support, pre-request
suppression, later-cycle cancellation, DCache `s1_kill`, TileLink A/D fate, or
general absence of a side effect.
An optional exact-address manager audit and a second pinned Rocket patch now
separate the next two boundaries. The Rocket patch retains the accepted
sequence-2 request's PC, address, and local tag for one cycle and directly
samples the Rocket-facing `s1_kill`; the exact run reports `s1_kill=1` and the
hardwired `s2_kill=0`. The manager audit independently records each matching A
acceptance and holds its source/opcode/size/phase until D completion. In the
bounded redirect log it sees the two before/after load `Get` pairs and no
wrong-path store `Put`. Manager A/D source equality is a local transport
correlation only: the Rocket token/tag is not carried across DCache,
Fragmenter, or TileLink, so these observations cannot be joined into semantic
initiator identity or a general cancellation invariant.
The CPU runner also constructs a probe ELF with one four-byte writable
`PT_LOAD` at `0x08000000`, verifies that exact program-header and symbol layout,
and invokes the simulator without `+loadmem`. In one manager lifetime the
pre-CPU snapshot sees two serial-class non-origin requests from the pinned
FESVR aligned transport, then a CPU read adds one config-specific tagged
DCache-origin request. Accepted and completed classifications are conserved
at 2/2 before and 3/3 after the CPU read. This tests one concrete PT_LOAD path;
it does not make transport request count an ELF-segment invariant.
Neither layer supplies an instruction PC or target-ELF semantic intent, nor do
the current tests exclude all loader/debug DCache activity. A dedicated
test-only configuration exports DMI to a repository-owned bounded driver and
performs one 8-bit Debug SBA write before a CPU read. Generated graphs and
manager-local A/D accounting classify the write in Debug `[8192,8224)` as
non-DCache origin and the read in the configuration-specific DCache range as
DCache origin. The DMI/SBA implementation uses the pinned Chipyard/Rocket-Chip
`WithDebugSBA`, `DMIToTL`, and system-bus machinery; register encodings follow
the RISC-V Debug interface. These are source-provenance locators and functional
client-class evidence, not legal clearance or a semantic-initiator identity.
Durable semantic assignment, remaining loader/debug negatives, and matched
resources remain later work.

Linux retains the non-authoritative transport harness implemented under
ADR-0019. ADR-0024 additionally permits the first complete product loop in
GNU/Linux userspace, provided Raveil-owned admission, semantic, evidence, and
rollback contracts remain authoritative. Host mechanisms implement those
contracts; they do not redefine them.

ADR-0020 defines the first shared JobDescriptor/CompletionRecord byte contract.
Descriptors carry bounded object/version/range/effect and resource requests;
completions carry claimed epoch, sequence, and cookie fields. T-0031 must
enforce Sonatine issuance, equality, replay, and one-shot consumption.
Structural validity is neither admission nor commit, and `EXECUTED` never
grants Experience or object-visibility authority by itself.

ADR-0021 adds the first Sonatine-owned execution-state seed: a boot-scoped
ObjectManifest table, bounded submission/completion rings, and an inflight
ledger that issues and checks epoch/sequence/cookie bindings once. It is
single-hart kernel memory, not a U-mode or Linux interface and not a Daphnis
device. Object version publication still belongs to the later commit boundary.

ADR-0022 routes consumed completion observations through a bounded UART adapter
into a segregated append-only cold telemetry journal. The QEMU adapter fixes
the evidence class to emulation and host provenance surrounds, rather than
trusts, guest fields. This journal is outside active Experience retrieval and
does not establish semantics, commit, energy, or hardware performance.

ADR-0023 adds a kernel-owned finalization ledger after completion observation.
Only an explicit full-binding approval plus optimistic revalidation of every
READ/WRITE version can publish exact-successor WRITE versions. Cancellation is
sticky and multi-output metadata publication is all-or-nothing. ADR-0031 and
T-0043 subsequently add the bounded data-byte and semantic boundaries without
changing this metadata lifecycle.

## Named components

| Formal component name | Short name | Responsibility |
|---|---|---|
| Sonatine Microkernel | Sonatine | RISC-V microkernel and execution authority |
| Daphnis Execution Subsystem | Daphnis | adaptive implementation/execution plane |
| Miroirs Graph Compiler | Miroirs | graph IR, legal transforms, structural verification |
| Pavane Semantic Oracle | Pavane | deterministic reference execution and semantic oracle |
| Ondine Object Memory Subsystem | Ondine | object residency, spill, stream, and rematerialization |
| La Valse Optimization Subsystem | La Valse | search, mapping, and proposal generation |
| Boléro Experience Runtime | Boléro | persistent runtime, retrieval, and variant selection |
| Scarbo Verification Subsystem | Scarbo | adversarial testing, fuzzing, and fault injection |

## Variant and memory lineage

A GraphVariant records its parent, transformation sequence, ProgramIdentity,
contract hash, hardware signature, resource certificate, and MemoryPlan. A
MemoryPlan selects and composes policies such as `KeepSram`,
`SpillExternal`, `Rematerialize`, and `Stream`. Evaluation includes
latency, peak bytes, external traffic, energy, tail behavior, and recomputation.

The current T-0041 userspace slice implements strict v1 owned artifacts for a
narrower host boundary. Each `GraphVariant` binds its `GraphProgram`,
`ExecutionContract`, transformation list, and bounded host-memory
`MemoryPlan`. Each `OptimizationProposal` binds those identities and the full
ordered candidate set. Exact-key validation and lineage checks run before any
backend execution. This seed does not yet implement hardware signatures,
ResourceCertificate, general placement policies, or enforcement of the
descriptive memory bound.

## Adaptive Council

Optimization uses multiple policy layers rather than replacing a cheap
algorithm with an expensive one. Heuristics act immediately on easy cases;
bandit/Bayesian, learned, and LLM-level advisers are consulted when expected
value justifies their cost; periodic reviewers can challenge stale local
optima.

This is not majority voting. Separate decisions govern:

- what executes in production now;
- what dissenting candidate is worth shadow-testing;
- what proposer deserves future compute budget.

The council remains Proposed; see
[`ADR-0008`](decisions/ADR-0008-staged-adaptive-council.md).

## Language and upstream boundaries

Rust `no_std` owns selected trusted invariants; C++20 owns host/runtime/compiler
integration; Python owns research and analysis; Chisel owns generated RTL; a
stable, versioned C ABI connects Rust and C++.

IREE/MLIR, TVM, CGRA projects, OR-Tools, QEMU, Verilator, Chipyard, and OpenROAD
may be used behind adapters. Raveil owns ProgramIdentity, ExecutionContract,
GraphVariant, ObjectManifest, MemoryPlan, OptimizationProposal,
ResourceCertificate, ExperienceRecord, JobDescriptor, and CompletionRecord.
Upstream types do not become Raveil's public contract.

The first executable IREE boundary is deliberately narrower: a pinned compiler
validates one digest-bound, repository-authored MLIR fixture and the adapter
emits only the canonical `GraphProgram` and `raveil.graph-import/v1`
provenance. VMFB bytes, MLIR objects, compiler paths, and diagnostics remain
private adapter state. Compiler acceptance cannot bypass Miroirs, Pavane,
baseline-first execution, or explicit commit/rollback.

## Measurement and research-data boundary

Raveil owns versioned BenchmarkManifest, EnvironmentSignature,
MeasurementRecord, and PolicyOutcome schemas. ToyDaphnis, native C, pinned TVM,
and future QEMU telemetry remain adapters behind
`MeasurementBackend.measure(context, candidate)`. The baseline-first,
semantic-check, target-measurement, and rollback boundaries apply before an
Experience proposal can become evidence.

Ignored immutable research bundles preserve raw measurements locally and on a
verified Google Drive durability copy. Neither Drive nor an upstream tuning
database is Program/Graph/Data/Experience authority or an online Experience
retrieval service. See ADR-0009 and RFC-0002.
