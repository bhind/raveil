# ADR-0132: Automatically partitioned integer array programs

Status: Proposed
Local scope: owner-authorized implementation and UT
Date: 2026-10-11
Task: T-0235
Context: ADR-0107; proposed ADR-0128 and ADR-0131; EXP-0002 integration follows UT

## Decisions fixed before implementation

The owner requests all phase-one decisions now and implementation plus unit tests
without further clarification. This record fixes that endpoint. Public adoption
and QEMU/RTL integration remain distinct from local UT completion.

| Decision | Selected contract |
| --- | --- |
| Common input | Strict `raveil.array-program/v1` JSON: named static stages and requested outputs; each stage has inputs, shape, boundary, kernel and optional post; no authored tiles or execution jobs. |
| Shapes and composition | 1..8 stages, 1..8 inputs per stage, 1..8 distinct stage outputs, shapes 1..64 by 1..64. Inputs are grid-input/v2 literals or `{from: stage}` links. Stable lexical topological stage order; cycles and missing producers reject. |
| Scalar language | Dependency-ordered SSA; load, add, mul, unsigned max, add_imm, unsigned ge_imm, max_i32, relu_i32. Preserve even unused nodes. At most 128 source nodes including post across all stages. |
| Numbers | uint32 bit patterns; arithmetic and sum wrap after every operation. Signed max/ReLU reinterpret the current wrapped bits. Unsigned22-bit immediates. No floating point, saturation, widening or inferred signedness. |
| Coordinates | Existing nonnegative affine row/column/step coefficients 0..63, offsets -63..63; zero/clamp/wrap. 1..8 views per kernel. Fold extent 1..64; sum or unsigned max. Post sees only `reduced`. |
| Partition | Deterministically materialize every scalar node as a full array pass. Stream fold indices and reduce on the backend after each map; first map result initializes the accumulator. Post runs after the entire fold. |
| Backend | Each pass is existing grid/v5 with fixed 16x16 tiles, identity or one scalar operation. Existing ISA, register, map, session and proof rules remain unchanged. |
| Data movement | Host gathers original affine samples into contiguous planes from frozen literals or verified predecessors. Host production path performs no arithmetic results; this is not device affine gathering. |
| Global admission | At most 128 passes, 128 sessions, 32,768 generated output-word evaluations, 65,536 conservative logical working-plane words. Reject before creating an attempt. These limits are operational, not optimal or measured. |
| Lifetime | Plan last uses; release each temporary after its final consumer; pin requested output producers through publication. Count all literal input words, live planes, operand packing and the current result conservatively. This is not a bound on Python RSS. |
| Storage | Retain the existing 128 MiB / 16,384-entry hard inventory ceiling. Preflight known capture copies plus a stated reservation; check inventory during execution. Future logs are not statically bounded: overflow leaves an unsealed attempt, never success. |
| Execution | Serial passes; capture source/plan/kernel/runtime; reload and bind each child before dependent execution. No learned authority, cache, concurrent writer, restart-in-place or hidden recomputation. |
| Failure | Incomplete child stops the exact scheduled prefix and suppresses every requested output, including otherwise completed outputs. Exceptions/cancellation/uncertain cleanup remain unsealed. Retry creates a fresh attempt and preserves prior evidence. |
| Saved evidence | Recompile plan and reconstruct every exact child source from frozen source and verified predecessors, require common executables and exact prefix/inventory; recheck independent whole-source oracle before success. No process execution on read. |
| Compatibility | New source/parent schema and array CLI; grid/flow v1..v5 contracts and saved readers retain meaning and bytes. |
| UT endpoint | Compiler, independent interpreter, liveness/bounds, actual existing backend admission, mocked sealed-child coordinator, CLI, tampering/failure/retry and affected legacy host regressions all pass. No UT fixture is QEMU/RTL evidence. |
| Deferred | QEMU/RTL integration/system tests follow UT. Hardware purchase, general MLIR/model import, dynamic control, float, optimization and Groq superiority are not phase-one UT conditions. |

## Consequences

Long expressions and high source-level live-value counts require no hand-written
partition or new RTL. Materialization, host gathering and repeated sessions can be
expensive. This is a complete correctness-first implementation within explicit
bounds, not an efficient accelerator or a novelty/performance result. A source
within syntactic limits can exceed expanded-work or capture limits and reject.
There are no remaining user decisions blocking this local implementation/UT scope.

## Verified local UT closeout

Primary verified33 new and253 legacy host tests:286 distinct IDs, no failures,
errors or skips. New coverage includes128-node maps, nine simultaneously needed
values, shapes up to64x64, independent GEMM/transpose/boundary/fold/post results,
all operators,60 deterministic generated combinations, strict grammar, liveness,
resource boundaries and existing backend admission. Coordinator tests exercise
verified linkage, saved reinspection without processes, tampering, failure/retry,
source freezing, capture overflow, interrupted publication and CLI dispatch.

Independent source review found a missing session runtime-copy term. Primary
verified the execution path, fixed byte and entry multiplicities and added both
before-attempt regressions. Final read-only review found no material blocker.
These are host tests with mocked child execution, not new QEMU/RTL evidence.
Raw commands/logs and test-ID/source hashes are in the T-0235 candidate evidence
directory. This local UT endpoint is complete; public adoption remains Proposed.

## T-0236 end-to-end functional continuation

The owner directed completion beyond the UT-only milestone. The unchanged common
source and compiler now pass actual QEMU/RTL across18 workload/boundary families,
including every source operation and maximum shape/input/stage/output cardinalities.
Primary verified27 sealed parents,177 sealed DAG sessions/jobs and4562 published
words;3 intended incomplete parents suppress outputs and1 cancelled unsealed
attempt is recorded separately. This resolves the earlier deferred local QEMU/RTL
integration work. Future numeric/import/control features and public adoption remain
distinct. No new architectural boundary or commercial/performance claim follows.
See EXP-0002, STATUS and docs/log/2026-10-12.md for exact evidence boundaries.
