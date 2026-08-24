# T-0044/S14 common-memory strategy inventory

Status: Non-authoritative engineering review
Date: 2026-08-24
Task: T-0044/S14
Decision context: ADR-0048, ADR-0050, ADR-0061
Evidence class: public-source and provenance triage; not physical evidence or legal advice

## Question and boundary

T-0044/S13 stopped before EXP-0011 allocation because the pinned physical
image contains no required Liberty timing or LEF geometry/pin view for any of
the seven byte-identical common memory macros. This read-only review asks
whether a public source already supplies the exact view set or whether an
identically bound common standard-cell memory is immediately available.

The review does not download or adopt artifacts, change the common-memory
denominator, allocate or freeze EXP-0011, run synthesis or P&R, or establish
license, patent, freedom-to-operate, physical, performance, FPGA, ASIC, or
silicon evidence.

## Authoritative repository packet

- `docs/experiments/receipts/T-0044-EXP-0011-physical-input-readiness.json`
  binds the byte-identical seven-macro contract and zero Liberty/LEF result.
- `raveil/t0044_integrated_rtl.py` owns the exact names, dimensions, ports,
  pins, masks, and fail-closed readiness validation.
- `hardware/chisel/check-exp0011-macro-views.sh` owns the deterministic pinned
  search predicate.
- ADR-0048 requires an identical common implementation and physical condition;
  ADR-0050 governs evidence sealing; ADR-0061 limits S14 to read-only triage.

The required contract is not a generic total bit count. It includes
`cc_dir_ext` 1024x128 mrw, `cc_banks_0_ext` 16384x64 rw,
`data_arrays_0_ext` 512x256 mrw, `tag_array_ext` 64x88 mrw,
`tag_array_0_ext` 64x84 mrw, `data_arrays_0_0_ext` 512x128 mrw, and
`memory_ext` 1024x32 separate masked-write/read behavior, with their recorded
mask granularities and pins.

## Public-source observations

The following primary sources were inspected on 2026-08-24:

- VLSIDA OpenRAM `stable` at
  `b2b069ce119d1488cbe6883b2240bceb5c7ce29a` describes a BSD-3-Clause SRAM
  compiler that can generate layout, netlist, timing, power, and P&R views:
  <https://github.com/VLSIDA/OpenRAM/tree/b2b069ce119d1488cbe6883b2240bceb5c7ce29a>.
  It is a potential generation substrate, not a verified seven-macro result.
- Efabless `caravel_mgmt_soc_litex` at
  `503eda0790085712ffef7f4ad8934c7daed3237f` shows public Liberty and LEF use
  for `sky130_sram_2kbyte_1rw1r_32x512_8`:
  <https://github.com/efabless/caravel_mgmt_soc_litex/blob/503eda0790085712ffef7f4ad8934c7daed3237f/Makefile#L663-L665>.
  That is one differently named 32x512 1rw1r macro, not the required seven-set.
- OpenRAM issue 298 was open and unchanged since 2026-07-17 when inspected. It
  reports a 0.04 ns input-pin `max_transition` in the generated Liberty for
  that 32x512 macro and an infeasible OpenROAD slew check:
  <https://github.com/VLSIDA/OpenRAM/issues/298>. This is an issue report, not
  a generally established defect or a characterization of Raveil's macros.
- The SkyWater SKY130 SRAM build-space repository at
  `be33adbcf188fdeab5c061699847d9d440f7a084` documents an Apache-2.0 public
  build space:
  <https://github.com/google/skywater-pdk-libs-sky130_fd_bd_sram/tree/be33adbcf188fdeab5c061699847d9d440f7a084>.
- The SKY130 PDK rules at
  `7198cf647113f56041e02abf3eb623692820c5e1` state that the process SRAM cells
  are hard-IP-specific and prohibit using their cells or devices outside the
  specific IP:
  <https://github.com/google/skywater-pdk/blob/7198cf647113f56041e02abf3eb623692820c5e1/docs/rules/device-details.rst#sram-cells>.

No exact-name search or inspected public source supplied a verified
Liberty-plus-LEF set for all seven required names, dimensions, ports, pins,
masks, technology, and PVT conditions. This is **no candidate identified**, not
proof that no candidate exists.

## Disposition

S14 closes as a bounded negative inventory. T-0044/S13 remains Blocked and
EXP-0011 remains unallocated and unfrozen. OpenRAM may be evaluated only in a
new pre-data proposal that generates all required views and demonstrates exact
functional, port, mask, PVT, physical, and provenance compatibility. A common
standard-cell memory rewrite is likewise a denominator change, not a drop-in
asset.

Before either path starts, the Project Manager must handle HCI-06 for external
dependency, license, provenance, and patent risk; HCI-08 for the memory/fairness
design fork; HCI-04 if identity, PVT, or pin equivalence cannot be preserved;
and a fresh HCI-02 immediately before any EXP-0011 allocation or claim-bearing
freeze. Qualified legal review remains necessary before any license, patent,
or freedom-to-operate conclusion.
