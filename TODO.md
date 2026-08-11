# Raveil TODO

Last updated: 2026-08-11

Checkboxes are execution state, not priority. Every material task has a stable ID.

## Delivery line — active GNU/Linux userspace MVP

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

- [ ] **T-0092** Extend the existing bounded Sonatine U-mode shell with an
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
- [ ] **T-0042** Bootstrap a mapper/simulator adapter without leaking upstream types.
- [x] **T-0043** Implement Miroirs Graph Compiler structural validation and
  Pavane Semantic Oracle differential semantic checking. Miroirs now admits
  only the canonical owned compiler slate and fully bound proposal before any
  backend call; Pavane independently executes the bounded deterministic integer
  reference and requires exact baseline/candidate agreement without using
  latency or Experience as semantic authority.
- [ ] **T-0044** Compare static, elastic, stream, and hybrid Daphnis Execution Subsystem organizations.

## Research backlog

- [ ] **T-0050** Tail-preserving bounded coreset experiment.
- [ ] **T-0051** Negative-transfer-aware retrieval and calibrated abstention.
- [ ] **T-0052** Graph/hardware contrastive representation.
- [ ] **T-0053** Multi-policy periodic review of stale local optima.
- [ ] **T-0054** Cross-hardware transfer with a small target measurement budget.
- [ ] **T-0055** ANN/near-memory profile before FPGA acceleration.
- [ ] **T-0056** FPGA Experience retrieval/filter prototype only after access
  patterns and schemas stabilize.
- [ ] **T-0057** Define and test the RFC-0001 native dependency/effect/object
  graph schema against a sequential and VLIW-like baseline.
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
