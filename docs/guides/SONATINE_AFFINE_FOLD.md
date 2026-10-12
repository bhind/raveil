# Sonatine affine fold: local candidate workflow

T-0212 is an unpublished local candidate. It executes MF01 in software on
RV64/QEMU; the Chisel engine is tested separately. No hardware purchase is needed.

## Run an editable region

Build once using the installed native RV64 tools:

```sh
make -C sonatine
python3 -m raveil.sonatine_fold --region region.json --inputs inputs.json --kernel sonatine/build/sonatine.elf --output runs/fold-001
python3 -m raveil.sonatine_fold --verify runs/fold-001
```

The region uses the same raveil.affine-fold.v1 JSON as project fold-run. Inputs
may be two arrays or the existing project object
{"schema":"raveil.fold-input/v1","buffers":[[1,2],[3,4]]}.
Choose a new output directory for each execution. The command freezes inputs,
region and kernel, checks the complete result and seals receipt.json only after
agreement with the independent Python SSA reference. Verification does not run
QEMU. A timeout or mismatch leaves evidence without a success receipt.

One executable handles variable shapes, affine input views, joins, broadcasts,
transposes, uint32 scalar maps and sum/max reductions. MF01 remains bounded:
16x16 outputs,64 reduction steps,16 instructions,8 views and2x324 input words.
Up to256 outputs publish through two existing512-byte objects in one finalize.
The two objects are not independently approved/publicly reported.

## Compare with RTL

Given an existing verified T-0211 runtime build and successful QEMU receipts:

```sh
python3 scripts/fold_differential.py --qemu-evidence runs --rtl-build path/to/runtime-build --output comparison-001
python3 scripts/fold_differential.py --verify comparison-001
```

The first command executes the same captured descriptor/input on the reusable
RTL simulator, then compares every word. The second checks both saved records,
the same computation and all output values without execution. QEMU receipts are
currently linked by their original absolute paths; retain those paths when
rechecking a differential packet. Each backend retains its own evidence class.

## What the result establishes

The guest admits and trusts its C interpreter, commits output, and reports it.
Independent SSA agreement is checked by the host after that commit. Hashes bind
local evidence; CRC32 detects transport corruption. Neither authenticates a
hostile producer. Kernel inputs are boot data, not user capability objects.
The run is one request per guest boot. No real RTL device in QEMU, asynchronous
reset/cancellation contract, measured hardware speed/energy or Groq advantage
is established. See Proposed ADR-0116 for precise boundaries.

## T-0213: guest-issued execution on the existing RTL simulator

The local coupling candidate uses the same region/input files. Build the updated
kernel, then use an existing verified T-0211 runtime build:

```sh
make -C sonatine
python3 -m raveil.fold_bridge --region region.json --inputs inputs.json --kernel sonatine/build/sonatine.elf --build path/to/runtime-build --output runs/coupled-001
python3 -m raveil.fold_bridge --verify runs/coupled-001
```

Sonatine emits the request before the broker starts RTL execution. It validates
the returned binding and checks all output words against its C reference before
publication. A failed exchange leaves output unchanged. Verification rechecks
saved UART phase order, binding, request and complete RTL trace without running
either backend. This supports one job per guest boot. UART pacing and the host
broker are experimental functional transport, not a hardware device or a speed
benchmark. Proposed ADR-0117 records precise deadlines, trust and reset limits.

## Bounded sequential sessions (local T-0214)

`raveil.fold_session` accepts `{"schema":"raveil.fold-session.v1","jobs":[...]}`.
Each of1..8 jobs contains a distinct `name`, an admitted `region`, and two literal
`inputs` buffers, in the same format as the single-request bridge. All are checked
before dispatch. One guest retains output/version state through all jobs.

```sh
python3 -m raveil.fold_session --session session.json --kernel sonatine/build/sonatine.elf --build EXISTING_RUNTIME --output NEW_SESSION_DIRECTORY
python3 -m raveil.fold_session --verify SAVED_SESSION_DIRECTORY
```

Full output replacement zero-pads unused words. A framed semantic/binding fault
preserves the preceding output and permits continuation; framing loss halts the
remaining plan. This is independent-input functional coupling, not a dependency
pipeline or persistent simulator. The admission/acceptance scripts provide
negative test injections; normal CLI execution uses no injected faults.

## Result-dependent chains (local T-0215)

Use schema `raveil.fold-chain.v1`, the same named jobs and regions, and replace
an input array with `{"from":"producer-name"}` to read its committed result.
Both linked arrays must refer to one earlier producer; lengths must match its
logical output. Literal and linked inputs may be mixed. Example: a16x16 map can
feed a transpose, matrix product or row reduction without a guest restart.

```sh
python3 -m raveil.fold_chain --session chain.json --kernel sonatine/build/sonatine.elf --build EXISTING_RUNTIME --output NEW_CHAIN_DIRECTORY
python3 -m raveil.fold_chain --verify SAVED_CHAIN_DIRECTORY
```

Failed/overwritten sources halt before dispatch. Two banks retain at most two
current results, so an arbitrarily old name is not guaranteed available. Each
response is semantically checked before publication. Saved verification rebuilds
all dependencies and checks the actual guest-derived input envelopes. This is
functional simulation; linked-input authority does not include literal arrays.

## Resource-admitted DAGs (local T-0216)

Use schema `raveil.fold-dag.v1`, topological named `jobs`, and `output` naming the
result to retain. Either input may name any earlier producer with `{"from":"name"}`;
two distinct producers are supported when the existing reference/memory limits
permit them. The complete graph is checked before the first dispatch.

```sh
python3 -m raveil.fold_dag --check --session examples/fold-dag-diamond.json
python3 -m raveil.fold_dag --session examples/fold-dag-diamond.json --kernel sonatine/build/sonatine.elf --build EXISTING_RUNTIME --output NEW_DAG_DIRECTORY
python3 -m raveil.fold_dag --verify SAVED_DAG_DIRECTORY
```

The example calculates root3+5=8, left8+2=10, right8*3=24, then merges10+24=34.
Changing the first literal3 to4 yields38 without changing the RTL build. Saved
records retain the earlier computation. --check is read-only and needs no kernel,
simulator or Docker; it reports the allocated object IDs, reference counts and
lifetimes. It rejects unsupported fan-in/live-memory pressure before execution.

The designated output's `available` field is separate from every node's success
and the graph's halt state. An early designated output can remain available when
later unrelated work fails. Reclaimed intermediate identities are historical,
not live handles. Literal arrays remain frozen boot data; linked arrays use
capability snapshots. This is functional QEMU/RTL evidence, not timing/FPGA data.

## Workspace entry points

Local T-0217 connects the same DAG executor to project dag-check/dag-run/dag/dags/
dag-diff; see [project workspace](PROJECT_WORKSPACE.md). It freezes exact source,
kernel and runtime, retains immutable names/history and compares saved designated
outputs without executing. The standalone commands above remain supported.

## Bounded producer subranges (local T-0219)

Use `"schema":"raveil.fold-dag.v2"` to select a word interval from an earlier
result. For example, a consumer buffer of128 words can use:

```json
{"from":"producer","offset":128,"length":128}
```

Length must equal that consumer buffer's declared length and fit the producer's
logical result. It must be positive; offsets are zero based uint32 word units.
Whole-result `{"from":"producer"}` links remain usable in v2. V1 retains its
original whole-result-only grammar. No element is copied from a failed/stale
producer and no last-success fallback exists.

Admission counts the union of touched128-word chunks and destination chunks,
limited to four object references. A128-word interval beginning at offset64
touches two chunks. A and B can refer to overlapping intervals of the same
producer; shared chunks consume one reference. Producers remain entirely live
until their last consumer. This does not implement partial memory reclamation.

`project dag-check` shows exact ranges and READ/WRITE object counts;
`project dag-run`, saved inspection/history and comparison use the same workflow.
The guest retains conservative full512-byte READ references for touched objects,
then reads the requested segments through bound submission snapshots. No host
input substitution or authority-limit increase is involved.

```sh
python3 scripts/fold_dag_range_acceptance.py --kernel sonatine/build/sonatine.elf --build EXISTING_RUNTIME --output NEW_ACCEPTANCE_DIRECTORY
python3 scripts/demo_project_dag_ranges.py --kernel sonatine/build/sonatine.elf --build EXISTING_RUNTIME --output NEW_WORKSPACE_DIRECTORY
```

The demo changes a range offset from128 to64 and checks all128 changed output
words, saved inspection/history/diff and unchanged earlier snapshots. These are
host-mediated QEMU/RTL functional results, not timing or hardware measurements.
