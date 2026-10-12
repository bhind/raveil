# ADR-0116: MF01 execution and complete output in Sonatine/QEMU

Status: Proposed
Date: 2026-10-11
Task: T-0212 local candidate
Context: ADR-0107, Proposed ADR-0114 and ADR-0115; EXP-0002 regression evidence

## Scope

Continue the owner-requested software/simulation work using existing tools.
The candidate remains unpublished, outside canonical main; no accepted ADR,
Issue/Project state, Sprint, or gate advancement is invented. T-0210 supplies
MF01 semantics. T-0211 supplies the separately executed RTL comparator.

## Transport and execution

A freestanding C validator/interpreter admits the same65 configuration words,
2x324 input words,8 affine views,16 instructions,16x16 output and64 reduction
extent. Arithmetic is unsigned modulo2^32. It accepts a frozen boot request at
0x87ff0000 on the existing single-hart128MiB virt platform. The existing GEMM
magic/path remains separate. No guest RTL device is introduced.

The little-endian envelope has32 header bytes: magic0x51464631,version1,
totalBytes,lenA,lenB,reserved0 (six uint32), then nonzero uint64 request ID.
65 MF01 words follow, then contiguous A and B input words, CRC32 over preceding
bytes and end marker0x46454e44. Total size is300+4*(lenA+lenB), at most2892.
Length/configuration agreement, zero reserved fields, CRC and end marker are
required. CRC detects accidental corruption, not malicious modification or
identity forgery. A wrong magic is not routed to this backend.

Inputs are frozen kernel-owned boot data, not admitted user capability objects.
Fixed program/graph/contract identities identify this interpreter version;
they are not program content hashes. Existing resource fields govern registered
object references; placeholder runtime/input/scratch values do not meter actual
interpreter execution or kernel storage. No resource-accounting claim follows.

## Full output through existing authority

Up to256 uint32 outputs occupy one or two objects of at most512 bytes. Each is
registered version1, staged privately and included in a single completion.
Program approval follows successful admitted interpreter execution; one
plane_data_finalize publishes all output objects as version2. Existing authority
checks every generation/version before copying any visible byte. Readback
precedes UART publication. Failure exposes no output words in the result frame.
No object-size or max-object authority bound changes.

The program authority trusts the interpreter: the independent Python SSA oracle
checks the complete UART output on the host AFTER guest commit. This is not an
independent semantic oracle inside Sonatine, nor a two-phase host approval.

## Evidence and limits

Host adapter freezes request, descriptor, inputs and kernel, captures command,
QEMU version output, stdout/stderr and verifies every output against SSA before
atomically sealing receipt.json. Timeout/failure remains unsealed. Verification
reconstructs the request and checks metadata, fixed evidence class, command and
hashes without executing. These local hashes are integrity aids, not signatures
or hostile-host authenticity. The kernel ELF is bound as bytes; provenance from
source is supplied by the accompanying build/source manifest, not ELF parsing.

Separate QEMU and RTL runs use the same descriptor/input and are compared with
SSA. Evidence classes remain qemu-emulation-correctness and
RTL-functional-simulation. This is not QEMU/RTL co-simulation, asynchronous
transport, physical hardware, timing, energy, novelty or Groq superiority.
