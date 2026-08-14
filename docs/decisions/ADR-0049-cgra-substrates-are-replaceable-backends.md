# ADR-0049: CGRA substrates are replaceable backends

Status: Accepted
Date: 2026-08-15
Task: T-0044
Related: ADR-0006, ADR-0039, RFC-0004, RFC-0005, EXP-0008, EXP-0009

## Context

The current `StaticStencilRegion` is a repository-owned, hardwired five-point-
stencil FSM. Its Chisel source fixes the load/add/store sequence, affine address
offsets, iteration count, and state transitions. The descriptor SHA-256 is
exposed as a binding tag, but the RTL does not consume arbitrary descriptor
nodes or schedules. It is therefore a specialized static accelerator reference,
not a configurable CGRA and not a general installed Graph executor.

Replacing those source-coded transitions with loadable schedules, configurable
functional units, programmable routes, or token-driven readiness would enter
established temporal-CGRA, VLIW, spatial-CGRA, or dataflow mechanism classes.
T-0057 already records high similarity to those classes. Reimplementing them
under Raveil names would not establish differentiation, even if the result beat
Rocket or BOOM on the one fixed stencil.

Raveil nevertheless needs a portable execution boundary. Its plausible system
distinction is the lifetime of a bounded operation/dependency/effect/object
contract: construction and admission, object/version authority, resource
limits, semantic validation, cancellation, unpublished output, publication,
fallback, rollback, and replayable evidence. Those rules must not depend on one
configurable fabric or a new closed compiler ecosystem.

## Decision

Treat CPU, VLIW, CGRA, NPU, FPGA, and future ASIC implementations as
replaceable execution backends behind Raveil-owned versioned contracts. A
backend configuration, completion, compiler mapping, or learned proposal never
grants Program, Data, execution, publication, or Experience authority.
Sonatine and the owned contract/admission/finalization boundary retain those
responsibilities; Linux remains a non-authoritative development and driver
host under ADR-0019.

Use existing frontends, interchange formats, compiler infrastructure, and
source- and license-reviewed public CGRA work before creating equivalents.
Raveil-specific compiler work is limited to thin adapters and passes for owned
identity, effects, object/version bounds, resource certificates, provenance,
admission, backend lowering, and semantic/fallback bindings. Do not require a
new Raveil source language, forked general optimizer, or end-to-end proprietary
toolchain when an upstream IR or adapter can preserve those fields. Upstream
types remain private adapter state under ADR-0006 and ADR-0032.

Name mechanisms truthfully. A source-generated per-kernel FSM is a specialized
accelerator or HLS-like result. A schedule-memory executor is temporal
VLIW/CGRA-like control. A configurable processing-element array is a CGRA. A
token-ready array is elastic/dataflow machinery. None is Raveil novelty merely
because it accepts a Raveil descriptor.

Before any T-0044 `go` can authorize a custom configurable Graph executor,
RISC-V extension, FPGA transition, or ASIC transition, a separately frozen
CGRA non-reinvention gate must establish all of the following:

1. At least one source-, revision-, license-, and provenance-verified public
   VLIW/CGRA/dataflow implementation or faithful reproducible control is in the
   direct comparison. Open-source copyright permission is recorded separately
   from patent and freedom-to-operate state.
2. One candidate interface loads at least three semantically distinct operation
   graphs, with different topology and memory behavior, without editing or
   regenerating Chisel/RTL or changing the hardware source. Different input
   bytes, constants, shapes, or repetition counts do not satisfy this rule.
3. The same owned contract and exact effect/output expectations execute through
   an ordinary CPU backend and the configurable backend, including rejection,
   cancellation, unpublished failure, fallback, and publication checks.
4. Compilation, placement/routing or scheduling, configuration bytes and time,
   installation, execution, memory traffic, fallback crossings, area, timing,
   and energy proxies are accounted for against the hardwired FSM, matched CPU,
   and public configurable control.
5. The record identifies a contract-lifetime or authority property that is not
   supplied by merely renaming an existing CGRA mapper/runtime, and demonstrates
   that property independently of backend performance.

The custom-hardware branch is `no-go` if any of these conditions holds:

- changing the admitted graph still requires RTL/Chisel source regeneration;
- its claimed advantage disappears when compared with an equally programmable
  VLIW/CGRA control under matched resources and full configuration cost;
- a reviewed existing backend supplies the execution mechanism and the custom
  hardware adds no measured PPA, enforcement, integration, or evidence benefit;
- general readiness, routing, replay, alias, or commit machinery recreates a
  general OoO/dataflow engine outside the accepted resource bound; or
- use requires a closed Raveil-only frontend or optimizer despite an adequate
  standard-IR adapter path.

A custom-hardware no-go does not kill Raveil. It pivots Daphnis to a portable
software contract/runtime over existing CPU and reviewed configurable backends.
Conversely, strong fixed-FSM PPA does not by itself authorize a configurable
executor or a Raveil hardware-novelty claim.

## Experiment and transition boundary

This decision does not alter, reinterpret, or retroactively add a threshold to
the frozen EXP-0008 or EXP-0009 manifests. EXP-0009 may finish its already
frozen static Graph/Rocket physical-proxy screen. Survival opens only the
CGRA non-reinvention experiment above; it does not open FPGA, ISA, ASIC, or
product implementation.

The smallest next configurable candidate, if T-0044 reaches that point, is a
temporal schedule-memory executor with bounded functional units and no general
runtime issue machinery. A spatial array is not the default next step. Public
CGRA source may be inspected, reproduced, or adapted only after the existing
Vreji/Project-Manager source, license, prior-art, and IP-risk boundary. Public
availability never establishes patent clearance or freedom to operate.

## Consequences

Raveil may become a system that uses a CGRA, and a Daphnis backend may honestly
be a CGRA. Raveil itself is not defined by ownership of a novel array. Its
portable thin waist is the versioned contract and authority lifecycle across
software and hardware backends.

This narrows custom compiler and RTL scope, makes public toolchains comparison
controls and potential dependencies rather than ideas to rewrite, and preserves
CPU-only usefulness if configurable hardware is rejected. It also raises the
bar for a hardware research claim: the current static result remains a useful
specialization reference but cannot establish general Graph execution.
