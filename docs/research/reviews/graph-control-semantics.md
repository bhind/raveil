# T-0181 Graph arithmetic and predicate decision spike

Status: Planning recommendation; no implementation or adoption authority

Task: T-0181

Evidence class: Planning

## Result

Recommend exactly one next implementation candidate: `GE_IMM_U32`, an unsigned
compare against a bounded immediate that returns canonical uint32 zero or one.
Do not implement it under T-0181. A separate accepted task and ADR must version
the compiler, installed program, request, C++ validation and RTL together.

The recommendation comes from one program that the user can see and edit:
threshold raw 8x8 intensity data and then apply T-0185's cross-neighborhood
binary dilation in the same Graph. Five loads, five comparisons, four MAX
reductions and one STORE occupy 15 of the current 16 instruction slots.

## Current boundary

The current language has 16 instructions, eight value registers, uint32 values,
one final STORE and eager fixed-schedule execution. Binary arithmetic has two
source fields. `ADD_IMM_U32` has one source and an unsigned 22-bit immediate.
There is no type tag, condition state, implicit flag, source-free value or
conditional effect. Descriptor v4, program v5 and dynamic request v6 reject
unknown operations; T-0181 does not change that behavior.

## Three attempted programs

| Candidate | Concrete rejected program | Exact current result | Honest workaround | Decision |
|---|---|---|---|---|
| Full-width/source-free `CONST_U32` | Fill 8x8 output with `0xF1234567` | Unknown opcode; using `ADD_IMM_U32` rejects the value above `0x3fffff`; a full 32-bit literal does not fit the current unary-immediate word | Put duplicated values in the input snapshot and LOAD them, or preprocess on the host; neither installs a constant | Defer. A multiword literal or constant-pool design changes program counting and decode/PC or memory semantics. Estimated relative implementation risk: 5–8+ SP. |
| Unsigned saturating subtraction | Dark-frame correction `max(sample - dark, 0)` | `SUB_SAT_U32` is an unknown opcode; current arithmetic cannot express subtraction or negation | Preprocess on the host | Defer. A binary opcode is relatively contained, but it unlocks less of the current editable experience. Estimated risk: about 3 SP. |
| Bounded unsigned comparison | Threshold each of center/north/south/west/east at 100, then cross-dilate | `GE_IMM_U32` is an unknown opcode | Convert all 324 inputs to zero/one on the host, then run T-0185 dilation; the interesting threshold semantics disappear outside the Graph | Recommend for a separate implementation decision. It composes directly with T-0185 and fits 15/16 instructions. Estimated risk: 3–5 SP. |

The fixtures and exact rejection strings live in
`tests/fixtures/graph_device_dynamic/rejected-workloads/`. Their checker proves
15 hand-calculated truth vectors, five proposed-rejection vectors and the exact
current failures. They are proposed semantics, not executable Graph descriptors.

## Proposed `GE_IMM_U32` semantics

For source `x` and immediate `t`:

```text
result = 1u32 if unsigned(x) >= unsigned(t) else 0u32
```

- `x` is an existing uint32 value.
- `t` is an unsigned integer from 0 through `0x3fffff`; booleans, negatives,
  non-integers and larger values are rejected, not truncated.
- The true path is exactly uint32 `1`; the false path is exactly uint32 `0`.
- There is no overflow, signed interpretation, type propagation or implicit
  predicate register.
- The source is evaluated eagerly. Comparison does not skip loads, arithmetic,
  STORE or any other effect. The sole final STORE remains unconditional.
- Every descriptor dependency remains explicit. This is a value-producing
  comparison, not control flow and not general SELECT.

Truth table for threshold 100:

| x | result |
|---:|---:|
| 0 | 0 |
| 99 | 0 |
| 100 | 1 |
| 101 | 1 |
| `0xffffffff` | 1 |

The separate maximum-immediate boundary vector uses `x = t = 0x3fffff` and
returns 1. Proposed rejection vectors cover boolean, negative and `0x400000`
thresholds, an undefined source and opcode 7 under old program version 5.

## Proposed encoding and compatibility policy

If separately accepted, descriptor v5 and program v6 would assign opcode 7.
The 32-bit word would reuse the unary-immediate shape:

```text
[31:28] opcode=7 | [27:25] destination | [24:22] source | [21:0] threshold
```

Dynamic request v7 would carry program v6 with an explicit 324-word snapshot;
the proposal is snapshot-only, like current program v5. Old descriptor schemas reject
`GE_IMM_U32`; program versions 1–5 reject opcode 7; old request/program pairs
remain exact. A v5 descriptor with threshold `0x400000`, an undefined source,
wrong trace immediate or cross-version request must fail before execution.
Program capacity, payload-word counting, value-register count, affine windows,
input/output transport, final-STORE rule and eager scheduling remain unchanged.

An implementation acceptance packet must cover descriptor oracle, installed-
program software fallback, independent C++ admission/execution, Chisel RTL,
Garden lowering, old-byte compatibility, maximum threshold, version failures
and actual RTL equality. It must not claim speed, area, energy, FPGA or silicon.

## Why not general SELECT now

A general select needs condition, true value and false value: three inputs,
while the present instruction format and allocator expose at most two sources.
A two-input conditional-zero instruction is cheaper, but still needs a producer
for the threshold condition. RISC-V Zicond demonstrates this distinction: its
conditional-zero operations use two source registers and preserve dependencies,
while a full conditional select is synthesized from multiple instructions.
RISC-V RV32I similarly makes comparisons explicit value producers (`SLT` and
`SLTU` yield zero or one). These are semantic references, not copied code:
[RISC-V Zicond 1.0](https://docs.riscv.org/reference/isa/v20260120/unpriv/zicond.html),
[RISC-V RV32I 2.1](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html).

Signed/saturating arithmetic also needs a narrower decision than its label
suggests. The RISC-V vector specification separates signed and unsigned
saturating operations and exposes accumulated saturation state. Raveil should
not accidentally import type, rounding or flag state with one vague opcode:
[RISC-V Vector Extension 1.0](https://docs.riscv.org/reference/isa/unpriv/v-st-ext).

## Prior-art and IP boundary

Comparisons, conditional-zero, saturation and constant materialization are
standard ISA mechanisms. No external code, specification text, test data or
encoding was copied. The cited specifications only sharpen the semantic
comparison. Patent families, jurisdictions and freedom to operate are
unreviewed; Apache-2.0 does not establish patent clearance for external
mechanisms. Reassess with qualified legal review before hardware or commercial
promotion. No novelty claim follows from this planning recommendation.
