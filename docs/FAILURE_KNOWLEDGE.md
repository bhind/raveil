# Failure knowledge

Status: reusable operational guidance
Last updated: 2026-08-23

This index captures short lessons that prevent repeated mistakes. It does not
replace raw experiment bundles, EXP conclusions, regression tests, ADRs, TODO,
or dated logs. Add an entry only when the failure is non-obvious and likely to
recur. Link to authoritative evidence instead of copying large logs.

Each entry records the symptom, cause or current explanation, prevention,
detection, evidence, and whether follow-up remains open. Unknown causes stay
labelled unknown.

## Sprint slices must not reopen a completed parent task

- Symptom: the initial Weekly Sprint backlog attached BOOM token-lifecycle
  negatives to `T-0042/S01` through `/S10` and forecast another T-0042 closeout,
  although canonical TODO, STATUS, ADR-0046, and ROADMAP already close T-0042
  and assign conditional attribution hardening to T-0106.
- Cause: Project decomposition reused the identity of visible work-in-progress
  without first reconciling the current parent-task exit and superseding ADR.
- Prevention: before creating a `/SNN` coordination label, verify the parent
  checkbox, current STATUS statement, accepted ADR owner, start phase, and
  latest experiment outcome. A Project slice may narrow accepted work but may
  not reopen or redefine its parent.
- Detection: fail refinement when a planned child depends on closing an already
  completed parent, or when its acceptance language matches another task's
  explicit ownership. Record checker success is insufficient because this is
  semantic governance consistency.
- Evidence: T-0116 integration review against `origin/main` `648eea4`,
  ADR-0046, completed T-0042, conditional T-0106, and EXP-0010.
- State: classification corrected in the local integration record and private
  GitHub Project; human Sprint review and repository integration remain pending.

## Recompute estimates from executable work after every scope change

- Symptom: after ADR-0046 reduced T-0042 to a small-start slice, the Project
  Manager estimated three to six working days. The implementation candidate
  was committed 2 hours 48 minutes after the scope commit.
- Cause: the estimate retained effort intuition from the superseded exhaustive
  token-lifecycle scope. It did not inventory the already implemented Graph
  scratchpad, CPU manager, frozen workload, oracle, wrappers, or persistent
  Docker builds; it also did not separate edit, cached verification, and final
  integration time. In parallel, the implementation branch started from
  `793973e` and did not include the later authority commit `cb2d56b`.
- Prevention: bind every estimate to one authority commit and exact exit
  contract; classify each exit item as verified, reusable, configuration-only,
  new, or unresolved; inspect warm/cold build state and current delivery-rate
  evidence; estimate edit, verification, and integration separately; and
  recompute immediately after scope or authority changes. Before completion,
  require `git merge-base --is-ancestor <authority-commit> HEAD` to exit 0.
- Detection: reject an estimate with an incomplete
  `docs/templates/ESTIMATE-TEMPLATE.md`. Reject completion when the authority
  ancestry check is nonzero, even if tests on the stale branch pass.
- Evidence: T-0107; commits `793973e`, `cb2d56b`, and `0f4be3b`; the observed
  `git merge-base --is-ancestor cb2d56b 0f4be3b` exit was 1.
- State: workflow and PM-role prevention added. The `0f4be3b` implementation
  remains an integration-pending candidate until reconciled with `cb2d56b` and
  reverified.

## Powermetrics readiness is an event boundary, not elapsed time

- Symptom: an intermittently short measurement window reported two samples
  where the contract required three.
- Cause: the test inferred sampler readiness from scheduler timing and could
  discard observations already buffered with the readiness record.
- Prevention: synchronize readiness explicitly, exclude exactly the readiness
  observation, and carry later observations from the same read into the window.
- Detection: deterministic same-burst regression plus repeated synchronized
  execution.
- Evidence: T-0075 and EXP-0003, especially its sampler-readiness recurrence.
- State: corrected; retain the regression.

## Backend preparation heat can invalidate the first workload

- Symptom: a full run failed closed at thermal level `Moderate`, including
  after compilation or database preparation.
- Cause: setup heat occurred before the first measurement without the same
  recovery boundary used between workloads.
- Prevention: apply bounded idle plus two valid preflights after backend
  preparation and before the first measurement; keep measurement windows
  fail-closed.
- Detection: persist cooldown observations, thermal state, battery, frequency,
  and load context.
- Evidence: T-0081 and EXP-0003.
- State: corrected for the Gate 1 harness.

## Sealed evidence must record logical portable commands

- Symptom: a completed run could not seal because a recorded compile tuple
  contained an absolute machine-local bundle path.
- Cause: execution paths and provenance paths were recorded as the same value.
- Prevention: execute with resolved local paths but record repository-relative
  sources and bundle-relative outputs before sealing.
- Detection: pre-seal absolute-path and credential scan.
- Evidence: T-0082 and EXP-0003.
- State: corrected; do not normalize an already sealed bundle.

## Divergent prototype branches are donors, not automatic merge targets

- Symptom: an apparently useful MVP branch would delete later Sonatine,
  contract, Linux, telemetry, and test work if merged wholesale.
- Cause: the prototype diverged before later main integration and reused some
  record identifiers independently.
- Prevention: inspect `git diff --name-status` against current main, preserve
  allocated identifiers, and port reviewed units plus tests onto a fresh branch.
- Detection: branch-wide deletion review and canonical record comparison.
- Evidence: T-0087, ADR-0024, and the T-0086 port history.
- State: corrected for T-0086; apply to future long-lived branches.

## Mutable research writes must stay inside one RUN-ID

- Symptom: a caller-controlled `../` path could address a sibling mutable run
  while still remaining below the shared artifact root.
- Cause: containment was checked at the artifact-root boundary rather than at
  the individual RUN-ID boundary.
- Prevention: restrict mutable APIs to RUN-local names; open directories and
  files descriptor-relatively; reject absolute paths, traversal, symlinks,
  hard links, and directory swaps.
- Detection: assert that no probe file is created across each escape variant
  and pin the artifact-root device/inode.
- Evidence: T-0072 and `docs/log/2026-08-10.md`.
- State: corrected; security/integrity regression coverage is mandatory.

## Compiler packages and their FFI must be pinned as one ABI set

- Symptom: the resolver-selected Apache TVM FFI imported with a missing dynamic
  library symbol.
- Cause: independently compatible-looking package versions did not form a
  compatible binary ABI set.
- Prevention: pin the official compiler package, FFI, and exact supporting
  dependencies together in an isolated environment; record their sources.
- Detection: import before a campaign, compile all contract families, reopen
  the schedule database, and query stored schedules before execution.
- Evidence: T-0079 and `docs/log/2026-08-10.md`.
- State: corrected for the pinned Apple Silicon adapter; revalidate on every
  platform or version change.

## Immutable evidence can be correct but operationally expensive

- Symptom: synchronizing and download-verifying thousands of individual raw
  powermetrics files produced high object count and long transfer time.
- Cause: integrity was defined per file without an efficient immutable packing
  layer.
- Prevention: do not weaken existing attestation; prototype a content-addressed
  or packed representation only against a copied fixture.
- Detection: report object count, uploaded bytes, and sync/check elapsed time.
- Evidence: T-0071 and the preserved 3,600-record EXP-0003 history bundle.
- State: open; T-0071 owns follow-up.

## Root Docker allowlists must admit every owned build input

- Symptom: the Sonatine graph container build could not copy the guest sources
  even though the Dockerfile and sources were present in the repository.
- Cause: the root `.dockerignore` was an allowlist for the earlier GNU/Linux
  graph MVP and excluded the newly required `sonatine/` tree.
- Prevention: when a root-context Dockerfile gains an owned build dependency,
  update the root allowlist in the same change while continuing to exclude
  generated build directories and research artifacts.
- Detection: build the final root context from a clean checkout and run the
  containerized end-to-end command, not only host tests or a cached image.
- Evidence: T-0090 and `docs/log/2026-08-11.md`.
- State: corrected for the Sonatine graph backend.

## Per-tick UART diagnostics can destroy an interactive control path

- Symptom: the released QEMU demo continuously printed `clint-preempt` and
  neither the prompt nor `Ctrl+C` appeared responsive to its operator.
- Cause: every 100 Hz context transition synchronously wrote UART prose, while
  the U-mode line editor discarded ETX (`0x03`) as an unsupported control byte.
- Prevention: keep routine preemption silent, verify its count at a bounded
  self-test boundary, and route ETX through the same current-task-checked
  shutdown syscall as `exit`.
- Detection: real-QEMU smoke must assert that ETX exits, the normal transcript
  completes, and neither log contains `clint-preempt`.
- Evidence: T-0096 and the v0.0000000000002 operator report.
- State: corrected in local and fresh-clone CI with real-QEMU ETX regression;
  published in v0.0000000000003.

## Local call-sign catalogs must not share a public documentation path

- Symptom: the local-only `AgentNames.md` appeared in main and public release
  tags after being bundled into an unrelated reference-management commit.
- Cause: the file was created at repository root, outside the existing
  `.codex/*` ignore boundary, and no regression asserted its absence.
- Prevention: keep the catalog only at ignored `.codex/AgentNames.md`, ignore
  the root filename explicitly, and use generic role names in public records.
- Detection: the minimum suite fails if root `AgentNames.md` exists or loses
  its explicit ignore rule.
- Evidence: T-0097 and commit `9d069be` where the file first entered history.
- State: corrected for future commits; immutable historical tags still contain
  the non-secret catalog and are not rewritten.

## A baseline-first demo is not a production fast path

- Symptom: a screen can show a favorable candidate interval even though it
  repeatedly paid sequential/equal-concurrency baseline and validation cost.
- Cause: evaluation timing and a deployed execution path are different
  quantities; comparing only a weaker sequential baseline also confuses worker
  count with a Graph effect.
- Prevention: display baseline-first total cost separately, retain an
  equal-concurrency direct control, and state production reuse as absent unless
  the executor actually owns it.
- Detection: T-0103 tests assert the three controls and output labels;
  `showcase-incremental` names its cache as demo-only.
- Evidence: T-0103, ADR-0037, EXP-0004 (Planned), and
  `docs/guides/NATIVE_COMMAND_GRAPH_SHOWCASE.md`.
- State: corrected for the synthetic walkthrough; T-0104 remains open.

## Measurement must follow a falsifiable architecture contract

- Symptom: substantial Experience measurement and a process-level Command
  Graph showcase existed before the intended CPU/ISA mechanism, matched CPU
  controls, observable events, and fair resource envelope were defined.
- Cause: an available harness and visible demo were treated as progress on the
  core microarchitecture thesis even though they operated at different
  abstraction levels and answered different questions.
- Prevention: before performance work, record the candidate mechanism,
  ISA-visible semantics, workload, in-order and OoO controls, cache/memory and
  functional-resource matching, instrumentation, evidence class, confounders,
  and stopping rule. Tooling smoke and semantic tests may run earlier but may
  not produce performance claims.
- Detection: reject any benchmark plan that cannot identify which architecture
  hypothesis each metric can falsify, or that compares a Graph candidate only
  with an artificially weakened CPU.
- Evidence: EXP-0003 remains a valid narrow negative Experience result;
  T-0103/ADR-0037 remain a synthetic process-level illustration; RFC-0004 and
  T-0105/T-0057/T-0042/T-0044 record the corrected research order.
- State: open until the first matched Chisel comparison contract is accepted
  and executed; preserve this lesson even if that comparison is also negative.

## External source trees are not Raveil records

- Symptom: after fetching an ignored Rocket Chip reference checkout, the Raveil
  record checker reported upstream Markdown links as broken project records.
- Cause: the checker recursively scanned every Markdown file below the
  repository and did not exclude the explicit external-source boundary.
- Prevention: keep fetched upstream trees under ignored `external/` and exclude
  that directory from project-record discovery. Validate upstream material with
  its own pinned tooling rather than rewriting it to satisfy Raveil rules.
- Detection: fetch a pinned external checkout, confirm `git check-ignore`, and
  ensure the Raveil record count and result are unchanged.
- Evidence: T-0105 Rocket checkout and the task-governance record checker.
- State: corrected; retain this boundary for future external dependencies.

## Direct prior art must precede mechanism sketches

- Symptom: RFC-0004 named static, elastic, stream and hybrid Graph candidates
  and a comparison sequence before directly mapping TRIPS/EDGE, WaveScalar and
  DySER mechanisms, limitations and patent risk.
- Cause: fair baseline design was conflated with candidate architecture design.
  A useful OoO control does not establish that a proposed graph mechanism is
  new, safe to adopt or even sufficiently specified.
- Prevention: before Graph RTL, create a locator-backed mechanism matrix,
  identify counterevidence, record high-similarity and patent-family hits, and
  freeze node, ISA, memory, exception/commit, resource, invalidation, fallback
  and no-go semantics. Keep generic tooling bootstrap separate.
- Detection: reject an architecture task whose proposed mechanisms cannot be
  traced to a reviewed T-0057 distinction and IP-risk disposition.
- Evidence: T-0057, RFC-0003, RFC-0004, and
  `docs/research/reviews/2026-08-11-T-0057-native-graph-prior-art-matrix.md`.
- State: phase A and the ADR-0039 simulation-only phase-B boundary are recorded;
  qualified legal review remains open for broader implementation or claims.

## DMI response readiness may participate in request readiness

- Symptom: a repository-owned DMI driver never accepted its first request when
  response ready was asserted only after request acceptance. After making the
  response channel continuously ready, the first response instead arrived in
  the same cycle as request acceptance and tripped an outstanding-only assert.
- Cause: the pinned `DMIToTL` maps DMI response readiness into TileLink D
  readiness, and intervening buffering can make that readiness part of the A
  request-ready path. The return path can also be zero-latency at the harness
  interface.
- Prevention: keep response ready asserted for the bounded driver, and accept
  a response only when it pairs with either a previously outstanding request
  or a request firing in the same cycle. Retain a fail-closed assert for every
  other response and a finite watchdog for missing progress.
- Detection: require bounded request/response markers plus the final manager
  signature in both Rocket and BOOM Debug SBA simulations.
- Evidence: T-0042 repository-owned Debug SBA driver and
  `docs/log/2026-08-13.md`.
- State: corrected for the bounded functional harness; this is not a general
  Debug transport, security, or semantic-initiator claim.

## RTL index arithmetic must widen before a boundary increment

- Symptom: the first static-stencil RTL run matched its independent oracle for
  output addresses 0 through 14, then disagreed at address 15.
- Cause: a four-bit column slice added one without first widening, so logical
  column 16 wrapped to zero. The same defect would have affected the final row.
- Prevention: explicitly widen bounded index fields to the range required after
  arithmetic, then add. Do not infer Chisel result width from the destination
  wire.
- Detection: compare every RTL output against an independently implemented
  oracle, include both final-column and final-row boundaries, and fail before
  accepting a self-reported checksum.
- Evidence: T-0042 `StaticStencilRegion.scala`,
  `static_stencil_sim_main.cpp`, and `docs/log/2026-08-12.md`.
- State: corrected with five-bit coordinate padding; the full 512 checked
  outputs and cancel/restart path pass in Verilator.

## SBT hardware builds may execute Git while loading project settings

- Symptom: the first pinned BOOM Scala-project compile downloaded SBT and then
  failed during project loading with `Cannot run program "git"`.
- Cause: the minimal Temurin JDK container omitted Git, while an SBT Git plugin
  queries repository metadata before the selected project compiles.
- Prevention: include the exact external tool in the owned build environment;
  do not assume a Java-only compile uses only the JVM.
- Detection: start the build in a fresh container and require both tool-version
  output and a final scoped success marker. Keep the source bind read-only and
  compile an ephemeral copy so plugins cannot dirty evidence authority.
- Evidence: T-0042 `run-boom-project-compile.sh` and
  `docs/log/2026-08-12.md`.
- State: dedicated compile image includes Git; Maven coordinate resolution is
  still labelled unlocked and cannot support measurement evidence.

## Chipyard elaboration needs the Make-provided boot ROM and device-tree compiler

- Symptom: direct `chipyard.Generator` invocation first reached the configured
  BOOM tile and failed on a missing target-directory `bootrom.rv64.img`; after
  supplying the image it reached the next phase and failed because `dtc` was
  absent from the minimal container.
- Cause: invoking the Scala generator directly bypassed two prerequisites that
  Chipyard's normal Make flow supplies: copying the checked-in testchip boot
  images to the target directory and providing a device-tree compiler.
- Prevention: reproduce both prerequisites explicitly in the owned functional
  wrapper, print the `dtc` version, and retain the external Chipyard checkout as
  read-only input. Treat digest-pinned base image plus unlocked APT/Maven
  resolution as functional bootstrap only, never as measurement authority.
- Detection: require the final elaboration marker and non-empty FIRRTL plus
  annotation outputs containing `BoomCore`; reaching BOOM parameter output is
  progress, not successful elaboration.
- Evidence: T-0042 `run-boom-elaboration.sh`, `Dockerfile.boom`, and
  `docs/log/2026-08-12.md`.
- State: wrapper prerequisites corrected; retain both failed attempts as
  bootstrap evidence.

## Recursive Chipyard submodule setup is wider than the BOOM control boundary

- Symptom: recursive initialization created nested checkout collisions and
  attempted to fetch an unrelated private Mentor plugin before BOOM
  elaboration could start.
- Cause: the upstream repository's full recursive dependency graph includes
  parent/nested ordering constraints and optional or private integrations that
  are outside the BOOM functional-control scope.
- Prevention: initialize only the explicit public parent gitlinks required by
  the selected Chipyard project, without recursion, and accept each revision
  only from the pinned parent tree.
- Detection: require `git status --ignore-submodules=none` to be clean and the
  source verifier to pass before every compile or elaboration.
- Evidence: T-0042 `fetch-boom-elaboration-deps.sh` and
  `docs/log/2026-08-12.md`.
- State: corrected with explicit non-recursive public gitlinks; optional and
  private integrations remain outside the owned boundary.

## Chipyard simulator outputs and tool prefixes must be verified, not guessed

- Symptom: the first simulator wrapper checked for a shortened executable name
  after the Verilator link had succeeded; the actual Make output includes the
  `chipyard.harness` package. Earlier tool probes also looked for the RISC-V
  compiler directly under the environment `bin`, while the lock installs it
  below the configured `RISCV` prefix. A full Spike build was started even
  though Chipyard's simulator link needed only FESVR and its headers.
- Cause: paths and prerequisites were inferred from component names instead of
  the selected Chipyard Make flow and lockfile layout.
- Prevention: use the exact Make-produced simulator path, export both the
  locked environment and `$RISCV/bin`, and build only `libfesvr.a` plus the
  installed FESVR headers. Require cached trees to have no tracked changes
  while permitting untracked build outputs such as CDE `target/`. Stop and
  replace a wider disposable build once its extra scope is recognized.
- Detection: require the simulator executable, compiler version, FESVR archive
  and header, ELF machine and symbols, normal Verilator finish, and exact
  functional-only completion marker.
- Evidence: T-0042 `run-boom-functional-smoke.sh` and
  `docs/log/2026-08-12.md`.
- State: corrected for the functional smoke; the conda-lock reader bootstrap
  remains unlocked and explicitly outside future measurement authority.

## Locked build inputs must exclude convenience hooks and generated state

- Symptom: Rocket's upstream Nix development shell installed current Python
  packages into an untracked `venv/`; a later path-based flake evaluation tried
  to scan a generated Mill Unix socket and failed. A cold container then reused
  host `out/` from another Nix store and failed to load Mill's Zinc worker.
  After isolating only Nix and `out/`, a second ephemeral-container run failed
  again because the first run's Mill/Coursier user cache had vanished.
  Nix's nested builder seccomp BPF also failed under Apple Silicon amd64
  emulation.
- Cause: the convenience development shell, mutable working tree, package
  authority, and container security layers were treated as one environment.
  The committed flake was fixed, but its shell hook and path input were not
  sufficient evidence boundaries for this smoke.
- Prevention: bind Nix evaluation to the exact Git revision and committed
  `flake.lock`; select only required package attributes with `nix shell`; do not
  run the upstream shell hook; keep generated output and cache volumes outside
  input identity. Keep one generation-matched Nix-store, Mill-output, and
  Mill/Coursier user-cache volume set; never share host `out/` across stores or
  retain Mill output after discarding its worker cache. Under
  cross-architecture Docker, disable only Nix's nested syscall filter while
  retaining Docker seccomp and `no-new-privileges`.
- Detection: require a clean pinned source/submodule tree, reject `nix develop`
  and Python installation in the owned wrapper, rerun after generated output
  exists, and require the exact functional-only completion marker.
- Evidence: T-0105, ADR-0038,
  `hardware/chisel/rocket-reference-in-container.sh`, and
  `tests/test_chisel_substrate.py`.
- State: corrected for the T-0105 reference smoke. Reassess the platform and
  security envelope before T-0044 measurement.

## ELF section checks must request wide names

- Symptom: the first shared-scratchpad functional wrapper stopped after both
  prerequisite CPU smokes even though compilation emitted the requested long
  section name.
- Cause: `readelf -S` abbreviates long section names to fit its default display;
  an exact grep for `.scratchpad_signature` therefore failed closed.
- Prevention: use `readelf -SW` for exact section-name validation and use `nm`
  independently for the required input/output addresses.
- Detection: distinguish an absent final marker from RTL failure, then inspect
  the first failing static assertion before rerunning a simulator.
- Evidence: T-0042 `run-shared-scratchpad-stencil-functional.sh` and
  `docs/log/2026-08-12.md`.
- State: corrected; the subsequent Rocket/BOOM/diagnostic TLRAM run passed.

## TileLink latency observers must match the fragmented beat boundary

- Symptom: an observer above `TLFragmenter` accepted 37 logical requests but
  saw 296 response beats, so a one-entry-per-source A-to-D matcher reported
  hundreds of unmatched responses even though the signature was correct.
- Cause: the upstream request and downstream response were observed at
  different effective granularities; the fragmenter expands logical transfers
  into bank-local beats and recombines their responses.
- Prevention: attach endpoint-latency telemetry below the fragmenter, key each
  accepted A beat to D completion by the expanded source ID, and keep upstream
  logical-request accounting as a separate metric.
- Detection: fail closed on unmatched D beats, premature source reuse, pending
  requests at finish, and inconsistent opcode/address-region totals.
- Evidence: T-0042 `tlram_endpoint_latency_observer.sv`, its parser tests, and
  `docs/log/2026-08-12.md`.
- State: corrected for bank-local functional diagnostics; CPU end-to-end and
  Graph-matched latency remain open.

## Generated simulator file lists retain their container locator

- Symptom: rebuilding an existing Chipyard generated source tree from a volume
  mounted at `/rocket` failed because its file list still named every source
  below the original `/build/chipyard` locator.
- Cause: the generated Verilator file list records absolute build-container
  paths; moving the same bytes to another mount name does not rewrite it.
- Prevention: recreate the original read-only locator inside the disposable
  build container, or regenerate the file list from the new locator. Keep
  observer model and binary paths separate from validated normal artifacts.
- Detection: inspect the first missing-module path before treating the failure
  as RTL or source corruption.
- Evidence: T-0042 `run-tlram-latency-observer.sh` and
  `docs/log/2026-08-12.md`.
- State: corrected in the observer wrapper; no validated normal simulator was
  overwritten.

## Endpoint latency without attribution is not a common memory contract

- Symptom: the shared TLRAM observer reported 296 matched one-cycle read beats
  in each CPU mode, but no writes and no distinction among CPU execution,
  cache activity, FESVR staging, or signature recovery.
- Cause: the passive bind was intentionally below the fragmenter at the memory
  endpoint. That gives correct beat correspondence but loses request origin and
  lifecycle context, while the Graph RTL does not use that path at all.
- Prevention: define an owned request/response boundary with explicit
  initiator, lifecycle phase, read/write, byte mask, error, backpressure, and
  accepted/completed/pending accounting before adapting either machine.
- Detection: reject resource matching when any initiator/phase is ambiguous,
  either operation direction is unexercised, adapters bypass the owned
  interface, or only endpoint `minLatency`/observed latency is available.
- Evidence: T-0042 TLRAM observer, ADR-0042, ADR-0043, and the standalone
  `OwnedFixedLatencyScratchpad` assert-enabled Verilator harness.
- State: local owned protocol and the Graph adapter are verified; CPU adapters
  remain open and fixed end-to-end latency is not claimed.

## Chisel integration runners must compile every emitted child module

- Symptom: the first owned-memory Graph integration emitted the top-level
  `StaticStencilRegion` successfully, but Verilator could not find the two
  generated `OwnedFixedLatencyScratchpad` child modules.
- Cause: the older runner passed only `StaticStencilRegion.sv`; that was enough
  while the design emitted one module but not after structural composition.
- Prevention: pass the complete bounded generated-SystemVerilog directory to
  Verilator and retain an explicit top-module selection. Keep generated output
  outside Git and clear only its exact task-local directories.
- Detection: distinguish Chisel elaboration success from downstream Verilator
  module-resolution success; require the executable RTL marker, not only the
  generated top file.
- Evidence: T-0042 `run-static-stencil.sh` and the Graph owned-memory adapter
  integration log.
- State: corrected; the subsequent assert-enabled two-bank Graph run passed.

## Adapter accounting must follow the executable memory schedule

- Symptom: the first successful two-bank Graph RTL marker reported 3,072
  execution cycles while the host's adapter v2 JSON still reported the former
  direct-storage value of 1,536.
- Cause: the six logical operation phases stayed unchanged, but each owned
  request now needs a request-acceptance and response-retirement cycle. Static
  observation defaults had not moved with the executable implementation.
- Prevention: compare every human marker with every machine-readable adapter
  field in the same run before accepting a milestone. Separate logical Graph
  schedule phases from interface cycles.
- Detection: fail review on unequal staging, execution, validation, cancelled
  useful-operation, or missing-accounting facts across RTL, adapter JSON,
  tests, STATUS, and operator guidance.
- Evidence: T-0042 `StaticStencilRegion.scala`, `simulation_adapter.py`, the
  Verilator marker, and strict adapter tests.
- State: corrected to 648 staging, 3,072 execution, and 512 validation cycles;
  installation, completion, publication, CPU matching, and total remain open.

## Non-cacheable managers cannot be inserted behind a coherent cache unchanged

- Symptom: the first CPU-owned TileLink overlay compiled but Rocket elaboration
  stopped in `TLSlaveParameters` when the inclusive cache added acquire support
  to an idempotent manager.
- Cause: the overlay initially attached a non-cacheable manager to MBUS. The
  inherited inclusive-cache adapter expects a cacheable/uncached manager there;
  adding coherent acquire support while retaining `IDEMPOTENT` region type is
  an invalid TileLink capability combination.
- Prevention: select the bus from the evidence question. Use an uncached path
  for the first observable translation test; design and verify a separate
  matched local-memory topology before comparison rather than changing region
  attributes merely to make elaboration pass.
- Detection: require both Rocket and BOOM top-level elaboration, inspect the
  manager's region/capability negotiation, and keep resource matching false for
  any peripheral-bus bootstrap.
- Evidence: T-0042 `RaveilOwnedTLMemory.scala`, pinned inclusive-cache
  `InclusiveCache.scala`, and the failed first elaboration attempt.
- State: corrected by ADR-0044's explicit uncached, unmatched bootstrap; CPU
  execution and matched memory remain open.

## Bus-attached stateful LazyModules need an explicit clock domain

- Symptom: after moving the owned manager to PBUS, diplomacy completed its
  address map but Chisel elaboration stopped with `No implicit clock` while
  instantiating the stateful manager.
- Cause: the first overlay coupled a plain `LazyModule` directly to the bus and
  never connected the bus wrapper's fixed clock to the manager registers and
  synchronous memory.
- Prevention: wrap stateful bus peripherals in an explicit `ClockSinkDomain`
  and connect its `clockNode` to the selected bus clock. Do not rely on an
  ambient top-level clock.
- Detection: top-level elaboration must instantiate the manager under both
  Rocket and BOOM configurations; source-string or standalone Scala checks are
  insufficient.
- Evidence: T-0042 `RaveilOwnedTLMemory.scala` and the failed PBUS elaboration
  attempt.
- State: corrected with the bus wrapper's generated synchronous domain; the
  final Rocket and BOOM dual-target elaboration passed.

## Raw TileLink tests must obey the negotiated protocol before testing a manager

- Symptom: the first direct owned-manager harness failed during elaboration
  when client `supports*` fields were misused as emitted-request declarations;
  a later run tripped the upstream monitor by clocking a lane-one byte request
  with an incompatible transfer size. Separate attempts also failed from an
  unbounded parallel assembly build, the wrong upstream `plusarg_reader`, and
  an omitted legacy-Verilator `sc_time_stamp` definition.
- Cause: TileLink master `supports*` fields describe slave-to-master behavior,
  legal A-channel masks depend on address and size, and emitted BlackBox/model
  support must match the exact pinned Rocket Chip version. Full Chipyard
  assembly also exceeded the available Docker memory when left unconstrained.
- Prevention: derive legality from the pinned `Parameters.scala` and monitor,
  keep the monitor enabled, test manager rejection only with legal negotiated
  requests, use the exact pinned BlackBox resource, bound SBT parallelism, and
  cache assemblies by the overlay content hash rather than by a mutable name.
- Detection: require the complete FIRRTL-to-Verilog-to-Verilator path and the
  final `OWNED-TL-PROTOCOL-V1 status=OK` marker; Scala compilation or monitor-
  disabled simulation is insufficient.
- Evidence: T-0042 `RaveilOwnedTLProtocolHarness.scala`,
  `run-owned-tl-protocol.sh`, the failed direct-protocol attempts, and the final
  16-transaction monitor-enabled run.
- State: corrected; the manager-local legal protocol slice passes. CPU
  execution, initiator attribution, resource matching, and measurement remain
  open.

## RV64 signed loads can create false 32-bit data mismatches

- Symptom: the first Rocket-owned-memory workload reached the manager and its
  diagnostic signature showed the expected `cafebabe` word, but the ELF took
  its execution-data failure branch.
- Cause: `lw` sign-extends bit 31 into RV64 while the `li 0xcafebabe` comparison
  value was represented as a zero-extended 64-bit constant. The stored 32-bit
  values were equal; the test compared unequal 64-bit register values.
- Prevention: choose `lw` or `lwu` deliberately for every 32-bit test value and
  keep an independently decoded signature that records observed values before
  a failure exit.
- Detection: on a CPU smoke mismatch, inspect both the signature and ELF
  disassembly before attributing the failure to the memory RTL. Retain a value
  with bit 31 set in the workload so signedness stays covered.
- Evidence: T-0042 `owned_memory_cpu_smoke.S`,
  `verify_owned_memory_cpu_signature.py`, the failed diagnostic signature, and
  the subsequent successful `OWNED-ROCKET-MEMORY-SMOKE-V1` run.
- State: corrected by using `lwu` for the unsigned `cafebabe` comparison; the
  exact Rocket RTL workload and host signature verifier now pass.

## Diplomacy child ports require a named LazyModuleImp type

- Symptom: the first standalone TileLink-to-owned bridge assembly reached the
  repository overlay, then Scala reported that `io`, `ownedRequest`, and
  `ownedResponse` were not members of the child `LazyModuleImp` as referenced
  by the parent harness.
- Cause: each child used an anonymous `new LazyModuleImp(this)`. Its public
  `module` value widened to the base `LazyModuleImp` type, which hides ports
  that exist only on the anonymous subclass.
- Prevention: when a parent diplomacy harness must connect child-specific
  ports, define a named `LazyModuleImp` subclass and return that concrete type
  from the child's `lazy val module`.
- Detection: compile the complete pinned Chipyard project and elaborate the
  parent harness; source inspection or compiling an isolated child cannot
  prove that the parent sees the refined module type.
- Evidence: T-0042 `RaveilOwnedTLContractBridge.scala`, the failed first
  `run-owned-tl-contract-bridge.sh` assembly, and
  `docs/log/2026-08-12.md`.
- State: corrected with named bridge/client module implementations; the final
  assert-enabled Verilator run and checksum-verified cache rerun pass.

## TileLink metadata must be verified through every negotiated junction

- Symptom: a DCache-local origin bit compiled in the adapter but arrived false
  at the owned manager; a later echo-field attempt stopped during FIRRTL
  lowering with uninitialized Xbar and error-manager fields.
- Cause: the pinned `TLXbar` intentionally replaced request `user` fields with
  `DontCare`. Moving the diagnostic to an echo field avoided that assignment
  but imposed a D-response echo obligation on every reachable manager,
  including `TLError`, and a field present on only one client left unioned wide
  bundle members without deterministic defaults.
- Prevention: choose request metadata when only A-side observation is needed;
  initialize absent unioned fields from their declared defaults and preserve
  negotiated fields through the pinned Xbar. Do not infer metadata retention
  from diplomacy negotiation or a tagger module name alone.
- Detection: require complete firtool lowering plus runtime positive and
  negative counters. For T-0042 the two CPU paths must report structural origin
  8/8 and non-origin 0/0, while the untagged raw client must report origin 0/0
  and non-origin 7/7.
- Evidence: T-0042 `RaveilDCacheOriginTagger.scala`,
  `t-0042-tlxbar-request-defaults.patch`, the failed request-user and echo
  attempts, and the final Rocket/BOOM signature V3 plus protocol V4 markers.
- State: corrected for the pinned diagnostic path. Target-ELF semantic
  initiator identity and loader/debug negative coverage remain open.

## Extending a request Bundle does not extend partial pipeline assignments

- Symptom: the BOOM LSU asserted token `{valid=1, epoch=1, sequence=1}` on its
  accepted store request, but the first owned-manager trace received the
  negotiated TileLink fields as invalid/zero.
- Cause: `BoomDCacheReq` gained the token fields and the I/O MSHR copied them to
  TileLink, but the intervening DCache MSHR request was initialized with
  `DontCare` and assigned selected legacy members individually. The new fields
  therefore never crossed the `s2_req` to MSHR boundary.
- Prevention: when extending a Bundle that traverses partial member
  assignments, audit every register, wire, arbiter, and request conversion;
  explicitly copy authority-bearing fields and explicitly invalidate producers
  that must not carry them.
- Detection: require an end-to-end verifier to compare the CPU-minted token
  with the manager's exact A acceptance and retained D completion. Compilation
  and local producer assertions alone are insufficient; invalid/zero at the
  consumer is a failed handoff when a valid producer is expected, not an
  untagged success. A configuration that deliberately omits the producer is a
  separate negative and must instead require default-invalid metadata,
  unknown classification, and a completed ordinary transaction without
  semantic promotion.
- Evidence: T-0042 `t-0042-boom-store-token-handoff.patch`, the failed first
  BOOM token simulation, and `docs/log/2026-08-14.md`.
- State: corrected for the bounded BOOM store path by copying all three fields
  from `s2_req` into the MSHR request. Replay, reset/epoch, other request classes,
  and general multi-live behavior remain open.

## ELF segment count is not transport request count

- Symptom: the first dedicated four-byte loader probe expected one non-origin
  TileLink request before CPU execution, but the pinned Rocket run observed two
  accepted requests and failed its exact pre-CPU signature check.
- Cause: the expectation equated one ELF `PT_LOAD` with one transport request.
  FESVR aligns the four-byte write to the transport's eight-byte boundary by
  reading the aligned chunk and writing the updated chunk, producing two
  manager requests for this pinned case.
- Prevention: validate ELF segment layout and observed transport multiplicity
  as separate contracts. Do not derive TileLink request count from program-
  header count.
- Detection: snapshot accepted/completed and origin/non-origin counters before
  the CPU touches the mapped page, then require their conservation again after
  the CPU access. Keep source values bounded by the exact generated graph.
- Evidence: T-0042 `owned_memory_loader_probe.S`,
  `verify_owned_memory_loader_probe.py`, pinned FESVR `memif.cc`, the initial
  failed Rocket signature, and the corrected Rocket/BOOM probe runs.
- State: corrected as an expectation-model mismatch; the verifier now requires
  serial-class non-origin 2/2 before CPU access and one additional tagged
  DCache-origin completion afterward. This does not generalize the count to
  other segments or transports.

## Load writeback is not a same-cycle DCache response

- Symptom: the first pinned Rocket witness asserted that a load reaching WB
  also had `dmem_resp_valid` in that cycle and stopped an otherwise valid run.
- Cause: the diagnostic conflated separately timed load WB and DCache response
  events; the failure says nothing about same-cycle request/response behavior.
- Prevention: retain the accepted request tag and observe response and WB as
  independent qualified events that may arrive in either order.
- Detection: require both events and exact request/response tag equality before
  accepting a bounded load witness; never infer response timing from WB alone.
- Evidence: T-0042 pinned Rocket request-retire patch and the corrected RTL
  replay recorded in `docs/log/2026-08-13.md`.
- State: corrected for the bounded positive; replay, kill, exception, reset,
  durable-token, and owned-manager completion cases remain open.

## Chisel diagnostic output needs verbose mode and both output streams

- Symptom: RTL execution and signature completed, but the verifier found zero
  lifecycle records in the captured file.
- Cause: one run omitted `+verbose`; after that was corrected, the runner still
  piped only stdout while the pinned simulator emitted Chisel `printf` records
  on stderr.
- Prevention: invoke diagnostics as `+permissive +verbose ...
  +permissive-off` and capture `2>&1` through a `pipefail`-protected `tee`.
- Detection: require the exact record prefix, count, schema, and signature;
  inspect the persisted raw log rather than relying on combined terminal text.
- Evidence: T-0042 `run-owned-cpu-memory-smoke.sh`, the persistent-volume logs,
  and `docs/log/2026-08-13.md`.
- State: corrected; timeout and exact verifier remain mandatory.

## Verifier fixtures must preserve emitted Chisel numeric formatting

- Symptom: real records used padded decimal fields such as `epoch= 1` and
  `sequence=    1`, while hand-written fixtures used unpadded values; the real
  stream would fail parsing after log capture was corrected.
- Cause: the fixture represented semantic values but not Chisel `%d` output
  formatting, leaving a transport-format blind spot.
- Prevention: normalize only whitespace following `=` before exact-schema
  parsing and keep a fixture copied from the emitted field shape.
- Detection: run the verifier against captured RTL output in addition to
  mutation fixtures, and continue rejecting missing, extra, or duplicate keys.
- Evidence: T-0042 `verify_owned_rocket_request_retire.py`, its boundary tests,
  and the corrected direct RTL replay.
- State: corrected for the current marker; future marker formats need their own
  emitted-output fixtures.

## A taken branch can accept the following wrong-path DCache request

- Symptom: the first Rocket redirect-negative design expected zero owned-address
  request records after an always-taken branch, but the pinned RTL emitted one
  `allocate` and one accepted `request` for the immediately following store.
- Cause: the older branch resolves in MEM while the younger store is already in
  EX. `io.dmem.req.valid` is driven from the EX-stage memory instruction, so the
  request handshake and `take_pc_mem` can occur in the same cycle.
- Prevention: classify lifecycle evidence from the actual pinned pipeline
  signals. Do not call a branch-skipped instruction a pre-request kill without
  observing the request boundary.
- Detection: require an exact `kill` event qualified by accepted request,
  branch, taken direction misprediction, both correlated PCs, and
  `promotion=blocked`; separately state that DCache S1-kill and TileLink A/D
  fate were not checked.
- Evidence: T-0042 `owned_memory_rocket_redirect_negative.S`, the preliminary
  pinned RTL log with `allocate/request` only, the corrected Rocket patch, and
  `docs/log/2026-08-13.md`.
- State: corrected for the one simultaneous accepted-request/MEM-redirect
  probe. Pre-request kill, later post-request exception/rollback, and transport
  completion remain open.

## Uninitialized RTL memory cannot supply a fixed negative-test baseline

- Symptom: the first exact redirect-negative workload required the post-probe
  load to return zero, but the pinned run returned `0xc5686cac` and exited with
  failure after emitting the expected killed-token lifecycle.
- Cause: the owned manager uses `SyncReadMem`; the workload had not initialized
  the probed word, so zero was not an architectural or manager invariant.
- Prevention: do not assign a fixed value to an uninitialized simulated memory.
  Establish an ordered baseline or use bounded before/after differential
  readback with a fail-closed collision value.
- Detection: include all compared values in the signature and require exact
  equality plus explicit rejection of the wrong-path magic value.
- Evidence: T-0042 exact Rocket RTL runs, `owned_memory_rocket_redirect_negative.S`,
  and `verify_owned_rocket_redirect_negative.py`.
- State: corrected with two completed loads observing the same non-magic value;
  this still does not prove general absence of a memory side effect.

## A one-entry load witness remains live until response and retirement close

- Symptom: a differential workload placed a second owned-address candidate
  after the first load's WB event but before its response marker, triggering
  `Raveil Rocket witness live-token mismatch`.
- Cause: the observer intentionally retains a load token until both matching
  response and WB have appeared. One register entry cannot represent a new
  candidate during that interval.
- Prevention: bounded single-token workloads must create a true dependency on
  the prior load value before the next candidate. Supporting overlap requires a
  separately specified multi-entry observer, not silent token replacement.
- Detection: retain the fail-closed assertion and test response/WB ordering and
  overlapping candidate cases before broadening the diagnostic claim.
- Evidence: T-0042 exact Rocket RTL assertion, ADR-0045 lifecycle rules, the
  pinned Rocket witness patch, and `docs/log/2026-08-13.md`.
- State: the bounded negative is serialized by a data dependency. Multi-live-
  token observation remains open and is not claimed.

## Branch redirect stimuli depend on pinned fetch and predictor history

- Symptom: adding initialization, moving the branch PC, using `jalr`, or
  self-training a conditional changed the negative from an accepted wrong-path
  request to pre-request suppression.
- Cause: whether the younger store reaches EX when the older redirect resolves
  depends on the exact pinned fetch/predictor history and intervening DCache
  state; ISA control flow alone does not fix that microarchitectural timing.
- Prevention: verify the exact emitted branch/store PCs and redirect
  qualification in RTL, and retain the stimulus only when the accepted request
  itself appears. Do not infer a request from assembly layout.
- Detection: the verifier requires exact `allocate/request/kill`, adjacent PCs,
  accepted request, branch/taken/direction-misprediction, and no store retire.
- Evidence: T-0042 rejected workload variants and the final exact Rocket trace.
- State: corrected for one pinned workload; no predictor behavior or
  performance generalization is made.

## Exact graph and numeric verifiers must admit new diagnostic identities

- Symptom: the first Rocket DCache-fate build completed RTL elaboration and
  Verilator compilation but stopped because the source-map verifier admitted
  only `RaveilOwnedRocketConfig`; the next run completed RTL but rejected the
  same address when Chisel printed additional hexadecimal leading zeros.
- Cause: the diagnostic introduced an exact new config identity while the
  topology verifier retained a single old name, and the fate verifier compared
  a numeric address as presentation text rather than as an integer.
- Prevention: enumerate every admitted generated graph by exact filename and
  compare numeric RTL fields after base-aware parsing. Keep schema, cardinality,
  source-range, opcode, and A/D ordering checks strict.
- Detection: require the graph filename to match exactly one admitted config,
  reject all other names, and include zero-padded numeric encodings plus
  request/S1 tag mismatches in verifier mutation tests.
- Evidence: T-0042 `verify_owned_cpu_source_map.py`,
  `verify_owned_rocket_redirect_dcache_fate.py`, the two fail-closed runs, and
  the subsequent successful exact Rocket RTL run.
- State: corrected for the admitted Rocket and Rocket-fate configs and the
  bounded fate schema; future configs remain fail closed until enumerated.

## Patch context must not move an observer before its state definitions

- Symptom: the first post-request-exception elaboration failed with a null
  `raveilExceptionActive` reference even though the patch applied cleanly.
- Cause: a broad second hunk matched an earlier `wb_valid` definition, placing
  the outcome logic before the later request-state registers in Scala class
  initialization order.
- Prevention: keep dependent diagnostic state and outcome logic in one
  narrowly anchored hunk, then inspect the fully composed pinned source rather
  than accepting `git apply` success as placement evidence.
- Detection: apply every ordered patch to a temporary pinned source, check its
  exact post-patch hash and diff, and require full Chisel elaboration.
- Evidence: T-0042 post-request-exception patch, failed elaboration, and
  `docs/log/2026-08-13.md`.
- State: corrected by colocating the state and outcome logic; the subsequent
  exact RTL run passed.

## A new workload can change retry cardinality of reused lifecycle records

- Symptom: the first successful exception RTL simulation emitted the intended
  request/exception pair, but its verifier expected eight surrounding aligned-
  load records and rejected the actual ten.
- Cause: each aligned load made two accepted DCache request attempts in this
  exact workload, while the new verifier fixture assumed the one-attempt shape
  from a different positive workload.
- Prevention: treat request attempts as explicit lifecycle events and define
  exact per-workload cardinality; do not inherit replay assumptions from a
  neighboring test.
- Detection: verify the persisted raw RTL markers before relaxing a count. For
  this workload require attempts 1 then 2 with identical token, PC, address,
  operation, and tag for each aligned load.
- Evidence: T-0042 post-request-exception raw RTL log, verifier mutation tests,
  and `docs/log/2026-08-13.md`.
- State: corrected for the exact two-retry surrounding-load trace; this does
  not establish general replay support or a durable token.

## A repeated DCache request is not a core replay witness by itself

- Symptom: each aligned load in the Rocket post-request-exception workload
  fired the same request twice, making that stable trace look like a minimal
  replay candidate.
- Cause: an exploratory pinned-source hook found every directly surveyed core
  replay, DCache nack, and replay-next qualifier low on both second attempts.
  Attempt cardinality alone did not identify the cause of refiring.
- Prevention: require an exact upstream replay/nack qualifier correlated with
  the retained token, PC, address, and attempt before describing a pinned trace
  as replay. Keep retry and architectural replay terminology separate.
- Detection: instrument the direct pinned signals first and treat an all-zero
  result as a candidate no-go, not proof that replay never occurs.
- Evidence: T-0042 exploratory Rocket replay trace and
  `docs/log/2026-08-13.md`.
- State: the exploratory hook was removed; replay remains open under ADR-0045.

## A TileLink denied response need not become a precise CPU exception

- Symptom: manager-side denied/error injection appeared to offer a small
  post-A exception workload for the pinned Rocket.
- Cause: the current owned manager does not advertise `mayDenyGet`, and the
  pinned Rocket DCache reports uncached denied/corrupt D responses through its
  bus-error output rather than `s2_xcpt.ae`, which is the Rocket WB access-
  exception input.
- Prevention: survey manager capabilities, TileLink monitors, DCache response
  handling, and core exception wiring before designing an error stimulus. Do
  not infer a precise architectural exception from a manager D error.
- Detection: require a legal monitor-clean A/D path and an existing precise
  request-identity-to-WB-exception path; otherwise classify a manager-only
  injection as no-go.
- Evidence: T-0042 pinned `RaveilOwnedTLMemory`, DCache, and RocketCore source
  inspection recorded in `docs/log/2026-08-13.md`.
- State: manager-only injection was rejected. Adding precise DCache/Core error
  semantics would be a larger mechanism and needs an ADR decision before use.

## Mode-specific patches must not fall through into a neighboring mode

- Symptom: the first BOOM misaligned-rollback build applied its own LSU patch,
  then stopped fail closed while attempting to apply the BOOM load-lifecycle
  patch to the same source.
- Cause: the shared runner selected the new patch in one branch but left the
  neighboring lifecycle patch application outside its matching mode branch.
- Prevention: keep `apply --check` and `apply` together inside each exact mode
  branch, and give an incomplete source cache a new dedicated volume name.
- Detection: require the mode/config/volume tuple, exact ordered patch set,
  and post-patch source hash before building or reusing a ready marker.
- Evidence: T-0042 BOOM misaligned-rollback runner's initial fail-closed build
  and the corrected dedicated `build-v2` run recorded in
  `docs/log/2026-08-13.md`.
- State: corrected; the unrelated long-running Docker workload and prior
  incomplete cache were not stopped or deleted.

## A BOOM ROB index alone is not lifecycle identity

- Symptom: the first later-request guard for the BOOM misaligned-load probe
  stopped on a request that matched only the retained ROB index, leaving the
  event's relationship to the retained context ambiguous.
- Cause: a finite ROB coordinate alone cannot distinguish the retained uop
  context from later index reuse, and the repository sequence is not carried
  into the DCache request bundle.
- Prevention: within a bounded exact workload, qualify a candidate-relative
  request with every available retained field: ROB index, LDQ index, PC, and
  address. Keep those fields as context rather than promoting them to durable
  identity.
- Detection: emit a separate request record and require exact event order,
  cardinality, and field correlation in the verifier. Preserve the limitation
  that same-context reuse outside the bounded trace is not excluded.
- Evidence: the T-0042 BOOM misaligned-rollback feasibility runs. After the
  guard was expanded, the final exact trace did match the complete available
  tuple and is recorded in `docs/log/2026-08-13.md`.
- State: corrected for the exact bounded workload; general stale-response and
  index-wrap handling remain open.

## A stale queue payload must not qualify a new lifecycle candidate

- Symptom: the first complete BOOM store trace passed its intended four events,
  then a later unrelated store commit stopped on an authorization-context
  assertion.
- Cause: the candidate predicate compared only the STQ address payload. BOOM
  retains stale address bits after clearing an entry, so an invalid entry could
  still equal the audit address when the commit head advanced.
- Prevention: require both queue-entry validity and address validity before
  reading payload fields as candidate context. Keep exact mode patches inside
  their own apply/check branches.
- Detection: run the complete workload past the intended terminal event under
  assertions, then require a successful process exit and exact event
  cardinality; do not accept an apparently complete prefix.
- Evidence: T-0042 BOOM store-authorization fresh RTL attempts recorded in
  `docs/log/2026-08-13.md`.
- State: corrected; fresh and cached exact runs exit 0.

## BOOM uncached loads cannot supply this speculative post-request stimulus

- Symptom: a wrong-path BOOM load to the owned PBUS address completed the
  workload with zero lifecycle records, so there was no accepted request to
  cancel or kill.
- Cause: BOOM marks the target uncacheable, suppresses the incoming speculative
  DCache request, and wakes that load only at the ROB/LDQ head. The older
  unresolved branch prevents the wrong-path load from reaching that point;
  redirect removes it first.
- Prevention: choose the memory class from the evidence question. Use a fixed
  cacheable scratch word for a CPU-local speculative request/kill diagnostic,
  and state explicitly that the owned manager is not exercised.
- Detection: require exact nonzero event cardinality together with an explicit
  memory-class and manager marker. Treat zero events as failed stimulus, never
  as cancellation evidence.
- Evidence: pinned BOOM LSU source inspection and the failed uncached T-0042
  post-request-redirect attempt recorded in `docs/log/2026-08-13.md`.
- State: corrected for the bounded CPU-local diagnostic; owned-path post-A
  cancellation remains open.

## Address-only BOOM lifecycle probes can conflate distinct instructions

- Symptom: after the intended request/response/redirect sequence, a correct-path
  load to the same cacheable scratch address qualified while the retained
  candidate was still live and triggered a context assertion.
- Cause: setup, speculative, and final validation loads intentionally reuse the
  scratch address. Address and live branch context did not uniquely select the
  wrong-path instruction.
- Prevention: inspect the exact ELF layout and qualify the bounded candidate by
  instruction PC plus accepted request and branch context. Keep PC, ROB/LDQ
  indices, branch mask, and lane as validation context, never durable identity.
- Detection: assert the expected label address in the runner, require exact
  event order and cardinality, and mutation-test both the PC and address
  predicates.
- Evidence: the T-0042 BOOM post-request-redirect feasibility runs and exact ELF
  disassembly recorded in `docs/log/2026-08-13.md`.
- State: corrected for the exact workload; general replay, stale context, and
  durable transport identity remain open.

## Promotion checklist

At milestone review, promote a lesson here when all are true:

- the behavior was observed or the rejected path is recorded;
- repeating it would waste meaningful time or threaten correctness/evidence;
- the prevention or detection advice is specific;
- an authoritative code, test, T-ID, ADR, EXP, or log locator exists.

Do not add generic advice, unverified folklore, secrets, personal data, exploit
details, or copied third-party text.
