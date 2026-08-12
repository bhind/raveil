# Failure knowledge

Status: reusable operational guidance
Last updated: 2026-08-12

This index captures short lessons that prevent repeated mistakes. It does not
replace raw experiment bundles, EXP conclusions, regression tests, ADRs, TODO,
or dated logs. Add an entry only when the failure is non-obvious and likely to
recur. Link to authoritative evidence instead of copying large logs.

Each entry records the symptom, cause or current explanation, prevention,
detection, evidence, and whether follow-up remains open. Unknown causes stay
labelled unknown.

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

## Promotion checklist

At milestone review, promote a lesson here when all are true:

- the behavior was observed or the rejected path is recorded;
- repeating it would waste meaningful time or threaten correctness/evidence;
- the prevention or detection advice is specific;
- an authoritative code, test, T-ID, ADR, EXP, or log locator exists.

Do not add generic advice, unverified folklore, secrets, personal data, exploit
details, or copied third-party text.
