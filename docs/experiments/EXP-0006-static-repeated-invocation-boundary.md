# EXP-0006: Static repeated-invocation boundary

Status: Planned
Evidence class: RTL simulation pilot
Date: 2026-08-14
Task: T-0044
Authority: RFC-0004, RFC-0005, ADR-0039, ADR-0046, T-0042 integration
commit `528fbe28a0dcdfbab65d4ae2995c0876857e053a`, boundary implementation
commit `10b4f0fc2efe1e0b7f3d6a8722c5c766a23a6c2d`, collector implementation
commit `7575602e6651cc1e755e8d2f7b255aa8872db856`, runtime-fix commit
`80a35e61881393ba9790b19719eb1f6dcb4ee415`, installation-accounting
commit `cf454e4cd847d43d223fe7166b20d75dae0c2ffe`, log-synchronization commit
`988c25e615feaf711cb4d91f121d551bf88420ea`
Prior evidence: EXP-0005 (preserved unchanged)
Manifest: `benchmarks/manifests/t0044-static-repeated-invocation-v1.json`
Frozen manifest SHA-256:
`9dcf89434ea75c1d2a75e146f1d242f26f465dcad82b833beb16c6ebadf8dc21`

## Falsifiable question

Can static Graph, Rocket in-order, and BOOM OoO each execute ordered fresh
RFC-0005 inputs in one simulator process with one reset, one installation, no
artifact reload, exact per-invocation lifecycle accounting, independently
verified output bytes, and the same execution-window meaning? BOOM
serialize-dispatch is included only as a retained-structure diagnostic.

The commissioning stage answers only whether inputs 1--4 establish this
boundary and identifies fairness gaps. It is non-claim evidence. Only after it
passes unchanged may a separate 256-invocation RUN-ID derive the frozen
1/4/16/64/256 prefix accounts. Neither stage completes T-0044 or supplies
energy, timing, area, other Graph organizations, FPGA, ASIC, or silicon
evidence.

## Frozen session and phase contract

Each candidate session has exactly one simulator process, reset, installation,
and artifact, with no re-elaboration, reboot, program/descriptor reload, or
artifact replacement between inputs. Inputs are deterministic versions 1--256
in fixed order; input and output storage is overwritten every invocation and
actual 256-word output responses are hashed against the independent oracle.

Installation ends at the first owned input request. Staging runs from that edge
or the previous validation response through the final current-input staging
response and includes candidate-local preparation. Execution retains EXP-0005's
same-meaning final-staging-response through final-output-write-response window;
the Graph launch cycle is included. Drain/completion ends at the first
validation request. Validation ends at the 256th output response. Publication
is zero-cycle because output evidence is emitted on validation responses. The
account ends at the final validation response; later CPU checksum/`tohost`
cycles are outside it.

The CPU generates deterministic inputs with candidate-local instructions while
Graph generation is testbench-side. This asymmetry is frozen and visible. It
does not invalidate the execution window, but staging and end-to-end claims are
ineligible unless commissioning proves a same-meaning interpretation. The
predeclared result for an unresolved asymmetry is `pause`, not silent omission.

## Primary, diagnostic, estimator, and inference unit

The primary matrix is static Graph, Rocket in-order, and BOOM OoO. Each retains
lawful optimization: CPU load reuse stays enabled and Graph's extra traffic is
reported. CPU weakening is forbidden. BOOM serialize-dispatch remains
diagnostic-only and is never an “OoO-disabled CPU”. No secondary matched-load
ablation is active.

Commissioning derives prefixes 1 and 4 from one four-input session per member.
The campaign, if authorized, derives 1/4/16/64/256 from one 256-input session
per member; these nested prefixes are not independent samples. The inference
unit for input-dependent behavior is the fresh input at its frozen position.
Report exact vectors, cumulative and amortized totals, median, minimum,
maximum, and paired candidate/Rocket ratios. An input-dependent 95% paired
percentile bootstrap uses 100,000 MT19937 resamples with seed 6006 while
holding installation fixed once per resampled account. Input-invariant cycles
use exact values and distinct-input reproducibility counts without an
inferential interval. Commissioning intervals are never claim-bearing.

## Fail-closed and transition rules

Stop on oracle or resource failure; unexplained/pending traffic; missing
accounting; source, config, toolchain, artifact, or session drift; incomplete
matrix; different execution-window meaning; restart/reset/reload; or duplicate
or missing input/output versions. Dynamic traffic inequality alone is not a
failure, but an unexplained fairness boundary is claim-ineligible.

The full campaign may start only after the four-member commissioning passes and
a fairness review finds no source/config/toolchain change. Campaign account
256 is a new RUN-ID and artifact parameterization and must independently pass
its prefix 1 and 4 gates. Any other implementation/config/toolchain change
requires a new freeze and commissioning. Failed runs remain evidence.

Below 64 fresh inputs no RFC-0005 numerical no-go is permitted. Latency/traffic
cannot declare go. Missing energy, timing, and area always makes the result
partial/pilot. The only terminal labels are `advance`, `pause`, and
`early no-go`.

## Evidence layout and commands

Raw logs and exact command metadata are written under ignored
`artifacts/research/EXP-0006/<RUN-ID>/raw/`; derived analysis is written under
`derived/`; `raw-seal.json` binds raw bytes and the derived report. Host
wall-clock is operations-only.

Commissioning from a clean checkout of the freeze commit:

```sh
python3 -m raveil.t0044_repeated collect \
  --repo . \
  --manifest benchmarks/manifests/t0044-static-repeated-invocation-v1.json \
  --chipyard-source /path/to/pinned/chipyard \
  --account 4 \
  --run-dir artifacts/research/EXP-0006/<RUN-ID>
```

Earlier freezes produced only retained failed commissioning attempts. Stack,
installation-accounting, and log-synchronization corrections changed source,
so the manifest was re-frozen with the hash above before any replacement run
or complete-matrix observation.

## Estimate

The initial narrow estimate was 2--5 hours at medium confidence. Discovering
the compile-time CPU seed and one-shot manager changed it to 3--6 hours for
implementation/freeze plus about 15--60 minutes for commissioning, at
medium-to-low confidence until the first end-to-end run. This is a range, not a
single-date commitment, and must be updated from the first completed command.
