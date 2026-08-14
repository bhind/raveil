# T-0044 EXP-0008 evidence-promotion owner packet

Status: ready for execution after ADR-0048 integration
Task: T-0044
Evidence: existing EXP-0008 RTL-simulation latency/traffic bundle
Decision context: ADR-0009, ADR-0048, EXP-0008

## Objective

Promote the already completed EXP-0008 failed and recovery bundles to durable,
download-verified evidence without rerunning any simulator or modifying any
sealed byte. Record a non-sensitive receipt in Git. This closes only the
EXP-0008 durability gap; T-0044 and RFC-0005 remain open.

## Jitro prompt

```text
Work as Jitro on T-0044. Use a dedicated branch named
research/t-0044-exp-0008-evidence-promotion after ADR-0048 is integrated. You
are not alone in the repository: preserve unrelated work and never revert,
stash, amend, or absorb another branch's changes.

Authority, in order:
1. executable collector/verifier code and tests;
2. docs/experiments/EXP-0008-static-full-campaign.md;
3. ADR-0009 and ADR-0048;
4. docs/STATUS.md, TODO.md, docs/ROADMAP.md, docs/OPEN_QUESTIONS.md;
5. docs/log/2026-08-15.md.

Goal:
Verify and durably promote the existing EXP-0008 evidence. Do not collect new
performance data. Do not rerun Static Graph, Rocket, BOOM, or BOOM serialize.
Do not change any estimator, threshold, manifest, RTL, ELF, raw log, derived
report, RUN-ID, or existing seal.

Required source bundles:
- failed RUN-ID 20260814T130018Z-4368066-campaign256;
- recovery RUN-ID 20260814T153738Z-0203248-campaign256-recovery;
- expected failed-seal SHA-256
  88fe79590c3ea98129d57363920686b084fb10b45e2a9c5fc0b53db3f3bc8726;
- expected recovery raw-seal SHA-256
  7c90f8a4a09291f5269e19d1425d1eac1a7915b8b3abcc4f16eb7206f438eeef;
- expected derived-report SHA-256
  1e52c4e213cb19cb2455cfef67077d3d3acb959bfb834c24e6b12e932d2f7a65.

Implementation requirements:
1. Add the smallest repository-owned EXP-0008 promotion verifier/adapter. Reuse
   the fail-closed semantics of raveil.research_bundle where possible, but do
   not force the existing T-0044 seal into an incompatible schema and do not
   copy hundreds of megabytes merely to reshape a directory.
2. Before network access, verify both seal files, every listed relative path,
   exact byte count and SHA-256, the recovery derived report hash, frozen base
   and recovery manifest hashes, failed-seal lineage, and the absence of
   symlinks or unexpected mutation. Require both exact RUN-IDs.
3. Copy each RUN directory to
   <remote-root>/EXP-0008/<RUN-ID>/ with immutable/no-overwrite behavior. Use a
   repository-external rclone configuration. Exclude credentials and host-local
   absolute paths from commands, logs, receipts, and Git.
4. Perform download-based one-way content verification. Only after it succeeds,
   upload completion-marker.json last with immutable semantics and read it back
   byte-for-byte. Refuse an already completed remote path; never overwrite it.
5. Emit a canonical JSON receipt containing schema/version, evidence class,
   verifier Git revision, EXP-ID, both RUN-IDs, logical remote locators, source
   seal/report hashes, checked file and byte totals, redacted exact argv,
   rclone version, exit statuses, UTC verification time, and completion-marker
   hashes. Reject unknown fields and secrets. Add focused mutation, missing
   file, symlink, wrong-size/hash, completed-remote, check-failure, and
   marker-readback tests using a fake rclone boundary; tests must not require
   real network access.
6. With owner-provided external credentials only, run the real immutable copy
   and download verification. If credentials or remote access are unavailable,
   stop with a tested local verifier and status `promotion-blocked`; do not
   fabricate a receipt or mark promotion complete.
7. On verified success, track only the small receipt and update EXP-0008,
   STATUS, TODO, ROADMAP, OPEN_QUESTIONS, experiments/README, and the dated log.
   State exactly `remotely durable RTL-simulation evidence`; do not say silicon,
   product, RFC-0005 go, T-0044 complete, or general workload speedup.

Acceptance:
- existing failed and recovery seal bytes remain unchanged;
- no simulator process runs;
- local verification independently recomputes every file size/hash;
- both remote paths use immutable transfer and download-based checking;
- completion markers are last and read back exactly;
- the tracked receipt contains no secret or machine-local absolute path;
- focused tests, relevant campaign/recovery tests, record checker, and
  git diff --check pass;
- exact commands, versions, exits, counts, receipt hash, remaining non-claims,
  and any blocked external step are recorded.

If any source byte or seal is missing/mismatched, stop. Preserve the finding
and propose a new preregistered EXP/RUN-ID; never reconstruct evidence from the
published summary table and never silently rerun EXP-0008.
```

## Expected handoff

Return the branch and commit, files changed, exact local and remote verification
commands, evidence class, receipt path/SHA-256 if created, checked file and byte
counts, completion-marker readback result, test results, and unresolved risks.
An unavailable owner credential is a promotion blocker, not permission to
change the measurement or claim.
