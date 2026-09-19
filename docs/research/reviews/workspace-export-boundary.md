# T-0180: Saved-run export boundary (draft)

Status: In progress, Planning only
Date: 2026-09-19

## Scope

Inspect one existing saved run, then propose a bounded portable format. This
does not implement export/import or authorize extraction or execution.
Reference boundaries: `Project.load_run` validates the record checksum/schema;
`tree` bounds regular-file snapshots to 1024 entries and 16 MiB. Checksums
provide cooperative integrity, not authenticity or an experiment seal.

## Initial proposal, not accepted architecture

- One saved run only; no whole-workspace or home-directory archive.
- Explicit member allowlist derived from the saved record and actual verified
  files. Include record/checksum and required input/output snapshots, not
  external simulator binaries, credentials, unrelated recipes or raw evidence
  outside the run. Missing provenance is labelled, never reconstructed.
- At most 1024 entries and 16 MiB total uncompressed content, aligning with
  existing snapshot bounds. Member counts/bytes/hashes precede any extraction.
- Canonical relative names only: reject absolute paths, parent traversal,
  duplicate names, symlinks, hardlinks, special files and case-fold collisions.
- Inspect without executing. Import, if later approved, uses a fresh isolated
  destination and fails on conflicts; never overwrite or merge existing runs.
- Review the explicit file list for sensitive inputs before sharing. Hashes
  cannot sanitize user data; no automatic public upload is authorized.

## Threats to resolve in the inspection fixture

| Input | Required decision |
|---|---|
| Traversal, links, absolute paths | Reject before extraction |
| Oversized/compressed expansion | Enforce uncompressed byte and entry budgets |
| Duplicate/case-colliding names | Reject rather than choose a winner |
| Sensitive input snapshots | Explicit member review; no default public sharing |
| Malformed or stale schema | Fail closed; no silent migration |
| Missing raw evidence | Label unavailable; do not imply authenticated results |
| Existing destination | Reject conflict; retain existing run unchanged |

## Remaining work

Actual local inspection now exists in
`tests/fixtures/project_export/native-logs-inspection.json`: a freshly initialized
sample ran `logs` on native successfully, independent reference PASS, output
`errors.txt` = `2\n`. `Project.load_run` admitted its record and `tree` generated
the inspected member hashes. Fixture leading slashes are existing workspace
manifest notation, NOT accepted archive absolute paths.

Important observed limitation: even this log-only run snapshots unrelated
sample inputs (bias-grid, neighborhood, left/right) in inputs and workspace.
Blindly archiving the run directory could disclose unrelated user files.
Therefore defer automatic whole-run export. A later proposal must reconcile
selective disclosure with the original record's complete snapshot hashes,
rather than silently removing files and claiming unchanged provenance.

Manifest-only sharing reduces byte exposure but still reveals names/hashes;
a bounded archive enables replay but increases disclosure and extraction risk.
Recommendation: adopt inspection-only preview first, defer archive import until
explicit selective-disclosure and lineage semantics are accepted.

Test the proposed member rules against the retained example, add exact byte
accounting and independent review, then request adopt/defer. No
implementation adoption is implied by this draft.
