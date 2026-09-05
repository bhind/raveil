# Intended Raveil architecture

Status: intended architecture; only the subset in
[`STATUS.md`](STATUS.md) is implemented
Last updated: 2026-09-05

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

### Garden read-only projection

T-0117/S01 adds `raveil.garden-snapshot/v1` as a bounded host presentation
envelope. Garden reconstructs the existing owned `GraphProgram` and accepts a
snapshot only when its full `GraphVariant` list exactly equals a fresh
`GraphCompiler` result. The terminal view derives topology and dependencies
from that accepted state and displays its explicit evidence class, non-claim
status, and module-CLI demo commands.

Garden is an observe-only adapter. It imports no execution backend and has no
authority to run a graph, mutate state, approve or rank a candidate, publish a
result, promote evidence, close a task, or change a gate. Its deterministic
line rendering and bounded navigation avoid a terminal-library dependency;
this is a host-functional Playable boundary, not T-0093's directory projection
and not simulation, FPGA, ASIC, silicon, or performance evidence.

T-0120 changes only Garden's presentation layout. The renderer accepts an
explicit bounded width rather than reading terminal state. Widths of at least
120 columns compose three ASCII panes for graph navigation, selected-node
inspection, and variants/evidence; narrower admitted widths stack the same
panes. Header and command/status regions stay full-width, and critical
authority and evidence text wraps instead of disappearing. The snapshot
schema, canonical compiler check, navigation state, and observe-only authority
remain unchanged.

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

ADR-0085 adds a project workspace above these existing paths. The project
layer owns no executor or semantic authority: it stores versioned editable
recipes and inputs, invokes the Command comparison or guarded GEMM path, and
places each exact recipe/input snapshot, compiled Graph, output and result in
a fresh run directory. Read-back verifies a local artifact manifest and record
digest. This detects later mutation for ordinary development use but is not a
signed audit store or OS isolation boundary.

ADR-0086 connects `graph-device` recipes to `rtl-sim` through the existing
dynamic request compiler, offline Verilator runner and independent verifier.
An editable descriptor under project inputs is captured once and bound to the
input manifest, compiled program, execution receipt and retained output. A
post-execution input-tree check rejects snapshot drift. The input remains
deterministically generated from a uint32 seed. The full 256-word output
window is retained alongside an active-row text view; run diff exposes program,
simulator and RTL-manifest identities. Raw transport artifacts stay under the
repository's dynamic evidence directory. No project path selects executable
code, no hardware semantics change, and no persistent simulator cache is added.

The repository POSIX launcher supplies the `raveil` command outside the
checkout by prepending the checkout to Python's module path. Private-by-default
project/run directories use mode `0700` and artifacts use `0600`; no-follow
descriptor mode changes avoid mutating a replaced external path. These modes
reduce accidental local disclosure but do not promote the workspace to hostile
multi-user containment.

The project layer also exposes the existing bounded Sonatine/QEMU GEMM adapter
and an explicit QEMU console attachment. Command recipes never enter Sonatine;
only GEMM dimensions 1 through 8 use its existing request envelope. Console
bytes are interactive transport and carry no Graph, Program, Data, Experience,
approval or publication authority. macOS and Linux share the CLI grammar, but
their allowlisted tool identities may differ.

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

ADR-0049 classifies the current Chisel implementation more narrowly still: its
source fixes the stencil states, address offsets, and iteration control, while
the descriptor hash is only a binding tag. It is a hardwired specialized
accelerator reference, not a configurable CGRA and not a general Graph
executor. A successor with loadable schedules, configurable functional units
or routes, or token readiness belongs to the established VLIW/CGRA/dataflow
comparison class and must pass the T-0044 non-reinvention gate. Strong results
from the fixed FSM cannot by themselves authorize that successor.

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

The execution substrate is replaceable. An ordinary CPU, reviewed CGRA/VLIW or
NPU, FPGA experiment, and later ASIC may implement the same bounded contract,
but no backend configuration or completion grants authority. Sonatine retains
admission, capability, object/version, cancellation, publication, rollback,
fallback, and evidence boundaries. This hardware-independent contract lifetime
is the architectural thin waist; owning a novel processing-element array is not
a Raveil requirement.

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

T-0122 wraps that exact hardwired region in the first task-neutral simulated
device vertical slice. `raveil.graph-device-abi/v1` defines a fixed-width,
little-endian, pointer-free word interface with immutable descriptor,
configuration, and implementation identities; bounded input and private-output
windows; start, cancel, reset, status, and checksum registers; one outstanding
request; and finite polling. The host compiler emits the canonical artifact
and inputs, a transport-neutral C++ `DeviceTransport` owns staging and lifecycle
ordering, and only the outer adapter knows Verilator types. Pavane independently
recomputes and checks every output word before the append-once receipt is
accepted. This makes the simulation runnable through one operator command, but
does not install a new schedule, publish Data, define AXI/UIO, measure
performance, or turn the hardwired region into general Daphnis.

T-0123/S01 adds an observation boundary outside that owned ABI. A deterministic
compiler derives an immutable schedule and internal scratchpad transaction
template from the same validated descriptor. Four Chisel outputs expose only
accepted `requestFire` events to the Verilator adapter; they are absent from the
device register contract and grant no execution or publication authority. A
strict finalizer compares two complete traces and one cancelled strict prefix,
checks store data against Pavane, and binds the schedule to the complete T-0122
artifact/ABI/source/input/oracle/output/simulator/environment receipt. The
executor still follows its hardwired state machine and does not consume or
install the generated schedule. Affine configuration and multi-DAG execution
remain later boundaries.

ADR-0063 separates the next configuration-installation boundary from that
execution ABI. A bounded installer owns fixed-width clear, sequential payload
write, and atomic commit only while the executor and owned memory are idle. The
executor consumes installed rows, columns, and input/output strides, while the
implementation tag remains separate from the live installed digest. The 324-
word input and 256-word private output windows do not move. Reset restores the
baseline profile and clears the simulation scratchpad, making inactive compact
output words zero before the complete fixed window becomes valid. This is a
simulation-functional ownership rule, not a physical-memory implementation or
performance claim. S02 now verifies this boundary for baseline 16-by-16 and
compact 8-by-8 profiles on one elaborated RTL image. The execution ABI retains
its fixed configuration-identity words; the separate installation ABI alone
reports the installed digest. The executor is still the same five-point
stencil state machine, not a general-DAG engine.

ADR-0064 adds a third owned boundary without changing either prior ABI. The
program-installation ABI atomically installs one bounded instruction sequence;
the affine ABI continues to own only rows, columns, strides, and active output
count. A generic sequential core consumes both installed views and decodes
only `LOAD_U32`, `ADD_U32`, and final `STORE_U32`. External Graph JSON is
lowered by a task-neutral host compiler, while an independent direct-Graph
oracle and a separate compiled-program fallback provide two validation paths.
Execution is authorized only when both installers are installed and fault-free.
This intended S03 boundary remains RTL-simulation-only until executable
evidence passes.

T-0128/S01 adds only the operator admission envelope above those accepted
boundaries. The top-level CLI resolves one exact repository-relative member of
the frozen three-Graph catalogue, rejects symbolic links and identity drift,
recompiles it through the existing bounded compiler, and emits descriptor,
program, and seed identities with `execution=not-started`. The envelope is not
a device artifact, execution authorization, receipt, Data publication, or
Experience input. No transport adapter consumes it in S01; a later child must
be separately promoted before mapping it onto the existing execution, affine,
and program-install ABIs.

T-0128/S02 supplies that mapping without changing any of the three ABIs or the
Chisel RTL. A lower-level selected runner revalidates the S01 envelope, prepares
the existing frozen three-program header plus the selected seed, and passes only
the admitted Graph identity and seed to a separate Verilator runtime entry. The
runtime resolves the generated program and affine metadata, exercises the same
eight installer rejection cases, then installs and executes only the selected
program. A host finalizer independently regenerates the generated headers and
oracles and rejects any log, trace, output, source, simulator, or environment
substitution before writing the private receipt. The host repository is mounted
read-only and exact source inputs are copied into a container-private build
directory; only the private evidence mount is writable. The receipt binds the
complete build-source manifest, named two-pass RTL manifests, and a retained
simulator binary through recomputed hashes and is created exclusively. This
receipt also binds a strict sorted manifest of the Scala dependency cache,
which is mounted read-only during the selected build; symlinks and special
entries fail before build instead of remaining outside that manifest. This remains a local
Docker/Verilator adapter around pointer-free word-addressed
boundaries; the S03 top-level CLI must stay a thin presentation and may not
introduce a Verilator-specific ABI or generalize the frozen Graph catalogue.

T-0128/S03 implements that thin presentation as a host-side CLI adapter only.
It invokes the unchanged selected shell runner, captures incidental build
diagnostics, accepts exactly one strict private evidence marker, confines the
resolved run directory to the repository artifact root, and calls the same S02
receipt reconstruction in read-only mode. The operator sees only the requested
Graph and seed, three-way RTL/oracle/fallback agreement, the eight named
installer faults, rejected publication zero, and explicit evidence/non-claim
labels. This presentation is not a transport, device ABI, execution authority,
public Data path, or Experience input.

T-0132/S01 adds the first concrete control transport without changing those
three owned ABIs. ADR-0067 places execution, affine installation, and program
installation at relative byte ranges `[0x0000,0x2000)`, `[0x2000,0x3000)`, and
`[0x3000,0x4000)` in one 32-bit little-endian AXI4-Lite aperture. Its absolute
platform base is intentionally unassigned. The wrapper around the unchanged
`StaticStencilRegion` captures AW and W independently but owns only one total
read-or-write transaction. It preserves R/B responses under backpressure,
classifies decoded invalid accesses separately from unmapped addresses, and
uses external ARESETn for bus-plus-core reset. Execution `CONTROL.reset`
retains its OKAY B response through handshake and then applies a bounded core-
only reset barrier before admitting another request.

This S01 adapter exposes only identity, version, status, counts, and execution
reset. Data windows, install payloads, digests, start/cancel, DMA, IRQ, and an
operator runtime remain outside the adapter. Chisel/Verilator evidence proves
only the repository-owned RTL control behavior; the relative aperture is not
an AXI certification, physical-address assignment, Linux driver, FPGA
integration, or performance result.

T-0132/S02 extends that same wrapper only across the two already-owned
installation namespaces. Full-word AXI writes may request affine/program
clear, sequential payload, and commit operations; installed digest, status,
and count become readable. Each admitted mutation remains queued until its
held OKAY write response is accepted, then applies exactly one core command
behind a bounded admission barrier. The same aligned, in-aperture, full-word,
decoded predicate that selects OKAY also authorizes the queued side effect;
DECERR and SLVERR transactions cannot mutate a rounded internal word address.
Execution data, start, cancel, and output remain fail-closed for a later slice.
This is still an unbased, single-outstanding RTL-simulation transport, not
Linux or FPGA integration.

T-0132/S03 adds only the execution data plane reserved by ADR-0067. Execution
word decoding uses address bits `[12:2]` because the 8 KiB namespace includes
the output window beginning at byte `0x1000`; configuration and program remain
independent 4 KiB namespaces decoded with `[11:2]`. Ordered input words are
queued behind accepted B, then hold the existing input-stage request and
response handshakes while all AXI admission is blocked. Start and cancel are
post-B one-cycle core pulses with a following admission barrier. Completion
and cancellation are sticky at the wrapper because the nested core reports
them as pulses. An accepted cancel revokes output authority even if the core
finishes while B is backpressured. Output reads enter the existing validation
request/response path and only then create a retained AXI R response; premature
or cancelled output remains SLVERR. This slice exposes checksum only with
authorized output and deliberately leaves execution descriptor and
implementation digest registers unsupported. It is one factory bounded Graph
in RTL simulation, not a general accelerator or platform runtime. Its private
evidence binds the complete external AXI transaction transcript; the harness
holds one authorized output R response and holds an admitted cancel B long
enough for core completion, then verifies that post-B cancel still suppresses
publication.

T-0132/S04 adds a host-side AXI simulation adapter without changing the S03
wrapper, core, or any owned ABI. One C++ bridge implements the existing
transport-neutral execution, affine-install, and program-install interfaces by
issuing only external AXI4-Lite reads and writes into the three relative
windows. The unchanged DAG runtime then executes the frozen three-Graph
catalogue, including four completed invocations, one cancellation, one
factory-default restart through the runtime's execution reset, and the eight installer rejection cases, against one
emitted RTL image. A private finalizer binds the complete AXI transcript,
double RTL elaboration, simulator, toolchain, source set, independent oracles,
and output hashes in an exclusively created local receipt. The writer refuses
replacement, but the same filesystem owner can delete and recreate the private
bundle; this is not an immutable external seal.

The explicit `graph-device run --transport axi4lite-sim` option preserves the
existing Graph path and seed as a fail-closed admission request, but S04 runs
the complete fixed catalogue rather than claiming that the requested pair is a
single selected AXI invocation. The CLI says so directly. A later slice must
separately connect per-request selection if product operation requires that
semantics. S04 remains RTL-simulation-functional evidence with performance not
measured; it is not Linux/UIO, a driver, an absolute address assignment,
DMA/IRQ, FPGA/KV260, general Graph execution, or production security.

T-0132/S05 makes per-request semantics explicit without changing the hardware
boundary. The default `selected-rtl` path remains the pre-AXI direct Verilator
adapter; `axi4lite-catalogue-sim` names S04's fixed full-catalogue regression;
and `axi4lite-sim` now passes the admitted repository descriptor identity and
uint32 seed to unchanged `run_selected_dag` through a second thin instance of
the same three-interface AXI bridge. Graph choice remains in the host runtime,
not the bridge or RTL. The request finalizer recomputes admission, deterministic
input, compiled program, affine payload, and direct oracle. It requires the
fixed 507-record malformed/busy prefix plus an exact request-dependent suffix:
reset, affine/program installation, 324 staged input words, start, terminal
status sequence, and 256 private output reads. All records remain external
AXI4-Lite transactions.

The local receipt binds that semantic trace, request, private output, oracle,
sources, generated inputs, owned ABIs, double RTL elaboration, simulator,
toolchain, and fixed offline environment. As in S04, exclusive creation is not
an immutable seal against the same filesystem owner. This remains a three-
descriptor, three-opcode, RTL-simulation-functional path; it does not establish
arbitrary Graph support, Linux/UIO or a driver, absolute mapping, FPGA/KV260,
DMA/IRQ, performance, resources, production security, or silicon behavior.

T-0132/S06 extracts the address calculation from the Verilator bridge into one
transport adapter over a minimal 32-bit `RegisterIo`. It alone maps execution,
affine-install, and program-install word offsets into the ADR-0067 namespace
bases and rejects overflow or namespace crossing before I/O. The Verilator
backend still emits the same external AXI transactions. A second backend opens
only an explicit `/dev/uioN`, binds its `fstat` device identity to sysfs, checks
map 0 is exactly 16 KiB, and exposes aligned volatile words at relative offset
zero. Neither backend contains Graph-selection logic.

The Linux runner is compiled for one prepared request. A generated header
freezes the exact request record, canonical JSON, deterministic input bytes,
catalogue Graph, and seed; every corresponding file must match byte-for-byte
before the UIO device is opened. The unchanged `run_selected_dag` then owns
installation and execution. Output creation is exclusive and no-follow, so an
existing file or symlink cannot be truncated. This is a host transport build,
not a dynamic admission service, driver authority, or hardware result. No
absolute base, `/dev/mem`, DMA/IRQ, cache policy, device tree, bitstream, FPGA,
or performance boundary is introduced. The UIO executable captures rather
than forwards the shared runtime's simulation summary and emits only
`linux-uio-transport-unverified`, `graph_output=unpromoted`, and explicit
not-verified RTL/hardware labels.

Before an operator attempts that transport on the tentative KV260 target, the
separate `graph-device kv260-preflight` command may observe only the explicit
UIO path with `lstat` and fixed device-tree, UIO-map and FPGA-manager
properties. It requires Linux aarch64, a KV260 model, exact character-device
and sysfs identity, and an aligned 16 KiB map 0, then reports that the device
was not opened and MMIO was not issued. This observation is not retained as a
capability: the UIO backend still revalidates the opened object under ADR-0071
to close the time-of-check/time-of-use boundary. The preflight has no load,
deployment, discovery, execution, evidence-promotion or measurement authority.

T-0132/S07 places a deterministic RTL-export boundary after the same unbased
AXI4-Lite top and before every board-specific wrapper. It elaborates the exact
Chisel source closure twice in one immutable offline environment and admits a
bundle only when the two SystemVerilog manifests are byte-identical. The
bundle contains the `.sv` closure, relative-aperture header, ABI identities,
toolchain identity, source-bound receipt, and recursive manifest. It contains
no absolute address, clock/pin constraint, device tree, bitstream container,
vendor project, or UIO success evidence. Thus a future KV260 adapter may
consume a fixed RTL handoff without allowing Vivado or a board shell to become
Graph, admission, execution, or evidence authority.

T-0132/S08 removes the Linux runner's build-time request specialization without
making the hardware or Graph language more general. A transport-independent
host reader accepts only the fixed 20-byte request envelope, resolves its
catalogue index through the compiled three-Graph generated header, recomputes
the seed-derived 324-word input, and validates both selected input copies plus
the runtime's fixed seed-1 negative-matrix input before any UIO open. The
returned Graph ID and seed enter the unchanged `run_selected_dag`.
`request.json` stays audit metadata rather than executable authority, so the
runner does not acquire a JSON parser, descriptor loader, program compiler, or
arbitrary-Graph path. RTL, ABIs, the relative aperture, and the checked UIO
transport remain below the same boundaries. The Linux build also rejects a
generated DAG header that is not byte-identical to the current canonical
descriptor-derived header.

T-0132/S09 applies that same reader to the AXI4-Lite Verilator bridge. The
bridge accepts only a request root and must finish admission before opening its
transcript or constructing the simulated device; Graph ID and seed are no
longer independent process authority. The ordinary one-request CLI remains,
while a bounded runtime demo emits the unchanged RTL twice, compiles one
simulator once, and invokes the byte-identical executable for two distinct
request roots. Each root is still finalized against its own request, complete
AXI trace, private output, and independent oracle. A corrupted third root must
fail without an AXI transcript. This is a single-build simulation proof, not a
persistent cache, service, production request bundle, or hardware result.

T-0132/S10 exposes that bounded proof as `graph-device run-pair`. The CLI
requires exactly two ordered Graph/seed pairs and performs the existing frozen-
catalogue admission for both before starting the lower runner. On return it
confines the session marker to the expected artifact root, revalidates each
append-once receipt against the corresponding admitted pair, requires both to
bind the marker-named simulator SHA-256, and independently checks that the
deliberately rejected root contains no AXI transcript. The shell marker is
therefore routing information, not result authority. The interface remains a
two-request, one-build simulation command rather than a batch scheduler,
persistent runtime, or hardware service.

T-0140 adds a sibling simulation-only path rather than weakening that
catalogue boundary. A fixed pointer-free dynamic host request carries one
accepted affine-profile payload, one existing 32-word program-install payload
and a uint32 seed. Its reader validates the complete bounded program and input
before an AXI transcript or model exists. The same transport-neutral runtime
then installs those unchanged payloads through the existing configuration and
program namespaces, stages input and executes through the existing execution
namespace. One pair invocation must build one generic simulator and invoke
that exact executable for both a catalogue and a non-catalogue program.

The host envelope is not an RTL or Linux UIO ABI. Descriptor compilation and
independent oracles remain above it; the Chisel installer repeats semantic
validation below it. This demonstrates runtime configurability only inside the
accepted selectors, opcodes, instruction/register capacities and two affine
profiles. It is neither dynamic scheduling nor arbitrary Graph support.

T-0141 adds a one-request presentation over that same dynamic host boundary.
The public `dynamic-run` command requires one non-catalogue descriptor; the
existing pair command keeps its catalogue then non-catalogue ordering. Both
commands prepare every request before starting the lower runner, and the same
two shell runners accept only the exact `request-1` or ordered
`request-1`/`request-2` layouts. They still generate and compile one simulator
per command and invoke it once per request. The single receipt retains the same
descriptor/program/request/source/ABI/RTL/toolchain/simulator/trace/oracle/
fallback/output identity closure. `polls=` remains a host termination
diagnostic, not an architectural cycle counter or performance observation.

T-0142 inserts a sealed host admission object above that unchanged dynamic
envelope. The creator reads one repository-relative descriptor and the bounded
compiler/source set through no-follow directory descriptors, compiles from the
retained descriptor bytes, and exclusively publishes an exact inventory whose
manifest digest is both directory name and final seal marker. Verification
rechecks source, manifest, program, affine, input and request semantics and
returns retained bytes rather than pathname authority. Simulator replay
materializes only those bytes into a new private request root; it never parses
the sealed descriptor and writes all output/evidence outside the sealed tree.
The UIO dry-run is a pure Host Functional conversion derived from the existing
aperture contract. It exposes relative namespace and payload identities but
contains no device opener, mapper, MMIO primitive or promotion authority.

T-0143 extends this bounded vertical path with exactly one unsigned
`MAX_U32` register operation. The opcode reuses the ADD instruction's two
source and one destination fields and adds no selector, constant, predicate,
memory operation, scheduling state or variable latency. A version-2 program
payload, dynamic request and sealed envelope make the changed semantic
alphabet explicit. Version-1 programs and newly generated v1 requests/seals
retain their bytes and accepted behavior; cross-version and unknown-opcode
pairs fail at host admission and are checked again by the installer. The
program-install, affine-install and execution transport ABIs remain v1 with
the same relative aperture. This is a bounded nonlinear stencil path, not a
general Graph machine or CGRA/VLIW claim.

T-0144 adds a second Garden input schema for explaining this bounded dynamic
path. The Graph-device compiler emits a deterministic lowering witness beside
the program: descriptor dependencies and fan-out, exact encoded words, value
register assignments, and program-order definition/last-use/release positions.
It validates the witness against its program words and SHA-256. Garden admits
only a bounded self-contained explanation that carries this witness, affine
configuration, retained execution identities, three-way output agreement,
evidence labels and non-claims. The view validates and projects the witness; it
never invokes or reimplements the compiler/allocator and never rereads a live
descriptor, sealed request, simulator session or receipt.

T-0145 connects the sealed host-admission boundary to a Linux UIO-shaped
no-device adapter. The ADR-0079 verifier remains the only consumer of a sealed
bundle and projects its retained request, inputs, oracle, generated headers and
canonical seal binding into a new private directory. The C++ adapter accepts
that `VERIFIED_REQUEST_ROOT` plus an injected `RegisterIo&`; it contains no UIO
backend, device path, opener, mapping or MMIO primitive. A test-only injected
callback and fake register transport prove zero calls on invalid sealed input
and the ordered install, stage, start, poll, read and oracle-equality path on
valid input. The ARM64 adapter object is compiled but not connected to a real
backend. This is Host Functional evidence, not device, FPGA or performance
evidence.

T-0148 adds a versioned address-generalization path without adding another
device ABI. Descriptor schema v2 lowers each `LOAD_U32` address object into
signed five-bit row and column deltas in program/request version 3. Admission
currently accepts only `[-1,1]` in each dimension, so every request remains
inside the existing one-cell input halo. Program versions 1 and 2 bypass these
fields and retain their fixed center/north/south/west/east semantics. The
program installer exposes the admitted version to the sequential executor;
the core chooses versioned address decoding before issuing the same single
outstanding owned-memory request. No graph identity appears in RTL.

The first v3 fixture fills the 16-instruction program exactly with eight
non-center loads, seven unsigned maxima and one store. A nine-input binary
reduction is structurally outside the current capacity. Python walks the
descriptor directly, the C++ fallback independently validates and interprets
the program words, and RTL repeats fail-closed admission before execution. All
three agree on exact private-output bytes in RTL simulation. This adds neither
runtime scheduling nor a table/CGRA fabric and does not establish performance
or physical behavior.

The dynamic explanation loader has a separate component-wise no-follow,
regular-file, bounded-read admission path. It rejects path escape, symlinks,
special files, schema or identity inconsistency and observed replacement before
rendering. This necessary fixture read does not add executor, subprocess, UIO,
device, approval, mutation or promotion authority. T-0144 is Host Functional
presentation evidence only; any displayed T-0143 RTL Simulation Functional
hash is a retained reference. Program-order positions are not cycles or time,
and `polls=` remains solely a termination diagnostic.

The post-EXP-0010 T-0044/S08 top is a separate integration prerequisite around
that fixed executor. `RaveilStaticStencilCore` contains the Graph state machine;
`RaveilStaticStencilTLClient` translates its bounded word requests onto the
shared TileLink fabric. The generated system retains one Rocket tile and its
cache, one fixture provider, and one owned TileLink memory. A runtime selector
admits either Graph or Rocket activity while the inactive candidate must remain
quiescent. The Graph result remains private until its validation path completes.
The matched Rocket-only top shares the external port, generator/toolchain,
Rocket module, memory-macro, and clock-root contracts and exists only as the
future integrated physical denominator. This structural composition does not
make the fixed executor configurable and does not establish physical or
performance advantage.

T-0044/S15 adds a candidate-independent source boundary for exploring one
possible common standard-cell-memory realization without adopting it as the
physical denominator. Seven synthesizable SystemVerilog modules reproduce the
canonical macro type signatures and bounded functional semantics. A
machine-readable validator derives the eleven-instance, 4,631,296-bit ledger;
an offline Verilator harness checks module behavior, and fresh per-type Yosys
processes stop at collected memories before mapping. Functional execution uses
ADR-0062's verified tagless simulator receipt. This boundary deliberately does
not splice the modules into either exported candidate hierarchy, map storage to
standard cells, establish macro equivalence under excluded collisions, or
authorize physical collection. Those are later pre-data closure and fairness
boundaries.

T-0044/S16 uses that source to elaborate both real S08 candidate exports under
one offline hierarchy preflight. It does not generate candidate-specific
wrappers: the source is loaded first, each export supplies its existing
hierarchy, and the checker requires all eleven macro instances to expose the
exact named-port pass-through set, including clock and mask pins. A canonical
RTLIL module identity removes only fixed candidate mount prefixes and Yosys
process-local auto identifiers; it does not equalize Graph activity or remove
Graph logic. The comparison separately preserves the identical Rocket module,
common memory paths, external ports, and allowed clock roots while permitting
the integrated candidate's additional Graph endpoints. The closure contract
binds the hierarchy comparison, source preflight, functional simulation,
runtime receipt, and every raw/derived size/hash manifest. Completed evidence
trees are read-only and independently revalidated. This remains a pre-mapping
structural and RTL-functional boundary: `$mem_v2` cells are expected here.
Only a future identical `memory_map`, `dfflibmap`, and `abc` stage may invoke
the mapped-netlist guard that rejects remaining `$mem*` cells and blackboxes
before P&R.

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
Verilator harness assert this local protocol only. Under ADR-0046 the static
Graph region now uses one physical 1024-word bank with two logical regions:
input `[0,324)` and private output `[324,580)`. Words `[580,1024)` are
physically present but invalid. The controlled Rocket and BOOM configurations
use the same executable owned resource tuple at their manager boundary. The
implementations are separate RTL modules, not shared storage; equality is
admitted only when all exact tuple fields and the canonical resource hash
match.

The minimal controlled path is:

```text
Rocket core -> DCache -> origin tagger -> TL translation --+
                                                          +-> RaveilOwnedTLMemory
BOOM core   -> DCache -> origin tagger -> TL translation --+   (one owned ingress)

StaticStencilRegion -> OwnedFixedLatencyScratchpad             (one owned ingress)
```

Both owned ingresses expose four-byte operations over 32-bit data plus four
byte-mask bits, one request port, one response port, at most one outstanding transaction, no request
buffer, one held-response slot, read and byte-mask write operations, no arbitration inside the
owned-contract ingress, and a response available one module-local cycle after
acceptance and stable until consumed. TileLink transfer-size negotiation is
adapter-specific; the controlled CPU manager rejects non-four-byte data
operations, and the compared owned resource is the normalized 32-bit word read
or byte-mask write below that translation. DCache,
TileLink crossbar, fragmenter, and width translation remain adapter-specific
and outside the compared owned resource. The structural origin bit and the
six-phase state are bounded controlled-run membership classifiers only; they
do not establish semantic initiator identity.

For the CPU records, the execution window opens only after the 324th staging
write response drains and closes on the response for the exact 800-read,
256-write optimized-ELF traffic ledger. Every accepted request in that window
must be an expected DCache-origin four-byte request in the frozen input/output
regions; unsupported, denied, control, loader, FESVR, Debug, setup, recovery,
or unknown traffic fails the run before aggregation. Validation then starts at
private-output word 324 and admits exactly 256 sequential four-byte reads. It
does not use the request origin bit or TileLink source as authority: the pinned
FESVR signature dump can change structural origin between fragments. Graph
uses the same after-staging-response and after-final-execution-response
quiescence convention. Only the three-record aggregate may promote resource
equality and functional comparison eligibility.

ADR-0047 adds a controlled-measurement fixture before any repeated campaign.
A common deterministic provider, not Rocket, BOOM, or Graph execution,
generates each fresh input and issues 324 ascending writes through a
phase-exclusive mux at the existing single owned ingress. The provider and
candidate cannot overlap; the final staging response is the sole candidate
release edge. This adds neither a second memory port nor a candidate-specific
DMA, buffer, bank, or arbitration policy. The provider formula, mux,
exclusivity, counters, and release rule are part of the common resource and
contract identities. This fixture is not yet implemented and is not a product
data path or general semantic-initiator mechanism.

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
an explicit lifecycle violation. These remain accepted invariants for any
later general semantic-attribution claim. ADR-0046 changes their delivery
order: the first T-0042/T-0044 controlled-run comparison may bracket a
quiescent frozen workload, reject any unaccounted traffic, and leave
per-operation initiator identity unknown. It must still prove equal owned
ports, buffering, request capacity, arbitration, width, response rules,
complete lifecycle accounting, and semantic output. General token lifecycle
coverage is T-0106 and is not a prerequisite for connecting the controlled CPU
paths to the ADR-0043 resource boundary. A standalone repository-owned Chisel
ledger now exercises the general invariants with synthetic
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
A separate pinned Rocket exception hook retains one accepted misaligned-load
request's PC and DCache-local tag until WB. The exact workload checks trap
cause, fault address, exception PC, single trap recovery, and equal aligned
loads before and after the fault; the hook requires WB misaligned-load cause,
the DCache `ma.ld` indication, and `take_pc_wb` before recording
`promotion=blocked`. This closes one Rocket-local post-request exception
transition only. The misaligned request is not correlated to a TileLink A beat,
the token is not transported through DCache, and no post-A rollback or general
side-effect invariant follows.
A first pinned BOOM lifecycle hook is similarly narrower than the full
ADR-0045 ledger. It allocates a repository sequence when the exact
`0x08000100` load request fires at the LSU DCache interface, retains the
request PC plus ROB/LDQ context, matches the returned DCache response, and
requires `commit.valids` together with `commit.arch_valids` before promotion.
Sequence is the local identity; ROB index, LDQ index, branch mask, and lane are
context only. The positive diagnostic is single-live and fail-closed on
overlap, sequence exhaustion, response-context mismatch, duplicate response,
commit-before-response, and duplicate commit. It does not carry its sequence
through DCache or TileLink, authorize a store, identify a semantic ELF
initiator, or establish general BOOM replay/kill/exception/reset behavior.
A separate BOOM negative allocates its local sequence at the exact
misaligned-load addrgen candidate. It retains PC plus ROB/LDQ context through
the per-lane LSU exception, one matching DCache request accepted after that
exception, and the later global ROB rollback state while asserting that no
matching response or commit is valid. The faulting ROB entry is removed outside
the reported rollback rows in the exact trace, so `matching_rbk=0` is required.
This is an exact exception-before-request ordering diagnostic only: because the
exception precedes request acceptance, it neither establishes post-request
exception/cancellation nor transports the sequence into DCache, TileLink, or
the owned manager.
A separate BOOM store diagnostic allocates its local sequence at architectural
ROB retirement while the matching STQ entry is authorized. It retains ROB/STQ,
PC, address, branch-mask, and lane context through the accepted DCache store
request, store response/succeeded transition, and STQ clear. The optional
owned-manager audit independently records the exact-address Put A/D pair and a
readback Get A/D pair. These are deliberately separate ledgers: no repository
sequence crosses DCache or TileLink, and temporal/address agreement does not
join the manager completion to the CPU-local token or prove complete store
attribution.
A separate BOOM post-request redirect diagnostic is deliberately CPU-local and
cacheable. BOOM does not issue the owned PBUS region's uncached wrong-path load
before the older branch resolves because that load waits for ROB-head wakeup,
so the diagnostic instead pins one wrong-path `lwu` at PC `0x80000048` and DRAM
scratch address `0x80010000`. It allocates a repository sequence only when that
exact LSU DCache request is accepted, retains it through the matching response,
and then requires `IsKilledByBranch` with no matching commit. Exact PC, ROB/LDQ
indices, branch mask, and lane qualify this bounded trace but remain context,
not identity. The owned manager is not exercised, no sequence crosses DCache or
TileLink, and the trace establishes neither post-A cancellation nor memory
side-effect absence, semantic initiator identity, or general rollback.
A separate BOOM store-token diagnostic extends only the already-authorized
store path. The LSU mints `{valid, epoch, sequence}` while ROB retirement and
the matching STQ commit authorize the exact request; DCache pipeline and I/O
MSHR fields preserve it into negotiated TileLink A metadata. Cached refill and
prefetch producers explicitly emit invalid/zero metadata. At the owned target,
the exact Put A acceptance latches the token into the target's existing
single-outstanding response state, so the subsequent D record is correlated
without treating TileLink source as identity. Missing or zero fields classify
invalid, and no result feeds the ADR-0043 bridge or `InitiatorCpu`. The current
epoch is the fixed diagnostic value 1, so this mechanism is not yet the
reset/redirect-aware epoch policy of ADR-0045. ROB/STQ/PC/address/branch and TL
source remain local validation or transport context only.
A companion negative configuration retains only DCache request-field
advertisement and the Xbar's aligned explicit defaults; it omits LSU token
members/minting and I/O-MSHR token assignments. For one committed owned-region
store, manager A and D therefore observe the negotiated
`{valid=0, epoch=0, sequence=0}` value and keep classification unknown while
the transaction and readback complete. This is fail-closed semantic
attribution, not access denial, and it does not model a field stripped after a
valid producer or authorize the default as CPU identity.
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

## Component model and executable boundaries

The formal names below describe intended responsibility domains, not a claim
that every domain is already implemented as one process, library, device, or
trusted component. The portable architectural boundary is the owned artifact
and authority lifecycle across them: identity, effects, object versions,
resources, provenance, admission, semantic comparison, private output,
publication or rollback, fallback, and replayable evidence.

Each project component name combines a Ravel-derived code name with a plain
functional name. The canonical glossary owns the same terminology without
renaming executable identifiers.

| Layer | Project code name | General function | Current executable realization | Boundary that must remain explicit |
|---|---|---|---|---|
| Portable thin waist | Couperin Contract Core | cross-backend contracts, identity, lineage, and authority lifecycle | strict owned schemas cover the bounded Native tensor and related job/object paths | upstream types, learned decisions, and backend configuration never become public authority merely by crossing an adapter |
| Graph construction and structural admission | Miroirs Graph Compiler | graph compiler, legal-transform boundary, and structural validator | the tensor `GraphCompiler` emits one fixed candidate slate; `MiroirsStructuralValidator` checks exact lineage; `CommandGraphCompiler` is a separate bounded command frontend | Miroirs is not yet a general compiler, and tensor and Command Graph schemas are not one shared IR |
| Semantic validation | Pavane Semantic Oracle | independent reference executor and semantic oracle | deterministic owned reference execution and exact comparison cover the bounded integer tensor families | Pavane does not select candidates, certify resources, measure performance, or publish results |
| Proposal and optimization | La Valse Optimization Subsystem | optimizer, search system, mapper, ranker, and abstention policy | `AnalyticalPredictor` ranks the fixed Native tensor slate and may abstain | proposal code is fallible advice and has no admission, execution, measurement, or publication authority |
| Experience | Boléro Experience Runtime | persistent Experience store, retrieval, retention, and advisory transfer | append-only JSONL, a bounded active index, and replayable policy experiments exist | raw measurement, completion telemetry, and Command Graph demo caching remain separate; no current Command Graph or hardware-selection loop consumes Boléro advice |
| Guarded orchestration | Chloé Graph Orchestrator | admission sequencing, baseline-first execution, private failure, selection, fallback, and rollback | bounded tensor and Command Graph executors implement separate host paths | the orchestrator is not Daphnis, the predictor, the semantic oracle, or the backend implementation |
| Execution plane | Daphnis Execution Subsystem | replaceable software or hardware execution backend and configuration plane | no general Daphnis exists; current adapters are `NativeCBackend`, correctness-only `SonatineQEMUBackend`, and the bounded T-0122 simulated Graph device | the T-0122 ABI runs only the current hardwired region; it does not make Verilator, Sonatine, or that region the general execution plane |
| Object memory | Ondine Object Memory Subsystem | object residency, versioning, movement, spill, stream, and rematerialization | a descriptive Native `MemoryPlan` plus bounded Sonatine single-hart object/version and publication slices exist | no general allocator, coherent heterogeneous memory, DMA, spill/rematerialization runtime, or persistent object service exists |
| Privileged runtime | Sonatine Microkernel | capability microkernel, execution authority, cancellation, and guarded publication | the RV64 single-hart kernel exercises job/object lifecycle and guarded publication under QEMU | Sonatine is optional for the Native profile, and emulation is not physical evidence |
| Measurement and telemetry | Alborada Measurement Observatory | segregated measurement, environment, completion, and policy-evaluation evidence | versioned records, experiment bundles, and cold completion telemetry paths exist | collected evidence does not automatically enter Boléro or grant publication authority |
| Host and transport | Rapsodie Host Bridge | userspace host integration and future device transport | GNU/Linux and macOS Native paths plus T-0122's transport-neutral word runtime and Verilator adapter | the simulated device ABI defines no real MMIO, DMA, IRQ, shared-memory, cache-coherency, or physical reset contract |
| Hardware research | Tzigane Hardware Research Laboratory | RTL architecture comparison and backend-hypothesis testing | `StaticStencilRegion`, Rocket, and BOOM remain research candidates or controls; T-0122 adds a one-command Verilator device loop | the runnable simulated device is not an installed general Daphnis backend and grants no Program, Data-publication, or Experience authority |
| Adversarial assurance | Scarbo Verification Subsystem | adversarial testing, fuzzing, fault injection, and hostile-case verification | repository tests cover many malformed, stale, fault, rollback, and fail-closed cases | there is no integrated Scarbo subsystem, complete fuzzing program, or production security assurance |

### Portable orchestration versus backend execution

The current tensor `GraphExecutor` owns the lifecycle ordering for the Native
vertical slice: validate the exact admitted slate and proposal, execute the
trusted baseline first, invoke a replaceable backend, ask Pavane for a semantic
verdict, and record selection, abstention, failure, or rollback. It does not
implement native instructions, device transport, Graph hardware, prediction,
or Experience retrieval.

The Command Graph surface is intentionally separate. Its compiler emits a
`CommandGraphProgram`; `DirectCommandExecutor` and `CommandGraphExecutor` run
the same allowlisted host tools under the same workspace and resource policy;
publication requires exact outcome agreement. It does not pass through the
tensor `GraphCompiler`, `MiroirsStructuralValidator`, `PavaneSemanticOracle`,
or Boléro.

### Deployment profiles

- **Native host profile:** owned schemas, Miroirs/Pavane checks, guarded host
  orchestration, and `NativeCBackend`; runs on GNU/Linux and macOS without
  Sonatine.
- **Sonatine emulation profile:** a bounded adapter carries owned requests into
  Sonatine's capability, object-version, cancellation, and publication path
  under QEMU; this is correctness evidence only.
- **RTL research profile:** `StaticStencilRegion`, Rocket, and BOOM are isolated
  experiment candidates or controls. They are not installed Daphnis backends,
  and their simulation results grant no Program, Data, publication, or
  Experience authority.

  BOOM functional simulator execution uses a repository-owned local image
  receipt boundary. One explicit tagless builder may create a provenance-
  bearing OCI index. Ordinary runners resolve an ignored current pointer to an
  append-only digest-named receipt, verify the exact local index descriptor,
  its BuildKit-bound linux/amd64 payload manifest, Config view, RootFS layer
  list, and platform, then execute the returned digest. A Docker tag is never
  runtime authority. This receipt is host-local because verification requires
  the corresponding BuildKit history record; it is not a portable artifact,
  remote registry identity, or durable experiment seal.

The Linux module remains outside these authority domains as a non-authoritative
transport harness. No real MMIO, DMA, IRQ, shared-memory, cache-coherency, or
device-reset contract exists. A future reviewed CPU, CGRA, FPGA, NPU, RISC-V
extension, or ASIC implementation must remain behind the same owned thin waist
and cannot import backend types or learned decisions into public authority.

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

Existing language frontends and interchange/compiler infrastructure are the
default. Raveil-specific compilation is a thin set of import, identity,
effect/object/version, resource, provenance, admission, validation, and backend-
lowering passes. A new Raveil source language, forked general optimizer, or
closed end-to-end toolchain requires a demonstrated interoperability gap and a
separate accepted decision; it is not the default consequence of adding a new
backend.

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
