# ADR-0067: Graph-device ABIs use one relative AXI4-Lite aperture

Status: Accepted
Date: 2026-08-29
Task: T-0132/S01

## Context

Raveil already owns three transport-neutral, 32-bit word-addressed contracts:
the execution ABI, affine-configuration installation ABI, and bounded-program
installation ABI. The next vertical slice needs one control-plane transport
that can later be driven by Linux or an FPGA host without assigning a board-
specific physical address or changing any existing ABI byte.

Issue #55 required this decision before implementation. A seven-file candidate
was nevertheless prepared before ADR-0067 existed. That candidate had no
decision authority and is retained only as implementation provenance. It may
be accepted only after this record is accepted, its behavior is reconciled to
this decision, and the complete exact-head acceptance and independent replay
pass. The ordering defect is not evidence that the earlier candidate was
correct.

## Decision

Map the three existing ABI namespaces into one relative 16 KiB byte aperture:

- execution: `[0x0000, 0x2000)`;
- affine configuration: `[0x2000, 0x3000)`;
- bounded program: `[0x3000, 0x4000)`.

The absolute base remains unassigned. Within each namespace, an existing ABI
word offset maps to `namespace_base + 4 * word_offset`. Existing ABI files
remain byte-identical.

The first adapter is 32-bit, little-endian, and accepts only full-word writes
with `WSTRB=0xf`. It permits one total in-flight transaction across read and
write channels. AW and W are captured independently; a partial write capture,
an outstanding R or B response, or a reset barrier blocks admission of the
other transaction class.

Response classes are fixed as follows:

- aligned, mapped, valid S01 access: `OKAY`;
- aligned access to a decoded hole, unsupported S01 register, wrong access
  mode, invalid control value, or partial write: `SLVERR` without mutation;
- misaligned or outside-aperture access: `DECERR`.

External active-low `ARESETn` clears wrapper state, the unchanged
`StaticStencilRegion`, and all captured or outstanding AXI state. The only S01
write with authority is execution `CONTROL.reset` with its exact reset bit and
full strobe. The wrapper first retains `BVALID/OKAY` until the owner accepts
the B response. Only then does it apply a bounded core-only reset barrier. No
new AW, W, or AR request is admitted while either the response or barrier is
outstanding. The next identity and status reads must show execution idle with
no output authority and the factory affine/program installations restored.

S01 exposes only identity, version, status, payload-or-I/O counts, and the
execution reset above. Execution data windows, digests, installation payloads
and controls, start, and cancel remain decoded but unsupported and return
`SLVERR`. S02 and S03 require separate promotion before enabling full windows
or an operator runtime.

The implementation wraps the real current `StaticStencilRegion`; it does not
copy vendor HDL or introduce a behavioral stand-in.

## Consequences

- A later platform may assign an absolute base without changing the relative
  register contract, but that assignment needs its own accepted boundary.
- One deliberately narrow AXI4-Lite control path can be tested through actual
  RTL pins while the existing execution and installation ABIs stay transport-
  neutral.
- The single-outstanding rule and full-word-only writes simplify the first
  wrapper; bursts, partial writes, DMA, IRQ, coherence, and Linux driver work
  remain outside this decision.
- Passing Chisel/Verilator evidence is `rtl-simulation-functional` only. This
  ADR establishes no AXI compliance certification, performance, resource,
  FPGA, ARM64, ASIC, silicon, general-Graph, publication, or product-readiness
  claim.
