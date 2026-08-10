# ADR-0019: Linux is a non-authoritative driver-development host

Status: Accepted
Date: 2026-08-11

## Context

Linux accelerates driver and transport development, but ADR-0003 permanently
assigns boot, admission, capabilities, recovery, and trusted fallback to
RISC-V/Sonatine. No real Daphnis device or shared JobDescriptor exists yet.

## Decision

Linux is a development and contract-validation host, not Raveil execution
authority. The first harness runs without root in user space and communicates
over a mode-0600 Unix `SOCK_SEQPACKET` socket. It accepts one same-UID client,
one copied fixed-size request, and one completion at a time.

The Raveil-owned v1 ABI contains magic, version, exact structure size, bounded
opcode, zero-required flags, request ID, and scalar argument/result. It contains
no pointer, path, file descriptor, credential, PID, capability handle, physical
address, Linux-private structure, or Experience write. Only PING and test NOP
exist; these are not JobDescriptor or Daphnis execution.

Kernel modules, networking, `ioctl`, `mmap`, shared rings, DMA, MMIO, IRQ,
IOMMU, PCI, VirtIO, device reset, real job admission, and telemetry ingestion
require later tasks and accepted boundaries. Linux never bypasses Sonatine's
future validation, capability, commit, cancellation, or rollback authority.

## Consequences

The protocol core can be tested on the macOS development host, while daemon
build/runtime evidence requires Linux. A future kernel adapter may reuse the
versioned owned ABI but must not silently promote Linux to authority.

## Verification

Host tests enforce ABI sizes, version/size/flags/opcode rejection, one-inflight
backpressure, request-ID preservation, completion consumption, and reset.
Linux `make smoke` must compile warning-free, create the private socket, verify
same-UID peer credentials, complete PING, and remove the endpoint on normal
shutdown.
