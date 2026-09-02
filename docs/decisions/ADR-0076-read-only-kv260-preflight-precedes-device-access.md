# ADR-0076: Read-only KV260 preflight precedes device access

Status: Accepted
Date: 2026-09-02
Task: T-0139

## Context

T-0138 identifies KV260 plus Ubuntu Server 24.04 arm64 as the tentative first
board target, but the target kernel, FPGA manager and UIO exposure have not
been observed.  The existing Linux UIO runner validates its opened device and
map before execution, which is necessary for transport safety but too late for
an operator-facing readiness check: opening or mapping a wrong device must not
become the way Raveil discovers that the host is unsupported.

The repository also must not turn planning metadata or a host inspection into
FPGA-functional or performance evidence.

## Decision

Add `python3 -m raveil graph-device kv260-preflight --device /dev/uioN` as a
read-only, fail-closed target inspection.  Before any later transport may open
the supplied device, the preflight requires:

- Linux `aarch64` and a bounded kernel-release identity;
- a canonical `/dev/uioN` path whose `lstat` result is a character device;
- exact major/minor agreement between that path and
  `/sys/class/uio/uioN/dev`;
- one 0x4000-byte, 0x4000-aligned UIO map 0;
- a bounded NUL-terminated device-tree model containing `KV260`; and
- a bounded FPGA-manager state at `/sys/class/fpga_manager/fpga0/state`.

The implementation may read only those fixed procfs/sysfs properties and use
`lstat` on the explicit device path.  It must not call `open` on the device,
map it, issue MMIO, discover alternate devices, load firmware or overlays, or
change the target.  The success marker includes a hash of the model string,
the observed identities and explicit `device_opened=0`, `mmio=0`,
`evidence=target-host-observation`, and `performance=not-measured` labels.

The preflight is necessary but not sufficient for a device run.  The existing
opened-object checks in ADR-0071 remain authoritative after open; callers must
not treat a prior preflight as a stable capability or skip revalidation.

## Consequences

The physical owner can determine whether a booted target exposes the minimum
expected Linux surfaces without granting Raveil access to the UIO aperture.
Failures are ordinary diagnostics and cannot partially execute a Graph.

There remains a time-of-check/time-of-use interval between this observation
and a future UIO open.  It is deliberately closed by revalidation in the UIO
transport, not by weakening the preflight or retaining a file descriptor.

This decision assigns no absolute address, device-tree binding, bitstream,
load route, clock, reset, firmware or package identity.  It proves no Vivado,
UIO execution, FPGA function, performance, resource, security, ASIC, silicon,
commercial-readiness, novelty, patent or freedom-to-operate claim.
