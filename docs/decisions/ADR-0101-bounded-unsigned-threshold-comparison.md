# ADR-0101: Bounded unsigned threshold comparison

Status: Accepted

Date: 2026-09-19

Task: T-0182

## Context and authority

The owner explicitly approved the T-0181 recommendation and T-0182 simulation
implementation. This resolves the opcode-selection HCI, not Sprint acceptance
or physical-device authority. ADR-0097 remains the historical v5 addition
contract; this decision adds a new version rather than rewriting it.

## Decision

Descriptor v5 and installed program v6 admit `GE_IMM_U32`: unsigned source
greater than or equal to an unsigned 22-bit immediate yields uint32 1,
otherwise uint32 0. Boolean, negative, fractional and oversized immediates
are rejected. Opcode 7 uses destination bits 27:25, source bits 24:22 and
immediate bits 21:0. The opcode occupies bits 31:28.

Program v6 retains existing arithmetic including ADD_IMM_U32. Dynamic request
v7 admits program v6 only, with a 324-word explicit snapshot and seed zero.
Old descriptor/program/request pairs retain their exact acceptance and bytes.
The existing immediate-aware lowering trace v2 also describes comparison.

This is an eager value operation, not control flow. Sixteen instructions,
eight registers, fixed affine windows, 32 payload words and one unconditional
final STORE remain unchanged. Sealed UIO admission is not extended.

## Acceptance and resource boundary

Require independent oracle/fallback agreement for all 256 output words,
host-parser negative controls, old-byte regressions and one offline generic
RTL simulator identity for old/new programs. Demonstrate threshold editing,
rerun, saved-result diff and read-only Garden without altering the first run.
Use the existing local Docker image/cache; no network image pull, paid resource,
device access or performance campaign. Preserve evidence locally immediately;
ordinary Drive preservation remains weekly under ADR-0099.

## Alternatives and consequences

Host preprocessing hides the editable threshold outside the Graph. Full-width
constants require a wider encoding decision; SELECT requires another operand
or decomposition. Both remain deferred. Comparison enables a 15-instruction
threshold-plus-cross-dilation example but does not make the language general
purpose. Basic unsigned comparison is not a novelty or patent-clearance claim.
Evidence is RTL simulation functional only, not speed, area, energy or silicon.
