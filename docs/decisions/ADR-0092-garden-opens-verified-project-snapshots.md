# ADR-0092: Garden opens checked project snapshots without execution

Status: Accepted
Date: 2026-09-06
Task: T-0161
Related: ADR-0081, ADR-0087, ADR-0090, ADR-0091

## Decision

Add `project garden RUN_ID` with bounded `--keys` and `--width` navigation.
The project verifies its existing run checksum and artifact manifest, captures
graph.json, receipt.json and the snapshotted descriptor through NativeWorkspace,
binds captured bytes to the manifest, and rechecks the run before display.
Only successful graph-device/rtl-sim records are eligible. Saved output,
descriptor, program, lowering, shape and receipt agreement must be consistent.

Extract the existing strict compiler-owned lowering validator for reuse without
calling the compiler. Garden receives an immutable in-memory project view, not
a newly minted retained-execution envelope. No new on-disk schema is needed.
Existing Garden formats, project runs and execution paths remain unchanged.

Project records are cooperative local data, not authenticated evidence seals.
Label the display Host Functional and the historical oracle/fallback/RTL
agreement as a saved receipt reference. Do not synthesize missing compiler or
provenance identities, follow evidence_directory, access a device, run a
compiler, or rerun a simulator. Checksums detect inconsistent snapshots, not
malicious coordinated rewriting of all records. New independent validation of
the original execution is explicitly not claimed.

## Acceptance

Open existing editable-input runs without modifying them, navigate nodes and
show relative LOAD or modular MUL semantics. Repeated views are deterministic.
Tests forbid execution/compilation, reject failed/non-Graph runs, changed
artifacts and capture races, and preserve legacy Garden behavior. No EXP,
research gate, physical readiness or Sprint ceremony acceptance changes.
