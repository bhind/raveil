# Raveil design principles

Status: accepted project rules
Last updated: 2026-08-08

1. **Semantics precede implementation.** Program meaning and an explicit
   ExecutionContract are immutable inputs to optimization.
2. **Experience is advice, never authority.** Retrieval, heuristics, solvers,
   and learned models may propose or rank. They cannot install executable state,
   grant rights, or declare their own result correct.
3. **Measure before commit.** A target-context measurement or shadow execution
   is required before promotion, with a trusted baseline and rollback path.
4. **Make dependencies and effects explicit.** Native Daphnis Execution Subsystem work should expose
   graph dependencies, object-bounded accesses, effects, resource requirements,
   and semantic constraints. It must not inherit a sequential register ISA as
   its native abstraction by accident.
5. **Do not pretend timing uncertainty is gone.** Readiness, backpressure,
   memory/I/O completion, and data-dependent behavior remain dynamic.
6. **Use dynamic islands deliberately.** Pointer chasing, interpreters, JITs,
   irregular control, and unpredictable traversal belong on RISC-V or bounded
   dynamic tiles when graph execution is a poor fit.
7. **Preserve evidence, including failure.** Cold evidence is append-only.
   Rejected variants, negative transfer, dissenting proposals, and failed
   experiments are retained as information.
8. **Bound the hot path.** Online Experience retrieval and policy computation
   have explicit budgets; the full historical log is not scanned synchronously.
9. **Allocate optimization economically.** Hot repeated work can earn expensive
   search. Rare work is allowed to remain generic and slow.
10. **Separate evidence classes.** Analytical, simulated, emulated, FPGA, and
    silicon observations are reported separately.
11. **Languages follow responsibility.** Rust `no_std` is reserved for small
    high-integrity invariants where it materially helps; C++20, Python, Chisel,
    and C are used where their ecosystems and roles fit.
12. **Own the contracts.** External projects may accelerate implementation, but
    Raveil owns public schemas, authority boundaries, versioning, and replay
    metadata.
13. **Advance through executable gates.** Grand architecture does not substitute
    for a small reproducible implementation and an honest comparison.
14. **Repository memory is implementation.** Code, STATUS, TODO, ADR, EXP, and
    chronological records change together.
