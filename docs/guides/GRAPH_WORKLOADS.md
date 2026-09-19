# Bounded Graph workload staging pack

The staging pack in `examples/graph-workloads/` contains three small computations
that can be copied into an ordinary Raveil project, edited, rerun and compared.
They use the existing Graph compiler, runtime request and RTL simulator. They
are functional examples, not representative performance benchmarks.

## Stage a disposable workspace

From the repository checkout:

```sh
DEMO="$(mktemp -d)/raveil-graph-workloads"
python3 -m raveil project init "$DEMO"
cp examples/graph-workloads/recipes/*.json "$DEMO/recipes/"
cp examples/graph-workloads/inputs/*.json "$DEMO/inputs/"
python3 -m raveil project recipes --project "$DEMO"
```

The copy is deliberate: edit only the disposable workspace. The repository
pack remains a known starting point.

## Cross-neighborhood binary dilation

`cross-dilate-binary` treats the active 8x8 cells as binary occupancy. Each
output is the unsigned maximum of its center, north, south, west and east
inputs. The active grid has a one-cell zero halo inside a 10x10 footprint.
Words 100 through 323 are fixed-transport padding and are ignored.

```sh
python3 -m raveil project show cross-dilate-binary --project "$DEMO"
python3 -m raveil project check cross-dilate-binary --backend rtl-sim --project "$DEMO"
python3 -m raveil project run cross-dilate-binary --backend rtl-sim --project "$DEMO"
```

Edit a `0` to `1` in the active footprint of
`inputs/cross-dilate-binary-input.json`, then run it again. Use the printed run
identifiers:

The first 100 words are a row-major 10x10 grid. Active coordinate `(row,
column)`, counted from zero, is word `(row + 1) * 10 + column + 1`; its outer
row and column are halo. For the repository input, the demonstrated edit is
`word[23]` from `0` to `1`. It changes 3 of the 64 active outputs. Words 100
through 323 are transport padding, so editing them does not change the output.

```sh
python3 -m raveil project output FIRST_RUN --project "$DEMO"
python3 -m raveil project output SECOND_RUN --project "$DEMO"
python3 -m raveil project diff FIRST_RUN SECOND_RUN --project "$DEMO"
python3 -m raveil project garden SECOND_RUN --project "$DEMO"
```

Garden is read-only. It explains the saved Graph, lowering and evidence; it
does not execute, mutate, approve or promote the run.

## Sensor energy plus bias

`sensor-energy-bias` computes `(x * x + 17) modulo 2^32` independently for
each active cell. The input intentionally includes boundary values so unsigned
wraparound is visible. The name describes a synthetic transform, not a sensor
calibration or a physical energy claim.

```sh
python3 -m raveil project show sensor-energy-bias --project "$DEMO"
python3 -m raveil project run sensor-energy-bias --backend rtl-sim --project "$DEMO"
```

## Editable threshold followed by cross dilation

`threshold-cross-dilate` uses descriptor v5 / program v6. Five unsigned
`GE_IMM_U32` comparisons turn raw intensity values into 0 or 1; four MAX
operations then combine the center and its four neighbors. This fits 15 of
16 instructions and uses the same fixed input/output windows.

```sh
python3 -m raveil project show threshold-cross-dilate --project "$DEMO"
python3 -m raveil project run threshold-cross-dilate --backend rtl-sim --project "$DEMO"
```

The starting input contains three isolated values, 100, 120 and 200. At
threshold 100, each creates a five-cell cross: 15 output cells are 1.
Edit all five `immediate` fields in
`inputs/threshold-cross-dilate-descriptor.json` from 100 to 150, then run
again. Only 200 now passes, leaving five output cells equal to 1. Ten cells
change from 1 to 0; the input snapshot itself is unchanged. Use the same
`project output`, `project diff` and `project garden` commands above with
the printed run IDs. The original saved run must remain unchanged.

Garden explains the comparison as unsigned `source >= threshold`, not a
branch: every load and the final STORE still execute. Thresholds range from
0 through 4194303; 0 passes every uint32 input, including the zero halo.
Negative, fractional, boolean or larger thresholds are rejected, not clamped.
This path is RTL simulation only and does not admit the program to sealed UIO.

## Deliberate limits and next questions

All examples are fixed 8x8 snapshots with exactly 324 uint32 input words and
one output. T-0182 adds only the comparison opcode under ADR-0101, not capacity,
another backend or CLI. A Sobel edge filter still needs signed subtraction;
general SELECT and full-width constants remain deferred. One sensor pass
that emits both raw squared energy and biased energy needs two output identities
and violates the current exactly-one-final-STORE rule; multi-output Graphs
remain T-0183. A full 3x3 dilation needs nine loads, eight MAX operations and a
store (18 instructions), exceeding the current 16-instruction capacity;
capacity and tiling remain T-0184.
