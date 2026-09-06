# ADR-0097: Bounded Graph immediate addition

Status: Accepted
Date: 2026-09-06
Task: T-0173
Related: ADR-0089, ADR-0091, ADR-0093

## Decision

The owner-approved next playable Graph increment admits ADD_IMM_U32 in
descriptor v4 and program v5. Opcode 6 uses destination bits 27:25, source
bits 24:22 and an unsigned immediate in bits 21:0 (0 through 4,194,303).
The result is `(source + immediate) modulo 2^32`. Booleans, negatives,
non-integers and larger constants are rejected, not truncated. Existing
LOAD/ADD/MAX/MUL/final STORE semantics and the first-LOAD rule are preserved.
This is not arbitrary full-width constant materialization.

Keep 16 instructions, eight value registers, 32 program payload words and
the existing bounded affine/input/output windows. The new instruction uses
one source and one destination; normal last-use allocation still applies.
Prior descriptor, program and trace bytes remain unchanged.

Program v5 selects lowering trace v2. Every entry has an explicit immediate
field: a bounded integer for ADD_IMM_U32, null otherwise. Garden validates
its exact value against the encoded word and displays unsigned wrap semantics.
Trace v1 is still required for programs v1-v4. Garden remains read-only;
saved artifact checks do not create or promote execution evidence.

Dynamic request v6 carries program v5 only, explicit 324-word input snapshots
and seed slot zero. Request v5 retains its program-v1-v4 restriction. Seeded
entry points reject program v5; project snapshots are the supported entry.
The shared runner includes both new contracts in its source manifest. Sealed
source inventories may name the new contracts but sealed admission stays
v1/v2: source identity is not execution permission. No UIO device support is
added. Historical seals are not rewritten or silently rebound to new sources.

## Alternatives and consequences

A source-free CONST node would require revisiting the first-LOAD rule and
consume a live register. Full uint32 constants need another encoding strategy.
Neither is required to let a user edit a bias and observe a changed result.
The new adder path changes RTL; functional simulation does not establish
frequency, area, energy or performance, and no EXP or hardware gate changes.

## Acceptance

Require independent descriptor oracle, encoded fallback, C++ admission and
actual offline RTL agreement. Check zero, maximum, wraparound, undefined
sources, invalid versions and trace fields, and preserved old program bytes.
Run edit/run/output/diff/Garden with changed constants. Record actual commands,
environment and source/simulator identities before technical completion.
The scheduled September 12 owner Sprint Review and subsequent retrospective
remain separate from this task's technical acceptance.
