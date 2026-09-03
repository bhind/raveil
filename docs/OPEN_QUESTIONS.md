# Open questions

Last updated: 2026-09-02

These items are intentionally unresolved. A conversation hypothesis does not
become implementation authority until an Accepted ADR or reproducible EXP
resolves it.

## Simulation-first device path

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

- If S03 passes its three external bounded DAGs, what additional discriminator
  is required before broadening the fixed address-selector alphabet or calling
  the executor generally installable? ADR-0064 deliberately stops at five
  neighbor selectors, three opcodes, 16 instructions, eight value registers,
  one active invocation, and one outstanding memory request. No larger opcode,
  memory, scheduling, or exception boundary is selected yet.

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
- T-0128/S02 answers only how one S01-admitted frozen descriptor and seed
  map onto the existing program/config/execution ABIs in RTL simulation. It
  does not broaden the three accepted identities or answer the generality
  question. T-0128/S03 now exposes that exact lower-level
  selected runner through the same top-level CLI without changing the ABI and
  revalidates marker, path, raw evidence, and receipt. PR #43 made this bounded
  answer canonical. No accepted discriminator yet authorizes a larger Graph
  catalogue, selector/opcode/window boundary, scheduler, or generally
  installable claim.

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
  control and possible Daphnis adapter? Selection remains open; public access or
  an OSS license alone is not patent clearance.
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
