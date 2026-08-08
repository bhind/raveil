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

Environment preflight on 2026-08-08 installed rclone 1.75.0. A repository-
external `gdrive:` OAuth remote is configured, but Google Drive API access for
its OAuth project returned HTTP 403 `SERVICE_DISABLED`; no remote listing or
transfer succeeded. Powermetrics requires interactive sudo authentication, and
the cache is terminal/session specific; the agent process cannot reuse a cache
created in another terminal.

## Procedure

1. Commit the pilot/full manifests and harness; require a clean worktree.
2. Authenticate in the same user-operated terminal with `sudo -v`, then run
   `python3 -m raveil experiment run --manifest
   benchmarks/manifests/gate1-powermetrics-pilot-v1.json` with permission to execute
   `/usr/bin/powermetrics`. The runner uses `sudo -n` only for powermetrics and
   creates no RUN-ID directory if privilege/power/thermal preflight fails.
3. Warm each pilot invocation, measure the trusted baseline first, execute the
   seeded randomized schedule with five repetitions/candidate, and require at
   least three CPU-power samples with stable nominal thermal state in every
   measured window.
4. Analyze, seal, and remotely verify the pilot as sampling-contract evidence;
   do not evaluate policy or make a Gate performance claim from it.
5. Run the 24-holdout full manifest with at least 15 repetitions/candidate.
   Fail closed on timeout, invalid candidate, checksum mismatch, insufficient
   power samples, permission denial, or thermal-state change.
6. Pre-register policy selections without target-oracle input; analyze latency,
   energy, HCR, energy-HCR, NTR, coverage, calibration, budget, retrieval p95,
   active memory, and cold evidence.
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

No RUN-ID, sealed bundle hash, successful remote connection, or completed
remote verification exists yet.
An experiment run is incomplete until remote content/hash/size checks pass and
the completion marker is present.

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

## Interpretation

None yet. The Gate remains open.

## Limitations and next action

Retry the pilot only after the machine returns to the pre-registered `Nominal`
thermal state; do not silently admit `Moderate` measurements into the same
experiment. The calibrated iteration counts derive from a short, unsealed host
calibration and may still be insufficient under different candidate or thermal
behavior.
The policy-outcome production path, full retention comparison, calibration and
coverage report, isolated TVM implementation, authorized powermetrics pilot,
enabled Google Drive API plus verified sync, and independent rerun remain
required. Apple powermetrics is estimated same-Mac evidence and cannot be
extrapolated to RISC-V, QEMU, Daphnis, FPGA, or another Mac.
