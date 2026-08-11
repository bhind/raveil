# Failure knowledge

Status: reusable operational guidance
Last updated: 2026-08-11

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

## Promotion checklist

At milestone review, promote a lesson here when all are true:

- the behavior was observed or the rejected path is recorded;
- repeating it would waste meaningful time or threaten correctness/evidence;
- the prevention or detection advice is specific;
- an authoritative code, test, T-ID, ADR, EXP, or log locator exists.

Do not add generic advice, unverified folklore, secrets, personal data, exploit
details, or copied third-party text.
