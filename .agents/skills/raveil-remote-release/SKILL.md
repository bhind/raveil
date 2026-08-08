---
name: raveil-remote-release
description: Audit, prepare, publish, and verify a Raveil Git tag and remote GitHub Release with immutable-tag and cost controls. Use for release readiness, version/tag reconciliation, release notes, remote publication, GitHub Release verification, or changes to the release process. Do not use it to enable hosted CI/CD.
---

# Raveil Remote Release

Treat remote publication as an explicit external mutation. Default to a
read-only readiness audit unless the project owner clearly authorizes the
specific release publication.

## Policy boundary

- Keep CI/CD local. Run `scripts/ci-local.sh`; do not add or trigger GitHub
  Actions, hosted build services, or automatic release workflows.
- Defer remote releases while the repository policy says release publication
  is local-only or postponed. A request to audit or prepare is not permission
  to publish.
- Before publishing, require the owner to approve the exact version/tag,
  target commit, remote repository, release visibility, and expected external
  effects. Resolve ambiguity before writing remote state.
- Never move, overwrite, or delete an existing public tag or Release. If a tag
  already exists at another commit, preserve it as history and choose a new
  version only with owner approval.
- Never expose tokens, credentials, generated evidence, machine-local paths,
  IDE state, or build output.

## Readiness audit

1. Use `raveil-task-governance`. Read `VERSION`, `TODO.md`, `docs/STATUS.md`,
   `docs/ROADMAP.md`, relevant accepted ADRs, the release experiment, and the
   dated log.
2. Inspect `git status`, the target commit, remote URLs, upstream alignment,
   existing tags, and existing remote Releases. Use read-only commands first.
3. Run `scripts/ci-local.sh` from a fresh public clone of the exact candidate
   commit. Record commands, versions, exit statuses, evidence class, and log
   hashes required by the applicable experiment.
4. Scan tracked files and history for generated outputs, secrets, credential
   patterns, `.idea`, build directories, evidence JSONL, and absolute local
   paths. Do not claim public hygiene from an unpushed working tree.
5. Confirm all gate tasks and exit conditions required by the release are
   complete. Keep unsupported hardware, performance, IDE, or deployment claims
   out of the release notes.
6. Return a readiness result with exact target SHA, proposed new tag, open
   blockers, verification evidence, and the remote mutations publication would
   perform.

Stop after the audit if local CI fails, the tree is not reproducible, records
conflict, the candidate is not public, credentials are unavailable, an
existing tag conflicts, or publication approval is incomplete.

## Publication

Only after a passing audit and explicit approval:

1. Commit and push the coherent implementation and same-commit records.
2. Re-fetch and verify the remote branch still resolves to the approved SHA.
3. Create a new annotated tag at that exact SHA. Never retarget an existing
   tag.
4. Push only that tag.
5. Create the GitHub Release from the pushed tag with evidence-bounded notes.
   Do not create or enable a hosted workflow.
6. Read back the remote tag object, peeled commit, Release URL, title, body,
   publication state, and attached assets. Report any mismatch immediately;
   do not silently repair it with destructive operations.

Prefer non-interactive Git and `gh` commands. Request approval when network,
credential, or external-write permissions require it. Do not delete or replace
a failed remote publication without a separate explicit instruction.

## Closeout records

Update `TODO.md`, `docs/STATUS.md`, `docs/ROADMAP.md`, the applicable EXP, and
the dated log only with verified facts. Record the exact tag, tag object,
peeled commit, Release URL, commands, statuses, and evidence class. Keep future
hosted CI/CD adoption as a separate task requiring multiple contributors and
explicit cost approval.
