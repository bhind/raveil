# Experience model

Status: architecture plus a minimal implemented subset
Last updated: 2026-08-08

## Purpose

Experience is the evidence accumulated while optimizing and executing work. It
includes context, candidate lineage, measurements, failures, uncertainty,
decision boundaries, and policy outcomes—not merely the current winning binary.

```text
exact reuse
  -> local transfer
  -> abstract proposal
  -> target measurement
  -> safe commit or rollback
  -> evidence and lineage update
```

## Storage hierarchy

- **Exact cache:** previously verified result for the same identity and context.
- **Bounded episodic memory:** nearby cases available to online retrieval.
- **Semantic/model memory:** slower-changing abstractions and calibrated models.
- **Cold evidence:** append-only auditable records, including failures and
  dissenting proposals.

The current Python seed implements only append-only JSONL cold evidence and a
fixed-size in-memory episodic set.

Consolidation should preserve candidate ranking, ranking reversal, failure
boundaries, negative transfer conditions, uncertainty, lineage, and Pareto
relations. Average reconstruction quality alone is not sufficient.

## Optimization budget

The conceptual return on optimization is:

```text
expected future reuse × expected saved time
  - search
  - verification
  - storage
  - risk
```

Suggested service classes are:

| Class | Default behavior |
|---|---|
| hot | aggressive optimization and repeated review |
| warm | opportunistic measured optimization |
| cold | generic execution with limited search |
| archival | do not optimize unless explicitly requested |

Optimization effort is intentionally not distributed fairly across code.

## Multi-layer policy

Cheap heuristics solve easy cases without waiting for an LLM. More expensive
policies—measured search, bandit/Bayesian methods, learned cost models,
structural proposal models, and LLM/meta-optimizers—receive a budget only when
the expected return warrants it. Periodic independent review can re-open a
stable local choice. Minority proposals and policy calibration remain in
evidence even when not selected.

No LLM is placed on the execution hot path.

## Required evaluation

For baseline latency \\(L_0\\), selected latency \\(L_E\\), and an offline
oracle \\(L_C\\):

\\[
HCR = \\frac{L_0-L_E}{L_0-L_C}
\\]

HCR must be accompanied by:

- Negative Transfer Rate (NTR);
- coverage and calibrated abstention;
- measurement budget and optimizer compute cost;
- retrieval latency and active-memory size;
- total cold-evidence size;
- latency/energy/memory/tail objectives;
- holdout type: lineage, shape, memory budget, operator composition, hardware;
- exact environment and evidence class.

Gate 1 instantiates these requirements through RFC-0002 and EXP-0003. Its
bounded-versus-cold threshold is at least 5% median improvement for both
latency and same-Mac estimated energy with paired-bootstrap 95% lower bounds
above zero. A greater-than-2% regression is negative transfer; joint NTR must
be at most 5%. Bounded latency and energy selection quality must remain within
2% of full history while respecting active memory, and bounded retrieval p95
must improve on large evidence. Offline oracle enumeration never enters online
selection.

`MeasurementRecord` evidence classes stay distinct. In particular, QEMU
telemetry is `emulation`; Apple native measurements are `silicon` scoped to the
recorded Mac; powermetrics energy is an estimate for within-Mac relative
comparison and never a RISC-V/Daphnis extrapolation.

## Principal risks

1. Contexts may be too unique for Experience to amortize.
2. The memory wall may dominate regardless of scheduling.
3. Dynamic uncertainty machinery may recreate a large OoO design.
4. Candidate search may explode.
5. Semantic or numerical equivalence may be too costly to establish.
6. Flexible Daphnis Execution Subsystem routing/configuration may lose to fixed accelerators.
7. Evidence may age, and retrieval may stop scaling.
8. Cold-start cost may overwhelm useful execution.

The first serious benchmark should attempt to falsify the thesis before FPGA or
ASIC investment.

## AI workload direction

AI graphs offer repeated structure and large amortization opportunities.
Prefill/decode separation, shape- and memory-specific variants, KV-cache and
tensor movement, MoE residency, and subgraph transfer are candidate studies.
A small Transformer that visibly changes policy as Experience grows is a
potential demonstration, not current implementation.
