# Raveil TODO

Last updated: 2026-08-26

Checkboxes are execution state, not priority. Every material task has a stable ID.

## Start timing phases

This table, together with each task's own trigger text, governs when unfinished
work may start. A branch, patch, local modification, or previously spent effort
does not promote a task. See `docs/guides/TASK-START-PHASES.md`.

| Phase | Meaning and start rule | Unfinished tasks |
|---|---|---|
| **P0 — immediate** | At most two explicitly independent delivery lanes may run under ADR-0061 and ADR-0065. | T-0128/S01 |
| **P1 — next** | Start only after its named P0 dependency passes. | None selected. |
| **P2 — result-conditioned** | Start only if the named research result survives or a separately accepted product requirement triggers it. | T-0106 |
| **P3 — future planned** | Retained planned work, but not scheduled. The Project Manager must select and promote one after P1 rather than running these in parallel by default. | T-0104, T-0100, T-0093, T-0091, T-0018 |
| **P4 — optional/triggered** | No default start date. Start only when the task's explicit operational, research, security, scale, contributor, or equipment trigger occurs. | T-0063, T-0068, T-0069, T-0071, T-0073, T-0025, T-0050, T-0051, T-0052, T-0053, T-0054, T-0055, T-0056, T-0058, T-0059 |

Promotion into P0 requires a dated log entry naming the satisfied trigger,
dependencies, owner, stop rule, file allowlist, and displaced or completed P0
task. ADR-0061 permits at most two independently acceptable implementation
items when their task, files, artifacts, tests, and evidence are disjoint.
Project Manager record integration and PR merge remain serial. Read-only
review and failure preservation do not consume the two-item delivery limit.

## Project entry point

- [ ] **T-0128** Turn the accepted three-Graph device capability into a small,
  serial operator submission path without reopening the ABI, RTL, opcode, or
  general-Graph boundary. Parent T-0128 is not an active mutation item and has
  no aggregate SP. Promote only one independently acceptable child slice at a
  time, re-estimating after each canonical merge.

  S01 is the sole P0 under real Issue #36 and branch
  `feat/t-0128-s01-operator-admission`, with Initial and Current SP 3. It adds
  `python3 -m raveil graph-device submit --graph <canonical-json> --seed N` and
  emits a deterministic `raveil.graph-device-submission/v1` envelope only for
  the three byte- and program-identity-bound T-0123 descriptors. Absolute,
  escaping, symlinked, unknown, mutated, malformed, extra-field,
  duplicate-identity, and invalid-seed requests fail closed. The command does
  not execute RTL, invoke Docker or Verilator, publish Data, write a receipt,
  or authorize S02.

  The Systems Implementer owns only `raveil/cli.py`,
  `raveil/graph_device_submit.py`, and `tests/test_graph_device_submit.py`;
  canonical records remain Project Manager-owned. PM and independent Tester
  verification pass 35 combined submit/DAG/Playable tests, all three canonical
  CLI admissions, representative exit-2 rejection paths, and `git diff
  --check`. Evidence is `host-functional` admission only. S02 remains
  unallocated until S01 merges and is re-estimated from canonical authority.
  Stop on ABI, Graph JSON, compiler/oracle, Chisel/Verilator, T-0044, opcode,
  selector, window, scheduler, Experience-authority, filesystem-authority, or
  arbitrary/general-Graph expansion.

- [x] **T-0124** Remove the mutable shared BOOM simulator tag from ordinary
  RTL execution after an independent replay silently rebuilt
  raveil-boom-functional-sim:v1. Keep the explicit image build separate and
  tagless. Publish each successful local runtime OCI-index receipt under its
  exact digest without replacing an earlier receipt, use only a validated
  current pointer for local convenience, and fail closed unless the descriptor
  digest/media type/size, BuildKit index-to-linux/amd64-payload attachments,
  Config view, RootFS layer list, platform, and exact runtime image all agree.

  Migrate the complete eleven-runner consumer closure, not only the runner
  that exposed the incident. Preserve the stable payload manifest
  9009a923...fdaf822 as a payload identity rather than mislabelling it as the
  provenance-bearing runtime OCI index. Ordinary runners may not build, tag,
  pull, or execute the former shared tag. The explicit bootstrap may resolve
  the already pinned base dependency; post-bootstrap simulation runs use no
  network. The accepted result is local rtl-simulation-functional
  reproducibility hygiene only. It does not reinterpret a prior experiment,
  create performance or physical evidence, or make a local BuildKit receipt
  portable to another host.

- [x] **T-0122** Deliver the smallest simulation-first Static Graph device MVP
  on current main. Reconstruct, rather than merge wholesale, the previously
  clean-replayed T-0113 prototype from commit `f5ea057`. One command must bind
  the canonical bounded-stencil descriptor to a task-neutral, versioned,
  fixed-width, little-endian, pointer-free device artifact; stage 324 words
  through a transport-neutral runtime; start and finitely poll the Verilator
  device; read 256 private output words only after output-valid; and validate
  every word plus checksum with the independent Pavane oracle. Two normal
  inputs, cancellation with no publication, and reset/restart must pass.

  Keep the implementation in new task-neutral contract/runtime/runner/test
  files. Existing `static_region`, `simulation_adapter`, Static Graph core,
  scratchpad, and T-0044 files are read-only dependencies for this slice.
  Receipts bind artifact, ABI, source, oracle, simulator, input, and environment
  identities and remain `rtl-simulation-functional`. Exclude dynamic schedule
  installation, AXI, UIO, Vivado, DTBO, bitstream, DMA, IRQ, kernel modules,
  FPGA execution, latency comparison, area, energy, and product claims.

  The task-neutral `raveil.graph-device-abi/v1`, artifact/finalizer,
  `DeviceTransport` runtime, Verilator adapter, and one-command runner now pass
  30 focused tests plus primary and independent clean Docker/Verilator replay.
  Both successful seeds stage 324 words, finish in 3,072 finite status polls,
  expose 256 private words identical to Pavane, and bind full hashes in an
  append-once receipt. The cancel seed exposes no output, and reset/restart
  passes. This closes only the bounded `rtl-simulation-functional` MVP; all
  physical and performance exclusions above remain in force.

- [x] **T-0123** After T-0122 is accepted on current main, reconstruct the
  bounded generality ladder from the clean-replayed T-0114 donor commits
  without importing their stale records. First prove that a generated immutable
  schedule is transaction-trace equivalent to the fixed control; then admit
  bounded affine shape/stride variants; finally run at least two distinct
  acyclic DAGs over `LOAD_U32`, `ADD_U32`, and `STORE_U32` on one executor RTL
  and the unchanged T-0122 device ABI, with separate independent oracles and
  fallback parity. Stop before installable general graphs, variable-latency
  issue, CGRA/VLIW expansion, AXI/KV260 work, or a performance campaign.

  The G2 clean-replay donor `c3a5eda` is implementation reference only; its
  stale T-0114 task names and records are not authority. S01 is promoted to P0
  from current-main commit `12227f5` with one live Project item, one clean
  `feat/t-0123-bounded-generality` worktree, one Chisel mutation owner, and a
  five-SP warm estimate. Its mutation allowlist is
  `hardware/chisel/StaticStencilRegion.scala`,
  `hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala`,
  `hardware/chisel/graph_device_verilator.cpp`, the two new
  `run-graph-device-generated-schedule*` runners,
  `raveil/graph_device_schedule.py`, and
  `tests/test_graph_device_schedule.py`. Existing T-0122 ABI, runtime,
  artifact compiler, oracle, scratchpad, and every T-0044 file are read-only.
  S01 must prove exact generated-schedule equivalence for two complete traces,
  a strict-prefix cancelled trace, and Pavane-matched store data while keeping
  the T-0122 ABI unchanged. S02 later completed; S03's serial promotion is
  recorded below.

  S01 now passes at implementation commit `f44d444`. The task-neutral schedule
  compiler emits an immutable ten-entry schedule and six-transaction template;
  simulation-only `requestFire` observation records exactly 1,536 accepted
  scratchpad requests for each successful seed and a nine-request strict
  cancellation prefix. Both complete traces and all store data match the
  descriptor-derived schedule and Pavane. The unchanged ABI, artifact, source,
  input, oracle, private output, simulator, and environment identities are
  bound into the append-once schedule receipt. Primary and independent exact-
  commit runs reproduce receipt SHA-256
  `f91582420c49b88465b6215a61d1937b9448803f7b7fe76e3c8a5855c111e232`.
  This completes S01 only: the schedule is observed but not consumed by the
  executor. S02 remains P1 until its separate current-main allowlist,
  installation boundary, acceptance packet, and live Project item are fixed.

  S02 is now promoted from canonical commit `84c926b` under ADR-0063 and live
  Project item `T-0123/S02`. Its sole mutation owner may edit only
  `contracts/graph_device_install_abi_v1.json`,
  `hardware/chisel/GraphDeviceAffineConfigInstaller.scala`,
  `hardware/chisel/StaticStencilRegion.scala`,
  `hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala`,
  `hardware/chisel/graph_device_affine_runtime.h`,
  `hardware/chisel/graph_device_affine_runtime.cpp`,
  `hardware/chisel/graph_device_verilator.cpp`, the two new
  `run-graph-device-affine*` runners, `raveil/graph_device_affine.py`, and
  `tests/test_graph_device_affine.py`. The execution ABI, T-0122 runtime and
  artifact compiler, S01 evidence, scratchpad, and every T-0044 path remain
  read-only. Acceptance requires baseline and compact affine profiles on one
  RTL image, independent oracle and fallback parity, exact transaction/store
  equivalence, zero inactive output, fail-closed installation/lifecycle/hash
  negatives, cancellation and reset/restart, deterministic exports, and one
  append-once RTL-simulation receipt. S03 remains serial and is promoted only
  by the separate packet below.

  S02 now passes at implementation commit `b9b7d88`. The same RTL and unchanged
  execution ABI run baseline 16-by-16 and compact 8-by-8 profiles installed
  through the separate ABI. Primary and independent runs reproduce affine
  receipt SHA-256
  `58d788bfcddf85a5c85236b99e8fc79d3d05659464936f19ead4bccda936e955`;
  77 scoped regressions and the unchanged S01 runner pass. Partial, order,
  duplicate, digest, and busy negatives fault without mutation; Pavane,
  fallback, transaction/store traces, cancellation, zero inactive tail, and
  reset/restart checks pass. The allowlist expanded only to update the stale
  `tests/test_static_region.py` assertion. Initial SP remains 8 and Current SP
  is 13 after two incomplete low-agent packets, PM recovery, and independent
  evidence closure. This completes S02 only. T-0123 and S03 remain open, and
  no performance or physical claim follows.

  S03 is promoted from canonical PR #25 merge commit `27870f0` under
  ADR-0064 and live Project item `T-0123/S03`. It preserves the execution and
  affine-install ABI files byte-for-byte and adds a separate 32-word program-
  installation ABI. Three repository-owned external Graph JSON files describe
  baseline five-point, compact horizontal-three-point, and baseline vertical-
  three-point DAGs. A task-neutral compiler must topologically lower all three
  without name-based semantics; one sequential executor RTL interprets at most
  16 `LOAD_U32`/`ADD_U32`/`STORE_U32` instructions over eight value registers.

  The sole mutation owner may edit only
  `contracts/graph_device_program_install_abi_v1.json`, the three files under
  `contracts/graph_device_dags/`,
  `hardware/chisel/GraphDeviceProgramInstaller.scala`,
  `hardware/chisel/StaticStencilRegion.scala`,
  `hardware/chisel/chipyard-overlay/RaveilStaticStencilCore.scala`,
  `hardware/chisel/chipyard-overlay/RaveilStaticStencilTLClient.scala`,
  `hardware/chisel/graph_device_dag_runtime.h`,
  `hardware/chisel/graph_device_dag_runtime.cpp`,
  `hardware/chisel/graph_device_verilator.cpp`, the two new
  `run-graph-device-dag*` runners, `raveil/graph_device_dag.py`,
  `tests/test_graph_device_dag.py`, and `tests/test_static_region.py`.
  Existing execution and affine ABI files, T-0122 runtime/compiler, S01/S02
  evidence and tests, scratchpad, Pavane inputs, and every T-0044 manifest and
  evidence path remain read-only.

  Acceptance requires three deterministic external Graphs on one byte-
  identical RTL export, unchanged existing ABIs, direct-DAG oracle and generic
  compiled-program fallback parity, exact transaction/store traces, compact
  inactive-tail zero, cancellation without publication, factory reset/restart,
  fail-closed graph/program/install/source/receipt negatives, and primary plus
  independent clean replay of one append-once receipt. Initial and Current SP
  are 21. This is an AI delivery-risk estimate: the warm range is 3--6 hours
  editing, 1.5--3 hours verification, 0.5--1 hour Tester, and 0.5--1 hour PM
  integration, or 5.5--11 AI working hours at medium confidence. No arbitrary
  Graph, performance, resource, physical, FPGA, ASIC, or silicon claim follows.

  The initial low Chisel owner returned two partial packets despite the frozen
  full-packet requirement. Its second `run-graph-device-dag.sh` exited zero by
  compiling only the five-point JSON and did not elaborate or execute RTL.
  Core, TLClient, tests, receipt, and the three-Graph matrix were missing. The
  PM rejected the result, recorded a repeated-root-cause HCI, and obtained
  explicit owner approval to take sole mutation ownership. The 16-path
  allowlist, both read-only ABI boundaries, 21 SP, acceptance, and non-claims
  are unchanged; no partial packet is completion evidence.

  S03's primary implementation/evidence candidate is commit `9682f783`.
  Its finalizer correction removes the non-contractual busy-mutation zero-count
  requirement: this segment may be empty or a strict correct prefix of the
  first invocation, and its observed count is receipt-bound. The ignored
  `run.mAgriX` primary receipt SHA-256 is
  `093aa3ba723bca69f3e26f5e1b960d53bfdbb00a2cb708b1bf4a01cb5b221942` with
  evidence class `rtl-simulation-functional` and `performance=not-measured`.
  It proves only the frozen three-Graph scope. Independent exact-head review
  approved the candidate, and PR #26 merged it at canonical commit `0cd2c890`.
  T-0123 is complete at this bounded evidence class; it does not complete any
  broader generality, performance, resource, physical, FPGA, ASIC, or silicon
  boundary.

- [x] **T-0125** Present the accepted bounded Graph-device capability as one
  operator-readable command without changing its execution or evidence
  boundary. Reuse the T-0123/S03 runner and append-once receipt unchanged, then
  render the three external Graph identities, affine shapes and strides,
  instruction counts, program hashes, one shared RTL identity, and direct-
  oracle/generic-fallback/RTL agreement. Contrast this only with the earlier
  fixed five-point baseline capability: the improvement is installing three
  frozen programs on one executor image without Graph-specific RTL
  regeneration, not a speed, area, energy, or generality result.

  The mutation owner is limited to a new task-neutral presentation module, a
  new wrapper command, its focused tests, and the relevant Chisel README. The
  Chisel RTL, three accepted ABIs, external Graph JSON, T-0123 compiler,
  runner, receipt schema, raw evidence, and every T-0044 path are read-only.
  Acceptance requires deterministic fail-closed receipt rendering, exactly
  three distinct programs, one nonempty shared RTL identity, successful
  oracle/fallback/RTL status, explicit `performance=not-measured`, one clean
  one-command RTL replay, and independent review. Initial and Current SP are 5;
  the warm AI estimate is 45--90 minutes editing, 30--60 minutes verification,
  20--40 minutes Tester replay, and 30--60 minutes PM integration, or 2.1--4.2
  AI working hours at medium confidence. Stop on ABI or RTL mutation, receipt
  weakening, identity ambiguity, arbitrary-Graph or opcode expansion, or any
  performance/resource/physical claim.

  Two low-owner packets failed the same acceptance/reporting boundary. The
  second packet still omitted the required negative matrix after claiming it
  was present, so HCI-07 preserved the incomplete state and stopped that owner.
  The repository owner then explicitly selected owner transfer: Jitro assumed
  the four-file mutation without changing the task scope, 5 SP, read-only
  ABI/RTL boundary, evidence class, or non-claims. Issue #27 carried the
  complete ADR-0065 packet through its accepted lifecycle.

  The implementation candidate is locally verified. Twenty focused Playable
  tests cover valid presentation, exact marker/path and repository containment,
  symlink rejection, receipt regeneration, artifact/RTL/trace/output/source
  substitution, lifecycle errors, and deterministic rendering. The combined
  Playable, DAG, and static-region suite passes 39 tests. PM run `run.tJxhWF`
  and independent run `run.LpVgAC` each present the accepted receipt SHA-256
  `093aa3ba723bca69f3e26f5e1b960d53bfdbb00a2cb708b1bf4a01cb5b221942`,
  shared RTL aggregate
  `64524cdc6b9f0365749f6f5925981d859a3b0b6e1c1b7c959ae8dbfddf58510f`,
  and three Graph rows with RTL/oracle/fallback PASS. Independent low-agent
  exact-head review found no blocker, major, or minor defect and was recorded
  on PR #31. The PR merged as canonical commit `770a299b`; Issue #27 closed.
  This completes only the bounded operator presentation at
  RTL-simulation-functional evidence, with performance explicitly not measured.

- [x] **T-0126** Make GitHub Project #1 an executable work queue instead of an
  after-the-fact DraftIssue ledger. ADR-0065 requires every newly active P0
  slice to use a real `work-item` Issue, stable T-ID branch, named owner,
  visible execution fields, and checked `In Progress`/`Review`/closed/`Done`
  lifecycle. Reconcile `AGENTS.md` with ADR-0061 so at most two Implementers may
  own truly disjoint mutation packets while PM records, acceptance, and merge
  remain serial. Add a dry-run-default queue CLI and focused fail-closed tests.

  T-0125 was converted in place to real Issue #27 and retained all Project
  fields; T-0126 uses real Issue #28. Historical Draft cards remain untouched.
  The live audit passed with one active delivery item after T-0125 was moved to
  `Blocked`. Seventeen unit tests cover valid two-lane state, active Drafts,
  complete independence packets, missing cards, WIP overflow, full child-slice
  identity, transition preflight/order, task/lifecycle/branch mismatch, visible
  fields, and PR closing references. This is host-functional governance only; it changes no
  Graph, research, performance, FPGA, ASIC, silicon, or gate result.

- [x] **T-0127** Enforce ADR-0065 in every repository agent role. All ten
  `.codex/agents` role definitions require the role-appropriate real-Issue,
  full-T-ID, Project-state, ownership, allowlist, acceptance, evidence,
  stop-rule, and non-claim checks. Mutation roles refuse unbound edits;
  read-only roles cannot consume mutation WIP; Tester cannot edit tracked
  files; and only the Project Manager may apply queue transitions. The shared
  task-governance skill repeats the kickoff, progress, and closeout checks.
  Agent-boundary regression tests enumerate every role so a new or weakened
  role fails closed. The queue pre-start seam now permits a `Ready` item to omit
  `Parent T-ID` until `start` writes all metadata before status, while still
  rejecting a wrong populated identity. Twenty-three focused tests, the record
  checker, and the live Project audit passed. PR #34 merged as canonical commit
  `3c7cbc9`; Issue #32 is closed and its Project item is `Done`. This is
  host-functional governance only; it changes no Graph, research, performance,
  FPGA, ASIC, silicon, or gate result.

- [x] **T-0110** Define continuous execution and Human-confirmation incidents
  as repository-wide agent workflow. Once an owner authorizes a bounded task,
  local investigation, assigned edits, atomic commits, tests, review, record
  reconciliation, and the next accepted slice continue without ceremonial
  acknowledgement. Require human confirmation only for ADR-0051's exhaustive
  authority/scope, irreversible experiment/gate, destructive/remote, evidence-
  ambiguity, user-work, cost/credential/legal-risk, repeated-blocker/resource,
  and material-design-fork incidents. Add executable assertions for the PM and
  workflow markers. This operational rule changes no implementation P0,
  experiment result, performance claim, or remote-publication authority.

- [x] **T-0109** Reorganize the root `Components and boundaries` summary and
  the canonical architecture component map after read-only comparison with the
  executable tree. Separate the portable owned contract/authority thin waist,
  tensor and Command Graph frontends, advisory proposal/Experience paths,
  guarded orchestration, execution adapters, Sonatine's optional privileged
  profile, host transport, and RTL research controls. State explicitly which
  named components are intended responsibility domains rather than complete
  implementations. Use the formal `code name + general function` form for all
  project components and register Couperin Contract Core, Chloé Graph
  Orchestrator, Alborada Measurement Observatory, Rapsodie Host Bridge, and
  Tzigane Hardware Research Laboratory for previously unnamed domains. The
  owner reviewed the exact English table and approved direct push on
  2026-08-15. This documentation-only clarification preserves ADR-0025,
  ADR-0027, ADR-0049, all experiment outcomes, and the current roadmap gates;
  it does not displace T-0044 or create a performance, hardware, or security
  claim.

- [x] **T-0108** Replace the stale root README with a current, evidence-bounded
  project entry point. Explain Raveil as an Experience-guided Graph
  compiler/runtime across replaceable CPU, CGRA, FPGA, NPU, and future ASIC
  backends; separate the implemented Native, Experience, Sonatine, and RTL
  slices from the intended integrated loop; state the fixed-C negative result
  and current non-claims; and route readers to canonical records. Preserve
  ADR-0049's CGRA non-reinvention boundary and make the Experience-driven
  software/hardware feedback loop an unvalidated research hypothesis. The
  draft received human review and push approval on 2026-08-15. This
  documentation-only task does not displace T-0044 or authorize
  implementation, measurement, or a new research claim.

## Project operations

- [x] **T-0116** Establish a repository-linked GitHub Project weekly sprint
  loop with a stable-T-ID Kanban board, calculated and reviewable Fibonacci
  story points, an eight-point solo pilot capacity, WIP limit two, a required
  runnable increment and demo, and a weekly retrospective. Keep TODO, ROADMAP,
  ADR, RFC, EXP, and executable evidence authoritative; the private Project
  coordinates but cannot promote claims or gates. Provide seven-day
  Iterations and review fields, and seed S-0001 with the already-active bounded
  BOOM negative plus an unpointed review/retro item. The corrective closeout also
  populates an ordered Product Backlog with independently accepted work slices,
  owner and support roles, dependencies, initial/current SP, priority, committed
  or forecast sprint, forecast date and confidence, Definition of Ready/Done,
  and an explicit one-human integration-capacity assumption. Parent epics carry
  no SP so child work is not counted twice. A canonical-authority audit then
  corrected the BOOM item from `T-0042/S01` to a bounded `T-0106/S01` evidence
  carry-in: T-0042 remains complete, the carry-in does not activate the rest of
  conditional T-0106, and later token-hardening slices remain unscheduled.
  The replacement plan instead refines the accepted T-0044 integrated-physical
  boundary into T-0044/S08. It was initially forecast for S-0003, then moved as
  one eight-point slice into S-0001 at the calibrated 21-SP warm ceiling.
  ADR-0057 later hardens integration operations: dedicated branches may be
  pushed and opened as PRs for already authorized bounded work, but `main`
  accepts changes only through a PR. ADR-0058 adds standing authority to merge
  immediately after the PM verifies that the PR is complete, mergeable, and
  free of every ADR-0051 Human-confirmation incident.

- [x] **T-0118** Recalibrate weekly execution around AI role lanes rather than
  treating eight SP as the full capacity. Preserve eight SP as an
  under-utilization lower-bound check, set a provisional committed capacity of
  13 SP and a warm stretch range of 13--21 SP, and preserve Initial SP while
  using Current SP only as relative AI delivery risk. Forecast from observed
  accepted-slice cycle time, role packets, resource use, and warm/cold edit,
  verification, and serial PM integration ranges. Keep delivery WIP two with
  one coherent low-reasoning
  mutation owner, one low-reasoning Tester, at most two read-only reviewers,
  medium Librarian routing, high PM/risk review, and milestone-only high
  Researcher work. Add a dedicated low-reasoning Chisel implementer, executable
  role-tier tests, Project AI estimate/cycle/tier/packet/resource fields, and
  ADR-0059. Recalibrate the 13--21 SP band after two closed Sprints without
  treating agent lanes as additive FTE. This changes no implementation P0,
  evidence class, EXP conclusion, or research/hardware gate.

- [x] **T-0119** Enforce a strict weekly Codex usage cost guard independently
  of Sprint SP. Accept only current telemetry for the 10,080-minute weekly
  window, calculate remaining as 100 minus used percentage, permit exactly
  five percent cautiously, and pause new tasks, subagents, long jobs, remote
  updates, and merges below five percent. Fail closed for new costly work when
  telemetry is unavailable or unverifiable, preserve the smallest safe receipt,
  and notify the owner. Do not consume reset credits, purchase capacity, change
  service plans, or bypass the guard without separate explicit authority. This
  operational invariant changes no P0, evidence class, EXP conclusion,
  performance claim, or research/hardware gate.

## Playable pillar — Raveil Garden TUI

- [x] **T-0117** Build the first read-only Raveil Garden TUI on ordinary host
  ARM64/x86-64. Render one strictly validated graph snapshot, node/dependency
  structure, variants, evidence labels, and runnable demo commands with bounded
  keyboard navigation plus explicit empty/error states. Reuse existing owned
  schemas and authority boundaries; the TUI may observe but never execute,
  approve, mutate, promote Experience, close a task, or change a gate. Provide
  a deterministic fixture, host-functional tests, clean terminal acceptance,
  and one command that a hobbyist can run and understand. This is a Playable
  interface task, not T-0093's static directory snapshot and not performance,
  FPGA, ASIC, or silicon evidence. S01 integrated through PR #6 at
  `bb1631109842f85b2a958ebcf30e5ee6a1b5312f`; S02 independently reproduced
  the normal, navigation, empty, and malformed-input paths from that clean
  canonical revision and recorded the terminal transcripts and hashes.

- [x] **T-0120** Build the deterministic multi-pane Garden workspace. Preserve
  T-0117's validated read-only snapshot and authority boundary while adding an
  explicit 72--240-column render contract, a three-pane wide view, a stacked
  narrow view, bounded line lengths, and reproducible host acceptance. Initial
  and Current SP are 5; the owner-priority addition places it in S-0001 above
  the calibrated warm planning band without changing that capacity model.
  Independent verification at `7054e01f384a659774635d333c0e114adf6bd800`
  passed 40 tests, both wide and stacked demos, the record checker, and the
  diff/clean-tree checks. A reviewable 150-column static capture was inspected.
  This remains `host-functional` and `development-non-claim`; it cannot imply
  graph execution, performance, RTL, FPGA, ASIC, or silicon behavior.

- [ ] **T-0121** Reconsider Garden as an actual Linux/macOS TUI after the
  critical path. The dependency-free ASCII CLI remains canonical and usable;
  a local-only directed Graph Canvas draft is preserved at `d59bbc7` but is
  neither independently accepted nor merged. Re-refine the interface and
  dependency policy before resuming, including whether a native TUI library,
  color, focus, and a real graph layout are worth the platform restriction.
  Keep this P2 and unscheduled; do not displace T-0044.

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
  IP-risk review; retain an explicit no-go outcome. EXP-0005/EXP-0006's frozen
  1/4-fresh-input latency/traffic pilots covered static Graph, Rocket in-order,
  BOOM OoO, plus BOOM serialize-dispatch as a diagnostic (not an “OoO-disabled
  CPU”). These completed pilots remain retained evidence. The current P0
  authority is only the read-only S14 physical-input strategy inventory while
  S13 remains Blocked before EXP-0011 allocation or data.
  Primary comparison preserves lawful CPU load reuse
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
  The first Graph RUN-ID is a sealed pre-Yosys operational failure; the
  log-handoff-only recovery authority/manifest is ready and must be committed
  before a distinct reattempt.
  That reattempt reached Yosys and failed on CIRCT block-local variables.
  Commission the physical-only `disallowLocalVariables,disallowPackedArrays`
  emitter without changing runtime RTL, then freeze its exact RTL or pause the
  physical screen if the complete matrix still cannot close.
  The lowered RTL-only export now succeeds and recovery-v2 manifest is ready;
  commit that freeze before a distinct candidate RUN-ID.
  The lowered RUN then failed before synthesis on black-box ordering. Freeze
  the `read -> blackbox -> hierarchy` collector-only recovery and retry once;
  pause if the complete report still cannot close.
  Recovery-v3 is ready; commit it, run one distinct Graph RUN-ID, and pause on
  any further incomplete report rather than adding another recovery loop.
  That final RUN remained incomplete at Yosys module selection. T-0044 is now
  resumed on that one point: a pinned-tool syntax probe proves named-module
  selection, exactly one instance, and verified black-box attributes for both
  common partitions, and the collector
  binds that selection mode into raw identity. Do not run Rocket until
  Graph yields a complete sealed partition report, and do not interpret the
  probe or any failed log as area/timing evidence.
  Recovery-v4 authority `fe7b9f6...3c046` and manifest
  `de396d4f...129d31` are frozen at `caa0983...5fd4c3`; run Graph only from its
  clean descendant.
  Recovery-v4 Graph `run-005` reached mapping, then sealed a post-map integrity
  failure with 212 undriven-wire reports and no candidate datum. Toy diagnostics
  isolate the cause to missing mapped-cell Liberty definitions and unsupported
  OpenSTA collection/report commands. Freeze the library-aware check plus
  supported equivalent Tcl as recovery-v5 before another Graph RUN-ID; do not
  relax `check -assert` or promote diagnostic output.
  Recovery-v5 authority `104c603...bc7ef2` and manifest
  `6973030c...6d051e` are frozen at `f1d62e9...b8abf5`; retry only Graph from
  its clean descendant.
  Recovery-v5 Graph `run-006` sealed Yosys/STA raw files, but derivation rejected
  two implicit OpenSTA common-module black boxes. Do not reuse the contained
  values. Freeze explicit, exactly-once Yosys black-box declarations as
  recovery-v6, rerun Graph, and keep Rocket gated on a complete derived Graph
  result.
  Recovery-v6 authority `d4990d9...4d8cf9` and manifest
  `135f30d6...bc398a` are frozen at `474c1b5...22587c`; run the distinct Graph
  retry only from its clean descendant.
  Graph `run-007` now has a complete sealed partition estimate, but Rocket
  `run-008` failed before synthesis on Yosys 0.27 parsing generated packed
  arrays. Keep the matrix and claims paused. Commit and freeze only the pinned
  upstream `ENABLE_YOSYS_FLOW=1` physical-export path, prove byte-identical
  pre-firtool/SFC inputs against the baseline export, then collect fresh Graph
  and Rocket RUN-IDs under one recovery-v7 manifest. Do not reuse `run-007` in
  that matrix or alter the runtime simulator cache/path.
  The first isolated build completed but stopped before export on absolute
  cache-root strings and nondeterministic file-list order. Freeze only the
  verified exact-root annotation normalization plus sorted basename-set check,
  then export to a new path; retain the failed cache/output attempt.
  The `v2` export and pinned Yosys parse/hierarchy/check now pass. Bind its RTL,
  provenance, generator, and common compatibility-policy hashes in recovery-v7
  before any Graph/Rocket synthesis; then rerun both partitions under that one
  manifest.
  Recovery-v7 authority `0611b04...1bee98` and manifest
  `5b165299...ec1780` were frozen; neither prior Graph result can be imported.
  `run-009` is an ineligible wrong-directory host failure and reveals that RTL
  hash verification occurred after Docker. Freeze the pre-container input
  preflight plus verified private snapshot as the sole recovery, seal `run-009`
  through its exact hash-locked retrospective path, then allocate a new Graph
  RUN-ID with the exact `generated-src` tree. `run-009` is now sealed with
  failed-seal `d5b7023...9d2af`; recovery-v8 authority
  `50639f0...aad938` and manifest `3dfb0dd...dd0b1` freeze only this collector
  correction. Run fresh Graph and Rocket partitions under v8 and derive a
  matrix only if both seal complete.
  Under v8, Graph `run-010` completed, while Rocket `run-011` raw evidence
  sealed but derived reporting failed because the checker counted seven
  unrelated module-area rows as ambiguity. Freeze the exact-frozen-top-only
  parser correction under a new authority, retain both v8 runs, then allocate
  fresh paired RUN-IDs. Do not derive a matrix across recovery manifests.
  Recovery-v9 authority `558c7c0...9c6df` and manifest
  `d052987...1fd63` freeze only that exact-top parser correction. Run new Graph
  and Rocket RUN-IDs under v9, then derive the matrix only from those results.
  V9 fresh runs now complete: area ratio 0.229563 is below the 0.25 no-go, Graph
  meets 20 ns, and Rocket misses it. Keep T-0044 open at `pause-boundary`.
  Resolve one boundary only: define and freeze a timing comparison in which the
  Rocket fallback partition also meets, without changing RTL/resources or
  importing the current ratio as whole-system area. Do not expand latency
  accounts or claim go/no-go from this physical proxy meanwhile.
  EXP-0010 now owns this single follow-up. Review and commit the manifest-driven
  20/40 ns collector compatibility, freeze one 40 ns manifest chained to v9,
  then run only fresh `run-014` Graph and `run-015` Rocket partitions. Preserve
  EXP-0009 `pause-boundary`; do not sweep clock targets or reuse its results.
  EXP-0010 authority `f662d68...1a9e3` and manifest `a09a641...b76ef` are
  ready for the freeze commit. After it, execute only the preregistered fresh
  pair and matrix; stop on any identity or timing-tuple drift.
  EXP-0010 is complete: fresh 40 ns pair meets, area ratio 0.229563 is below
  0.25, and outcome is `advance-to-integrated-physical`. Close the single-
  target follow-up and move only to an integrated boundary that includes the
  Rocket fallback, Graph incremental logic, common fixture/memory, adapters,
  cache/interconnect, clocks, and placement/routing. Do not promote the
  partition sum to whole-system area or reuse 40 ns as a performance claim.
  T-0044/S08 implements and functionally verifies the first bounded part of
  that boundary: one elaborated ChipTop now includes the fixed Graph core,
  Rocket fallback, common fixture provider, common owned TileLink memory,
  selector/adapter path, cache/interconnect, and common external clock/reset
  boundary. Graph-active, Rocket-active, runtime selection, inactive-origin,
  private-output, oracle, reset, and accounting smokes pass. A matched
  integrated/Rocket export pair also passes structural preflight with equal
  external ports, canonical Rocket identity, memory-macro inventory, and clock
  roots. Keep the local exports and preflight receipts as development evidence
  only. The independent performance/fairness review passes the bounded S08
  classification but blocks EXP-0011 freeze. The first independent clean
  replay retained a fail-closed canonical-Rocket mismatch even though the two
  exported `Rocket.sv` files were byte-identical. The bounded checker
  correction now preserves dependency/control order and normalizes only
  independent statements; local re-analysis of that retained raw pair passes.
  A fresh clean replay at `bad871d...6e87` passes 63 tests, G1b through G1e,
  both exports, the full Yosys preflight, and all raw/derived re-hashes.
  The bounded S08 prerequisite is integrated through PR review. Its independent
  clean replay absorbs T-0044/S09 at Current SP zero while preserving Initial
  SP 3. T-0044/S10 now implements the repository-only, fail-closed readiness
  validator for the estimand/overhead ledger, common/delta connectivity,
  clock/reset semantics, all integrated macro physical-view identities,
  repetition/seed and uncertainty policy, append-once raw/derived seal, and
  decision rules. It preserves Graph's 1,280 reads plus 256 writes as unequal
  to Rocket's lawful 800 reads plus 256 writes. The validator passes 31 focused
  tests and all 102 T-0044 tests in primary and independent clean-environment
  verification. It allocates or freezes no experiment and stores no result.
  T-0044/S11 now adds a separate v2 contract for full source/config/export/
  toolchain identity, an exhaustive common/Rocket/Graph component denominator,
  bounded workload and independent oracle identity, explicit unequal traffic
  and load reuse, common physical conditions, and an integrated P&R area/timing
  target with all result claims disabled. Primary and independent Python 3.14
  verification passes 35 focused and all 106 T-0044 tests. It stores no actual
  manifest or physical artifact. T-0044/S12 now completes the bounded
  repository-only pre-freeze validator for a two-seed paired physical matrix,
  absolute and incremental area accounting, common 40 ns timing, explicitly
  unavailable statistical intervals, fixed 0.25/40 ns decisions, and
  ADR-0050-strength RUN/evidence sealing. Primary and independent verification
  passes 38 focused, 21 physical-proxy, and all 109 T-0044 tests, and the high
  Performance review approves the bounded contract. It explicitly excludes
  the dynamic 1/4/16/64/256 campaign, energy, BOOM, and CGRA. **HCI-02 now
  applies immediately before** allocating EXP-0011 or freezing its first
  claim-bearing manifest. Do not collect synthesis, placement, routing,
  timing, area, energy, FPGA, ASIC, silicon, or performance data from
  S08/S10/S11/S12, and do not close T-0044.
  The owner authorized HCI-02 on 2026-08-24. T-0044/S13 then performed only the
  required pre-data physical-input binding and hit the fixed
  `required_physical_input_component_unavailable` pause: the pinned image has
  usable standard-cell/technology/RC views but no required Liberty timing or
  LEF geometry/pin view for any of the seven byte-identical
  integrated/matched memory macros. Matching GDS files are also absent but are
  supplemental to this pause. Preserve the tracked deterministic inventory
  runner and transcript identities recorded by the readiness receipt.
  Do not allocate or freeze EXP-0011, invent placeholder macros, or collect
  candidate data until one common memory physical-view strategy passes
  provenance, resource, and fairness review. Initial SP 13 is retained;
  Current SP is 3 for the bounded accepted readiness packet, and the remaining
  implementation/P&R scope is not counted while blocked.
  T-0044/S14's read-only public-source inventory is complete. It found no
  verified Liberty-plus-LEF set matching all seven exact macros and no already
  qualified standard-cell substitute. OpenRAM and one public SKY130 32x512
  1rw1r macro are possible inputs to a future proposal, not compatible assets.
  Keep S13 Blocked. Any generator or standard-cell-memory path requires the
  recorded external-dependency, fairness/design-fork, identity, and fresh
  pre-data confirmations before adoption or EXP-0011 work.
  T-0044/S15 completes the narrower repository-only common-source functional
  prerequisite. Its seven synthesizable module types match the canonical port
  directions, widths, depths, write masks, and functional semantics; the
  machine-readable contract derives eleven instances and 4,631,296 storage
  bits. Deterministic Verilator and Yosys preflight evidence is recorded in
  STATUS and the 2026-08-25 log. This does not unblock S13 or adopt the source
  as a physical denominator. Before any EXP-0011 allocation, candidate flow,
  or physical use, add a clean pre-data closure that replaces all exact 11
  instances in both exported hierarchies with one byte-identical source,
  verifies full connectivity/clocks/masks and absence of reachable blackboxes
  or `$mem*` cells at the required mapping boundary, binds the actual runtime
  receipt to the contract, and receives the already-required fairness/design
  review. Preserve collision/interleaving exclusions or prove the additional
  admissible semantics. Do not infer synthesis, P&R, area, timing, energy,
  performance, FPGA, ASIC, silicon, T-0044 completion, or go/no-go evidence.
  T-0044/S16 completes that repository-only pre-data closure at implementation
  commit `3b91286be86d8dadf098a91f00c369c5a1d28743`. The integrated and
  matched-Rocket exports each resolve the same seven concrete macro modules at
  the same eleven exact paths; every instance has the complete expected
  named-port connection set, including clocks and write masks. Both retain the
  same canonical Rocket identity and approved clock-root policy with zero
  reachable blackboxes. A v4 unfrozen contract and v2 bundle validator bind the
  comparison report plus all six raw/derived leg manifests, rehash every
  payload size and SHA-256, verify an aggregate manifest, and seal completed
  trees read-only. PM and independent one-command runs exit zero, pass all 162
  scoped tests, reproduce the same comparison SHA-256
  `1d3957d0f6b009d2ffedfac932c837f1051cc0a4f63b798392686e5891a6a7c3`,
  seven-memory source preflight, and 28-check Verilator result. Preserve both
  run-local hierarchy logs: their only differences are Yosys operational
  CPU/system/peak-memory/time-spent footers, so their manifest and dependent
  receipt hashes legitimately differ. Do not normalize raw evidence or treat
  those values as candidate performance. S16 does not unblock S13: before any
  EXP-0011 allocation or candidate flow, adopt and review actual common
  Liberty/LEF physical views, execute the future mapping passes identically,
  prove the mapped netlists contain no `$mem*` or reachable blackbox cells, and
  complete the already-frozen physical fairness boundary. Keep EXP-0011
  unallocated and T-0044 open.
  Separately, ADR-0050 requires the retained failed
  RUN and completed recovery RUN to receive immutable remote copies,
  download-based verification, marker-last completion, and a tracked
  non-sensitive receipt before EXP-0008 is called remotely durable or
  externally promoted. Use
  `docs/guides/T-0044-EXP-0008-EVIDENCE-PROMOTION.md`; do not rerun simulation
  merely to close this durability gap. The dedicated verifier and fake-rclone
  mutation/failure suite pass, and both RUNs now have immutable remote copies,
  successful download checks, marker-last byte-for-byte readback, and tracked
  receipt SHA-256
  `3ea8b815fb0c83c9563f19c22820f14130be6cc9af5bcfa20508d3eb87699392`
  covering 20 files and 738,617,303 bytes. This closes only EXP-0008 durable
  promotion. Continue the separately preregistered energy, timing, area, IP,
  and missing-organization work; T-0044 and RFC-0005 remain open.
  ADR-0049 adds a later categorical gate without changing frozen EXP-0008,
  EXP-0009, or EXP-0010: no custom configurable Graph executor, RISC-V extension,
  FPGA transition, or ASIC transition may advance until T-0044 includes a
  source/revision/license/provenance-verified public VLIW/CGRA/dataflow control,
  executes at least three semantically distinct graphs through one candidate
  interface without Chisel/RTL regeneration, proves the same owned
  effect/authority/fallback contract on CPU and configurable backends, and
  accounts for compile/map/configure/install/PPA cost. Treat an adequate public
  implementation as an adapter candidate, not an idea to rewrite. Custom
  hardware is explicit no-go when only source-generated per-kernel FSMs work,
  when matched configurability erases the claimed benefit, or when a new
  Raveil-only frontend/toolchain is required without a recorded standard-IR
  interoperability gap. Hardware no-go preserves the portable software
  contract/runtime path.

- [ ] **T-0106** Harden CPU-owned semantic attribution only after the candidate
  survives T-0044 or a separately accepted product requirement introduces
  untrusted or concurrent initiators. Preserve ADR-0045's implementation-owned
  token/epoch and fail-closed semantics; cover reset with outstanding work,
  stale/duplicate/exhausted and multi-live tokens, replay/source reuse,
  post-request exception and post-A rollback, arbitrary ELF identity, general
  loader/FESVR/Debug exclusion, and Rocket/BOOM lifecycle parity. This task is
  explicitly not a prerequisite for the controlled-run T-0042/T-0044 slice.
  The separately admitted five-point S-0001 carry-in is complete: one valid
  BOOM store token is cleared to invalid/zero before TileLink A, remains
  unknown at manager A/D, completes without hanging, and preserves readback.
  A current-main source-closure correction and independent replay both pass in
  the pinned BOOM/Verilator environment. This is bounded
  `rtl-simulation-functional` negative evidence only. It does not start the
  remaining conditional T-0106 matrix, reopen T-0042, establish resource
  matching, or support a performance claim.

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
