# EXP-0014: Host inventory cost on unchanged image programs

Status: Completed
Task: T-0242
Decision context: Proposed ADR-0137; retain completed EXP-0013 unchanged.
Evidence classes: host software wall time; QEMU/RTL functional/cycle counters.

## Hypothesis and boundaries

Descriptor-relative inventory traversal reduces saved-proof verification cost
without removing nested semantic checks, changing image outputs or changing RTL
work. Diagnostic cProfile samples selected this hotspot; they are exploratory,
not included in the paired acceptance dataset. No physical or Groq claim.

Compare frozen T-0241 engine against T-0242 on the same three EXP-0013 images,
all using fused v2. Prepare fresh adjacent old/new applications with identical
existing kernel/runtime and source bytes.3 repeats per image/engine,18 fresh
runs, followed by18 saved reads. Alternate old/new order by repeat+case index.
Saved comparisons use the exact same first successful capture path for both
engines, with subprocess execution forbidden inside the probe. No warmup or
outlier exclusions; do not restart failed attempts or silently tune after data.

Time the complete foreground CLI subprocess through exit, including startup,
execution, nested validation and output. Saved timing includes Python startup,
imports and complete recursive load, ending after the record digest is printed.
Record all argv/cwd/stdout/stderr/return codes, source/application/input hashes,
run identities, bound trace hashes and counters. Verify every output against the
independent image oracle. Require identical outputs, jobs, sessions, cycles,
reads/writes, interface bytes, ordered per-job trace hashes and executable identities
across all versions/repeats for each image.

Run on the existing local Mac/Python/QEMU/Docker setup, with no installation,
hardware purchase or controlled CPU affinity/thermal/power conditions. Report
all paired ratios and medians descriptively, not statistical significance or
production latency. Timing observer overhead and OS caches remain in the boundary.

## Fixed disposition

Require all correctness/resource/hash checks and UT to pass. Retain the change
if every image's saved-read median decreases by at least20% and no image's fresh
CLI median increases by more than10%. Otherwise retain evidence and do not
claim an accepted performance improvement; revisit the implementation separately.
No new hardware/generalization gate advances either way.

## Commands and records

`python3 -B scripts/inventory_experiment.py --output OUTPUT --baseline BASELINE
--kernel KERNEL --build RUNTIME` (one invocation; arguments are absolute paths
in raw command records). `freeze.json` is written before timed collection;
`frozen-protocol.md` preserves this version. Results will be appended afterward,
without changing scientific fields. Current task authorization covers this bounded
host-cost correction and comparison; GitHub integration remains separately pending.


## Results — 2026-10-17 local acceptance

The frozen collection completed without exclusions, retries or failures:18 fresh
parents,114 distinct sessions/jobs,16,416 output words and18 saved reads. All
three outputs, ordered per-job trace hashes, executable identities and RTL counts
match for all six runs of each image. Total459,960 simulated active cycles and
52,896 port transactions are unchanged work, not a device-speed improvement.
All104 collection-source hashes and307 final product/test/script hashes reconcile;
original frozen protocol is preserved before this results appendix. Both prepared
app manifests/launchers and all input hashes match. Successful raw Docker/process
queries find no owned resources. Primary independent recount and read-only review
agree with the collector; raw job hashes are rechecked independently.

| Input | Fresh CLI old median s | New median s | Reduction | Saved old median s | New median s | Reduction |
|---|---:|---:|---:|---:|---:|---:|
| blocks-16 | 6.061898 | 5.820459 | 3.98% | 1.433103 | 0.902081 | 37.05% |
| diagonal-24 | 27.732285 | 15.385933 | 44.52% | 2.284013 | 1.416924 | 37.96% |
| texture-16x24 | 12.432758 | 9.938098 | 20.07% | 1.607429 | 1.131464 | 29.61% |

Disposition: retain the inventory implementation. Every saved-read median clears
20% reduction; no fresh CLI median regresses by more than10%. These are descriptive
local observations with substantial spread, not statistical significance or
production latency. For example blocks16 old fresh runs range5.990–12.750s.
No compiler/operator/kernel/RTL change and no physical/generalization gate advance.

Affected broad regression:593 UT; final18 inventory/collector tests and15 app
checks reconcile597 distinct passed tests. Additional compatibility revalidation
of all18 original EXP-0013 captures executes no processes and preserves outputs.
The primary changed only raveil/project.py within the prepared product engines;
preparation additionally includes the new ADR document.

Evidence: OUTER/artifacts/raveil-host-20261017 (freeze, all36 timed subprocess
records and logs, bound metrics/traces, summary, resources, primary verification).
Source/UT/review/patch records: canonical artifacts/research/T-0242.
Ready application: OUTER/artifacts/raveil-image-fast-20261017.
Freeze SHA256:3a9789f6d7f690056d43d8555da022e7fc1893f30943928395748d9f6e78188d.
Summary SHA256:662a8f37e069a750fd76564d4d245536ee3beedfc1dc4305104d644d35c6d30a.
No remote benchmark publication, Issue acceptance or main integration is implied
by the local disposition. Any later package smoke is outside this frozen dataset.
