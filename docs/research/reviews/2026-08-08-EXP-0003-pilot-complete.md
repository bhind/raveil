# EXP-0003 powermetrics pilot-completion review

Status: Non-authoritative research memo
Stage: Pilot complete
Date: 2026-08-08

## Hypothesis

After a sampler-readiness barrier, calibrated native-C windows yield at least
three powermetrics CPU-power samples while thermal pressure remains `Nominal`.
This pilot tests measurement-contract adequacy only, not the Gate 1 performance
hypothesis.

## Evidence inventory

- successful RUN-ID `20260808T113416Z-643414460-d6179399`;
- 90 measurement records and 90 raw powermetrics files;
- analysis, environment, manifest, commands, source, and compiled tool records;
- sealed bundle SHA-256
  `231b83ef176a32e4e86811d756d8a0fe41b94a49a7baa2a955c6f3f09e05980b`;
- independent remote check with 0 differences and 100 matching files;
- preceding remotely preserved sampler-startup failure RUN-ID
  `20260808T112420Z-af35dd5c0-d6179399`.

## Data quality

All 90 measurements and semantic checksums passed. Every thermal observation
was `Nominal`; power-sample counts ranged from 3 to 12 with median 5. Every raw
file was non-empty and contained the readiness/measurement boundary marker.
The randomized five-repetition pilot covers six workloads and three candidate
families, but is intentionally too small and structurally unable to decide the
Gate hypothesis.

## Problems and counterevidence

The first formal attempt refuted the assumption that window duration alone
ensures sampler availability: its second raw file was empty. The readiness
barrier corrected that observed failure in the next RUN-ID. The minimum count
of exactly 3 leaves no margin for some fastest windows; full-run monitoring must
remain fail-closed. Summer ambient conditions previously produced `Moderate`
thermal pressure before bundle creation.

## Results and non-claims

The sampling-contract pilot passed and its immutable remote copy verified. The
analysis returned `not-applicable-pilot`, a complete measurement matrix, and no
claims. It does not show that any candidate, policy, or Experience improves
latency or energy. It provides no RISC-V, QEMU, Daphnis, FPGA, other-Mac, or TVM
performance evidence.

## Implications

Proceeding to the full fixed-C dataset is supported, subject to the existing
thermal, checksum, sample-count, clean-tree, and remote-integrity boundaries.
The failed startup bundle should remain available for T-0025 analysis. Drive
sync should be milestone-driven to limit storage and future API-quota exposure;
local sealed retries remain incomplete until later remote verification.

## Issue candidates

No new task ID is required. T-0022 owns policy comparison, T-0024 owns complete
metric reporting, T-0025 owns failed/boundary variants, and T-0065 owns the
already implemented durable-bundle mechanism and milestone sync policy.

## Next goals

Produce pre-registered PolicyOutcome inputs without oracle leakage, run the
24-holdout fixed-C manifest, preserve any unique failures, and complete an
independent fixed-C rerun before beginning pinned TVM integration.

## Recommendation

`continue`: the pilot measurement contract is adequate for the fixed-C full
stage. `pivot` only if the full run repeatedly reaches the three-sample boundary
or cannot maintain `Nominal` thermal pressure.
