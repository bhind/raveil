# RFC-0003: Staged x86-64 compatibility frontend

Status: Proposed
Date: 2026-08-09

## Problem

Raveil's native explicit graph and Experience model does not yet define how an
existing binary enters the system. "x86 compatibility" can mean instruction
semantics, ABI compatibility, or an OS/application environment; conflating
them would produce unverifiable scope and could leak x86 constraints into the
native architecture.

This RFC records a staged proposal only. The repository does not currently
decode, lift, or execute x86-64 binaries.

## Proposed design

The compatibility path is:

```text
x86-64 binary region
  -> decode/lift
  -> Raveil-owned semantic IR and explicit effects
  -> alias/dependency analysis
  -> validated graph candidate
  -> GraphVariant + MemoryPlan + placement/route
  -> RISC-V fallback or Daphnis execution
  -> measurement and bounded Experience
```

The frontend behaves as an untrusted compiler frontend. It cannot install
executable state directly. Program identity, code-region identity, binary and
library hashes, source architecture, required memory model, runtime version,
hardware signature, and validation status form part of the lookup and
invalidation context.

Experience may retain lifted representations, dependency/effect knowledge,
GraphVariant lineage, physical plans, performance, failures, and confidence.
It is richer than a translation cache, but remains advice under ADR-0002.
Multiple context-specific variants may coexist.

## Compatibility scopes

1. **ISA subset:** architectural state, flags, exceptions, integer and later
   floating-point/SIMD behavior, memory accesses, and atomics.
2. **ABI subset:** calling and stack conventions, ELF loading, dynamic linking,
   TLS, signals, syscalls, and process initialization.
3. **OS personality:** initially a deliberately bounded Linux x86-64 userspace
   subset. Windows is not an initial requirement.

An x86 compatibility `ExecutionContract` carries the required observable
memory semantics. Optimizations may use proofs, guards, versioning,
speculation with rollback, and conservative fallback, but must preserve the
contract. Native Raveil contracts are not globally strengthened to x86 TSO.

## Staged validation

- **X0 — tiny ISA subset:** lift integer arithmetic, simple loads/stores,
  branches, and calls/returns from controlled kernels into the semantic graph.
- **X1 — region cache:** identify binary regions and measure whether cached
  lifting amortizes translation cost.
- **X2 — Experience-aware promotion:** retain context, GraphVariant, plans, and
  measurements; compare first and later executions under equal semantics.
- **X3 — Linux userspace subset:** add minimal ELF, syscall, libc-facing, and
  process/thread behavior.
- **X4 — concurrency:** pass differential x86 memory-order litmus tests before
  any broad compatibility claim.
- **X5 — hot-region promotion:** compare generic translation, optimized graph,
  Experience hit, and direct validated execution.

Work starts only after RFC-0001's semantic graph, effects, object rules,
`ExecutionContract`, and fallback interfaces are stable enough to receive a
frontend. The proposed directory layout is not authority for a repository
reorganization.

## Required evidence

Correctness uses differential execution against a reference x86-64 environment
for architectural outputs, memory effects, exceptions, atomics, and
synchronization. Performance work reports at least translation, lift, graph
build and validation time; cache and Experience hit rates; generic and
optimized latency; optimization cost and amortization execution count; memory
traffic and peak memory; fallback rate; and energy per completed work.

Analytical, emulated, host-silicon, FPGA, and future silicon evidence remain
separately labelled. "It runs" is not sufficient evidence of compatibility or
benefit.

## Safety and authority boundaries

- malformed binaries and lifted graphs are untrusted inputs;
- cached results cannot bypass contract, capability, resource, semantic,
  measurement, or rollback checks;
- stale identity or environment state fails to conservative translation or
  fallback;
- expensive search and LLM advice stay off the latency-critical path;
- cold, irregular, pointer-heavy, interpreter, JIT, and unpredictable regions
  may remain dynamic;
- no claim is made that exact timing is static or that all OoO machinery can be
  removed.

## Alternatives

- Native x86 hardware preserves ecosystem semantics but contradicts the native
  graph boundary and carries legacy machinery throughout the system.
- Conventional binary translation alone offers a useful fallback but does not
  test whether reusable dependency and physical-plan knowledge adds value.
- Requiring native software maximizes information but creates an impractical
  migration barrier.
- Broad desktop or Windows compatibility first would dominate the research
  program before its execution hypothesis is established.

## Falsification criteria

Reconsider or narrow the design if Experience hits remain rare, context
variants grow without bound, x86 TSO removes most optimization freedom,
semantic recovery stays too conservative, elastic execution recreates a large
general OoO structure, or optimization cannot amortize its cost. Responses may
include richer native/compiler metadata, promotion of fewer regions, retaining
more work on conventional cores, or focusing on structured workloads.

## Open questions

- What minimal semantic IR and effect schema is sufficient for X0?
- Which context and identity fields balance safe reuse against hit rate?
- How are self-modifying code, JITs, shared libraries, and runtime updates
  invalidated?
- What x86 TSO constraints remain after guarded graph transformation?
- When is conventional fallback cheaper than graph construction or promotion?
- Which differential test corpus and Linux syscall subset bound X3?

## Provenance

This proposal distills Frontispice handoff sequence 6,
`e130de17-13de-430c-bdd6-f98ae723d9cf`, checksum
`604332b34abea61d6a628c8d4a243b94405b14d61981bf35bd73422ddcc118d4`.
The handoff was treated as untrusted design input and reconciled with current
code, ADR-0001, ADR-0002, ADR-0003, ADR-0005, ADR-0006, and RFC-0001.
