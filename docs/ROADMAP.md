# Raveil gated roadmap

Status: planning record
Last updated: 2026-09-02

Gates are evidence requirements, not calendar promises. Passing a later-looking
prototype does not waive an earlier correctness or reproducibility gate.

## Current research reset and delivery focus

State: **T-0128 bounded operator-to-RTL vertical MVP is canonical; no Product P0 is active and T-0044 physical research remains blocked**

The first Experience measurement campaign began before the CPU/ISA thesis,
matched controls, observation points, and candidate microarchitecture were
fixed. Its negative evidence remains valid for its narrow preregistered
Experience hypothesis, but it cannot answer whether low-level explicit-graph
execution can simplify or outperform an in-order or OoO CPU. More measurement
or process-demo work would repeat that ordering error.

The corrected critical path is:

The 2026-08-23 Sprint coordination audit does not reopen T-0042 or alter this
critical path. One already-active BOOM stripped-token negative is retained as
bounded T-0106 carry-in evidence. S01 now passes current-main RTL acceptance
and independent replay and is complete, but it does not satisfy the trigger
for further T-0106 implementation. The active
Research delivery remains T-0044's post-EXP-0010 integrated physical boundary.
The first S08 implementation now elaborates and functionally verifies the
Static Graph/Rocket/common-owned-memory hierarchy and passes a matched RTL
structural preflight. S10--S12 add fail-closed readiness, identity/denominator,
oracle/budget, physical-condition, typed physical estimator, fixed decision,
and evidence-protocol validators. None collects or claims whole-system area,
timing, energy, FPGA, ASIC, silicon, or performance results. The next boundary
is HCI-02 immediately before EXP-0011 allocation or freeze.
The owner granted HCI-02 on 2026-08-24, but S13 stopped before allocation under
the preregistered missing-physical-input rule. All seven required common memory
macros lack the Liberty timing and LEF geometry/pin views required by the P&R
estimand in the pinned public image, although the standard-cell, technology,
and RC inputs are present. Matching GDS files are also absent but are
supplemental to this pause. The integrated physical
gate is therefore **pause-boundary before data**. It may resume only with one
reviewed common memory implementation/view set bound identically to both
candidates; placeholder or candidate-only macro conditions are prohibited.
S15 supplies a deterministic repository-owned functional source and structural
collection preflight for all seven required macro types. It does not satisfy
that resume condition by itself. S16 now demonstrates that the actual
integrated and matched-Rocket hierarchies resolve the same source at all eleven
exact paths with complete clock/mask connections, the same Rocket identity,
approved clock roots, and zero reachable blackboxes, and it seals the complete
pre-data evidence chain. It still deliberately stops before memory mapping,
synthesis, and P&R. The required Liberty/LEF physical views do not exist, the
future mapped-netlist postconditions have not been exercised, and the physical
denominator has not been re-frozen or reviewed. S13 therefore remains
**pause-boundary before data** and EXP-0011 remains unallocated.

Start timing is governed by the canonical phase table in `TODO.md`. ADR-0061
now permits two explicitly independent P0 delivery lanes. T-0122 has completed
the simulation-first operator path from canonical artifact through a
transport-neutral runtime and Verilator device to Pavane validation. It uses
new task-neutral interface files and treats the existing compiler, oracle, RTL
core, scratchpad, and every T-0044 file as read-only. T-0044 separately retains
the matched physical Research line, but S13 remains blocked before EXP-0011
allocation or data until a reviewed common memory implementation/view set
exists. S14 is complete with no compatible candidate identified. OpenRAM remains a
possible generator for a separately reviewed proposal, not an adopted view set;
the blocked S13 resume condition and all pre-data confirmations are unchanged.

T-0123/S01 and S02 pass their exact scoped RTL-simulation acceptance. ADR-0063's
separate task-neutral install ABI configures baseline and compact bounded
shapes/strides while preserving the byte-identical execution ABI and one
executor image. The generated schedule remains observation-only. ADR-0064's
S03 implementation preserves both existing ABIs byte-identically, adds a
separate bounded program-installation ABI, and compiles the three external
Graph JSON files into one generic sequential interpreter RTL. The compact case
changes both affine shape/stride and program. Its primary receipt is
  `rtl-simulation-functional` only. Exact-head review approved it and PR #26
  merged at `0cd2c890`. T-0123 therefore closes only the bounded progression to
  the frozen three Graphs on one executor; no broader generality or performance
  result exists. T-0125 makes that capability understandable in one command
  while preserving the accepted
  RTL, ABI, Graph, compiler, runner, receipt, and non-claim boundaries. Its
  first mutation owner was stopped after two incomplete acceptance packets.
  The owner-authorized HCI-07 transfer to Jitro is now exercised: the four-file
  candidate passes focused tests, primary and independent presentation of the
  accepted S03 receipt, and read-only evidence-closure validation. Issue #27 is
  closed after independent exact-head review and PR #31 merged as canonical
  commit `770a299b`. T-0125 therefore completes only the bounded operator
  presentation; it adds no Graph generality or performance result. T-0126 and
  T-0127 change only Project execution coordination and agent enforcement;
  neither alters this research
  or product gate.
T-0128 is split into serial child slices rather than one large delivery item.
S01 was the only promoted child and merged through PR #37 at canonical commit
`748debee`: it admits exactly one of the three accepted
descriptor byte/program identities through the top-level CLI and emits a
non-executing host envelope. It changes no ABI, Graph JSON, compiler/oracle,
RTL, runtime transport, or evidence receipt. S02 was then separately packeted
as Issue #39 and completed as a five-SP slice. It maps one admitted frozen
Graph and seed onto the existing program/config/execution ABIs, installs and
runs only that selected program under Verilator, and binds private output to the
direct oracle, generic fallback, eight hardware rejection cases, source, RTL,
simulator, dependency-cache, and environment identities. Two primary selected
Graph replays, one independent selected replay, and the existing fixed matrix
pass at `rtl-simulation-functional` evidence. Exact-head Security and Tester
reviews found no blocker; PR #40 merged canonical commit `1a3ad369`. S03 was
then separately packeted as three-SP Issue #42. It adds a thin
top-level CLI that invokes the unchanged selected runner, requires one strict
private marker, revalidates the raw receipt, and displays oracle agreement and
all eight boundary faults. The exact vertical-three-point/seed-7 demo passes;
an independent five-point/seed-83 replay also passes. Exact-head Security and
Tester reviews found no blocker; PR #43 merged canonical commit `25d094bc`.
S03 and parent T-0128 are complete, no Product P0 is active, and no future work
inherits authority merely from the parent identifier.
T-0106 remains P2 only after T-0044 survival or an accepted product trigger.
P3 future-planned and P4
optional/triggered work cannot enter either lane merely because a branch or
partial implementation already exists. Canonical record integration, PR
acceptance, and merge remain one serial Project Manager boundary.

1. **T-0105 — reproducible substrate (complete):** the owned counter and pinned
   unmodified Rocket reference now elaborate and execute under fixed
   Docker/Git/Nix inputs. All 16 `rv64mi-p` functional tests pass. This proves
   tooling and RTL simulation correctness only.
2. **T-0057A — direct-prior-art boundary:** inventory conventional OoO,
   EPIC/VLIW, TRIPS/EDGE, WaveScalar, DySER and spatial-CGRA mechanisms with
   exact locators, counterevidence and preliminary patent/IP triage. This may
   reject mechanisms; it does not authorize adoption.
3. **T-0057B — hypothesis and contract (simulation-only accepted):** RFC-0005
   and ADR-0039 fix one
   low-level, fixed-latency static operation/effect region and a memory-heavy
   five-point stencil that does not predetermine a win, including exact alias,
   private-output, fallback, oracle, accounting, and no-go rules. The
   mechanism-specific review authorizes only repository-owned functional RTL
   simulation and makes no patent/FTO conclusion.
4. **T-0042 — owned RTL adapter (complete):** the smallest admitted static
   Graph executor now matches an independent oracle and survives
   cancel/restart in Verilator. A strict common functional adapter v2 now makes
   missing lifecycle accounting and unmatched memory/resources explicit and
   refuses comparison readiness. ADR-0046 resets the critical path to the
   smallest controlled-run comparison boundary: equal owned ports, buffering,
   request capacity, arbitration, width, and response rule for Rocket, BOOM,
   and Graph; quiescent execution-window bracketing; rejection of unaccounted
   traffic; and complete six-phase/total-cycle records. General per-operation
   semantic attribution is not claimed. Further reset/stale/duplicate/replay/
   rollback and arbitrary-initiator hardening moves to T-0106 and does not gate
   T-0042 closure or T-0044 entry. Pinned BOOM, the
   same-core diagnostic semantics and licenses are source-verified through
   ADR-0040. `SmallBoomConfig` now elaborates to FIRRTL containing `BoomCore`
   and executes a minimal RV64 sum/store/load/check ELF to successful `tohost`
   completion in both normal and CSR-verified serialize-dispatch modes. Matched
   semantic stencil outputs are also validated for both BOOM modes, but their
   v2 records correctly remain cache-backed and comparison-ineligible. The
   pinned Rocket control now validates the same 256-word stencil signature and
   emits the same honest unmatched record class. ADR-0042 additionally moves
   every CPU control's buffers onto the inherited common subsystem TLRAM and
   validates them, but correctly leaves end-to-end latency and resource matching
   unverified. A passive post-fragmenter observer now confirms matched A/D
   source correspondence and one-cycle bank-local intervals for the read beats
   seen in one pinned run, while also exposing that no write beat and no
   initiator/phase attribution are available there. ADR-0043 now implements
   and verifies the first standalone owned local transaction target with
   read/write, backpressure, attribution, accounting, and a one-cycle
   module-local response property. The static Graph region now uses disjoint
   input/private-output logical regions in one physical owned instance for
   staging, execution, validation, and cancel/drain/restart. The ADR-0046
   controlled slice now connects dedicated Rocket and BOOM paths to the same
   canonical one-bank, one-port, 32-bit, four-byte-operation,
   maximum-one-outstanding contract with no request buffer, one held response,
   no owned-ingress arbitration, and the same module-local response rule.
   Exact oracle, quiescence, traffic conservation, and complete six-phase
   records pass for all three. The aggregate verifies resource equality and
   bounded functional comparison eligibility, but dynamic execution traffic
   differs (Graph 1,536; each CPU 1,056), so T-0044 measurement readiness and
   every performance claim remain false. ADR-0044
   defines the first CPU translation step as a repository-owned 32-bit
   TileLink manager on the uncached peripheral path in dedicated Rocket and
   BOOM configurations. It is observable by design but explicitly unmatched;
   elaboration now has direct monitor-enabled protocol tests for the owned
   manager. The same phase-fenced RTL workload now traverses the mapped manager
   on both Rocket and BOOM and validates full/partial writes, reads, phase
   selection, and aggregate counters with identical decoded signatures. Exact
   generated-graph verification and runtime A/D audit registers now observe
   only each config's DCache-MMIO client range for the eight data transactions
   and preserve accepted/completed phase 2/2. This is topology-dependent
   client-class evidence, not semantic initiator proof. Semantic initiator
   attribution and matched common-memory topology remain. A standalone
   post-fragmenter TileLink-to-owned bridge now verifies the mechanical
   request/response translation, TileLink source/size retention, explicit
   initiator/phase handoff, backpressure, range denial, and 6/6 conservation.
   Its attribution is harness-supplied and neither CPU is connected, so it is
   a prerequisite rather than semantic initiator or resource-match proof.
   Direct manager protocol V4 additionally separates a half-open expected
   source range from deliberate lower/upper boundary sources with 3/3 versus
   4/4 conservation and blocks same-source reuse while D is pending. This is a
   harness-local negative classifier diagnostic, and its untagged raw client
   completes as DCache-origin 0/0 versus non-origin 7/7. Repository-owned hooks
   now insert a structural request marker immediately after each DCache and
   before the shared tile master Xbar. Both CPU signatures observe origin 8/8,
   non-origin 0/0, in-range final sources, and phase 2/2. This proves bounded
   structural DCache origin rather than target-ELF semantic intent. A second
   test-only harness now drives origin true upstream, removes the negotiated
   field before the manager, and completes as origin 0/0 versus non-origin 7/7;
   metadata loss therefore fails closed in this bounded transport model.
   A dedicated four-byte writable PT_LOAD now exercises one actual pinned
   SimTSI/FESVR transport path without `+loadmem`: its two aligned transport
   requests complete as serial-class origin 0/0 versus non-origin 2/2 before a
   CPU read adds one in-range DCache-origin completion. This is a bounded
   loader-path negative, not complete loader/debug exclusion or target-ELF
   semantic identity. One repository-owned DMI sequence now also performs an
   8-bit Debug SBA write in both CPU configurations; exact topology and runtime
   accounting separate the Debug client class from the following tagged DCache
   read at 1/1 each. Durable semantic attribution and remaining loader/debug
   negatives remain open in T-0106; those diagnostic paths are not the later
   ADR-0046 controlled resource-equality proof. A cross-workload audit now
   demonstrates that two distinct ELFs reuse the same exact DCache source in
   each CPU configuration, so source/origin cannot be promoted to ELF identity.
   ADR-0045 fixes the next boundary as CPU-owned, commit-aware token correlation:
   replay retains identity, kill/exception/reset fails closed, and load/store
   attribution requires the applicable architectural retirement and memory
   completion; stores additionally require CPU-specific authorization. A
   standalone repository-owned Rocket ledger now passes these state-machine
   cases with synthetic events and an exact fail-closed marker verifier. The
   first pinned Rocket request/response/WB probe now supplies bounded positive
   RTL evidence for accepted store/load requests, captured DCache tags, a
   separately matched load response, and WB retirement. A second pinned probe
   covers one same-cycle accepted-request/MEM-redirect negative by recording a
   killed wrong-path store with no WB retirement and equal completed loads
   before and after the probe. A third exact-config diagnostic directly observes
   the following-cycle Rocket `s1_kill` for that request and separately records
   two successful owned-manager load A/D pairs with no probed-address Put in the
   bounded log. It carries no Rocket token into TileLink. A fourth pinned probe
   correlates one accepted misaligned load with its later WB misaligned-load
   exception and exact trap recovery, while explicitly leaving post-A fate
   untested. Multi-live-token overlap, pre-request kill, post-A exception or
   rollback, replay, reset/epoch, durable DCache/TL token correlation, store
   authorization and complete owned-D lifecycle coverage remain to be
   implemented. The first pinned BOOM positive now correlates one exact LSU
   DCache load request, its response, and architecturally valid ROB commit by
   repository sequence. It carries no token through DCache/TileLink and leaves
   BOOM replay, reset, and same-token store cases open.
   A second pinned BOOM diagnostic covers one narrower negative ordering: an
   exact misaligned-load candidate is correlated with its LSU exception, one
   matching DCache request accepted after the exception, and the later global
   ROB rollback state, with no matching response or architectural commit. The
   faulting entry is not a rollback-row match. Because exception precedes
   request acceptance, post-request BOOM exception/cancellation and general
   rollback remain open. A third pinned BOOM diagnostic now observes the exact
   local ROB/STQ store-authorization transition through DCache request,
   response, and STQ clear, while a separate manager audit observes the exact
   Put A/D pair and readback. Since the local sequence is not transported,
   same-token owned-manager D completion and complete store attribution remain
   open.
   A fourth pinned BOOM diagnostic uses one exact cacheable wrong-path load and
   correlates accepted LSU DCache request, response, and later branch kill while
   forbidding architectural commit. It does not exercise the uncached owned
   manager, carry a token to TileLink, or prove post-A cancellation.
   A fifth pinned BOOM diagnostic carries only the local store's
   `{valid, epoch, sequence}` through the DCache and uncached TileLink request,
   then retains the same token from the exact owned-manager Put A acceptance to
   its D completion. This is one fixed-epoch, single-store transport witness;
   it does not promote ROB/STQ/PC/source context, implement reset/stale/replay
   policy, establish Rocket parity, or connect semantic initiator authority to
   the common bridge.
   A sixth pinned BOOM diagnostic negotiates the same request fields while
   deliberately omitting the LSU/I/O-MSHR producer. The committed store and
   readback complete, but manager A/D both retain invalid/zero metadata and
   classification remains unknown. This closes one absent-producer default
   case only; stripping after a valid producer, malformed nonzero metadata,
   epoch/reset/stale/duplicate/exhaustion, replay/source reuse/backpressure,
   non-CPU traffic, parity, and semantic promotion remain open.
   None of these functional smokes or endpoint diagnostics is a performance
   or structural-ablation result.
5. **T-0044 — matched comparison:** compare in-order RISC-V, conventional OoO,
   valid same-core diagnostic ablations, and static/elastic/stream/hybrid Graph
   organizations with matched semantics, cache/memory, functional resources,
   and correctness checks. EXP-0005 completed only the first 1/4-fresh-input
   static/Rocket/BOOM latency/traffic pilot plus BOOM serialize-dispatch
   diagnostic. The primary execution window is eligible: Graph records exact
   3,073 cycles versus Rocket 14,621 and BOOM 21,892, while its 1,536 versus
   1,056 transactions is explained by lawful CPU load reuse. EXP-0006
   completed a four-input commissioning of all candidates under one
   installed configuration without simulator reboot. Its execution-window
   latency/traffic evidence is eligible, but CPU-local versus Graph-testbench
   input generation left staging and end-to-end meaning unresolved. ADR-0047's
   common fixture provider and frozen EXP-0007 complete 1/4 commissioning now
   pass the same-meaning staging boundary. The bounded decision is `advance`
   to a separately preregistered 1/4/16/64/256 campaign. The pilot does not
   implement the remaining organizations or collect energy, synthesis timing, or area, so
   T-0044 remains open and no go/no-go follows.
   EXP-0008 now owns that campaign as one 256-input installed session with
   nested prefix reports and paired latency estimators. Its implementation,
   manifest, and first RUN-ID were frozen before RTL collection. That attempt
   sealed an operational timeout after all primary sessions completed; a
   separately frozen recovery may import those exact primary raw hashes and
   rerun only the diagnostic serialize session. It may not alter the estimator,
   decision thresholds, RTL, ELF, or sample count. Recovery is now complete:
   the 64-input correct-latency upper 95% bound is 0.2086002 versus the frozen
   1.05 threshold, and break-even is invocation 1. The bounded result is
   `advance-partial-latency-traffic`; matched energy/timing/area, IP, and the
   other organizations remain the open T-0044 gates. ADR-0048 selects a
   partitioned Graph/Rocket area/timing lower-bound screen as the next gate and
   forbids Graph-island energy promotion. EXP-0009 has passed only its
   candidate-independent toolchain commissioning and now freezes a separate
   Graph/Rocket Stage-B manifest from committed authority. Bounded attempts
   produced no candidate datum and paused at Yosys-visible common-partition
   selection. A pinned-tool, candidate-independent probe now proves named-
   module selection, single instances, and black-box attributes for both common
   partitions; its collector-only
   repair awaits a recovery-v4 freeze before Graph data, Rocket remains unrun,
   and the complete matrix is still open.
   Recovery-v4 then reached mapping but sealed a library-unaware post-map check
   failure before statistics/STA. Candidate-independent toy probes identify a
   collector-only Liberty/OpenSTA compatibility correction, which requires a
   new freeze; no physical datum or roadmap gate has advanced.
   That correction reached sealed raw reports, but derivation rejected two
   implicit OpenSTA common-module declarations. Explicit exactly-once stubs are
   the remaining collector boundary; contained raw numbers remain ineligible.
   Recovery-v6 then produced one complete Graph-partition synthesis estimate,
   while Rocket failed before synthesis on generated packed-array syntax. The
   matrix and roadmap gate remain open. A hash-bound upstream physical-export
   lowering with identical shared elaboration must be frozen, followed by fresh
   Graph and Rocket runs under the same manifest; the prior Graph partition
   result is not a reusable matrix sample.
   The first isolated lowering build completed but publication stopped on
   non-semantic cache-root and file-list-order differences. A narrowly verified
   normalization recovery remains pre-data and does not advance this gate.
   The normalized Rocket export and pre-synthesis Yosys probe now pass; only a
   frozen shared-lowering identity and fresh paired synthesis can advance it.
   Recovery-v7 now freezes that identity; the gate still awaits both fresh
   partition results under the same manifest.
   A wrong-directory `run-009` exposed post-container input validation; the
   pre-container preflight and verified private-snapshot recovery are mandatory
   before the paired run and do not advance the gate.
   Recovery-v8 freezes that collector-only correction; the gate still awaits
   two fresh, complete partition results under v8.
   V8 produced a complete Graph partition and sealed Rocket raw evidence, but
   the Rocket derived checker failed on unrelated module-area rows. The gate
   remains unchanged pending an exact-top parser recovery and fresh same-
   manifest pair.
   Recovery-v9 freezes the parser-only correction; the gate awaits the fresh
   v9 pair and remains open.
   The v9 pair is complete but yields `pause-boundary`: incremental area is
   below the no-go threshold, while only Graph meets the common 20 ns target.
   Gate 1 remains open pending one timing-boundary resolution; this is neither
   an advance nor a candidate early-no-go.
   EXP-0010 is the pre-data, single-40-ns follow-up for that point. It cannot
   change the EXP-0009 outcome and cannot advance the gate before a fresh,
   complete same-manifest pair.
   The EXP-0010 40 ns manifest is now pre-data frozen in content; fresh paired
   collection begins only after its commit and cannot reuse EXP-0009 results.
   EXP-0010's fresh pair now passes its bounded screen and advances only to the
   integrated physical boundary. Gate 1 remains open until that complete
   composition is implemented, closed, and measured without missing parts.
   T-0044/S08 now supplies the first integrated implementation prerequisite:
   one generated top contains Graph incremental logic, Rocket fallback, the
   common fixture/provider and owned memory, selector/adapter,
   cache/interconnect, and common external clocks/reset. Candidate-mode RTL
   smokes and a matched integrated/Rocket structural preflight pass. Gate 1
   remains open because this is functional, structural, and host contract-
   validation evidence, not a frozen integrated physical experiment. S10--S12
   now close the bounded readiness, identity/denominator, typed estimator,
   fixed decision, and evidence-protocol review. HCI-02 applies before
   EXP-0011 allocation or any claim-bearing physical collection.
   Separately, ADR-0050 separates the locally sealed EXP-0008 result from
   durable promotion: both
   the retained failed RUN and completed recovery RUN need immutable remote
   copies, download checks, completion markers transferred last, and a tracked
   non-sensitive receipt. That durability step gates external promotion and
   T-0044 closeout, not the next reversible preregistered local experiment; it
   never authorizes a deterministic simulator rerun as another sample. The
   campaign-specific verifier and fake-rclone failure suite are implemented;
   both RUNs now pass immutable remote copy, download verification, and
   marker-last readback with a tracked receipt. This closes the durability
   sub-gate only; energy, timing, area, IP, and missing organizations still
   prevent T-0044 closeout.
   ADR-0049 does not modify frozen EXP-0008, EXP-0009, or EXP-0010. Even after
   EXP-0010's bounded advance to the integrated physical boundary, transition
   remains closed until a separately frozen CGRA
   non-reinvention gate compares a reviewed public configurable control, runs
   three distinct graphs without RTL regeneration, proves CPU/backend contract
   parity, and accounts for compilation/configuration/PPA cost. Failure stops
   custom Graph hardware but preserves Raveil as a portable contract/runtime
   over existing CPU and reviewed configurable backends.
6. **T-0106 — conditional attribution hardening:** only after T-0044 survival
   or an accepted untrusted/concurrent product requirement, complete the
   general ADR-0045 token lifecycle matrix. It is not on the first-comparison
   critical path.
7. **Transition only after physical and non-reinvention survival:** prefer a
   thin adapter to an adequate reviewed CGRA/VLIW/NPU implementation. Build an
   attached engine, custom RISC-V extension, programmable fabric, or separate
   ASIC plane only if the recorded gap cannot be closed by that adapter and the
   custom backend earns its measured or enforcement difference. ARM-hosted
   software is transition/product evidence, not evidence about hidden CPU
   internals.

No performance campaign begins before its comparison contract,
instrumentation, confounders, and stopping rule are recorded. Smoke tests may
establish build and functional correctness only. Simulation, synthesis
estimates, FPGA results, and silicon measurements remain separate evidence
classes.

The Native CLI, T-0103 synthetic tool/process showcase, Sonatine, and EXP-0003
remain preserved artifacts. T-0104 production tool-cache work and further
shell growth are deferred while the critical path above is tested. Sonatine
remains a later OS/capability backend unless evidence makes it necessary.

## Playable pillar — Raveil Garden TUI

State: **T-0117 and T-0120 complete at host-functional evidence**

T-0117 creates a host-native, read-only TUI over one strictly validated graph
snapshot so the Playable pillar has a visible object a hobbyist can run and
inspect. The first slice shows topology, dependencies, variants, evidence
labels, and demo commands with deterministic terminal behavior. It reuses the
owned schemas and guarded graph state, but has no execution, mutation,
approval, Experience-promotion, task, or gate authority.

The S01 canonical commit `bb1631109842f85b2a958ebcf30e5ee6a1b5312f`
implements the strict versioned snapshot,
canonical-variant validation, deterministic bounded navigation, and explicit
empty/error states without an external TUI dependency. S02 reproduced the
normal TTY view, deterministic navigation and exit, empty state, malformed
input refusal, evidence labels, and 35 scoped tests from a clean checkout of
that revision. This is host-functional Playable acceptance only.

Garden is distinct from T-0093's static graph directory projection and from
T-0103's synthetic timing showcase. Its host-functional evidence cannot imply
Graph hardware performance, OoO effects, FPGA behavior, or silicon behavior.
The TUI may later consume T-0093 output if that task completes, but neither is
an acceptance dependency of the other unless a later decision records it.

T-0120 is a bounded Playable refinement, not a reopened T-0117 acceptance
slice. It adds deterministic wide and stacked workspace layouts while keeping
the same observe-only snapshot, compiler-validation, and authority boundary.
Its 40-test clean acceptance, independent review, and reproducible static
capture are complete. It does not change any research or hardware gate.

T-0121 is a deferred P2 follow-up. Its local Graph Canvas draft is preserved,
but the project will reconsider Garden as an actual Linux/macOS TUI, including
library, color, focus, and graph-layout choices, after the critical path. The
canonical dependency-free Garden CLI remains available meanwhile.

## High-priority demo extension — Sonatine native operator shell

State: **T-0092 complete (QEMU emulation correctness)**

T-0092 turns the existing U-mode command prompt, two-node capability VFS, and
bounded Sonatine graph lifecycle into one visible operator demo. The target
surface is `ls`, `cat`, `echo`, `write`, `stat`, `jobs`, `run`, `cancel`, and
`result`. Filesystem output must be derived from VFS state. Graph commands must
report real bounded lifecycle states and may use only a fixed built-in demo job;
`cancel` must never report success without a real transition or an explicit
`EMPTY`/`TOO_LATE` result.

Ciste implements and freezes the Sonatine/QEMU serial contract first. Lifri may
then add a host-side runner that launches the pinned QEMU command, drives the
fixed transcript, validates versioned machine-readable frames, and writes one
exclusive replayable JSON record. The record is QEMU emulation correctness,
not performance or production evidence.

This work reuses current owned code only. BusyBox remains an optional external
GPLv2 reference and is not imported or linked for this slice. No ELF loader,
fork/exec, pipe, signal, tty, general argv/environment, POSIX compatibility,
arbitrary user pointer, new Gate claim, or RK3588 replacement enters T-0092.
The exact ownership, acceptance transcript, and sequential handoff prompts are
in [`guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md`](guides/T-0092-SONATINE-NATIVE-SHELL-DEMO.md).

The completed slice uses a distinct current-task-bound demo broker capability,
real two-node VFS operations, and one fixed 2x2 integer GEMM lifecycle through
the existing job, completion, Experience-observation, byte-shadow approval,
commit, cancellation, and rollback seams. A strict host runner accepts only the
18 expected versioned frames and exclusively publishes one
`raveil.sonatine-demo-result/v1` record bound to the kernel and input hashes.
This closes the operator demo only; it does not advance Gate 3 or Gate 4.

## Queued visibility side project — graph directory view

State: **T-0093 complete; non-blocking**

T-0093 exposes one validated graph snapshot as an ordinary read-only host
directory so a person can inspect program, contract, node, variant,
memory-plan, proposal, selection, and result relationships with `find`, `tree`,
and `cat`. The materializer consumes only strict existing v1 artifacts, emits a
root manifest with source and output hashes, uses deterministic collision-free
names, and refuses stale lineage, symlinks, traversal, nonempty targets, and
overwrite.

The first slice is a generated inspection artifact, never an authority or
database. It does not mount FUSE, expose a writable graph filesystem, add a
Sonatine VFS namespace, execute a graph, ingest Experience, or make a
performance/security claim. A live `/graphs` namespace requires a later ADR
covering snapshot consistency, capability visibility, lifecycle, and
write-back prohibition; T-0093 deliberately does not pre-decide it.

PR #70 merged the bounded ordinary-directory slice as canonical commit
`4db3a1e`. This completion records host-functional inspection behavior only;
the later live `/graphs` decision remains intentionally unmade.

## Post-MVP side project — ReactOS portability probe

State: **Planned; non-blocking**

T-0091 preserves a ReactOS user-mode port as the first deliberately non-POSIX
host probe after the GNU/Linux MVP. It tests whether the same Raveil-owned v1
graph artifacts and guarded baseline/proposal/abstention/verification/rollback
loop survive an NT-compatible OSS environment without moving OS-specific types
into the owned contracts.

Entry requires the current GNU/Linux/macOS host regressions and exact v1
artifact-lineage tests to remain green. The first probe runs in an isolated
x86/x64 virtual machine because ReactOS documents itself as Alpha-quality and
recommends virtual-machine or non-sensitive test hardware. It may use a direct
Win32 CLI; a message-mode named-pipe adapter is optional and a kernel driver is
out of scope.

Exit requires a pinned ReactOS build and architecture, reproducible cross-build
command, one bounded graph run with trusted baseline-first semantics, semantic
checksum and explicit commit/rollback or abstention, fail-closed unsupported
API/candidate behavior, and replayable environment/result records. All results
are VM host-correctness and portability evidence only. They do not advance a
Gate, establish production Windows compatibility or isolation, reverse
EXP-0003, or substitute for the separate GNU/Linux/AArch64/RK3588 direction.

The port should depend only on documented Win32 interfaces or independently
implemented adapters. ReactOS is GPL-2.0-licensed; implementation kickoff must
revalidate the exact upstream version, license/provenance boundary, and any
source-reuse or IP-review gaps before importing code.

## Gate 0 — independently reproducible minimum seed

State: **Completed**

- all nine host/Python acceptance tests pass from a clean clone;
- release and explicit debug Sonatine Microkernel builds are reproducible;
- debug ELF contains line and debug information;
- native macOS or Docker QEMU smoke transcript is recorded in EXP-0002;
- command-line GDB attaches and stops at `kmain`;
- local CI covers Python, host C, freestanding RV64 build, and QEMU smoke;
- no generated evidence, build output, IDE state, secrets, or local absolute
  paths are committed.

Verified on 2026-08-08: clean native release/debug builds, separated release
and debug flags, DWARF `.debug_info`/`.debug_line`, release QEMU smoke,
command-line GDB stop at `kmain`, clean Docker build and Docker-contained QEMU
smoke. A fresh clone of public commit `3347087` passed all nine tests and both
build modes plus smoke. The same checks are available through
`scripts/ci-local.sh`; hosted CI/CD is intentionally deferred until the project
has multiple contributors and explicit cost approval. The public-tree hygiene
scan found no generated evidence, build output, IDE state, credentials, or
machine-local paths. The actual IntelliJ `Remote Debug` type was verified;
IDE-driven attachment is not a Gate 0 claim.

## Gate 1 — real Experience boundary

State: **Falsified (closed negative)**

The replayable pilot/full manifests, environment/measurement/policy schemas, 24
native-C holdouts, checksum harness, analysis functions, and immutable
raw-bundle lifecycle are implemented. A non-claim powermetrics pilot must
validate sampling and thermal stability before the full run. That pilot now
passes with a sealed and remotely verified bundle; a preceding sampler-startup
failure is also preserved. A sealed and remotely verified 24-workload history
source dataset and a first target policy comparison exist. The first target
run failed the 5% latency/energy improvement and positive bootstrap-lower-bound
criteria. The independent fixed-C rerun confirmed zero median latency/energy
improvement and additionally exceeded the NTR limit, so fixed-C now provides a
reproduced negative conclusion rather than a passing result. The pinned TVM
history/target execution reproduced zero median improvement and exceeded the
joint NTR limit, with immutable remote verification. The preregistered 5%
hypothesis is therefore falsified; this is not a claim that Experience is
universally ineffective. Compare cold prior, full-history nearest
neighbor, bounded Experience, FIFO, reservoir, and random under lineage, shape,
working-set, and composition holdouts. Report latency/energy HCR, NTR, coverage,
calibration, budget, retrieval cost, storage, and evidence class.

Exit requires all of the following in EXP-0003:

- every candidate passes its semantic reference checksum;
- bounded Experience improves holdout median latency and same-Mac estimated
  energy by at least 5% versus cold, and both paired-bootstrap 95% lower bounds
  exceed zero;
- a regression greater than 2% counts as negative transfer and joint NTR is at
  most 5%;
- bounded selection-quality degradation versus full history is at most 2% for
  both latency and energy;
- active memory remains within its limit and bounded retrieval p95 is below
  full history on large evidence;
- immutable local/Google Drive content verification completes, and an
  independent execution reaches the same conclusion;
- the fixed-C contract is repeated through a pinned official apache-tvm
  MetaSchedule adapter. A conclusion conflict triggers research review and
  keeps the Gate open.

## Gate 2 — minimal isolated Sonatine Microkernel slice

State: **Complete (QEMU emulation correctness)**

Make the platform contract explicit or parse the device tree; add Sv39, U-mode
`init`, context switching, timer preemption, blocking capability IPC, and
fault tests.

Exit: the current shell remains observable from U-mode and survives preemption
without a capability bypass.

T-0083 met this exit with a persistent scripted U-mode shell, real CLINT
`U -> idle -> U` resumption, current-task-derived syscall identity, and
kernel-derived rejection evidence for forged, wrong-owner, and insufficient
rights capabilities. This does not claim physical RISC-V isolation, S-mode,
multi-user fairness, or performance.

Filesystem and command-prompt growth follows this kernel line: a minimal VFS,
RamFS/initramfs, then—after the isolation/scheduling base is credible—VirtIO
block and a simple persistent filesystem such as FAT32. This is a staged
direction, not an implemented feature or production-OS compatibility promise.

T-0017 supplies the first step as a bounded two-node, pointer-free VFS seed.
VirtIO and persistent storage remain T-0018.

T-0089 completes the next command-prompt growth step without reopening Gate 2:
the persistent U-mode task now accepts bounded command lines, survives
preemption with partially entered input, and retains current-task capability
authority. This remains QEMU emulation correctness, not a new isolation or
performance claim.

T-0090 supplies a narrow explicit Sonatine/QEMU backend connection for the
existing userspace graph loop. It reuses Gate 3 job/completion/finalization
artifacts and Gate 4 owned frontend contracts, but supports only an 8-or-smaller
GEMM correctness seed with no timing. Gate 3 and full Gate 4 remain planned;
this adapter by itself did not provide byte-shadow or Four-plane authority.
T-0034 and T-0085 now supply those separate kernel seeds, but not a general
compiler, real device path, or performance completion.

## Gate 3 — connect authority and evidence

State: **Planned**

Remaining specialized-authority work is preserved but paused until the
userspace MVP exposes a concrete requirement. Existing T-0030 through T-0033
artifacts remain valid.

The T-0084 Linux harness is pre-Gate transport scaffolding only. It validates
the owned ABI envelope without claiming a JobDescriptor, device, or authority
path and therefore does not advance Gate 3 state.

T-0030 provides the bounded shared JobDescriptor/CompletionRecord schema, and
T-0031 provides a kernel-internal ObjectManifest/object-table/ring seed with
boot-scoped replay protection. T-0032 adds segregated append-only QEMU
completion telemetry without promoting it to active Experience. Gate 3 remains
Planned until byte-shadow execution, semantic verification, and Four-plane
write authorities are executable. T-0033 now supplies only the kernel-owned
metadata-shadow finalization and cancellation seed.

T-0034 supplies the boot-scoped Four-plane capability firewall and guarded
normal graph path, T-0043 supplies bounded semantic verification, and T-0085
supplies fixed byte-shadow publication. Gate 3 remains Planned because real
device transport/lifetime, persistent recovery, and non-seed authority
integration are still absent.

Define JobDescriptor, ObjectManifest, and CompletionRecord; add
submission/completion rings; append measured telemetry to Experience; implement
shadow execution, cancellation, commit, and rollback; enforce Four-plane write
authority.

## Gate 4 — one owned adaptive graph path

State: **T-0086 narrow vertical slice complete; full Gate remains planned**

Import one pinned real workload behind an adapter; define Raveil-owned
GraphVariant, MemoryPlan, OptimizationProposal, and ResourceCertificate; add
Miroirs Graph Compiler structural validation and Pavane Semantic Oracle differential checking; compare static,
elastic, stream, and hybrid execution models.

An AI-compute demonstration may then test a small Transformer, including
prefill/decode and memory-regime variants, if Gate 1 results justify it.

T-0086 intentionally precedes the full exit: it proves the product control
loop on an existing OS/ISA and replaceable native backend. It does not require
a new kernel, ISA, driver, FPGA, or complete graph compiler.

The verified slice now covers owned graph/contract construction, trusted
baseline-first execution, candidate proposal or abstention, structural and
checksum semantic validation, explicit candidate selection or rollback, and
segregated host-correctness evidence on GNU/Linux. It does not satisfy the
remaining full Gate 4 compiler, workload, resource-certificate, or semantic
oracle scope.

T-0041 additionally makes `GraphVariant`, `MemoryPlan`, and
`OptimizationProposal` strict versioned artifacts and rejects stale program,
contract, or candidate-set lineage before backend execution. This closes the
owned schema slice only; the Gate state and remaining exit scope are unchanged.

T-0043 supplies executable Miroirs structural admission and an independent
Pavane deterministic integer reference for the two bounded MVP graph families.
Native and Sonatine observations must match the owned expected checksum;
semantic approval is not inferred from backend self-report or timing. This
closes the current semantic-oracle slice, while full Gate 4 remains planned for
the pinned real-workload import, mapper/resource boundary, and broader compiler
scope.

T-0040 adds one pinned real-workload import under ADR-0032. A bounded,
repository-authored MLIR GEMM fixture is validated by IREE 3.11.0 and reduced
to the existing owned `GraphProgram` plus a strict provenance record before
the unchanged guarded graph loop runs. This closes the single-workload import
slice only; the mapper/resource-certificate and broader compiler scope keep
full Gate 4 planned.

## Gate 5 — hardware exploration

State: **Canonical T-0132/S01--S09 plus active S10 operator runtime-pair CLI; no FPGA or silicon evidence exists**

Profile stable software access patterns before considering an Experience
Processing Unit, FPGA fabric, or ASIC. Hardware claims require separate
simulation, FPGA, and silicon experiment records.

RFC-0004 proposes the pre-FPGA foundation. T-0105 established the generic
Chisel/simulator/RISC-V functional substrate independently; T-0057 bounded
direct prior art and IP risk, T-0042 implemented the bounded Graph RTL, and
T-0122 supplies the smallest operator-visible simulation path and T-0123/S01
adds generated-schedule observation without promoting FPGA evidence. T-0044 separately uses
matched RISC-V configurations under a common cache, memory, workload,
functional-resource, and correctness envelope. Rocket/BOOM remain candidate
references, not adopted product code, ARM equivalents, or proof that OoO can
be removed.

T-0132/S07 exports the current 16 KiB relative AXI4-Lite Graph-device top as a
double-emitted, source-bound SystemVerilog bundle. This closes only the
vendor-neutral RTL handoff prerequisite. Board selection, an absolute address,
clock/reset and pin integration, Vivado outputs, device-tree/UIO binding, and
real output-oracle equality remain later separately reviewed FPGA work under
ADR-0039 and ADR-0071.

T-0132/S08 is the next software-only product slice. It may make the Linux
runner request-independent only for the existing three catalogue Graphs and
uint32 seeds, with strict validation before UIO open. It cannot broaden the
Graph/program alphabet, change RTL or an ABI, or satisfy any board gate.

The reviewed S08 implementation passes host admission, ARM64 build, and
unchanged S05 Verilator replay checks. It still does not satisfy a KV260 or
FPGA gate.

T-0132/S09 is the next simulation-first product slice. It reuses the S08
request-root admission in the AXI4-Lite Verilator bridge and must demonstrate
two different accepted requests through one compiled simulator plus rejection
before AXI for malformed input. It may not create a persistent simulator
service, broaden the catalogue, change RTL or an ABI, or promote evidence
beyond RTL Simulation Functional.

T-0132/S10 exposes the accepted S09 behavior through the top-level operator
CLI for exactly two ordered requests. It must pre-admit both, independently
revalidate both receipts, and require one common simulator identity plus
rejection-before-AXI. It remains one build per invocation and cannot expand
into a general batch, cache, service, performance claim, or board work.

## No calendar claim

Early discussion estimated weeks for a shell/RamFS seed and roughly one to one
and a half months of concentrated work for a persistent QEMU prototype. Those
were rough feasibility estimates, not commitments, and production compatibility
would be substantially larger.
