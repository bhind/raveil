# Current status

Last updated: 2026-08-29
Development state: `unreleased`
Latest feature release: `v0.0000000000001` (`10^-13`), immutable historical seed
Current Pre-release: `v0.0000000000002`, T-0092 Sonatine operator demo,
published from `d59873cb8e27bf033b32a2a72d2fa3d04576dc79`
Current corrective Pre-release: `v0.0000000000003`, T-0096 interactive
control fix, published from `c8002cf4d87e6a0a907f9327dc42cce2c90e9673`
Current Native Pre-release: `v0.0000000000004`, T-0099 Native CLI workspace,
published from `3cfb13c762b51291d08d519126286aad078df7a1`
Current Command Graph Pre-release: `v0.0000000000005`, T-0101 Native Command
Graph, published from `8ba6c17794d27913b6c8f2b5318be6f6296488ac`.
Current Native CLI Pre-release: `v0.0000000000006`, T-0102 bounded Tab
completion, published from `5f3d8d0d0a3a609af7ffc25a8be40aeb78bf6524`.
Current Native showcase Pre-release: `v0.0000000000007`, T-0103 synthetic
Command Graph walkthrough, published from
`a3befaa94b74700ced444e7384057f2c1a43c4e1`.

この文書は構想ではなく、現行treeで実装されている範囲だけを記録します。

T-0109 reorganizes the root component summary and the canonical architecture
map without changing executable behavior or an accepted boundary. The records
now distinguish the portable owned thin waist, the two separate Graph surfaces,
guarded orchestration, replaceable execution adapters, Experience admission,
Sonatine's optional privileged profile, and isolated RTL research controls.
Every component table now uses a Ravel-derived code name followed by its plain
general function. The previously unnamed responsibility domains are Couperin
Contract Core, Chloé Graph Orchestrator, Alborada Measurement Observatory,
Rapsodie Host Bridge, and Tzigane Hardware Research Laboratory. These and the
existing Miroirs, Pavane, La Valse, Boléro, Daphnis, Ondine, Sonatine, and
Scarbo names remain documentation responsibility domains; their presence in a
table does not imply that a complete integrated subsystem exists or rename an
executable identifier.

## Development workflow support

Repository-scoped Project Manager, three Implementer, Tester, Performance
Reviewer, Security Reviewer, Researcher, and Librarian role definitions are
present. The read-only Librarian plus `raveil-context-librarian` skill rank a
small task-specific reading packet instead of loading all project records.
The Librarian is named Vreji and also reports prior-art similarity and IP-risk
gaps under ADR-0014 while remaining unable to decide infringement, legal
clearance, freedom to operate, or implementation approval.
Task-governance, Gate 0 evidence, and remote-release skills remain available.
These govern development workflow only; local IDEA/MCP endpoints and personal
Codex runtime configuration remain ignored.
T-0131 adds the repository-scoped `raveil-sprint-operator` that routes
Sprint audit, kickoff, continuation, correction, review, closeout,
retrospective, and next-pull work through the existing governance and queue.
Its phase reference uses `project_queue.py` for transitions, preserves Initial
SP and evidence classes, applies HCI-09 and every other HCI boundary, and
returns one stable receipt. The PM role is bound to invoke it at phase
boundaries. The skill validator, four PM/role boundary tests, 23 queue tests,
record checker, diff check, and live queue audit passed. PR #53 merged as
canonical commit `2cf5413`; Issue #52 is Closed and Project Done. This is
host-functional workflow configuration, not a measured delivery-speed or
autonomous-authority result.
T-0137 corrects an operational ambiguity exposed during T-0093: task PR review
and the weekly Sprint Review are separate phases. The task phase validates and
integrates exact-head work continuously without a per-task owner demo by
default; the scheduled weekly ceremony aggregates the Sprint's runnable
outcomes and alone applies ADR-0069's owner-visible disposition. Issue #72,
branch `fix/t-0137-sprint-review-boundary`, S-0003, two SP, and the Project
Manager own the bounded skill/workflow/record correction. This changes no
product code, research claim, evidence class, Gate, cadence, or authority.
The integrated correction implements that split in the skill router, phase reference,
WORKFLOW, and SPRINTS. Twenty-three queue regressions, the governance record
checker, diff check, and an equivalent Ruby YAML/frontmatter validation pass.
The bundled Python skill validator is not runnable because its host lacks the
validator's undeclared PyYAML dependency; no project dependency was added to
mask that environment defect. PR #73 merged exact reviewed head `74b1f27` as
canonical commit `e8b500e`; Issue #72 is Closed and T-0137 is complete. This
task completion is not a weekly S-0003 Review disposition.
T-0133 and ADR-0068 change the recurring Sprint ceremony from Sunday to
Saturday while preserving Monday-through-Sunday Iterations. The Sprint
operator reference now reserves Sunday for bounded record reconciliation,
failed-demo recovery, explicit same-item re-review, and Monday preparation;
Sunday does not authorize new closing-Sprint scope. PR #57 merged as canonical
commit `0416e15`; Issue #56 is Closed, Project Done, and the S-0001 review card
is Ready for Saturday 2026-08-29. This is host-functional governance and
changes no task, evidence, research, gate, Graph, performance, FPGA, ASIC, or
silicon conclusion.
T-0134 and ADR-0069 make the owner-visible Sprint review a separate fail-closed
boundary from successful command execution. The ceremony stays non-Done until
the actual output or interface is shown and explained, durable feedback is
classified and routed, and the owner explicitly chooses `Accept`,
`Conditional Accept`, `Carry`, or `Reject`. Every conditional item requires a
stable tracked destination. Issue #59 and branch
`docs/t-0134-owner-visible-review` carry this host-functional governance
correction. The owner's first conditional S-0001 feedback is T-0135, a P1
Product Backlog feature to explain baseline materialization versus fusion in
Garden without adding execution authority or making a performance claim.
The Skill validator, 27 focused queue/agent-boundary tests, record checker,
diff check, exact-head PR inspection, and live queue audit passed. PR #61
merged as canonical commit `b02402c22a27ad8c693d2153df19f52051656c72`;
Issue #59 is Closed and Project Done. T-0134 is complete at host-functional
governance evidence only.
The owner then conditionally accepted the S-0001 review after personally
launching Garden, navigating all three fixture nodes, and reviewing the
baseline-materialization versus fusion explanation. The review records 104
host checks, the Garden interaction, the retained T-0044/S13 macro-view
blocker, and three frozen programs passing RTL/oracle/fallback agreement on one
shared Verilator RTL image. T-0134 satisfies the review-process condition;
T-0135 retains the Garden explanation condition as unstarted Backlog. This
ceremony disposition changes no task, EXP, gate, evidence class, performance,
FPGA, ASIC, silicon, publication, or product-readiness conclusion.
T-0107 now makes estimate evidence and authority freshness explicit. The PM
role must inspect reusable implementation plus warm/cold build state, separate
edit/verification/integration effort, and re-estimate after scope or authority
change. A completion branch that does not descend from the latest named
authority commit is an integration-pending candidate, not a completed task.
`docs/templates/ESTIMATE-TEMPLATE.md` supplies the required estimate record.
T-0110 and ADR-0051 now make continuous execution the repository default after
an owner authorizes a bounded task. Progress reports, local edits and commits,
tests, bounded corrections, and the next accepted slice do not create approval
checkpoints. Nine exhaustive Human-confirmation incident classes retain human
authority over scope or gate expansion, first claim-bearing experiment
collection, destructive or remote action, unresolved evidence ambiguity,
user-work overlap, external cost/credentials/legal risk, repeated recovery or
resource overrun, material design forks, and the weekly Codex usage cost guard.
ADR-0060 and T-0119 require a current 10,080-minute weekly reading, compute
remaining as 100 minus used percentage, and stop new costly work below five
percent. Exactly five percent may continue cautiously. Missing or unverifiable
weekly telemetry fails closed for new costly work, and reset-credit use,
capacity purchases, service-plan changes, or bypass require separate owner
authority. The PM role and an executable
agent-boundary regression carry the same rule. No implementation P0,
experiment, evidence, performance claim, or remote-publication authority
changes.
ADR-0056 and T-0116 add a repository-linked, private GitHub Project weekly
sprint workflow with a stable-T-ID Kanban board, retained initial and revised
Fibonacci estimates, seven-day Iterations, WIP limit two, executable review
demo, and retrospective. ADR-0059 and T-0118 supersede only the assumption that
eight SP is the full weekly capacity. Eight SP remains an under-utilization
lower-bound check, 13 SP is the provisional committed capacity, and 13--21 SP
is the warm stretch range. These are planning bands, not stop conditions; the
ADR-0060 weekly usage guard is an independent service-cost stop.
Execution uses one serial high-reasoning PM integration lane. ADR-0061 now
permits up to two independently acceptable low-reasoning mutation lanes only
with disjoint tasks, files, artifacts, tests, and evidence; one low-reasoning
Tester follows each accepted packet, with at most two
read-only risk reviewers, a medium Librarian, and a milestone-only
high-reasoning Researcher. The Project has an
explicit `Sprint Board` Kanban plus a filtered `Product Backlog` table and six
seeded weekly Iterations. Its corrected Product Backlog initially contained 30
decomposed planning items plus the three original S-0001 items. Each executable
slice records an owner role, support roles,
parent T-ID, dependencies, initial/current SP, priority, evidence class, demo
or evidence command, forecast sprint/date, confidence, AI estimate, observed
cycle, agent tier, role packets, and resource use. T-0117's preserved Initial
SP is 5+3 while its first
AI-evidence correction sets Current SP to 3+2. Parent epics have no SP, and
specialist agents are not counted as independent FTE: final integration and
acceptance remain serial. ADR-0061 requires the default live Kanban to expose
ten pull fields while populated historical fields remain retained. Active mutation must have a
matching live Project item; unmatched worktrees are donor material or
provenance, not current WIP. ADR-0065 and T-0126 now require that item to be a
real `work-item` Issue rather than an active DraftIssue. Issue title, branch,
Parent T-ID, owner, demo, evidence class, and lifecycle are checked by
`scripts/project_queue.py`; transitions are read-only unless `--apply` is
given. `AGENTS.md` permits named Implementers to own ADR-0061-compliant
disjoint mutation packets while canonical records, final verification, PR
acceptance, and merge stay serial with the Project Manager. Historical Draft
cards remain preserved. T-0127 binds all ten repository agent configurations
to this role-specific contract and extends the task-governance skill across
kickoff, progress, and closeout. Four Implementers refuse mutation without an
`In Progress` real-Issue packet; Researcher is limited to its assigned memo;
Tester and the three read-only roles cannot transition the queue or claim
completion; and only the Project Manager may use `--apply`. An executable
agent-boundary test enumerates the exact role set and required constraints.
The queue audit permits missing start metadata on a `Ready` item so `start` can
write all metadata before status, but still rejects an incorrect pre-populated
Parent T-ID and requires complete metadata for active and `Done` items.
ADR-0066 and T-0130 additionally require every active real-Issue item to carry
a configured Sprint Iteration. `start --sprint TITLE` resolves the title before
any remote edit, writes Sprint with the other metadata, and moves status last;
the audit rejects a missing active Sprint. The non-pullable S-0001 review Draft
is Backlog rather than Ready. A separate clean current-main clone is the normal
operator entry while the dirty historical T-0042 root remains untouched.
The subsequent authority audit found that
its T-0042 child sequence contradicted completed T-0042 and ADR-0046. The
already-active stripped-token slice is therefore a bounded T-0106 evidence
carry-in only; later T-0106 work is unscheduled, and S-0003 is refined around
T-0044's accepted integrated-physical boundary instead. That refined slice was
subsequently moved into S-0001 as T-0044/S08 at the 21-SP warm ceiling. Its
already-performed independent clean replay absorbs the stale T-0044/S09
planning item: Initial SP 3 is retained and Current SP is zero so one evidence
packet is not counted twice. T-0044/S10 adds a five-SP contract-readiness
validator slice, bringing S-0001 to 26 Current SP. This is an observed
owner-authorized over-band Sprint, not a new capacity promise or stop
condition. Sprint state remains a coordination view and cannot promote task,
gate, decision, experiment, or evidence status.
The live Project after S-0001 conditional acceptance contains 58 items and 37
fields: 26 Backlog, no Ready item, one Blocked, 30 Done, one In Progress, and
no Review item. T-0132/S01 is the sole active delivery item. T-0135 remains
Backlog and has not started. The visible Story
Points assigned across all historical
Sprints sum to S-0001=119 and S-0002=5; these totals include completed and
retained planning items and are not the current delivery load. S-0003 is no
longer committed. The capacity calibration uses 13 SP as the
committed weekly load and 13--21 SP as a warm range while retaining eight SP as
an under-utilization alarm. The Project records role packets and resource use
separately; existing slices state when token usage was not instrumented. These
are planning facts, not measured productivity claims. No Project slice retains
T-0042 as its parent.

T-0132/S01 now supplies the first relative AXI4-Lite control wrapper around
the real current `StaticStencilRegion`. ADR-0067 maps the unchanged execution,
affine-installation, and program-installation word ABIs into relative byte
ranges `[0x0000,0x2000)`, `[0x2000,0x3000)`, and `[0x3000,0x4000)` while
leaving the absolute base unassigned. The wrapper admits one total transaction,
captures AW and W independently, holds R/B responses under backpressure,
distinguishes `SLVERR` from `DECERR`, and delays the core-only execution reset
until its retained OKAY B response is accepted. External ARESETn clears core,
wrapper, and captured bus state. S01 maps only identity/version/status/count
reads and execution reset; all execution data, digest, installation payload,
installation control, start, and cancel accesses fail closed.

The corrected implementation candidate is `363cad3`. Thirty-six host tests
pass, including strict append-once receipt and evidence-substitution rejection.
The offline Chisel/Verilator run reaches the real core through only the AXI top,
returns the exact marker
`GraphDevice-AXI4LITE-CONTROL-V1 status=OK evidence=rtl-simulation-functional
performance=not-measured`, and records identical RTL manifest SHA-256
`0b591c15f98982c65e0fee9673fe94c3c48e75254a075100e877138382d5ee36`
for both emissions. This is RTL-simulation-functional control evidence and
host-functional contract/finalizer evidence only. It is not full Graph
execution through AXI, a Linux or FPGA integration, AXI certification, or a
performance, resource, ARM64, ASIC, silicon, publication, or product-readiness
result.

T-0132/S02 is the sole active P0 after T-0093 and T-0137 closeout. Issue #75
and clean current-main branch `feat/t-0132-s02-axi-install` bind S-0003, eight
SP, the Systems Implementer, Tester/PM support, and RTL Simulation evidence to
one install-only vertical slice. It exposes only the unchanged affine and
bounded-program clear, ordered payload, commit, installed digest, status, and
count words through the existing relative AXI4-Lite aperture. S01 behavior
remains a regression requirement; execution I/O/start/cancel, Linux, board
addresses, KV260/FPGA, performance, resource, Experience, and ABI/schema
changes remain excluded.
The first S02 RTL checkpoint now queues one accepted affine/program mutation
until the held OKAY B response is accepted, applies one bounded installer pulse
behind an admission barrier, and reads the existing installed digests. The
first real S01 replay caught an execution output-count word accidentally routed
to the new digest path; the same branch restored its priority and the corrected
offline Chisel/Verilator replay passed. Both RTL emissions have manifest
SHA-256 `59d4b5c94a8959756c4877d2fa1dd0b3514d0e72dc516d8ce70c71d2812f11bd`.
The completed S02 candidate transcript then installed the compact affine
profile and one bounded DAG program through actual AXI4-Lite pins, read back
their existing installed digests, retained B under backpressure, rejected
partial/misaligned/read-only/out-of-range and malformed install sequences,
kept configuration and program namespaces separate, and restored factory state
through the existing core reset. A negative replay first exposed that a
misaligned config-control address returned DECERR but still queued the rounded
word mutation; the wrapper now shares its accepted-transaction predicate with
both response and side-effect authorization. Private corrected run
`artifacts/graph_device_axi4lite_install/run.9i9v74` exits zero with exact
marker `GraphDevice-AXI4LITE-INSTALL-V1 status=OK
evidence=rtl-simulation-functional performance=not-measured`, identical
double-emitted RTL manifest SHA-256
`02e010b141d7ce9d05eb0ee1df307c13d12a77823dfc6b1473cef0c0beffaf89`,
and an append-once, re-verifiable receipt binding sources, unchanged ABIs,
simulator, empty runtime/container stderr, toolchain, and the reviewed immutable
offline image ID. Twenty-one focused/regression host tests pass. Independent
security and measurement reviews found no blocking AXI-authorization or claim-
classification defect after invalid-control, payload-overflow, and split-AW/W
coverage was added. Both reviewers approved exact head `23538c9`; PR #76
merged as canonical commit `f2c283449ce9071755a9ff1d0ba35834368a7ca0`,
Issue #75 is Closed, and its Project item is Done. T-0132/S02 is complete.
This establishes no execution, Linux, FPGA, performance, resource, ASIC,
silicon, publication, or product-readiness claim.

T-0132/S03 is now the sole active P0 under real Issue #78 and clean branch
`feat/t-0132-s03-axi-execution`. The eight-SP S-0003 Product Slice is the
smallest data-plane continuation: stage exactly 324 factory five-point words,
start and poll one invocation, read 256 private output words only under output
authority, compare them with the independent oracle, then exercise cancel and
reset/restart through actual AXI4-Lite pins. It preserves S01/S02 and the three
unchanged ABIs. Descriptor/implementation digest promotion, arbitrary Graphs,
Linux, absolute board mapping, KV260/FPGA, DMA/IRQ, performance, resources,
Experience, and schema changes remain excluded. This is planned RTL Simulation
Functional evidence only; no S03 result exists yet.

After the accepted S-0001 owner-visible review and Keep/Problem/Try
retrospective, the owner removed ADR-0068's Monday-only wait. ADR-0070 permits
one ready next-Sprint item to be pulled immediately after closeout while
retaining every usage, WIP, dependency, Issue-packet, branch, evidence, and
queue guard. T-0136 merged through PR #66 as canonical commit `224394b`;
Issue #65 is Closed and its Project item is Done. T-0135 completed the S-0002
P0 Product Slice under Issue #60 and branch
`feat/t-0135-garden-fusion-explanation`. The accepted implementation explains
the validated materialized and fused paths, binds the unchanged program and
result-contract hashes, and labels `512B` versus `0B` as only the
intermediate-buffer scope. Forty-three focused/regression tests and the 150-
and 100-column host demos pass. After seeing the exact-head output and its
non-claims, the owner explicitly accepted the increment under ADR-0069. PR #67
merged as canonical commit `cde349c2d4896f0d19a59eef177f359966132f17`, and
Issue #60 is Closed. This remains host-functional evidence only; no measured
delivery-speed, Graph-performance, total-memory, compiler, RTL, FPGA, ASIC, or
silicon claim follows. No implementation P0 is selected after this closeout.

ADR-0070 next-pull evaluation found no live Ready item after T-0135, rejected
T-0121 as unready because its native-TUI dependency and interface policy remain
a material owner decision, and refined the already-planned T-0093 host
directory snapshot instead. Issue #69 and clean branch
`feat/t-0093-graph-directory-snapshot` bind current main `96b2c60`, S-0003,
five SP, the Experience Implementer, complete dependencies, exact allowlists,
an owner-runnable demo, host-functional evidence, and fail-closed non-claims.
The canonical start dry-run and `--apply` succeeded, and the following live
branch audit passed with T-0093 as the sole active delivery item. The slice may
add strict parsers only to existing Graph Program/Graph MVP v1 records and a
deterministic ordinary-directory projection. It adds no schema, contract
identity, Garden dependency, execution authority, filesystem security claim,
FUSE/VFS/write-back behavior, performance evidence, or hardware result.

The T-0093 implementation candidate now adds strict loaders for the existing
Graph Program, nested variant/observation, and Graph MVP result v1 records,
then validates canonical contract, variant-set, proposal, observation,
selection, and outcome lineage before any publication. The new
`graph-directory` CLI exclusively publishes one deterministic ordinary
directory with ordinal node/variant/memory-plan files, exact source and output
hashes, a manifest, an observe-only selection summary, and a bounded text tree.
It rejects malformed types, duplicate/unknown fields, stale or inconsistent
lineage/outcomes, nonregular inputs, symlinks, nonempty targets, and overwrite.
Sixty-one focused/regression tests pass; two fresh CLI materializations are
byte-identical with manifest SHA-256 `b6ab732f9305212cc39510eb0f7e01ab3c4172bb2f209da636937b994bc92ca0`.
PR #70 merged its exact reviewed head `64ca94b` as canonical commit `4db3a1e`;
Issue #69 is Closed and T-0093 is repository-accepted. This is host-functional
inspection-artifact evidence only. It grants no execution, mutation, approval,
Experience, filesystem-security, FUSE/VFS, performance, hardware, publication,
or product-readiness claim. Its task integration is distinct from the still
pending S-0003 weekly Sprint Review and does not complete that ceremony.

The bounded T-0106/S01 carry-in is repository-accepted. On the current-main
descendant, the owned CPU runner now includes the complete five-file Scala
source closure required by `RaveilDCacheOriginTagger.scala`; the added Static
Stencil sources satisfy compile-time type references and are not instantiated
by `RaveilOwnedSmallBoomTokenConfig`. A fresh versioned `build-v3` run and one
independent cached replay both complete after 10,916 simulation cycles. The
test-only boundary patch changes the positive producer's token from
`{valid=1, epoch=1, sequence=1}` to invalid/zero before TileLink A. The owned
manager classifies request and response unknown, completes the Put A/D
transaction, and the independent store verifier confirms readback. Both runs
bind input SHA-256 `63454ac39c7043f4cee9c1c98da033c193804935f12f9cb5b8f1dcb2af9f4aff`,
source SHA-256 `0c6c0bbc25f7f2300d1c9c6acfeae3d26ea9fdfabf6e657b949dc8028c5cca46`,
and graph SHA-256 `8fbee170f393e6ed777484c9fbb3f6e0d6adddbf1802525fa5a1bb680756a948`.
This closes only the five-point S01 carry-in as `rtl-simulation-functional`
negative evidence; T-0106 remains open and conditional, T-0042 remains
complete, and no performance or resource-match claim follows.

T-0124 removes a mutable local Docker tag from the complete BOOM functional
simulator consumer closure. The incident was not a changed executable payload:
Docker 29.6.2 with Buildx 0.35.0 emitted a provenance-bearing OCI index whose
digest changes between builds, while its linux/amd64 payload manifest
9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822,
Config-view hash
32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522,
and RootFS-layer-list hash
154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c
remained stable. The evidence defect was that an ordinary runner rebuilt and
retagged a shared name and project records could conflate the stable payload
manifest with the dynamic runtime index.

The only build entry point is now the explicit tagless
build-boom-functional-sim-image.sh. It publishes an append-only ignored
receipt under the exact runtime digest and atomically updates a local current
pointer only after the verifier binds descriptor digest/media type/size,
BuildKit runtime-index and linux/amd64-payload attachments, Config, RootFS,
platform, and the exact locally loaded image. Eleven existing runners consume
only the verifier result; none references or replaces
raveil-boom-functional-sim:v1. The primary and independent v2 builds used
different runtime OCI indexes,
7f8b6466109f0839d3f1d802e7db0b70181e05f6340779c379a38858ead18320
and
673e17bee26db760ef51b0ebb1655f349ac175f258f7832ca3fd9d1df34a2cc5,
with the same descriptor size 856 and stable payload, Config, and RootFS
identities above. The BOOM stripped-token wrapper again passed after
10,916 cycles, and the G1E runtime selector again passed both Graph and Rocket
modes on one RTL image. The old shared tag retained exact ID
ccf3e059120c688014eaf5bc4fa2dd15b7fed719061d969ee0146b0477e01791
and LastTagTime 2026-08-23T20:46:35.539767298Z before and after all accepted
runs.

This is local rtl-simulation-functional and evidence-integrity support only.
The receipt depends on the local BuildKit history record and is therefore not
a cross-host portable OCI archive. No prior performance result, EXP decision,
resource match, physical result, FPGA, ASIC, silicon, or general semantic
claim changes.

T-0122 now supplies the current-main simulation-first Graph device MVP. The
task-neutral `raveil.graph-device-abi/v1` is fixed-width, little-endian,
pointer-free, word-addressed, single-request, and finitely polled. The owned
artifact tool binds the canonical Static Graph descriptor/configuration,
source, ABI, implementation, inputs, independent Pavane oracles, simulator,
and environment. A transport-neutral C++ runtime and a Verilator-only adapter
stage 324 words, execute two normal seeds, expose 256 private output words only
after output-valid, cancel a third seed without output, and reset/restart.
Thirty focused tests pass. Primary and independent clean linux/amd64
Docker/Verilator runs both completed with 3,072 polls per successful seed and
byte-identical private output/oracle SHA-256 values
`dd749f0f218c7389730bef5b97af4e9203b0501d5ec57fa48ffa643356f23582`
and `58090120063557607cf04f684fb511adc3b3794e10ba1902003328113b38fe11`.
This is `rtl-simulation-functional` evidence only; no dynamic schedule,
performance, resource, AXI/UIO, FPGA, ASIC, or silicon claim follows. T-0123
S01 is accepted on the unchanged T-0122 ABI. S02 passes its scoped acceptance;
the S03 bounded-DAG implementation and primary evidence are recorded below.

T-0123/S01 now passes at implementation commit `f44d444` in the clean
`feat/t-0123-bounded-generality` worktree. It adds no register or transport
field to `raveil.graph-device-abi/v1`; four simulation-only ports observe each
accepted internal scratchpad request at `requestFire`. The task-neutral
schedule compiler derives ten immutable entries and a six-transaction template
from the validated descriptor, keeps host ABI windows distinct from internal
scratchpad words `[0,580)`, and rejects malformed lifecycle, numeric, count,
address, store-data, ABI, artifact, source, input, oracle, output, simulator,
environment, cancel-publication, and receipt identities. All 12 focused
unittest methods pass; parameterized negative checks remain reported within
those methods rather than being inflated into the runner's test count.

Primary exact-commit evidence at
`artifacts/graph_device_schedule/run.8IMrPt` and independent evidence at
`artifacts/graph_device_schedule/run.roJ3MC` reproduce two complete 1,536-
transaction traces, one nine-request strict cancellation prefix, Pavane-matched
store data, no cancelled private output, and the same schedule receipt SHA-256
`f91582420c49b88465b6215a61d1937b9448803f7b7fe76e3c8a5855c111e232`.
Stable identities include ABI
`fe01496e260f6504a9a04a0a54a5f65ad680fdded267293087f3edb929867277`,
artifact `8e2d655e1769ca291ed99d72698cdc52f0b64924cac685de6d6883bafd766e6c`,
generated schedule
`f6a8beeb814bf60ba3b42b4070d50d2e71f79b9396d7c7c63d6e05deb1932e30`,
transaction trace
`8e998d7ea4332b2c7485fd754c939a326cbbd935d397e560227e7d85852f3dbc`,
and Graph-device receipt
`2b05e1c63a644a1f36a82b2336e32895fdc4108f6ea701e42ec730b176ae8f7a`.

The initial low-reasoning mutation owner twice omitted the required prerequisite
receipt closure and negative matrix while reporting them complete. The PM
stopped under HCI-04/HCI-07, obtained owner approval for one narrow recovery,
and directly closed the fail-open in the two authorized Python paths. A PM run
before the final source edit produced schedule receipt `6491c373...a7f0`; its
runtime payload is valid but its schedule source identity is not exact-
`f44d444`, so it is excluded from closeout provenance. The independent agent
wrapper later returned status 6 despite creating a complete valid receipt;
the PM repeated the exact command at exact commit and observed shell exit zero
with the same receipt. S01 is `rtl-simulation-functional` only. The generated
schedule is not consumed or installed, S02 affine and S03 multi-DAG generality
remain open, and no performance, physical, FPGA, ASIC, or silicon claim follows.
The warm exact-commit PM end-to-end replay completed in about 37 seconds after
the image existed, and the focused test suite completed in 6.410 seconds. The
overall edit cycle was not time-sealed, and the repeated receipt-closure repair
invalidated the initial five-SP risk assumption; Initial SP remains 5 while
Current SP becomes 8 for the accepted slice. Remaining record, review, and PR
integration is re-estimated at 30--60 AI working minutes.

T-0123/S02 passes at implementation commit `b9b7d88` in the clean
`feat/t-0123-bounded-affine` worktree. ADR-0063 preserves the byte-identical
execution ABI and owns a separate fixed-width, little-endian, pointer-free,
word-addressed configuration-installation ABI with identity `0x52564901`.
The same elaborated executor admits baseline 16-by-16 strides 18/16 and compact
8-by-8 strides 10/8, retains fixed 324/256 windows, clears inactive output on
reset, and faults partial, misordered, duplicate, digest-mismatched, and busy
installation attempts without mutation. The implementation tag remains fixed;
only the separate installation ABI exposes the live installed digest.

The PM scoped suite passed 77 tests. Exact-commit primary evidence at
`artifacts/graph_device_affine/run.97Wn56` and independent Tester evidence at
`artifacts/graph_device_affine/run.gAZdlo` both reproduce receipt SHA-256
`58d788bfcddf85a5c85236b99e8fc79d3d05659464936f19ead4bccda936e955`.
Both bind artifact
`49e5b5c450f344af632c91dfb901a3658eed28a6208c94ff5a9702d9310bb012`,
transaction trace
`66df204d8345be202f948578d443057358a030ea25d549d4de41e430e7e094c5`,
simulator
`4667dd1352e9c2a48c3397e004a7c3a4f0e179cefc23c0d01e9957339381ff01`,
and environment
`d9963ad4fa4dc0aff9279ae5ed2a20813bd552e669c2b89c6c7299a36627af77`.
The two deterministic exports in each run are byte-identical with RTL identity
`146f291d6964835d4bcd9d59b6c9cc2218e94da84afc550301f0c3fe051d9945`.
Baseline and two compact inputs complete with 1,536/384/384 accepted
transactions, all active words and store traces match independent Pavane and
generic fallback results, compact tails contain 192 zeros, two strict cancel
prefixes publish no output, and reset/restart succeeds. The unchanged S01
runner also passes at the same commit; the execution ABI diff is empty.

The frozen allowlist expanded from 11 to 12 paths only to correct the stale
`tests/test_static_region.py` regression assertion after the core became
configuration-driven. Two sequential low-reasoning mutation owners returned
partial packets that did not meet the slice acceptance. Their work was not
accepted as completion evidence; after owner authorization the PM took sole
mutation ownership, completed the bounded packet, and assigned a separate
read-only low Tester. Initial SP remains 8 and Current SP becomes 13 to retain
the implementation recovery, evidence-integrity work, 12-path closure, and
independent double RTL replay. This is an AI-work estimate, not person-days.
The original 2.8--6.3 AI-hour range trended toward its upper bound; the total
edit interval was not time-sealed. Warm verification measured about 31 seconds
for 77 tests and roughly two minutes for each RTL runner. Weekly telemetry had
reset to 100 percent before the final fresh run.

S02 is `rtl-simulation-functional` evidence only and completes only this affine
slice. The generated schedule remains observation-only; T-0123 remains open
for S03. No general-DAG, performance, resource, physical, FPGA, ASIC, silicon,
or publication result is recorded.

T-0123/S03 starts from canonical PR #25 merge commit `27870f0` in clean
worktree `feat/t-0123-multi-dag`. ADR-0064 keeps the execution and affine-
installation ABI files byte-identical and adds a separate 32-word task-neutral
program-installation ABI. The frozen slice uses three external Graph JSON files:
baseline five-point, compact horizontal-three-point, and baseline vertical-
three-point. A generic compiler and one sequential interpreter are bounded to
five neighbor selectors, `LOAD_U32`/`ADD_U32`/`STORE_U32`, 16 instructions,
eight value registers, one active invocation, and one outstanding memory
request. The compact Graph changes both shape/stride and instruction sequence.

The live Project item binds a 16-path mutation allowlist, one mutation owner,
one low Tester, serial PM integration, Initial and Current 21 SP, exact stop
rules, acceptance, demo command, and non-claims. The first low Chisel owner
returned two incomplete packets; the second also made the placeholder runner
exit zero after compiling only one JSON file while core, TLClient, tests,
receipt, and matrix work were absent. The PM rejected that false-green result,
recorded the repeated-root-cause HCI, obtained owner approval, and took sole
mutation ownership without changing scope or accepting partial evidence.

The warm Dockerfile-derived linux/amd64 image and Scala cache are present. The
AI estimate remains 3--6 hours editing, 1.5--3 hours verification, 0.5--1 hour
Tester, and 0.5--1 hour PM records/PR integration, or 5.5--11 AI working hours
at medium confidence pending the first honest end-to-end run. Current local
Codex telemetry read 98 percent weekly remaining before promotion. These are
planning observations, not S03 evidence. No arbitrary Graph, performance,
resource, physical, FPGA, ASIC, silicon, novelty, legal, or T-0044 result is
recorded.

T-0123/S03 implementation commit `9682f783a7dfbc66426bfb6637cfa03cacd07b87`
now passes its primary bounded `rtl-simulation-functional` evidence run at
ignored `artifacts/graph_device_dag/run.mAgriX`. The same RTL export was
generated twice with matching raw hash
`64524cdc6b9f0365749f6f5925981d859a3b0b6e1c1b7c959ae8dbfddf58510f`; the
append-once receipt SHA-256 is
`093aa3ba723bca69f3e26f5e1b960d53bfdbb00a2cb708b1bf4a01cb5b221942` and binds
raw trace SHA-256
`4ed091a66a9d68063ddc76ad251feb6c4aa5b7a46cf1b5b8485ecd563f94bee2`.
It records three external Graphs, four complete invocations with transaction
counts 1536/256/1024/1536, one three-transaction strict cancellation prefix,
eight invalid program cases, one same-RTL image, direct-DAG oracle and generic
fallback parity, and no cancelled output publication. The busy-program-mutation
segment has one correct read prefix transaction; finalization now derives that
segment from the first invocation and accepts either an empty or strict correct
prefix, recording its observed count in the receipt. This corrects a previous
zero-count finalizer and unit-fixture assumption without changing ADR-0064,
either accepted ABI, or execution timing. `python3 -m unittest
tests.test_graph_device_dag tests.test_static_region` passed 19 tests (exit 0).
Independent exact-head review approved the candidate, and PR #26 merged it at
canonical commit `0cd2c890c26cba5dbb51fc5ea6cf454e8e4fe09c`. T-0123 is
complete for the frozen three-Graph `rtl-simulation-functional` boundary. No
arbitrary Graph, performance, resource, physical, FPGA, ASIC, or silicon claim
follows.

T-0125 is the sole implementation P0 after that merge. It adds only an
operator-readable wrapper and deterministic receipt presentation around the
unchanged T-0123/S03 one-command runner. Its intended visible result is a
three-row capability matrix binding external Graph, affine shape/stride,
instruction/program identity, one shared RTL identity, and oracle/fallback/RTL
agreement. The comparison to the earlier fixed five-point baseline is
functional capability only: three frozen programs may be installed without
Graph-specific RTL regeneration. Chisel RTL, all accepted ABIs, Graph JSON,
the S03 compiler/runner/receipt, and T-0044 remain read-only. Evidence remains
`rtl-simulation-functional` plus `development-non-claim`; performance is not
measured.

The low mutation owner twice failed the same T-0125 acceptance/reporting
boundary; the second packet still omitted the required negative matrix after
reporting it present. HCI-07 preserved that incomplete state and stopped the
owner. The repository owner then explicitly authorized option A, transferring
the frozen four-file mutation to Jitro. After T-0126 merged, Issue #27 was
upgraded to the complete ADR-0065 execution packet and moved through `Ready`,
`In Progress`, and `Review`; no parallel-session file or authority was
overwritten.

The resulting local T-0125 candidate validates rather than trusts the retained
raw evidence: it rejects symbolic links and path escape, copies the raw run to
a temporary closure, removes the receipt, reruns the canonical S03 finalizer,
and requires the regenerated receipt to be byte-identical. Twenty focused
Playable tests and the combined 39-test Playable/DAG/static-region suite pass.
PM replay `run.tJxhWF` and independent replay `run.LpVgAC` both render three
Graph rows with RTL/oracle/fallback PASS from receipt SHA-256
`093aa3ba723bca69f3e26f5e1b960d53bfdbb00a2cb708b1bf4a01cb5b221942`;
the shared RTL aggregate is
`64524cdc6b9f0365749f6f5925981d859a3b0b6e1c1b7c959ae8dbfddf58510f`.
Independent low-agent review of exact head `8e6182b` found no blocker, major,
or minor defect and was recorded on PR #31. The PR merged as canonical commit
`770a299b0b35e806e2ac8e42f497fc7f7a83d9c4`, closing real Issue #27. T-0125 is
complete only for this bounded operator presentation. Its evidence class
remains `rtl-simulation-functional` plus operator-presentation development
evidence; performance is not measured, and no arbitrary-Graph, resource,
physical, FPGA, ASIC, or silicon result follows.

T-0128/S01 is the first deliberately small operator-submission slice after
T-0125. Real Issue #36 and branch
`feat/t-0128-s01-operator-admission` bind a three-file Systems Implementer
allowlist and three SP. `python3 -m raveil graph-device submit` accepts only an
exact repository-relative path to one of the three frozen T-0123 descriptor
files plus a uint32 seed. It revalidates all three descriptor byte hashes,
schema/content, Graph identities, compiled program identities, and catalogue
uniqueness before emitting deterministic
`raveil.graph-device-submission/v1` JSON. Absolute, escaping, symlinked,
unknown, mutated, malformed, extra-field, duplicate-identity, and invalid-seed
requests fail closed with exit 2 and no traceback.

PM verification passed 35 submit/DAG/Playable tests and the vertical-three-
point CLI demo. Independent Tester verification passed the focused six tests,
29 DAG/Playable regressions, all three canonical admissions, and representative
rejections; its raw regression and CLI logs have SHA-256
`aa680128ec65170e960c8b635e0cf90e0f25513a7f54c661d8ddcb876845000d`
and `f0dc2017e00942943840c650ac3cd7d6b46909596d19647e2ac2c525463edc67`.
This is `host-functional` admission only with `execution=not-started`. It does
not invoke Docker or Verilator, write a receipt, publish Data, execute RTL,
allocate S02, broaden the three accepted Graphs, or establish performance,
resource, emulation, KV260, FPGA, ASIC, silicon, Experience-authority,
security, novelty, patent, or legal results.

PR #37 merged the exact reviewed S01 candidate as canonical commit
`748debee204d8cfe06da99c456aa0ba8d1d543e1`. S01 is complete only for that
host admission envelope. At that S01 closeout point, Parent T-0128 remained
open, no Product P0 was active, and S02 was unallocated.

T-0128/S02 completed under real Issue #39, branch
`feat/t-0128-s02-selected-rtl-execution`, Systems Implementer ownership, and an
exact eight-path implementation allowlist. It reuses S01 admission and
the frozen T-0123 compiler/oracles and leaves all three pointer-free ABIs and all
Chisel/Scala RTL byte-for-byte unchanged. A new selected runtime entry resolves
one generated Graph and affine profile, runs the existing eight-case installer
negative matrix, installs only the selected program, stages the selected uint32
seed input, and executes it on the existing Verilator transport. The private
finalizer regenerates and compares the three generated C++ headers, verifies an
exact three-line device log and complete transaction trace, requires RTL output,
direct Graph oracle, and generic fallback byte agreement, and binds source,
environment, toolchain, RTL, simulator, descriptor, program, input, and output
identities in an append-once receipt. The Scala dependency cache is mounted
read-only, rejected before build if it contains a symlink or special entry,
emitted as a strict sorted regular-file manifest, and hash-bound into that receipt.

The implementation passes 71 focused host tests on macOS 26.5.1 arm64 with Python
3.14.6. Primary Docker/Verilator `linux/amd64` runs `run.W9rhdR`
(vertical-three-point, seed 59) and `run.cIzTvg`
(compact-horizontal-three-point, seed 61) both complete, reject all eight
installer negatives with rejected output publication zero, and report the same
RTL-manifest SHA-256 `a3d5b60035e3a31bb5449718994c9560f5c1df15073c76ba12d2bb1bd38fb059`
and simulator SHA-256
`e19b21f2226641a870fcb24b3852812db8dd2e6c1d5baf9c3a14b79f9920a0fd`,
source SHA-256 `4064c263079c4827c36b8f443d5f6e86964c4b8d79143964a514b8ee0f538600`,
and dependency-cache SHA-256
`eb98a9093fbe5b21b21d149cbc95a9ef0f91654850759d6b228b5a844dd8f726`.
Their receipt SHA-256 values are
`c89ec08ca4ae7ba80be7bc2ef479eb2992c1b84da746bedb88d24179eb7d8a4c`
and `bf0b7f7db553cccebaa42afade7baa7a909cf23d63dd8b18c558c04c8eeb5c4b`.
Existing T-0123 fixed-matrix replay `run.tAfxeP` also passes on the same final
source with receipt SHA-256
`da989f65d7e1eb98946ff472cbde822c5b6670ab933e6e50477d0760129c5cdd`.
Independent exact-head Tester replay `run.Hh2saa` executes five-point/seed 67
with receipt SHA-256
`bd5f20a3db779f59cadef3dd2883270e187d1242f661170075a474db97746321`;
its source, RTL, simulator, and dependency-cache identities equal the primary
runs. Final Security review found no High or Medium issue; one non-blocking Low
same-user evidence-tree TOCTOU remains within the private, non-production-
security boundary. PR #40 merged the reviewed head as canonical commit
`1a3ad369`. This is `rtl-simulation-functional` evidence only. At that S02
closeout point S03 was unallocated and no Product P0 was active. T-0044 remains
blocked, and no
performance, resource, emulation, KV260/FPGA, ASIC, silicon, general-Graph,
production, legal, publication, or Experience-authority claim follows.

T-0128/S03 completed under real Issue #42, branch
`feat/t-0128-s03-top-level-rtl-cli`, Experience Implementer ownership, and an
exact six-path implementation allowlist. It adds a thin top-level
`graph-device run` presentation without changing any S02 shell/C++ runtime,
contract, Graph descriptor, compiler/oracle, ABI, or Chisel/Scala RTL. The
wrapper captures lower-runner diagnostics, requires exactly one strict private
marker, resolves only a real repository-confined evidence directory, and
read-only revalidates the raw S02 evidence and append-once receipt against the
current accepted source/compiler/oracle identities before rendering.

The implementation passes 50 focused submit/DAG/selected/Playable/run tests. Initial
real runs completed valid lower S02 receipts but exposed that Scala/Verilator
build diagnostics also occupy stdout; requiring the marker to be the only line
therefore failed closed at the S03 presentation boundary. The corrected wrapper
ignores captured diagnostics as non-authoritative while still rejecting zero,
multiple, or malformed markers. Exact top-level demo
`artifacts/graph_device_selected/run.SUXz5A` executes vertical-three-point/seed
7 and deterministically displays RTL, direct oracle, and generic fallback PASS;
partial, order, duplicate, opcode, undefined, reserved, missing-store, and busy
FAULT; and rejected publication zero. Its receipt SHA-256 is
`388fbe7b3985d38600365d4b88b4e8e93cea45289bf1267b12833a121ffb6217`.
Source SHA-256 is
`cd99617868145371ac8607cbf8f7c4ac375a7d048ba1bc2b3f1ae1350ba32bae`;
RTL, simulator, and dependency-cache hashes remain the canonical S02 values.
Independent exact-head Tester passed 62 tests and reproduced five-point/seed 83
through the same top-level CLI as `run.xM83E7`; receipt SHA-256 is
`ec70f0a2aeaaead1bd18cf804ffd8c00327e26fce952ad9516923ddade7ba194`,
and source, RTL, simulator, and dependency-cache identities equal the primary
run. Final Security review found no High or Medium issue; the inherited Low
same-user private-evidence TOCTOU remains inside the explicit non-production-
security boundary. PR #43 merged the reviewed head as canonical commit
`25d094bc`. This is `rtl-simulation-functional` evidence only. S03 and parent
T-0128 are complete, no Product P0 is active, T-0044 remains blocked, and no
arbitrary/general-Graph, performance, resource, emulation, KV260/FPGA, ASIC,
silicon, production, legal, publication, or Experience-authority claim follows.

T-0129 completes the smallest operator-visible verified-trace refinement on
canonical main. It keeps the exact `python3 -m raveil graph-device run --graph
<canonical-json> --seed N` command and the lower selected runner, receipt
schema, Graph catalogue, compiler/oracles, three ABIs, C++ runtime, and
Chisel/Scala RTL unchanged. Only the top-level presenter, focused tests, and
Chisel README changed. After the append-once receipt validates, the presenter
byte-binds one captured descriptor to the submission SHA-256, rechecks the
second trace read's fixed lifecycle, two segments, complete transaction order,
addresses, and write data, then renders canonical installed node/operand order,
full selected-run totals, and first/middle/last output-cell samples. It labels
read addresses as RTL-observed but their shown values as receipt-bound and not
RTL-observed; only write addresses/data are labelled RTL-observed, and ADD
internals are not claimed as observed.

Fifty-four focused submit/DAG/selected/Playable/run tests pass on macOS 26.5.1
arm64 with Python 3.14.6. Primary vertical-three-point/seed-7 run
`artifacts/graph_device_selected/run.tFw7sp` reports 1,024 transactions (768
reads and 256 writes), three-way RTL/direct-oracle/fallback PASS, eight named
installer FAULTs, and rejected publication zero; receipt SHA-256 is
`388fbe7b3985d38600365d4b88b4e8e93cea45289bf1267b12833a121ffb6217`.
Independent five-point/seed-83 run `run.DgHipE` reports 1,536 transactions
(1,280 reads and 256 writes) with the same acceptance outcomes; receipt SHA-256
is `ec70f0a2aeaaead1bd18cf804ffd8c00327e26fce952ad9516923ddade7ba194`.
Exact-head Security review found High 0, Medium 0, Low 0 after a bounded
descriptor-identity correction. PR #46 merged the three-file implementation as
canonical commit `4e4028142403dd7438afae9e4369cc328bb962df`; Issue #45 is
Closed, Project is Done, active delivery WIP is zero, and T-0044 remains
blocked. Evidence remains `rtl-simulation-functional` plus presentation
development only. No real-time telemetry, ARM64 execution, performance,
emulation, KV260/FPGA, ASIC, silicon, arbitrary/general Graph, publication, or
Experience-authority claim follows.

The agent call-sign catalog is also local-only under ignored `.codex/` state;
the root `AgentNames.md` is absent and explicitly ignored. Historical releases
that already contained it remain immutable provenance.

T-0117 is complete. S01 integrated through PR #6 at canonical commit
`bb1631109842f85b2a958ebcf30e5ee6a1b5312f`. The Garden
TUI loads one bounded `raveil.garden-snapshot/v1` fixture, reconstructs the
existing owned `GraphProgram`, requires its complete variant list to equal a
fresh canonical `GraphCompiler` slate, and renders nodes, dependencies,
variants, evidence labels, and runnable commands. Deterministic `j/k/g/G/q`
navigation plus explicit empty and fail-closed error states are covered by
host tests; duplicate JSON fields and non-printable terminal controls are
rejected before rendering. Garden is deliberately separate from T-0093's
static read-only directory snapshot and imports no execution backend. Its
evidence is
`host-functional` and `development-non-claim`; it has no execution, mutation,
approval, evidence-promotion, performance, or gate authority. S02 independently
reproduced the merged revision in a clean worktree: the normal TTY view,
deterministic `jjq` navigation, and empty state exited 0; malformed input was
rejected with the expected exit 2; and all 35 scoped tests passed. This closes
the bounded Garden Playable only and changes no research or hardware gate.

T-0120 extends that completed observe-only boundary with a deterministic
IDE-like terminal workspace. An explicit width from 72 through 240 controls
either three side-by-side `Graph Navigator`, `Node Inspector`, and
`Variants / Evidence` panes or a narrow stacked layout; `Commands / Status`
remains full-width. The default width is 150 and no terminal capability is
consulted, so the same accepted snapshot, navigation keys, and width produce
byte-identical text. The implementation remains dependency-free and retains
Garden's existing snapshot validation and read-only authority. This is
host-functional development evidence only, not graph execution, performance,
RTL, FPGA, ASIC, or silicon evidence. Independent clean verification of
`7054e01f384a659774635d333c0e114adf6bd800` passed 40 Garden and owned-graph
tests, the 142-file record checker, wide and stacked CLI demos, and diff/clean
tree checks. The acceptance log SHA-256 is
`c82485df3a2e254bfa54f623fa94f2f88f6b90f7a3a958e3488f7bf05edb2f6f`.

ADR-0026 adds lightweight defect governance. Existing experiment failures,
negative results, regression tests, and logs remain authoritative evidence;
`docs/FAILURE_KNOWLEDGE.md` indexes reusable prevention lessons, and the GitHub
bug template captures actionable defects without making Issues project
authority. Same-branch corrected defects do not require issue-tracker churn.

Gate 0 is complete, so tracked work now uses a dedicated
`<type>/<record-id>-<short-slug>` lowercase branch.
ADR-0057 additionally makes pull requests the only integration path to
`main`. GitHub ruleset 20582491 is active for `refs/heads/main`, has no bypass
actor, requires a pull request with zero mandatory approvals for the current
single-owner workflow, requires review-thread resolution, and blocks deletion
and non-fast-forward updates. Dedicated task-branch push and PR creation are
normal integration steps for already authorized bounded work; PR merge remains
subject to the incident-free audit in ADR-0058. A verified PR now merges
immediately when that audit finds no HCI; an HCI still pauses the affected
merge. No direct `main` push is permitted.

## Delivery-line state

The manufacturing line resumed for the sole P0 T-0086 after T-0087
reconciliation. ADR-0024 makes a
GNU/Linux userspace graph vertical slice the next delivery line without
discarding any current artifact. Sonatine Microkernel (Sonatine), the Linux harness,
shared job/object/completion contracts, job rings, completion telemetry,
Experience infrastructure, EXP-0003 evidence, and metadata-shadow finalization
remain implemented and preserved.

T-0086 is implemented by selective port onto the T-0087 milestone state. The
donor branch was not merged, so none of its deletions or stale records entered
the result.

## GNU/Linux userspace graph MVP

T-0098 adds `python3 -m raveil shell` as the primary human-facing Native
userspace path. One explicit session owns the current graph, canonical variant
slate, proposal, execution result, and local command history while delegating
all authority to the existing GraphCompiler, AnalyticalPredictor,
Miroirs/Pavane-backed GraphExecutor, and NativeCBackend. Invalid order,
malformed arguments, duplicate execution, and overwrite fail without a
traceback. Results retain `raveil.graph-mvp-result/v1` and remain host-
correctness development evidence only.

T-0099 adds `--workspace PATH` and fixes one existing real directory as the
session's virtual `/`. Bounded `pwd`, `cd`, `ls`, `cat`, `stat`, `mkdir`, and
exclusive `write` commands share one `NativeWorkspace`; graph result files use
the same virtual path boundary. Parent traversal, symlink components, broken
links, special files, excessive paths/files/listings, root replacement, and
overwrite fail closed without exposing host absolute paths. The existing
GraphCompiler, adviser, Miroirs/Pavane-backed GraphExecutor, NativeCBackend,
baseline-first rule, commit/rollback, and result v1 remain unchanged.

This is application-level workspace containment and host-correctness evidence,
not hostile-code isolation. T-0100 remains open for descriptor-relative and
platform-enforced worker isolation. Sonatine and its shell are unchanged.

T-0101 adds a separate strict `CommandGraphProgram` rather than reusing tensor
graphs for shell work. The Native CLI now supports direct `run`, deterministic
`graph compile`, command `graph show`, baseline-first `graph execute --compare`,
balanced development `graph benchmark`, and exclusive `graph result`. The
bounded grammar covers quoted argv, pipelines, redirection, success/sequence
edges, and owned `|||` join-fanout over hash-bound allowlisted host tools.
Direct and DAG executors use equal workspace snapshots, controlled environments,
resource limits, and concurrency; exact stdout/status/output agreement gates
publication. Failure, timeout, stale identity, undeclared mutation, and output
collision remain uncommitted. Existing GEMM behavior and schemas are unchanged.

The manual `cat | grep | wc` demo returned `2` through real host tools and exact
direct/graph agreement. Its four-repetition timing is development/non-claim;
EXP-0004 remains Planned; the smoke sets `crossover_evaluated=false` and makes
no performance claim.
The current direct interpreter buffers pipeline stages, so benchmark records
mark ordinary-pipeline and scheduling claims ineligible; EXP-0004 retains the
concurrent OS-pipeline baseline as required future measurement work.

T-0102 adds host readline/libedit Tab completion without changing dispatch or
authority. Completion candidates are limited to documented commands, graph
subcommands/options, the fixed Command Graph tool allowlist, and bounded
virtual-workspace paths. Symlinks and host paths are omitted; completed input
still passes through the existing parser, workspace checks, and guarded graph
flow. Completion is ephemeral host usability, not expansion, arbitrary PATH
lookup, persistence, or an OS isolation boundary.

T-0103 adds `python3 -m raveil showcase list|prepare|run|mutate`: a synthetic
16/32/64-way independent ordinary `sort` fan-out, plus a four-small-file
control. It prints nodes/edges/critical path, hash-bound direct-argv admission,
exact semantic output manifest hash, sequential and equal-concurrency direct
baselines, DAG construction/execution/end-to-end intervals, observed
parallelism, and baseline-first evaluation cost separately. Its first run
executes all nodes; a deterministic one-input replacement then reuses only
showcase cache artifacts whose complete node recipe/tool identity, active input
SHA-256, and payload SHA-256 all match, while separately direct/Graph-validating
the changed node. The cache is intentionally outside `CommandGraphExecutor`:
the output states `production_reuse=not-implemented`, and T-0104 owns any
production design. Experience is explicitly not connected to this command
surface and remains advice-only. This is host-development-smoke only; EXP-0004
remains Planned and no timing line is a performance, scheduling, hardware, or
special-ISA claim.

The showcase now prints an explicit abstraction warning: whole host
tools/processes are conceptual nodes, far above the intended native
operation/dependency/effect/object graph. It does not test dependency discovery,
OoO replacement, cache hierarchy, pipeline, ISA encoding, area, or energy, and
its memoization is not evidence that Graph is required. RFC-0004 is only a
proposal for the correctly ordered Chisel RTL/simulation study. T-0105 now has
unmodified Rocket functional execution. T-0042 separately has bounded static
Graph and CPU RTL simulation evidence. The ADR-0046 small-start exit slice is
now complete: controlled Rocket, BOOM, and static Graph preserve the frozen
RFC-0005 semantics and independent oracle, use the same canonical owned
resource tuple, enter and leave execution quiescent, conserve all admitted
execution traffic, and emit complete installation/staging/execution/
completion/validation/publication plus total-cycle records. The three-way
verifier reports `resource_equality_verified=true` and bounded functional
`comparison_eligible=true`. It also reports
`dynamic_memory_traffic_equal=false` and
`t0044_measurement_claim_ready=false`: Graph admits 1,280 reads plus 256 writes
while each optimized CPU execution admits 800 reads plus 256 writes. T-0044
must explain that fairness boundary before a measurement claim. EXP-0005 now
does so for the bounded execution window described below. Exhaustive CPU token
lifecycle hardening remains deferred to T-0106. Existing ADR-0045 diagnostics
remain bounded functional evidence; no general semantic-initiator,
performance, CPU/ISA advantage, FPGA, ASIC, or silicon claim is promoted.
T-0044 has completed only its preregistered EXP-0005 latency/traffic pilot.
Before data collection, the machine-readable manifest froze fresh seeds
1--4, the primary static Graph/Rocket/BOOM matrix, BOOM serialize-dispatch as a
diagnostic only, the same-meaning execution-window edges, paired estimators and
conditional 95% interval rule, raw/derived separation, and fail-closed stop
conditions. The pilot deliberately omits VLIW/CGRA, elastic/stream/hybrid,
energy, synthesis timing, and area; T-0044 remains open and no go or RFC-0005
numerical no-go may follow from four inputs.
The post-freeze EXP-0005 instrumentation accepts fresh seeds without result
reuse, includes the Graph launch edge in execution, emits owned-boundary stall/
backpressure and useful-work/byte counters, and adds the BOOM
serialize-dispatch diagnostic runner. A clean-worktree collector writes 16 raw
logs, exact command exit/wall-clock metadata, derived observations, and a
SHA-256 raw seal under one exclusive ignored RUN-ID. The sealed 4x4 RTL matrix
completed at collection commit `6733c44`: all commands exited zero, four
distinct input and oracle/output hashes agree across candidates, the resource
and execution-window meanings match, and all required accounting conserves.
The exact execution cycles are 3,073 Graph, 14,621 Rocket, and 21,892 BOOM for
each of four fresh inputs. The BOOM serialize-dispatch diagnostic is 70,898
cycles and remains diagnostic only. Graph admits 1,536 transactions versus
1,056 for either optimized CPU because CPU code legally reuses loads; that
difference is explained and the bounded primary execution-latency/traffic
pilot is claim-eligible without weakening either CPU. End-to-end reuse
amortization is not eligible because current fresh-process runs repeat CPU
installation while Graph is elaboration-installed. EXP-0005 therefore ends
`pause` at exactly one required boundary: run repeated fresh inputs under one
installed configuration without simulator reboot. T-0044 remains open; the
pilot is partial and decides neither RFC-0005 go nor numerical no-go.
The successor boundary implementation is now present on the dedicated
`research/t-0044-repeated-invocation-boundary` line and has produced the
completed EXP-0006 commissioning evidence described below. It adds separate
repeated-only Rocket/BOOM configurations,
one ELF process that consumes ordered runtime seed versions, per-invocation
owned-memory lifecycle counters, actual 256-word output evidence, and a strict
repeated-session verifier/collector with exclusive raw/derived/seal paths,
without changing EXP-0005. The repeated manager
re-enters staging structurally after each drained validation response; it adds
no candidate-visible port, buffer, bank, arbitration path, or software phase
command. Static checks passed, and EXP-0006 plus its machine-readable manifest
froze the installation/staging boundary before RTL commissioning. No EXP-0006
data existed at freeze. In particular,
CPU staging currently includes candidate-local input-generation instructions
while Graph input generation is testbench-side, so end-to-end eligibility is
not inferred from the implementation alone.
The first frozen EXP-0006 commissioning attempt retained two failed RUN-IDs.
The first exposed only the already known ignored Chipyard locator requirement.
The second completed Graph, cold-built Rocket, then entered a CPU trap/reboot
loop before any owned-memory measurement marker because the new repeated C
function used a stack while its bare-metal entry left `sp` uninitialized. No
CPU observation or performance claim was produced. The minimal correction
initializes a private main-RAM stack outside the owned RFC-0005 resource; the
manifest must be re-frozen before another run.
The stack fix is now hash-bound by the replacement EXP-0006 manifest; no
replacement commissioning data existed at that re-freeze.
The replacement Rocket run then completed all four inputs and actual-output
oracle checks, but the strict parser rejected invocation one's 2,216 accepted
operations: 580 additional writes are ELF-loader initialization of the owned
valid words during installation, followed by 1,636 staging/execution/
validation operations. Because the marker did not split installation reads
and writes, this remains failed evidence rather than an inferred accounting
result. Instrumentation now emits the split explicitly and requires another
pre-data re-freeze.
The installation-accounting fix is now included in replacement manifest
authority; no subsequent commissioning data existed at this re-freeze.
The next complete-matrix attempt passed Graph and Rocket. BOOM RTL also emitted
exactly 1,024 output words, four complete lifecycle records, and passes the
strict parser when the retained outer raw log is replayed, but the immediate
in-container verifier observed an incomplete `tee` file and failed cardinality.
This is a harness visibility failure, not promoted BOOM evidence. The runner
now synchronizes the named-volume log before reopening it and reports observed
versus expected cardinality; another re-freeze is required.
The synchronization fix is now included in replacement manifest authority; no
subsequent complete-matrix run existed at this re-freeze.
The following attempt again produced all 1,024 diagnostic output markers in
the completed outer raw log while the in-container immediate reader saw only
215. The evidence boundary is therefore moved to the collector after the
Docker command closes: the container emits source/artifact/config/toolchain
identity with accounting pending, and the host collector strictly validates
the completed immutable outer raw before derivation or sealing. This removes a
redundant racing reader without weakening any oracle/accounting check and
requires another re-freeze.
The completed-outer-log collector boundary is now replacement manifest
authority; no subsequent complete-matrix run existed at this re-freeze.
The next attempt showed the completed outer file itself growing from 215 to
1,024 diagnostic output markers about 0.6 seconds after Docker CLI return.
Thus Docker Desktop stdout forwarding, not the simulator or parser, is the
remaining boundary. The collector now waits up to 30 operations-only seconds
for frozen output/complete/host marker cardinalities before hashing, deriving,
or sealing; timeout fails closed. Another re-freeze is required.
The bounded Docker-output-drain wait is now replacement manifest authority; no
subsequent complete-matrix run existed at this re-freeze.
The next attempt failed closed on Graph at the same 215/1,024 outer-marker
count even after the bounded wait. Inspection found that the Graph wrapper
itself deliberately printed only the first 240 lines of its complete internal
RTL log, a legacy interactive-smoke preview cap; this was deterministic
truncation rather than Docker forwarding loss. Repeated mode now emits the
complete verified internal log to the outer collector while non-repeated smoke
output retains the preview cap. This evidence-transport correction requires a
new manifest re-freeze and RUN-ID; the failed run is not promoted.
The Graph raw-transport correction is now replacement manifest authority; no
subsequent complete-matrix run existed at this re-freeze.
EXP-0006 RUN-ID `20260814T100000Z-7b6e5df-commission8` then completed and
sealed the full four-member, four-input matrix. Every command exited zero;
all outputs match the independent oracle; contract/resource/output identities
agree across the primary candidates; and traffic, phase, quiescence, one-
process/one-reset/one-installation, and no-reload accounting pass. Static Graph
execution is 3,073 cycles per input with 1,536 transactions; Rocket is
14,592/14,548/14,548/14,548 with 1,056 each; BOOM OoO is
21,904/21,900/21,902/21,903 with 1,056 each. BOOM serialize-dispatch is
70,871/70,862/70,862/70,862 and remains diagnostic only. Execution preserves
lawful CPU load reuse and exposes Graph's extra traffic, so the bounded
execution latency/traffic view is pilot-eligible. CPU-local versus Graph-
testbench input generation still prevents a same-meaning staging/end-to-end
claim. EXP-0006 therefore ends `pause` at that single boundary; no 256-input
campaign, go/no-go, energy, synthesis timing, or area conclusion follows, and
T-0044 remains open.
ADR-0047's narrow successor boundary is now implemented but not yet frozen or
measured. One shared `RaveilFixtureInputProvider` supplies Graph and CPU adapters
through a phase-exclusive mux at their existing single owned ingress, records
all 324 accepted input words, releases only on the final response, and rearms
only on the 256th validation response. CPU input generation/stores are absent
from the fixture ELF; its first load is held without acceptance or payload
drift while staging completes. Resource identity
`87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7`
binds the provider, mux, release, and rearm rules. Seventy-four focused tests
and pre-freeze Graph, Rocket, BOOM, and diagnostic BOOM RTL runs pass. The
four-input Graph run records exact
`648/3072/1/512` staging/execution/completion/validation cycles and 1,536
execution transactions per input; one-input Rocket and BOOM runs each record
the same 648-cycle provider window, 800 execution reads, 256 execution writes,
no unexplained traffic, and matching output. This is pre-freeze functional evidence, not
EXP-0007 commissioning data or a performance claim. Manifest
`t0044-fixture-owned-staging-v1.json` is frozen at SHA-256
`c9b0f9d307421cfd611978c4e221d84faeb939f0630c4b9818180630c5f26c57`
against implementation authority `8e96d24188df9ab83eb7ed0f700b4db914174c33`.
Frozen EXP-0007 RUN-IDs
`20260814T115314Z-8e96d24-commission1` and
`20260814T115314Z-8e96d24-commission4` now complete with all eight commands at
exit zero. Four distinct inputs match the independent oracle for every
candidate; resource, lifecycle, traffic, identity, execution-window, one-
process/reset/install, and no-reload checks pass. Median execution cycles are
3,072 Graph, 14,539 Rocket, and 21,893 BOOM, with 1,536 versus 1,056
transactions per input. The 480-transaction difference remains explained by
lawful CPU load reuse. Common fixture staging is exactly 324 writes and a
648-cycle provider window for all candidates. EXP-0007 therefore resolves the
single EXP-0006 fairness pause and returns `advance` for a separately frozen
1/4/16/64/256 campaign. The evidence remains partial RTL-simulation pilot:
T-0044 is open and neither RFC-0005 go nor numerical no-go is decided.
EXP-0008 is allocated for the authorized full latency/traffic campaign. Its
new collector keeps EXP-0007 immutable, runs one 256-input session per matrix
member, derives nested 1/4/16/64/256 prefixes, and adds paired execution plus
six-phase correct-latency intervals with installation fixed once. It also
records failed raw evidence, bounds disk/log/drain operations, and distinguishes
missing activity from zero. Seven campaign tests pass. Implementation authority
`fb8e95aca23da021918ed22d8798134d5ca99c5e` and manifest SHA-256
`2e2b71097bb88acf60904d17ce87ec6ec4399eaf1795a45c14542ee39f7d6359`
are frozen before data. No EXP-0008 RTL measurement or claim exists yet.
The first frozen collection completed all three 256-input primary sessions,
then the diagnostic serialize-dispatch command hit the CPU runner's hardcoded
3,600-second operational timeout during invocation 115 and exited 124. The
collector failed closed, emitted no derived report, and sealed the raw attempt.
This is not a semantic/resource/performance no-go. Recovery preserves that
RUN-ID, imports every completed primary log by frozen hash without rerunning it,
and will retry only the diagnostic under a separately frozen 10,800-second
operational envelope. RTL, ELF, estimator, thresholds, and primary samples are
unchanged.
Recovery authority `1c6160bda7325f039ef88ca1efcc50eb3a572916` and
manifest SHA-256
`c9226d05f348c740801b7cbceb673514495c3f5fc15c1192629f31b2f58a1eb6`
are frozen before retry data. The new RUN-ID is
`20260814T153738Z-0203248-campaign256-recovery`.
That recovery completed and sealed EXP-0008. All 256 fresh inputs pass the
oracle and all matrix/resource/fixture/window/session/accounting/prefix gates.
At 256 inputs, execution medians are Graph 3,072, Rocket 14,539, and BOOM
21,893 cycles; Graph traffic is 1,536 versus each CPU's 1,056 transactions.
At the claim-bearing 64-input prefix, cumulative six-phase Graph/Rocket ratio
is 0.2085927 with 95% interval [0.2085784, 0.2086002], below the 1.05 latency
no-go threshold, and break-even occurs at invocation 1. The decision is
`advance-partial-latency-traffic`: execution latency/traffic and end-to-end
reuse amortization are eligible RTL-simulation evidence, but energy, synthesis
timing, area, IP disposition, and the missing Graph organizations remain open.
Report SHA-256 is
`1e52c4e213cb19cb2455cfef67077d3d3acb959bfb834c24e6b12e932d2f7a65`;
raw-seal SHA-256 is
`7c90f8a4a09291f5269e19d1425d1eac1a7915b8b3abcc4f16eb7206f438eeef`.
ADR-0048 and EXP-0009 now start the next T-0044 physical-proxy gate without
promoting the standalone Graph island to a whole-system result. A pinned
linux/amd64 Yosys 0.27+3/OpenSTA 2.3.3/Sky130 HD typical-corner toy flow
successfully synthesizes, maps, and times repository-owned non-candidate RTL.
Two cached reruns retain image ID `7a0db885...7169`, exact tool/library/
environment hashes, and toy netlist `81aa8113...5a09`. This is synthesis-
toolchain commissioning only. No Graph, Rocket, BOOM, energy, static-power,
placement, routing, FPGA, or silicon datum exists in EXP-0009 yet.
The Stage-B pre-data implementation now owns separate Graph/Rocket RTL export,
manifest-driven synthesis/STA, runtime tool/Liberty and RTL identity checks,
append-once failed-run evidence, sealed raw evidence, separated derived
partition reports, and an analytical fallback-plus-Graph matrix report. Its
top, black-box list, partition role, generated RTL, and constraints must all
match the later frozen manifest. This implementation has not run candidate
synthesis and is not yet the frozen Stage-B authority.
Initial Rocket RTL-only export commissioning failed before RTL copy or
synthesis because external-source locators were implicit and a new exporter
assignment was malformed. The latter is corrected and regression checked;
these are pre-data operational failures, not physical results.
A subsequent broad Rocket copy included generated simulator collateral; it was
rejected before freeze or synthesis. The corrected path admits only Chipyard's
`.top.f` RTL entries and binds their tree and file-list hashes.
Stage-B implementation authority is now
`f487259fbadc5dc35548c15d7c8967b7065cd466`. Its manifest freezes Graph top
`StaticStencilRegion` with the common provider/scratchpad black-boxed and
Rocket core top `Rocket`, exact RTL/tool/library/constraint identities, raw
sealing, and fail-closed matrix rules. Manifest SHA-256 is
`681fd43e6f38a4b65cba8698eacbbf3768edc93d633141274c74ce846d61d216`.
Freeze commit is `d44c2e603ade69ceccb14ac0db2a77374d47ab7b`.
This is still candidate pre-data: no Graph or Rocket physical estimate exists.
The first frozen Graph RUN-ID stopped before Yosys because the host-created
container log violated the container's empty-directory check. Failed raw files
are sealed at `080f3ac9...b6f3` and are claim-ineligible. Recovery changes only
the log handoff and requires a separately frozen descendant manifest; the
scientific contract and generated RTL remain unchanged.
Recovery authority `b6c3125...0e94` and manifest SHA-256
`14f5786f...5786` now bind that one operational change; candidate reattempt is
authorized only from recovery freeze commit `64ffcc4...adb39` or a clean
descendant.
The recovery Graph RUN-ID reached Yosys but failed parsing CIRCT block-local
`automatic logic`; sealed raw digest is `dcda0e56...094ec` and contains no area
or timing datum. A physical-export-only CIRCT lowering mode is now the single
bounded recovery candidate. It requires new RTL hashes and manifest before use.
Recovery-v2 authority `cba6226...7e6bf` emits physical-only Graph RTL at
`e95e2e02...5a41d` with incompatible local/packed forms removed. Manifest
SHA-256 `293d83bf...1c04` binds it while preserving Rocket and all scientific
fields. Recovery-v2 freeze commit is
`ba8ee88863750be9137bd519af0102ed0560cbb5`.
Its Graph RUN-ID parsed RTL but exposed a black-box ordering error before
synthesis; failed raw digest is `b4ed5c06...56c3d`. One final recovery moves
black-box assertions before hierarchy pruning without changing the contract.
Final bounded recovery authority is `daa984f...b226d`; recovery-v3 manifest
SHA-256 is `efe1ec48...806ed` and changes ordering only.
The final Graph RUN-ID still selected zero black-box modules after successfully
parsing all three RTL modules, exited 1 before synthesis, and sealed raw digest
`f203b7c8...7aed9`. EXP-0009 is therefore `pause-boundary`: matrix incomplete,
Rocket not started, candidate area/timing absent, and claim eligibility false.
Resume requires exactly one proven Yosys-visible common-partition boundary;
derived pause report SHA-256 is `340d0d0e...ce700`.
Recovery-v3 freeze commit is `c238c9631f7e248960a2fa421e513764c60dcadd`.
The paused boundary has now been reproduced with a candidate-independent
pinned-tool probe: Yosys `N:<module>` selects each common module definition,
`t:<module>` verifies exactly one instance, and `blackbox N:<module>` sets a
verified black-box attribute before checked hierarchy. The failed `m:` form was
a memory-object selector, not a module selector.
The collector now binds selection mode
`yosys-module-name-single-instance-v1` into raw identity. This is pre-data
boundary repair only; there is still no candidate area/timing datum.
Recovery-v4 authority is `fe7b9f6...3c046`; manifest SHA-256 is
`de396d4f...129d31` and retains all prior RTL/tool/partition/decision fields.
Only a clean descendant of the manifest freeze may collect the next Graph
RUN-ID.
Recovery-v4 freeze commit is
`caa09835116cce0baadd2a12596b10e2b25fd4c3`.
Recovery-v4 Graph `run-005` passed partition selection and mapping but failed
closed on 212 apparently undriven wires at the post-map check; sealed files
digest is `74898373...16ee3` and no netlist/stat/STA datum was published. A toy
reproduction proves the same failure is caused by omitting mapped-cell Liberty
definitions from the integrity check: 32 warnings without `read_liberty -lib`,
zero after it. Pinned OpenSTA diagnostics also reject
`remove_from_collection` and `report_clocks`; supported Tcl iteration and
`report_clock_properties` retain the intended clock and I/O-delay contract.
The collector-only correction is pre-data and requires recovery-v5 freeze.
Recovery-v5 authority is `104c603...bc7ef2`; manifest SHA-256 is
`6973030c...6d051e` and all candidate RTL/tool/partition/decision identities
remain unchanged. Only a clean descendant of its freeze may collect Graph.
Recovery-v5 freeze commit is
`f1d62e95618d4a2107a1dfe20635098425b8abf5`.
Recovery-v5 Graph `run-006` sealed complete raw Yosys/STA files but the parser
rejected OpenSTA's two implicit `module not found; creating black box` warnings;
raw files digest is `6df847ec...e435f1`, raw-seal SHA-256 is
`14847d3f...ad74c`, and no derived result is eligible. A pinned-tool diagnostic
proves explicit Yosys black-box stubs remove the warnings while preserving the
mapped core. The collector now asserts one declaration for each frozen common
partition; this pre-data recovery requires a v6 freeze before Graph retry.
Recovery-v6 authority is `d4990d9...4d8cf9`; manifest SHA-256 is
`135f30d6...bc398a`, with all candidate RTL/tool/partition/decision fields
unchanged. Only a clean descendant of its freeze may collect Graph.
Recovery-v6 freeze commit is
`474c1b5c10fecdef5de0fefc2c5ff7199c22587c`.
Recovery-v6 Graph `run-007` is the first complete partition estimate:
11,851.3664 um2, 1,592 cells, and +11.45991 ns setup slack at 20 ns; raw-seal
SHA-256 is `634329f4...9fa1` and result SHA-256 is `c778d6fb...60d1`.
It is not a whole-system, performance, or energy result. Rocket `run-008`
failed before synthesis because Yosys 0.27 rejected a generated packed-array
declaration; failed-seal SHA-256 is `639bf2cc...186d`, with no Rocket datum.
The matrix and decision remain `pause-boundary`. A separate-volume,
physical-export-only upstream `ENABLE_YOSYS_FLOW=1` path now binds
`disallowPackedArrays` and exact shared-elaboration hashes; it requires a
recovery-v7 freeze and fresh Graph/Rocket RUN-IDs.
The first isolated physical build completed, but the exporter stopped before
publication on absolute build-root strings in otherwise identical annotation
files. Diagnostics prove both normalized annotations, FIRRTL/SFC inputs,
module hierarchies, and normalized file-list sets match. A checker-only
normalization of the two exact cache roots and file-list ordering is required
under a new authority; no Rocket RTL or physical datum was published.
Authority `c2842a0...d1035a` then exported the verified 376-file Rocket tree
`641735c1...86d2f`; provenance SHA-256 is `fd91b3b9...620da`. The packed-array
inventory is empty and pinned Yosys read/hierarchy/check passes. This is
pre-data compatibility evidence. A parser-bound recovery-v7 manifest and fresh
paired candidate runs remain required.
Recovery-v7 implementation authority is `0611b04...1bee98`; frozen manifest
SHA-256 is `5b165299...ec1780`. It binds unchanged Graph RTL, verified physical
Rocket RTL, generator provenance, and one common compatibility-lowering
policy. Fresh Graph and Rocket runs may begin only after the manifest freeze
commit; no prior Graph result can enter the v7 matrix.
The first v7 Graph command (`run-009`) supplied the export parent instead of
`generated-src`; actual tree hash `961002ee...fbeca` differed from the frozen
Graph hash. The host failed before sealing/derivation, but only after Docker
completed, exposing a preflight-order defect. No value is eligible. The
collector now verifies manifest authority and exact variant tree before raw
directory creation, copies that verified tree to a private snapshot, verifies
the snapshot again, and mounts only the snapshot into Docker. Retrospective
sealing is hash-locked to the exact run-009 manifest, RTL trees, file set, and
pre-seal evidence digest. A new recovery freeze was therefore required.
Run-009 is now sealed as ineligible host-operational evidence: failure-metadata
SHA-256 `5d242ee...d7162`, failed-seal SHA-256 `d5b7023...9d2af`. Recovery-v8
authority `50639f0...aad938` and frozen manifest SHA-256
`3dfb0dd...dd0b1` preserve every RTL/tool/constraint/decision field from v7
and change only the preflight/snapshot collector boundary. Fresh paired runs
must use distinct RUN-IDs under v8.
Under v8, Graph `run-010` sealed and derived a complete partition synthesis
estimate: 11,851.3664 um2, 1,592 cells, and +11.45991 ns setup slack at 20 ns;
raw-seal SHA-256 `355aaea...01e77`, result SHA-256
`5280a4d...0b91`. Performance, energy, and whole-system claims are false.
Rocket `run-011` sealed complete raw evidence, raw-seal SHA-256
`103dc16...4580`, but derivation failed closed because the log contains eight
module-area rows while the parser incorrectly required one row globally. There
is exactly one frozen-top row; no Rocket result or matrix is eligible. The
checker now requires exactly one frozen-top log row, exactly one plain/escaped
stat top, and equality between them. A fresh recovery freeze and paired rerun
remain required.
Recovery-v9 implementation authority is `558c7c0...9c6df`; frozen manifest
SHA-256 is `d052987...1fd63`. It changes only exact-top report selection and
retains all v8 RTL, toolchain, physical, evidence, and decision fields. No v8
result is imported into the v9 matrix; both partitions require fresh RUN-IDs.
Recovery-v9 freeze commit is `c9972af...a1fd9`. Fresh Graph `run-012` and
Rocket `run-013` both sealed and derived as `partition-complete` under manifest
`d052987...1fd63`. Graph is 11,851.3664 um2 / 1,592 cells / +11.45991 ns
slack; Rocket is 51,625.7632 um2 / 6,549 cells / -12.768833 ns slack at the
frozen 20 ns clock. The Graph/Rocket incremental area ratio is 0.229563, below
the preregistered 0.25 area no-go, but Rocket misses timing. The matrix outcome
is therefore `pause-boundary`, not advance or early-no-go. It is partitioned
synthesis-estimate evidence only; common memory, integration, clock tree,
placement/routing, energy, performance, and whole-system claims remain absent.
EXP-0010 is the bounded follow-up implementation for that one pause point. It
preserves EXP-0009 and parameterizes the existing collector for exactly two
admitted timing tuples: legacy 20/1/1 ns and follow-up 40/1/1 ns. EXP-0010 is
bound to recovery-v9, one fixed doubled period, fresh Graph/Rocket runs, and no
prior result reuse. Candidate collection remains prohibited until its
implementation authority and machine-readable manifest are committed.
EXP-0010 implementation authority is `f662d68...1a9e3`; frozen manifest
SHA-256 is `a09a641...b76ef`. It preserves every recovery-v9 identity and
decision field while binding only the 40/1/1 ns follow-up tuple. Fresh
`run-014` Graph and `run-015` Rocket collection is the next authorized action
after the manifest freeze commit.
EXP-0010 freeze commit `993f394` produced fresh complete Graph `run-014` and
Rocket `run-015` partitions at 40 ns. Graph is 11,851.3664 um2 / 1,592 cells /
+31.459913 ns slack; Rocket is 51,625.7632 um2 / 6,549 cells / +7.231165 ns
slack. Area ratio is 0.229563 and both timing reports meet, so the frozen
outcome is `advance-to-integrated-physical`. EXP-0009 remains paused at 20 ns.
This is partition synthesis-estimate evidence only; every performance, energy,
and whole-system claim remains false.
T-0044/S08 now implements the smallest integrated functional prerequisite after
that bounded advance. One generated ChipTop contains the fixed
`RaveilStaticStencilCore`, its TileLink client, the unchanged Rocket fallback,
the common fixture/input provider, one common owned TileLink memory, and a
runtime Graph/Rocket selector. Focused RTL simulation verifies Graph-active,
Rocket-active, inactive-origin-zero, reset, private-output, oracle, and traffic
accounting paths. Separate integrated and matched-Rocket RTL exports pass a
Yosys structural preflight with equal external ports, one Rocket instance in
each closure, equal canonical Rocket-module identity, the same eleven admitted
memory-macro instances, and the same three external clock roots. The successful
comparison report SHA-256 is
`30ffeb2652ae459b33aca2f2b0ccee93d2380e23f871cdf6d437e5a6a2ba9fe2`;
the raw and derived manifest hashes are respectively
`14f1abb186e2f3592bb046ef133db96ebfbb2c633254fd81a53131c41647d54a`
and `617803e806e3a01bbf6ef4a27650144c6ae09b57d9e103efb169e827d87af97f`.
This is development-only `rtl-simulation-functional` and
`rtl-structural-preflight` evidence. No synthesis, mapping, timing, area,
energy, FPGA, ASIC, silicon, or performance result was collected. The ignored
artifact directories are operational local evidence, not an append-once EXP
seal. T-0044 remains open, and EXP-0011 has not been allocated or frozen; the
next gate is independent pre-data fairness and identity review before any
claim-bearing integrated physical collection.
An independent high-reasoning fairness review at candidate `1602e53` passed 41
focused source/checker tests and found no basis for a stronger S08 evidence
class. It blocks EXP-0011 pre-data freeze until a hash-bound contract fixes the
estimand and overhead ledger, common-module/delta connectivity, clock and reset
semantics, macro physical views and PVT/RC constraints, repetition/seed and
uncertainty policy, and append-once raw/derived rules. The existing Graph 1,280
reads plus 256 writes and Rocket 800 reads plus 256 writes remain lawful but
unequal dynamic traffic; no later record may describe them as equal traffic or
equal execution work.
The first independent clean replay passed all 62 then-current focused tests,
all four G1 functional runners, and both deterministic exports, but failed the
final structural comparison because Yosys emitted byte-identical Rocket source
with a different order for independent default assignments and synchronous
updates inside one RTLIL process. The failed preflight log is retained at
SHA-256 `21ade950f7077be6393aaaeb7262018126c2636165f945c6a2c2f0a2b24eda1d`.
The checker correction preserves every dependency and control
boundary while canonicalizing only independent statements within a contiguous
default-assignment run or one synchronous-update run. Sixty-three focused
tests pass, including dependency, duplicate-write, clock, switch, and case
negative tests. Re-analysis of the retained clean raw RTLIL now gives equal
Rocket canonical SHA-256
`09a5cb7cc8214f4fd933eacc6343943b7eba41ab9c3a520075fbf2fa10c43713` and
comparison-report SHA-256
`5f1cc0685bb8d73b7949412fe59fa81b074d5e5ed6e97247a3f3d474290cae6d`.
A fresh independent replay at candidate `bad871d95abcaed9d5589bf24ce40f4fa9666e87`
then passed all 63 tests, G1b through G1e, both exports, the complete Yosys
preflight, and every raw and derived manifest re-hash. Its preflight-log,
raw-manifest, and derived-manifest SHA-256 values are respectively
`59370e6a39cffeeff902f1a7833fe3815aab1ed0967870b121abed29a84b0354`,
`9901949fc321d4a2a77f31c2113f54171cf0406e6533ed3750f34c329eff205f`,
and `bc184ea0368c0ff3138b9b2e8359e1eb069a99de1592e77307f8db66000bc0ab`.
This verifies only the S08 functional/structural prerequisite. It neither
freezes EXP-0011 nor supports a physical or performance claim.
T-0044/S10 now supplies a pure fail-closed validator for the next integrated-
physical contract. It requires an explicit estimand and non-overlapping
Graph/Rocket/common overhead ledger, unequal-traffic disclosure, complete
common/delta connectivity and ownership, normalized clock and reset semantics,
all seven integrated memory-macro Liberty/LEF/PVT/RC identities, unique
repetition seeds and independent uncertainty policy, ordered append-once raw
and derived seals, and complete stop, pause, no-go, and advance rule sets. It
accepts no allocated experiment identity, requires `freeze_state=unfrozen`,
rejects result-bearing or unknown fields, and creates no tracked manifest.
Primary and independent clean-environment verification passed 31 integrated-
RTL tests, 21 physical-proxy tests, and all 102 T-0044 tests. Independent raw
logs are retained at SHA-256
`5f24f7545e80b7dc766c80b83eeb3c2436f3ead1f67ed37ff82a2ce17b05d94d`
and `e25ba501f7eebf1b722f0f46aa7d478129374885bfedbc126acb84d3d8dc8d9b`.
This is host contract-validation evidence only. EXP-0011 remains unallocated
and unfrozen; no synthesis, timing, area, energy, FPGA, ASIC, silicon, or
performance datum or conclusion follows.
T-0044/S11 adds a separate v2 pre-freeze identity and denominator validator
without weakening or silently widening S10's accepted v1 contract. V2 requires
the full implementation commit, integrated and matched config/RTL/export
identities, separate generator and physical toolchain images and root files,
standard-cell and macro physical views, preflight hashes, and common SDC
identity. Its exhaustive nine-component ledger admits common fixture, memory,
cache/interconnect, clock/reset, private validation, and Rocket fallback in
both peers while limiting Graph core/client/selector deltas to the integrated
peer. It also fixes the bounded uint32 stencil and independent oracle boundary,
six lifecycle phases, explicit unequal traffic and CPU load reuse, complete
accounting field names, common physical conditions, and an integrated P&R
area/timing target with energy and hardware claims disabled.
Primary and independent Python 3.14.6 verification passed 35 integrated-RTL
tests, 21 physical-proxy tests, and all 106 T-0044 tests. The independent clean
acceptance log SHA-256 is
`9a55ad52858c37f447ca3cc23794a740f27b6a73f790f5b5425ba5f063dabc55`.
An earlier stripped environment selected system Python 3.9.6 because PATH was
ordered incorrectly; its unrelated `zip(strict=True)` discovery errors remain
preserved at SHA-256
`c1780b6fa98433fb1d08eebd988eef0d969b8ce916919db06d65f24bc7044e51`
as an operational failure, not candidate evidence. S11 stores no manifest,
resolves no declared hash to a physical artifact, and does not yet type the
estimator, fixed decision thresholds, run matrix, or complete evidence seal.
EXP-0011 therefore remains unallocated and unfrozen, and every physical,
performance, energy, FPGA, ASIC, and silicon claim remains false.
T-0044/S12 adds a separate v3 measurement-readiness validator without changing
the accepted S10 or S11 schemas. It fixes a physical-only Graph/Rocket versus
matched-Rocket matrix at paired flow seeds 101 and 202, a balanced run order,
fresh synthesis and P&R per pair, the exact seven-stage physical lifecycle,
and deterministic reruns as reproducibility checks rather than samples. The
typed estimator reports both absolute top areas and the per-seed
`graph_delta_component_area / matched_rocket_component_area` ratio, requires
per-candidate worst setup slack at the common 40 ns condition, and treats the
two seeds only as a controlled sensitivity check. A 95% interval is explicitly
unavailable and may not be imputed. Exact stop, pause, no-go, and
`advance-partial-integrated-physical` rules retain the 0.25 area threshold and
40 ns timing boundary while prohibiting generic go, T-0044 closure, adaptive
threshold changes, and product or hardware claims. ADR-0050-strength raw,
derived, failed-attempt, recovery, and durable-promotion rules are also typed.
Primary and independent Python 3.14.6 verification passed 38 integrated-RTL
tests, 21 physical-proxy tests, and all 109 T-0044 tests. The independent log
SHA-256 is
`782fed7aeb337fff0ea429bbbe59f7aa91f64544695a811eeae6b1c62468647b`,
and the high Performance review found no blocking fairness or overclaim defect.
Dynamic 1/4/16/64/256 latency/traffic work, energy, BOOM, and CGRA are
explicitly outside this physical slice. No manifest, EXP identity, RUN-ID,
physical invocation, result, or claim was created. EXP-0011 remains
unallocated and unfrozen; HCI-02 applies immediately before allocation or a
claim-bearing pre-data freeze.
The owner then authorized HCI-02 for T-0044/S13, but the mandatory pre-data
physical-input binding stopped before EXP allocation. The two S08 exports have
the same seven-entry memory contract, SHA-256
`f318d6bd905d3c8b411082e9c33652593c96ae26d29669da8baf34e726b4de52`,
while the pinned `raveil-physical-proxy-toolchain:v1` image contains zero
required Liberty timing or LEF geometry/pin matches for every required macro.
Matching GDS files are also absent, but are supplemental to the pause.
Standard-cell Liberty, standard-cell LEF, technology LEF, and OpenRCX rules are present and hashed,
so this is specifically a missing memory physical-view boundary rather than an
absent OpenROAD installation. The fixed
`required_physical_input_component_unavailable` pause rule fired. EXP-0011
remains unallocated and unfrozen; no synthesis, placement, routing, parasitic,
timing, area, or other candidate datum was collected. The tracked readiness
receipt is
`docs/experiments/receipts/T-0044-EXP-0011-physical-input-readiness.json`,
SHA-256
`0c64aa343b6801c0846744364f2d5dece7af00e26648d53b437de51ea74f3945`,
with deterministic replay runner SHA-256
`9ff24ece4f418edb706857048507b8c63bd05ad6b4901a242bfbec3199583d18`
and byte-matched tracked transcript SHA-256
`f44b4ec1da28110d60f693529f230d0809f1ab396b8c7c151b86ae740aca1d52`.
The subsequent read-only T-0044/S14 public-source inventory found no verified
Liberty-plus-LEF set for the exact seven-name/dimension/port/pin/mask/PVT
contract and no already qualified common standard-cell substitute. OpenRAM is
a possible view-generation substrate, and a public SKY130 32x512 1rw1r macro
demonstrates that Liberty/LEF views can exist, but neither is the required
drop-in set. S14 is complete as negative planning evidence; S13 remains
Blocked, EXP-0011 remains unallocated and unfrozen, and no candidate flow or
physical result was created. The source and risk packet is retained in
`docs/research/reviews/2026-08-24-T-0044-S14-common-memory-strategy-inventory.md`.
T-0044/S15 now establishes only the repository-owned common-source functional
prerequisite for the standard-cell-memory option. Seven synthesizable modules
implement the exact emitted macro type interfaces and uninitialized,
reset-free, synchronous-read, masked/full-write, and output-hold semantics.
The contract derives eleven instances and 4,631,296 storage bits from the
canonical integrated/matched-Rocket inventory. Verilator passes 28 counted
behavior checks across all seven types, while seven fresh Yosys processes each
collect exactly one `$mem_v2` and find no reachable blackbox. Two PM runs are
byte-identical: simulation raw-manifest and metadata SHA-256 values are
`1061edc55daeb0bc4608c5a54bbb0d2c0f4562d47ae145ac1fe66e8763777ad9`
and
`1792fa166b57f86ed7cdb2a6d3660e1d33afee27fd1dd3ebb3d2ad6f5dfbd38f`;
preflight values are
`b134d7cc1fef25f5649388baabb949f8acfcf5f08d8ee12160b5d5962c0fcbfd`
and
`efd412e6cd65c71ad31fbe8d6b6203cc2621f40c261e19f550f3bb1d02d6d00a`.
Functional execution uses ADR-0062's verified tagless runtime OCI index and
binds its stable payload, Config, RootFS, and verifier identities. This is
`rtl-simulation-functional` and
`physical-input-readiness-no-candidate-data` evidence only. It does not prove
that all eleven instances in both real candidate hierarchies close on this
source, bind a proposal contract to a sealed run receipt, preserve the physical
denominator after mapping, or authorize EXP-0011. S13 remains Blocked; no
candidate synthesis, P&R, area, timing, energy, FPGA, ASIC, silicon,
performance, completion, or go/no-go claim follows.
T-0044/S16 closes the next repository-only pre-data hierarchy and evidence
boundary without resuming S13. Fresh integrated and matched-Rocket exports load
one byte-identical common memory source before either candidate file list.
Yosys `hierarchy -check`, process lowering, memory collection, structural
checking, and flat clock analysis resolve all seven macro types and all eleven
instances with exact named-port pass-through connections, including clocks and
write masks. Both candidates retain the same canonical Rocket module SHA-256
`ee1c4008da0e1cbb4874365fc4ed0d6051beb979c871432bfd7a56043619f8e3`,
the same three approved clock roots, zero unconstrained clock endpoints, and
zero reachable blackboxes. The stable comparison report SHA-256 is
`1d3957d0f6b009d2ffedfac932c837f1051cc0a4f63b798392686e5891a6a7c3`.
The v4 unfrozen Option-B contract now binds the hierarchy comparison and all
raw/derived manifests for hierarchy, source preflight, and functional
simulation. The v2 bundle validator rehashes every listed payload size and
SHA-256, rejects unsafe or incomplete file sets, creates a verified aggregate
manifest, and leaves the completed evidence tree read-only. The PM one-command
run and an independent one-command replay both exit zero, pass 162 scoped
T-0044 tests, reproduce seven source-preflight memories and 28 Verilator
checks, and independently validate their complete immutable bundles. Their
source-preflight and functional-simulation manifests and structural comparison
are byte-identical. Their hierarchy raw-log manifests and dependent run-local
contract/bundle hashes differ only because Yosys records CPU/system time, peak
memory, and time-spent footer telemetry; both raw logs remain unmodified and
sealed. Those footer values are operational provenance, not candidate
performance or resource data. This is `rtl-structural-preflight`,
`rtl-simulation-functional`, and
`physical-input-readiness-no-candidate-data` evidence only. It does not run
memory mapping, synthesis, P&R, or prove that the future mapped netlists remove
all abstract memories. S13 remains Blocked, EXP-0011 remains unallocated and
unfrozen, and no area, timing, energy, performance, FPGA, ASIC, silicon,
equivalence, T-0044 completion, or go/no-go claim follows.
ADR-0050's EXP-0008 promotion boundary is now verified. The dedicated
fail-closed verifier accepted only the two frozen RUN-IDs and expected
seal/report/manifest hashes, recomputed every sealed file size and SHA-256,
verified recovery lineage and the complete non-symlink file set, and rechecked
source identity across transfer steps. Immutable copies of both RUNs at their
logical `Raveil/research-data/EXP-0008/<RUN-ID>/` locators passed
download-based one-way checks; completion markers were transferred last and
read back byte-for-byte. The tracked receipt covers 20 files and 738,617,303
bytes at
`docs/experiments/receipts/EXP-0008-evidence-promotion.json`, SHA-256
`3ea8b815fb0c83c9563f19c22820f14130be6cc9af5bcfa20508d3eb87699392`.
This is remotely durable RTL-simulation evidence. It is not silicon, product,
RFC-0005 go, T-0044 completion, or a general workload speedup; energy,
synthesis timing, area, IP disposition, and missing organizations remain open.
ADR-0049 now fixes the post-EXP-0010 transition boundary without changing the
frozen EXP-0009 or EXP-0010 manifests. The current `StaticStencilRegion` remains a hardwired stencil
FSM with a descriptor binding tag, not a configurable CGRA or general Graph
executor. Any configurable successor must be compared as VLIW/CGRA/dataflow,
reuse a reviewed public backend when adequate, accept at least three distinct
graphs without RTL regeneration, and preserve the same CPU/backend
effect/authority/fallback contract. No such configurable executor, public-CGRA
adapter, three-graph proof, or compiler/configuration/PPA comparison is
implemented; this is an accepted transition/no-go boundary, not new evidence.
The roadmap now separates the completed T-0105 generic Chisel/RISC-V substrate
from T-0057 prior-art/IP boundary plus Graph-contract definition and T-0042
Graph RTL implementation. T-0057 phase A now has a non-authoritative,
locator-backed matrix covering conventional OoO, EPIC, TRIPS/EDGE, WaveScalar,
DySER and
spatial-CGRA classes. It finds high mechanism similarity and records preliminary
WaveCache and EDGE-family patent hits as unreviewed; it establishes neither
novelty, infringement nor freedom to operate. ADR-0039 later accepts only the
RFC-0005 bounded static candidate for repository-owned RTL simulation; no
product Graph ISA or architecture has been accepted. This is a
planning/research
correction, not a CPU experimental result. T-0105 includes a
functional tooling smoke: under an explicit linux/amd64 Docker environment on
the Apple Silicon host, Chisel 7.2.0 emitted SystemVerilog for an owned four-bit
counter and Verilator 4.038 executed the C++ harness to
`CHISEL-SMOKE-V1 status=OK cycles=10 value=8`. This is emulated-host tooling and
RTL functional evidence only. No RISC-V core, Graph RTL, CPU comparison, or
performance evidence has run in that owned-counter path.
T-0105 also has a local ignored external Rocket Chip checkout at
`749a3eae9678bc70b029c5b9091fae33fad539c4`, the gitlink selected by Chipyard
1.11.0. Its fixed Chisel, CDE, and HardFloat submodules are fetched by the owned
revision-checking helper. An owned fixed Git/Nix/Docker wrapper now elaborates
the unmodified Rocket `DefaultSmallConfig`, builds the unmodified
`DefaultConfig` Verilator emulator, and requires all 16 official `rv64mi-p`
tests to pass with no failed logs. The verified run exited 0 and reported Nix
2.13.3, Mill 0.11.1/OpenJDK 19.0.2, Rocket's Scala 2.13.12/Chisel 5.1.0,
CIRCT firtool 1.56.1, Verilator 5.012, clang 11.1.0, CMake 3.26.4, Ninja 1.11.1,
and DTC 1.7.0 on emulated Linux amd64 under an Apple Silicon Docker host.
ADR-0038 fixes the ignored-source, immutable-container, locked Git-flake and
selected-package boundary. It deliberately avoids the upstream mutable Python
shell hook, excludes generated output from Nix input identity, and keeps a
version-matched Nix-store, Mill `out/`, and Mill/Coursier user-cache volume set
so foreign or vanished absolute paths cannot be silently reused. The
user-facing `./hardware/chisel/run-rocket-reference.sh` path completed both a
clean build/execution and a second separate-container cached rerun with the
required 16/0 marker.

This closes T-0105 as RTL functional/simulation substrate evidence only. The
result is not a cycle comparison, performance or energy measurement, area or
timing estimate, Graph RTL result, OoO-removal result, FPGA result, silicon
result, or CPU/ISA advantage. ADR-0039 now satisfies the T-0057B acceptance gate
for the narrow T-0042 simulation slice; T-0044 remains the later matched
comparison.

T-0057B now has an Accepted contract in RFC-0005. ADR-0039 authorizes, for
repository-owned RTL simulation only, an operation-level uint32 five-point
stencil lowered at installation to a
fixed-cycle schedule over bounded resources. The candidate has an internal
simulation interface, disjoint read-only/private-output objects, no runtime
token store, alias speculation, general LSU, rename, ROB, or architectural
block commit, and an ordinary RV64IM fallback. It defines configuration
identity, invalidation, exact semantic checking, complete configuration/staging
accounting, interruption behavior, and numerical no-go thresholds centered on
energy rather than speed.

The updated T-0057 matrix maps the draft to TRIPS/EDGE, WaveScalar, DySER,
EPIC/VLIW, and CGRA prior art. Similarity remains high, especially for installed
static configuration, hybrid fallback, and private-output publication. The
three patent discoveries remain unreviewed and fail-closed. The 2026-08-12
feature-to-document review records inspected claim locators and excluded
features without making a legal conclusion. ADR-0039 then admitted only the
fixed static slice for T-0042 functional validation; T-0044 measurement remains
separately gated.

T-0042 now implements the first owned RFC-0005 functional slice. The
`raveil.static-region/v1` compiler deterministically emits five `LOAD_U32`, four
`ADD_U32`, and one `STORE_U32` nodes plus nine SSA edges, affine object effects,
a six-phase logical schedule, one-read/one-add/one-write resources, zero runtime-ready
slots, and the ADR-0039 exclusion set. An independent validator recomputes the
graph, schedule, object, effect, bound, and fallback invariants. Canonical
descriptor SHA-256 is
`d4bf9395a510385f42ba4a193ae2c747f308ad502a8fe807843ed19c2fa4d1e2`.
The validator also rejects unknown fields, alternate schedules, altered effect
kinds, and any dynamic-issue resource request rather than treating a different
descriptor as compatible with the fixed RTL.

The owned Chisel `StaticStencilRegion` binds the first 64 hash bits as a
configuration tag and now reaches one 1,024-word physical instance of the
ADR-0043 request/response scratchpad for staging, execution, and validation.
Input `[0,324)` and private output `[324,580)` remain disjoint logical regions.
It applies the fixed logical schedule over all 256 output points and has no
runtime dependency queue, token store, rename, ROB, general LSU, commit
frontier, or issue-mode switch. Cancellation clears output validity; restart
begins the fixed schedule from point zero.

The user-facing `./hardware/chisel/run-static-stencil-rtl.sh` path completed in
linux/amd64 Docker emulation on the Apple Silicon host. Chisel 7.2.0 emitted
SystemVerilog and Verilator 4.038 checked two complete invocations with distinct
inputs against an independently implemented C++ oracle: all 512 output words
and both checksums matched. A third invocation cancelled after 17 execution
cycles left `outputValid=0`, and a subsequent full restart passed. The fixed
schedule asserted 3,072 interface-accounted execution cycles per complete invocation, below the
8,192 functional bound.

The first compile failed because the Chisel utility import for `switch/is` was
missing. The first executable RTL then disagreed with the oracle at output 15
because a four-bit column plus one wrapped before assignment to a five-bit
wire. Adding the import and widening row/column slices before addition fixed
both failures; the independent full-output check is retained.

This is RTL simulation-functional evidence only. The cycle count is a schedule
correctness assertion, not comparative performance. No Rocket/BOOM comparison,
energy, area, timing, OoO-removal, FPGA, silicon, CPU/ISA, novelty,
non-infringement, or FTO claim follows. T-0057 is complete as contract/prior-art
and functional-schema validation.

T-0042 now also has the implementation-neutral
`raveil.simulation-adapter/v2` functional boundary. It fixes the descriptor,
workload semantics, disjoint private scratchpad model, useful-operation counts,
implementation identity, completion state, and installation/staging/execution/
completion/validation/publication accounting fields without importing Rocket
or BOOM types. ADR-0041 corrects the v1 ambiguity between semantic validity and
matched resources: every observation now reports its actual memory model,
resource-match verification, and matched-comparison readiness. Exact validation
rejects unknown fields, mismatched semantic counts, publication before
authority, an asserted total while any phase is unknown, or a match claim for
anything other than the required fixed-latency banked scratchpad. Common v2
adapter SHA-256 is
`56dbe3f2ab479233eb5e4fe1c79eb06e07458b42ea77acebb471a101afd24c1e`.

The legacy Graph smoke still emits validated v2 records for complete, cancelled, and
restart invocations. All are deliberately `accounting_complete=false` with
`total_cycles=null`: installation, completion, and publication costs are not
yet available. The reported 3,072 execution, 648 staging, and 512 validation
cycles therefore cannot be added or compared as an end-to-end result.
They also declare `memory_model=owned-private-scratchpads`,
`resource_match_verified=false`, and `matched_comparison_ready=false`; this
record class predates and remains separate from the ADR-0046 strict controlled
record.
T-0042 now has semantic stencil records for Rocket, BOOM normal, BOOM's
serialize-dispatch diagnostic, and the Graph RTL behind this boundary. It
also has the separately verified strict controlled three-way resource boundary;
T-0044 remains the matched measurement task.

The strict `raveil.controlled-run/v1` records bind contract
`f95cc6dc896659a32f1407f0f5a8f74ec475d208632f9dd5ff4d43d9cb2f7978`,
resource
`16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748`,
input
`65b00605d894f4a6934862137c751e7f25e7c86a41077f6172cb7142c7ab9254`,
and oracle/output
`dd749f0f218c7389730bef5b97af4e9203b0501d5ec57fa48ffa643356f23582`.
They also bind each admitted source set, built simulator or ELF artifact,
pinned toolchain contract, and derived implementation configuration. The
three-way aggregate records Graph/Rocket/BOOM configuration SHA-256 values
`3ff3df8a...a33b` / `a7899b30...3a16` / `29659996...3e41`, so a changed
workload, linker input, binary, simulator source, toolchain contract, or peer
configuration fails closed instead of aliasing a prior run.
Graph phases are `0/648/3072/1/512/0`, total 4,233; Rocket phases are
`44630/3865/14621/410/16513/0`, total 80,039; and BOOM phases are
`44761/4208/21892/425/16513/0`, total 87,799. These are lifecycle accounting
observations for one pinned RTL simulation, not comparative timing results.

ADR-0044 now adds the first CPU-side translation target without pretending it
is that matched scratchpad. A repository-owned Chipyard overlay removes the
inherited subsystem scratchpad from dedicated Rocket and BOOM configurations
and attaches a 32-bit, maximum-one-outstanding TileLink manager at
`0x08000000`, with a phase/counter control page at `0x08010000`, to the
uncached peripheral bus. The manager implements logic for `Get`, `PutFull`, and
`PutPartial`, byte masks, response backpressure, invalid phase-write denial,
source/size response routing, and aggregate software-declared phase counts.
This placement is deliberately observable and resource-unmatched; initiator
attribution, equal ports/arbitration/buffering, and common-memory promotion
remain unverified. The same phase-fenced workload now passes through both the
Rocket and BOOM CPU paths as described below.
The elaboration runner therefore reports execution not run, resource matching
false, comparison readiness false, and performance not measured.
This is not yet the ADR-0043 common-contract CPU adapter: the phase begins as a
software-declared label and does not provide owned semantic initiator metadata.

The owned manager now also passes a direct, monitor-enabled TileLink RTL
simulation. Protocol V4's raw bounded client issued 30 legal negotiated
transactions and
verified `PutFull`, two `PutPartial` byte-mask patterns, readback, invalid
phase-write denial, D-channel backpressure stability, maximum-one-outstanding
backpressure including same-source reuse rejection, reset phase, selected
aggregate counters, expected/unexpected source-class conservation,
accepted-to-completed phase correlation, and D response
`param`/`size`/`source`/`sink`/`denied`/`corrupt` metadata. This closes the
manager-local protocol corner-case bootstrap only. No CPU instruction executed;
phase remains software-declared, initiator attribution and the ADR-0043 common
contract remain open, and resource matching, comparison readiness, fixed
end-to-end latency, performance, energy, and area remain unverified.
Unlike V2, whose expected range covered every client source, V4 uses the
half-open classifier range `[1,3)`: in-range traffic completed 3/3 and deliberate
boundary sources 0 and 3 completed as unexpected 4/4. Requests from this raw
client, which has no DCache-origin request field, completed with DCache-origin
accepted/completed 0/0 and non-DCache-origin 7/7. This is a negative control
for manager-local classification and A/D conservation only, not evidence of CPU
execution, target-ELF semantic initiator identity, or loader/debug exclusion.
A second test-only top now drives the origin field true on every upstream raw
request and then removes that field at an explicit diplomacy adapter before the
same manager. The same 30-transaction driver completed with origin 0/0 and
non-origin 7/7, showing that negotiated metadata loss fails closed through A/D
accounting. This models field removal only; it is not an execution of a real
FESVR, loader, or debugger path and does not close semantic attribution.

The same owned manager now passes one phase-fenced CPU workload through both
the dedicated `RaveilOwnedRocketConfig` and `RaveilOwnedSmallBoomConfig`
Verilator systems. The identical bare-metal RV64 ELF read reset phase zero,
performed full-word and two byte-lane writes through `0x08000000`, selected
execution phase two through `0x08010000`, and checked the resulting data plus
aggregate accepted/completed and per-phase counters. Both independently
decoded signatures matched
`11223344`, `5522aa44`, `cafebabe`, phase 2, accepted/completed 8/8,
installation reads/writes 2/3, and execution reads/writes 2/1. This upgrades
both CPU paths for this bounded workload to `rtl-simulation-functional`. The
shared runner admits only those two named configurations and keeps separate
content-addressed simulator volumes; its payload hash covers the overlay, ELF
source, linker script, source-map verifier, signature verifier, and shared
runner, while the marker separately identifies the CPU/configuration. Exact
generated-graph verification identifies the DCache-MMIO client ranges at the
manager as `[8224,8256)` for Rocket and `[8288,8320)` for BOOM, disjoint from
the `[0,8192)` SimTSI/FESVR serial range. Runtime audit registers latch the
accepted data A-channel source and software-declared phase until D completion.
Both CPU runs observed expected-client accepted/completed 8/8,
unexpected-client 0/0, in-range final sources, and final accepted/completed
phases 2/2. A repository-owned adapter immediately after each DCache adds a
one-bit structural request field before the tile master Xbar. The pinned Xbar
is patched ephemerally to preserve negotiated request fields while applying
their declared false defaults to clients without the field. CPU signature V3
extends the retained 22-word prefix to 30 words; both CPUs observed structural
DCache-origin accepted/completed 8/8, non-DCache-origin 0/0, final origin
sources inside their config-specific ranges, and final origin phases 2/2.
The manager latches the field at A acceptance and holds it with source and
software phase until D completion. These config/Xbar/fragmenter-dependent
source IDs establish a
TileLink client class, not an ISA identifier or proof that the target ELF was
the semantic initiator. The structural bit proves only that the request crossed
the DCache-local adapter; it does not identify an instruction, PC, ELF, or
exclude untested loader/debug DCache activity. Matching signatures prove
semantic agreement for this one workload only. The evidence does not implement
ADR-0043 owned semantic initiator
metadata, establish equal resources, isolate OoO, or support a performance,
energy, area, OoO-removal, FPGA, or silicon claim.
These older topology and attribution diagnostics do not themselves implement
the ADR-0043 common contract. The separate ADR-0046 controlled-run slice now
implements the minimum common owned-resource boundary required to close
T-0042; general semantic attribution remains outside that boundary.

The shared CPU runner now also executes a dedicated loader-path negative probe
in each pinned configuration. Its ELF contains one four-byte writable
`PT_LOAD` at the owned data page and keeps code, signature, and `tohost` in
main RAM; exact `readelf` and symbol checks fail closed on layout drift, and
the simulator invocation contains no `+loadmem` override. Before the CPU
accesses the page, the manager observes two accepted/completed requests from
the `[0,8192)` serial class, DCache-origin 0/0, and non-origin 2/2. The two
requests are the pinned FESVR transport's aligned read/write sequence, not a
one-request-per-segment invariant. After the CPU reads the loaded word, totals
are 3/3, with DCache-origin 1/1, non-origin still 2/2, and the final origin
source in the configuration-specific DCache range. This is bounded functional
RTL evidence for the tested SimTSI/FESVR PT_LOAD path followed by a structural
DCache crossing in the same simulation. Source and origin metadata do not
prove the target ELF's semantic initiator, and Debug SBA, other loader/debug
paths, durable semantic attribution, and matched resources remain open.

A dedicated repository-owned DMI harness now exercises one concrete Debug
System Bus Access path in both pinned CPU configurations. Exact generated
graphs place the Debug client at `[8192,8224)`, with Rocket DCache MMIO at
`[16416,16448)` and BOOM DCache MMIO at `[16480,16512)`. In each bounded RTL
run, an 8-bit Debug SBA write of `0xa5` completed as unexpected/non-DCache
origin 1/1 at software phase zero; the subsequent CPU read completed as
expected/DCache origin 1/1, bringing aggregate accepted/completed to 2/2.
Request source and phase were retained from A acceptance through D completion.
This establishes generated-topology and runtime TileLink client-class
classification for the tested path only. It does not halt/resume the hart,
prove an instruction, PC, target-ELF semantic initiator, or exclude every
loader/debug path. Resources remain unmatched and no performance, power, area,
OoO, FPGA, silicon, novelty, non-infringement, patent-clearance, or FTO claim
follows.

The regular CPU and PT_LOAD signatures now also feed a fail-closed
cross-workload audit. Rocket reused exact DCache source 8224 and BOOM reused
8288 across two distinct ELF binaries with different payload/semantic
signatures. This executable counterexample shows that DCache source and origin
class do not carry a unique ELF semantic identity. It narrows the next step to
a separately decided CPU-side witness with replay/flush/commit semantics; it
does not itself provide that witness.

ADR-0045 now fixes that next attribution policy without claiming its
implementation. CPU-owned, non-software-writable tokens name candidate memory
operations before DCache request acceptance; Rocket binds a bounded sequence
to the corresponding EX/MEM PC and epoch, while BOOM uses sequence/epoch as
identity and ROB index plus branch mask only as lifecycle context. Exhaustion
or wrap alias fails closed. Replay retains one token, reset advances its epoch,
loader/FESVR/Debug traffic cannot mint it, and kill, exception, rollback, stale
epoch, or duplicate outcome fails closed. Load attribution requires both
successful memory response and architectural retirement; store attribution
requires retirement, CPU-specific store authorization, and owned-manager D
completion. A post-A exception does not cancel transport and any later side
effect is reported as a lifecycle violation.

A repository-owned standalone Chisel observer now makes that lifecycle policy
executable against synthetic events before any pinned-core hook. Its
assert-enabled `linux/amd64` RTL simulation accepted 21 tokens and conserved
them as 3 committed loads, 1 committed store, and 17 noncommitted outcomes. It
separately recorded 8 core attempts, 1 core replay, 1 DCache retry, A/D counts
of 7/7, 5 retirements, 1 store authorization, 2 unknown inputs, and 8
violations. Positive load/store cases and pre-A kill, post-A exception,
reset-outstanding, stale epoch, stripped/untagged metadata, duplicate token and
outcome, invalid completion, D error, and sequence exhaustion negatives passed.
An exact-schema verifier rejected missing fields, changed counters, and
duplicate markers and checked terminal conservation. Review found and the RTL
regression closed one invalid-completion promotion bug by requiring the event
that completes the existing ADR-0045 load/store conjunction to itself be a
valid D-completion, retirement, or store-authorization transition.
The event source remains synthetic: pinned Rocket execution, CPU signal
binding, target-ELF semantic initiator attribution, the BOOM probe, common
bridge connection, resource matching, matched comparison, and performance are
all still unimplemented or unverified.

A separate pinned Rocket request/response/WB diagnostic now observes the exact
`0x08000100` workload at the `RocketCore` DCache boundary. It allocates only
when a request is accepted, captures that request's DCache tag, matches the
load data response separately, and observes exception-free WB by PC and
load/store kind. The bounded RTL run records one first-attempt store and one
first-attempt load, two retirements, one matched load response, and the exact
two-word signature. This is partial `rtl-simulation-functional` evidence only:
the DCache-local tag is not a durable token, store WB is not store
authorization or owned-manager completion, and replay, kill, redirect,
exception, reset/epoch, BOOM lifecycle, common-bridge admission, semantic
initiator identity, resource matching, and performance remain unverified.

The pinned Rocket diagnostic now also closes one bounded same-cycle
accepted-request/redirect outcome. A first owned-address load completes as
sequence 1 and supplies a data dependency before a deliberately taken branch
places an owned-address store on the wrong path. The store request is accepted
while the older branch resolves as a MEM-stage direction misprediction. The
diagnostic records `allocate/request/kill` with `promotion=blocked` as sequence
2, then requires a second load's response plus WB as sequence 3. The wrong-path
store has no WB retirement, and the two loads both observe `0xc5686cac` in the
exact run. This is post-request redirect bookkeeping and differential readback
for that simultaneous case, not pre-request-kill coverage, proof of DCache S1
cancellation or TileLink A/D completion, general absence of a memory side
effect, multi-live-token support, durable token transport, semantic initiator
identity, resource matching, or performance evidence.

The same exact redirect workload now has a separate pinned Rocket DCache-fate
diagnostic. One cycle after the accepted sequence-2 request, the Rocket-facing
S1 record directly reports `s1_kill=1` and `s2_kill=0`; its sequence, PC,
address, and local DCache tag match the existing killed request. An independent
owned-manager monitor records exactly two successful `Get` A/D pairs for the
before/after loads, with sources 8240 and 8224 inside the exact generated
Rocket manager range `[8224,8256)`, and records no `Put` for the probed address.
Both loads observe `0x682513da`. This is bounded `rtl-simulation-functional`
evidence for a Rocket-local request/S1 correlation and separate manager-local
A/D source correlations in that exact log. No token is carried from Rocket
through DCache/TileLink, so it is not semantic-initiator attribution, general
transport cancellation or side-effect proof, resource matching, or a
performance, power, area, OoO, FPGA, silicon, novelty, non-infringement,
patent-clearance, or FTO result. Pre-request kill, later-cycle kill/exception,
replay, reset/epoch, multi-live-token operation, and the BOOM lifecycle probe
remain open.

A fourth pinned Rocket diagnostic now covers one distinct later post-request
exception boundary. An exact misaligned load at `0x08000101` is accepted at
the Rocket DCache request interface, and the retained Rocket-local PC and tag
match a later WB misaligned-load exception with cause 4, `ma_ld=1`,
`take_pc_wb=1`, and `promotion=blocked`. Aligned loads before and after the
trap both return `0x682513da`; the trap handler verifies `mcause`, `mtval`, and
`mepc` and resumes exactly once. This is bounded `rtl-simulation-functional`
evidence for a Rocket-local accepted-request/WB-exception correlation. It is
not a post-TileLink-A exception, does not carry a token through DCache or
TileLink, and does not prove general rollback, side-effect absence, semantic
initiator identity, resource matching, or performance. Pre-request kill,
post-A exception/rollback, replay, reset/epoch, multi-live-token operation,
and the remaining BOOM lifecycle cases remain open.

The first pinned BOOM lifecycle diagnostic now covers one positive load at the
BOOM LSU boundary. For the exact `0x08000100` load, a repository-owned sequence
correlates one accepted LSU DCache request, its matching DCache response, and
one architecturally valid ROB commit. The bounded trace reports PC
`0x80000010`, ROB index 4, LDQ index 0, response/signature value `0xdaab9780`,
and `promotion=eligible`. Sequence is the identity; ROB/LDQ indices, branch
mask, and lane remain context only. No token is carried through DCache or
TileLink, and this does not prove target-ELF semantic initiator identity, store
authorization, replay/kill/exception/reset behavior, complete BOOM lifecycle,
resource matching, OoO effects, or performance. Those claim boundaries remain;
ADR-0046 routes the general lifecycle cases to T-0106. The separate controlled
common-resource and complete-accounting slice now closes T-0042 without
promoting this diagnostic to general authority.

A second pinned BOOM diagnostic now covers one deterministic but narrower
negative ordering. At the exact `0x08000101` misaligned-load addrgen candidate,
an LSU-local repository sequence retains the PC and ROB/LDQ context, correlates
the following LSU misaligned-load exception, then observes one matching DCache
request accepted after that exception but before the later global ROB rollback
state. The exact trace has no matching response or architectural commit, and
the faulting ROB entry does not appear in a rollback row (`matching_rbk=0`).
This is bounded `rtl-simulation-functional` evidence for the exact BOOM-local
`candidate -> exception -> request -> rollback-state` order only. Because the
exception precedes request acceptance, it is not the still-required
post-request exception/cancellation case; absence of a response in this trace
does not prove transport cancellation or general side-effect absence. The
sequence is not carried through DCache or TileLink; general rollback, semantic
initiator identity, store authorization, replay/reset behavior, resource
matching, OoO effects, and performance remain unproven.

A third pinned BOOM diagnostic now covers one exact store-authorization path.
At PC `0x8000001c`, a repository-local sequence correlates architecturally
valid ROB retirement and the matching STQ committed transition with one
accepted DCache store request, one store response/succeeded transition, and
the later STQ clear. The exact context is ROB index 7, STQ index 3, branch mask
0, and lane 0. Independently, the owned-manager audit records one successful
`PutFullData`/`AccessAck` pair at `0x08000100` with source 8304 and one
successful readback `Get`/`AccessAckData` pair with source 8288; the software
readback equals `0x51a7c0de`. This is bounded `rtl-simulation-functional`
evidence for a BOOM-local authorization/request/response/clear correlation and
a separate manager-local A/D source correlation. The repository sequence is
not carried through DCache or TileLink, so same-token owned-manager D
completion, complete store attribution, semantic initiator identity, general
store behavior, resource matching, OoO effects, and performance remain
unproven.

A fourth pinned BOOM diagnostic now covers one cacheable, CPU-local
post-request redirect. The exact wrong-path `lwu` at PC `0x80000048` and DRAM
scratch address `0x80010000` produces one accepted LSU DCache request, its
matching response, and a later branch-mask kill with no matching architectural
commit. The repository sequence remains identity; PC, ROB index 17, LDQ index
0, branch mask 1, and lane 0 are bounded validation context. The owned PBUS
manager is not exercised, no token crosses DCache or TileLink, and no
post-TileLink-A cancellation, transport side-effect absence, semantic
initiator, same-token manager completion, general rollback, resource matching,
OoO effect, or performance result follows.

A fifth pinned BOOM diagnostic now carries the repository-owned token for the
exact committed store at PC `0x8000001c` across the BOOM DCache request and
uncached TileLink A metadata. The owned manager latches `{valid=1, epoch=1,
sequence=1}` with the exact `PutFullData` acceptance at `0x08000100`, retains
it across backpressure, and emits the same token with the successful
`AccessAck` D completion and source 8304. The BOOM-local authorization,
request, response, and STQ-clear ledger uses the same epoch/sequence, and
software readback remains `0x51a7c0de`. Absent producers default the negotiated
fields to invalid/zero, malformed fields classify invalid, and verifier
mutations reject missing, altered, duplicated, denied, or source-mismatched
records. This is bounded `rtl-simulation-functional` transport-correlation
evidence for one pinned BOOM store only. Epoch 1 is diagnostic and fixed;
reset/redirect advancement, stale/duplicate/exhaustion behavior, replay,
multi-live tokens, BOOM loads, Rocket parity, post-A rollback, loader/FESVR/
Debug negatives, CPU-side consumption of manager D, common-bridge promotion,
semantic initiator identity, resources, OoO effects, and performance remain
unproven.

A sixth pinned BOOM diagnostic now exercises the negotiated default-invalid
case live. It advertises the three token fields at the BOOM DCache client but
deliberately omits LSU token minting and I/O-MSHR token assignment. The same
committed store still completes its owned-manager `PutFullData`/`AccessAck`
pair and software readback, while the manager observes `{valid=0, epoch=0,
sequence=0}` unchanged at A and D and classifies both records unknown. This is
bounded `rtl-simulation-functional` evidence that one absent producer becomes
the explicit negotiated default and does not promote semantic attribution,
without denying the underlying transaction. It does not test stripping after a
valid producer, malformed nonzero metadata, stale epochs, duplicate/exhausted
tokens, reset with work outstanding, replay/source reuse/backpressure, untagged
loader/FESVR/Debug traffic, BOOM loads, Rocket parity, CPU-side D consumption,
common-bridge promotion, semantic initiator identity, resources, OoO effects,
or performance.

A seventh bounded diagnostic distinguishes absent production from metadata
loss after a valid producer. It first observes the exact BOOM token
`{valid=1, epoch=1, sequence=1}` at I/O-MSHR source 3, then a test-only patch
clears the token values before the request reaches manager source 8304. The
manager observes invalid/zero on both A and D, classifies the token unknown,
completes the Put, and preserves the verified store readback. The two source
numbers remain transport coordinates, not token identity. This closes only the
fixed value-clearing stripped-after-valid negative. Field removal, malformed
nonzero metadata, epoch/reset/stale/duplicate behavior, replay/source reuse,
multi-live operation, semantic promotion, resource matching, OoO effects, and
performance remain unproven.

T-0042 now also has a standalone post-fragmenter TileLink-to-owned-contract
bridge before CPU integration. The bridge accepts negotiated `Get`, `PutFull`,
and `PutPartial` requests, translates them into an upstream-type-free owned
request carrying write/address/data/mask plus explicit adapter-supplied
initiator and lifecycle phase, and retains TileLink source/size until the owned
response is consumed on D. An independent owned target holds response data,
error, operation, initiator, and phase under backpressure and asserts
accepted/completed conservation. The assert-enabled pinned Chipyard/Verilator
harness passed six requests with full and two partial writes, both byte masks,
readback, deterministic range denial, single-outstanding request blocking, D
backpressure, source/size routing, and initiator/phase correlation at 6/6.
The exact rerun verified the content-addressed assembly checksum before
reproducing the same marker. This proves the mechanical bridge and explicit
metadata handoff only: the harness supplies the initiator/phase inputs, neither
CPU is connected, semantic CPU/ELF identity remains unproven, and resources
remain unmatched. No performance, power, area, OoO, FPGA, silicon, novelty,
non-infringement, patent-clearance, or FTO conclusion follows.

The narrower pinned-source candidate is now implemented diagnostically:
repository-owned Rocket and BOOM hooks insert the adapter immediately after
each DCache and before the shared tile master crossbar. Runtime positive paths
and the raw-client absence plus explicit field-stripping negative paths verify
field retention and fail-closed false classification in these bounded
harnesses. A concrete SimTSI/FESVR PT_LOAD probe now additionally observes
serial-class traffic as non-origin before one tagged CPU read in the same run.
This structurally separates that tested transport path from the observed CPU
class, but it still cannot identify a particular ELF instruction, PC, or
semantic intent, and it does not test every loader/debug path. Selecting a
durable ADR-0043 semantic metadata assignment boundary requires later policy,
negative tests, and a new decision if the field is promoted beyond ADR-0044
diagnostics.

ADR-0040 now pins the BOOM control source. Chipyard tag 1.11.0 at
`ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1` selects BOOM
`9459af0c1f6847f8411622dac770ac78fe10847c`; the initial configuration is
`chipyard.SmallBoomConfig`. The ignored detached checkouts are clean, origin
and parent gitlink checks pass, and BOOM's BSD-3-Clause plus SiFive Apache-2.0
notice hashes are fixed in `boom-pin.env`.

Source inspection verifies chicken CSR `0x7c1` mask `0x8`. Its bit-3
`disableOOO` diagnostic makes dispatch wait for an empty ROB/LSU, but does not
remove rename, ROB, issue, physical-register, or LSU structures. It is now
named `boom-ooo-disabled-diagnostic`/`serialize-dispatch`, never an in-order or
structurally stripped BOOM. `verify-boom-reference.sh` emits a successful
source-verification marker.

The owned BOOM bootstrap now initializes only explicit public Chipyard
gitlinks, compiles the 56-source BOOM Scala project, and elaborates
`chipyard.SmallBoomConfig` through the integrated Chipyard generator. The
successful functional marker confirms non-empty FIRRTL and annotations with a
`BoomCore`; emitted parameters include one-wide decode, three issue ports, a
32-entry ROB, three 8-entry issue windows, 52 integer physical registers, and
8/8 load/store queues. These are configuration/elaboration facts, not measured
costs. The elaboration wrapper uses a digest-pinned Temurin 17 base but unlocked
APT and Maven resolution, so it is not a measurement environment.

The separate functional-simulator path pins a Miniforge linux/amd64 base,
Chipyard's lean simulator lockfile and hash, Verilator 5.020, RISC-V GCC 12.2.0,
DTC 1.6.1, CIRCT firtool 1.61.0 and the installed firtool binary hash. It uses
explicit public parent gitlinks and read-only source mounts. The first owned
workload executed on `chipyard.SmallBoomConfig`: an RV64 ELF summed 1 through
16, stored and loaded the result, checked 136, and signalled success through
`tohost`. Verilator reached its normal finish and emitted
`BOOM-FUNCTIONAL-SMOKE-V1 status=OK`.

This is a minimal RTL simulation-functional execution, not the RFC-0005 Graph
workload and therefore not a common-adapter record. The conda-lock reader
bootstrap remains an unlocked package solve, and the upstream CIRCT downloader
is accepted only after validating the installed binary hash. No performance,
energy, area, timing, OoO comparison, Graph comparison, FPGA, or silicon result
follows.

The same simulator also executed the identical workload after the tracked ELF
set CSR `0x7c1` mask `0x8`, read the bit back, and failed closed to a non-success
`tohost` code if the readback was absent. The diagnostic run completed normally
with `BOOM-SERIALIZE-DISPATCH-SMOKE-V1 status=OK`,
`diagnostic=serialize-dispatch`, and `structures=retained`. This proves only
functional execution under that CSR setting; it neither proves which dynamic
instructions overlapped nor measures any latency, energy, area, or benefit.
This minimal diagnostic does not by itself supply a semantic stencil record or
matched comparison boundary.

BOOM normal and serialize-dispatch modes now also execute the RFC-0005 semantic
five-point stencil rather than only the minimal sum smoke. One tracked RV64
fallback initializes 324 deterministic uint32 words, computes all 256 outputs,
and exposes the private output range through FESVR's signature boundary. A
separate Python parser validated every word against the repository-owned oracle;
both modes produced checksum `0000007f11ba2640`. Their validated adapter v2
records identify `boom-ooo` and `boom-ooo-disabled-diagnostic`, but report
`memory_model=cache-backed-variable-latency`, all lifecycle cycles unknown,
resource matching false, and comparison readiness false. This is semantic
functional evidence, not the RFC-0005 isolation comparison.

The pinned `chipyard.RocketConfig` Verilator simulator now executes the same
tracked C/assembly stencil and validates the same 256-word FESVR signature
against the same independent oracle. It also produced checksum
`0000007f11ba2640` and emitted a validated `rocket-in-order` adapter v2 record.
That record is likewise cache-backed, has every lifecycle cycle unknown, and
sets resource matching and comparison readiness false. All required control
identities now have semantic functional records; the common fixed-latency
banked scratchpad/resource boundary remains unimplemented and unverified.

ADR-0042 now records one intermediate shared-memory prototype. Pinned
`AbstractConfig` gives both CPU controls the same 64 KiB, one-bank subsystem
TileLink RAM at `0x08000000`. A separate linker keeps code and `tohost` in the
normal `0x80000000` region while placing the 324 input words and private 256
output words at `0x08000000` and `0x08000510`. Rocket, BOOM normal, and the
serialize-dispatch diagnostic all completed from this placement and again
matched the 256-word oracle with checksum `0000007f11ba2640`. Their v2 records
use `memory_model=shared-tilelink-banked-scratchpad-unverified-latency`; all
cycle fields remain unknown and both resource matching and comparison readiness
remain false. Common addressable TLRAM is a functional bridge, not proof of
fixed latency, matched CPU paths, or a Graph-side common adapter.

T-0042 now also has a passive TLRAM endpoint observer. Separate non-tracing
Verilator models bind below the bank-local TileLink fragmenter and match each
accepted single-beat A request to its completed D response by source ID. In the
pinned Rocket, BOOM normal, and serialize-dispatch diagnostic runs, all three
signatures remained correct and each observer reported 296 completed beats,
all classified as reads: 162 in the input range, 128 in the private-output
range, and 6 elsewhere;
all observed endpoint intervals were one cycle with no unmatched response,
premature source reuse, or pending request. No write beat was observed, and the
boundary cannot attribute initiator or lifecycle phase. These are run-local
functional diagnostics only. They do not prove fixed end-to-end CPU latency,
exercise a comparable write path, match the Graph storage, or change either
resource matching or comparison readiness from false.

ADR-0043 now establishes a Raveil-owned local scratchpad transaction boundary
before either side is adapted. `OwnedFixedLatencyScratchpad` has one request
and response stream, at most one outstanding transaction, explicit read/write,
byte mask, initiator and lifecycle phase, deterministic range errors,
backpressure, and accepted/completed/stall/pending counters. Its assert-enabled
emitted RTL passed a standalone Verilator harness covering reads, writes,
partial writes, request/response stalls, attribution, and rejection. A response
is available one module-local cycle after acceptance and remains stable until
consumed. Before the controlled CPU slice, the static Graph region was
connected through disjoint input and private-output logical regions in one
physical instance: two full runs each
accepted 1,280 execution reads and 256 execution writes, matched all 512
host-oracle outputs in total, and passed
cancel/drain/restart. Those legacy records leave CPU controls unconnected and
resource matching false. The later ADR-0046 strict records supersede only that
open resource-connection status; fixed end-to-end CPU latency is still not a
T-0042 claim.

ADR-0025 implements one OS/ISA-neutral owned `GraphProgram` and
`ExecutionContract` for bounded GEMM and GEMM+bias+ReLU graphs. A fixed
structural compiler emits a unique baseline-first slate; an analytical adviser
either proposes an admitted variant or abstains. The executor always runs and
semantically validates the trusted baseline first, compares a proposed result
against both its reference checksum and the baseline, and then records explicit
commit or rollback. Invalid baselines fail closed.

The `graph-mvp` CLI compiles the existing native-C adapter with strict C11,
executes the vertical slice, and exclusively creates a segregated
`raveil.graph-mvp-result/v1` JSON result. The result is host-correctness
evidence, not Experience, MeasurementRecord, completion telemetry, silicon
performance, or energy evidence.

T-0090 makes backend choice explicit. `native` remains the default.
`sonatine-qemu` accepts one bounded GEMM of at most 8x8x8 through a versioned
128-byte pointer-free request loaded into the fixed QEMU RAM contract. Sonatine
validates it, reuses JobDescriptor, ObjectManifest, rings, CompletionRecord,
approval, and metadata finalization, then emits one request-bound result frame.
The host rejects missing, duplicate, stale, malformed, unknown, unapproved,
timeout, or nonzero-exit results. Its evidence class is fixed to
`qemu-emulation-correctness`, and latency is deliberately absent.

The verified 8x8 GEMM path runs the trusted baseline, produces the same exact
checksum as the native backend, and records explicit adviser abstention. QEMU
`EXECUTED` is not sufficient: semantic validity is exposed only after exact
checksum agreement plus Sonatine approval/finalization.

T-0041 now gives `GraphVariant`, `MemoryPlan`, and `OptimizationProposal`
strict v1 schemas with exact-key deserialization. Variants bind the owned
program and execution-contract identities; proposals additionally bind the
complete ordered candidate set. The executor rejects stale or malformed
lineage before invoking a backend. The bounded host-memory plan remains
descriptive and is not resource-enforcement or performance evidence.

T-0043 makes the named Miroirs and Pavane boundaries executable in the same
OS/ISA-neutral frontend. Miroirs rejects any graph, contract, variant slate, or
proposal that differs from the canonical owned compiler output before a backend
call. Pavane independently regenerates the deterministic `int32` inputs,
executes the bounded `int64` GEMM or GEMM+bias+ReLU reference, computes the
owned FNV-1a checksum, and compares both baseline and candidate observations to
that expected value. Backend-supplied `semantic_valid` and reference checksums
cannot approve a self-consistent wrong result. Semantic approval remains
independent of selection timing, so the timing-free Sonatine/QEMU baseline
continues to support explicit abstention.

T-0040 adds the first pinned upstream compiler import under ADR-0032. The
adapter admits only the repository-authored 8x8x8 i32-input/i64-accumulation
GEMM fixture, verifies its strict manifest and SHA-256, checks
`iree-base-compiler` package 3.11.0 and exact compiler revision, bounds the
subprocess and private VMFB, and emits only the existing canonical
`GraphProgram` plus a separate pointer-free `raveil.graph-import/v1`
provenance sidecar. The imported graph then follows the
unchanged Miroirs, baseline-first, Pavane, proposal/abstention, and explicit
commit/rollback path. No MLIR/IREE object or VMFB enters an owned public
contract.

The GNU/Linux arm64 container compiled the real fixture and completed the
native graph demo with explicit abstention and an exact valid baseline. This is
compiler/import and host correctness only. IREE runtime execution, general
MLIR import, optimization quality, latency, energy, FPGA, ASIC, and silicon
remain non-claims.

The native result adapter and Sonatine serial adapter now also reject
non-canonical scalar encodings, wrong JSON types, missing fields, negative
latency, zero cookies, and invalid binding ranges. These checks are correctness
boundaries only and create no performance or hardware claim.

The completed tree passed the full local test suite plus RV64 release/debug,
DWARF, U-mode shell, telemetry replay, and graph differential checks. A Linux arm64 container
also passed the 29 focused graph/backend tests and actual QEMU/native
differential. These are host and emulation correctness results only.

Sixteen focused tests pass on native macOS and in a Debian 12 arm64 GNU/Linux
container. The real Linux smoke ran baseline then candidate and chose rollback
because the candidate did not improve that development run. This is functional
control-loop evidence only. Sonatine and all prior artifacts remain unchanged.

## Executable track A: Sonatine Microkernel RV64 seed

QEMU RISC-V `virt`向けのfreestanding kernel seedがあります。

T-0034 adds an executable Four-plane write firewall under ADR-0030. Program,
Graph, Data, and Experience use distinct capability object types and exact
type/right/owner/generation checks. Fixed boot-scoped registries seal full
Program identities and Program-bound Graph identities. The normal job path
requires Data authority for object registration, submission, and metadata
publication; separate Program authority gates injected semantic approval;
Experience authority admits only a bounded consumed-completion observation.

The public job authority header no longer exposes unguarded registration,
submission, approval, or finalization functions. Host tests exercise all 16
plane-capability/operation combinations, identity mismatch, wrong owner,
attenuated delegation, and revoked-handle denial. QEMU smoke executes the same
guarded path. This is a single-hart volatile kernel policy seed, not physical
plane isolation, persistent authority, per-object least privilege, DMA/IOMMU,
or hardware evidence.

Implemented:

- RV64 machine-mode entry、one hart、fixed 128 MiB memory contract;
- versioned `qemu-virt-rv64-v1` platform contract with pinned QEMU `virt`,
  `rv64` CPU, 128 MiB RAM, one hart, no firmware, and compile/test assertions
  tying the fixed MMIO/RAM assumptions to the launch configuration;
- Sv39 page-table construction with a supervisor-only 128 MiB kernel identity
  map, an explicit non-executable user window, page-walk validation, and an
  aligned `satp` root; current M-mode execution does not yet enforce the maps;
- transient U-mode init/fault probes followed by a persistent scripted U-mode
  shell copied into separate U/R/X code and U/R/W stack pages, with RAM-only
  PMP admission and trusted kernel-stack trap entry through `mscratch`; the
  retained M-mode diagnostic shell is not entered by the normal boot path;
- fail-closed U-mode trap disposition: an illegal-instruction probe and unknown
  syscalls return through trusted kernel-stack control and ABI state to the
  diagnostic kernel instead of resuming or hanging;
- a persistent scripted U-mode shell task with current-task-bound console,
  clock, and scalar endpoint syscalls; no user-provided task/owner identity,
  `CONTROL` operation, kernel pointer, or arbitrary user pointer crosses the
  syscall veneer;
- a line-oriented `raveil-u> ` U-mode command shell with an eight-byte
  task-owned scalar buffer, CR/LF/CRLF handling, empty-line suppression,
  backspace/delete editing, fail-closed overflow recovery, explicit unknown
  command errors, and `help`, `info`, `ticks`, `ipc`, `fs`, and `exit`;
- a T-0092 native operator demo adding `ls`, `cat`, `echo`, `write`, `stat`,
  `jobs`, `run`, `cancel`, and `result`; VFS commands use the real bounded
  nodes, while graph commands require a distinct non-delegable demo capability
  and reuse the bound job/completion, Experience-observation, byte-shadow,
  independent fixed-GEMM semantic comparison, approval, commit, cancellation,
  and rollback seams;
- an exact bounded `RAVEIL-SONATINE-DEMO-V1` frame with monotonic sequence and
  a strict host `sonatine-demo` runner. The runner binds repository revision,
  kernel and input SHA-256, fixed transcript, QEMU/Python versions, every frame,
  final state, semantic result, checksum, and exit status into one exclusively
  published `raveil.sonatine-demo-result/v1` JSON record;
- command state that remains intact across real CLINT preemption without
  passing a line pointer to the kernel; the only added console operation emits
  one seven-bit scalar byte after current-task and capability validation;
- T-0096 correction removes per-preemption UART prose from normal
  operation and treats ETX as an operator request for the same current-task-
  checked shutdown used by `exit`; local and fresh-clone QEMU verification
  passed and v0.0000000000003 is published as a Pre-release;
- non-blocking U-mode console reads that return `WOULD_BLOCK` instead of
  polling in M-mode with interrupts masked; M-origin faults take a distinct
  fail-stop path, and seed shutdown is restricted to the scheduler-registered
  U-mode init task;
- one shared 272-byte M/U trap frame preserving x1-x31, interrupted `sp`,
  `mepc`, and `mstatus`, with `mscratch` bound to the running context's trusted
  kernel-stack top;
- `.bss` initializationと16 KiB boot stack;
- NS16550A polled console;
- 4 KiB bitmap physical-page allocator;
- owner、type、rights、generationを持つ64-entry capability table;
- `init`と`idle`のfixed kernel task records;
- an RV64 callee-saved context frame and independent 4 KiB idle stack, with a
  verified cooperative `init -> idle -> init` round trip;
- CLINT 100 Hz timer-driven preemption that switches `init -> idle -> init`
  from a live U-mode shell to M-mode idle and back to the same user frame;
- a non-reentrant timer-dispatch guard that rejects nested scheduling without
  changing the incoming frame/PC, incrementing the tick, or performing another
  context selection;
- capability-checked four-message IPC endpoint;
- queued IPC blocking/retry state transitions with operation-specific wake-up,
  distinct denied/invalid results, and ready-only task selection;
- `CONTROL`-authorized capability delegation to non-recursive leaf grants with
  nonempty attenuated rights and independent generation-checked revocation;
- kernel-derived smoke evidence for forged, wrong-owner, and send-only receive
  capability rejection, followed by a valid endpoint round trip;
- a two-node VFS with immutable initramfs `/hello`, volatile bounded RamFS
  `/scratch`, filesystem root capabilities, and pointer-free byte I/O from the
  persistent U-mode shell before and after CLINT preemption;
- fail-closed capability generation exhaustion that retires a slot instead of
  wrapping an old handle back into validity;
- CLINT 100 Hz machine timerとinteger register trap frame;
- a retained legacy `raveil>` M-mode diagnostic shell implementation that is
  no longer entered by the normal smoke boot path;
- `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, `reboot` commands;
- release `-Os` build and isolated `DEBUG=1` `-Og -g3` build;
- `make debug` QEMU GDB server and `make gdb` command-line client entry
  points;
- Docker build context exclusion for host artifacts and a clean container
  release build;
- local Gate 0 CI script for host tests, release/debug RV64 builds, DWARF
  inspection, and QEMU smoke. Hosted CI/CD is intentionally not configured。

Not implemented:

- S-mode kernel execution;
- PMP policy;
- persistent scheduling of multiple user contexts;
- persistent multi-user blocking scheduler execution, cancellation, and
  fairness;
- capability derivation trees and cascading revocation;
- device-tree memory discovery;
- real Daphnis Execution Subsystem device, MMIO/DMA/IRQ transport, and
  U-mode-facing submission path.

## Linux driver-development harness

Linux is implemented as a non-authoritative development/transport-validation
host under ADR-0019. The tree contains a Raveil-owned fixed-width v1 PING/NOP
ABI, a pure-C one-inflight contract core, and Linux-only unprivileged
`SOCK_SEQPACKET` daemon/client sources. The daemon uses a mode-0600 socket under
`XDG_RUNTIME_DIR`, accepts one client, verifies `SO_PEERCRED` against its own
UID, rejects partial/version/size/flags/opcode-invalid messages, and copies no
user pointer into the contract.

The protocol core is host-tested. A Debian bookworm arm64 Docker build compiled
the Linux-only daemon/client with GCC 12.2.0 and `-Werror`; a UID/GID 65534
container smoke used a private mode-0700 runtime tmpfs, verified socket mode
0600, completed PING, and verified normal socket cleanup. This is Linux
container correctness, not a kernel driver, real Daphnis device, JobDescriptor,
DMA/MMIO/IRQ path, performance result, Experience writer, or Sonatine
replacement.

## Shared job/completion contracts

ADR-0020 is implemented as a platform-neutral strict-C11 contract and
validator. JobDescriptor v1 is a fixed 320-byte, four-object envelope with
opaque identities, nonzero resource ceilings, generation/version/range/effect
references, and fail-closed reserved/unused slots. CompletionRecord v1 is a
fixed 176-byte observation carrying job ID plus execution epoch, sequence, and
cookie claims; T-0031 must enforce their trusted issuance, equality, and
one-shot consumption. Executed outputs must exactly match WRITE objects and
advance versions.

These validators establish structural correctness only. No executable path yet
resolves descriptor IDs as caller capabilities, commits output, or writes
telemetry to Experience. Linux PING/NOP remains a separate transport envelope.

ADR-0021 implements the kernel-internal T-0031 seed: an exact 64-byte
ObjectManifest v1 validator, fixed eight-entry boot-scoped object table,
four-entry submission and completion rings, and four-entry inflight ledger.
Admission checks ID, generation, visible version, bounds, and permitted effect.
Sonatine issues boot-scoped epoch/sequence/cookie bindings; wrong, stale, or
duplicate completions fail closed and valid completions are consumed once.
Host tests and a QEMU kernel smoke cover the state machine. The rings are
single-hart and kernel-owned; they are not Linux, U-mode, shared-memory, DMA,
MMIO, IRQ, hardware, or performance evidence. `EXECUTED` does not change the
visible object version or commit data.

ADR-0022 implements the T-0032 emulation telemetry seed. After successful
one-shot completion consumption, Sonatine emits one bounded versioned UART
frame with binding, observed status/detail/output versions, and QEMU machine
timer ticks spanning the kernel smoke path from manifest construction through
completion consumption. This is not execution latency. The host CLI ingests
only this frame into a separate mode-0600,
single-writer, hash-chained append-only cold journal with raw-log provenance and
full-history duplicate detection. Source/backend/evidence/platform are fixed to
Sonatine/QEMU/emulation and cannot be overridden by guest data. Re-ingesting the
same source is idempotent.

Completion telemetry is not `ExperienceRecord`, `MeasurementRecord`, semantic
validity, commit evidence, silicon performance, energy evidence, or active
retrieval input. Serial authenticity, crash-spanning exactly-once delivery,
cross-boot uniqueness, and real Daphnis telemetry remain unimplemented.

ADR-0023 implements the T-0033 kernel-owned metadata-shadow lifecycle.
Completion consumption retains the exact binding and descriptor until an
explicit one-shot commit or rollback. `EXECUTED` alone cannot commit; the seed
requires a separate injected kernel approval and revalidates every READ/WRITE
object generation, visible version, and range. All outputs must be exact
successor versions and multi-output publication prevalidates every target
before changing any visible version. Conflicting writers, cancellation, stale
bindings, missing approval, and replay fail closed.

ADR-0031 completes T-0085's bounded byte-shadow seed. Each object owns at most
512 visible bytes; admission snapshots referenced bytes, Data authority stages
only exact consumed-completion WRITE ranges, Program approval requires complete
coverage and freezes the shadow, and finalization publishes bytes with exact-
successor versions only after whole-transaction revalidation. Rollback,
cancellation, conflict, missing approval, and replay preserve visible bytes and
zero the shadow. The QEMU graph path stages its real GEMM output and validates
the checksum again from the committed backing.

This is still a volatile, single-hart, copy-based kernel seed. It provides no
general allocator, real Daphnis device, DMA/cache ordering, persistent recovery,
multi-hart atomicity, U-mode byte API, or hardware evidence. Queued cancellation
discards undispatched state; dispatched cancellation is sticky and a late
`EXECUTED` observation cannot commit.

## Executable track B: bounded Experience seed

Python標準ライブラリだけで、次の閉ループがあります。

- immutable JSONL cold evidence;
- fixed-limit active Experience;
- repeated exact observationのaggregation;
- invalid、negative transfer、strong improvementを優先するtail retention;
- workload/hardware/shape/memory distanceによるnearest retrieval;
- typed candidate ranking;
- trusted baseline first measurement;
- deterministic analytical ToyDaphnis backend;
- cold/warm HCR benchmark。

Gate 1 measurement infrastructure is also implemented:

- versioned BenchmarkManifest, EnvironmentSignature, MeasurementRecord,
  PolicySelection, and PolicyOutcome Python contracts;
- a common `MeasurementBackend.measure(context, candidate)` protocol;
- a committed six-workload powermetrics pilot manifest plus a separate
  24-holdout full manifest separating lineage, shape, working set, and operator
  composition;
- a native C adapter for GEMM, GEMM+bias+ReLU, and two-stage MLP with
  deterministic `int32` inputs, `int64` accumulation, and reference checksum;
- baseline-first, seeded randomized candidate schedules with five repetitions
  for the non-claim pilot and at least 15 for the full experiment;
- a tracked fixed-argument C helper and helper-only non-interactive
  sudo/powermetrics boundary; runtime root-ownership, non-symlink, and
  non-writable-path checks; standalone manifest-aware preflight; a minimum three
  CPU-power samples per measured window; a sampler-readiness barrier that
  excludes exactly its startup observation while preserving later samples
  already buffered in the same read; an explicitly synchronized fake-sampler
  regression that does not infer sample count from elapsed sleep time;
  thermal-stability checks; and same-Mac relative energy calculation;
- an optional, command-recorded between-workload cooldown that idles for a
  configured minimum and requires two consecutive valid thermal preflights;
  measurement-window thermal changes still fail closed and cooldown evidence is
  appended to the run bundle; the same recovery boundary follows backend
  preparation before the first measurement;
- paired-bootstrap, latency/energy HCR, joint NTR, full-history quality-gap,
  active-memory, equal-budget, and retrieval-p95 analysis functions;
- repetition-aware hierarchical-bootstrap sensitivity intervals, per-candidate
  energy-variation and normalized time-block drift diagnostics, plus start/end
  battery, available CPU-frequency, and system-load measurement context;
- fail-closed policy evidence analysis requiring an exact manifest-wide
  cold/bounded/full-history/FIFO/reservoir/random matrix, unique rows, matching
  run/manifest/budget/candidate provenance, preregistration before measurement,
  and summary values recomputed from raw measurements;
- a production policy-plan path that reads a sealed, disjoint-workload source
  run and generates equal-budget cold, full-history, bounded, FIFO, reservoir,
  and random candidate slates; target runs copy the plan before measurement and
  analysis automatically emits slate-bound outcomes;
- a committed 24-workload fixed-C history manifest with distinct IDs, lineage,
  and shapes but the same ten-candidate contract as the target holdouts;
- a target active-memory limit of 64 summary records versus 240 full-history
  records, fixed from source-only simulation before any target measurement;
- per-policy HCR, energy-HCR, coverage, calibration error, NTR, retrieval p95,
  measurement budget, active-memory maximum, and cold-evidence counts;
- `experiment run`, `analyze`, `seal`, and `sync` CLI lifecycle;
- ignored local research bundles with SHA-256/size manifests, immutable sealing,
  rclone immutable copy/download verification, overwrite refusal, and a
  completion marker copied last; mutable writes resolve and remain inside their
  own RUN-ID directory rather than merely the shared artifact root;
- a completed non-claim fixed-C sampler pilot with 90/90 valid semantic and
  measurement records, all nominal thermal samples, minimum power-sample count
  three, and a sealed Google Drive-verified bundle;
- a completed 24-workload fixed-C history-source run with 3,600/3,600 valid
  silicon measurement records, zero checksum mismatches, all nominal thermal
  observations, three-to-fourteen CPU-power samples per window, and a sealed,
  Google Drive-verified bundle;
- a completed first fixed-C target policy run with 3,600/3,600 valid silicon
  measurements and a complete 144-row pre-registered policy matrix; bounded
  retained 64 versus 240 full-history summaries and reduced retrieval p95, but
  its cold-relative median latency and energy improvements were both zero, so
  the Gate improvement and bootstrap criteria did not pass;
- a completed independent fixed-C target rerun with cooldown boundaries,
  3,600/3,600 valid semantic and silicon measurements, all measurement windows
  `Nominal`, a sealed and Google Drive-verified bundle, and the same zero median
  latency/energy improvement conclusion; its joint NTR was 12.5%, so the fixed-C
  Gate hypothesis failed independently;
- a pinned official Apache TVM 0.25.0.post1 / TVM FFI 0.1.12 Apple Silicon
  adapter that lowers the same int32/int64 workload and candidate contracts,
  commits constrained schedules to a MetaSchedule JSON database, queries them
  back before compilation, and passes a 60-kernel semantic/database-reuse smoke;

Not implemented or not yet evidenced:

- real graph IR and equivalence proof;
- a Gate-passing fixed-C policy result;
- system installation and post-`sudo -k` verification of the root-owned
  powermetrics helper and helper-only sudoers rule;
- neural representation、GAN/AAE、ANN;
- cross-hardware learned transfer;
- multi-objective Pareto policy;
- transactional database and distributed Experience。

## Verification status

The original Gate 0 acceptance suite contains nine tests covering the Python
loop, host-executable Sonatine Microkernel task/capability/IPC logic, and the
isolated debug-build contract. The current host acceptance suite contains 152
tests. On 2026-08-12 all 152 passed in 53.363 seconds on macOS with Python
3.14.6; one opt-in real-QEMU integration was skipped. The same
`scripts/ci-local.sh` run completed RV64 release/debug/DWARF builds, normal and
interrupt QEMU smoke, completion replay, Sonatine graph execution, and
native/QEMU semantic checksum differential with exit status 0. The suite now
also checks the Rocket wrapper's executable entrypoints, pin agreement,
immutable environment and volume-name boundary, and functional-only/non-claim
marker. This is implementation and emulation
regression verification, not EXP-0003 or Rocket performance evidence.

On the T-0022 policy-integrity worktree, `scripts/ci-local.sh` passed with exit
status 0: all 40 host tests, clean RV64 release/debug builds, DWARF checks, and
QEMU smoke. The ignored emulation smoke-log SHA-256 was
`314c185549dfd5e11e48f467320ac871e3862960bdb4d02d40ba86c909c0475f`.

On the sampler-readiness-corrected 2026-08-08 Gate 1 pilot worktree,
`scripts/ci-local.sh` passed: all 33 host tests, clean RV64 release/debug builds,
DWARF checks, and QEMU smoke completed with exit status 0. The QEMU portion is
emulation regression evidence only.

On the T-0068 least-privilege-helper worktree, `scripts/ci-local.sh` passed with
exit status 0: all 38 host tests, clean RV64 release/debug builds, DWARF checks,
and QEMU smoke. The ignored emulation smoke-log SHA-256 was
`c222caea0fdc41b0b3992a7772ddde6db99e2a693d915afff36283ffa73e018b`.

The artifact-creating environment did not contain QEMU or a RISC-V cross
compiler. On 2026-08-08, a user-operated Apple Silicon/Homebrew environment
successfully produced `sonatine/build/sonatine.elf` with the
`riscv64-elf-` toolchain. `file` identified it as a 64-bit RISC-V ELF, and
`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain` symbols.

On 2026-08-08 the native Homebrew path performed a clean release build, a
separate debug build, release QEMU smoke, and command-line GDB verification.
The release ELF contains no DWARF debug sections. The debug ELF contains
`.debug_info` and `.debug_line`; GDB 17.2 connected to QEMU 11.0.3,
installed a `kmain` breakpoint, and stopped at `src/kernel.c:25` with source
lines available.

Exact commands, tool versions, Git base revision, console output, and ignored
raw-log hashes are recorded in `EXP-0002`. A clean no-cache Docker build and
Docker-contained QEMU smoke also passed. Public commit `3347087` was then
cloned into a fresh directory: all nine tests, release and debug builds, DWARF
checks, and QEMU smoke passed. The same checks pass through
`scripts/ci-local.sh`. A GitHub Actions workflow briefly ran once during Gate 0
work before the local-only policy was clarified; it was then removed, and no
hosted CI/CD remains configured. A public-tree scan found no generated
evidence, build output, IDE state, credentials, or machine-local absolute
paths. Gate 0 is complete.

The installed IntelliJ 2026.2 C/C++ plugin exposes `Remote Debug`
(`CLion_Remote`) for attaching to an existing QEMU GDB stub. The configuration
type and required fields were inspected, but no claim of a completed
IDE-driven attach is made.

## Non-claims

- ToyDaphnis cycle values are analytical scaffolding, not accelerator performance.
- QEMU correctness would not establish FPGA/ASIC timing or isolation security.
- The Four-plane architecture, Rust/C++ split, Miroirs Graph Compiler, Pavane Semantic Oracle,
  Boléro Experience Runtime, Ondine Object Memory Subsystem, La Valse Optimization Subsystem,
  Scarbo Verification Subsystem, and native Daphnis Execution Subsystem are intended architecture, not all present
  in this minimal tree.
- No claim of removing general-purpose OoO hardware has been demonstrated.
- No Gate 1 latency or energy improvement is claimed. Independent fixed-C and
  pinned TVM target executions both produced zero median latency and energy
  improvement and exceeded the joint NTR limit. Their sealed bundles were
  immutably copied to Google Drive and download-verified. Gate 1 is closed as a
  falsified preregistered 5% hypothesis; the measurement system remains a
  maintenance-mode verification facility. Sonatine Gate 2 is complete on QEMU
  emulation evidence; this is not physical-hardware isolation evidence.
