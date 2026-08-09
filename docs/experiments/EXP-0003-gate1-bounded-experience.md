# EXP-0003: Gate 1 bounded Experience on native C and TVM

Status: In progress
Evidence class: silicon
Date: 2026-08-08

## Falsifiable hypothesis

Under the same target measurement budget on one Apple Silicon Mac, a bounded
Experience policy improves holdout median latency and estimated energy by at
least 5% relative to the cold prior, with both paired-bootstrap 95% lower
bounds above zero, joint NTR at most 5%, and no material loss relative to full
history.

This is falsified or left open if any checksum fails, results do not reproduce,
native C and TVM conclusions conflict, or the immutable remote bundle cannot be
verified.

## Baselines and holdouts

- trusted scalar `ijk` baseline, always measured first;
- cold prior, full-history nearest neighbor, bounded Experience, FIFO, reservoir,
  and random retention comparisons under equal online measurement budgets;
- native candidates: `ijk`, `ikj`, tiles 8/16/32/64, and fused/materialized
  operator variants;
- a six-workload, three-candidate powermetrics pilot that is explicitly
  non-claim evidence;
- 24 committed full-run holdouts across GEMM, GEMM+bias+ReLU, and two-stage
  MLP;
- lineage, shape, working-set, and operator-composition partitions are distinct
  manifest fields.

The committed full preregistration is
`benchmarks/manifests/gate1-fixed-c-v1.json`. The sampling-contract pilot is
`benchmarks/manifests/gate1-powermetrics-pilot-v1.json`; it cannot satisfy Gate
criteria. Inputs are deterministic `int32`; accumulation and output checks use
`int64`. Workload bounds keep arithmetic within `int64` range.

## Environment

Planned target: one Apple Silicon Mac. Each run records Git SHA, macOS/machine/
CPU identity without user or serial identity, Python/compiler/tool versions,
and evidence class. Official `apache-tvm` will be installed in an isolated,
pinned environment only after the fixed-C pilot stabilizes the contract.

Environment preflight on 2026-08-08 installed rclone 1.75.0. The repository-
external `gdrive:` OAuth remote subsequently completed immutable upload and
download-based verification of both the selected failed pilot and successful
pilot. Direct powermetrics still requires superuser authority. ADR-0010 replaces
the terminal-specific interactive sudo cache with a root-owned fixed-argument
helper and helper-only `NOPASSWD` rule; its tracked implementation is verified,
but the machine installation and post-`sudo -k` proof remain T-0068.

## Procedure

1. Commit the pilot/full manifests and harness; require a clean worktree.
2. Install the ADR-0010 helper and helper-only sudoers rule using
   `docs/guides/POWERMETRICS_HELPER.md`. After `sudo -k`, run `python3 -m raveil
   experiment preflight --manifest
   benchmarks/manifests/gate1-powermetrics-pilot-v1.json`. The runner uses
   `sudo -n` only for the fixed helper and creates no RUN-ID directory if the
   installation, authority, power, or thermal preflight fails.
3. Warm each pilot invocation, measure the trusted baseline first, execute the
   seeded randomized schedule with five repetitions/candidate, and require at
   least three CPU-power samples with stable nominal thermal state in every
   measured window.
4. Analyze, seal, and remotely verify the pilot as sampling-contract evidence;
   do not evaluate policy or make a Gate performance claim from it.
5. Run the 24-holdout full manifest with at least 15 repetitions/candidate.
   Fail closed on timeout, invalid candidate, checksum mismatch, insufficient
   power samples, permission denial, or thermal-state change.
6. Run and seal `gate1-fixed-c-history-v1.json`, whose 24 source workloads have
   IDs, lineage, and shapes disjoint from `gate1-fixed-c-v1.json` while sharing
   its candidate contract. Generate an oracle-free
   `PolicySelection` v2 slate for every target workload under cold,
   full-history, bounded, FIFO, reservoir, and random policies. Each slate
   includes the baseline and has exactly the registered measurement budget.
   Copy the plan into the target bundle before measurement. Analysis requires a
   complete, unique matrix, binds it to manifest/candidate/budget/run
   provenance, selects the joint latency/energy winner only within each slate,
   derives offline-oracle values from the exhaustive raw matrix, then reports
   latency, energy, HCR, energy-HCR, NTR, coverage, calibration, budget,
   retrieval p95, active memory, and cold evidence.
7. Seal and sync the run; verify remote content before uploading the completion
   marker. Repeat independently with a new RUN-ID.
8. Repeat through the pinned TVM MetaSchedule adapter. Send a contradictory
   conclusion to research review; do not close Gate 1.

Gate criteria:

- every candidate passes its reference checksum;
- bounded versus cold median latency and energy improvement are each at least
  5%, with paired-bootstrap 95% lower bounds above zero;
- a greater-than-2% regression is negative transfer; joint NTR is at most 5%;
- bounded selection-quality degradation versus full history is at most 2% for
  latency and energy;
- active memory remains within its limit and bounded retrieval p95 is below
  full history on large evidence;
- an independent run reaches the same conclusion.

## Raw evidence

Local logical path:
`artifacts/research/EXP-0003/<RUN-ID>/` (ignored).

Remote logical path:
`Raveil/research-data/EXP-0003/<RUN-ID>/` through a repository-external rclone
configuration.

Failed pilot RUN-ID `20260808T112420Z-af35dd5c0-d6179399` is sealed with bundle
SHA-256 `5c4db3f8b6fadb65cc63a7835bd81d7fde59a55ff6bec20ecd7f8a3d66a4d0c8`
and stored at the registered remote logical path. An independent
`rclone check --download --one-way` reported 0 differences and 12 matching
files; the completion marker readback matched. This completed preservation does
not make the failed pilot a successful experiment.

Successful sampling pilot RUN-ID `20260808T113416Z-643414460-d6179399` is
sealed with bundle SHA-256
`231b83ef176a32e4e86811d756d8a0fe41b94a49a7baa2a955c6f3f09e05980b`.
Its 2,010,279-byte local bundle was copied to the registered remote path;
independent verification reported 0 differences and 100 matching files, with a
completion marker present. An experiment run is incomplete until remote
content/hash/size checks pass and the completion marker is present.

To limit storage and future API-quota cost exposure, local analysis and sealing
remain immediate but sync is milestone-driven. Successful pilot/full/rerun
bundles and selected unique failures sync individually; redundant retries may
queue locally for a later batch and remain incomplete until verified remotely.

## Results

No performance or energy result has been collected. A local native-C
calibration observed individual one-iteration candidate latencies from roughly
18 microseconds to 487 microseconds. This showed that the original measurement
windows were too short for a 100 ms powermetrics sampling interval. The pilot
and full manifests now target roughly 400 ms for the fastest observed candidate
per workload, and actual windows require at least three power samples. This is
sampling-contract calibration, not evidence for the Gate hypothesis.

Host acceptance tests only verify schemas, schedule invariants, C reference
checksums, statistical calculation, fail-closed power parsing, and bundle
integrity behavior. These are implementation facts, not hypothesis evidence.

The clean-tree CLI preflight failed closed before bundle creation when sudo
privilege was unavailable. This verifies a failure boundary only, not a
measurement result.

A subsequent user-operated pilot attempt on 2026-08-08 passed the privilege
boundary but the powermetrics preflight reported thermal level `Moderate`.
The runner rejected it before creating a RUN-ID directory. Repository-side
inspection confirmed that no EXP-0003 run directory exists. This is a verified
thermal failure-boundary observation, not latency or energy evidence.

After the machine returned to `Nominal`, RUN-ID
`20260808T112420Z-af35dd5c0-d6179399` entered the measurement loop. Sequence 1
passed its semantic checksum and captured nine nominal CPU-power samples.
Sequence 2 also passed its semantic checksum but its powermetrics raw file was
zero bytes, so the run failed closed with no energy value. The faster second
candidate completed before the newly launched sampler emitted its first
observation. These partial values diagnose sampler startup behavior only and
must not be used for candidate or Gate performance claims.

The corrected RUN-ID `20260808T113416Z-643414460-d6179399` completed all 90
pilot records. All 90 semantic checksums and measurements were valid, all
thermal observations were `Nominal`, all 90 raw files were non-empty and
contained an explicit readiness/measurement boundary, and no record carried a
failure. Measurement-window power sample counts ranged from 3 to 12 with a
median of 5. Analysis correctly returned `not-applicable-pilot`, no claims, and
a complete matrix; remote verification was the only unmet item before sync.

## Interpretation

The sampler-readiness correction resolved the observed startup failure and the
pilot now supports proceeding to the full fixed-C data stage. This establishes
measurement-contract behavior only; it does not establish latency or energy
improvement, bounded-Experience quality, or Gate 1 success. The failed bundle
remains preserved as boundary evidence and the Gate remains open.

## Limitations and next action

The policy plan/outcome path and per-policy aggregation are implemented, but no
source/target policy dataset or report exists. The full retention comparison,
full fixed-C dataset, isolated TVM implementation, and independent rerun remain
required. Apple powermetrics is estimated same-Mac
evidence and cannot be extrapolated to RISC-V, QEMU, Daphnis, FPGA, or another
Mac.
