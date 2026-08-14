# Open questions

Last updated: 2026-08-14

These items are intentionally unresolved. A conversation hypothesis does not
become implementation authority until an Accepted ADR or reproducible EXP
resolves it.

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
  25% incremental Rocket-core area as later no-go thresholds. T-0044 must still
  define the estimator, repetitions, interval construction, and matched
  synthesis boundary before collecting data.
- Where is the measured boundary between static, elastic dataflow, stream, and
  hybrid Graph Execution Subsystem organizations?
- How large should the RISC-V core's OoO machinery be, if any?
- Which regions remain on RISC-V or bounded dynamic tiles: pointer chasing,
  interpreters, JITs, branch-heavy control, exceptions, and unpredictable
  traversal?
- If the fixed-latency RFC-0005 candidate fails, is that a no-go for the initial
  path or sufficient evidence to draft a separately reviewed variable-latency
  mechanism? Elastic token/readiness machinery is not authorized by RFC-0005.
- Can one pinned Chisel/Chipyard environment support a fair matched comparison
  among Rocket in-order, BOOM OoO, BOOM's same-core OoO-disabled diagnostic,
  and an owned explicit-graph tile without inheriting upstream authority or
  comparing unequal cache/memory/functional resources? ADR-0046 answers the
  bounded resource-connection part for Rocket, BOOM, and static Graph: the
  strict controlled run proves the canonical owned tuple equal, preserves the
  exact oracle, brackets quiescent windows, and conserves all admitted traffic.
  The fairness question remains open for T-0044 because Graph admits 1,536
  execution transactions while each optimized CPU admits 1,056; no measurement
  claim is ready. Source survey found no
  existing upstream config that proves this boundary: Rocket's tile-internal
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
  work, replay/source reuse/backpressure, stripping after a valid producer,
  malformed nonzero metadata,
  untagged loader/FESVR/Debug traffic, BOOM load and Rocket parity, CPU-side D
  consumption, and the boundary that may drive `InitiatorCpu`. One negotiated
  absent-producer negative now observes invalid/zero at manager A/D and blocks
  attribution without blocking the store; it does not answer those remaining
  questions. ADR-0046 resolves the sequencing question: none of these remaining
  general-attribution cases gates the controlled-run T-0042/T-0044 slice.
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
- ADR-0032 fixes only one static linalg fixture and pinned IREE compiler. Which
  additional dialects, tensor signatures, import-record evolution, and
  sandboxed compiler distributions are justified before a general frontend?
- What immutable environment receipt, base-image digest, and OS resource
  limits are required before the pinned compiler adapter may process anything
  beyond repository-owned allowlisted sources?
- Which upstream components should be integrated, wrapped, progressively
  replaced, or rejected?
- What measured threshold—performance, memory, energy, variance, security, or
  adaptability—justifies replacing a mature upstream implementation?
