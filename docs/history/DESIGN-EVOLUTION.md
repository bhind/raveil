# Design evolution

Classification: historical synthesis; not implementation authority

Historical wording below is preserved. For the current formal component names,
see the [Glossary](../GLOSSARY.md).

This document records how the Raveil direction changed. Current facts live in
[STATUS](../STATUS.md), accepted decisions in
[ADRs](../decisions/README.md), and unresolved proposals in
[RFCs](../rfcs/README.md).

## From scheduler simplification to an explicit machine contract

The initial discussion compared RISC-V, VLIW, dataflow, and OoO execution. It
then moved upstream: known dependencies and effects should be represented in an
execution contract rather than repeatedly recovered from a sequential
instruction stream. Classic VLIW was not selected because exact schedules are
brittle under cache misses, variable latency, branches, and hardware-width
changes. The current explicit graph/effect direction remains Proposed in
[RFC-0001](../rfcs/RFC-0001-native-explicit-graph-machine.md).

## Permanent RISC-V control and fallback

RISC-V changed from a possible bootstrap vehicle into the permanent
boot/control/exception/admission/fallback architecture. Daphnis became a
separate implementation plane for measured structured work. This avoided an
all-or-nothing claim about eliminating OoO execution. The accepted boundary is
recorded in [ADR-0003](../decisions/ADR-0003-risc-v-control-and-daphnis-execution.md).

## Four authority planes

Adding AI-generated optimization made ordinary code/data separation
insufficient. Program semantics, installed graph configuration, mutable data,
and accumulated Experience gained separate write authorities. The safety rule
became: AI proposes; trusted non-AI components verify, measure, commit, and
roll back. See
[ADR-0001](../decisions/ADR-0001-four-plane-adaptive-harvard.md) and
[ADR-0002](../decisions/ADR-0002-experience-advises-measurement-governs.md).

## Experience as project memory

The optimization target changed from a one-shot winning binary to an auditable
lineage of contexts, candidates, measurements, failures, and decision
boundaries. Online retrieval became bounded while cold evidence remained
append-only. Later discussion added economic allocation and a proposed
multi-policy Adaptive Council.

## Practical bootstrap and language split

An earlier broad prototype reportedly contained C++20 host/runtime seeds, a
planned Rust `no_std` policy core, Python research tools, Chisel RTL seeds, and
RV64 firmware. No `previous/raveil` artifact exists in the current tree, so
these claims are historical provenance rather than inspectable implementation.

The project rejected a Rust-everywhere rule. Rust is reserved for small trusted
invariants where it materially helps; C++20, Python, Chisel, and C follow their
accepted responsibilities in
[ADR-0004](../decisions/ADR-0004-languages-follow-responsibility.md).

## Reset to two executable seeds

On 2026-08-07 the project reset to `v0.0000000000001`: a freestanding RV64
Sonatine shell/authority seed and a Python bounded-Experience loop using
analytical ToyDaphnis. The reset intentionally excluded production LLM, GNN,
TVM, RTL, and hardware-performance claims.

## Repository memory and environment validation

The 2026-08-08 migration converted conversation knowledge into STATUS, TODO,
ROADMAP, ADR, EXP, RFC, and chronological records. macOS/IntelliJ work also
corrected several CLion-derived assumptions: the observed IntelliJ C/C++ plugin
used Custom Build Targets, the kernel entry symbol is `kmain`, and the
original ELF lacked source debug sections.

The reconstructed source discussion remains in
[archive](../archive/conversations/2026-08-07-08-digest.md).
