# EXP-0010: Common 40 ns physical timing follow-up

Status: Planned
Evidence class: partitioned synthesis estimate
Date: 2026-08-15
Task: T-0044
Authority: RFC-0005, ADR-0048, EXP-0009

## Question and non-reinterpretation rule

EXP-0009 remains completed at `pause-boundary`: static Graph met the frozen
20 ns constraint and Rocket did not. This follow-up does not change, supersede,
or reinterpret that result. It asks one new exploratory question selected only
after EXP-0009 closed: under one fixed common 40.000 ns constraint, do the
unchanged Graph and Rocket partitions both meet while the Graph incremental
area ratio remains at most 0.25?

The target is a single doubled-period follow-up, not a measured critical-path
fit, binary search, parameter sweep, or adaptive stopping rule. No 33 ns or
observed-path-derived target is tested. The 40 ns selection and all rules below
must be committed before any EXP-0010 candidate run.

## Fixed comparison contract

The comparison reuses the exact recovery-v9 identities for:

- static Graph and Rocket generated RTL trees, tops, partitions, configuration,
  source, lowering, and generator provenance;
- pinned linux/amd64 image, Yosys 0.27+3, OpenSTA 2.3.3, Sky130 HD typical
  Liberty, system packages, and binary hashes;
- Graph common-fixture/common-memory black boxes and Rocket zero-black-box
  partition policy;
- synthesis, exact-top report parsing, raw-seal, result, and matrix schemas;
- 1.000 ns input delay and 1.000 ns output delay; and
- area threshold, missing-component disclosures, and claim limits.

Only `clock_period_ns` changes from 20.000 to 40.000. The outer collector reads
all three timing values from the frozen manifest, formats them to three decimal
places, and passes them into the offline container. The inner collector accepts
only the exact `20.000:1.000:1.000` legacy tuple or the new
`40.000:1.000:1.000` tuple. Runtime tool identity and the emitted SDC must agree
with the manifest or derivation fails closed.

ADR-0048 is not superseded: Rocket remains the fallback/area denominator, both
partitions use the same clock/library/flow, and all excluded components remain
excluded. EXP-0010 changes an experiment setting, not the accepted
partition/resource/ownership boundary, so no new ADR is allocated.

## Pre-data manifest and identity requirements

The machine-readable manifest must:

- use experiment ID `EXP-0010` and task `T-0044`;
- bind EXP-0009 recovery-v9 manifest SHA-256
  `d052987747c2a41920e8c1f39152b5a6257092454c9139ed4544bcaa9541fd63`
  through `followup_of_manifest_sha256`;
- bind timing policy `raveil.physical-common-timing-followup/v1`, fixed target
  40.0 ns, selection `one-fixed-doubled-period-no-sweep`, fresh paired runs,
  and no reuse of prior candidate results;
- contain no EXP-0009 `recovery_of_manifest_sha256` lineage;
- bind a full implementation-authority commit and exact recovery-v9
  RTL/tool/resource/report identities; and
- be committed from a clean descendant before either candidate run.

The preregistered fresh evidence paths are:

- Graph raw/derived: `run-014-static-graph-raw` and
  `run-014-static-graph-derived`;
- Rocket raw/derived: `run-015-rocket-in-order-raw` and
  `run-015-rocket-in-order-derived`; and
- matrix: `matrix-exp0010-v1`.

Existing EXP-0009 raw reports, results, mapped values, or matrix cannot enter
the EXP-0010 matrix. Generated RTL may be re-exported or reused only after its
complete frozen tree identity passes both preflight checks; each synthesis and
STA run is fresh.

## Decision and stopping rules

The matrix is complete only when both fresh partitions are manifest-bound,
`partition-complete`, and sealed. Then:

- `early-no-go-area` if Graph incremental area / Rocket area is greater than
  0.25;
- `early-no-go-timing` if Graph misses 40 ns while Rocket meets it;
- `advance-to-integrated-physical` if both meet 40 ns and the area ratio is at
  most 0.25; or
- `pause-boundary` for a Rocket miss, both-candidate miss, incomplete matrix,
  or any identity/resource/tool/report ambiguity.

Any authority, RTL, source/config, toolchain, Liberty, partition, black-box,
clock/I/O, report, seal, or result drift fails closed. There is no second
target, sweep, retry at a different period, or result-guided rule change inside
EXP-0010.

## Claim limits

This is an explicitly data-informed exploratory follow-up to a failed fixed
target. Even `advance-to-integrated-physical` would authorize only the next
integrated physical boundary. It is not RFC-0005 go and provides no
whole-system area, placed/routed timing, performance, energy, static-power,
FPGA, or silicon claim. Common memory, fixture, fallback integration,
cache/interconnect, clock tree, and placement/routing remain missing.

Deterministic synthesis is one exact tool observation; reruns are
reproducibility checks, not independent samples. EXP-0008 remains the separate
RTL latency/traffic evidence authority.

## Estimate

Before EXP-0010 data, implementation review, freeze, fresh paired collection,
derivation, and record closeout are estimated at 0.25--1 working day with
medium-high confidence. The prior paired container work was under roughly two
host minutes, but host duration is operational information only. The main
uncertainty is contract/identity review, not expected tool runtime.
