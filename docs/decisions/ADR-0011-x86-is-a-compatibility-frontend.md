# ADR-0011: x86-64 is a compatibility frontend, not a native ISA

Status: Accepted
Date: 2026-08-09

## Context

Raveil needs a credible path for existing software without turning Daphnis into
an x86 microarchitecture or weakening the native explicit-graph direction.
Instruction-set, ABI, and operating-system compatibility are separate scopes,
and preserving x86-visible behavior does not require reproducing an x86
pipeline internally.

## Options considered

- implement x86-64 as a native physical ISA;
- translate x86-64 into a conventional fallback instruction stream only;
- treat x86-64 as an input language that is lifted through an explicit,
  validated compatibility boundary;
- defer all legacy compatibility and require native Raveil programs.

## Decision

Treat x86-64 as an optional compatibility frontend, never as Raveil's native
execution contract. A future frontend may decode and lift supported binary
regions into Raveil-owned semantic and effect representations, then submit
validated work through the same GraphVariant, MemoryPlan, measurement, and
Experience boundaries as other untrusted proposal sources.

Compatibility requirements remain explicit in an `ExecutionContract`. In
particular, x86-visible memory ordering such as x86 TSO is enforced at the
compatibility boundary and MUST NOT become the global native Raveil memory
model. Exact physical timing remains elastic and dynamic.

RISC-V remains the permanent trusted control, baseline, cold-code, irregular,
and fallback path established by ADR-0003. A cached translation or Experience
record is advice: identity, contract, semantic validation, measurement, and
rollback checks still govern its use.

Linux x86-64 userspace is the first candidate compatibility environment.
Windows compatibility and arbitrary existing binaries are outside the initial
scope. No x86 frontend is currently implemented.

## Rationale

This preserves software migration as a frontend concern while keeping native
Raveil semantics freer than a legacy ISA. It also allows repeated compatible
regions to reuse verified execution knowledge without claiming that all code
can be graphed or that runtime uncertainty disappears.

## Consequences

- ISA semantics, ABI behavior, and OS personality require separate contracts
  and tests.
- The frontend and lifted representation are untrusted until structural,
  effect, contract, and semantic validation succeeds.
- Self-modifying code, JITs, binaries, libraries, runtimes, and hardware
  changes must invalidate incompatible Experience records.
- Cold or graph-hostile regions may remain on a generic compatibility or
  RISC-V fallback path.
- Broad compatibility claims require differential and memory-model evidence;
  architecture intent is not implementation evidence.

## Verification and supersession

RFC-0003 defines the proposed staged implementation, metrics, and falsification
criteria. Any future decision to make x86 native, impose x86 TSO globally,
remove the RISC-V fallback, or promise a broader initial OS scope must
explicitly supersede this ADR.

