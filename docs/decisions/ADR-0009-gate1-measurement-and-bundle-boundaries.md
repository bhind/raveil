# ADR-0009: Gate 1 uses measured adapters and immutable research bundles

Status: Accepted
Date: 2026-08-08

## Context

The analytical ToyDaphnis loop cannot support a hardware performance claim.
Gate 1 needs a small honest boundary before framework integration, while raw
measurements must remain replayable without turning Google Drive, an upstream
framework, or Experience into execution authority.

## Decision

Raveil owns the versioned `BenchmarkManifest`, `EnvironmentSignature`,
`MeasurementRecord`, and `PolicyOutcome` contracts described by RFC-0002.
Backends implement the Raveil-owned `measure(context, candidate)` boundary.

Gate 1 stabilizes that contract with a fixed native C benchmark before using an
isolated, pinned official `apache-tvm` MetaSchedule adapter. A trusted baseline
is measured first. Experience proposes candidates only; semantic checks and
target measurement govern evidence. QEMU may later emit the same record shape,
but its evidence class is always `emulation`, never hardware performance.

Native energy evidence uses Apple `powermetrics` CPU power estimates multiplied
by measured wall time. It is valid only for relative comparisons on the same
Mac and run contract. Missing permission, missing samples, or thermal-state
change invalidates the measurement.

Raw runs live under ignored `artifacts/research/<EXP-ID>/<RUN-ID>/`. A sealed
bundle is content-addressed and cannot be amended; another measurement gets a
new RUN-ID. `rclone copy --immutable` transfers the data to
`Raveil/research-data/<EXP-ID>/<RUN-ID>/`, a download-based content check must
pass, and a completion marker is transferred last. Google Drive is a durable
copy, not Git authority or an online retrieval database. Credentials and
machine-local identity remain outside the repository and bundle.

## Consequences

The native harness, TVM, ToyDaphnis, and future QEMU telemetry remain separate
adapters with explicit evidence classes. Remote failure leaves an experiment
incomplete. Gate 1 cannot pass from local summaries, native C alone, or a
single execution; EXP-0003 owns the actual claims and contradictions.
