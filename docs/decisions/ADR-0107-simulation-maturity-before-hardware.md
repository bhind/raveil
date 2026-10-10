# ADR-0107: Mature the simulation implementation before acquiring hardware

Status: Accepted
Date: 2026-10-10
Task: T-0204 / Issue286; implementation successor T-0197 / Issue266
Authority: owner explicitly requested QEMU/Chisel implementation until the
system takes shape, then approved repository and GitHub Project reflection.
Supersedes: ADR-0105 immediate hardware/host-inventory delivery ordering only.
Preserves: ADR-0105 affordable eventual implementation/measurement objective,
ADR-0106 board boundary, existing numerical/admission/rollback contracts and
all historical research/experiment outcomes.

## Decision

Make a usable, reproducible simulation implementation the current objective.
Do not make Windows inventory, Vivado availability, board ownership or mapped
resource reports prerequisites for ordinary software and RTL development.
Defer hardware acquisition, vendor setup and physical bring-up until the
implementation-maturity review below. Keep initial incremental spend zero.
This changes ordering; it neither abandons eventual hardware nor restores a
novelty requirement. Groq superiority remains unproven, not a delivery gate.

Use Chisel for owned RTL and Verilator for its functional execution. Use QEMU
for supported Sonatine/RISC-V software paths. Current `raveil/project.py`
requires graph-device recipes to use `rtl-sim`; `sonatine-qemu` currently admits
only GEMM dimensions1..8. These are separate backends. No existing QEMU/Chisel
co-simulation, common device model or end-to-end hardware equivalence is implied.
If coupling is needed, scope an explicit interface task; do not require a new
large co-simulation platform before the next useful increment.

## Implementation-maturity review before hardware work

Require an evidence packet showing:

1. A user can edit inputs and computation, check, execute, inspect saved output
   and compare runs without editing generated RTL or losing prior snapshots.
2. Multiple semantically different admitted Graphs run on the same RTL with
   independent oracle and C++ fallback agreement. Program edits do not require
   an architecture rebuild for each job.
3. One frozen input produces two named private child results. Parent success
   requires every child to pass; failure/cancel keeps diagnostic evidence but
   never publishes a complete result set. Retry is a fresh attempt.
4. Invalid inputs/resource bounds, backpressure, cancellation, reset during
   execution and recovery have explicit reproducible checks at their relevant
   backend boundary. A host mock is not RTL or QEMU execution evidence.
5. Source/tool identities, exact commands, a runnable demonstration and known
   limits are recorded. Distinguish host functionality, QEMU emulation and RTL
   simulation; none establishes FPGA clock, fit, energy or application speed.

Some of these behaviors already exist; this ADR does not declare the combined
review passed. T-0197 provides the missing bounded parent-result implementation.
After the review, re-open T-0188 host/budget readiness then T-0189 physical work.
Review does not automatically authorize purchase, install, license acceptance,
programming, or pass a historical performance gate. A later performance claim
still needs its own frozen EXP and matched comparison.

## Next implementation and boundaries

Restore existing T-0197/#266 as the single next implementation after this
planning integration. Follow accepted T-0183 planning: ordered host composition
of one/two existing single-output Graphs, unchanged STORE/ABI, freeze input once,
private child evidence and all-or-incomplete parent publication. The concrete
pair is raw `x*x mod 2^32` and biased `(x*x+17) mod 2^32`. Preserve single-output
CLI compatibility. T-0196 supplies optional compiled-simulator reuse, not result
reuse or shared arithmetic. Require the implementation ADR and failure/cancel
checks before runtime acceptance, plus an actual RTL demo. Do not claim speedup.

T-0186 standard-IR work remains a later bounded candidate, not parallel WIP.
The S04 per-byte-valid RAM idea remains unaccepted; do not turn speculative
physical optimization into the primary product task. Preserve existing memory
semantics and the diagnosis for later evidence-based selection.

T-0188/#194 and the unfinished physical part of T-0189/#195 remain Backlog,
explicitly deferred by sequence, not missing-user-information blockers on
current development. Completed T-0189/S01-S04 and their evidence remain intact.
Existing S-0005 weekly Review stays postponed and unaccepted; adding a reporting
iteration or delivering a task does not accept any weekly ceremony.
