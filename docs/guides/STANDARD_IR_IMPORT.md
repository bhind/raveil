# Pinned standard-IR import

T-0186 / ADR-0110 adds a second owned MLIR fixture to the existing IREE import
route. It maps exactly reviewed source bytes into an existing Raveil graph:

| Manifest in `benchmarks/iree/` | Owned computation |
|---|---|
| `gemm-8x8x8-i32-i64.import.json` | 8x8x8 signed i32 inputs, signed i64 accumulation |
| `gemm-bias-relu-8x8x8-i32-i64.import.json` | Same GEMM, signed i64 bias by column, signed ReLU |

This is a small fixed-fixture adapter. Editing operations, shapes or source text
causes rejection even if the manifest hash is recomputed. The importer does not
parse arbitrary MLIR or translate IREE's output into Raveil instructions.

## Run with the existing pinned compiler

Use an already installed matching compiler by absolute path:

```sh
python3 -m raveil graph-mvp --backend native \
  --import-manifest benchmarks/iree/gemm-bias-relu-8x8x8-i32-i64.import.json \
  --iree-compile /absolute/path/to/iree-compile \
  --minimum-predicted-improvement 0.99 \
  --output /tmp/raveil-import-result.json
```

The result path and adjacent `.import.json` sidecar must not exist. Compiler
3.11.0rc20260316 at revision `e4a3b0405d7d23554da26403658d0e8c3c5ecf25`
is required. No compiler flags/plugins or arbitrary input files are admitted.
The existing native backend generates its deterministic bounded inputs.

For full acceptance with the existing offline image, use a fresh output directory:

```sh
mkdir -p artifacts/research/T-0186

docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,exec,nosuid,nodev -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/raveil:ro" -v "$PWD/artifacts/research/T-0186:/evidence:rw" \
  -w /raveil --entrypoint python3 \
  sha256:b525b868f8d6c40bff3a2e38cf71b73cb85dd8d99f7a3c96f5643b87127a988b \
  scripts/demo_iree_bias_relu.py --iree-compile /usr/local/bin/iree-compile \
  --compiler cc --output /evidence/my-new-run
```

This command reuses the local image; do not infer installation or download
permission when it is absent. The temporary executable filesystem is needed
for native compilation. Sources are read-only and container networking is off.

The demo imports both fixtures, checks the baseline against Pavane's independent
reference, and invokes unchanged owned C materialized/fused functions on four
extra vectors. It checks all512 cells against independent Python arithmetic,
including column broadcast, negative/zero/positive ReLU boundaries and signed
widening beyond i32. Every product, accumulation step and bias addition is checked
for signed i64 range. These extra vectors belong to the acceptance harness;
they do not create a user-input API. Logs, commands, input vectors, outputs,
source hashes and a final receipt remain in the new evidence directory.

## What this proves

The compiler accepts the two pinned standard-IR fixtures. The owned CPU graph
and replay functions pass their numeric checks. Both facts are recorded
separately: the generated VMFB is not executed, so IREE runtime equivalence is
unverified. RTL and QEMU use separate paths. No timing, energy, general compiler,
novelty, FPGA or silicon result follows. A successful policy abstention means
the trusted baseline ran; it does not mean a new optimization was selected.
