# T-0042 BOOM reference source and diagnostic review

Status: source pin verified; RTL execution not yet run
Date: 2026-08-12
Evidence class: upstream-source verification; not legal advice or performance evidence

## Exact packet

| Item | Exact locator | Finding |
|---|---|---|
| Chipyard release | `ucb-bar/chipyard` `ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1`, tag `1.11.0` | Parent integration coordinate |
| BOOM gitlink | Chipyard `.gitmodules` plus tree entry `generators/boom` | Official origin `https://github.com/riscv-boom/riscv-boom.git`, gitlink `9459af0c1f6847f8411622dac770ac78fe10847c` |
| Initial control config | Chipyard `generators/chipyard/src/main/scala/config/BoomConfigs.scala`, `SmallBoomConfig` | One `WithNSmallBooms(1)` tile; not yet resource-matched |
| Small BOOM resources | BOOM `src/main/scala/common/config-mixins.scala`, `WithNSmallBooms` | Decode width 1, 32 ROB entries, three 8-entry issue queues, 52 integer and 48 floating physical registers, 8-entry LDQ/STQ |
| Diagnostic definition | BOOM `src/main/scala/common/parameters.scala`, `BoomCustomCSRs` | Chicken CSR bit 3 defaults to zero and is named `disableOOO` |
| Diagnostic consumer | BOOM `src/main/scala/exu/core.scala`, `wait_for_empty_pipeline` | Forces dispatch to wait for empty ROB/LSU; structures remain instantiated |
| CSR address | Rocket Chip `src/main/scala/tile/CustomCSRs.scala` at the same Chipyard-selected Rocket revision | `chickenCSRId = 0x7c1`; bit mask is `0x8` |

The local ignored sources were checked detached and clean. The owned verifier
also checked the Chipyard parent gitlink and exact origin URLs. This packet is
reconstructable through `hardware/chisel/fetch-boom-reference.sh`; it is not a
vendored source copy.

## License and reuse boundary

BOOM `LICENSE` is BSD-3-Clause with SHA-256
`0dff9c3cc0950c7ae66a0d88eec0cee96a978d0bb3525a9cddc309fcd860b004`.
BOOM `LICENSE.SiFive` is Apache-2.0 with SHA-256
`63b453c2c3f5e5d31007f55eaacc2b72e8b7a40e6ab33eae6972ba010fa7acc4`.
The external checkout retains both. Raveil-owned code invokes and observes the
control through owned scripts and schemas; no BOOM RTL was copied into the
static Graph candidate.

These notices establish a copyright-license boundary for the inspected files,
not the scope or applicability of any patent claim. No novelty,
non-infringement, legal status, or freedom-to-operate conclusion is recorded.

## Engineering interpretation

The diagnostic changes dispatch behavior within the same BOOM design. It may
help separate some dynamic overlap effects while holding the compiled design
constant, but it retains OoO structures and their area/static-power cost. It
also does not make BOOM resource-identical to Rocket. Valid future reporting
must therefore keep three distinct labels:

1. `rocket-in-order`: separate in-order control;
2. `boom-ooo`: ordinary BOOM control;
3. `boom-ooo-disabled-diagnostic`: same BOOM RTL with serialized dispatch.

No ratio among them is authorized until the exact workload, scratchpad, clock,
functional resources, lifecycle accounting, correctness checks, and simulator
observation points are matched under T-0044.

## Remaining gaps

- BOOM and its transitive build dependencies have not been elaborated or run.
- No repository-owned immutable Chipyard 1.11.0 build environment exists yet.
- The RFC-0005 bare-metal fallback and chicken-CSR diagnostic program are not
  yet compiled or executed on BOOM.
- BOOM/Rocket do not yet emit `raveil.simulation-adapter/v1` records.
- No common fixed-latency scratchpad, synthesis constraint, or activity counter
  has been integrated.
