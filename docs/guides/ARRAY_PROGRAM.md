# Automatically partitioned integer arrays (local T-0235)

Phase one accepts `raveil.array-program/v1`. Edit a common JSON source; the compiler
chooses all passes and 16x16 tiles. Long expressions, affine sampling, reductions
and linked stages use the same entry point. No per-workload compiler or RTL is
required. The end-to-end functional verification and replay entry are documented in
[GENERALIZATION_COMPLETION.md](GENERALIZATION_COMPLETION.md).

## Start and inspect

From this candidate checkout:

```sh
python3 -m raveil project init /tmp/my-array-workspace
cp examples/array-program/gemm.json /tmp/my-array-workspace/inputs/program.json
python3 -m raveil project array-check --project /tmp/my-array-workspace --input program.json
```

Other editable examples are `pointwise.json`, `long-expression.json` (24 nodes)
and `stencil.json`. All examples use the same schema and compiler. `array-check`
is read-only. Its structural preview contains every generated pass, exact source
hash, session/work counts, release lists and conservative logical plane words.
It does not require a simulator and does not prove available capture capacity.

## Input contract

Top-level fields are exactly `schema`, `stages`, `outputs`. Each stage contains
`name` and `source`. A source contains `inputs`, `shape`, `boundary`, `kernel` and
optionally `post`. There is no `tile` field. Names follow existing workspace names.
Stage authoring order is irrelevant; lexical topological order is deterministic.
Outputs are a distinct ordered list of stage names. All declared stages and nodes
execute, including ones outside the requested output dependency path.

Each input is a grid-input/v2 object (`schema`, `rows`, `columns`, uint32 `words`)
or a `{ "from": "producer-stage" }` link. Inputs may have different shapes.
A kernel contains `extent`, `fold`, `views`, `nodes`, `result`:

- `fold` is `sum` (wrap32) or `max` (unsigned); extent is 1..64.
- A view contains zero-based `input`, and two-element `offset`, `row`, `column`,
  `step` vectors. Sample coordinates are `offset + r*row + c*column + k*step`.
  Offsets are -63..63; other coefficients are 0..63. Boundary is `zero`, `clamp`
  or `wrap`. Transposition, broadcasting, strided sampling and matrix products
  follow from those coordinates without separate special operators.
- Nodes have unique `id` and `op`. `load` has `view`; other nodes have `args`
  referencing earlier nodes. Binary operations: `add`, `mul`, `max`, `max_i32`.
  Unary operations: `relu_i32`, `add_imm`, `ge_imm`; the latter two require `imm`
  in 0..4194303. Unknown fields, bool/float words and malformed dependencies reject.
- Each operation stores a uint32 bit pattern. Addition/multiplication wrap before
  later signed operations. `max_i32` and `relu_i32` reinterpret those bits as int32;
  `max`, `ge_imm` and the fold remain unsigned. No widening or saturation.
- Optional `post` has `nodes` and `result`; its loads may name only `reduced`.
  It executes after the entire reduction, which matters for overflow and ReLU.

## Exact operational limits

There are at most 8 stages, 8 inputs and 8 views per stage, 8 requested outputs,
128 total source nodes including post, and 64x64 cells per grid. Expansion must
fit 128 passes, 128 total tiled sessions, 32768 output-word evaluations and 65536
conservative logical working-plane words. The last number includes all literals,
retained intermediate planes, packed operands and the current result; it is not
Python RSS or total proof/interpreter memory. Source syntax limits alone do not
promise expanded admission. Rejection explains the exceeded class of bound.

The initial compiler materializes each scalar node. Fold iterations execute in
order and combine on the backend; post follows the final fold. Last-use lists
release temporary planes while requested output producers remain pinned. Original
affine samples are gathered by the host. Arithmetic results are computed by the
backend, with a separate original-coordinate scalar interpreter checking final
outputs. This may create many sessions and copies; it is not a speedup claim.

## Execution and saved inspection

The same source uses the existing QEMU/RTL execution path with a verified kernel
and runtime:

```sh
python3 -m raveil project array-run --project /tmp/my-array-workspace --input program.json --kernel /path/to/kernel.elf --build /path/to/verified-runtime
python3 -m raveil project arrays --project /tmp/my-array-workspace
python3 -m raveil project array RUN_ID --project /tmp/my-array-workspace
python3 -m raveil project array-diff FIRST_ID SECOND_ID --project /tmp/my-array-workspace
```

Each attempt freezes source, structural plan, kernel and runtime. Every child is
reloaded and bound to its exact derived source and common executables before
its output can feed another pass. Saved inspection repeats those checks without
executing any process. Comparison requires successful captures with matching
named output shapes and executables. These are functional results, not timing.

A failed child stops all successors and suppresses every parent output. Exceptions,
cancellation, capture overflow or uncertain cleanup leave an unsealed attempt.
Retry by running again; never overwrite or resume an old attempt. History preserves
unsealed attempts. The 128 MiB/16384-entry inventory ceiling remains unchanged.
Preflight counts `1 + passes + sessions` runtime and kernel copies plus a byte
reservation of 64 KiB/pass and 128 KiB/session, and an entry reservation of
64/pass and 32/session. The reservation is not a guarantee about future logs;
inventory is checked after each pass and before publication. No partial parent
output can be published on capacity failure.

Floating point, dynamic branches, general MLIR/model import, optimized pass fusion,
hardware purchase and claims of advantage over Groq are outside this UT milestone.
See [ADR-0132](../decisions/ADR-0132-materialized-array-program.md).

Versioned v2 fusion is described in [ARRAY_FUSION.md](ARRAY_FUSION.md). V1 keeps the exact materialization and saved-proof interpretation above.
