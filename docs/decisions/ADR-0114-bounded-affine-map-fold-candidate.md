# ADR-0114: Bounded affine map/fold RTL candidate

Status: Proposed
Date: 2026-10-10
Task: T-0210 candidate; no public Issue, Project item or delivery branch
Context: ADR-0107 simulation-first; ADR-0112 remains the integrated grid contract.

This is a local review candidate, not accepted or integrated.

## Problem and direction

Host tiling and composition preserve the old core's one-input, per-cell,
shape-preserving execution boundary. They cannot directly express a binary
join, dot product or matrix product in RTL. The owner asked for substantially
greater generality and an eventual advantage over Groq. This candidate widens
the computation supported by one small execution engine. It does not establish
novelty, efficiency or a Groq advantage.

Use a bounded structured region:

    for i,j in output shape:
        accumulator = 0
        for k in reduction extent:
            value = scalar_program(affine_views(inputs, i,j,k))
            accumulator = sum_mod_u32_or_unsigned_max(accumulator, value)
        private_output[i,j] = accumulator

Map-only operations use extent1. Zero strides express broadcasting; exchanged
strides express transpose; a reduction index expresses dot products and matrix
products. Views, shape, extent and scalar instructions are runtime configuration
of the same RTL. This is a known structured-loop mechanism, also reflected by
MLIR Linalg's indexing maps and parallel/reduction iterators.

## Separate MF01 contract

Do not reinterpret the existing stencil instructions or installer. New
standalone AffineFoldRegion samples65 configuration words once on idle start.
Words0..8 are magic0x4d463031,rows,columns,extent,fold,lengthA,lengthB,
viewCount,instructionCount. Eight five-word views occupy9..48:
buffer0/1,offset,iStride,jStride,kStride. Sixteen instruction slots occupy49..64.
Unused views/instructions must be zero. Bounds:

- rows/columns1..16, extent1..64, fold0(sum)/1(max);
- two immutable input spans, each0..324 words, at physical word offsets0/324;
- eight views maximum, nonnegative offset/strides0..323, whose exact maximum
  address must lie within the selected input span;
- two to16 instructions and eight uint32 registers; at most15 map instructions
  followed by one YIELD; one contiguous private output at648, at most256 words.

Opcode31:28 is LOAD1, ADD2, YIELD3, MAX4, MUL5, ADD_IMM6 or GE_IMM7.
Destination27:25, sourceA/view24:22, sourceB21:19 or immediate21:0.
Reserved bits must be zero; YIELD has no destination; all operands must have
been defined during the current map. Arithmetic wraps modulo2^32 at every
operation and sum fold. MAX/comparison are unsigned. Both fold identities are
zero; empty reductions and floating point are unsupported.

Configuration admission precedes all memory effects. The Python compiler
accepts dependency-ordered SSA nodes and uses liveness-based allocation;
register pressure beyond eight rejects without spilling. The reference
interpreter executes SSA dependencies without interpreting encoded instructions.
Caller-owned data must remain immutable for the execution; this bare core does
not enforce memory ownership against another master.

## Transaction and cancellation boundary

One Decoupled request and one response may be outstanding. Request address,
direction and data remain stable until acceptance. There is no fixed response
latency in the correctness contract. The environment must eventually accept
and answer requests for progress; no deadline is promised.

Configuration changes and start pulses while busy have no effect. Cancellation
before an offered request stops immediately; after an offer it retains the offer
and drains its response before completing cancelled. A write accepted before
cancellation can modify private output memory. Success remains false and that
memory has no publication authority. An error response similarly prevents
success. Completion flags persist until the next accepted idle start.
Reset requires a coordinated reset/drain of the memory responder, not an
assumption that an old outstanding response disappears.

## Adoption and limits

This is a separately executable local proposal, not a replacement for the
workspace backend. No AXI/Linux/UIO/QEMU coupling, program composition adapter,
MLIR parser, negative strides, data-dependent addresses, arbitrary loops,
multiple outputs, SIMD throughput or floating-point implementation is included.
No FPGA or silicon result, physical fit claim, performance EXP or gate decision.
T-0209's reviewed snapshot stays independent and unchanged.

Automatic approval review previously rejected public T-0209 registration as an
unapproved concrete scope expansion. No retry, public registration or integration
is inferred from this new local candidate. Adoption requires a concrete owner
decision and the normal Issue/Project/branch/review path.
