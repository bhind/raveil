# ADR-0034: Native interactive Session wraps the guarded graph loop

Status: Accepted
Date: 2026-08-11

## Context

ADR-0024 makes ordinary macOS/GNU/Linux userspace the first product path, and
ADR-0025 already provides a complete bounded graph loop. The reproducible
`graph-mvp` command does not let a person inspect and drive it incrementally.
Extending Sonatine first would return focus to a specialized kernel before the
userspace product interaction is evaluated.

## Decision

Add `python3 -m raveil shell` with one explicit Native Interactive Session. The
Session owns only the current GraphProgram, canonical variants, proposal,
result, and local command history. It invokes the existing GraphCompiler,
AnalyticalPredictor, Miroirs/Pavane-backed GraphExecutor, and NativeCBackend;
it cannot skip baseline-first execution, abstention, semantic validation,
commit, rollback, or fail-closed behavior.

Use Python's ordinary terminal input facilities for editing and history. Keep
the existing graph result schema and exclusive-create behavior. Sonatine stays
preserved as a later backend and authority boundary, but its shell receives no
feature expansion until this Native CLI has human evaluation.

## Consequences

The interactive grammar is a usability adapter, not a new compiler, executor,
shell language, database, or authority. Session history is ephemeral and is
not Experience. Evidence is host correctness only; this decision makes no
latency, energy, FPGA, ASIC, Sonatine-performance, or silicon claim.
