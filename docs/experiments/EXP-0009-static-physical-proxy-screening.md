# EXP-0009: Static Graph physical-proxy screening

Status: In progress
Evidence class: synthesis-toolchain commissioning; synthesis-collector failure; candidate-independent collector probes
Date: 2026-08-15
Task: T-0044
Authority: RFC-0005, ADR-0039, ADR-0043, ADR-0046, ADR-0047, ADR-0048, EXP-0008

## Question and scope

After EXP-0008's latency/traffic survival, can the static Graph candidate pass
the smallest honest same-library area/timing screen against Rocket without
hiding fallback, common memory, integration, or tool uncertainty?

Stage A commissions only the synthesis toolchain with repository-owned toy RTL.
It creates no Graph, Rocket, or BOOM result. Stage B may collect the separately
frozen static Graph/Rocket partitioned area/timing matrix. Dynamic energy,
static power, placement, routing, physical memory, BOOM physical comparison,
other Graph organizations, FPGA, and silicon remain out of scope for this
screening and cannot be inferred from it.

## Accepted boundary

ADR-0048 fixes Rocket as the fallback and area denominator. The Graph side must
report both its complete candidate-local incremental logic and the analytical
logic composition `Rocket fallback + Graph incremental`. The common fixture
provider and common owned scratchpad or identical abstract memory are separate
partitions. No Graph-only island number is a whole-system result.

The same emitted-RTL lowering policy, Sky130 HD typical Liberty, 20.000 ns
clock, synthesis commands, timing commands, black-box policy, and report parser
apply to Graph and Rocket. Stage B is ineligible if the generated RTL cannot be
closed, a partition is missing, memories differ, clocks or libraries drift,
unresolved cells remain, reports are incomplete, or the worktree/source/config
identity is stale.

Synthesis is deterministic for one source/tool/configuration coordinate.
Identical reruns are reproducibility checks, not independent samples; area and
timing are reported as exact tool observations with no fabricated confidence
interval. The RFC-0005 64-fresh-input and 95% interval rule remains reserved
for a later complete dynamic-energy proxy.

Decision rules for this screen are frozen as follows:

- `early-no-go-area` only if complete Graph incremental mapped area divided by
  complete matched Rocket-core mapped area is greater than 0.25;
- `early-no-go-timing` only if Graph misses the 20.000 ns constraint while
  Rocket meets it under the exact same complete flow;
- `advance-to-integrated-physical` if both partitions are complete, both meet
  timing, and the incremental-area ratio is at most 0.25; and
- `pause-boundary` for any incomplete/ambiguous partition, shared-resource
  mismatch, both-candidate timing failure, or identity/tool/report failure.

No outcome from this stage is RFC-0005 go.

## Stage A toolchain commissioning

The owned toy path pins:

- linux/amd64 base image
  `mambaorg/micromamba:1.4.2@sha256:efb0733f0f06f78e79eb21a5795a6fb2eb6c91b8fc534329f692b685140fc8ad`;
- Yosys `0.27_4_gb58664d44`;
- OpenROAD package `2.0_7070_g0264023b6`, using its standalone OpenSTA 2.3.3
  engine for post-synthesis timing;
- Open PDKs Sky130A `1.0.457_0_g32e8f23`;
- `sky130_fd_sc_hd__tt_025C_1v80.lib`; and
- a 20.000 ns clock with 1.000 ns input/output delays.

The first successful provenance-disabled image and two cached reruns report
the same image ID
`7a0db885c100695626175931d3e053ba6a1602d949167b83e2ef60888eea7169`,
size 2,178,077,591 bytes, Yosys binary
`a078aea6eafafcfe9ed4b1d343acdc612f74ad078efb7b930ed1333968ce7508`,
OpenSTA binary
`3f804b33123a68858cf668a1d2253af865e056413d92403351cd5343996e514f`,
Liberty
`e66aab4e0a3eef8d0b13eb5b75aaadb725ba78b032203342eb1e419a2c111baf`,
Conda environment
`ddcfd6e7c9f580feb5f236cce3294087a9db842c95c604239cf2506ecfc974ee`,
and system-package identity
`8cce2c230bf60e1da1fb177051c99448c00af28b42fcca10fdef6a2950dfdf1f`.
The toy mapped netlist is stable at
`81aa811303fdfa1f1d8cca46ba0dad3f065dfe437d6e42d7b5740b2ff8ac5a09`.

The cold build exposed and retained three commissioning-only operational
failures before success: the classic Conda solver stalled, isolated micromamba
needed explicit OpenMP and GL runtimes, and OpenROAD required a technology
database while standalone OpenSTA did not. No candidate RTL was synthesized,
no performance datum was collected, and every failed attempt exited nonzero.

Exact commissioning command:

```sh
./hardware/chisel/run-physical-proxy-toolchain-smoke.sh
```

Initial implementation/freeze/Stage-B estimate is 2--5 working days, with a
further 2--6 working days for a later 64-input energy proxy only after a valid
whole-system boundary exists. Confidence is medium for Stage B and low for the
later energy work because generated CPU RTL closure, memory abstraction, and
fallback activity are not yet proven. The successful cached end-to-end toy run
takes about five operational seconds; simulator or host wall-clock is never a
CPU performance fact.

## Stage-B frozen pre-data state

No Stage-B candidate synthesis data exists. Implementation authority
`f487259fbadc5dc35548c15d7c8967b7065cd466` descends from the commissioned
toolchain and owns the exporters, runner, seals, parser, matrix derivation, and
tests. The frozen manifest is
`benchmarks/manifests/t0044-static-physical-screen-v1.json`, SHA-256
`681fd43e6f38a4b65cba8698eacbbf3768edc93d633141274c74ce846d61d216`.
Freeze commit is `d44c2e603ade69ceccb14ac0db2a77374d47ab7b`; all
candidate RUN-IDs must be descendants of both that commit and the implementation
authority.

The implemented but not yet frozen collector has four explicit boundaries:

- Graph and Rocket exporters write generated RTL into new paths and report
  source/configuration, generator-image, and complete RTL-tree identities;
- the candidate runner obtains top and black-box policy only from the frozen
  manifest, verifies a clean descendant checkout and the exact synthesis image,
  and retains any nonzero container run as sealed ineligible failure evidence;
- successful raw evidence includes the exact read-file list, black-box list,
  Yosys script, SDC, OpenSTA script, mapped netlist, structured Yosys statistics,
  runtime binary/Liberty hashes, logs, and run metadata under one append-once
  seal; and
- derived partition and matrix reports live outside raw evidence, reject any
  seal/manifest/RTL/top/tool/clock/report mismatch, and always keep energy and
  whole-system claims false.

The pre-authority verification command
`python3 -m unittest tests.test_t0044_physical_proxy -v` passes nine tests,
including raw mutation, top/black-box drift, contradictory timing status, and
fallback-composition negatives. Shell syntax, Python byte-compilation, and
`git diff --check` also pass. These are implementation tests, not candidate
measurements.

The first Rocket RTL-only export commissioning attempts exited nonzero before
copying generated RTL. The dedicated worktree needed explicit read-only
Chipyard and Rocket-Chip locators, and then exposed a malformed shell
assignment in the new exporter. No synthesis tool ran and no candidate report
or performance datum was created. The assignment is corrected with a literal
source-directory regression assertion; the corrected commit supersedes the
earlier Stage-B implementation commit as authority.

A later successful copy attempt exposed a second pre-freeze issue: copying the
whole Chipyard generated-source directory admitted Verilator objects and other
build collateral (993 files, about 358 MB) rather than only synthesis RTL. That
export is rejected and will not enter the manifest. The corrected exporter
accepts only the exact `.sv`/`.v` entries in Chipyard's generated `.top.f`,
flattens them into a collision-checked directory, and separately hashes the RTL
tree and normalized file list. It records the stable generator RootFS-layer
identity rather than the provenance-bearing local image-manifest ID.

The first canonical-copy commissioning then failed closed because the `.top.f`
locator was one directory too high. Read-only volume inspection found the file
inside the configuration-specific generated-source directory; the locator is
corrected before any canonical export or synthesis.

The accepted frozen inputs are:

- static Graph top `StaticStencilRegion`, generated-RTL SHA-256
  `b7ee40467b904c0dfd3bf252de0312d60315bdd114f17fe367653d591d07778f`,
  with `OwnedFixedLatencyScratchpad` and `RaveilFixtureInputProvider` as the
  explicit common partitions excluded by black-box, while Rocket excludes
  them at its core top boundary;
- Rocket denominator top `Rocket`, 376 `.top.f` RTL files, generated-RTL
  SHA-256
  `d98d3a7802d0ba1f99e4e3affab27c5ac66b306720563de507af079268791599`,
  with caches, common owned memory, and integration disclosed outside this
  core-logic denominator; and
- the same pinned synthesis image, Sky130 HD typical Liberty, `clock` port,
  20.000 ns period, and 1.000 ns input/output delays for both partitions.

Clean-checkout collection commands, each using a new RUN-ID directory, are:

```sh
./hardware/chisel/run-physical-proxy-synthesis.sh \
  benchmarks/manifests/t0044-static-physical-screen-v1.json static-graph \
  <graph-rtl-dir> <new-graph-raw-dir> <new-graph-derived-dir>
./hardware/chisel/run-physical-proxy-synthesis.sh \
  benchmarks/manifests/t0044-static-physical-screen-v1.json rocket-in-order \
  <rocket-rtl-dir> <new-rocket-raw-dir> <new-rocket-derived-dir>
python3 -m raveil.t0044_physical derive-matrix \
  --manifest benchmarks/manifests/t0044-static-physical-screen-v1.json \
  --graph-result <graph-derived-dir>/result.json \
  --rocket-result <rocket-derived-dir>/result.json \
  --derived-dir <new-matrix-derived-dir>
```

Any failed raw directory is retained and never reused. A deterministic rerun
uses a distinct RUN-ID and is only a reproducibility check.

## First Stage-B attempt and recovery boundary

The first frozen Graph RUN-ID exited before Yosys because the host opened
`container.log` before container launch while the container required a wholly
empty raw directory. The runner retained `run-001-static-graph-raw` as an
ineligible failed seal; its files digest is
`080f3ac93706ff88a6df90c04b52d09992e24ad1c26b2a57a6fd859867edb6f3`.
No RTL was read by Yosys, no area/timing report exists, and no candidate datum
may be recovered from that RUN-ID.

Recovery changes only that handoff: the container now requires exactly one
empty, host-owned `container.log` and rejects every other preexisting entry.
The original manifest remains immutable. A separately frozen recovery manifest
must bind the corrective implementation authority before a new RUN-ID; all
RTL, partitions, tools, constraints, estimators, and decision rules remain
unchanged.

Recovery implementation authority is
`b6c3125f70dcd4f08343a961c8557088bae30e94`. Recovery manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v1.json`, SHA-256
`14f5786f146543d3cf8035e9c4c1b561ed025789144fa3ad4e0b35a193a35786`,
binds the original manifest hash and changes only the log handoff. Candidate
reattempts are authorized only from recovery freeze commit
`64ffcc498c49ff30c7e282efbbe66616270adb39` or its clean descendants.

The recovery Graph RUN-ID passed the log handoff but stopped in Yosys parsing
at CIRCT-emitted block-local `automatic logic`. Failed raw files are sealed at
`dcda0e56c135b72be5d194680df2d0fe201a3ba2cc4a5d34037ac499c48094ec`;
no mapped area or timing report exists. The pinned Yosys 0.27 coordinate does
not accept that Chisel 7 output form.

A second recovery may add a physical-export-only CIRCT lowering mode with
`disallowLocalVariables,disallowPackedArrays`. The runtime emitter and design
semantics remain unchanged. Because emitted RTL bytes and lowering identity do
change, this is not covered by either prior manifest: the new source and RTL
must be committed, exported, hash-bound, and frozen before another candidate
RUN-ID. If that exact lowering still cannot close the complete Graph/Rocket
matrix, EXP-0009 pauses at the generated-RTL boundary rather than weakening the
tool or silently rewriting reports.

Recovery-v2 implementation authority is
`cba62261484d2946b9e3bcc39f05763408f7e6bf`. Its clean RTL-only export has
source SHA-256 `eebf3176...27c8`, generator image ID `c0d90df9...14ce9`, and
lowered Graph RTL SHA-256 `e95e2e02b0e3c0460596c89b6dd324e7135208e0e1a097dcd689fdbef2f5a41d`.
No `automatic` local or packed-array declaration remains. Recovery-v2 manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v2.json`, SHA-256
`293d83bfb884b7e0b3b8d7416f4438aa8be2968be1bfb109b801bd514b411c04`,
binds those bytes and the unchanged Rocket/tool/decision contract. Candidate
use is authorized only from recovery-v2 freeze commit
`ba8ee88863750be9137bd519af0102ed0560cbb5` or a clean descendant.

The lowered Graph RUN-ID parsed all RTL, then stopped before synthesis because
an initial `hierarchy -top` pruned the common modules before the frozen
black-box existence assertions. Failed raw digest is
`b4ed5c06050a1df8c3561cfab5590f1bd194ddfe90dcecd6e403ce7fe1056c3d`;
there is still no area/timing result. A final bounded collector recovery orders
the same operations as `read -> assert/blackbox -> hierarchy -check`; it changes
neither admitted modules nor the black-box list. It requires another exact
authority/manifest/RUN-ID. Failure after that ordering fix pauses the physical
screen rather than opening another implementation loop.

Final bounded recovery authority is
`daa984f1e9f5aa350b79862977f189ac3aab226d`. Recovery-v3 manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v3.json`, SHA-256
`efe1ec48a99c08766f4866d94179f160f3ca1f334161c06a63deefc8bf1806ed`,
binds recovery-v2 and changes only the Yosys black-box/hierarchy ordering. It
retains every RTL, partition, tool, clock, report, and decision field.
Recovery-v3 freeze commit is `c238c9631f7e248960a2fa421e513764c60dcadd`.

## Result and disposition

The final bounded Graph RUN-ID again parsed all three RTL modules, but Yosys
0.27 selected zero modules for `m:OwnedFixedLatencyScratchpad`; the frozen
common-partition black-box could not be established. It exited 1 before
synthesis and sealed files digest
`f203b7c8ab4130ecb78ea25cdb1726241834dc21f3c7a01ce27f0dbf0587aed9`
and failed-seal SHA-256
`c0178010cf01af04f7f3c63d8e7530788ded0d86c13cf6561d9437104b690382`.
Rocket candidate synthesis was not started because the primary matrix was
already incomplete.

The machine-readable derived pause report is
`artifacts/research/EXP-0009/derived/pause.json`, SHA-256
`340d0d0e30b21d80a74f68d96b9d27887ee4614564364f78d716a03eef9ce700`.
All four failed raw directories and the exact final Graph/Rocket export trees
are retained separately under `artifacts/research/EXP-0009/`.

Disposition is `pause-boundary`, not `early-no-go` and not `advance`. There is
no mapped area, setup slack, critical path, energy, or whole-system candidate
datum, so claim eligibility is false. The single resume condition is to prove
an explicit Yosys-visible common fixture/memory partition boundary before
synthesis without changing the frozen Graph/Rocket semantics or resource
policy. That may be a verified module-selection form or an explicit physical
wrapper; it requires new committed authority and a new frozen manifest rather
than another EXP-0009 recovery loop.

The initial 2--5 working-day Stage-B estimate reached toolchain commissioning,
export, manifests, and the first end-to-end collector attempts, but not the
matrix. Based on the observed parser/partition failures, the narrow resume item
is now estimated at 1--3 working days with medium confidence; Rocket closure
remains unestimated until Graph produces a complete report. This is a range,
not a completion-date promise.

## Resume boundary proof (pre-data)

The user resumed the single paused boundary on 2026-08-15. A read-only probe
against the pinned Yosys 0.27+3 image and the already frozen lowered Graph RTL
proved the correct distinction: `N:<module>` selects the module definition,
while `t:<module>` selects its instance cell. For each common partition the
probe asserts that the named module exists, exactly one instance exists, then
applies `blackbox N:<module>` and verifies the module's `blackbox` attribute
before `hierarchy -check`. This is
candidate-independent collector-boundary evidence, not area or timing data.

The recovery implementation therefore changes only the exact black-box
selection form from the invalid memory-object `m:` pattern to verified named-
module black-boxing, preserves the existing top, RTL, common
partitions, library, constraints, parser, and decision rules, and records
`yosys-module-name-single-instance-v1` in raw tool identity. No wrapper or new ADR
is needed because the accepted ADR-0048 physical/resource boundary is
unchanged. A recovery-v4 manifest must bind the committed authority, preceding
manifest hash, and selection mode before a new Graph RUN-ID. Rocket remains
blocked until Graph produces a complete sealed partition result.

Recovery-v4 implementation authority is
`fe7b9f615c7ad7833fae00165297d0e7fc33c046`. Frozen manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v4.json`, SHA-256
`de396d4f4d4bd81484c5a57b859ac59fdfca84a4cab7cc1a8834d3276c129d31`,
chains recovery-v3 and adds only the verified collector policy. Candidate use
is authorized only from recovery-v4 freeze commit
`caa09835116cce0baadd2a12596b10e2b25fd4c3` or a clean descendant.

The distinct recovery-v4 Graph `run-005` proved the common module boundary and
reached technology mapping, then failed closed at the post-map
`check -assert`: 212 wires were reported as used without a driver. It exited 1
before netlist publication, statistics, or STA. Failed raw files digest is
`74898373a89ee9262ab20c729f322a0c2b14b33f8665224fcbde853b72c16ee3`;
failed-seal SHA-256 is
`7ecf3a4192f38f4fb0b69aa71721168d27c907ddade3616770973eaa4a4d51d1`.
No area or timing datum exists and Rocket remains unrun.

A candidate-independent toy reproduction isolated the failure to the
collector: the post-map check reports 32 equivalent undriven wires when mapped
Sky130 cell definitions have not been loaded and passes after
`read_liberty -lib -ignore_miss_func`. The same library-aware check passes on
the Graph diagnostic path without publishing a report. Diagnostic continuation
also showed that pinned OpenSTA 2.3.3 does not implement
`remove_from_collection` or `report_clocks`; its supported equivalent is a Tcl
`foreach [all_inputs]` plus port-name property test and
`report_clock_properties`. These probes are not candidate data.

The next collector-only authority adds the library-aware integrity check and
the exact supported Tcl equivalents while keeping the 20.000 ns clock, 1.000 ns
non-clock input/output delays, RTL, partition, Liberty, estimator, and decision
rules unchanged. It must be bound in a recovery-v5 manifest before a new Graph
RUN-ID. A wrapper remains unnecessary unless the complete frozen flow later
fails to preserve the explicit cut.

Recovery-v5 implementation authority is
`104c6037fc13da99dbc73f07533488b3cebc7ef2`. Frozen manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v5.json`, SHA-256
`6973030c78c744fe5f59e37b4e7bce38735cc15358a10bd28a3c966fb76d051e`,
chains recovery-v4 and adds only the two collector compatibility identities.
Candidate use is authorized only from recovery-v5 freeze commit
`f1d62e95618d4a2107a1dfe20635098425b8abf5` or a clean descendant.

Recovery-v5 Graph `run-006` completed Yosys, strict mapped checking, and
OpenSTA, then sealed raw evidence before derivation. Derivation failed closed
because the mapped netlist omitted the two intentional common-module
declarations; OpenSTA reported each module `not found` and created an implicit
black box. Raw files digest is
`6df847ecd3c0c5047fad47e9422827add11d4cbd3499db83eadeef1019e435f1`;
raw-seal SHA-256 is
`14847d3fb84d103d222f4eb23d10bdadc5d62c38892ada024c0bd218593ad74c`.
Although sealed raw files contain statistics and an STA path, the frozen parser
correctly rejects the unresolved declarations. They are ineligible and must
not be reused as candidate data; no derived result exists and Rocket remains
unrun.

Pinned-tool diagnostics show that Yosys
`write_verilog -noattr -blackboxes` emits exactly the two declared common-module
stubs. Reading those stubs before the sealed `run-006` mapped core removes both
OpenSTA `not found` warnings and links a single clock path without changing its
logic. The next collector-only authority writes the intentional stubs before
loading standard-cell Liberty definitions, concatenates them with the mapped
core, asserts exactly one declaration per frozen black box, and makes that mode
part of raw identity. This diagnostic is not a candidate result and requires a
recovery-v6 freeze before a distinct Graph RUN-ID.

Recovery-v6 implementation authority is
`d4990d9265e37683a50fe61470e54481384d8cf9`. Frozen manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v6.json`, SHA-256
`135f30d6899742eb769d67c8a8dc6929db105f03e54e284e7e81900acebc398a`,
chains recovery-v5 and adds only the exact mapped black-box declaration mode.
Candidate use is authorized only from recovery-v6 freeze commit
`474c1b5c10fecdef5de0fefc2c5ff7199c22587c` or a clean descendant.

Recovery-v6 Graph `run-007` completed the frozen partition flow. Its sealed
synthesis estimate is 11,851.3664 um2, 1,592 mapped cells, and +11.45991 ns
setup slack at the frozen 20 ns clock. Raw files digest is
`e30beb18ad377c7ee3d1ecb55dacd51e40b7b9a12fc54e2bb57053c80751c072`,
raw-seal SHA-256 is
`634329f49bd253161b046e0707093dca542b001f13445e26399c25514d479fa1`,
and derived-result SHA-256 is
`c778d6fbea328f9cc06bb6b5200c04535948b01e6a3303ae26bd21ae99bf60d1`.
This is an eligible Graph-partition synthesis estimate only. It excludes the
common fixture/memory, Rocket fallback, integration, clock tree, placement,
and routing, and makes no performance, energy, or whole-system claim.

The matching Rocket `run-008` then failed closed during Yosys parsing at
`AXI4UserYanker.sv:255`: pinned Yosys 0.27 rejected a generated
multi-dimensional packed array before synthesis. Files digest is
`4065b750900e92053550fcdbe8b2cd0d70cedc316b8543d43d38566725c1a80c`,
failed-seal SHA-256 is
`639bf2cc414ead6faeeb0400cc6d29dc74c9e29aba811ac3f116a8562d35186d`,
and no Rocket candidate datum exists. The matrix remains incomplete, so
disposition stays `pause-boundary`; Graph `run-007` cannot be combined with a
later manifest.

The pinned Chipyard generator already defines a physical Yosys compatibility
path: `ENABLE_YOSYS_FLOW=1` appends only `disallowPackedArrays` to its canonical
firtool lowering options. The next recovery uses that upstream physical-export
path in a separate Docker volume, leaves the runtime simulator path unchanged,
and fails closed unless the baseline and physical exports have byte-identical
FIRRTL and SFC inputs, build-root-normalized identical annotations, identical
module hierarchies, and identical normalized file-list sets.
It records the common Makefile, firtool, lowering-options, source, cache, RTL,
file-list, and provenance hashes. The same compatibility policy is already
present in the Graph physical emitter. This changes neither ADR-0048's
partition/resource boundary nor the estimator and therefore needs no new ADR,
but it requires committed authority, a chained recovery-v7 manifest, and fresh
Graph and Rocket RUN-IDs before any matrix decision.

The first clean-authority physical build completed under isolated cache key
`bdd35a347a3d57ecf5d00c80c0166236e87090a64f5d0f6bb02103ffc5b515f1`,
but export failed closed because the initial checker compared annotation files
byte-for-byte. Read-only comparison proved their only differences were the two
absolute cache-root paths embedded in hierarchy annotations. FIRRTL, SFC
level/options/FIRRTL, build-root-normalized annotations, and all three module
hierarchy files match; the 376-entry top and 38-entry model file lists have
identical filename sets but generator-dependent order. The checker correction
normalizes only the two exact frozen cache roots and sorts basename-only file
lists while still retaining each physical file-list hash. This operational
recovery publishes no RTL or candidate datum and requires a new committed
authority before another distinct export.

From normalization-recovery authority
`c2842a0deb51046a85798229ea559aae53d1035a`, the distinct `v2` export passed
all shared-provenance gates. Rocket RTL tree SHA-256 is
`641735c13d371aff71f4856bdbb3a7a618d2600484a7f652e2f122c90d786d2f`,
its 376-file list SHA-256 is
`d38af48c22bfbf8a88ca5da9b61c758112afd7d6f625759267a0be9c9011db46`,
and lowering-provenance SHA-256 is
`fd91b3b9f5d4dd807195d809cd34ecaee5939aa1dc04953d84a7c1da6d2620da`.
The tree contains no remaining generated multi-dimensional packed-array
declaration under the frozen inventory pattern. A pinned Yosys 0.27 parse,
checked Rocket hierarchy, and strict pre-synthesis `check -assert` pass over all
376 files. This is compatibility/provenance evidence only, not synthesis data.

The measured operational cost of the first clean-cache generation was about
12 minutes on this host; the cache-bound revalidation/export completed in about
30 seconds. These are workflow observations, not CPU performance evidence or
independent samples. With the parser/manifest identity addition now required,
the remaining narrow freeze plus fresh paired Graph/Rocket physical run is
estimated at 0.5--2 working days with medium confidence, assuming no later
Yosys mapping/STA incompatibility. This is a range, not a completion-date
promise.

Recovery-v7 implementation authority is
`0611b0431cf052fa1e30f1024f664dffbd1bee98`. Frozen manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v7.json`, SHA-256
`5b16529903cc12ef594a5d1177b2620a3ab81da7d64cfdaeda6a7eb050ec1780`,
chains recovery-v6 and binds the shared compatibility-lowering policy, exact
Rocket generator/provenance identities, new Rocket RTL, and unchanged Graph
RTL. It changes no partition, toolchain, Liberty, clock, I/O delay, estimator,
or decision rule. Candidate collection is authorized only from the eventual
recovery-v7 freeze commit or its clean descendants, and both Graph and Rocket
must receive fresh RUN-IDs under this one manifest.

The first v7 command allocated Graph `run-009` but passed the export parent
directory instead of its `generated-src` tree. The actual tree hash was
`961002ee96be9185bbf77179362998320d59de63309124381290119ee79fbeca`,
not the frozen Graph RTL hash. The host detected this only while writing
post-container metadata, after the container had run, and exited 1 before raw
sealing or derivation. No contained value was inspected or admitted. This is
an ineligible host/operator operational failure, not a Graph candidate result.

The incident exposes a collector ordering defect: variant RTL identity was
verified after, not before, candidate synthesis. The correction adds an exact
manifest/authority/variant/tree preflight before raw-directory creation. It
then copies the verified tree to a private temporary snapshot, verifies that
snapshot again, and mounts only the snapshot read-only into Docker. This closes
the preflight-to-mount mutation window. Retrospective sealing is limited to
this exact incident by the v7 manifest hash, expected and actual RTL hashes,
RUN-ID, raw file set, pre-seal file-map digest, and successful container marker;
it cannot authorize another drifted run. This changes no RTL, physical
constraint, estimator, or decision rule, but requires another committed
authority and recovery manifest before a new RUN-ID.

Run-009 was retrospectively sealed only after matching every frozen incident
fingerprint above. Failure-metadata SHA-256 is
`5d242ee63992866611184897f3d9792b3afd500245ed9a3c575c457dd98d7162`;
failed-seal SHA-256 is
`d5b7023972488df52ebcc7aac2db7b1d070ed64a420dbd88e6ed80707d69d2af`.
Its metadata records container exit 0, host exit 1, and
`ineligible-host-operational-failure`; it is historical incident evidence, not
a candidate result.

Recovery-v8 implementation authority is
`50639f08b68bf50ab919e0577a7a3614e9aad938`. Frozen manifest
`benchmarks/manifests/t0044-static-physical-screen-recovery-v8.json`, SHA-256
`3dfb0dd588017ed0722d2610cd1f7a76ad35274f8acb6f4133680f6bc52dd0b1`,
chains v7 and changes only the collector operation to exact preflight plus a
reverified private snapshot. Graph/Rocket RTL, lowering provenance, toolchain,
Liberty, partitions, 20 ns clock, 1 ns I/O delays, estimator, report contract,
stop conditions, and decision rules are byte-equivalent to v7. Both partitions
require new RUN-IDs from the v8 freeze commit or a clean descendant.

Recovery-v8 Graph `run-010` passed both input preflights, container collection,
raw sealing, and derivation. It is a `partition-complete` synthesis estimate of
11,851.3664 um2, 1,592 mapped cells, and +11.45991 ns setup slack at the frozen
20 ns clock. Raw-seal SHA-256 is
`355aaea8b2c717b741ffc321aee97610c3d3d3e73a17d3c9498dd61f0b401e77`;
derived-result SHA-256 is
`5280a4d86d8c9f1a1a9606f91673f4ff3eac1c5a5080b229d93bd4b646500b91`.
It has no performance, energy, or whole-system claim and cannot form a matrix
without the paired Rocket partition.

Rocket `run-011` also passed both input preflights and container collection,
then sealed raw evidence under v8. Raw-seal SHA-256 is
`103dc163a007017939680ccfcc513b66f34d0524ea6fdedd3c17059db9d84580` and
raw file-map SHA-256 is
`935b83dfbbc8c2104abed3540e2cf36f671de9c82c80c166f5dc7e6e52b42097`.
Derivation failed closed before a result because the Yosys log has eight area
rows--one frozen `Rocket` top and seven named submodules--while the checker
required one area row globally. No Rocket datum or matrix is admitted.

The bounded correction filters log area rows to the exact manifest top and
still requires exactly one match; it also rejects simultaneous plain and
escaped stat-top aliases and retains exact log/stat equality. Unrelated module
rows are not candidates and cannot select the result. This is a report parser
correction, not an RTL, tool, estimator, threshold, or physical-contract
change. The measured end-to-end container work was under roughly two minutes
for the pair on this host; with tests, records, freeze, and one fresh paired
rerun, the updated estimate is 0.25--1 working day with medium-high confidence,
assuming no further report-contract failure. Host duration is operational
information only.
