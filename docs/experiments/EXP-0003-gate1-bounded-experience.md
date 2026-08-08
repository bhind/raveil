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
- 24 committed holdouts across GEMM, GEMM+bias+ReLU, and two-stage MLP;
- lineage, shape, working-set, and operator-composition partitions are distinct
  manifest fields.

The committed preregistration is
`benchmarks/manifests/gate1-fixed-c-v1.json`. Inputs are deterministic `int32`;
accumulation and output checks use `int64`. Workload bounds keep arithmetic
within `int64` range.

## Environment

Planned target: one Apple Silicon Mac. Each run records Git SHA, macOS/machine/
CPU identity without user or serial identity, Python/compiler/tool versions,
and evidence class. Official `apache-tvm` will be installed in an isolated,
pinned environment only after the fixed-C pilot stabilizes the contract.

## Procedure

1. Commit the manifest and harness; require a clean worktree.
2. Authenticate in a user-operated terminal with `sudo -v`, then run
   `python3 -m raveil experiment run --manifest
   benchmarks/manifests/gate1-fixed-c-v1.json` with permission to execute
   `/usr/bin/powermetrics`. The runner uses `sudo -n` only for powermetrics and
   creates no RUN-ID directory if privilege/power/thermal preflight fails.
3. Warm each invocation, measure the trusted baseline first per holdout, then
   execute the seeded randomized schedule with at least 15 samples/candidate.
4. Fail closed on timeout, invalid candidate, checksum mismatch, missing power
   or thermal sample, permission denial, or thermal-state change.
5. Pre-register policy selections without target-oracle input; analyze latency,
   energy, HCR, energy-HCR, NTR, coverage, calibration, budget, retrieval p95,
   active memory, and cold evidence.
6. Seal and sync the run; verify remote content before uploading the completion
   marker. Repeat independently with a new RUN-ID.
7. Repeat through the pinned TVM MetaSchedule adapter. Send a contradictory
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

No RUN-ID, sealed bundle hash, or completed remote verification exists yet.
An experiment run is incomplete until remote content/hash/size checks pass and
the completion marker is present.

## Results

No performance or energy result has been collected. Host acceptance tests only
verify schemas, schedule invariants, C reference checksums, statistical
calculation, fail-closed power parsing, and bundle integrity behavior. These are
implementation facts, not hypothesis evidence.

## Interpretation

None yet. The Gate remains open.

## Limitations and next action

The policy-outcome production path, full retention comparison, calibration and
coverage report, isolated TVM implementation, authorized powermetrics pilot,
verified Google Drive sync, and independent rerun remain required. Apple
powermetrics is estimated same-Mac evidence and cannot be extrapolated to
RISC-V, QEMU, Daphnis, FPGA, or another Mac.
