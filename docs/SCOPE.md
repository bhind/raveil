# Scope of v0.0000000000001

## Included invariant

Experience is advice, never authority. A candidate must be measured in the target context before it can become the best result. The trusted baseline is always the first measurement and remains available when every proposed variant fails.

Sonatine Microkernel (Sonatine) is the authority boundary. Even in this first RV64 seed, IPC resolves a generation-checked capability owned by the calling task before it touches an endpoint.

## Included Sonatine Microkernel boot slice

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
- Miroirs Graph Compiler/Pavane Semantic Oracle admission checks;
- real compiler transformations;
- parallel execution;
- neural latent representation;
- adversarial training;
- ANN or accelerator hardware;
- multi-objective Pareto selection;
- crash-safe database transactions.

## Next version gate

This file defines the boundary of `v0.0000000000001`; it does not own future
task or gate state. See [ROADMAP](ROADMAP.md) for exit conditions and
[TODO](../TODO.md) for current actionable work.

The next implementation must preserve the existing trusted-baseline and
`measure(context, candidate) -> Metrics` boundaries unless an accepted ADR
supersedes them.
