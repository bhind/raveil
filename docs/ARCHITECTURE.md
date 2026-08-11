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

T-0043 instantiates the frontend's named verification stages. Miroirs compares
the admitted artifacts with the canonical `GraphCompiler` output and exact
program, contract, candidate-set, and proposal bindings before execution.
Pavane is a separate deterministic owned reference executor: it regenerates
the fixed integer inputs and expected checksum without trusting a backend's
reference field. Pavane decides semantic equivalence only; proposal advice,
timing-based selection, Sonatine finalization, and evidence classification stay
outside the oracle.

The leading Daphnis Execution Subsystem (Daphnis) direction is a sealed explicit graph/effect contract, not a
conventional sequential register instruction stream and not an exact-cycle VLIW
schedule. A native job should carry:

- explicit data and control dependencies;
- explicit read, write, and external effects;
- object-bounded memory access and versions;
- resource requirements and limits;
- preferred placement, route, and memory plan;
- semantic and numerical constraints.

Hardware remains responsible for exact operand readiness, backpressure, token
movement, arbitration, and variable latency. This split attempts to remove
repeated *dependency-discovery* work from structured hot regions while
preserving the *timing-dynamic* mechanisms required by physical uncertainty.
The exact encoding remains Proposed in
[`RFC-0001`](rfcs/RFC-0001-native-explicit-graph-machine.md).

## RISC-V and Daphnis Execution Subsystem

RISC-V/Sonatine is a preserved semantic/control/fallback and specialized
authority architecture for boot, exceptions, irregular code, capabilities,
object management, admission, and recovery. Under ADR-0024 it is not an MVP
prerequisite and must earn primary-path status through a bounded comparison.
It is not the native Daphnis machine code.

Daphnis is connected through owned job/object/completion contracts. Static,
elastic dataflow, stream, and hybrid organizations remain comparison
candidates. Dynamic islands or RISC-V fallback handle pointer chasing,
interpreters, unpredictable traversal, and other graph-hostile regions.

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
sticky and multi-output metadata publication is all-or-nothing. This is not a
semantic oracle or data-byte shadow: T-0085 and T-0043 retain those boundaries.

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
