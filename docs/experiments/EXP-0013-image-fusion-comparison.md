# EXP-0013: One visible integer-image workload and bounded fusion comparison

Status: Completed
Protocol: frozen and collected; original retained with evidence
Task: T-0241, local provisional registration pending GitHub authentication
Owner: primary; read-only measurement review is advice
Authority: owner explicitly approved the proposed demonstration, comparison and
continuation decision on 2026-10-17, without intermediate approval stops.
Context: ADR-0107; T-0240 verified candidate; no new architecture or hardware gate.

## Question and fixed endpoint

Does existing v2 fusion materially reduce simulated execution and port traffic for
one visible image pipeline compared with existing v1 scalar materialization?
Finish this question within the owner-approved one-week cap. Do not add operators,
model import, new hardware or unrelated generalization to defer the decision.
Fusion is established compiler practice; this experiment makes no novelty claim.

## Workload and equality

Input is an even 2..64 by 2..64 uint8 image, represented as existing uint32 words.
At each pixel compute right-minus-left with clamped horizontal neighbors; encode
the signed difference modulo2^32; apply explicit signed ReLU; take each2x2 maximum.
Publish gradient, activation and pooled outputs. Three deterministic owned inputs:
blocks16x16, diagonal24x24, texture16x24, defined in scripts/image_demo.py.
Independent Python coordinate arithmetic and independent native C implement the
formula, without consuming compiler plans. Both source variants differ only in
the array schema selecting existing v1/v2 compilation; same inputs, operations,
requested outputs, kernel, RTL/runtime binary and interpreter contracts.

## Collection frozen before first run

Freeze exact source/input hashes, runtime/kernel/native executable identities,
prepared engine inventory/manifest/launcher and imported harness helper identities,
expected outputs, environment, commands, order and thresholds into freeze.json.
Preserve a copy of this protocol. Execute each variant three times for each input;
alternate scalar/fused order by case and repetition. All18 runs are included;
no excluded warmups, optional stopping, outlier removal or favorable reruns.
Each invocation starts fresh QEMU/RTL sessions; existing host/Docker caches are
not reset or isolated. Thermal state, power state, competing load and affinity
are uncontrolled; wall timings are only observations of this local session. This is a small descriptive paired engineering comparison,
not a statistically powered or representative application-performance study.
Each run has900-second cooperative timeout and975-second outer watchdog.
Stream partial stdout/stderr to disk from process start; on timeout/interrupt
request foreground SIGTERM and allow75 seconds to drain before last-resort kill.
Always preserve command/status/failure and audit owned resources after failure. Any
failure stops claim-bearing collection, preserves all attempts and requires a
separately labelled revision rather than replacing a result. Cap18 runs and2GiB
new experiment artifacts; no download, paid resource, new image or purchase.

## Three distinct measurement boundaries

1. **RTL simulation:** validate each complete saved parent and its exact bound
   DAG/RTL records before extracting metrics. Sum successful jobs' last trace
   response cycle plus1. The harness cycles begin after the start edge; the final
   write response finishes AffineFoldRegion on that edge. Includes post-start RTL header/instruction
   validation, execution and seed-213 cycle-driven synthetic stalls; excludes reset/start edges, host
   packing, QEMU/Docker startup, inter-job gaps and filesystem work. Hash trace
   bytes and executable identity. The existing checker validates transactions
   and ordering but does not independently replay every cycle timestamp.
2. **RTL port traffic:** count accepted reads/writes from validated device.json
   and trace.bin; payload bytes=4*(reads+writes). Includes every intermediate job's
   transfers. This is not host copies, UART bytes, cache/DRAM bandwidth or energy.
   The current DAG fixes seed213 with the same synthetic memory policy. Because
   its RNG advances per cycle, variants do not have identical per-access delays.
3. **Host usability:** monotonic elapsed time immediately around the full CLI
   subprocess, including preparation, actual QEMU/RTL, saved verification and
   exit. Store all observations, medians and paired ratios. CPU C -O3 is separate
   compute-only context: one untimed warmup per invocation,50000 calls timed with
   CLOCK_MONOTONIC, five repetitions/input; read/parse/output excluded. A volatile
   function pointer prevents removing repeated computations. Verify all three
   complete output arrays. This CPU measure is not the denominator of a hardware
   speedup claim and is not the best possible CPU implementation.

## Preregistered interpretation

Correctness of every output and preserved source identity are mandatory. Require
at least20% fewer aggregate simulated job cycles AND20% fewer port transactions
on EACH input to call fusion useful for this pipeline. Require lower median host
wall time on EACH input to call local simulation operation improved in this uncontrolled local session. These are
engineering decision thresholds, not significance tests.

- Both conditions pass: retain existing fusion for this bounded workflow. Finish
  the demo; do not infer a reason to build new hardware or expand generality.
- RTL reduction passes but host condition fails: retain evidence and focus any
  next work on host costs before adding computational capability.
- RTL reduction fails: do not expand generality/hardware on this mechanism's
  behalf; publish the negative result and close this experiment.

No physical frequency, energy, area, real-time deadline, CPU superiority or Groq
advantage is inferred. A losing CPU practical comparison remains publishable.

## Deliverables and verification

scripts/image_demo_experiment.py performs frozen collection; image_demo.py supplies
source/oracle/trace metrics; image_demo_cpu.c supplies the independent C baseline.
tests/test_image_demo.py verifies hand results, independent generated comparisons,
cycle boundary/failed-trace rejection, nested-job aggregation, policy thresholds
and native C equality. The static report displays only outputs matched by actual
runs. Provide editable input/standalone app, visual report, raw runs, freeze,
derived metrics and a concise disposition. Relevant regression and record checks
precede local closeout. Canonical integration/Project remain separately pending.

## Results — 2026-10-17

All18 preregistered ordered runs complete, exit0, with267 distinct sessions/jobs
and16,416 output words. No failure, exclusion or rerun. Each variant's RTL counts
are identical across its three repeats on every input. Independent output equality
holds for gradient, activation and pooled images, including15 C invocations.

| Input | RTL active cycles scalar → fused | Reads | Writes | Host median seconds | CPU compute median ns |
|---|---:|---:|---:|---:|---:|
| blocks-16 | 40096 → 16167 | 2944 → 1280 | 2240 → 576 | 51.093148 → 6.621327 | 287.460 |
| diagonal-24 | 90276 → 36274 | 6624 → 2880 | 5040 → 1296 | 124.060685 → 30.192651 | 449.460 |
| texture-16x24 | 60313 → 24219 | 4416 → 1920 | 3360 → 864 | 86.449417 → 16.087237 | 299.100 |

Cycle reductions are59.679%,59.819%,59.844%; transaction reductions are64.198% each.
All matched fused/scalar wall ratios are below1.0, with all raw observations/order
retained. Host timing is uncontrolled and descriptive; CPU values are compute-only
context, not a physical accelerator comparison. CPU host is Apple M2, Mac14,15,
24GiB; macOS26.6.2 arm64/Python3.14.6. Existing QEMU11.0.3/Docker29.7.2 and pinned
local runtime image were used. Exact compiler version/options are in freeze.json
and cpu-build.json. There is no download, hardware acquisition or paid resource.

**Disposition:** both preregistered criteria pass for this specific workload,
backend and synthetic-memory policy. Keep existing fusion and finish this demo.
The seconds-long simulation path offers no demonstrated practical reason to
replace ordinary CPU image processing. No hardware expansion or further generic
capability backlog follows from this result. It demonstrates the engineering value
of removing scalar materialization in this implementation, not a new mechanism.

## Reproduction and closeout evidence

From the T-0241 candidate, run `python3 -B scripts/image_demo_experiment.py
 --output OUTER/artifacts/raveil-image-20261017 --kernel KERNEL --build RUNTIME`
with a fresh output path. KERNEL is the verified T-0238 ELF and RUNTIME the verified
T-0239 runtime-cid-verified directory; exact absolute command is preserved in
ignored evidence. The unchanged kernel SHA256 is
35db85f0018595fe4c68d425f5071c39072b9eb35095477b8d4cdec1ebee49f9;
runtime identity is bdb6eefe93fe768fa2aa656b9354dcf5c7a4c28107b7dd979c49902b322a18ab.
The frozen protocol is preserved as frozen-experiment.md before this result append.
Freeze SHA256:1ae92ffead552a151134687a284fe5fb8a4a0d9cade04c362a8f0611424f7efa.
Summary SHA256:a2b9805a0f5a5482d09afd33424333efbc41c75ae5eeb84b1fcfda97fe0f3656.

`python3 -B -m unittest -v tests.test_image_demo tests.test_array_program
 tests.test_array_fusion tests.test_project_fold tests.test_project_array_fusion`
passes64 tests in16.198s. A final `python3 -B -m unittest -v tests.test_image_demo`
passes12 in1.895s after the CPU collector adopts the same tested partial-log/timeout
wrapper. Precollection review corrected that evidence-retention boundary, app/
helper identity bindings and paired-ratio storage. Initial aggregation fixture
omitted project.json; corrected fixture initialization, not production semantics.

Primary verifies105 frozen source hashes before result-record edits; all267 trace
hashes and counts,18 output/ID records,15 CPU records and paired/median aggregates
match. The independent read-only reviewer corroborates these facts. Raw observer
queries establish no owned resources. Completed collection occupies about222MiB,
below the2GiB cap. All raw logs, partial-log infrastructure, commands, frozen data,
per-job metrics and source/app identities remain available in the delivery folder.
Native browser preview became stuck on OS permissions after collection; no
permission/settings change was attempted. HTML structural/data checks and visual
inspection of a PNG made from verified output matrices provide local artifact QA;
native browser rendering is not claimed. The saved viewer also revalidates a full
captured result before generating its standalone HTML without a new execution.
