# ADR-0024: Linux userspace MVP precedes specialized authority

Status: Accepted
Date: 2026-08-11

## Context

Raveil has accumulated two useful executable lines: a substantial RV64/QEMU
Sonatine Microkernel authority seed and host-side measurement, contract, Linux
transport, and Experience infrastructure. The EXP-0003 fixed-C and pinned-TVM
campaigns closed the preregistered 5% transfer hypothesis negative. They did
not test the complete graph-admission, semantic-check, execution, rollback, and
evidence loop that is the product concept.

Separate preserved branches explored a commodity-host-first, GNU/Linux and
OSS-first pivot and a userspace graph MVP. Those branches predate later main
work and cannot be merged wholesale without deleting verified Sonatine,
contract, Linux, and telemetry artifacts. They also reused identifiers that main later
allocated independently, so their records are design provenance rather than
canonical authority.

Requiring a particular ISA, a new kernel, a kernel driver, or custom hardware
before the first complete product loop delays the central evaluation. No
current measurement proves that Sonatine or RISC-V improves latency, energy,
area, cost, or isolation enough to justify that prerequisite.

## Decision

The next delivery line is an OS/ISA-neutral Raveil-owned vertical slice running
first in GNU/Linux userspace. Apple Silicon/macOS remains a supported
development host, including a Linux container or VM where useful. Existing OSS
is preferred behind owned, versioned adapters when license, provenance,
security, and IP-review state are recorded.

The minimum vertical slice admits one owned graph and execution contract,
constructs bounded objects and variants, executes a trusted baseline and a
replaceable candidate backend, performs structural and semantic checks,
abstains when evidence is insufficient, and exercises explicit commit or
rollback with segregated evidence.

All current artifacts remain preserved. Sonatine Microkernel (Sonatine) remains a
verified RV64/QEMU authority backend and research asset, but it is not a
prerequisite for the userspace MVP. The Linux harness, shared contracts,
Sonatine job rings, telemetry, and metadata-shadow finalization remain valid
implemented slices. A specialized kernel, RISC-V control target, FPGA, ASIC,
or native Daphnis Execution Subsystem may become a primary path only after a
bounded comparison demonstrates a material benefit.

The preserved `feat/t-0086-linux-graph-mvp` branch is an implementation donor,
not a merge target. Its graph-MVP code and tests must be reviewed and ported
onto current main without deleting or weakening later work.

Feature releases are immutable integration points. The published
`v0.0000000000001` tag remains the historical minimum seed. Development after
that tag is `unreleased` until a defined feature boundary, acceptance tests,
records, and release evidence are complete. The next feature release increments
the final decimal unit; no existing tag is moved or repurposed. Independently
verified delivery milestones receive immutable annotated
`milestone/<record-id>-<short-slug>` tags even when they are not public feature
releases.

## Consequences

- ADR-0003 remains an architectural exploration option but no longer makes
  RISC-V/Sonatine an MVP prerequisite.
- ADR-0007's two seeds remain preserved; its sequencing implication is
  superseded.
- ADR-0019's Linux transport implementation remains valid, while its ban on a
  non-authoritative Linux userspace product loop is superseded. Linux still
  cannot bypass owned admission, semantic, evidence, and rollback contracts.
- Gate 4's smallest userspace vertical slice may advance before the remaining
  Gate 3 specialized-authority work. Passing it does not waive Gate 3.
- T-0034, T-0085, VirtIO, kernel drivers, FPGA, and ASIC work are paused until
  the userspace MVP identifies a concrete need.
- OSS licensing does not establish patent clearance. Vreji continues the
  read-only similarity/IP inventory and escalation under ADR-0014.

## Verification and supersession

The first closeout target is a clean-main GNU/Linux userspace execution of one
owned graph through baseline, proposal or abstention, structural/semantic
validation, commit or rollback, and evidence output. Native macOS, Linux
container/VM, QEMU emulation, simulation, FPGA, and silicon results remain
separate evidence classes.

A later ADR is required to make a specialized kernel, ISA, device transport,
or hardware backend mandatory.
