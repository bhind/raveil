# Scope of v0.0000000000001

## Included invariant

Experience is advice, never authority. A candidate must be measured in the target context before it can become the best result. The trusted baseline is always the first measurement and remains available when every proposed variant fails.

Sonatine is the authority boundary. Even in this first RV64 seed, IPC resolves a generation-checked capability owned by the calling task before it touches an endpoint.

## Included Sonatine boot slice

- RV64IMAC machine-mode entry on QEMU `virt`, one hart;
- `.bss` initialization and a 16 KiB boot stack;
- polled NS16550A console;
- 4 KiB bitmap physical-page allocator over a fixed 128 MiB RAM map;
- fixed 64-entry capability table with owner, type, rights, and generation;
- fixed task table containing `init` and `idle` kernel task records;
- four-message IPC endpoint with capability-checked send/receive;
- 100 Hz CLINT machine-timer interrupt and complete integer-register trap save;
- init-owned interactive Raveil shell.

Shell commands deliberately make the slice observable: `mem`, `ps`, `caps`,
`ticks`, `ipc`, and `alloc` touch the corresponding subsystem.

## Included research metrics

For baseline cycles \(L_0\), selected cycles \(L_E\), and oracle cycles \(L_C\):

\[
HCR = \frac{L_0 - L_E}{L_0 - L_C}
\]

The CLI clamps HCR to `[0, 1]`. The oracle is available only because ToyDaphnis can cheaply enumerate the five seed candidates. A real backend must treat oracle enumeration as offline evaluation, not online policy input.

## Experience storage

- Cold evidence: append-only JSONL, unbounded on disk.
- Active memory: bounded by `--active-limit`.
- Consolidation: repeated exact observations are averaged.
- Tail retention: invalid variants, negative transfer, and unusually strong improvements receive priority.
- Retrieval: weighted nearest neighbors over workload, hardware, shape, and memory budget.

This is intentionally a simple baseline. It makes later coreset, ANN, learned encoder, and near-memory implementations comparable against a working reference.

## Explicitly absent

- graph semantics and equivalence proof;
- page tables, Sv39, U-mode isolation, and PMP;
- task context switching, preemption, and blocking scheduler semantics;
- capability derivation trees and inter-task delegation;
- device-tree RAM discovery (the v0 machine contract fixes RAM at 128 MiB);
- Miroirs/Pavane admission checks;
- real compiler transformations;
- parallel execution;
- neural latent representation;
- adversarial training;
- ANN or accelerator hardware;
- multi-objective Pareto selection;
- crash-safe database transactions.

## Next version gate

There are now two independent next gates. Do not add an LLM or dedicated hardware next.

For Sonatine, move `init` into U-mode under Sv39 and make timer preemption switch between `init` and `idle`. Keep the current shell commands as acceptance probes.

For Experience, replace ToyDaphnis with one real measurable backend while preserving the boundary:

```python
measure(context: Context, candidate: Candidate) -> Metrics
```

The smallest credible next experiment is a fixed set of CPU loop variants or a TVM MetaSchedule adapter across shape holdouts. Compare:

1. cold prior;
2. full-history nearest neighbor;
3. bounded Experience;
4. random or FIFO retention.

Report HCR, measurement budget, negative-transfer rate, active-memory size, retrieval latency, and total cold-evidence size separately.
