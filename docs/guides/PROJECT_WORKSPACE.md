# Raveil project workspace

Status: T-0149 and T-0148/S02 development guide

This is the shell-first path for editing a small workload, seeing its Graph,
running it more than once and comparing retained results. Use your normal
bash/zsh, editor, Git and file tools around the `raveil project` commands.

## Create and inspect

### Open a saved Graph run in Garden

After a successful `graph-device` run, use its printed run ID:

```sh
raveil project garden RUN_ID --project /tmp/my-raveil-project
raveil project garden RUN_ID --project /tmp/my-raveil-project --keys jjq --width 100
```

Use j/k/g/G/q (then Enter) to navigate. Garden checks the saved artifact
manifest and shows retained lowering and receipt identities without compiling
or running the Graph again. The view is Host Functional; saved simulation
agreement is a historical reference, not a new execution or authenticated seal.
Changed files, failed runs and non-Graph runs are rejected. Existing fixture
commands are unchanged. Substitute an actual saved run ID for `RUN_ID`.

### Initialize a workspace

For Graph recipes, `project show NAME` prints
`descriptor file: inputs/<actual filename>` and, for explicit input,
`input file: inputs/<actual filename>`. These paths are relative to the
selected project directory. Edit these files rather than inferring a filename
from the displayed Graph ID; recipe name, Graph ID and filename may differ.

From the repository root:

```sh
export PATH="$PWD/scripts:$PATH"
raveil project init /tmp/my-raveil-project
cd /tmp/my-raveil-project
raveil project recipes
raveil project show logs
raveil project show files
raveil project show gemm
```

The generated `recipes/` and `inputs/` files are ordinary JSON and text. The
Command recipes use only the bounded allowlisted syntax documented in
`NATIVE_COMMAND_GRAPH.md`; they do not accept arbitrary shell commands.

`project recipes` lists the `.json` entries in `recipes/` in filename order,
including your own recipes. It shows their kind and compatible backend names:
Command uses `native`, Graph uses `rtl-sim`, and GEMM also supports
`sonatine-qemu` when all dimensions are at most 8. Invalid recipe metadata or
unreadable entries appear as `unavailable` with an escaped diagnostic; other
entries remain visible. Non-JSON files are ignored. Existing directory, path
and text-size limits still apply.

Discovery is read-only metadata validation: it does not compile a Command or
hardware Graph, read referenced inputs, check installed tools, or execute a
recipe. A listed backend is not a successful-run guarantee. Follow with
`project show NAME` to inspect the workload and then `project run NAME` with
the indicated backend. Use `--project DIR` when outside the project directory.

## Edit, run and compare

```sh
raveil project run logs
printf 'ERROR changed\n' >> inputs/events.txt
raveil project run logs
raveil project runs
raveil project runs --recipe logs --backend native --status succeeded
raveil project diff RUN_A RUN_B
```

Replace `RUN_A` and `RUN_B` with the two IDs printed by `run` or `runs`. Each
run keeps its exact recipe and input copy, compiled Graph, output workspace and
result record under `runs/RUN_ID/`. You can inspect those files with your usual
editor or command-line tools.

Run history is cooperative local development evidence. The reader detects
later artifact mutation, but this is not a signed audit log, production cache
or hostile-code sandbox.

`project runs` accepts optional exact `--recipe`, `--backend`, and `--status`
filters. Filters may be combined and do not execute recipes or modify saved
runs. The unfiltered view continues to expose incomplete or invalid entries;
filtered views omit entries whose checked metadata cannot match. Valid status
values are `succeeded` and `failed`, and backend names use the same three
bounded project backends shown by `project recipes`.

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
path. Garden's read-only dynamic explanation admits v4 under ADR-0091;
saved project runs open through the separate ADR-0093 checked view. Sealed UIO
admission is not extended to v4 by this workflow.

`run` verifies descriptor-oracle/C++-fallback/RTL byte equality and saves the
receipt. Inspect `runs/RUN_ID/workspace/output.txt` for active rows and
`output.bin` for the full 256-word little-endian transport window, including
inactive cells. `runs/RUN_ID/generated-input.bin` retains all 324 input words.
The descriptor and ordinary input files remain under the run's `inputs/` copy.
`diff` reports changed nodes, the number of changed active cells, the first
changed cell's values, and whether simulator/RTL/program hashes match.
The original `neighborhood` recipe keeps seed-generated input.

### Inspect a checked saved result

```sh
raveil project output RUN_ID
```

This read-only command accepts a successful saved `rtl-sim` Graph run. It
checks the run record and artifact hashes, then reads the bounded saved
`workspace/output.txt` and checks those exact bytes against both recorded
output hashes before printing the run ID, evidence class and active rows.
Edits to today's inputs or recipe do not change the displayed historical
result. No compiler, backend or simulator is invoked.

Changed artifacts, incomplete/failed runs and non-Graph runs fail without
printing output rows. Use `--project DIR` outside the project directory.
This is the existing cooperative local integrity boundary, not a signed audit
or stronger hostile-filesystem isolation. It neither reruns validation nor
turns retained simulation results into hardware or performance evidence.

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
When both successful runs use explicit input, `diff` reports the changed word
count and first changed zero-based index with before/after uint32 values.
Example: `input: 1/324 words changed` and
`first changed input word [11] (zero-based): 7 -> 9`.
Values come from checked saved JSON bound to the recorded packed-input hash,
not today's editable file. Formatting-only changes report zero changed words
while raw-file hash differences remain visible. Counts include halo and unused
words; they do not establish a causal relationship with output differences.
Seed, mixed-input and failed-run comparisons retain their previous behavior.
This is a simulation-only input envelope, not a new instruction or device mode.

This path requires Docker running and the existing offline image/cache used by
`graph-device dynamic-run`; it refuses network image builds. The runner
rebuilds the same generic simulator per invocation, so allow a few minutes.
It does not implement a persistent cache. This is RTL simulation correctness;
it does not execute via Sonatine/QEMU or measure a physical FPGA.

Supported Graphs retain the existing 16-instruction/eight-value limits,
uint32 LOAD/ADD/MAX/STORE operations (plus MUL with descriptor v3 and
ADD_IMM with descriptor v4),
baseline 16x16 or compact 8x8 profile,
and one-cell relative halo. Unsupported Graphs fail before simulator launch
and retain a failed project run. Detailed raw evidence stays in the printed
repository artifact directory; the project history retains its receipt.

### Add an editable constant (T-0173 / T-0174)

New projects include `bias-grid`, an independent snapshot recipe. Run
`raveil project recipes` to find it. Its descriptor `inputs/bias-grid.json`
contains this bounded example:

```json
{
  "schema": "raveil.graph-device-dag/v4",
  "graph_id": "bias-grid",
  "affine": {"rows": 8, "columns": 8, "input_stride": 10, "output_stride": 8},
  "nodes": [
    {"id": "center", "op": "LOAD_U32", "address": {"row_delta": 0, "column_delta": 0}},
    {"id": "bias", "op": "ADD_IMM_U32", "input": "center", "immediate": 5},
    {"id": "store", "op": "STORE_U32", "input": "bias"}
  ]
}
```

Run `raveil project show bias-grid`, then
`raveil project run bias-grid --backend rtl-sim`. Note the run ID.
Edit `immediate` from 5 to 7 in your editor and run again. Use
`raveil project output RUN_ID`, `raveil project diff FIRST SECOND` and
`raveil project garden RUN_ID` (`j` then Enter selects the add node).
The saved first result stays unchanged. Garden displays the immediate and
unsigned modulo-2^32 addition; overflow wraps rather than saturating.

Only integer constants 0 through 4,194,303 are admitted. This is a one-source
immediate add, not a full-width constant node. Other arithmetic can consume
its result. The recipe uses its own `inputs/bias-grid-data.json` (324 uint32
words). Neither file is shared with `neighborhood`; the original examples
stay usable. Existing projects are not upgraded or overwritten: initialize a
new empty directory to try the starter. The old seeded `neighborhood` recipe
deliberately rejects this program version if manually substituted there.
The existing instruction,
register, input/output and shape bounds remain. This is RTL simulation,
not QEMU, native speed comparison or FPGA execution.

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
