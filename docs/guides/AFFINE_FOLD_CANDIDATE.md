# Affine map/fold local candidate

T-0210 / Proposed ADR-0114. This standalone simulation candidate is not yet
integrated into the Raveil project CLI, QEMU or the board interface.

## Express a dot product

Save the following as a JSON file. Both arrays contain four uint32 words.
The output is one uint32 dot product, with arithmetic modulo2^32.

```json
{
  "schema": "raveil.affine-fold.v1",
  "shape": [1, 1],
  "extent": 4,
  "fold": "sum",
  "lengths": [4, 4],
  "views": {
    "left": [0, 0, 0, 0, 1],
    "right": [1, 0, 0, 0, 1]
  },
  "nodes": [
    {"id": "a", "op": "load", "view": "left"},
    {"id": "b", "op": "load", "view": "right"},
    {"id": "product", "op": "mul", "args": ["a", "b"]}
  ],
  "result": "product"
}
```

`python3 -m raveil.affine_fold dot.json` validates and emits65 configuration
words. In Python, `reference(descriptor, [[1,2,3,4], [5,6,7,8]])` returns
`[70]`. This command compiles configuration; it does not invoke the RTL.

Each view is `[buffer, offset, iStride, jStride, kStride]`; it reads
`input[buffer][offset+i*iStride+j*jStride+k*kStride]`.
The output shape fixes i,j; extent fixes k; fold is sum or unsigned max.
Extent1 performs a map. Zero strides broadcast. Transpose exchanges i/j strides.
For M×K by K×N multiplication, views are `[0,0,K,0,1]` and
`[1,0,0,1,N]`, output shape `[M,N]`, extent K.

Limits: two324-word input spans, eight views, dimensions1..16, extent1..64,
eight scalar registers, at most15 map nodes plus final yield. Nonnegative
strides only. Supported map ops: load, add, mul, max, add_imm, ge_imm.
SSA nodes must appear in dependency order. The compiler rejects excess live
registers; it does not spill. No floating-point or signed arithmetic.

## Reproduce the owned functional probe

Run from the candidate root. Use a fresh evidence directory for every attempt.

```sh
python3 -m unittest tests.test_affine_fold -v
python3 scripts/affine_fold_vectors.py artifacts/research/T-0210/fresh-run
```

The next command assumes Docker and the exact previously installed image/cache.
It disables network access and mounts source/dependencies read-only. Never
substitute a pull/build/install step when either resource is absent.

```sh
docker image inspect sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c
docker volume inspect raveil-chisel-scala-cache-v1
docker run --rm --network none --platform linux/amd64 \
  --mount type=bind,src="$PWD",dst=/source,readonly \
  --mount type=bind,src="$PWD/artifacts/research/T-0210/fresh-run",dst=/evidence \
  --mount type=volume,src=raveil-chisel-scala-cache-v1,dst=/root/.cache,readonly \
  sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c \
  sh /source/hardware/chisel/run-affine-fold-in-container.sh
python3 scripts/verify_affine_fold_probe.py artifacts/research/T-0210/fresh-run
```

The harness builds one simulator and invokes71 cases under three memory-stall
seeds without resetting between cases. The generated C++ fixture table contains
inputs/configurations/oracles; the RTL has no per-workload variant. Editing the
fixture generator requires rebuilding the harness; this is not yet a general
user-facing simulation service.

The retained run-03 passed213 cases and6,117 cell comparisons, including6114
ordinary functional comparisons and3 immutable-configuration checks. Its
780,348 accepted transactions all have matching responses in the saved trace.
The testbench checks request stability while stalled and disallows publication
after cancellation/error; saved verification rechecks read data, output words,
counts, admission and hashes without executing the simulator.

run-01 is a retained failed attempt: configuration index width wrapped at the
sixteenth instruction. run-02 passed162 cases after the width fix. run-03 adds
combined maxima, richer admission tests and cancellation/error boundaries.
Finite seeded tests are not a proof of all protocol interleavings.
Coordinated reset with an outstanding response is specified but untested here.

The memory model owns private outputs. A cancelled write may leave bytes there,
but only the core's success flag authorizes a complete result. Callers must keep
inputs immutable, preserve request/response ownership and eventually answer
requests. No timeout, physical timing, FPGA fit, speed or energy is promised.
