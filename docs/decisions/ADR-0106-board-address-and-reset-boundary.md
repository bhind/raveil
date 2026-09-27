# ADR-0106: Bound board addresses and reset release outside the relative core

Status: Accepted
Date: 2026-09-27
Task: T-0189/S01 / Issue278; parent T-0189 / Issue195
Context: ADR-0105 budgeted demonstrator; no new EXP or performance claim.

## Decision

Add one owned `GraphDeviceBoardBridge` around the unchanged relative-address
`GraphDeviceAxi4LiteTop`. Its upstream integration contract is a 32-bit absolute
AXI4-Lite address within one explicitly supplied, 16-KiB-aligned window. This
is an interface requirement for later board wiring, not a claim that every
interconnect emits absolute addresses. Later wiring must verify that convention.

Compare address bits31:14 with BASE_ADDR before zero-extending bits13:0. Map
mismatches to aligned relative sentinel0xfffffffc, which the existing core
rejects as DECERR. Preserve low bits so in-window unaligned accesses are still
rejected. Comparing the high bits avoids both high-address aliasing and
end-address overflow at the final legal base0xffffc000. Misaligned parameters
select an unresolved module; simulation rejects it and the candidate synthesis
recipe also rejects black boxes. The bundle generator rejects invalid bases
before publishing. No actual board base is selected by simulation parameters.

Use asynchronous active-low assertion and two-flop synchronous release in the
single AXI/core clock domain. Gate incoming AW/W/AR VALID, B/R READY, external
AW/W/AR READY and B/R VALID until release. The first possible handshake is on
the third rising edge after reset deassertion. Reset aborts partial AW/W and
held B/R, rather than completing old requests later. External reset recovery
must quiesce/restart the master as well; AXI does not promise completion of
aborted transactions. B/R data while VALID is low carries no meaning.

PROT is explicitly ignored. This wrapper supplies no initiator isolation,
security identity, additional opcode, DMA, interrupt or semantic authority.
Existing admission, capabilities, bounded storage and numerical meaning remain.

## Source and tool boundary

A board-source bundle nests the full verified relative-core export and binds
owned wrapper/Tcl bytes, generator identity, base and target clock by hashes.
Verification requires the matching repository source. It rejects changed or
extra entries, symlinks and replacement. This is a cooperative private-directory
workflow, not a signed archive, hostile concurrent-writer defense or proof of
vendor compatibility. Different valid base/clock choices describe different
candidate bundles; they do not attest a physical design.

The provided Vivado2025.1 Tcl is an unvalidated out-of-context synthesis
candidate requiring an explicit installed part and a new output path. It
produces neither a board design nor a bitstream. A target clock constraint is
not timing closure. Vivado, physical CDC/reset timing, PS/PL wiring, constraints,
UIO mapping and recovery remain parent T-0189 acceptance work.

## Evidence and consequences

The owned testbench executes the actual exported core at three bases; host
packaging tests use an explicitly labelled stub fixture and Tcl mocks only.
See [the guide](../guides/FPGA-BOARD-BUNDLE.md) and September27 log for exact
commands/results. No FPGA/silicon/performance/novelty conclusion follows.

The mechanism is ordinary range decoding, reset synchronization and reproducible
packaging, not a new architectural claim. No external implementation is copied.
AMD UG8352025.1 `synth_design`, Usage/Arguments (`-generic`, `-mode
out_of_context`), is the command reference:
https://docs.amd.com/r/2025.1-English/ug835-vivado-tcl-commands/synth_design
Public documentation access supplies no legal-clearance conclusion.
