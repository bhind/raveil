# ADR-0025: Userspace graph MVP keeps advice non-authoritative

Status: Accepted
Date: 2026-08-11

## Context

ADR-0024 selected a GNU/Linux userspace vertical slice as the first complete
product loop. The preserved donor branch contained useful graph/compiler tests,
but it also predated and deleted later Sonatine, contract, telemetry, Experience,
and experiment work. The port therefore needs an owned boundary that can run on
ordinary POSIX hosts without weakening the existing authority model.

## Decision

The T-0086 MVP owns versioned `GraphProgram`, `ExecutionContract`,
`GraphVariant`, `OptimizationProposal`, and result records in Python. Its
native-C backend is a replaceable adapter and does not contribute public types.

Every run validates the graph and contract, admits a unique slate with exactly
one trusted baseline first, and executes that baseline before acting on a
proposal. The analytical predictor may propose one admitted non-baseline
variant or abstain. It cannot select, validate, or commit by itself.

A proposal is commit-eligible only when its execution succeeds, its checksum
and reference checksum agree, its result agrees with the trusted baseline, and
the observed development run is faster. Otherwise the selected state remains
the baseline and the result records abstention, fail-closed behavior, or
rollback explicitly.

The CLI writes a separate `raveil.graph-mvp-result/v1` JSON record using
exclusive creation. It is `host-correctness` evidence and is not an
`ExperienceRecord`, `MeasurementRecord`, policy outcome, completion telemetry
record, or performance claim. Existing Experience may advise future proposal
logic but cannot bypass this flow.

GNU/Linux is the first integration environment. The owned module remains
OS/ISA-neutral and is also tested on macOS. No Sonatine, kernel driver, custom
ISA, FPGA, ASIC, or hardware backend is required by this MVP.

## Consequences

- The donor branch remains unmerged; only reviewed module and test ideas are
  ported onto the T-0087 milestone state.
- Commit in this slice means selecting the validated candidate in the result
  record. It does not publish Sonatine object bytes or versions.
- Single-run host timing is a local control input, not benchmark evidence.
- The fixed graph families and native-C lowering are deliberately narrow;
  compiler expansion remains later work and is not part of T-0086.
- EXP-0003 remains falsified and unchanged.

## Verification

Acceptance requires deterministic host tests for structural rejection,
baseline-first execution, abstention, semantic rollback, slower-candidate
rollback, admitted-candidate commit, failed baseline, unknown proposals, and
non-overwriting evidence. It also requires an actual GNU/Linux container run
through the native-C adapter and the existing repository regression suite.
