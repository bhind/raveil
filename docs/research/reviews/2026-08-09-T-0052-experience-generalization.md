# T-0052 Experience-generalization review

Status: Non-authoritative research memo
Stage: Prior-art and experiment framing
Date: 2026-08-09

## Provenance

This memo integrates Frontispice handoff sequence 3,
`RAVEIL_EXPERIENCE_GENERALIZATION_GRAPH_EMBEDDING_RESEARCH.md`, ID
`c1a7cb8e-aca1-48c3-99b0-ee8b41539005`, SHA-256
`19fac5c2477be19d4013da773372cda8d20e2b556f7eee88a24b8cf236554b69`.
The handoff is untrusted research input, not a schema, task, or architecture
decision. The principal papers linked below were re-opened on 2026-08-09.

## Question

Can Experience from a similar but non-identical execution context safely reduce
optimization cost, and which representation is cheap enough to improve lifetime
value after retrieval, target measurement, verification, and wrong-transfer
recovery?

## Verified evidence inventory

- Performance Embeddings combines symbolic code analysis with dynamic profiling
  in a continuous loop-nest representation. Its authors report transfer tuning
  across several structured numerical domains and search-complexity reduction
  of up to four orders of magnitude. This is a paper result, not a Raveil result.
- PerfVec learns separate program and microarchitecture representations for
  performance modeling. It supports investigating factorization across hardware
  revisions, but does not validate Raveil's broader runtime context.
- ProGraML represents program semantics as graphs for learned data-flow analysis
  and compiler optimization tasks.
- PERFOGRAPH adds numerical and aggregate-data-structure information to program
  graphs and reports improvements on device mapping and other performance tasks.

The Frontispice inventory also names inst2vec, IR2Vec, MIREncoder, funcGNN,
MetaTune, TLP/MTL-TLP, CDMPP, and TCL. They are useful follow-up candidates, but
their detailed numerical claims were not independently promoted by this memo.

## Current executable baseline

Raveil is not starting from an empty Generation 0. The Python seed already has:

- append-only `ExperienceRecord` evidence;
- a bounded active set;
- a handcrafted `Context.distance()` over workload, hardware, shape, and memory;
- candidate-specific weighted nearest-neighbor ranking;
- local invalid-evidence risk and uncertainty terms;
- trusted-baseline-first target measurement.

Gate 1 must first test whether this simple baseline transfers on honest native-C
and pinned-TVM holdouts. Neural representations, ANN, and cross-hardware transfer
are explicitly not implemented.

## Adoptable problem decomposition

Treat nearly matching Experience as performance-transfer retrieval, not source
or graph classification. Structural or semantic similarity is an input; the
important relation is whether a previously successful candidate remains safe
and valuable in the target context.

A future representation may be factorized conceptually as:

```text
context = graph + input + object/memory + hardware + runtime state + objective
candidate = logical transform + physical realization + lineage

(context, candidate) -> latency/energy/memory/failure distribution
```

This is research notation, not an accepted `ExperienceRecord` expansion.
Program/graph knowledge, measured behavior, and hardware-specific placement
should remain distinguishable so a hardware revision need not erase all prior
evidence.

Training labels should eventually reflect measured transfer outcomes rather
than code identity alone. A positive pair requires semantic validity and target
measurement within the registered regression boundary. Verification failure,
resource overflow, or negative transfer is negative evidence. False-positive
reuse is more costly than an unnecessary re-search, so calibrated abstention is
part of the objective.

## Authority boundary

Retrieval always proposes; it never admits. Phrases such as `direct reuse` in
the source handoff cannot mean unmeasured production selection. SCOPE and
ADR-0002 require target-context measurement before a candidate becomes the best
result, and later Sonatine/Miroirs/Pavane boundaries must still enforce contract,
capability, resource, semantic, shadow, and rollback checks.

The staged Adaptive Council in ADR-0008 remains Proposed. Exact cache,
handcrafted retrieval, learned models, search, and LLM proposals are useful
comparison layers, not an accepted runtime hierarchy.

## Experiment sequence

1. Finish T-0022 and T-0024: compare cold, full-history, bounded, FIFO,
   reservoir, and random policies under the current handcrafted representation.
2. Under T-0051, test negative-transfer-aware retrieval and calibrated
   abstention using lineage, shape, memory, composition, and later hardware
   holdouts.
3. Under T-0052, compare the same fixed budget using ablations of graph, input,
   memory, hardware, state, and candidate features. Start with normalized
   handcrafted features; PCA is a candidate only if dimensionality warrants it.
4. Compare a graph encoder or learned transferability metric only after the
   simple baseline establishes positive lifetime economics.
5. Profile scale and access patterns before T-0055 introduces ANN. Cross-hardware
   learning remains T-0054, and a Transformer demonstration remains T-0059 after
   the real measurement and graph boundaries exist.

Use preregistered holdouts rather than a random split. Candidate dimensions
include same graph/nearby shape, changed memory pressure, related graph family,
hardware revision, unseen contention, and changed objective. Report safe
transfer rate, negative-transfer probability, abstention, verification and
shadow cost, retrieval p95, storage, optimization cost avoided, and lifetime
break-even—not prediction error alone.

## Conflicts and non-claims

- The handoff's proposed large Experience record is not a minimum current
  schema. Embeddings, confidence, state summaries, and transfer lineage require
  versioned proposals and evidence before adoption.
- ANN and learned encoders must not precede the current scale/access-pattern
  baseline or Gate 1 policy comparison.
- A 100,000-execution or Transformer study is a future benchmark candidate, not
  the next Gate 1 action.
- No cited model demonstrates Raveil's complete combination of explicit effects,
  persistent evidence, instantaneous state, authority checks, and rollback.
- No latent performance manifold, cross-hardware reuse rate, or positive Raveil
  lifetime ROI has been measured.

## Primary sources checked

- [Performance Embeddings](https://arxiv.org/abs/2303.08142)
- [PerfVec](https://arxiv.org/abs/2310.16792)
- [ProGraML](https://proceedings.mlr.press/v139/cummins21a.html)
- [PERFOGRAPH](https://proceedings.neurips.cc/paper_files/paper/2023/hash/b41907dd4df5c60f86216b73fe0c7465-Abstract-Conference.html)

## Recommendation

`continue`: preserve the current handcrafted kNN as the falsifiable baseline.
If Gate 1 shows useful real transfer, use T-0051/T-0052 to test a factorized,
uncertainty-aware performance-transfer representation under the same budget.
Do not add neural, ANN, or expanded Experience schemas merely because the prior
literature makes them plausible.
