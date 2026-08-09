# EXP-0003 fixed-C target full-dataset review

Status: Non-authoritative research memo

Stage: Fixed-C target full dataset

Date: 2026-08-09

## Hypothesis

For the registered 24 fixed-C target holdouts on one Apple M2, bounded
Experience can improve median latency and same-Mac estimated energy by at least
5% relative to cold while the paired-bootstrap 95% lower bounds are positive,
joint negative-transfer rate (NTR) is at most 5%, and bounded selection quality
does not materially degrade relative to full history.  This memo assesses that
hypothesis only for the reported fixed-C execution; it does not decide the Gate
or change an experiment record.

## Evidence inventory

- History/source RUN `20260809T090521Z-51ef48c69-0e3d9b20`, bundle SHA-256
  `9c6d92af382e8e561442316919a2520dc8bcb4366c82d2e9a1a502aeca870889`,
  supplies the sealed source evidence named by every target selection.
- Target RUN `20260809T113515Z-874c84ae2-ddb463a8`, bundle SHA-256
  `971ee9fa08d9f1c4f718a0a26c33530ee9ef99c3b674df6de4f6d60963d73156`,
  supplies 3,600/3,600 valid fixed-C silicon measurement records and 144
  complete policy outcomes: 24 holdouts times cold, full-history, bounded,
  FIFO, reservoir, and random.
- All target semantic checksums and measurement-valid flags pass.  Every
  reported thermal observation is `Nominal`; the power-sample count is 3--14
  with median 5.
- The local target bundle manifest records 3,612 included files and excludes
  itself.  The primary sync command reportedly exited 0.  Security review
  independently confirmed local bundle-integrity and sensitive-data scan
  checks, but did not independently verify the remote target copy.
- The selection records name the source RUN and source hash above and have one
  common local registration timestamp, `2026-08-09T11:34:44.232693+00:00`.
  The first target measurement is timestamped `2026-08-09T11:35:19.352529Z`.
  This supports the local preregistration ordering contract, not independent or
  adversarial timestamp attestation.

## Data quality and problems

The complete, checksum-valid, nominal-thermal matrix is strong fixed-C silicon
evidence for the recorded conditions.  Its minimum allowed three power samples
per window remains a narrow margin.  Energy variability is substantial:
performance review reports median energy CV 16.4% and p95 CV 34.7%.  The
reported paired bootstrap is therefore useful as implemented evidence but does
not model the workload/repetition hierarchy; a hierarchical bootstrap is
missing.

The six policy slates have equal *logical* online measurement budgets of three
candidates, but the target dataset measures the exhaustive ten-candidate matrix
to calculate the offline oracle.  It does not establish an actual online
execution-time or online-energy saving from making only the slate measurements.

Remote immutability remains an evidence gap for this review: a primary-command
success is not the same as the reviewer's independent download verification.
Security review also identified two boundary weaknesses to triage: bundle-path
traversal handling and a sensitive-data scan limited by filename extension.

## Results

The registered analysis reports the following bounded-versus-cold results:

| Measure | Result | Gate reading |
| --- | ---: | --- |
| Median latency improvement | 0% | below 5% |
| Latency bootstrap 95% interval | [0%, 0%] | lower bound is not positive |
| Median estimated-energy improvement | 0% | below 5% |
| Energy bootstrap 95% interval | [0%, 1.989%] | lower bound is not positive |
| Joint NTR | 1/24 = 4.17% | within the 5% limit |
| Latency / energy quality gap versus full history | 0% / 0% | within the 2% limit |
| Active-memory maximum, bounded / full history | 64 / 240 records | bounded limit met |
| Retrieval p95, bounded / full history | 83.383 / 241.534 microseconds | bounded is lower |

Thus the resource, retrieval, NTR, and reported full-history-quality conditions
are favorable, but neither primary improvement condition nor either bootstrap
lower-bound condition is met.  The target analysis correctly reports the Gate
as not ready.

## Non-claims

- These data do not show a latency or energy improvement for bounded Experience
  over cold on this fixed-C target run; zero median improvement is not a
  positive result.
- They do not establish an independent rerun, a pinned official apache-tvm
  MetaSchedule result, cross-hardware transfer, RISC-V, QEMU, Daphnis, FPGA, or
  ASIC performance.
- Powermetrics energy is an estimated relative metric on the same Mac, not a
  direct physical-energy result transferable to another system.
- Equal candidate-slate size does not by itself demonstrate an online execution
  saving while exhaustive measurements were used to construct the offline
  oracle.
- Local preregistration chronology and a successful primary sync command do
  not prove independently witnessed registration or remote bundle contents.

## Implications and counterevidence

Bounded retention appears to preserve the reported selection-quality metric
while reducing active memory fourfold and lowering retrieval p95 by about
65.5% versus full history.  Those are useful operational observations, not a
substitute for the Gate's improvement thresholds.

The direct counterevidence is decisive for this execution: latency and energy
medians are both zero rather than at least 5%, and their lower confidence bounds
are zero.  The energy-CV and missing hierarchical-resampling analysis further
reduce confidence in any fine-grained energy distinction.  The one negative
transfer holdout is within the prespecified rate limit, but it remains evidence
against a uniform benefit.

## Issue candidates

No new stable task ID is allocated by this memo.  The Project Manager should
deduplicate the following candidates against canonical records before routing:

- add hierarchical bootstrap/resampling that respects workload and repetition
  structure, and report sensitivity to energy CV;
- measure a true online three-candidate policy path separately from the
  exhaustive oracle-matrix collection, including its execution time and energy;
- independently download-verify the target remote bundle and retain the exact
  verifier output;
- reject bundle paths that escape the intended root, and make sensitive-data
  scanning content-aware or otherwise cover extensions outside the current
  allowlist.

Existing T-0022 and T-0024 remain the closest owners for policy-comparison and
complete metric evidence; T-0025 covers preserved boundary variants and T-0065
covers durable-bundle mechanics.  The security candidates require Project
Manager triage rather than an implied task allocation here.

## Next goals

1. Preserve the reported run and obtain independent remote download/content
   verification for the target bundle.
2. Repeat the fixed-C target execution independently, applying a
   hierarchy-aware uncertainty analysis and explicitly reporting energy-noise
   sensitivity.
3. Run a separately instrumented true online-slate experiment if online
   measurement saving is a desired claim.
4. Execute the pinned official apache-tvm MetaSchedule comparison and send any
   contradiction to research review.
5. Triage and close the path-traversal and extension-limited-scan boundaries
   before treating bundle review as comprehensive.

## Recommendation

`pivot` the fixed-C research direction while `pause` Gate advancement.  The
specific fixed-C target execution fails the preregistered 5% latency and energy
thresholds, so continuing toward a success claim on the current interpretation
is not supported.  This is not a global falsification of bounded Experience:
the required independent run and pinned-TVM comparison are absent, and the
resource/retrieval observations remain worth testing under a revised,
noise-aware design.  Continue only with those confirmatory and methodological
goals; do not mark EXP-0003 or Gate 1 ready from this dataset.
