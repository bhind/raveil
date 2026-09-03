# ADR-0077: Bounded dynamic programs use the existing Graph-device ABIs

Status: Accepted
Date: 2026-09-02
Task: T-0140

## Context

The current Graph compiler already validates a bounded descriptor and lowers
it to the 32-word program-install payload accepted by ADR-0064. The Chisel
program installer and sequential executor validate and execute that payload
without consulting a Graph name. Nevertheless, every operator request is
admitted through the three-entry compiled catalogue, so the current working
demo does not prove that a newly compiled bounded Graph can configure the same
executor binary at runtime.

Broadening the RTL, device ABIs, opcode set, affine shapes or catalogue is not
required to test that missing compiler-to-executor connection. Nor is a
persistent simulator service required to distinguish one reusable binary from
per-Graph RTL generation.

## Decision

Add a separate simulation-only dynamic-program request and operator command.
The host request is fixed-size and pointer-free. It carries one uint32 seed,
one of the two already accepted affine-profile payloads, and one complete
32-word program-install payload produced by the existing bounded compiler.
The host envelope is not a fourth device ABI and does not enter RTL.

Before any AXI transcript is created or Verilated model is constructed, the
host reader must validate the direct request root and fixed files, exact
header/version/size, deterministic seed input, affine profile identity, and
the program's existing magic, version, capacity, opcode, dependency, final
store and reserved-zero rules. The Graph-device still repeats its own
installer checks after AXI writes; host admission does not replace hardware
validation.

`graph-device dynamic-run-pair` accepts exactly two ordered descriptor/seed
pairs. Both descriptors are validated and compiled before the lower runner
starts. The initial proof must use one catalogue descriptor and one
repository-authored descriptor absent from the catalogue, while restricting
both to an existing affine profile and the accepted five selectors, three
opcodes, 16 instructions and eight value registers.

The lower runner elaborates and compiles `GraphDeviceAxi4LiteTop` once and
invokes the byte-identical simulator executable for both admitted requests.
Each request retains a private AXI transcript, output, independent descriptor
oracle, software fallback and append-once receipt. A shared simulator digest,
not a shell success line, proves reuse. The existing `run` and `run-pair`
catalogue boundaries remain unchanged.

## Consequences

Raveil can directly test the core proposition that Miroirs compiler output
configures one Daphnis executor without regenerating RTL for that Graph. This
is a bounded generality result: it is stronger than selecting among three
embedded programs but much weaker than an arbitrary Graph language or dynamic
scheduler.

The first implementation may build once per pair invocation. It does not add
a persistent cache, daemon, concurrent execution or batch scheduler. It does
not authorize the dynamic host envelope for Linux UIO; a physical transport
requires a separately accepted request, identity and recovery boundary.

This decision makes only RTL Simulation Functional claims. It changes no RTL,
device ABI, opcode, selector, affine profile, memory window or scheduling
policy and establishes no performance, area, energy, ARM64, UIO, KV260, FPGA,
ASIC, silicon, product-readiness, novelty, patent or legal-clearance result.
