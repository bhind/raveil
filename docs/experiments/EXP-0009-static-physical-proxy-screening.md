# EXP-0009: Static Graph physical-proxy screening

Status: In progress
Evidence class: synthesis-toolchain commissioning; planned synthesis estimate
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
