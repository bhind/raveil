# Raveil project workspace

## Run named result DAGs through Sonatine and RTL (local T-0217)

Place an admitted `raveil.fold-dag.v1` JSON in `WORK/inputs/dag.json`.
[The diamond example](../../examples/fold-dag-diamond.json) produces34.

```sh
python3 -m raveil project dag-check --project WORK --input dag.json
python3 -m raveil project dag-run --project WORK --input dag.json --kernel KERNEL_ELF --build EXISTING_RUNTIME
python3 -m raveil project dags --project WORK
python3 -m raveil project dag SAVED_ID --project WORK
python3 -m raveil project dag-diff OLD_ID NEW_ID --project WORK
```

Preview checks the full graph's reference/lifetime limits without executing or
writing. Run freezes the source JSON, kernel and runtime before execution. Edit
the source and run again for a fresh ID; saved inspect/diff never execute it again.
Changing the example root literal3 to4 produces38. Then changing the merge from
add to max produces27. The old34 and38 records remain independently inspectable.

Each record separately reports execution status and designated `output.available`.
A pinned output may remain available if unrelated later work fails. Diff requires
two available outputs with the same kernel/runtime, name and shape, and shows both
statuses. Interrupts/uncertain cleanup remain `unsealed`; retry as a new run.
The input bound is1MiB; evidence remains bounded to16MiB/1024 entries. No timing
or hardware result is implied. Actual offline demonstration:

```sh
python3 scripts/demo_project_dag.py --kernel KERNEL_ELF --build EXISTING_RUNTIME --output NEW_DEMO_DIRECTORY
```

## Compose named Graph results

Use one explicit input snapshot with one or two existing Graph recipes:

```sh
python3 -m raveil project compose --project WORK --input shared.json --output raw=raw --output biased=biased
python3 -m raveil project compositions --project WORK
python3 -m raveil project composition COMPOSITION_ID --project WORK
```

Here `inputs/shared.json` contains the existing324-word uint32 input format;
`recipes/raw.json` and `recipes/biased.json` are ordinary Graph recipes pointing
to their descriptors. The explicit input overrides both recipes' seed/input
choices for this attempt. Names are unique lowercase ASCII labels, up to31
characters, starting with a letter and then letters/digits/underscore/hyphen.
They are display values, not output paths. Both descriptors and the input are
captured before execution; later edits cannot change a running attempt.

The commands save separate parent history under `compositions/ID`, with numeric
private child projects. Existing single-run history and Garden stay unchanged.
Each child uses the normal oracle, C++ fallback and RTL validation. A complete
parent requires every child to pass and saved artifacts to revalidate. Inspect
shows both named outputs only for a complete parent; incomplete attempts retain
diagnostic evidence without displaying a complete result set. Reads do not run
the simulator again. A retry is another `compose` invocation and a fresh ID.

Ctrl-C before publication leaves the parent incomplete; an abrupt interruption
can leave an unsealed directory shown as `incomplete/unverified`. Already
published results are not revoked by a later interrupt. Inspection checks local
integrity, not authenticated provenance or hostile concurrent-writer isolation.
Input/descriptor capture is capped at4MiB and the saved tree at16MiB. Do not edit
retained composition evidence; edit the source recipes/inputs and run anew.

From the repository root, the actual cached-tool demonstration creates raw
`x*x` and biased `x*x+17`, modulo2^32, and checks all512 output words:

```sh
python3 scripts/demo_project_composition.py --output artifacts/research/T-0197/my-demo
```

Choose a new output path. The demo also cancels a second parent between actual
RTL child invocations and verifies it remains incomplete. This is a host
cancellation boundary, not device cancellation during execution. Toolchain and
image prerequisites match the existing RTL backend; no QEMU/RTL co-simulation,
shared arithmetic, hardware measurement or speedup is implied. See ADR-0108.

### Compare edited named results

After editing source input or descriptors and creating a new composition:

```sh
python3 -m raveil project composition-diff OLD_ID NEW_ID --project WORK
```

The command verifies both complete saved parents and pairs their outputs by
name, even if child order changed. It shows input/descriptor/output hashes,
common build identities, changed input words and changed active output cells
with the first changed coordinate/value. Nothing is executed or rewritten.
Incomplete/unsealed/tampered records, differing name sets, incompatible output
layouts or different simulator/RTL/source builds are rejected. Use ordinary
single-run `project diff` for ordinary runs. Comparison is Host Functional over
retained RTL evidence; it supplies no timing comparison or authenticity claim.

For the actual editable workflow demonstration, choose a new output directory:

```sh
python3 scripts/demo_project_composition_diff.py --output artifacts/research/T-0205/my-demo
```

It creates a complete pair, edits one input value and the bias17→23, reverses
child order, executes a second pair, checks all1,024 words against independent
scalar formulas, compares by name and verifies the old saved pair is unchanged.
Expected changes are one raw cell and all64 biased cells. See ADR-0109.

## When a Graph is rejected

`project check RECIPE --backend rtl-sim --project WORK` keeps the original
admission error and adds an advisory hint for known instruction-count,
register-allocation, shape/stride/window, relative-address and transport-profile
failures. For example, 18 nodes do not fit the current 16-instruction program;
spatial tiling alone does not reduce a per-cell expression's instruction count.

An eight-register rejection may include slots retained by unused results or
descriptor-order effects. Inspect the descriptor; it is not proof of intrinsic
hardware register demand. Editing the order does not guarantee success.
Compiler-valid shapes must also match the project's 8x8 strides10/8 or 16x16
strides18/16 transport profile. Unknown errors are not guessed at.

Hints do not modify files, prune/reorder nodes, retry, execute or change admission.
Re-run `project check` after manually editing; a failed check remains failed.
Even a passing check reports execution readiness as not checked.

## Inspect and selectively export saved files

```sh
python3 -m raveil project export-preview RUN_ID --project WORK
python3 -m raveil project export-preview RUN_ID --project WORK --member workspace/errors.txt
python3 -m raveil project export RUN_ID /absolute/new-selected.json --project WORK --member workspace/errors.txt --expect-preview HASH_FROM_SELECTED_PREVIEW --acknowledge-sensitive-data
```

The first command lists files, byte counts, hashes and warnings without selecting
anything or showing file contents. Repeat `--member` for each exact saved-run
relative path you intend to copy; use the hash from that same selection's
preview. A changed source or selection requires another preview. There are no
wildcards, automatic recommendations or default whole-run export.

Inspect file names and sensitivity yourself: snapshots may contain unrelated
inputs and the tool does not detect secrets. The new private JSON file contains
only selected base64 payloads, minimal source hashes and omitted count. It is
a labelled derivative, not an authenticated experiment or replayable full run.
`record.json` and `record.sha256` are lineage-only and cannot be selected;
the preview marks them non-selectable. The command does not upload, execute,
extract or import. Platforms without no-follow reads fail closed.

Destination must be new, outside WORK, with existing non-symlink parent paths.
No overwrite is allowed. Stop editing the source and destination directories
during preview/export: this is the existing cooperative single-writer boundary,
not a hostile-concurrency sandbox. Maximum source size is 16 MiB / 1024 files
plus parent directories; encoded JSON is capped at 24 MiB. Use normal tools to
inspect the JSON, not a nonexistent Raveil import command. Weekly Drive cadence
is unchanged.

### Inspect a received derivative without extracting it

```sh
python3 -m raveil project inspect-export /absolute/new-selected.json
```

No project directory or original run is needed. The command reads one bounded
regular JSON file, checks the strict envelope and each selected payload's
length/SHA-256, and lists paths and sizes without printing or writing contents.
It rejects duplicate JSON fields/members, path collisions, noncanonical base64,
unsupported claims, malformed/oversized input, links and special files.

`internal_integrity: consistent` means only that the supplied bytes agree with
their supplied hashes. A sender can replace both: this does not authenticate
the sender, verify the source run, prove an oracle result or establish safety.
The source hashes are unverified labels. Nothing is extracted, imported or
executed; `source_verified`, `authenticated` and `replayable_full_run` stay false.
Use the same cooperative no-concurrent-edit rule as export. This is not a
hostile-filesystem sandbox or a secret scanner.

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

Enter a displayed zero-based instruction number directly, or use j/k/g/G/q
(then Enter), to navigate a saved Graph. The fixture Garden uses its displayed
one-based stage numbers and additionally supports d for details. Invalid input
keeps the last valid Graph and selection visible. Garden checks the saved artifact
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

Each valid row names its exact `recipes/` file. Graph-device rows additionally
name the referenced `inputs/` descriptor and either the explicit input-data
file or the numeric seed. This makes shared metadata visible before editing:
`neighborhood` and `neighborhood-data` share `inputs/neighborhood.json`, while
`bias-grid` has its own descriptor and input-data file. The listing derives
these relationships from validated recipe metadata only; it does not open the
referenced files.

Discovery is read-only metadata validation: it does not compile a Command or
hardware Graph, read referenced inputs, check installed tools, or execute a
recipe. A listed backend is not a successful-run guarantee. Follow with
`project show NAME` to inspect the workload, `project check NAME --backend
BACKEND` to inspect known prerequisites, and then `project run NAME` with the
indicated backend. Use `--project DIR` when outside the project directory.

### Check before running

```sh
raveil project check logs --backend native
raveil project check bias-grid --backend rtl-sim
raveil project check gemm --backend sonatine-qemu
```

`project check` prints four ordered results: recipe schema, referenced input,
backend admission and relevant local tools. `pass` means that read-only check
succeeded; `fail` prevents readiness; `not-applicable` means the area does not
apply or could not safely follow an earlier failure; `not-checked` is never a
pass. Exit status is zero only when every required check passes.

The header says `known_prerequisites=true|false` and always says
`execution_readiness=not-checked`. A zero exit status and
`KNOWN-PREREQUISITES-PASS` are useful for local scripting, but they do not mean
that execution is ready or will succeed.

The check parses and validates bounded recipes without invoking even a tool's
`--version`. Native GEMM checks the compiler and source path; Sonatine checks
the QEMU and kernel paths; RTL simulation checks the Docker CLI, Dockerfile and
an executable non-symlink runner. It does not contact the Docker daemon or
prove that the immutable
image is cached. It creates no run, output or reservation and performs no
build, network fetch, simulation, device open or installation. Files can change
afterward, so `run` repeats authoritative validation and may still fail.

### Fork an editable recipe

Create an independent editable copy with a new confined name:

```sh
raveil project fork bias-grid my-bias
raveil project show my-bias
```

Command and GEMM forks copy the admitted recipe. Graph-device forks also copy
the referenced descriptor and explicit input data, then rewrite only the new
recipe. Seed-based Graph recipes copy their descriptor and retain the seed.
Existing destinations, traversal, symlinks and unavailable or admission-invalid
referenced paths are rejected; descriptor/input semantics remain a `show`/`run`
check. The source and saved runs are not modified.

Fork is a cooperative **single-user, single-writer** operation. Do not run two
forks concurrently in one project, edit its destination paths while it runs,
or treat a synchronized/shared directory as a concurrent writer surface. The
complete recipe is published atomically and last; caught failures clean only
files created by that invocation. A crash or power loss can still leave orphan
`inputs/` files, a non-discoverable partial temporary recipe, or a complete
destination plus its temporary hard link. Inspect
`recipes/DESTINATION.json`, non-JSON `.DESTINATION.*.fork` files and
`inputs/DESTINATION-*.json` before reusing a name; when ownership is uncertain,
use a fresh destination name. This is not a general filesystem transaction,
crash-recovery journal, hostile-writer boundary or sandbox. See ADR-0098.

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

### Optional compiled simulator reuse (T-0196)

Set `RAVEIL_SIMULATOR_REUSE=1` for successive local `--backend rtl-sim`
invocations. Unset it or use `RAVEIL_SIMULATOR_REUSE=0` for a fresh build.
Only the compiled simulator and build provenance are reused, never input,
output, admission, RTL execution or oracle verification. Changed source,
generated headers, pinned image or dependency contents invalidate reuse.

```sh
RAVEIL_SIMULATOR_REUSE=1 python3 -m raveil project run neighborhood --backend rtl-sim
# Edit inputs/neighborhood.json, then repeat the same command.
```

An eligible hit reports `build_reused=1 simulator_built_once=0` (the marker
prints these fields in the opposite order). A separate
`artifacts/graph_device_axi4lite_dynamic/run.XXXXXXXX/build-reuse-receipt.json`
records the key, dependency identity, hit and build count; the execution
receipt retains its existing schema. Zero builds does not mean zero execution
or a measured speedup: hashing/copying still costs work.

The private repository cache holds at most eight bundles (16 MiB payload plus
at most 8 KiB manifest per entry). A full cache
falls back to a fresh build without deleting entries. Corrupt or unsafe entries
fail closed; use explicit fresh mode to continue while preserving them for
inspection. This is cooperative same-user development storage, not a sandbox,
signed distribution channel or production cache. No daemon or network fetch.

### Editable example

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
ADD_IMM with descriptor v4 and unsigned GE_IMM comparison with descriptor v5),
baseline 16x16 or compact 8x8 profile,
and one-cell relative halo. Unsupported Graphs fail before simulator launch
and retain a failed project run. Detailed raw evidence stays in the printed
repository artifact directory; the project history retains its receipt.

For threshold-to-0/1 followed by neighborhood dilation, stage the editable
`threshold-cross-dilate` example from [Graph workloads](GRAPH_WORKLOADS.md).
Its simulation-only program v6 is not admitted by sealed UIO.

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
Its dependency-free directed canvas repeats each admitted data edge, making
external inputs, forks, joins, final outputs, and the selected node visible at
every supported width. It is a read-only projection of the saved graph; it
does not rerun or reinterpret the program.

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

## Run a32x32 grid through four RTL tiles

T-0207 / ADR-0111 adds a fixed five-point uint32 sum on a32x32 grid. The existing
RTL still runs16x16 at a time. Each tile receives the neighboring input cells;
only positions outside the full32x32 grid are zero. Arithmetic wraps modulo2^32.

From the repository, initialize a new project and one explicit input:

```sh
python3 -m raveil project init /tmp/raveil-grid32
python3 - <<'PY'
import json
from pathlib import Path
words = [0] * 1024
words[15 * 32 + 16] = 17
with Path('/tmp/raveil-grid32/inputs/grid32.json').open('x') as out:
    json.dump({'schema': 'raveil.grid-input/v1', 'rows': 32,
               'columns': 32, 'words': words}, out)
PY
RAVEIL_SIMULATOR_REUSE=1 python3 -m raveil project tile-run \
  --project /tmp/raveil-grid32 --input grid32.json
```

Use the reported TILING_ID to inspect saved output without another execution:

```sh
python3 -m raveil project tile TILING_ID --project /tmp/raveil-grid32
python3 -m raveil project tiles --project /tmp/raveil-grid32
```

Edit `inputs/grid32.json` (word index=row*32+column) and invoke `tile-run` again.
Each attempt captures a fresh input and gets a new ID; previous attempts remain
unchanged. Exactly1024 integer words in[0,4294967295] are required; booleans,
other shapes and extra fields fail. The fixed operation is center+north+south+
west+east; this entry point does not accept a custom expression or grid size.

A complete attempt contains four private child runs, frozen full input, all
four18x18 halo snapshots and the fixed descriptor. All children must validate,
use the same RTL build, and agree with a separate full-grid reference. Only
then does the atomic final `record.json` publish `output.words` (1024 words)
and its packed SHA-256. There is no separately published assembled output file.
An incomplete record has `output:null`; interruption during sealing can leave
an unsealed attempt which history labels `incomplete/unverified`. Completed
child evidence remains available for diagnosis. Retry is a fresh attempt.

The normal offline Docker/Chisel/Verilator prerequisites apply. Optional simulator
reuse skips rebuilding an unchanged binary, never skips execution. This is RTL
functional simulation; it does not establish hardware performance, QEMU coupling,
fsync/crash durability, or hostile concurrent-writer isolation.

Actual acceptance can be reproduced into a fresh repository artifact directory:

```sh
python3 scripts/demo_project_tiling.py --output artifacts/research/T-0207/my-new-run
```

The demo runs original and edited grids, checks all2048 cells with an independent
scalar formula, checks the five affected output cells, preserves the first
snapshot, and cancels a third attempt between actual child invocations.

## Rectangular grids and editable kernels

T-0208/#296 provides this owner-approved interface alongside the legacy fixed
T-0207 interface. Run these commands from the repository checkout.

A grid can have any integer row/column count from1 through64, including
nonmultiples of16. A kernel is an editable per-cell DAG over that grid; size and
boundary behavior are separate from the computation. Try a17x19 neighborhood
maximum plus a bias:

```sh
python3 -m raveil project init /tmp/raveil-general-grid
python3 - <<'PY'
import json
from pathlib import Path
root = Path('/tmp/raveil-general-grid/inputs')
grid = {'schema':'raveil.grid-input/v2', 'rows':17, 'columns':19,
        'words':[r*19+c for r in range(17) for c in range(19)]}
kernel = {'schema':'raveil.grid-kernel/v1', 'graph_id':'neighbor-bias',
          'nodes':[
    {'id':'c','op':'LOAD_U32','address':{'row_delta':0,'column_delta':0}},
    {'id':'n','op':'LOAD_U32','address':{'row_delta':-1,'column_delta':1}},
    {'id':'m','op':'MAX_U32','inputs':['c','n']},
    {'id':'b','op':'ADD_IMM_U32','input':'m','immediate':5},
    {'id':'out','op':'STORE_U32','input':'b'}]}
for name, value in [('grid.json',grid), ('kernel.json',kernel)]:
    with (root/name).open('x') as out:
        json.dump(value,out,indent=2)
PY
python3 -m raveil project tile-check --project /tmp/raveil-general-grid \
  --input grid.json --kernel kernel.json --boundary wrap
RAVEIL_SIMULATOR_REUSE=1 python3 -m raveil project tile-run \
  --project /tmp/raveil-general-grid --input grid.json \
  --kernel kernel.json --boundary wrap
```

`tile-check` reports dimensions, tile count, admitted instruction count and
boundary. It creates no attempt and runs no simulator. The17x19 example needs
four16x16 children; their valid output rectangles are16x16,16x3,1x16 and1x3.
Full child outputs are checked, then cropped to exactly323 grid cells.

Boundary behavior applies only to coordinates outside the **full** input grid:

| Option | Out-of-grid coordinate |
|---|---|
| `zero` (default) | Read0 |
| `clamp` | Read the nearest edge cell |
| `wrap` | Read the periodic row/column modulo the global dimensions |

Internal tile seams always read the corresponding original full-grid cell.
Each run is one pass over a frozen input, with at most16 children. The kernel
and boundary are frozen too; modifying live files cannot alter a saved run.

Supported node forms (all arithmetic is unsigned32-bit, wrapping after each
arithmetic operation):

| Operation | Fields besides `id`/`op` | Meaning |
|---|---|---|
| `LOAD_U32` | `address:{row_delta,column_delta}` | Both offsets are integers in[-1,1], including diagonals |
| `ADD_U32` | `inputs:[a,b]` | a+b modulo2^32 |
| `MUL_U32` | `inputs:[a,b]` | a*b modulo2^32 |
| `MAX_U32` | `inputs:[a,b]` | Unsigned maximum |
| `ADD_IMM_U32` | `input:a, immediate:N` | a+N modulo2^32 |
| `GE_IMM_U32` | `input:a, immediate:N` | Integer1 when a>=N, otherwise0 |
| `STORE_U32` | `input:a` | One final store, defining the grid output |

Immediates are integers0..4194303. References may name later-listed nodes;
dependencies must be acyclic. The final listed node must be the only store.
Undefined/duplicate IDs, extra keys, booleans as numbers, invalid offsets and
kernels exceeding the existing16-instruction/eight-register limits are rejected
before an attempt starts. Input JSON is bounded to128KiB, kernel JSON to16KiB.
Input must contain exactly rows*columns integers0..4294967295.

After the first run, edit the kernel's bias from5 to7, or replace `MAX_U32`
with `ADD_U32`, then run again with the same command. Compare the reported IDs:

```sh
python3 -m raveil project tile OLD_ID --project /tmp/raveil-general-grid
python3 -m raveil project tile-diff OLD_ID NEW_ID --project /tmp/raveil-general-grid
python3 -m raveil project tiles --project /tmp/raveil-general-grid
```

Comparison reports input changes, whether the compiled descriptor changed,
boundary before/after, changed output count and zero-based coordinates. Both
parents must be complete, untampered, same shape and same RTL build. Saved
inspection/comparison executes nothing and writes nothing. Failure/cancellation
retains private evidence and never publishes a complete grid. Retry is a new ID.
The v1 fixed32x32 command without `--kernel` and its saved results remain valid;
nonzero boundary modes require the explicit new kernel/v2 route.

The candidate acceptance demo uses actual RTL for multiple shapes, kernels and
all three boundary modes, plus kernel edit/cancellation; host tests separately
exercise the full64x64 bound. Run into a new local artifact directory:

```sh
python3 scripts/demo_project_grid.py --output artifacts/research/T-0208/my-new-run
```

The executable scope is a bounded one-input/one-output uint32 stencil/map DAG.
There is no floating-point, division, arbitrary radius, global reduction,
multi-pass loop or QEMU/RTL coupling. Simulation verifies functionality; no
hardware speed, energy or capacity result follows.

## DAG input ranges (local T-0219)

DAG v2 adds `{"from":"name","offset":128,"length":128}` producer intervals
inside either input buffer. `dag-check` previews intervals and touched-object
references; run/inspect/history/diff preserve the same frozen workspace contract.
See [bounded producer subranges](SONATINE_AFFINE_FOLD.md#bounded-producer-subranges-local-t-0219)
for grammar, limits and an actual editable demonstration command.

## Independent DAG batches (local T-0220)

`raveil.dag-batch.v1` contains `items`, an array of1..16
`{"name":"unique-name","dag":<existing DAG v1 or v2>}` entries. Each DAG has
its own input/dependencies and designated result. Cross-item links are unsupported.

```sh
python3 -m raveil project batch-check --project WORK --input batch.json
python3 -m raveil project batch-run --project WORK --input batch.json --kernel ELF --build EXISTING_RUNTIME
python3 -m raveil project batch BATCH_ID --project WORK
python3 -m raveil project batches --project WORK
python3 -m raveil project batch-diff OLD_ID NEW_ID --project WORK
```

Input JSON and common executables are captured before all execution. Named outputs
publish together after every child completes. First incomplete child stops the
batch and yields `outputs:null`; an interrupt or unexpected execution error leaves
an unsealed attempt. History and comparison verify saved proof without executing.
The original per-guest limits remain unchanged. Source4MiB, parent inventory128MiB
and16,384 entries are bounded separately; ordinary snapshots keep their defaults.

`scripts/demo_project_dag_batch.py --kernel ELF --build EXISTING_RUNTIME --output NEW_DIR`
executes nine8x8 tiles of an owned24x24 box sum, checks every cell against a separate
full-grid formula, edits the source and checks saved history/comparison.

## Source-preserving MF01 grids (local T-0221)

This candidate accepts one or two equal-shaped grid-input/v2 sources, a tile
shape, global zero/clamp/wrap boundaries and a bounded MF01 map/fold kernel.
See [ADR-0124](../decisions/ADR-0124-source-preserving-mf01-grids.md) for the schema
and explicit limits. Generate editable examples from `scripts.mf01_grid_cases`:

```sh
python3 -m raveil project init WORK
python3 -c 'from pathlib import Path; from raveil.project import encoded; from scripts.mf01_grid_cases import cases; Path("WORK/inputs/grid.json").write_bytes(encoded(dict(cases())["box-sum"]))'
python3 -m raveil project grid-check --project WORK --input grid.json
python3 -m raveil project grid-run --project WORK --input grid.json --kernel KERNEL --build BUILD
python3 -m raveil project grids --project WORK
python3 -m raveil project grid GRID_ID --project WORK
python3 -m raveil project grid-diff FIRST_ID SECOND_ID --project WORK
```

Use the existing compatible Sonatine kernel and offline runtime build; no new
guest/RTL build is needed for this layer. The captured parent freezes original
source and derived batch, verifies every independent child, assembles all cells
and checks an untiled original-coordinate oracle. Editing the workspace input
does not alter old captures. An incomplete child yields no whole-grid output.
Unexpected execution/cleanup errors remain unsealed. Saved reads revalidate
the source/lowering/proofs without execution. Diff requires successful grids of
the same shape and kernel/runtime but permits source/program/tile changes.

`scripts/demo_project_mf01_grid.py` exercises actual CLI source/program edits;
`scripts/mf01_grid_acceptance.py` covers max, two-input map/fold, all three
boundary modes, one-row edges, the 324-word input ceiling and a failed tile.
`scripts/mf01_grid_saved_audit.py` revalidates saved runs with process creation
disabled and rejects altered copies. All are QEMU/RTL functional evidence;
no physical throughput, energy, novelty or vendor advantage follows.

## Affine-coordinate MF01 grids (local T-0222)

The same grid-check/run/inspect/history/diff commands accept
`raveil.mf01-grid/v2`. V2 adds an explicit output `shape` and allows independently
shaped input grids. A view maps output row r, column c and fold iteration k as
`offset + r*row + c*column + k*step`, where all four values are coordinate pairs.
Row/column/step components are nonnegative integers 0..63; offsets are -63..63.
All previous packed-input, tile-count and MF01 operation/resource limits remain.

Generate a rectangular matrix-product input in an initialized WORK directory:

```sh
python3 -c 'from pathlib import Path; from raveil.project import encoded; from scripts.mf01_grid_affine_cases import matmul; value,expected=matmul(17,19,9); Path("WORK/inputs/grid.json").write_bytes(encoded(value))'
python3 -m raveil project grid-check --project WORK --input grid.json
```

That example multiplies 17x9 by 9x19 into 17x19, with nine partial/full 8x8 tiles.
The owned cases also include transpose, broadcast, strided boundaries and a
324-word-per-input matrix tile. Every coordinate is interpreted relative to its
selected input's dimensions. V1 inputs and their captured results remain valid.
See [ADR-0125](../decisions/ADR-0125-affine-grid-coordinate-maps.md) for exact
versioned fields and limits. This is still a bounded affine uint32 source;
dynamic control flow, signed strides and dependent tiles are not implemented.

## Admitted tile planning (local T-0224)

`grid-plan` searches every 1..16 by 1..16 uniform tile through existing admission.
It ranks admitted choices by coupled-session count, total packed input words,
then deterministic nominal-size ties. Preview is read-only. Saving explicitly
creates a new ordinary source file; existing files are never overwritten.

```sh
python3 -m raveil project grid-plan --project WORK --input grid.json
python3 -m raveil project grid-plan --project WORK --input grid.json --output selected.json
python3 -m raveil project grid-check --project WORK --input selected.json
python3 -m raveil project grid-run --project WORK --input selected.json --kernel KERNEL --build BUILD
```

For 17x64 by 64x19, requested 8x8 tiles exceed packed-input capacity; 5x5 is
the only admitted uniform partition (16 sessions). For the owned 24x24 box sum,
the selected 12x12 tiles use four sessions. These are static counts, not measured
speed. Planning a source without an admitted partition fails without an output
file or execution attempt. Source JSON, operation and resource validation remain
mandatory on the selected source when it runs. The advisory JSON itself is never
consumed as execution authority. See [ADR-0126](../decisions/ADR-0126-admitted-uniform-tile-advice.md).

## Post-reduction maps (local T-0225)

`raveil.mf01-grid/v3` adds a mandatory `post` object with `nodes` and `result`
to v2. Its only readable view is `reduced`, the committed reduction result for
that output cell. Existing uint32 operations apply after the complete fold,
with modulo-2^32 arithmetic after every operation. This can express a matrix
product followed by a scalar bias and threshold. Applying a bias to every
fold term would produce a different result.

```sh
python3 -c 'from pathlib import Path; from raveil.project import encoded; from scripts.mf01_grid_affine_cases import matmul; from scripts.mf01_grid_post_cases import with_post; value,_=matmul(17,19,9); Path("WORK/inputs/post.json").write_bytes(encoded(with_post(value)))'
python3 -m raveil project grid-plan --project WORK --input post.json
python3 -m raveil project grid-check --project WORK --input post.json
python3 -m raveil project grid-run --project WORK --input post.json --kernel KERNEL --build BUILD
```

Each tile uses two existing jobs in one coupled session. The second reads the
verified committed first result, and only the second result can become a grid
output. Failure at either stage suppresses the whole grid. Saved inspection
binds both stages to the original source. V1/v2 are unchanged. Tile planning
counts initial source packing; its cost excludes intermediate traffic.

Post nodes cannot access original grids, neighboring cells or another tile.
External tensor bias, additional reductions and arbitrary pipelines remain
outside this source contract. See [ADR-0127](../decisions/ADR-0127-post-reduction-map-source.md).

## Generated coordinate checks (local T-0226)

Run deterministic, source-coordinate formula checks across explicit partitions:

```sh
python3 scripts/mf01_grid_generated.py --seed 226 --count 1000 --output OUT
python3 scripts/mf01_grid_generated.py --seed 226 --count 1000 --output COUPLED --kernel KERNEL --build BUILD
python3 -m unittest tests.test_mf01_grid_generated -v
```

Output directories must be new. Every source, expected output and partition
result is retained in cases.json. Only the two declared capacity rejections
(rectangle size and tile count) count as rejected partitions; unexpected errors,
all-rejected runs and missing categories fail. Rejected partitions are never
counted as successful comparisons. For at least24 generated sources the harness
requires all24 boundary/fold/post/input-count combinations to have admission.

Coupled mode selects one admitted nonconstant-output source per category, then
prefers fewer sessions and more distinct output values. It fails if that coverage
cannot be met; a larger count can supply more candidates. Both declared inputs
are referenced in two-input sources. Actual execution and saved revalidation
must agree with the independently generated expected result. Static selection
scores make no claim about runtime speed or physical performance.

This tests shapes up to8x8, fold extent up to4, two views and short uint32
programs. It supplements the separate128/130/256-output and324-input boundary
fixtures; it does not replace them or prove arbitrary program correctness.

## Dependent grid-source flows (local T-0227)

A `raveil.mf01-flow/v1` source contains `stages` and `outputs`. Each stage has a
unique `name` and an ordinary grid `source`; replace an inline input grid with
`{"from":"producer-name"}` to read that stage's complete committed output. Both
inputs may be linked, and multiple stages may read one producer. Sources retain
existing coordinate, uint32 and resource semantics. Names resolve independently
of stage authoring order; cycles and unknown producers reject.

```sh
python3 -c 'from pathlib import Path; from raveil.project import encoded; from scripts.mf01_flow_cases import diamond; value,_=diamond(); Path("WORK/inputs/flow.json").write_bytes(encoded(value))'
python3 -m raveil project flow-check --project WORK --input flow.json
python3 -m raveil project flow-run --project WORK --input flow.json --kernel KERNEL --build BUILD
python3 -m raveil project flows --project WORK
python3 -m raveil project flow --project WORK FLOW_ID
python3 -m raveil project flow-diff --project WORK FIRST_ID SECOND_ID
```

The example computes a5x6 matrix product, branches to transpose and square, then
joins both results with another product. It returns both `product` and `join`.
There are4 stages and16 sessions with its explicit tiles. Other owned cases use
two successive products and an8-stage chain. No new guest/RTL build is needed.

Every stage passes admission before the first execution.1..8 stages may use at
most16 total sessions (at most32 jobs with current grid sources). All declared
stages execute, even when their outputs are not selected. The first incomplete
stage stops the entire schedule. Successful child receipts remain diagnostic;
parent outputs appear only when the entire schedule succeeds. Unexpected errors
leave an unsealed parent. Existing128MiB/16,384-entry capture limits still apply.

Saved loading re-derives each linked source from verified predecessors and checks
common executable hashes. Input/program edits create fresh attempts; old captures
remain unchanged. Comparison requires the same named output shapes and executables.
This is serial host orchestration with complete intermediate grids; streaming,
overlap and physical performance are not established. The ordinary source always contains explicit tiles; T-0228 supplies optional
advice that saves another ordinary source with only its tile fields changed.

## Flow partition advice (local T-0228)

`flow-plan` selects uniform tiles for each existing stage while retaining the
flow's links, inline values, programs and named outputs. Preview does not execute
or modify the project. Optional output creates a new source file and refuses to
overwrite any existing file. The normal runner admits the selected source again.

```sh
python3 -m raveil project flow-plan --project WORK --input flow.json
python3 -m raveil project flow-plan --project WORK --input flow.json --output selected-flow.json
python3 -m raveil project flow-check --project WORK --input selected-flow.json
python3 -m raveil project flow-run --project WORK --input selected-flow.json --kernel KERNEL --build BUILD
```

The owned branch/join example uses4 selected sessions instead of16 explicit ones,
with identical outputs against the retained actual execution. A3x8 by8x50 product
followed by3x50 by50x9 rejects1x1 requested tiles, but selects3x13 then3x5 tiles
and runs in6 sessions. Both follow the same admission/resource rules.

The finite objective is total sessions, then total per-stage initial packed input
words. Linked inputs are counted as packed inputs; post-stage accesses, repeated
loads within folds, intermediate writes/copies and storage are excluded. These
counts do not establish elapsed time or physical speed. If the minimum total
exceeds16 sessions, planning rejects without saving a selected file or creating
an execution attempt. Input shapes must remain independent of selected tiles;
streaming/shape-dependent planning is outside this proof.

## Malformed MF01 source diagnostics (local T-0230)

Malformed DAG/batch JSON types are rejected with the existing CLI exit2/error
message before an attempt directory or execution is created. Source admission
checks node, view, result, buffer and name types explicitly. Saved session/DAG
inspection rejects a processed count larger than the declared program even when
its transcript files and hash inventory have been rewritten consistently.
Valid source meaning, limits and saved format are unchanged. Verification details
and retained rejected examples are in the October11 log.

## Strict saved-proof readers (local T-0231)

MF01 standalone/bridge inspection and compiler source loading now use the same
strict integer JSON representation as session/chain/DAG inspection. Duplicate
fields and type substitutions reject even if modified files have updated hashes.
Valid JSON field reordering remains supported. Incomplete plans require a valid
64-character lowercase hexadecimal build digest, including before any build exists.
Chain processed counts are bounded before job indexing. No command or ISA changes.

The retained-proof audits below never launch QEMU/RTL. Each requires existing
captured artifacts and creates new mutation copies under a fresh output directory:
`mf01_bridge_saved_audit.py`, `mf01_standalone_saved_audit.py` and
`mf01_rejection_saved_audit.py`. The last accepts optional paired `--chain-root`
and `--expected-chain`; existing session/DAG invocations remain valid. Exact
invocations, initial failures and final receipts are in the October11 log.

## Cumulative host reproduction (local T-0232)

The T-0232 evidence directory contains `reconstruction.json`, the27-module
`test-modules.json`, `run-host-regression.py` and `revalidate-parents.py`.
Reconstruct canonical a58e5a5 with the T-0231 cumulative patch and verify its144
manifest hashes before running. The dated log lists additional canonical host
checks for shared consumers omitted by changed-test discovery. Saved parent checks
need the named retained workspaces and do not execute guest/RTL processes.

This reproduction is local compatibility evidence. It neither applies the held
signed-numeric proposal nor publishes any candidate to canonical main.

## Fresh flow retry verification (local T-0233)

A failed flow remains an inspectable incomplete parent with no published outputs.
Rerunning the same source creates a fresh parent and executes from the beginning.
T-0233 exercises this with the existing eight-stage uint32 example, checks the full
failed tree is unchanged and compares the retry output with a successful baseline.

The local evidence scripts `recover-flow.py` and `verify-fresh.py` live under
`artifacts/research/T-0233/`. The latter reads saved nested receipts, compares actual
session/job counts with the planner report and excludes the copied comparison
baseline. Both exact commands and immutable executable identities are in the log.

## Explicit signed ordering (local T-0229)

Use `raveil.mf01-grid/v4` with v2 coordinate fields and an optional v3-style `post`.
Both the kernel map and post map accept:

```json
{"id":"larger","op":"max_i32","args":["a","b"]}
{"id":"activated","op":"relu_i32","args":["larger"]}
```

These are individual node examples. Inputs and saved outputs remain uint32 bit
patterns: -1 is encoded as4294967295, INT32_MIN as2147483648. Negative JSON words
are rejected. Only these two operations decode signed ordering; existing `max`,
`ge_imm` and max reduction remain unsigned. Add, multiply and sum wrap modulo2^32
before the next operation interprets the bits. Thus this is not widened GEMM,
saturating arithmetic or a signed reduction. V1/v2/v3 retain their exact meaning.

Existing `grid-check`, `grid-plan`, `grid-run` and flow commands handle v4. Signed
operators expand into ordinary operations before admission, so a short source
can exceed15 map nodes or8 registers after expansion and reject before dispatch.
No silent spilling, node omission or extra jobs occurs. An explicit post map adds
the same single dependency job per tile as v3. Frozen original sources remain in
saved evidence; changing signed operations to unsigned operations cannot reuse
an old child execution even if the parent hashes/output are recomputed.

Owned cases: `scripts/mf01_numeric_cases.py` and `scripts/mf01_numeric_extra_cases.py`.
Actual commands, prior failures and exact runtime identity are in the October11 log.

## Generated signed coordinate checks

The existing test harness can generate signed v4 sources without changing its
unsigned default:

```sh
python3 -B scripts/mf01_grid_generated.py --numeric signed32 --seed 229 --count 1000 --output NEW_OUTPUT
```

Add `--kernel KERNEL --build BUILD` to execute 24 selected cases through the
existing coupled backend. Use a fresh output directory. Full inputs, expected
words, rejected partitions and counterfactual diagnostics are retained. Selection
requires observable signed semantics, out-of-bounds samples and sensitivity to
each input; insufficient coverage fails before execution. Nonconstant output alone
is insufficient. These checks are functional evidence, not performance estimates.

## Proposed shared signed transforms

The local T-0234 candidate recognizes `raveil.mf01-grid/v5`. Its fields and numeric
meaning match v4; the explicit version selects sharing of biased SSA values within
each map. To try host admission, save a new copy of an existing source with only
its schema changed, then use `grid-check` or `grid-plan`. Preserve the original.
Ordinary 15-node/8-register checks still apply. Inputs never select the lowering.

The prepared `scripts/mf01_numeric_shared_acceptance.py` covers chains, a modular
branch, post maps and linked flow using the existing backend. Its runtime acceptance
now passes after owner-directed continuation, including an injected post rejection
and a separate v4/v5 equality check. V4 records use their old exact lowering.
The resumed evidence is in `artifacts/research/T-0234/resumed-01/`; public adoption
remains separate.

## Automatically partitioned array programs (local T-0235)

Use [the common array input guide](ARRAY_PROGRAM.md) for long expressions and
linked integer-array stages with automatic partitioning. `array-check`, `array-run`,
`array`, `arrays` and `array-diff` share this source format. UT and actual QEMU/RTL
integration are separate evidence classes; existing grid/flow sources retain meaning.
