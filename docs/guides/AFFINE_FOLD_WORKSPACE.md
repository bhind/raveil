# Run editable affine-fold regions from a project

T-0211 is a local review candidate, not integrated main. It depends on T-0210.
Its RTL simulator reads configurations and data at runtime; no input fixture is
compiled into the binary.

## Build and create a project

From the candidate root, using the already installed Docker image/cache:

```sh
python3 scripts/build_affine_fold_runtime.py artifacts/fold-runtime
python3 -m raveil project init artifacts/fold-project
```

Use a fresh build directory. The command never installs tools or pulls images.
Save this descriptor as artifacts/fold-project/inputs/region.json:

```json
{
  "schema": "raveil.affine-fold.v1",
  "shape": [1, 1], "extent": 4, "fold": "sum",
  "lengths": [4, 4],
  "views": {"a": [0, 0, 0, 0, 1], "b": [1, 0, 0, 0, 1]},
  "nodes": [
    {"id": "a", "op": "load", "view": "a"},
    {"id": "b", "op": "load", "view": "b"},
    {"id": "product", "op": "mul", "args": ["a", "b"]}
  ],
  "result": "product"
}
```

Save inputs/data.json in the same project:

```json
{"schema":"raveil.fold-input/v1","buffers":[[1,2,3,4],[5,6,7,8]]}
```

```sh
python3 -m raveil project fold-check --project artifacts/fold-project --region region.json --input data.json
python3 -m raveil project fold-run --project artifacts/fold-project --region region.json --input data.json --build artifacts/fold-runtime
python3 -m raveil project folds --project artifacts/fold-project
```

The dot product should be [70]. Copy the returned id into:

```sh
python3 -m raveil project fold RUN_ID --project artifacts/fold-project
```

Edit data.json or region.json, then run again with the same build. Existing
records preserve their captured inputs. Compare two successful compatible runs:

```sh
python3 -m raveil project fold-diff FIRST_ID SECOND_ID --project artifacts/fold-project
```

Check/inspection/history/comparison do not execute RTL. A run is successful only
after its full memory trace and output agree with the captured computation.
Incomplete or unsealed runs have no published output; raw artifacts remain for
diagnosis. A cleanup failure leaves an unsealed attempt and requires resolving
the named container state before treating its files as stable.

## Scope and retained acceptance

See [MF01's computation bounds](AFFINE_FOLD_CANDIDATE.md). The new adapter keeps
uint32 arithmetic and existing resource bounds; it does not extend the core.
The retained acceptance uses one executable for32 distinct normal cases plus
input edits, snapshot preservation, cancellation/error and retry:37 invocations,
35 successful results and2 incomplete results,2,041 successful output cells.
All records were reread using the strengthened transaction verifier, with
execution disabled. This is RTL functional simulation, not device performance.

Reproduce in a fresh directory:

```sh
python3 scripts/project_fold_acceptance.py artifacts/fold-runtime artifacts/fold-acceptance
python3 -m unittest tests.test_project_fold tests.test_affine_fold -v
```

The unit tests use host fixtures and never count as actual RTL acceptance.
The acceptance script invokes the real simulator. No board is needed.

A separate coordinated-reset probe also passes six scenarios: validation, read
and write offers under backpressure, read/write response waits, and an already
acknowledged partial output. Resetting the synthetic responder and core together
allows a changed program/input to overwrite old private results correctly.
This uses the same emitted SV in a separate test executable. It does not test
asynchronous reset or a real bus. The workspace runtime itself is unchanged.
