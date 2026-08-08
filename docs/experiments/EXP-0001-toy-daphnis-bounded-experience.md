# EXP-0001: ToyDaphnis bounded-Experience closed loop

Status: Completed
Evidence class: analytical deterministic model
Original seed date: 2026-08-07
Reproduced: 2026-08-08

## Hypothesis

Under a two-measurement target budget, nearby Experience from training shapes
can rank the best analytical candidate more often than the cold prior while
online memory remains bounded.

## System under test

- workload label: `branching-mlp`;
- training shapes: 256, 512, 1024, 2048;
- holdout shapes: 384, 768, 1536, 3072;
- memory regimes: 8 and 32 KiB;
- candidates: baseline, vector8, vector16, remat16, spill8;
- backend: deterministic `ToyDaphnis`, not hardware;
- online active limit: 64;
- target measurement budget: 2 including the trusted baseline.

## Reproduction environment

- Git code revision: `d4204e10f62b4d232c6fdcf8a02a098cee595d3a`;
- macOS 26.5.1, arm64;
- Python 3.14.6;
- command:

```bash
python3 -m raveil bench --budget 2 --active-limit 64
```

## Result

| memory | shape | cold HCR | warm HCR | warm best |
|---:|---:|---:|---:|---|
| 8 KiB | 384 | 97.0% | 97.9% | remat16 |
| 8 KiB | 768 | 97.1% | 100.0% | remat16 |
| 8 KiB | 1536 | 95.9% | 100.0% | remat16 |
| 8 KiB | 3072 | 95.4% | 100.0% | remat16 |
| 32 KiB | 384 | 97.0% | 100.0% | vector16 |
| 32 KiB | 768 | 95.2% | 100.0% | vector16 |
| 32 KiB | 1536 | 94.0% | 100.0% | vector16 |
| 32 KiB | 3072 | 93.5% | 100.0% | vector16 |

Mean HCR was 95.6% cold and 99.7% warm, a +4.1 percentage-point difference.
The eight acceptance tests also passed in 1.180 seconds on this environment.

## Interpretation

The deterministic software loop retrieves, ranks, measures, appends, and
consolidates as designed for these hand-authored candidates and contexts. This
does not establish compiler, accelerator, FPGA, or silicon performance and is
not evidence that the same transfer rate survives real workloads.

## Limitations

The oracle enumerates only five candidates; workload and timing are analytical;
noise, retrieval latency, NTR, calibration, hardware drift, and semantic
equivalence are not meaningfully evaluated. Gate 1 requires a real replayable
measurement boundary and stronger holdouts.
