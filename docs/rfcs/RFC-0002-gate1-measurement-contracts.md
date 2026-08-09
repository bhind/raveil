# RFC-0002: Gate 1 measurement and policy-outcome contracts

Status: Proposed
Date: 2026-08-08

## Problem

Gate 1 needs replayable native and TVM measurements without leaking backend
types into Raveil, allowing oracle results into online selection, or confusing
estimated Apple energy with Daphnis performance.

## Proposed design

Five JSON contracts are versioned independently:

- `raveil.benchmark-manifest/v1`: experiment/backend/evidence identity, explicit
  `pilot` or `full` stage, compiler source and flags, repetition/warm-up/
  randomization/timeout/budget, energy contract including minimum sample count,
  candidates, and pre-registered holdouts;
- `raveil.environment-signature/v1`: Git SHA, OS/machine/CPU, Python/compiler,
  tool versions, and evidence class without hostname, username, serial, or
  credentials;
- `raveil.measurement-record/v1`: run/sequence/workload/candidate/repetition,
  baseline-first or randomized phase, latency, estimated CPU power and energy,
  reference/candidate checksum, power-sample count, thermal state, validity, and
  failure;
- `raveil.policy-selection/v2`: oracle-free, pre-measurement policy/workload/
  candidate slate bound to experiment, manifest SHA-256, registration time,
  measurement budget, source RUN-ID and sealed-bundle SHA-256, source-evidence
  cutoff, retrieval cost, evidence size, prediction, and abstention;
- `raveil.policy-outcome/v1`: run-bound baseline/selected/offline-oracle latency
  and energy, equal measurement budget, retrieval latency, and memory/evidence
  sizes.

`MeasurementBackend.measure(context, candidate)` is the owned interface.
ToyDaphnis remains analytical. Native C and pinned TVM adapters return measured
records. QEMU can connect at Gate 3 only with `emulation` classification.

The CLI lifecycle is:

```text
experiment run --manifest PATH
experiment plan --manifest TARGET --source-run RUN_ID --output PLAN.jsonl
experiment run --manifest TARGET --policy-selections PLAN.jsonl
experiment analyze --run RUN_ID
experiment seal --run RUN_ID
experiment sync --run RUN_ID
```

Run requires a clean Git worktree, copies the benchmark source into the local
bundle, measures each workload's trusted baseline first, then uses a seeded
random order. A pilot has at least three repetitions and three workloads and
must cover all three workload families; it cannot produce a Gate conclusion. A
full manifest has at least 15 repetitions and 20 holdouts. Analysis consumes
only pre-registered policy selections; exhaustive candidates are offline oracle
evidence and never online policy input. Gate analysis requires exactly one
selection and outcome for every manifest workload under each required policy,
rejects late or mismatched provenance, and recomputes all outcome metrics from
the raw measurement matrix.

The source run used by `experiment plan` must be sealed, use the same backend,
evidence class, and candidate set, and have workload IDs disjoint from the
target. Each policy plan contains the trusted baseline plus a fixed proposal
slate equal to the manifest budget. Analysis chooses the joint latency/energy
winner only inside that slate; exhaustive results remain offline oracle data.
Cold, full-history, bounded tail retention, FIFO, reservoir, and random
retention use the same budget.

After the one-time ADR-0010 setup, Raveil invokes only
`sudo -n /usr/local/libexec/raveil-powermetrics`; no interactive ticket is
required. The root-owned helper constrains sample rate/count and fixes the
sampler/output arguments. `experiment preflight --manifest PATH` performs a
one-sample CPU-power/thermal check without creating a bundle. Each actual
window requires the manifest's minimum sample count, and the full experiment
CLI never runs as root. Each sampler process must emit a valid readiness
observation before the benchmark starts; that startup observation is preserved
in raw telemetry but excluded from the measurement-window power aggregate.

Sealing creates per-file SHA-256 and size records plus a bundle hash. Sync
refuses an already completed remote bundle, but may resume an incomplete copy
without overwriting existing files. It copies immutably, verifies downloaded
content and size, uploads the completion marker last, and reads it back.

Seal runs locally as soon as analysis finishes. Remote sync is manual and
milestone-driven: successful pilot, accepted full dataset, independent rerun,
and selected non-duplicate failure evidence. Redundant retries may remain in a
local sealed queue and be transferred in a batch before stage closeout; they
remain incomplete until their remote checks pass. As verified on 2026-08-08,
standard Drive API use has no additional API charge, but files consume account
storage and Google has announced possible quota-overage charging later in 2026.
Review the current official
[Drive API usage limits](https://developers.google.com/workspace/drive/api/guides/limits)
and [Google storage rules](https://support.google.com/drive/answer/9312312)
before any large-data stage.

## Alternatives

- TVM first: rejected for the first boundary because compiler/search/runtime
  variability would obscure measurement-contract defects.
- Git LFS for raw evidence: rejected; raw runs are not repository authority.
- Drive as online Experience: rejected; remote durability must not enter the
  selection hot path or authority boundary.
- process energy-impact number: not the registered metric; Gate 1 uses the SoC
  CPU power estimate and wall time for same-Mac relative comparison.

## Safety and authority boundaries

Baseline-first, checksum equality, equal budget, no oracle leakage, bounded
memory, thermal stability, immutable remote copy, and credential/path scans
fail closed. Missing, duplicate, unknown, or mismatched selection/outcome rows
also fail closed. Experience remains advice. Sealed data is never repaired in
place. See ADR-0012.

## Experiments required

EXP-0003 must run fixed C and then pinned TVM on the same 24 holdouts, repeat
independently, and apply the Gate 1 latency/energy/bootstrap/NTR/retrieval
criteria. A native/TVM conclusion conflict requires research review.

## Open questions

- Which exact official `apache-tvm` build/version is reproducible on the Gate 1
  Apple Silicon environment?
- How should pre-registered bounded/full-history selection plans be produced
  without incorporating target oracle results?
- Do the calibrated roughly 400 ms measurement windows produce at least three
  stable samples for all pilot candidates before the full run?
