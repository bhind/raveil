# ADR-0073: Runtime request admission stays inside the frozen catalogue

Status: Accepted
Date: 2026-09-02
Task: T-0132/S08

## Context

ADR-0071 deliberately compiled one exact Graph, seed, request record, and input
into the first Linux UIO runner. That made the transport boundary small, but it
also meant that changing an already-admitted seed or selecting another of the
three accepted Graphs required regenerating a C++ header and rebuilding the
runner. S07 now provides a deterministic RTL handoff, so this build-time
request binding is the smallest remaining software-only obstruction to trying
the same operator flow on a later board.

Broadening the Graph catalogue, program language, RTL, ABI, or board contract
is neither necessary nor authorized. The runtime admission protocol must also
fail before opening UIO so malformed host input cannot cause device access.

## Decision

Replace only the Linux runner's request-specific compiled header with a strict
runtime reader for the existing 20-byte little-endian `uio-request.bin` v1
envelope. The envelope contains magic `0x52555131`, version `1`, encoded length
`20`, an index into the generated frozen Graph catalogue, and one uint32 seed.
Every field and the exact file size must match; a catalogue index outside the
compiled three-Graph array is rejected.

Before any UIO open, the reader requires the request root's final path component
to be a non-symlink directory and requires exact regular, non-symlink input
files. It recomputes all 324
input words from the seed using the repository's deterministic input rule and
requires byte equality for `request-input.bin`, `inputs/seed-SEED.bin`, and the
fixed `inputs/seed-1.bin` consumed by `run_selected_dag`'s malformed-program
matrix before the selected invocation. Only then may it return the compiled
catalogue Graph ID and seed to the unchanged runtime.

The binary request envelope is the execution admission record for this slice.
`request.json` remains human/audit metadata produced by the existing host
preparation path, but the C++ runner does not gain a JSON parser or accept a
descriptor path, program bytes, opcode, schedule, or Graph ID from that file.
This keeps the executable request-independent without creating a second Graph
compiler or broadening the catalogue.

The three owned ABIs, relative 16 KiB aperture, generated DAG catalogue,
transport-neutral runtime, RTL, Linux UIO checks, and output non-claims remain
unchanged. Existing S05 evidence may retain its generated request header for
receipt compatibility, but the Linux executable no longer compiles or trusts
that header. The Linux build treats `GENERATED_DIR` as a trusted input but
requires its DAG header to be byte-identical to the header regenerated from the
current canonical descriptors before compiling the runner.

## Consequences

One Linux runner build can accept different Graph/seed pairs within the same
frozen catalogue. Host tests can prove admission and rejection without a UIO
device, while an ARM64 build can prove compiler compatibility. Neither is an
FPGA run, and a zero return from a future UIO invocation remains only
`linux-uio-transport-unverified` until a separately accepted board and evidence
boundary exists.

The admission reader itself checks metadata before reopening each pathname,
and `run_selected_dag` later reopens validated input paths. These check/use
windows make the path developmental; it does not claim adversarial
filesystem-race resistance or production security. Closing those gaps requires
a separate descriptor-relative or immutable-bundle design. Arbitrary Graphs,
new opcodes or schedules, ABI/RTL changes, absolute
addresses, device tree, Vivado, bitstreams, DMA, IRQ, cache coherence, real UIO
execution, FPGA evidence, and performance/resource claims remain outside this
decision.
