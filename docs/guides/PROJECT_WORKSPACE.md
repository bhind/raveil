# Raveil project workspace

Status: T-0149 and T-0148/S02 development guide

This is the shell-first path for editing a small workload, seeing its Graph,
running it more than once and comparing retained results. Use your normal
bash/zsh, editor, Git and file tools around the `raveil project` commands.

## Create and inspect

From the repository root:

```sh
export PATH="$PWD/scripts:$PATH"
raveil project init /tmp/my-raveil-project
cd /tmp/my-raveil-project
raveil project show logs
raveil project show files
raveil project show gemm
```

The generated `recipes/` and `inputs/` files are ordinary JSON and text. The
Command recipes use only the bounded allowlisted syntax documented in
`NATIVE_COMMAND_GRAPH.md`; they do not accept arbitrary shell commands.

## Edit, run and compare

```sh
raveil project run logs
printf 'ERROR changed\n' >> inputs/events.txt
raveil project run logs
raveil project runs
raveil project diff RUN_A RUN_B
```

Replace `RUN_A` and `RUN_B` with the two IDs printed by `run` or `runs`. Each
run keeps its exact recipe and input copy, compiled Graph, output workspace and
result record under `runs/RUN_ID/`. You can inspect those files with your usual
editor or command-line tools.

Run history is cooperative local development evidence. The reader detects
later artifact mutation, but this is not a signed audit log, production cache
or hostile-code sandbox.

## Edit and execute a hardware Graph in simulation

New projects also contain `recipes/neighborhood.json` and
`inputs/neighborhood.json`. The recipe selects the descriptor and uint32 seed;
the descriptor defines the actual bounded Graph, not a catalogue demo name.

```sh
raveil project show neighborhood
raveil project run neighborhood --backend rtl-sim
```

In your editor, change the `combine` node's `op` in
`inputs/neighborhood.json` from `ADD_U32` to `MAX_U32`. Then:

```sh
raveil project show neighborhood
raveil project run neighborhood --backend rtl-sim
raveil project diff RUN_A RUN_B
```

For a third attempt, change the north load's `column_delta` from `0` to `1`
while keeping `row_delta: -1`: it now reads the north-east neighbor. Node IDs
are labels; the displayed coordinates determine the loaded cell. You can also
change the recipe seed to vary the generated input grid.

To multiply the two loaded neighbors, change the descriptor's `schema` to
`raveil.graph-device-dag/v3` and the `combine` node's `op` to `MUL_U32`.
Keep its two input IDs and the final STORE unchanged. Repeat the same
`show`, `run --backend rtl-sim`, and `diff` commands above. This explicitly
selects program/request v4; older descriptor schemas reject multiplication.
The result is the unsigned product's low 32 bits (for example,
`4294967295 * 4294967295` becomes `1`), not saturation or a 64-bit output.
ADD and MAX remain available in this version, so their nodes can be combined
with multiplication within the existing limits. This is the project execution
path; Garden's retained dynamic explanation and sealed UIO admission are not
extended to v4.

`run` verifies descriptor-oracle/C++-fallback/RTL byte equality and saves the
receipt. Inspect `runs/RUN_ID/workspace/output.txt` for active rows and
`output.bin` for the full 256-word little-endian transport window, including
inactive cells. `runs/RUN_ID/generated-input.bin` retains all 324 input words.
The descriptor and ordinary input files remain under the run's `inputs/` copy.
`diff` reports changed nodes, the number of changed active cells, the first
changed cell's values, and whether simulator/RTL/program hashes match.
The original `neighborhood` recipe keeps seed-generated input.

### Use your own input values

New projects also include the `neighborhood-data` recipe. Its version-2
recipe selects a JSON input file instead of a seed. Use `project show` to
see the exact input filename, count and identity, then edit that file:

```sh
raveil project show neighborhood-data
raveil project run neighborhood-data --backend rtl-sim
# Edit the input JSON with your normal editor, then run again.
raveil project run neighborhood-data --backend rtl-sim
raveil project diff RUN_A RUN_B
```

The input object has exactly `schema: "raveil.graph-input/v1"` and `words`:
an array of exactly 324 integers between 0 and 4294967295. No comments,
duplicate fields, floating point or booleans are accepted; limit 64 KiB.
Indices use the descriptor's input stride: an output cell `(r,c)` reads its
center at `(r+1)*input_stride+c+1`. For the compact example (stride 10),
the first center is `words[11]` and its north neighbor is `words[1]`.
For example, values 7 and 3 produce 10 with ADD; changing 7 to 9 produces 12.
The fixed storage includes halo and unused cells; do not shorten the array.

Only a JSON basename inside `inputs/` is accepted. Every run keeps the raw
JSON snapshot and the packed 324-word data used for execution. Input bytes and
their receipt hash must agree before success; previous runs remain unchanged.
Explicit runs save packed bytes as `input.bin`; old seed-based runs keep
`generated-input.bin`. Explicit-input receipts label snapshot provenance.
This is a simulation-only input envelope, not a new instruction or device mode.

This path requires Docker running and the existing offline image/cache used by
`graph-device dynamic-run`; it refuses network image builds. The runner
rebuilds the same generic simulator per invocation, so allow a few minutes.
It does not implement a persistent cache. This is RTL simulation correctness;
it does not execute via Sonatine/QEMU or measure a physical FPGA.

Supported Graphs retain the existing 16-instruction/eight-value limits,
uint32 LOAD/ADD/MAX/STORE operations (plus MUL with descriptor v3),
baseline 16x16 or compact 8x8 profile,
and one-cell relative halo. Unsupported Graphs fail before simulator launch
and retain a failed project run. Detailed raw evidence stays in the printed
repository artifact directory; the project history retains its receipt.

## Native and Sonatine GEMM

```sh
raveil project run gemm --backend native

make -C /path/to/raveil/sonatine
raveil project run gemm --backend sonatine-qemu \
  --sonatine-kernel /path/to/raveil/sonatine/build/sonatine.elf
```

The Sonatine backend accepts only the generated GEMM family with dimensions
from 1 through 8. Native results are Host Functional evidence; Sonatine/QEMU
results are QEMU Emulation Correctness evidence. Do not compare their timing.

## Enter the microkernel console

```sh
raveil project console sonatine \
  --sonatine-kernel /path/to/raveil/sonatine/build/sonatine.elf
```

At `raveil-u>` enter `help`. Enter `exit` to leave. The console is a direct way
to touch the current Sonatine seed; console text grants no execution approval
or evidence authority.

## Linux parity check

The commands use the same grammar on Python 3.11+ GNU/Linux. Tool identities
and therefore Command Graph IDs may differ from macOS because the resolved
allowlisted binaries differ. Semantic output, not a cross-host binary identity
or timing comparison, is the compatibility requirement.
