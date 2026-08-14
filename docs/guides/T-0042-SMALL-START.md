# T-0042 small-start execution packet

Status: active implementation guide
Date: 2026-08-14
Authority: T-0042, ADR-0041, ADR-0043, ADR-0046, RFC-0005

## Outcome

Produce the smallest replayable RTL-simulation artifact that makes Rocket,
BOOM, and the static Graph candidate eligible for T-0044 under one proved-equal
owned memory boundary. Do not add a performance claim in T-0042.

## Required slice

1. Freeze the exact workload, Graph descriptor, oracle, CPU configurations,
   simulator environment, and input/source/configuration hashes already used by
   the accepted records.
2. Select one existing owned local-memory contract. State its port count, data
   width, maximum outstanding requests, buffering, arbitration, accepted
   operations, and module-local response rule in executable configuration.
3. Connect the smallest Rocket and BOOM execution path and the existing Graph
   path to that same contract. Adapter-specific translation is allowed;
   compared resources are not.
4. Add deterministic quiescence and execution-window markers. Reject the run
   if unattributed setup, loader, FESVR, Debug, recovery, or other traffic
   enters the measured window. Do not claim general instruction identity.
5. Emit strict common records with exact semantic result, all six lifecycle
   phases, complete total cycles, resource equality, traffic conservation, and
   comparison eligibility. Verify them from a clean checkout.

## Stop rules

- Stop and report `inconclusive` if equal-resource connection requires changing
  the frozen workload semantics or the compared core microarchitecture.
- Stop and report `comparison-ineligible` if traffic cannot be isolated or
  completely accounted inside the execution window.
- Stop and request a decision if the common resource requires more ports,
  buffering, outstanding requests, or variable latency than ADR-0043 permits.
- Do not hide adapter, installation, staging, drain, validation, or publication
  cycles to obtain a favorable result.

## Explicitly deferred to T-0106

- additional stripped/malformed-token variants;
- reset/stale/duplicate/exhaustion and multi-live-token state;
- exhaustive replay and source-reuse cases;
- exhaustive post-request exception and post-A rollback cases;
- arbitrary ELF semantic identity and general loader/FESVR/Debug classification;
- complete Rocket/BOOM per-operation lifecycle parity.

Existing diagnostics are retained evidence. Do not delete or reinterpret them.
Do not start a new item from the deferred list while the required slice is
unfinished.

## Closeout evidence

Record exact commands, environment, source and artifact hashes, test exits,
raw-log locators, and evidence class. Reconcile STATUS, TODO, ROADMAP,
OPEN_QUESTIONS, ARCHITECTURE, the applicable ADRs, and the dated log. Passing
T-0042 authorizes T-0044 preparation only; it is not a performance result.

