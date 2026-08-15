# Raveil

> Experience-guided, authority-bounded Graph execution across replaceable
> software and hardware backends.

Raveil is an experimental compiler/runtime architecture. It investigates
whether structured computation can preserve and reuse execution knowledge
instead of rediscovering every decision from scratch, while retaining a safe
ordinary-CPU fallback.

The intended system imports or constructs a versioned operation/dependency/
effect/object Graph, generates bounded implementation candidates, and uses
accumulated **Experience** to rank them or abstain. A proposal becomes usable
only after independent contract, resource, structural, semantic, measurement,
and rollback checks.

Raveil is not a new CGRA name. CPU, VLIW, CGRA, NPU, FPGA, and future ASIC
implementations are replaceable backends. The portable part of Raveil is the
contract and evidence lifecycle around them.

## Status at a glance

Raveil is research software, not a production compiler, operating system, or
accelerator. The latest immutable pre-release is `v0.0000000000007`; current
development is unreleased.

- A bounded Native userspace Graph loop runs on GNU/Linux and macOS.
- A separate Command Graph CLI runs allowlisted host tools inside a bounded
  workspace and checks direct/Graph result agreement.
- A Sonatine RV64 microkernel seed boots and runs under QEMU.
- A hardwired static Graph region plus Rocket and BOOM controls have bounded
  RTL-simulation evidence.
- Append-only and bounded Experience infrastructure is executable.
- The preregistered fixed-C Experience hypothesis closed negative: it did not
  improve median latency or estimated energy by the required 5%. This does not
  prove that Experience is universally ineffective.
- There is no general Graph compiler, production CGRA backend, FPGA/silicon
  result, or established general performance, energy, area, security, or
  commercial advantage.

See [STATUS](docs/STATUS.md) for exact implemented facts and evidence classes,
and [ROADMAP](docs/ROADMAP.md) for the current gates.

## The system Raveil is trying to build

```text
existing program / standard IR / bounded command input
                         |
                         v
               immutable Program + contract
                         |
                         v
             Graph compiler and legal transforms
                         |
                         v
        software, schedule, memory, and backend candidates
                         |
                         v
         predictor + Experience: propose or abstain
                         |
                         v
       admission + resource + semantic verification
                         |
                         v
       CPU / CGRA / FPGA / NPU / future ASIC backend
                         |
                         v
             private output + target measurement
                    /                 \
             publish                  rollback
                    \                 /
                         v
        append success, failure, context, and lineage
                    to Experience
```

The predictor is never the authority. Experience may retrieve, rank, and
propose; it cannot approve its own candidate, publish output, or suppress the
trusted baseline. When evidence is weak, the correct result is abstention and
fallback rather than forced specialization.

## What may be distinctive

Profiling, PGO, JIT translation, autotuning, learned cost models, CGRA mapping,
and hardware design-space exploration already exist. Raveil does not claim any
of them individually as new. Its narrower research question is whether their
combination can form a reusable and auditable software-hardware loop:

1. use standard compiler inputs and thin backend adapters instead of requiring
   programmers to hand-write pipelines or adopt a closed Raveil language;
2. compare software transforms, memory plans, schedules, and backend mappings
   under one versioned identity and resource contract;
3. retain failures, negative transfer, uncertainty, environment identity, and
   candidate lineage—not only winning configurations—as Experience;
4. rank candidates with calibrated abstention while keeping learned systems
   outside the authority path;
5. validate semantics and effects independently, execute into private output,
   and publish only after approval, with explicit fallback and rollback; and
6. reuse measured outcomes at two different time scales.

The fast loop selects software transformations and existing backend
configurations for a current workload. The slower, future loop may use
accumulated evidence to propose different PE, memory, interconnect, RISC-V
extension, FPGA, or ASIC designs. The slow loop remains offline and separately
verified; Experience never reconfigures or manufactures hardware by authority.

```text
fast loop: Graph -> candidate -> configure -> verify/measure -> Experience

slow loop: accumulated Experience -> hardware proposal -> simulate/synthesize
           -> separate evidence -> possible next hardware generation
```

This integrated Experience-driven loop is a hypothesis, not an implemented or
validated project result.

## Components and boundaries

| Component | Role | Current boundary |
|---|---|---|
| Miroirs Graph Compiler | owned Graph IR, legal transforms, structural validation | bounded Graph contracts and checks exist; arbitrary C/program compilation does not |
| La Valse Optimization Subsystem | search, mapping, and candidate proposal | current predictor is analytical and narrow |
| Boléro Experience Runtime | persistent evidence, retrieval, retention, and variant advice | append-only JSONL plus bounded nearest-neighbor baseline exists; it is not connected to the Command Graph surface |
| Daphnis Execution Subsystem | replaceable implementation and execution plane | Native C and bounded Sonatine/QEMU adapters exist; no general Daphnis or production CGRA exists |
| Pavane Semantic Oracle | independent reference execution and semantic comparison | bounded deterministic checks exist |
| Ondine Object Memory Subsystem | object residency, spill, stream, and rematerialization | only narrow owned object/memory slices exist |
| Sonatine Microkernel | capability, execution-authority, and publication research substrate | RV64/QEMU correctness seed; not required for the Native MVP |
| GNU/Linux host and driver boundary | current userspace integration and bounded device-transport development | userspace is the primary MVP; the driver is only a non-authoritative harness and has no DMA/MMIO/IRQ or Experience authority |
| Scarbo Verification Subsystem | adversarial testing, fuzzing, and fault injection | named direction, not a complete subsystem |

The current Native MVP keeps these public artifact types independent of any
backend: `GraphProgram`, `ExecutionContract`, `GraphVariant`, `MemoryPlan`,
`OptimizationProposal`, and result records. Upstream compiler or accelerator
types remain private adapter state.

## Relationship to CGRA, VLIW, and specialized hardware

The current Chisel `StaticStencilRegion` is a source-coded five-point-stencil
FSM. It fixes the operations, addresses, iteration structure, and state
transitions in RTL. It is a specialized accelerator reference, not a
configurable CGRA and not a general installed Graph executor.

If schedules, functional units, routes, or token readiness become loadable,
the result enters established VLIW/CGRA/dataflow mechanism classes and must be
named and evaluated as such. Raveil will prefer reviewed public implementations
and standard IR/toolchain adapters before creating equivalents.

Any custom configurable backend must pass the
[CGRA non-reinvention gate](docs/decisions/ADR-0049-cgra-substrates-are-replaceable-backends.md):

- compare directly with a reproducible public configurable control;
- load at least three semantically distinct Graphs without editing or
  regenerating RTL;
- preserve the same CPU/backend contract, rejection, cancellation, private
  failure, fallback, and publication behavior;
- account for compilation, mapping, configuration, installation, execution,
  memory traffic, PPA proxies, and fallback crossings; and
- demonstrate a contract-lifetime or authority property beyond renaming an
  existing mapper/runtime.

A custom-hardware no-go does not kill Raveil. The project can remain a portable
compiler/runtime and evidence layer over ordinary CPUs and reviewed existing
accelerators.

## Evidence, not aspiration

Raveil keeps analytical, host, native-silicon, QEMU-emulation, RTL-simulation,
synthesis-proxy, FPGA, and silicon evidence separate.

| Surface | What the repository currently establishes | What it does not establish |
|---|---|---|
| Native Graph MVP | bounded baseline-first execution, proposal or abstention, semantic comparison, commit/rollback result | general compiler support or benchmark speedup |
| Command Graph | deterministic compilation of an allowlisted shell subset and exact direct/Graph output agreement | ISA-level Graph execution or production incremental reuse |
| Experience | persistent evidence, bounded retrieval, replayable policy experiments | useful transfer to CGRA mapping or hardware design |
| EXP-0003 | independently reproduced negative result for the registered fixed-C policy | universal failure of Experience |
| Sonatine | RV64 microkernel and guarded Graph correctness paths under QEMU | production isolation or physical-hardware performance |
| Static Graph/Rocket/BOOM | bounded functional and cycle evidence under frozen RTL-simulation contracts | general CPU superiority, custom-ISA go, FPGA/ASIC benefit, or silicon performance |

Read the relevant [experiment record](docs/experiments/README.md) before quoting
any number. Conversation, a single timing printout, analytical output, or one
backend's self-report is not a performance claim.

## Quick start

Python 3.11 or newer is required. The core Python runtime has no third-party
dependency.

Open the Native interactive session:

```sh
mkdir -p /tmp/raveil-demo
python3 -m raveil shell --workspace /tmp/raveil-demo
```

At the prompt, use `help`. The session includes a bounded workspace plus the
`graph create`, `graph show`, `variants`, `propose`, `execute`, `result`, and
`history` flow. Workspace containment is an application boundary, not an OS
sandbox.

Run one owned Graph through the guarded Native backend:

```sh
python3 -m raveil graph-mvp --backend native \
  --family gemm --m 8 --n 8 --k 8 \
  --output /tmp/raveil-native-result.json
```

Explore the synthetic Command Graph walkthrough:

```sh
mkdir -p /tmp/raveil-showcase
python3 -m raveil showcase prepare \
  --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16
python3 -m raveil showcase run \
  --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16
```

This showcase uses whole host processes as conceptual nodes. It is not the
intended operation-level Graph and makes no CPU, ISA, or hardware claim.

Run the Experience seed and repository tests:

```sh
python3 -m raveil demo --reset
python3 -m raveil bench
python3 -m unittest discover -s tests -v
```

Build and run Sonatine on QEMU with a local RISC-V cross-toolchain:

```sh
make -C sonatine
make -C sonatine run
```

Or use Docker:

```sh
docker build -t raveil-sonatine sonatine
docker run --rm -it raveil-sonatine
```

The QEMU path is emulation correctness only. See the
[Native CLI guide](docs/guides/NATIVE_CLI_WORKSPACE.md),
[Command Graph guide](docs/guides/NATIVE_COMMAND_GRAPH.md), and
[showcase guide](docs/guides/NATIVE_COMMAND_GRAPH_SHOWCASE.md) for complete
instructions and limits.

## Current research path

The immediate research task is T-0044: finish matched comparisons among
ordinary CPU controls, the hardwired static Graph reference, and—only after the
non-reinvention gate—reviewed configurable controls. Full configuration,
compiler, memory, verification, and amortization costs remain in scope.

Separately, a future Experience experiment must test whether prior evidence
reduces search or target measurements at equal or better final quality, with
new Graphs, shapes, memory regimes, and hardware revisions held out. It must
report negative-transfer rate and abstention calibration. It cannot reinterpret
the closed-negative EXP-0003 result.

The project advances custom hardware only if the complete comparison shows a
material, reproducible advantage. Otherwise it deliberately pivots to the
software contract/runtime over existing CPU and accelerator backends.

## Repository guide

- [Documentation router](docs/README.md): where each kind of project fact lives
- [Current status](docs/STATUS.md): implemented and verified facts
- [Vision](docs/VISION.md): research thesis and success conditions
- [Architecture](docs/ARCHITECTURE.md): components, contracts, and authority
- [Experience model](docs/EXPERIENCE.md): storage, policies, risks, and metrics
- [Roadmap](docs/ROADMAP.md): gates and exit conditions
- [TODO](TODO.md): stable-ID actionable work
- [Decisions](docs/decisions/README.md): accepted and rejected ADRs
- [Experiments](docs/experiments/README.md): registered evidence and claims
- [Failure knowledge](docs/FAILURE_KNOWLEDGE.md): retained failures and prevention

Executable code and tests outrank prose when records disagree. Failed
experiments and rejected decisions remain part of project memory.

## License

Raveil is licensed under the [Apache License 2.0](LICENSE). Third-party tools,
source trees, papers, and hardware designs retain their own licenses and IP
status. Public availability or an open-source license is not a patent or
freedom-to-operate conclusion.
