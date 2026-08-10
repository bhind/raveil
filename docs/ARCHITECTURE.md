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

RISC-V is the permanent semantic/control/fallback architecture for boot,
exceptions, cold or irregular code, capabilities, object management, admission,
recovery, and trusted baseline execution. It is not the native Daphnis machine
code and not merely a temporary boot loader.

Daphnis is connected through owned job/object/completion contracts. Static,
elastic dataflow, stream, and hybrid organizations remain comparison
candidates. Dynamic islands or RISC-V fallback handle pointer chasing,
interpreters, unpredictable traversal, and other graph-hostile regions.

Linux is a non-authoritative development and driver-validation host under
ADR-0019. Linux adapters may exercise Raveil-owned versioned contracts, but do
not own admission, capabilities, Experience writes, commit, or rollback and do
not replace the permanent RISC-V/Sonatine control path.

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
