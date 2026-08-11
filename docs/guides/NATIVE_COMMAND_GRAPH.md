# Native Command Graph demo

T-0101 evaluates ordinary bounded file-processing work itself. It does not
launch the tensor/GEMM demo as a substitute.

## Start

```sh
mkdir -p /tmp/raveil-command-demo
python3 -m raveil shell --workspace /tmp/raveil-command-demo
```

```text
raveil> write /input.txt "INFO start\nERROR failed\nERROR retry\n"
raveil> run cat /input.txt | grep ERROR | wc -l
2
raveil> graph compile cat /input.txt | grep ERROR | wc -l
graph=command-...
nodes=3 edges=2
raveil> graph show
raveil> graph execute --compare
semantic=valid
baseline_exit=0
graph_exit=0
raveil> graph benchmark --warmups 3 --repetitions 20
raveil> graph result /command-result.json
raveil> cat /command-result.json
raveil> exit
```

The shell supports quoted argv, pipelines (`|`), input (`<`) and exclusive
output (`>`) redirection, success dependencies (`&&`), explicit sequencing
(`;`), and the owned join-fanout operator `|||`. `a ||| b && c` runs `a` and
`b` independently under the same worker limit and starts `c` only after both
succeed. `|||` is not POSIX shell syntax and never creates a background daemon.

The initial tool allowlist is `echo`, `printf`, `pwd`, `ls`, `cat`, `stat`,
`mkdir`, `grep`, `wc`, `sort`, `uniq`, `cut`, `tr`, `head`, `tail`, `tee`,
`cp`, and `sha256sum` (adapted to `shasum -a 256` where required). Each binary
is resolved without ambient PATH lookup and bound by its hash, normalized
version, adapter, argv, and controlled environment.

Direct and graph runs use separate copies of the same workspace snapshot.
Only exact stdout, normalized error/status, and declared-output agreement can
publish exclusive outputs. A mismatch, timeout, stale tool, undeclared change,
or collision keeps graph output uncommitted.

## Limits and evidence

This is a bounded subset, not a POSIX/GNU shell. It has no arbitrary executable,
`shell=True`, `sh -c`, expansion, substitution, globbing, append, background
job, network tool, deletion, or privilege operation. T-0099 remains
application-level containment, not an OS security boundary; T-0100 remains
open.

`graph benchmark` is a development/non-claim smoke. It records balanced order,
execution-only and end-to-end samples, median, p95, IQR, paired bootstrap
interval, validation time, mismatch/timeout counts, and concurrency. EXP-0004
remains Planned until a manifest and Performance Reviewer-approved claim run
are frozen. The current smoke does not evaluate crossover; small-graph
overhead and a future measured no-crossover remain valid negative results.

Direct execution time is the source-order interpreter interval. Graph
execution time is the ready-set DAG scheduler interval. Direct end-to-end adds
the recorded parse and semantic-validation costs; graph end-to-end adds parse,
graph construction, and semantic-validation costs. Workspace snapshot creation and output publication
are outside both intervals in this seed. Invalid or timed-out pairs are counted
but excluded from summaries and paired bootstrap statistics.

The current direct interpreter buffers pipeline stages instead of reproducing
an ordinary concurrently running OS pipe. Benchmark records therefore set
`ordinary_pipeline_baseline=false` and `scheduling_claim_eligible=false`.
Claim-bearing EXP-0004 work must add that baseline; the implemented equal-
concurrency comparison is limited to explicit `|||` fan-out.
