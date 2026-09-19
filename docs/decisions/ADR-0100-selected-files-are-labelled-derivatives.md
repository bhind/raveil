# ADR-0100: Selected saved-run files are labelled derivatives

Status: Accepted
Date: 2026-09-19
Task: T-0193

## Context

Owner authorized T-0180's implementation successor. Whole-run snapshots can
include unrelated inputs; copying the directory silently risks disclosure.

## Decision

Provide local read-only `project export-preview` with file names, sizes, hashes,
selection and warnings. No default selection. `project export` requires exact
members, the preview SHA-256 for that selection, and sensitive-data acknowledgement.
Re-admit and capture the source; bind inventory and selection in the preview.
Reject changes, links, invalid paths, collisions and existing output.

Use a bounded JSON/base64 envelope, not tar/zip: no extraction or importer is
introduced. Include only selected payloads and minimal lineage (run ID, original
record hash, preview hash, omitted count). Do not include original full record,
unselected names/content or claim that the derivative is the original run.
Set authenticated=false and replayable_full_run=false even if every file is
explicitly selected. Hashes are cooperative integrity, not signatures.

Limits: 1024 files plus unique parent directories, 16 MiB total source bytes,
24 MiB serialized export. Output must be outside the project, in a non-symlink
parent path; private same-directory temporary file and atomic no-overwrite link
publish the JSON. No upload, execution or Experience-selected members.

This uses the existing cooperative single-writer workspace boundary, not a
hostile concurrent filesystem sandbox. Do not mutate project/output paths during
inspection/export. Metadata itself can be sensitive; acknowledgement is not
automatic redaction. Strong isolation remains T-0100. Weekly Drive policy holds.

## Alternatives

Whole-run archive rejected for disclosure; sanitized original record rejected
because it misrepresents lineage; archive import deferred to avoid extraction
authority. A simple inspectable derivative solves the selected-file use case.
