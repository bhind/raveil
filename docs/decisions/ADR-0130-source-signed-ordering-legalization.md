# ADR-0130: Explicit signed ordering legalized into existing MF01 operations

Status: Proposed
Date: 2026-10-11
Task: T-0229
Context: ADR-0107; Proposed ADR-0125/0127/0128/0129
Adoption: owner-authorized local validation complete; canonical/public adoption pending

## Problem

The existing uint32 storage/arithmetic can carry two's-complement bit patterns,
but unsigned max cannot implement signed max or ReLU. Per-workload reinterpretation
would lose numerical meaning at source capture and saved reconstruction.

## Proposed contract

Source `raveil.mf01-grid/v4` retains v2 fields and permits an optional v3-shaped
`post` map. Both maps accept explicit `max_i32(a,b)` and `relu_i32(a)` nodes,
in addition to existing operations. Input/output JSON still carries integer
bit patterns0..2^32-1; negative JSON words are not admitted. Decode bit patterns
as signed two's-complement only for these two ordering operations. Add/multiply
and sum remain modulo2^32. Existing `max`, `ge_imm`, and max reduction remain
unsigned. There is no signed reduction, saturation, float, widened accumulation,
new immediate range, implicit type inference or claim of i64 CPU equivalence.
V1/v2/v3 accepted programs and meanings remain unchanged.

## Lowering and mathematical identity

For unsigned word x, T(x)=(x+2^31) mod2^32 maps signed order to unsigned order.
Thus max_i32(a,b)=T(max_u32(T(a),T(b))) and relu_i32(a)=T(max_u32(T(a),2^31)).
T is its own inverse. The constant uses only existing allowed instructions:
GE_U32(a,0)=1; (1+32767)*(1+65535)=2^31. Build it once per map, then reuse it.
Reserve all public SSA names before allocating generated names. Validate original
SSA topology/fields, lower deterministically, then use ordinary admission on the
expanded map. The15-node/8-register, input/shape/session, authority and evidence
limits are unchanged. Reject overcapacity; do not spill, omit nodes or add jobs
silently. An optional explicit post still adds exactly one ordinary dependency job.

The untiled source oracle directly decodes signed integers and uses Python max;
it never consumes transformed operations, constants, register allocation or
encoded instructions. Saved proof recompiles the frozen original source and binds
it to captured children under the existing workspace verification.

## Initial verification and historical hold

Initial eight host tests passed boundary pairs, random words, partitions, name
collisions, explicit unsigned semantics, source immutability and composed formulas.
A separately started55-test run had54 passes and one test-helper AttributeError
(`project.loads` does not exist). At that point the helper import was corrected but had not been rerun.
At the initial closeout, QEMU/RTL acceptance was prepared but not executed. Automatic approval review
rejected its launch as a material signed-numeric scope expansion requiring explicit
owner approval. No alternate execution path is used. The exact local proposal was
pending owner disposition at that point; the original packet remains preserved.

The initial remaining acceptance included actual boundary/overflow/partition cases, signed
GEMM+bias+ReLU composition, injected post rejection, saved no-execution checks,
strict semantic-rewrite rejection, original-version compatibility and final
record/packet reconciliation. Finite functional checks are not performance,
physical hardware, Groq advantage, novelty or proof for all programs.

## Owner-authorized resumed verification

The owner explicitly approved T-0229 correction and local QEMU/RTL validation.
A clean T-0233 base retains all later proof/admission fixes and adds the numeric
proposal. The corrected earlier test-helper import passes. 203 selected host tests
pass; nine actual parents execute14 sessions/17 jobs, with16 approved jobs and one
injected post rejection. Eight complete parents publish240 final words. A15-map-node
case occupies16 encoded instructions including the final fold; repeated max retains
the original operand. Full-range GEMM+bias wraps before signed ReLU, independently
checked against unbounded Python products/sums followed by modulo32 interpretation.

All actual parents revalidate. Four changed numerical meanings, with parent source,
lowering, plan, output and hashes consistently rewritten, fail captured-child binding.
Thirty-six legacy parent paths (35 distinct payloads) revalidate without execution.
No guest/RTL/ISA changes or physical/performance/newness claim follows. Local
validation is complete; this proposed ADR awaits separate canonical adoption.

## Additional generated interaction evidence

T-0229's generated-01 continuation leaves the proposed contract unchanged.
Seed 229 produces 1,000 sources, 2729 admitted tested partitions and
51,094 matching words. Twenty-four numerically sensitive representatives
pass 24 actual coupled sessions/36 jobs/850 words. Independent signed
counterfactuals and per-input interventions prevent insensitive selections from
standing in for signed coverage. Scope limits are recorded in STATUS and the log.
