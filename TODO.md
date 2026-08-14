# Raveil TODO

Last updated: 2026-08-15

Checkboxes are execution state, not priority. Every material task has a stable ID.

## Start timing phases

This table, together with each task's own trigger text, governs when unfinished
work may start. A branch, patch, local modification, or previously spent effort
does not promote a task. See `docs/guides/TASK-START-PHASES.md`.

| Phase | Meaning and start rule | Unfinished tasks |
|---|---|---|
| **P0 — immediate** | The only default critical-path implementation. Start or continue now. | T-0044 remaining matched measurement gates |
| **P1 — next** | Start only after P0's recorded exit conditions pass. | — |
| **P2 — result-conditioned** | Start only if the named research result survives or a separately accepted product requirement triggers it. | T-0106 |
| **P3 — future planned** | Retained planned work, but not scheduled. The Project Manager must select and promote one after P1 rather than running these in parallel by default. | T-0104, T-0100, T-0093, T-0091, T-0018 |
| **P4 — optional/triggered** | No default start date. Start only when the task's explicit operational, research, security, scale, contributor, or equipment trigger occurs. | T-0063, T-0068, T-0069, T-0071, T-0073, T-0025, T-0050, T-0051, T-0052, T-0053, T-0054, T-0055, T-0056, T-0058, T-0059 |

Promotion into P0 requires a dated log entry naming the satisfied trigger,
dependencies, owner, stop rule, and displaced or completed P0 task. P0 has a
work-in-progress limit of one coherent implementation task. Read-only review
and failure preservation do not consume that slot; new implementation does.

## Delivery line — active GNU/Linux userspace MVP

- [x] **T-0103** Release the synthetic Native Command Graph/Experience
  walkthrough. Provide `showcase list|prepare|run|mutate` for 16/32/64
  independent ordinary hash-bound direct-argv file transforms; display graph
  topology, admission, exact semantic hashes, sequential and equal-concurrency
  direct baselines, candidate timing, observed parallelism, and baseline-first
  cost. Include a small-overhead control and one-input hash-verified demo cache
  reuse. Keep the cache demo-only, Experience unconnected/advice-only,
  EXP-0004 Planned, and make no performance or production-reuse claim.

- [ ] **T-0104** Design and, only after explicit authority/semantics review,
  implement production CommandGraphExecutor incremental reuse. Define durable
  artifact lineage, invalidation across tool/policy/environment/workspace
  changes, output publication/rollback, cache budget/eviction, concurrent
  safety, measurement fairness, and an Experience boundary. Do not promote the
  T-0103 showcase cache or call its observed work avoidance a production win.
  This tool/process-level follow-up is deferred behind T-0057, T-0042, and
  T-0044; it is not the next test of the native CPU thesis.

- [x] **T-0105** Bootstrap a reproducible, pinned Chisel/RISC-V simulation
  substrate. First elaborate and simulate one trivial repository-owned RTL
  circuit; then execute one unmodified reference RISC-V configuration if host
  memory and build time permit. Record exact JDK, Scala/build tool, Chisel,
  simulator, upstream revision, architecture, commands, and licenses. This
  proves tooling and functional execution only: do not implement the proposed
  Graph microarchitecture, collect performance evidence, call a reference core
  ARM-equivalent, or claim CPU/ISA advantage. T-0105 may precede T-0057 because
  no Graph contract depends on it. Completed with the owned counter smoke plus
  unmodified Rocket `DefaultSmallConfig` elaboration and `DefaultConfig`
  Verilator execution of all 16 `rv64mi-p` tests. The fixed Git/Nix/Docker
  wrapper rejects source drift, bypasses the upstream mutable Python shell
  hook, and labels the result `rtl-simulation-functional`; Graph RTL and
  performance remain unimplemented/unmeasured.

- [x] **T-0107** Correct the T-0042 estimate and stale-authority completion
  failure. The post-scope-reset estimate of three to six working days was wrong:
  the implementation candidate completed in 2 hours 48 minutes. Require every
  future duration estimate to bind an exact authority commit and exit contract,
  inventory reusable code and warm/cold build state, separate edit,
  verification, and integration effort, and expire on scope or authority
  change. Require the implementation HEAD to descend from the latest authority
  commit before calling it complete; otherwise label it integration-pending.
  The PM role, WORKFLOW, estimate template, failure knowledge, and dated log now
  carry the same prevention rule.

- [x] **T-0102** Add bounded Tab completion to the Native Interactive CLI.
  Complete only documented commands, graph subcommands/options, allowlisted
  command tools, and virtual workspace paths; omit symlinks and host absolute
  paths, retain readline/libedit editing and ephemeral history, and keep every
  completed token subject to the existing parser, workspace, validation, and
  authority checks. This is host usability, not shell expansion, PATH lookup,
  filesystem authority, or T-0100 isolation.

- [x] **T-0101** Build the Native Command Graph demo on the completed T-0099
  workspace. Parse a documented safe shell subset into an owned, versioned
  command DAG; execute the same preregistered ordinary file-processing
  workloads through a direct baseline and the graph executor; require exact
  stdout, output-file, exit-status, and failure-propagation agreement before
  comparing timing. Start with built-ins plus allowlisted host OSS tools for
  text filtering, counting, sorting, deduplication, slicing, hashing, and
  bounded file movement. Support pipelines, explicit file inputs/outputs,
  guarded sequencing, and independent fan-out without `shell=True`, arbitrary
  executables, command substitution, environment expansion, globbing, append,
  or host-path escape. Record graph construction, execution, end-to-end,
  toolchain identity, and per-node outcomes separately under EXP-0004. Keep
  existing tensor/GEMM graph schemas and authority unchanged, and do not claim
  performance, energy, GNU/POSIX compatibility, or sandbox security beyond the
  completed evidence.

- [x] **T-0099** Extend the T-0098 Native Interactive CLI with one explicitly
  selected workspace root and the minimum file-oriented operator commands:
  `pwd`, `cd`, `ls`, `cat`, `stat`, `mkdir`, and bounded exclusive `write`.
  Present that host directory as virtual `/`, resolve every CLI path beneath
  it, and reject host-absolute escape, escaping `..`,
  symlink escape, special files, oversized reads/writes, and overwrite, and
  keep existing `graph create`, `graph show`, `variants`, `propose`, `execute`,
  and `result` authority unchanged. Use the workspace for result publication
  and human inspection; do not add arbitrary shell execution, pipes,
  redirection, deletion, PATH lookup, GNU-tool emulation, or a performance
  claim. This first slice is application-level workspace containment and must
  not be described as an OS security boundary.

- [ ] **T-0100** Replace or reinforce T-0099's application-level workspace
  containment with a modern enforceable sandbox after the minimum Native CLI
  is human-evaluated. Preserve one portable capability-style workspace API;
  evaluate descriptor-relative path resolution plus Linux `openat2`/Landlock
  or a mount-namespace sandbox, and a container/VM or signed App Sandbox helper
  on macOS. Separate read-only inputs from writable work/output, isolate the
  compiler/executor worker, disable network by default, record the selected
  sandbox backend, and fail closed when strong isolation is explicitly
  requested but unavailable. Do not claim equivalent enforcement across OSes
  without platform-specific tests and a security review.

- [x] **T-0098** Add `python3 -m raveil shell` as the Native userspace
  interactive MVP. Keep one explicit Session over the existing guarded graph
  compiler/adviser/executor and reject invalid ordering and overwrite without
  traceback. Pause Sonatine shell feature growth pending human evaluation.

- [x] **T-0097** Remove the accidentally tracked root `AgentNames.md`, retain
  the call-sign catalog only under ignored local `.codex/`, explicitly ignore
  the root filename, and add a regression preventing its reintroduction.
  Preserve published tags and history rather than rewriting immutable releases.

- [x] **T-0088** Establish lightweight failure-knowledge and GitHub Issue
  governance: preserve experiments and raw evidence, maintain a reusable lesson
  index, provide a safe bug template, escalate only durable/actionable defects,
  and keep TODO plus repository records authoritative.

- [x] **T-0087** Reconcile the commodity-host/GNU/Linux/OSS-first pivot with
  current main without deleting Sonatine Microkernel, Linux harness, contract,
  telemetry, Experience, experiment, or metadata-shadow artifacts; reserve existing
  side-branch identifiers, adopt ADR-0024, and prepare a restart handoff.
- [x] **T-0086** Port the preserved `feat/t-0086-linux-graph-mvp` prototype onto
  current main without merging its deletions. Make one owned graph run in
  GNU/Linux userspace through baseline, proposal or abstention,
  structural/semantic checks, commit or rollback, and evidence output. This is
  the sole implementation P0 after the owner explicitly restarts the line.

T-0086 is complete on GNU/Linux and macOS host-correctness paths. T-0034 and
T-0085 were subsequently completed on independent Sonatine branches; T-0018,
compiler expansion, and hardware work remain preserved outside the userspace
MVP.

## High priority demo — Sonatine native operator shell

- [x] **T-0092** Extend the existing bounded Sonatine U-mode shell with an
  honest native operator demo covering `ls`, `cat`, `echo`, `write`, `stat`,
  `jobs`, `run`, `cancel`, and `result`. Reuse the capability-checked VFS and
  existing bounded graph job/completion/finalization path; derive listings and
  state from kernel objects rather than hard-coded success prose. Keep all
  U-mode requests scalar or fixed-width, preserve baseline/admission/semantic/
  rollback authority, and add deterministic QEMU smoke plus a replayable
  host-side demo record labelled emulation correctness. Do not import BusyBox,
  add an ELF loader, claim POSIX compatibility, add arbitrary user pointers,
  or report latency/energy. Execute Ciste's Sonatine slice first, then Lifri's
  host demo after the serial contract is frozen. Use the owner packet in
  [`docs/guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md`](docs/guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md).

T-0092 is the next demo P0 after already in-flight work reaches a clean
milestone. It is a bounded demonstrability task, not permission to grow a
general Unix personality or displace the GNU/Linux/RK3588 product path.

## Demo release

- [x] **T-0095** Publish the completed T-0092 operator flow as the immutable
  `v0.0000000000002` GitHub Pre-release. Tag the exact fresh-clone-audited
  commit, attach no generated evidence, keep hosted CI disabled, and read back
  the remote tag, target SHA, visibility, notes, and assets before closeout.

- [x] **T-0096** Correct the published interactive-demo failure: remove
  unbounded per-preemption UART logging from normal operation, map U-mode ETX
  (`Ctrl+C`) to the existing checked shutdown path, add a real-QEMU interrupt
  regression, auto-select either supported RV64 toolchain prefix, preserve the
  immutable v0.0000000000002 tag, and publish a new audited Pre-release.

## Queued visibility side project — graph directory view

- [ ] **T-0093** Add a deterministic read-only host directory view of one
  validated Raveil graph snapshot. Materialize the existing owned v1 program,
  contract, nodes, variants, memory plans, proposal, selection, and result into
  an explicitly selected empty output directory with stable names, exact
  identity hashes, a root manifest, and a text tree summary. Parse every input
  through the existing strict schema and reject stale lineage, unknown fields,
  duplicate names, traversal, symlinks, nonempty targets, and overwrite. The
  first slice is an inspection artifact only: no FUSE mount, Sonatine VFS
  projection, write-back, execution authority, Experience promotion, or
  performance claim. Preserve a later live `/graphs` view as a separate design
  decision after the host snapshot proves useful.

## Post-MVP side project — ReactOS portability probe

- [ ] **T-0091** After the GNU/Linux userspace graph MVP and owned v1 artifact
  lineage remain regression-clean, port the same bounded graph control loop to
  ReactOS as a non-authoritative Win32 host. Start in an isolated x86/x64
  virtual machine, cross-build a user-mode CLI, and preserve the existing
  `GraphProgram`, `ExecutionContract`, `GraphVariant`, `MemoryPlan`,
  `OptimizationProposal`, and result schemas without ReactOS-specific fields.
  Exercise baseline-first execution, proposal or abstention, semantic checksum,
  explicit commit or rollback, fail-closed unsupported-operation handling, and
  replayable environment/result evidence. A direct CLI is sufficient for the
  first slice; if process separation is useful, place the owned fixed-width ABI
  behind a Win32 named-pipe adapter. Do not require a kernel driver, copy
  ReactOS source, treat ReactOS as an RK3588/AArch64 target, or claim production
  compatibility, security isolation, latency, or energy improvement.

T-0091 is optional portability and fault-boundary work, not a dependency of the
main GNU/Linux/RK3588 delivery line or any existing Gate.

## Now — make v0.0000000000001 independently reproducible

- [x] **T-0009** Add repository-scoped Codex explorer/reviewer/verifier roles
  and the task-governance/Gate 0 evidence skills; validate discovery metadata
  and preserve local IDE configuration outside Git.

- [x] **T-0060** Replace the temporary handoff entry point with canonical
  docs routing, archive conversation provenance, extract reusable debugging and
  design-history records, and extend governance progress audits.

- [x] **T-0001** Run `make -C sonatine smoke` on macOS through Docker and record
  `EXP-0002` with exact Mac model, Docker/QEMU versions, console output, and result.
- [x] **T-0002** Run all nine tests from a clean GitHub clone and record commands
  in `docs/STATUS.md`.
- [x] **T-0003** Add a local CI entry point for Python tests, freestanding C
  release/debug builds, DWARF inspection, and QEMU smoke. Do not use hosted CI.
- [x] **T-0004** Reconcile the existing public `v0.0000000000001` tag and
  Release as historical artifacts. Do not move the tag or publish a new
  release while CI/CD is intentionally local-only.
- [x] **T-0005** Confirm that the public repository contains no generated
  Experience log, credential, build output, or machine-local path.
- [x] **T-0006** Add a first-class debug build mode (`-Og -g3` for C and `-g3`
  for assembly) without weakening the release flags, then verify `.debug_info`
  and `.debug_line` in the ELF.
- [x] **T-0007** Verify the actual IntelliJ IDEA C/C++ plugin run-configuration
  list before documenting IDE-driven GDB attachment. Do not substitute CLion
  menus or `Remote JVM Debug`.
- [x] **T-0008** Record the native macOS/Homebrew build and QEMU smoke transcript
  in `EXP-0002`, including exact tool versions and Git commit SHA.
- [x] **T-0061** Verify command-line QEMU `-S -s` plus
  `riscv64-elf-gdb`, stop at `kmain`, and record commands and results in
  `EXP-0002`.
- [x] **T-0062** Establish formal component names in the Glossary and apply
  the display convention to active records without renaming code identifiers
  or archived source text.
- [ ] **T-0063** Reconsider GitHub-hosted CI/CD only when the project has
  multiple contributors and its owner has explicitly approved the cost and
  operating policy.
- [x] **T-0064** Replace the three generic Codex roles with Project Manager,
  Experience/Systems/Measurement Implementers, Tester, Performance/Security
  Reviewers, and Researcher; enforce canonical-record and research-memo write
  boundaries.
- [x] **T-0089** Grow the persistent Sonatine U-mode task from single-byte
  commands into a bounded line-oriented `raveil-u>` shell with CR/LF/CRLF,
  empty-line, delete/backspace, overflow-recovery, unknown-command, timer
  preemption, and capability-authority regression coverage.
- [x] **T-0090** Add the explicit `sonatine-qemu` GNU/Linux graph backend with
  a versioned pointer-free loader request, bounded fully bound serial result,
  existing job/completion/finalization reuse, strict failure parsing, fixed
  emulation evidence, and native differential verification.
- [x] **T-0065** Implement ignored local research bundles plus immutable rclone
  copy, download-based content verification, overwrite refusal, external
  credential boundary, and completion-marker-last behavior. Real Drive sync is
  verified by EXP-0003. Seal every bundle immediately, but sync at experiment
  milestones or for selected unique failures; batch redundant retries and keep
  them incomplete until remote verification.
- [x] **T-0066** Add the read-only Raveil Librarian agent and context-routing
  skill that returns a minimal authoritative reading packet without deciding
  tasks, gates, or claims.
- [x] **T-0067** Require post-Gate-0 work branches and document the lowercase
  `<type>/<record-id>-<short-slug>` naming convention.
- [ ] **T-0068** Install and verify the ADR-0010 root-owned powermetrics helper
  and helper-only `NOPASSWD` sudoers entry after the tracked implementation and
  tests pass. Prove operation after `sudo -k`; never run Raveil itself as root.
- [ ] **T-0069** Pilot RFC-0003 reference management with the nine existing
  research sources: verify exact versions, authorship, rights/access status,
  correction or retraction state, source type, patent-review status, and source
  locators; add claim cards and offline validation before proposing a permanent
  workflow or ADR. Keep non-paper prior-art notes separate from paper abstracts.
  Vreji owns the read-only similarity/IP inventory and escalation under
  ADR-0014; the Project Manager owns canonical integration.
- [ ] **T-0071** Reduce immutable research-bundle remote object count and sync
  latency without weakening per-file SHA-256/size attestation, overwrite
  refusal, downloadable verification, credential isolation, or
  completion-marker-last semantics. The 3,600-record EXP-0003 history bundle
  exposed the cost of transferring and checking thousands of individual raw
  powermetrics files; preserve the existing verified bundle unchanged.
- [x] **T-0072** Constrain every mutable `ResearchBundle` write to its own
  RUN-ID directory, not merely the shared artifact root, and add traversal tests
  proving `..`, absolute, and symlink-resolved paths cannot write into another
  run or outside the artifact root.
- [ ] **T-0073** Extend pre-seal sensitive-data inspection beyond selected text
  suffixes, reject broader credential-key forms, validate external rclone config
  ownership/permissions, constrain the declared remote root, and persist a
  durable post-sync receipt without mutating sealed evidence. Bind uploaded and
  remotely checked bytes to a fixed verified snapshot so a local mutation
  between pre-sync verification, copy, check, and marker transfer cannot be
  certified by the original seal.
- [x] **T-0074** Add repetition-aware hierarchical or cluster bootstrap and
  preregistered drift diagnostics for Gate energy claims. Report sensitivity to
  the current workload-level paired bootstrap and capture power/battery,
  frequency, time-block, and background-load evidence where available. Analysis
  now reports a workload/repetition hierarchical sensitivity interval, per-group
  energy CV, normalized sequence quartiles, thermal levels, and start/end
  battery, frequency, and load snapshots without changing the preregistered
  paired-bootstrap Gate threshold.
- [x] **T-0075** Remove timing flakiness from the powermetrics readiness test
  without weakening the production minimum-sample fail-closed contract. The
  sampler now excludes exactly one readiness observation and carries any
  already-read later observations into the measurement window. After the first
  timing-based regression recurred, it was replaced by an explicit
  operation/fake-sampler handshake; that test and the deterministic same-burst
  regression verify the boundary without relying on scheduler timing.
- [x] **T-0079** Implement the pinned official Apache TVM MetaSchedule adapter
  after the fixed-C contract stabilized. Pin the Apple Silicon environment,
  preserve the same source/target holdouts and candidate identities, store each
  constrained candidate schedule in the MetaSchedule JSON database, query it
  back before execution, and verify all three workload families and ten
  candidates against the int64 semantic checksum.
- [x] **T-0080** Complete Gate 1 evidence collection: run and remotely verify an
  independent fixed-C target, a TVM history source, and a pre-registered TVM
  target; compare conclusions, obtain performance/security reviews, and record
  the final `pass`, `pause`, or `falsified` Gate decision without changing the
  preregistered thresholds.
- [x] **T-0081** Add an explicit between-workload thermal recovery protocol for
  fanless Apple Silicon after consecutive full-run attempts failed closed at
  `Moderate`. Keep every measurement window fail-closed, require a configured
  minimum idle period plus two consecutive valid powermetrics preflights before
  the next workload, bound the maximum wait, and record every observation and
  command parameter in the mutable run bundle.
  Apply the same boundary after backend compilation/database preparation and
  before the first measurement so TVM setup heat cannot enter its first window.
- [x] **T-0082** Keep recorded compile/prepare commands logical and portable.
  A completed independent run initially failed sealing because the native
  compile tuple contained absolute bundle paths; record repository-relative
  source and bundle-relative output paths while retaining the actual tool and
  flags, and normalize only the still-mutable command record before sealing.

## Now — turn Sonatine Microkernel seed into a real minimal microkernel slice

Gate 1 is closed negative. Full measurement campaigns are paused; the harness
remains a maintenance-mode verification facility. Resume a full campaign only
for a bounded, preregistered hypothesis tied to a concrete build decision and
only after a short pilot demonstrates candidate separation.

- [x] **T-0010** Parse or deliberately constrain the QEMU device tree instead of
  silently assuming all platform properties.
- [x] **T-0011** Implement Sv39 address spaces and explicit kernel/user mappings.
- [x] **T-0012** Move the minimal `init` bootstrap to U-mode behind an `ecall`
  boundary. The interactive diagnostic shell remains in M-mode until the
  scheduling/fault slices can keep it observable as a user task.
- [x] **T-0013** Implement context switch between `init` and `idle`.
- [x] **T-0014** Make the CLINT timer drive preemption.
- [x] **T-0015** Add blocking IPC semantics and capability delegation tests.
- [x] **T-0016** Add fault tests for stale capability generation, rights escalation,
  invalid endpoint, user fault, and timer re-entry.
- [x] **T-0083** Complete the Gate 2 persistent U-mode shell/task slice before
  filesystem work. Bind syscall identity to the current scheduled task rather
  than a user-supplied task ID; preserve a full trusted kernel context across
  U-mode traps; resume the user task after real CLINT preemption; expose only
  capability-mediated kernel operations. QEMU acceptance must show a prompt
  and command before and after preemption plus denied forged, wrong-owner, and
  rights-escalation attempts. Define the syscall ABI, task lifecycle, trap
  ownership, and scheduler boundary in ADR-0017 before implementation closure.
- [x] **T-0017** Add a minimal VFS plus RamFS/initramfs after the isolation and
  scheduling base is credible.
- [ ] **T-0018** Add VirtIO block and evaluate a simple persistent filesystem
  such as FAT32; keep production-OS compatibility out of this gate.

Sonatine gate: the existing shell remains observable from U-mode and survives
timer-driven switching without capability bypass.

## Next — replace ToyDaphnis with one real measurement boundary

- [x] **T-0020** Define a replayable benchmark manifest and environment signature.
- [x] **T-0021** Implement a fixed CPU-loop backend behind
  `measure(context, candidate) -> Metrics`, including fail-closed non-interactive
  powermetrics privilege preflight, calibrated pilot/full sampling windows, and
  a minimum power-sample contract, or document why TVM MetaSchedule is selected
  instead.
- [x] **T-0022** Compare cold prior, full-history nearest neighbor, bounded
  Experience, FIFO, reservoir, and random retention. The sealed-source plan
  generator and target outcome path now implement equal-budget comparison;
  policy analysis rejects
  incomplete, duplicate, unknown, late, or provenance/measurement-mismatched
  selection/outcome evidence under ADR-0012 and ADR-0013. The sealed and
  remotely verified 24-workload source history now exists. Source-only
  simulation exposed and corrected a non-binding 256-record memory limit; the
  target pre-registered 64 versus 240 full-history summaries. The first target
  comparison is complete and negative: bounded matched cold at zero median
  latency/energy improvement, so the Gate hypothesis did not pass this run.
- [x] **T-0023** Add lineage, shape, working-set/memory, and
  operator-composition holdouts.
- [x] **T-0024** Report HCR, NTR, Coverage, calibration, measurement budget,
  retrieval latency, active-memory size, and cold-evidence size separately. The
  per-policy aggregation and the first EXP-0003 target report are complete.
- [ ] **T-0025** Preserve and analyze failed and boundary variants, not only
  winners. The sealed and remotely verified sampler-startup failure RUN-ID is
  the first preserved boundary variant; broader failed-variant coverage remains.

Experience gate: EXP-0003 completed fixed-C independent and pinned-TVM
executions with immutable remote verification. Both produced zero median
latency/energy improvement and exceeded the joint NTR limit, so the
preregistered 5% hypothesis is falsified and Gate 1 is closed negative.

## Preserved — specialized authority integration

- [x] **T-0084** Add a non-root Linux driver-development harness with a
  versioned pointer-free PING/NOP ABI, same-UID private local transport, and a
  one-inflight contract core. This validates transport only; it does not admit
  Daphnis work or replace Sonatine authority.
- [x] **T-0030** Define shared `JobDescriptor` and `CompletionRecord` schemas.
- [x] **T-0031** Define standalone `ObjectManifest` and add Sonatine
  submission/completion rings plus the object table.
- [x] **T-0032** Send measured completion telemetry into append-only Experience.
- [x] **T-0033** Implement the kernel-owned metadata-shadow lifecycle, explicit
  approval, atomic visible-version commit, cancellation, and rollback.
- [x] **T-0034** Enforce Program/Graph/Data/Experience write authorities with
  distinct capability types, immutable boot-scoped Program/Graph registries,
  capability-gated Data registration/submission/publication, separate Program
  approval, and restricted Experience observation admission. Raw job mutation
  primitives are internal and normal kernel/graph paths use the guarded API.
- [x] **T-0085** Add fixed 512-byte object backing, dispatch-time snapshots,
  Data-authorized byte staging, approval-time freeze, and atomic byte/version
  publication. Rollback, cancellation, and conflict preserve visible bytes.

## After the userspace MVP — compiler and adaptive execution

- [x] **T-0040** Import the repository-owned 8x8x8 i32-to-i64 GEMM MLIR fixture
  through pinned IREE 3.11.0, emit only a strict owned import record and
  canonical GraphProgram, then retain the baseline-first Miroirs/Pavane and
  explicit commit/rollback path.
- [x] **T-0041** Define strict, versioned Raveil-owned `GraphVariant`,
  `MemoryPlan`, and `OptimizationProposal` schemas and bind every proposal to
  the exact program, execution contract, and candidate set before execution.
- [x] **T-0042** Bootstrap an owned mapper/simulator adapter without leaking
  upstream types. **ADR-0046 small-start priority:** stop adding token-lifecycle
  cases. T-0042 closes with the smallest controlled-run slice that (1) preserves
  the frozen RFC-0005 workload and independent oracle across Rocket, BOOM, and
  Graph, (2) connects all three through one owned contract with equal ports,
  buffering, request capacity, arbitration, width, and response rule, (3)
  brackets a quiescent execution window and rejects unaccounted traffic, and
  (4) emits complete six-phase and total-cycle records with explicit resource
  equality and comparison eligibility. General semantic-initiator attribution
  is not a T-0042 claim. The strict three-way RTL run passed with resource hash
  `16664d8...27748`, exact common input/oracle output, quiescence before and
  after each execution window, conserved traffic, and complete phase totals.
  The aggregate sets `resource_equality_verified=true` and functional
  `comparison_eligible=true`, but keeps `dynamic_memory_traffic_equal=false`,
  `t0044_measurement_claim_ready=false`, and `performance_claim=false` because
  Graph admits 1,536 execution transactions while each CPU admits 1,056. Use
  `docs/guides/T-0042-SMALL-START.md` as the replay packet. After T-0105 proves
  the substrate and T-0057 completes its
  direct-prior-art/IP review and freezes the minimal native graph/effect schema,
  use the pinned Chisel/Chipyard research environment with Rocket in-order,
  BOOM OoO and same-core OoO-disabled diagnostic configurations plus an owned
  Graph execution model. Chisel constructs RTL; use a simulator such as
  Verilator for evidence and label it simulation, not silicon. The first owned
  slice is functional: a deterministic compiler/validator binds RFC-0005
  configuration `d4bf9395...d1e2` to a six-phase Chisel stencil executor;
  Verilator matches an independent C++ oracle for 512 outputs and verifies
  cancel invalidation plus restart. A strict common simulation adapter v2 now
  normalizes semantics, useful operations, implementation identity, private
  output state, and six lifecycle accounting phases without leaking upstream
  types. ADR-0041 makes actual memory model, resource-match verification, and
  matched-comparison readiness explicit; semantic success cannot imply matched
  resources. The legacy Graph v2 record intentionally remains `accounting_complete=false`,
  `resource_match_verified=false`, and has no total until installation,
  completion, validation, and publication phases are implemented. That record
  remains provenance; the later strict controlled record supplies complete
  accounting. The earlier work then continued with pinned BOOM, its same-core
  diagnostic, and Rocket/BOOM records behind this boundary. ADR-0040 now fixes
  Chipyard 1.11.0/BOOM `9459af0...10847c`, `SmallBoomConfig`, the retained-
  structure serialize-dispatch diagnostic, and exact license hashes; source
  verification passes. The explicit-public-gitlink build compiles BOOM,
  elaborates `SmallBoomConfig` to FIRRTL containing `BoomCore`, builds the
  Verilator simulator, and executes a minimal sum/store/load/check RV64 ELF to
  a successful `tohost` completion. This smoke is not the RFC-0005 workload and
  emits no common-adapter record. The same ELF source also sets and reads back
  CSR `0x7c1` mask `0x8`, then completes the identical workload under the
  retained-structure serialize-dispatch diagnostic. Keep the task open for
  matched Rocket/BOOM/Graph functional records behind the common adapter. Do
  not turn the Graph schedule assertion, source pin, or either
  minimal BOOM execution into a performance result. BOOM normal and diagnostic
  now also execute the exact 324-word/256-output RFC-0005 fallback; independent
  host signature validation passes and emits honest cache-backed/unmatched v2
  records. The pinned Rocket control now executes the same fallback and matches
  the same 256-word signature/checksum while emitting an honest cache-backed/
  unmatched v2 record. All four semantic identities are present; those legacy
  records still leave the common fixed-latency scratchpad/resource boundary
  open. ADR-0042 now
  places all three CPU control buffers in their inherited common 64 KiB Mbus
  TLRAM and validates the same signatures, but labels its latency unverified
  and keeps resource matching false. A passive observer now validates the
  bank-local, post-fragmenter single-beat request/response correspondence in all
  three CPU modes. It observed the same one-cycle endpoint interval for 296
  read beats per run but no write beat and cannot distinguish CPU execution
  from cache refill or FESVR recovery phases. The ADR-0046 strict slice later
  replaces this run-local
  diagnostic with an owned CPU/Graph request adapter that exposes initiator,
  phase, read/write coverage, buffering, arbitration, ports, and invariant
  latency under one interface before closing T-0042. ADR-0043 now adds the
  first standalone owned target: an assert-enabled,
  maximum-one-outstanding scratchpad request/response module whose local
  response is available one cycle after acceptance and whose initiator, phase,
  read/write, byte-mask, backpressure, range-error, and transaction-accounting
  paths pass Verilator. The static Graph region now uses disjoint input and
  private-output logical regions in one physical instance of this contract for
  control staging, Graph execution, and control validation. Two full runs each
  passed 1,280 execution
  reads, 256 execution writes, every oracle output, and cancel/drain/restart.
  In those legacy records the CPU path is not connected and resource matching
  remains false. The strict controlled slice now builds and verifies the pinned
  CPU adapters under the same interface; fixed end-to-end latency and
  performance remain unclaimed. ADR-0044 adds the
  first repository-owned CPU TileLink translation target in dedicated Rocket
  and BOOM configurations. It intentionally uses the uncached peripheral bus
  so accesses to its mapped region are intended to traverse the manager. A
  phase-fenced bare-metal Rocket workload now executes full and partial data
  writes, reads, phase selection, and aggregate counter checks through that
  manager with an exact host-verified signature. This is still a
  resource-unmatched step, not the RFC-0005 common memory. Before calling it a
  common-contract CPU adapter, add semantic initiator separation. Direct monitor-enabled TileLink RTL
  coverage now passes for
  full/partial writes, two masks, invalid phase denial, response backpressure,
  one-outstanding admission, response metadata, reset phase, and bounded
  aggregate counters. The exact same ELF and verifier now pass on the dedicated
  BOOM system with an identical decoded signature. Exact generated-graph checks
  now verify the config-specific DCache-MMIO source ranges, and runtime audit
  registers correlate each accepted data request's source/software phase with
  D completion: expected 8/8, unexpected 0/0, and last phase 2/2 on both CPUs.
  This is bounded client-class and semantic agreement evidence, not semantic
  initiator proof or comparative evidence. A standalone post-fragmenter
  TileLink-to-owned-contract bridge now translates six assert-enabled harness
  transactions into explicit owned request/response initiator and phase
  metadata while preserving TileLink source/size; full/partial writes, both
  masks, range denial, one-outstanding blocking, D backpressure, metadata
  correlation, and 6/6 conservation pass. Those metadata values are supplied
  by the harness, not derived as durable CPU/ELF identity. Next connect the
  bridge through a CPU-side attribution boundary that separates loader/FESVR/
  debug activity and proves where semantic initiator metadata is assigned,
  then design the matched resource boundary. The deployed CPU overlay is not
  yet the ADR-0043 common-contract adapter and does not provide the matched
  resource boundary. Direct protocol V4 now supplies a real negative classifier
  control: expected range `[1,3)` completes 3/3 while deliberate boundary
  sources 0 and 3 complete as unexpected 4/4, and same-source reuse is blocked
  while D is pending. Its untagged raw client additionally reports structural
  origin 0/0 and non-origin 7/7. Repository-owned Rocket and BOOM hooks now add
  a request marker immediately after each DCache; both CPU signatures report
  origin 8/8, non-origin 0/0, in-range sources, and phase 2/2 through D
  completion. A second test-only protocol top now drives origin true upstream,
  removes the field before the manager, and completes as origin 0/0 and
  non-origin 7/7, proving that metadata loss fails closed in this transport
  model. A dedicated four-byte writable PT_LOAD probe now exercises the pinned
  SimTSI/FESVR loader transport without `+loadmem`: before CPU access it
  observes serial-class origin 0/0 and non-origin 2/2, then the CPU read adds
  configuration-specific DCache origin 1/1 while non-origin remains 2/2.
  This closes only that bounded loader-path negative. A repository-owned DMI
  driver now also exercises one concrete 8-bit Debug SBA write in both pinned
  configurations: Debug-class non-origin 1/1 is followed by DCache-origin 1/1,
  with exact generated source ranges and A/D phase correlation. Next determine
  what durable semantic witness beyond DCache origin identifies the intended
  ELF request, cover remaining loader/debug paths fail closed, and design the
  matched resource boundary. Do not promote a config-dependent TileLink source
  ID, or DCache origin alone, into target-ELF semantic identity. A
  cross-workload audit now makes that limit executable: two distinct ELFs reuse
  exact DCache source 8224 on Rocket and 8288 on BOOM while retaining different
  payload/signature semantics. ADR-0045 now defines CPU-owned, commit-aware
  token and epoch semantics plus replay/kill/exception/reset rules before any
  core/LSU modification. A repository-owned standalone Rocket lifecycle
  observer now passes those load/store and fail-closed cases with synthetic
  events, exact marker verification, and terminal conservation; it also rejects
  an invalid completion instead of promoting a retired operation. This is a
  contract smoke, not a pinned Rocket probe. A bounded pinned Rocket diagnostic
  now observes accepted store/load requests, captures the request DCache tag,
  separately matches the load response, and observes WB retirement; its exact
  positive workload and signature pass. One additional pinned negative now
  records an accepted wrong-path store and blocks promotion when an older taken
  branch redirects in the same cycle; bounded loads before and after the probe
  observe the same non-magic value and complete as distinct tokens. The current
  observer is deliberately single-live-token and rejects a new candidate while
  a load still awaits response/retirement closure. A separate exact-config
  diagnostic now directly observes `s1_kill=1` one
  cycle after that accepted request and independently records only two
  successful manager `Get` A/D pairs for the before/after loads; the probed
  wrong-path `Put` is absent from that bounded log. The Rocket request/S1
  sequence, PC, address, and local tag correlate, but no token is carried into
  TileLink. A separate pinned diagnostic now correlates one accepted
  misaligned load with its later WB misaligned-load exception, blocks
  promotion, verifies exact trap recovery, and preserves equal aligned
  before/after readback. This is Rocket-local post-request exception evidence,
  not post-TileLink-A rollback evidence. ADR-0045 therefore remains open for
  multi-token overlap, pre-request kill, post-A exception/rollback, replay,
  reset/epoch, durable DCache/TL token correlation, same-token owned-manager D
  completion, and complete owned-manager lifecycle coverage. A first pinned
  BOOM positive now
  correlates one exact LSU DCache load request, matching response, and
  architecturally valid ROB commit by repository sequence; ROB/LDQ indices and
  branch mask remain context, and no token crosses DCache or TileLink. The
  existing Rocket two-attempt trace is not a replay witness because every
  directly surveyed replay/nack qualifier was zero. One pinned BOOM
  exception-ordering diagnostic now correlates a misaligned-load candidate,
  LSU exception, one later matching DCache request acceptance, and the global
  ROB rollback state while requiring zero matching responses and zero
  architectural commits. The exception precedes request acceptance and the
  faulting entry is not present in a rollback row, so this does not close the
  still-required post-request BOOM exception/cancellation or general rollback
  boundary. A pinned BOOM store diagnostic now correlates the local ROB/STQ
  authorization transition with DCache request, response, and STQ clear, and
  independently observes one successful manager Put A/D pair plus readback.
  The sequence is not carried into TileLink, so complete same-token store
  attribution remains open. One deterministic cacheable BOOM negative now
  correlates an exact wrong-path LSU DCache request and response with a later
  branch kill and zero matching commit. It does not exercise the uncached owned
  manager or establish post-A cancellation. One bounded BOOM-store diagnostic
  now carries only `{valid, epoch, sequence}` from the already-authorized LSU
  request through DCache/TileLink, latches that identity on the exact owned
  manager Put A, and observes it unchanged at the matching D completion.
  ROB/STQ/PC/address/branch/source remain validation or transport context, not
  identity. This closes only the immediate same-token BOOM-store transport
  candidate. One live negative now advertises the fields but omits the BOOM
  producer and observes explicit invalid/zero metadata at manager A/D while
  the store transaction and readback still complete; attribution remains
  unknown and is not promoted. ADR-0046 removes further epoch/reset/stale/
  duplicate/exhaustion, stripped/malformed, replay/source-reuse/backpressure,
  non-CPU exclusion, BOOM-load/Rocket token parity, and post-A rollback cases
  from the T-0042 critical path. Retain the existing evidence without promoting
  semantic initiator identity. T-0106 owns that hardening after T-0044 survival
  or a separately accepted product requirement. The controlled CPU paths are
  now connected to the ADR-0043 resource boundary for the bounded small-start
  slice. T-0044 fairness preregistration is next; do not start another deferred
  token case first.
- [x] **T-0043** Implement Miroirs Graph Compiler structural validation and
  Pavane Semantic Oracle differential semantic checking. Miroirs now admits
  only the canonical owned compiler slate and fully bound proposal before any
  backend call; Pavane independently executes the bounded deterministic integer
  reference and requires exact baseline/candidate agreement without using
  latency or Experience as semantic authority.
- [ ] **T-0044** Compare static, elastic, stream, and hybrid Graph Execution
  Subsystem organizations against matched in-order and conventional OoO
  baselines. Hold ISA workload, cache/memory model, functional resources, and
  correctness constant where possible; report frontend, rename/ROB/issue/LSU,
  graph-ready/token/configuration, cycles, traffic, area, timing, and energy
  proxies separately. Admit only mechanisms that passed the T-0057 source and
  IP-risk review; retain an explicit no-go outcome. The current P0 slice is
  only EXP-0005/EXP-0006's frozen 1/4-fresh-input latency/traffic pilots: static Graph,
  Rocket in-order, BOOM OoO, plus BOOM serialize-dispatch as a diagnostic (not
  an “OoO-disabled CPU”). Primary comparison preserves lawful CPU load reuse
  and reports Graph's extra traffic. VLIW/CGRA, elastic, stream, hybrid,
  energy, synthesis timing, and area remain outside this checkpoint, so pilot
  success cannot close T-0044 or decide go. Fail closed on oracle/resource/
  traffic/accounting/source/config/matrix/window-boundary failure and do not
  decide the RFC-0005 numerical no-go below 64 fresh inputs. EXP-0005's 4x4
  matrix is now sealed and exact across four fresh inputs: Graph/Rocket/BOOM
  execution is 3,073/14,621/21,892 cycles, with 1,536/1,056/1,056 admitted
  transactions. Legal CPU load reuse explains the traffic difference, so the
  bounded execution-latency/traffic pilot is eligible. **Pause before full
  expansion:** implement one same-meaning install-once lifecycle that feeds
  repeated fresh inputs to every candidate without simulator reboot; do not
  start 16/64/256 collection until that single boundary passes. T-0044 stays
  open for the full matrix, energy, synthesis timing, and area. A dedicated
  repeated-only implementation now loops ordered inputs in one Graph/CPU
  simulator process and emits actual output plus per-invocation accounting;
  it is pre-data and must not be treated as evidence. EXP-0006 is frozen; run
  only its 1/4 commissioning matrix next. Fail closed or pause if CPU-local versus
  Graph-testbench input generation prevents a same-meaning staging/end-to-end
  boundary. The first CPU attempt failed before measurement because repeated C
  needed an initialized private stack; the minimal main-RAM stack fix is now
  re-frozen and commissioning must rerun under a new RUN-ID.
  The rerun exposed 580 owned-word loader writes in the first installation;
  bind the new explicit installation read/write fields in a replacement freeze
  rather than subtracting them implicitly, then rerun the complete matrix. The
  replacement freeze is complete; only the new RUN-ID remains.
  Commissioning then exposed a BOOM `tee`/immediate-read visibility race despite
  a complete outer raw log; freeze the explicit log synchronization and repeat
  the full matrix rather than promoting the replayed log. The replacement
  freeze is complete.
  The synchronized in-container reader still saw a partial diagnostic stream;
  freeze the completed-outer-raw collector boundary and rerun. Do not promote
  either externally replayed failed log. The replacement freeze is complete.
  The outer file then grew after Docker CLI return; freeze the bounded required-
  marker drain wait and rerun the complete matrix. The replacement freeze is
  complete. The next Graph run proved its wrapper was deterministically
  truncating repeated evidence to a 240-line smoke preview; emit the full log
  only in repeated mode, re-freeze that transport fix, and rerun under a new
  RUN-ID. The replacement freeze is complete.
  EXP-0006 RUN-ID `20260814T100000Z-7b6e5df-commission8` now passes the full
  install-once four-member matrix and seals exact 1/4 evidence. Execution
  latency/traffic is eligible, but staging/end-to-end remains ineligible
  because CPU input generation is candidate-local while Graph generation is
  testbench-side. **Pause at this one point:** define and prove a same-meaning
  input-staging initiator boundary before any 1/4/16/64/256 campaign. Do not
  start the 256-input run, secondary ablation, or unrelated T-0044 scope.
  ADR-0047 now accepts the only next implementation: a fixture-owned provider
  that performs the same 324 ordered writes through a phase-exclusive single
  ingress for every candidate, then releases execution once. EXP-0007 is
  allocated and the provider/held-request/release/rearm boundary plus
  fail-closed parser tests are implemented. Frozen EXP-0007 account-one and
  account-four commissioning passes the complete matrix and resolves the
  staging fairness point. Its bounded decision is `advance`: preregister the
  full 1/4/16/64/256 campaign separately before collecting more data. Do not
  reuse pre-freeze debug values, count deterministic replays as fresh samples,
  or close T-0044 before the remaining organizations and physical metrics.
  EXP-0008 is now allocated and its separate full-campaign collector implements
  one 256-input session with nested 1/4/16/64/256 paired analysis. Its
  implementation authority, exact manifest, RUN-ID, identity expectations,
  100,000-resample estimator, RFC-0005 64-input latency/break-even rules, and
  operational limits are frozen before data. Run only that complete matrix;
  EXP-0007 remains immutable. The first EXP-0008 attempt completed all primary
  sessions but the diagnostic serialize command reached the runner's fixed
  3,600-second timeout at invocation 115. Preserve its failed raw seal and do
  not reuse its RUN-ID. The operational-only recovery authority and manifest
  are now frozen; import all three completed primary logs by exact hash without
  rerunning them, and recollect only the diagnostic with 10,800 seconds. This
  recovery is complete and EXP-0008 returns
  `advance-partial-latency-traffic`: the 64-input latency no-go and break-even
  rules do not fire. Keep T-0044 open. Next work must separately preregister
  the energy proxy, matched synthesis timing/area, IP disposition, and missing
  VLIW/CGRA, elastic, stream, and hybrid organization evidence; do not infer
  those passes from latency/traffic. ADR-0048 now fixes the next bounded step
  as partitioned Graph/Rocket area/timing screening before any whole-system
  energy claim. EXP-0009's toy-only pinned Yosys/OpenSTA/Sky130 toolchain
  commissioning passes without candidate data. Commit the implementation
  authority for the now-owned export/sealed-evidence/report path is
  `f487259...d466`; exact generated RTL and the machine-readable Stage-B
  manifest are frozen without candidate synthesis. Collect only the complete
  Graph/Rocket partition matrix, retaining any failed RUN-ID. Keep dynamic
  energy paused until
  fallback, common-memory, integration, clock, and lifecycle activity are all
  included.
  The first Graph RUN-ID is a sealed pre-Yosys operational failure; freeze the
  log-handoff-only recovery authority/manifest before a distinct reattempt.

- [ ] **T-0106** Harden CPU-owned semantic attribution only after the candidate
  survives T-0044 or a separately accepted product requirement introduces
  untrusted or concurrent initiators. Preserve ADR-0045's implementation-owned
  token/epoch and fail-closed semantics; cover reset with outstanding work,
  stale/duplicate/exhausted and multi-live tokens, replay/source reuse,
  post-request exception and post-A rollback, arbitrary ELF identity, general
  loader/FESVR/Debug exclusion, and Rocket/BOOM lifecycle parity. This task is
  explicitly not a prerequisite for the controlled-run T-0042/T-0044 slice.

## Research backlog

- [ ] **T-0050** Tail-preserving bounded coreset experiment.
- [ ] **T-0051** Negative-transfer-aware retrieval and calibrated abstention.
- [ ] **T-0052** Graph/hardware contrastive representation.
- [ ] **T-0053** Multi-policy periodic review of stale local optima.
- [ ] **T-0054** Cross-hardware transfer with a small target measurement budget.
- [ ] **T-0055** ANN/near-memory profile before FPGA acceleration.
- [ ] **T-0056** FPGA Experience retrieval/filter prototype only after access
  patterns and schemas stabilize.
- [x] **T-0057** Define and test the RFC-0001 native operation/dependency/effect/
  object graph schema before further tool-level optimization work. Phase A now
  records the direct-prior-art matrix for OoO/EPIC/TRIPS/WaveScalar/DySER/CGRA
  and preliminary patent/IP triage in
  `docs/research/reviews/2026-08-11-T-0057-native-graph-prior-art-matrix.md`.
  RFC-0005 and ADR-0039 accept, for repository-owned RTL simulation only, an
  operation-level,
  fixed-latency, statically scheduled five-point-stencil region, internal
  simulator interface, disjoint read/private-output objects, RV64IM fallback,
  exact oracle, complete overhead accounting, and pre-registered no-go rule.
  The 2026-08-12 feature-to-document review records claim locators and excluded
  mechanisms but creates no patent clearance. T-0042 now supplies exact
  compiler/validator and RTL-versus-independent-oracle functional validation,
  including cancellation and restart. This closes the contract-definition
  task only. T-0044 owns comparison against sequential, in-order, conventional
  OoO, and relevant VLIW/dataflow controls under RFC-0004; do not infer CPU
  claims from this functional smoke or the T-0103 process-level showcase.
- [ ] **T-0058** Evaluate reuse-weighted optimization ROI and hot/warm/cold/
  archival budget classes.
- [ ] **T-0059** Build a reproducible small-Transformer Experience demo only
  after the real measurement boundary and honest holdouts exist.

## Explicitly not next

- a production LLM advisor;
- a GAN/Adversarial Autoencoder before meaningful real evidence exists;
- an ASIC before software access patterns stabilize;
- claims that general-purpose OoO can be removed;
- broad framework integration without one pinned reproducible workload.
