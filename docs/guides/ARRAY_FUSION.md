# Versioned array fusion

The local T-0237 candidate accepts `raveil.array-program/v2` through the same
array CLI. V1 files retain their original partition and saved-proof meaning.
V2 preserves the integer-array grammar and chooses admitted whole-stage or
single-output block execution automatically. Users specify computations, not
backend jobs or tiles.

```sh
python3 -m raveil project init /tmp/raveil-fused
cp examples/array-program/fused-gemm.json /tmp/raveil-fused/inputs/program.json
python3 -m raveil project array-check --project /tmp/raveil-fused --input program.json
python3 -m raveil project array-run --project /tmp/raveil-fused --input program.json --kernel /path/to/sonatine.elf --build /path/to/verified-runtime
python3 -m raveil project arrays --project /tmp/raveil-fused
```

Use a fresh workspace path. `fused-long-map.json` and `fused-stages.json` provide
editable map and linked-stage examples. The check command needs no simulator.
Existing `array`, `arrays` and `array-diff` inspect and compare retained attempts.
Execution needs the already-supported QEMU executable and verified offline RTL
runtime. No new tool installation or physical hardware is required.

The preview reports final passes, sessions, jobs, materialized output words,
packed words, conservative logical peak storage and source scalar evaluations.
Fewer sessions or materialized words are structural properties, not measured
speedups. The compiler first tries whole-stage grid admission. Long maps use
single-output blocks when they fit; multiple simultaneously live values may
still require individual passes. Every choice passes the existing backend checks. In `stages`, `mode: scalar`
means that whole-stage fusion was unavailable or not selected; subsequent block
grouping may still fuse that stage. Inspect `passes[].op` for the final choice.

The following are static plans for the acceptance inputs, with unchanged backend
limits. A session is a dispatch unit, not a time measurement.

| Input | V1 sessions | V2 sessions | V2 passes |
| --- | ---: | ---: | ---: |
| 24-node expression, 6 cells | 24 | 2 | 2 |
| 32x8 by 8x32 matrix product | 124 | 4 | 1 |
| 17x64 by 64x19 matrix product | Budget rejection | 16 | 1 |
| 24-node map over 64x64 cells | Budget rejection | 32 | 2 |
| 24-node map followed by transpose | 25 | 3 | 3 |

Post maps execute after the whole fold. All arithmetic remains uint32 wrapping
with explicitly signed max/ReLU interpretation. A failed child suppresses every
requested output; retry creates a new attempt. Saved verification reconstructs
the versioned plan and checks exact child bindings without process execution.

See [ADR-0133](../decisions/ADR-0133-admitted-array-fusion.md) for the exact bounds
and [the original input guide](ARRAY_PROGRAM.md) for the unchanged grammar.
Practical readiness for arbitrary applications is not established by these
functional workloads. In particular, float, dynamic control, model import,
large external-memory data and performance/energy targets remain unimplemented
or unverified in this common-array path.
