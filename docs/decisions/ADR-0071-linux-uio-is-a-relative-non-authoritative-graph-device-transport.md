# ADR-0071: Linux UIO is a relative non-authoritative Graph-device transport

Status: Accepted
Date: 2026-08-31
Task: T-0132/S06

## Context

ADR-0067 assigns the three owned Graph-device ABIs to one relative 16 KiB
AXI4-Lite aperture but deliberately leaves its absolute physical base
unassigned. T-0132/S05 can drive that aperture only through RTL simulation.
The next smallest physicalization step is to reuse the same transport-neutral
runtime from Linux without changing Graph semantics, the owned ABIs, or the
RTL.

ADR-0019 excluded `mmap` and MMIO from the first Linux socket harness, and
ADR-0039 requires another Project Manager and qualified legal review before an
actual FPGA implementation may be treated as authorized hardware evidence.
Therefore a Linux mapping boundary must be accepted separately and must not be
mistaken for FPGA success.

## Decision

Add one host-side adapter that maps the unchanged execution, affine-install,
and program-install transport interfaces onto a relative 16 KiB register-I/O
window. The shared adapter owns the only address calculation:

`relative_byte_address = namespace_base + 4 * word_offset`.

It rejects arithmetic overflow, misalignment, and every access outside the
ADR-0067 namespace bounds before performing register I/O. It does not know or
accept an absolute physical address.

On Linux, the first concrete backend may open only an explicitly supplied UIO
character-device path. It uses no pathname discovery and follows no symlink.
It opens read/write with close-on-exec and synchronous-access flags, verifies
the opened object with `fstat`, requires its major and minor device numbers to
match `/sys/class/uio/uioN/dev`, requires map 0's sysfs size to be exactly
16 KiB, and maps that relative window at UIO offset zero. Accesses are aligned
volatile 32-bit reads or writes. Object lifetime owns and releases both mapping
and descriptor.

The executable may pass the resulting adapter to unchanged
`run_selected_dag` for one already-admitted canonical Graph and seed. Linux and
UIO remain transport only: they acquire no admission, capability, publication,
Experience, reset-policy, or evidence-promotion authority.

The first runner is intentionally request-specific at build time. Host
preparation emits a fixed request record and a generated C++ header containing
the exact canonical request bytes, deterministic 324-word input, selected
catalogue Graph, and seed. Before opening UIO, the runner requires byte equality
between those compiled values and the request record, `request.json`,
`request-input.bin`, and selected input file. Runtime output files use
exclusive, no-follow creation with mode 0600; an existing path is an error,
not a truncation target. A later dynamic admission protocol must receive its
own accepted authority boundary rather than weakening these checks.

The UIO executable must not forward the selected runtime's simulation-only
summary. Even when the runtime returns zero, it labels the result only
`linux-uio-transport-unverified`, keeps Graph output unpromoted, and states
that RTL and hardware identity are not verified. Only the Verilator path may
emit `rtl-simulation-functional` or `same_rtl=1` for this slice.

Host tests may use fake register I/O and anonymous mappings to prove address
translation, bounds, and lifetime. A regular file, anonymous mapping, or other
fake backend must never produce an end-to-end Graph success marker. No
hardware-success marker or FPGA evidence class exists until an actual accepted
board path is executed and independently reviewed.

## Consequences

The same runtime can be compiled against Verilator or Linux UIO while the
relative contract and Graph semantics remain common. The simulator remains the
functional oracle for this slice; a warning-free Linux build and negative UIO
opener tests prove only host transport behavior.

The request-specific build is acceptable for this bounded MVP but is not the
eventual operator workflow: changing Graph or seed regenerates the binding and
rebuilds the small host runner. This avoids inventing a second dynamic request
parser before a real board exists.

This decision does not assign an absolute address, authorize `/dev/mem`, add a
kernel module, or define DMA, IRQ, cache coherence, IOMMU, device tree, XRT,
Vivado, bitstream, board reset, or recovery behavior. It makes no performance,
resource, AXI-certification, ARM64, KV260, FPGA, ASIC, silicon, product, novelty,
or publication claim.

An actual FPGA deployment still requires a later bounded task, an explicit
board and bitstream identity, the ADR-0039 Project Manager/legal review, and a
separate FPGA-functional evidence record.
