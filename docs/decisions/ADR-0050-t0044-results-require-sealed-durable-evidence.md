# ADR-0050: T-0044 results require sealed durable evidence before promotion

Status: Accepted
Date: 2026-08-15

## Context

EXP-0008 completed one frozen 256-fresh-input RTL-simulation campaign for
static Graph, Rocket in-order, BOOM OoO, and diagnostic-only BOOM
serialize-dispatch. Its tracked record identifies the pre-data manifests,
implementation authorities, failed RUN-ID, recovery RUN-ID, exact commands,
derived report SHA-256, raw-seal SHA-256, 256-input oracle result, and nested
1/4/16/64/256 accounts. The bounded result is
`advance-partial-latency-traffic`, not RFC-0005 go.

The raw logs and derived report are intentionally ignored Git artifacts. At
the time of this decision they exist only in machine-local storage; no
immutable remote copy or download-based content verification is recorded.
Conversation tables and tracked summaries cannot replace those bytes. Losing
the local bundle would leave hashes and replay code but remove independent
inspection of the original run.

ADR-0009 already requires immutable research bundles, download verification,
and a completion marker transferred last. T-0044 needs the same promotion
boundary without committing hundreds of megabytes of generated logs to Git or
rerunning deterministic simulation merely to manufacture another sample.

## Decision

T-0044 separates a locally sealed result from a promoted durable research
result.

1. A locally sealed result requires a pre-data machine-readable manifest,
   exact RUN-ID, command/environment/exit records, append-once raw logs,
   separate derived output, and a seal that binds every raw file by relative
   path, byte count, and SHA-256 plus the derived-report SHA-256.
2. The result record must bind implementation, source, configuration,
   artifact, toolchain, contract, resource, input, oracle, and output
   identities. Missing identity is reported as unavailable and cannot be
   imputed from a table or reconstructed after collection.
3. A 256-input repeated campaign must retain per-candidate evidence for every
   ordered fresh input and independently verify all output words. Prefixes 1,
   4, 16, 64, and 256 are derived from the same frozen session using the
   preregistered estimator; they are not separate samples or post-hoc subsets.
4. A failed collection and any bounded recovery remain separate immutable
   RUN-IDs. Recovery must bind the failed seal and every imported raw hash,
   identify exactly which command was rerun, and never relabel imported bytes
   as a new sample.
5. Promotion requires immutable copies of both the retained failed RUN and the
   completed recovery RUN under
   `Raveil/research-data/<EXP-ID>/<RUN-ID>/`. The source seal is verified before
   transfer; `rclone copy --immutable` or an equivalently fail-closed adapter
   transfers bytes; `rclone check --download --one-way` verifies content and
   size; and `completion-marker.json` is uploaded and read back only after the
   content check passes. Credentials, rclone configuration, and machine-local
   absolute paths remain outside the repository and bundle.
6. A tracked promotion receipt records the evidence class, both RUN-IDs,
   remote logical locators, local seal hashes, remote check command and exit
   status, checked file/byte counts, completion-marker hashes, verification
   time, and the Git revision that supplied the verifier. It contains no
   credential, token, host identity, or private absolute path.
7. Decision labels are dimension-scoped. EXP-0008's
   `advance-partial-latency-traffic` permits separately preregistered local
   work on energy, synthesis timing, area, IP disposition, and missing
   organizations. It does not mean RFC-0005 go, T-0044 completion, product
   readiness, FPGA/ASIC/silicon evidence, or an unbounded-workload claim.

## Consequences

EXP-0008 remains valid locally sealed RTL-simulation evidence and may justify
the next reversible T-0044 experiment. It is not called remotely durable or
externally promoted until the receipt above is verified. Remote failure or
missing credentials pauses promotion but does not reinterpret the measured
cycles.

Promotion must not rerun Graph, Rocket, BOOM, or the diagnostic merely because
the remote copy is absent. If either local seal fails, any sealed byte is
missing, or the recovery lineage cannot be verified, stop and retain the
failure. A replacement measurement requires a new EXP/RUN-ID and pre-data
freeze; a summary table must never be used to reconstruct raw evidence.

Raw logs remain ignored generated artifacts. Git retains the manifests,
collector and verifier code, EXP record, hashes, promotion receipt, and exact
replay instructions. Google Drive is durability only and never becomes
execution, measurement, or project authority.
