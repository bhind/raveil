# ADR-0131: Versioned sharing of signed-order representations

Status: Proposed
Date: 2026-10-11
Task: T-0234
Context: ADR-0107; Proposed ADR-0130
Adoption: local implementation and runtime verification complete; public adoption pending

## Trigger

A five-node source containing two dependent signed maxima then ReLU expands to
17 map nodes under v4 and fails the unchanged 15-node limit. Repeated translation
of an immutable SSA value is unnecessary. The improvement targets compiler
representation cost; it does not claim new arithmetic or hardware capacity.

## Proposed contract

Source v5 has exactly the v4 fields and numerical meaning. It explicitly selects
shared signed-order lowering for each map independently. V1 through v4 retain
existing lowering bytes and admission. Saved proofs bind their frozen version to
one deterministic compilation; no proof reader is relaxed or silently migrated.

For T(x) = x + 2^31 modulo 2^32, remember an emitted T(x) by exact original SSA ID.
A signed operation emits selected = max(T(a), T(b)) (or max(T(a), 2^31) for ReLU),
then emits the original public result T(selected). Since T is its own inverse,
selected is also T(public result) and may serve a later signed consumer.
All original public nodes remain emitted. Ordinary arithmetic uses their original
bit patterns and receives no inferred translated alias. Caches reset for kernel,
post map, compile invocation and source; no runtime-value specialization occurs.

The ordinary allocator and 15-node/8-register admission remain authoritative.
Sharing can extend lifetimes; reject any expanded map that fails ordinary admission.
No spilling, extra job, hidden buffer, dead-code elimination or resource-limit
increase is introduced. An unexercised rematerialization fallback was considered
and omitted. No claim that every v4-admissible map must fit v5 is made.

## Evidence requirements

Show v4 rejection/v5 admission, independent signed/modular outputs, partitions,
post and linked flow execution, original-operand lifetime, collision avoidance,
cache isolation, resource rejection and retained old proof compatibility. Rehashed
source-version changes cannot reuse mismatched children. Label source-node savings
separately from measured time, energy or physical performance.

## Local evidence and execution hold

46 selected host tests pass, including preserved public operands, generated-name
collisions, kernel/post isolation, unchanged v4 compiled bytes, capacity rejection,
old/new mocked workspace comparison and rehashed-version/child mismatch rejection.
The existing allocator actually rejects a nine-live-load fixture; no mocked
allocator result stands in for this admission check. The v5 conversion of 1,000
prior generated sources preserves 2,729 admitted comparisons/51,094 words and227
spatial rejections. Thirty-three retained old-version parents revalidate.

The primary prepared new chain, modular branch, post-map, linked-flow and injected
post-fault QEMU/RTL acceptance. Automatic approval review rejected the launch as
new T-0234/v5 scope requiring explicit owner approval. At that initial closeout no process started and no
alternate launch was attempted. That packet contained host-functional proposal
evidence only; the subsequent owner-directed runtime validation is recorded below.

## Owner-directed runtime validation

The owner replied “続けて” to the exact T-0234 approval packet. After reproducing
all157 file hashes, the same implementation passed fresh coupled execution:
eight parents,12 sessions,14 jobs (13 accepted,one injected post rejection),267
correct published words. A v4/v5 pair preserves49 output words and reduces15 to13
map nodes. A coherently resealed version change fails old-child binding; original
proofs remain readable without execution. The earlier local execution hold is
resolved. No source/numerical/resource change, physical claim or public adoption
follows from this bounded validation.
