# EXP-0004: Native command-graph correctness, overhead, and crossover

Status: Planned
Evidence class: silicon
Date: 2026-08-11

## Falsifiable hypothesis

For every preregistered ordinary file-processing workload, direct baseline and
Command Graph execution produce identical stdout, declared output hashes, exit
status, and failure propagation. For at least one preregistered independent
fan-out workload size, graph execution reduces median execution-only wall time
by at least 10% versus the equivalently specified sequential shell baseline,
with a paired-bootstrap 95% lower bound above zero. Graph construction and
end-to-end cost are reported separately and may falsify practical benefit.

## Baselines and holdouts

- direct argv execution of the same allowlisted tools and inputs;
- ordinary sequential composition for dependency and fan-out workloads;
- an equal-concurrency baseline must be added before claiming that scheduling,
  rather than concurrency alone, is the source of improvement;
- sequential text, pipeline, failure, and independent fan-out families with
  fixed seeds, file sizes, node counts, and repetitions.

## Environment

Planned first target: one Apple Silicon macOS host, followed by GNU/Linux.
Record Git SHA, OS and architecture, CPU model without serial identity, Python,
filesystem type when available, tool paths and versions, controlled
environment, workload manifest hash, and evidence class.

## Procedure

1. Freeze a versioned workload manifest before claim-bearing measurement.
2. Generate deterministic workspace inputs and hash them.
3. Warm each path without reusing outputs or caches asymmetrically.
4. Run the direct baseline first and the command graph under a seeded balanced
   order for enough repetitions to report median, p95, dispersion, and paired
   bootstrap intervals.
5. Reject a sample on timeout, semantic mismatch, undeclared output, stale
   lineage, tool identity change, non-nominal thermal state when observable, or
   unexpected exit status.
6. Store parser or graph construction, execution-only, and end-to-end durations
   separately. Preserve per-node status and hashes without machine-local paths.

## Raw evidence

Planned local logical path: `artifacts/research/EXP-0004/<RUN-ID>/` (ignored).
Remote preservation, if selected, follows the existing immutable research
bundle workflow and is not implied by a local demo run.

## Results

No claim-bearing measurements have been collected. A four-repetition manual
development smoke on macOS arm64 observed exact semantic agreement and zero
mismatches for `cat | grep | wc`. Its direct median was 60,775,479 ns and graph
median was 60,057,729 ns in that single noisy run. The sample is deliberately
insufficient for the preregistered hypothesis, reports
`crossover_evaluated=false` / `crossover=null`, and
must not be interpreted as a speedup. T-0099 workspace and existing GEMM tests
remain separate implementation evidence.

T-0103 additionally supplies a synthetic `showcase-parallel`/
`showcase-incremental`/`control-small` development walkthrough. It reports
same-input sequential and equal-concurrency controls, exact semantic hashes,
and a demo-only hash-verified cache state, but freezes no claim manifest and
preserves no EXP raw bundle. It is not an EXP-0004 sample, does not change this
experiment's evidence class or status, and cannot establish a crossover,
scheduling, reuse, or performance result.

## Interpretation

Pending. A faster graph path is not evidence of graph scheduling benefit until
baseline concurrency and semantic equivalence are accounted for. A slower or
no-crossover result remains valid evidence.

## Limitations and next action

The first experiment covers bounded file-processing tools on host silicon, not
interactive applications, network services, energy, Sonatine, ASICs, or a
general shell. Freeze a claim manifest, add/freeze the fair ordinary baselines,
and complete measurement fairness review before collecting claim-bearing
results. T-0103 is not a substitute for those steps.
