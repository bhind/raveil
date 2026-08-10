# ADR-0022: Completion telemetry is segregated cold evidence

Status: Accepted
Date: 2026-08-11

## Context

T-0032 must preserve measured completion telemetry without converting an
execution observation into optimization authority. The existing
`ExperienceRecord` requires Context, Candidate, Metrics, and a baseline; the
Gate 1 `MeasurementRecord` requires workload/candidate measurement and semantic
checksum evidence. A Sonatine CompletionRecord establishes none of those.

## Decision

Completion telemetry uses a separate versioned append-only cold journal. It is
never deserialized into the bounded active Experience index and never enters
nearest-neighbour retrieval, policy selection, Gate 1 analysis, commit, or
visibility. `EXECUTED` remains an observed status, not semantic validity,
measurement validity, or approval.

The T-0032 seed accepts only the bounded `RAVEIL-COMPLETION-V1` UART frame
emitted after Sonatine has successfully consumed a completion once. The host
adapter fixes source `sonatine-qemu`, backend `qemu-telemetry`, evidence class
`emulation`, and platform `qemu-virt-rv64-v1`; guest input cannot request
silicon, FPGA, energy, or hardware-performance classification. QEMU machine
timer ticks span the synthetic kernel smoke path from manifest construction
through completion consumption. They are emulation diagnostics, not job or
Daphnis execution latency.

The host supplies run ID, capture time, raw-log SHA-256, and raw line number.
The cookie is retained only as a SHA-256 digest and remains a non-secret binding
value. Each journal event has a canonical event ID, contiguous sequence,
previous-record hash, and record hash. Loading fails closed on corrupt JSON,
unknown or extra fields, partial lines, sequence gaps, duplicate events, or
hash-chain mismatch. Ingestion validates the whole source before opening the
journal, uses a single-writer advisory lock, rejects symlink/non-regular or
multi-link leaf targets, writes mode 0600, appends, and fsyncs.

Serial framing and host files do not provide cryptographic authenticity or
crash-spanning exactly-once delivery. The current design detects duplicate
re-ingestion but a crash between Sonatine consumption and durable host append
can lose an event. Cross-boot epoch uniqueness also remains unresolved.

## Consequences

Failures, cancellation, rejection, and execution observations can be retained
without polluting optimization evidence. A future promotion into active
Experience requires explicit semantic, measurement, commit, and provenance
gates. Real Daphnis, FPGA, or silicon adapters require separate trusted source
contracts and cannot reuse the QEMU classification.

## Verification

Python tests cover strict parsing, high-bit IDs, status/detail and output
validation, oversized/truncated/duplicate frames, idempotent ingestion,
hash-chain corruption, restrictive file mode, symlink rejection, and CLI
inspection. QEMU smoke emits exactly one frame after one-shot consumption,
ingests it, and verifies that a second ingest appends zero records.
