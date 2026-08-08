# Raveil TODO

Last updated: 2026-08-08

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
  credential boundary, and completion-marker-last behavior. A real Drive sync
  remains EXP-0003 evidence, not an implementation acceptance claim.
- [x] **T-0066** Add the read-only Raveil Librarian agent and context-routing
  skill that returns a minimal authoritative reading packet without deciding
  tasks, gates, or claims.
- [x] **T-0067** Require post-Gate-0 work branches and document the lowercase
  `<type>/<record-id>-<short-slug>` naming convention.

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
- [ ] **T-0022** Compare cold prior, full-history nearest neighbor, bounded
  Experience, FIFO, and reservoir retention.
- [x] **T-0023** Add lineage, shape, working-set/memory, and
  operator-composition holdouts.
- [ ] **T-0024** Report HCR, NTR, Coverage, calibration, measurement budget,
  retrieval latency, active-memory size, and cold-evidence size separately.
- [ ] **T-0025** Preserve and analyze failed and boundary variants, not only winners.

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
