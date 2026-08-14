# T-0042 small-start execution packet

Status: completed replay guide
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

## Completed slice

The exact replay command is:

```sh
./hardware/chisel/run-controlled-three-way-stencil.sh
```

It executes and strictly aggregates `StaticStencilRegion`,
`chipyard.raveil.RaveilMatchedRocketConfig`, and
`chipyard.raveil.RaveilMatchedSmallBoomConfig`. The canonical controlled-run
contract is
`f95cc6dc896659a32f1407f0f5a8f74ec475d208632f9dd5ff4d43d9cb2f7978`;
the owned resource tuple is
`16664d8ed96865c60ea41c91452b5e6748b055e0dfef3f786b13bd6f90127748`.
The frozen seed-1 input is
`65b00605d894f4a6934862137c751e7f25e7c86a41077f6172cb7142c7ab9254`
and the independent oracle plus all three observed outputs are
`dd749f0f218c7389730bef5b97af4e9203b0501d5ec57fa48ffa643356f23582`.

The integrated replay additionally binds source, built artifact, pinned
toolchain contract, and derived configuration identity for every peer:

| Peer | Source SHA-256 | Artifact SHA-256 | Toolchain SHA-256 | Configuration SHA-256 |
| --- | --- | --- | --- | --- |
| static Graph | `005eeaa6...cee2` | `8af26a8e...7686` | `20093415...7037` | `3ff3df8a...a33b` |
| Rocket in-order | `dac7b3e1...1f6e` | `52175480...8d30` | `ae2488b8...8eee` | `a7899b30...3a16` |
| BOOM OoO | `dac7b3e1...1f6e` | `bd78fc8a...71aa` | `ae2488b8...8eee` | `29659996...3e41` |

The CPU source identity includes the frozen C and assembly workload, linker
script, build/run verifier inputs, overlay/patch set, and pinned source
revisions; the artifact identity is the compiled ELF. The Graph artifact is
the built Verilated executable. The toolchain identities derive from the
pinned Dockerfile/base-image contract, target platform, locked environment,
and exact tool versions rather than a nondeterministic Docker attestation
manifest.

The six phase vectors
`installation/staging/execution/completion/validation/publication` are Graph
`0/648/3072/1/512/0`, Rocket `44630/3865/14621/410/16513/0`, and BOOM
`44761/4208/21892/425/16513/0`; totals are 4,233, 80,039, and 87,799.
All execution windows begin after staging response drain, end after the final
execution response, and report quiescence before/after, pending zero,
unaccounted traffic zero, and accepted equal completed. The aggregate sets
`resource_equality_verified=true` and bounded functional
`comparison_eligible=true`.

Graph admits 1,280 reads and 256 writes while each optimized CPU run admits
800 reads and 256 writes. Therefore the same aggregate explicitly sets
`dynamic_memory_traffic_equal=false`, `t0044_measurement_claim_ready=false`,
`semantic_initiator=not-proven`, and `performance_claim=false`. T-0044 owns any
fairness contract and measurement; T-0106 owns deferred token hardening.

For clean-checkout replay, provide the pinned ignored Chipyard checkout at
`external/chipyard-boom` as described in `hardware/chisel/README.md`, then run
the exact command above. Preserve the final aggregate JSON and raw Docker
volume logs with byte counts and SHA-256 values; do not treat the phase numbers
in this T-0042 functional packet as performance evidence.
