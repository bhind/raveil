# Raveil TODO

Last updated: 2026-08-09

Checkboxes are execution state, not priority. Every material task has a stable ID.

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
- [ ] **T-0080** Complete Gate 1 evidence collection: run and remotely verify an
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
- [x] **T-0082** Keep recorded compile/prepare commands logical and portable.
  A completed independent run initially failed sealing because the native
  compile tuple contained absolute bundle paths; record repository-relative
  source and bundle-relative output paths while retaining the actual tool and
  flags, and normalize only the still-mutable command record before sealing.

## Next — turn Sonatine Microkernel seed into a real minimal microkernel slice

- [ ] **T-0010** Parse or deliberately constrain the QEMU device tree instead of
  silently assuming all platform properties.
- [ ] **T-0011** Implement Sv39 address spaces and explicit kernel/user mappings.
- [ ] **T-0012** Move `init` to U-mode.
- [ ] **T-0013** Implement context switch between `init` and `idle`.
- [ ] **T-0014** Make the CLINT timer drive preemption.
- [ ] **T-0015** Add blocking IPC semantics and capability delegation tests.
- [ ] **T-0016** Add fault tests for stale capability generation, rights escalation,
  invalid endpoint, user fault, and timer re-entry.
- [ ] **T-0017** Add a minimal VFS plus RamFS/initramfs after the isolation and
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

Experience gate: the EXP-0003 fixed-C and pinned-TVM criteria in ROADMAP all
pass, immutable remote bundles verify, and an independent run reaches the same
conclusion. A fixed-C/TVM contradiction keeps the Gate open.

## Later — connect the two tracks

- [ ] **T-0030** Define shared `JobDescriptor` and `CompletionRecord` schemas.
- [ ] **T-0031** Add Sonatine Microkernel submission/completion rings and object table.
- [ ] **T-0032** Send measured completion telemetry into append-only Experience.
- [ ] **T-0033** Implement shadow execution, commit, cancellation, and rollback.
- [ ] **T-0034** Enforce Program/Graph/Data/Experience write authorities.

## Later — compiler and adaptive execution

- [ ] **T-0040** Import one real tensor workload through a pinned IREE/MLIR path.
- [ ] **T-0041** Define Raveil-owned `GraphVariant`, `MemoryPlan`, and
  `OptimizationProposal` schemas.
- [ ] **T-0042** Bootstrap a mapper/simulator adapter without leaking upstream types.
- [ ] **T-0043** Implement Miroirs Graph Compiler structural validation and Pavane Semantic Oracle differential
  semantic checking.
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
