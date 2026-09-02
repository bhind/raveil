# ADR-0072: Vendor-neutral RTL export precedes board integration

Status: Accepted
Date: 2026-09-02
Task: T-0132/S07

## Context

T-0132/S05 proves one admitted Graph request through the relative AXI4-Lite
top in RTL simulation. S06 reuses the same runtime through a checked Linux UIO
transport, but deliberately leaves the board and absolute address unassigned.
The next physicalization step must make the exact RTL closure portable without
allowing a vendor tool, board wrapper, or stale earlier T-0112 design to replace
the current accepted top.

ADR-0039 still prohibits treating FPGA implementation as authorized evidence
without a new Project Manager and qualified legal review. Therefore the export
boundary must remain independently useful and explicitly short of FPGA work.

## Decision

Export only the current repository-owned `GraphDeviceAxi4LiteTop` closure as
vendor-neutral SystemVerilog. Run two elaborations from the same exact source
in the existing immutable, offline Chisel environment and require their sorted
file-name/SHA-256 manifests to be byte-identical. Copy only the emitted `.sv`
closure into the final bundle.

The bundle also binds the three owned ABI identities, the relative 16 KiB
aperture and generated header, complete exporter/source identity, toolchain,
immutable image ID, recursive file manifest, and an exclusive-create receipt.
Local publication is allowed only below repository `artifacts/`; replacement,
links, special files, unbounded files, incomplete closure, changed current
source, or receipt/manifest drift fails closed.

The receipt fixes `absolute_base=unassigned`, `board=unassigned`,
`evidence_class=rtl-export-functional-prerequisite`, and
`performance=not-measured`. Export does not run a board tool or assert that
the RTL is synthesizable, placed, routed, timed, resource-feasible, connected
to Linux, or functionally correct on FPGA.

## Consequences

A future board slice receives one reproducible current-main RTL input instead
of reconstructing or silently substituting the design. Board wrappers and
vendor tools remain downstream adapters and gain no Graph, admission,
execution, publication, or evidence authority.

Vivado projects, clock/reset and pin constraints, absolute addresses, device
tree, UIO execution, XSA/XCLBIN/bitstream identity, FPGA oracle equality,
resources, timing, power, KV260/product claims, and external source reuse remain
outside this decision. They require a separately bounded task and the
ADR-0039 review before implementation or evidence promotion.
