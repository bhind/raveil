# Native Command Graph showcase

T-0103 is a reproducible **synthetic development smoke**, designed to make the
order and limits of the current Native Command Graph visible. It neither
concludes EXP-0004 nor claims a host, ISA, energy, scheduling, ASIC, or silicon
improvement.

> **Abstraction warning:** this showcase uses whole host tools/processes such as
> `sort` as nodes. It is only a conceptual operator-facing illustration and is
> far above Raveil's intended native operation/dependency/effect/object graph.
> It does not infer low-level dependencies from an instruction stream, replace
> or simplify OoO machinery, model instruction/data caches or pipelines, define
> a Daphnis encoding, or compare CPU microarchitectures. Its cache is ordinary
> showcase-only content-addressed memoization. Graph-free build systems can
> perform the same kind of reuse. Do not use this demo as evidence for the
> native-graph, ISA-extension, area, energy, or performance thesis.

## Run in a few minutes

Use a new empty directory; this is application-level workspace containment,
not a hostile-input sandbox.

```sh
mkdir -p /tmp/raveil-showcase
python3 -m raveil showcase list
python3 -m raveil showcase prepare --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16
python3 -m raveil showcase run --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16
python3 -m raveil showcase mutate --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16 --node 0
python3 -m raveil showcase run --workspace /tmp/raveil-showcase \
  --scenario showcase-incremental --nodes 16
```

`--nodes 16`, `32`, and `64` select the independent fan-out size. `control-small`
is a four-file, 512-byte control that can make Graph construction and
validation overhead visibly worse:

```sh
mkdir -p /tmp/raveil-showcase-small
python3 -m raveil showcase prepare --workspace /tmp/raveil-showcase-small --scenario control-small
python3 -m raveil showcase run --workspace /tmp/raveil-showcase-small --scenario control-small
```

## What each stage means

`prepare` creates deterministic, deliberately unsorted ordinary text files.
The work is an independent `sort INPUT > OUTPUT` for each file, admitted by the
existing fixed OSS tool allowlist, resolved binary hash, direct argv, controlled
environment, finite policy, and `shell=False`. It does not execute `sh -c` or
look up an arbitrary executable through ambient `PATH`.

`run` first displays the graph's nodes, edges (zero for this fan-out), and
critical path (one sort). It then performs three same-input/same-output paths:

1. source-order sequential direct baseline;
2. direct `|||` fan-out with the same worker cap as the candidate; and
3. ready-set Command Graph execution with that identical cap.

Exact output hashes, stdout/status, and declared outputs must agree before a
candidate is displayed. This equal-concurrency control matters: a difference
from the sequential baseline alone is only a parallelism difference, not a
Graph-specific result. The printed candidate-only delta/speedup is an observed
single smoke value, explicitly not a performance claim.

The output separates parser/construction, execution, validation/end-to-end,
and the baseline-first evaluation total. Running every baseline is useful for
fair evaluation but is not a production speedup.

## Incremental walkthrough and Experience

The first `showcase-incremental` run caches each output only after a private
direct-versus-graph semantic comparison. Cache identity includes the complete
node recipe (including hash-bound tool identity), active input SHA-256, and
payload SHA-256. `mutate` retains the original input and exclusively creates a
deterministic replacement for one selected input. The second run re-hashes
every cache payload, reuses only entries whose recipe and input hash still
match, and separately validates each changed node through direct and Graph
execution. It prints `executed`, `reused`, and `invalidated` node lists.

This is a **showcase-only validated derived-artifact cache**. The production
`CommandGraphExecutor` does not yet reuse nodes, so the output says
`production_reuse=not-implemented`; T-0104 owns any proposal to promote it.
The baseline-first comparison still runs during this development walkthrough,
so even this cache demonstration must not be presented as a deployed fast path.

Experience has no integration point here. Its displayed status is
`not-connected`: no retrieved record or learned proposal can admit a command,
choose concurrency, validate semantics, decide reuse, or commit output. In the
current Native implementation, Graph and Experience execute on the same normal
host ARM64/x86-64 ISA as any other process. Any benefit can only arise from
ordinary software effects—work avoidance, parallel scheduling, streaming, or
validated reuse—not from a special Raveil instruction set or ASIC.

## Evidence boundary

This guide is `host-development-smoke` / `development-non-claim`. EXP-0004 is
still Planned and requires a frozen claim manifest, fair ordinary baselines,
sufficient repetitions, and immutable raw evidence before any crossover claim.
Negative or no-win observations are valid and must be retained.
