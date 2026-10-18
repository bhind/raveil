# Prepared array workspace

Prepare once, then edit and execute with short commands. This uses the unchanged
integer-array source, QEMU and functional RTL runtime; it does not require a board.
Python 3.11 or later and POSIX filesystem APIs are required. Native Windows is not
supported. The tested delivery target is the owner's existing macOS environment.

## First use from a clean checkout

The common engine accepts integer-array graphs. Images are one optional client;
this path starts with matrix multiplication and also runs linked arithmetic,
transpose, reductions and fanout/join without a different compiler or RTL.

Inspect the existing offline build/runtime tools first:

```sh
python3 -B scripts/check_array_prerequisites.py
```

Exit0 means the listed tool checks passed; exit2 names the missing, incompatible
or timed-out probe. This is inspection only, not proof of compilation or execution.
The command never installs, pulls an image, creates a volume or launches a job.
It checks Python/POSIX, QEMU, the pinned local linux/amd64 Docker image, GNU Make,
the RISC-V GCC target and its assembler/linker, and the existing Scala cache volume.
Host Scala, Verilator, GDB and readelf are not required for this release-build path.
An existing cache volume can still lack a dependency: the offline build below is
what establishes that it is sufficient. Keep failed build logs; do not silently
allow network access to repair a missing cache.

Compiler selection follows the Makefile: honor `CROSS_COMPILE` if set (including
empty), otherwise prefer `riscv64-unknown-elf-` then `riscv64-elf-`. To select an
existing compiler explicitly, use the same environment prefix for both preflight
and make. A native host GCC target fails this inspection.

Use a checkout and kernel-build path without whitespace or commas. The unchanged
Makefile has unescaped target paths; prepared applications may still use spaces.
Choose fresh directories, preserving prior builds and apps. From the checkout:

```sh
(
set -eu
test ! -e sonatine/build/first-use
test ! -L sonatine/build/first-use
make -C sonatine BUILD_ROOT=build/first-use DEBUG=0 all
python3 -B scripts/build_affine_fold_runtime.py artifacts/first-use-runtime
python3 -B scripts/prepare_array_app.py --output artifacts/first-use-app --kernel sonatine/build/first-use/sonatine.elf --build artifacts/first-use-runtime --source examples/array-program/fused-gemm.json
artifacts/first-use-app/raveil array-doctor
artifacts/first-use-app/raveil array-check
artifacts/first-use-app/raveil array-run --timeout-seconds 300
)
```

Read the printed run ID, then inspect it with
`artifacts/first-use-app/raveil array-output PRINTED_RUN_ID`.

Stop the sequence if a command fails. `BUILD_ROOT` is a make command-line assignment;
do not use `make clean` or overwrite a previous build. The runtime builder uses
`--pull=never --network none`, the pinned image, and the read-only existing cache.
It never downloads dependencies. The app is portable after preparation; original
build paths are not required. Saved outputs remain functional QEMU/RTL evidence,
not evidence of a speed advantage over a CPU.

To inspect just external runtime tools from a checkout, use
`python3 -B scripts/check_array_prerequisites.py --run-only`. It does not require
GCC, Make or the build cache. It does not inspect an app's artifacts; the prepared
app's `array-doctor` verifies its copied kernel/runtime and current source binding.
For an already prepared app, start directly with that doctor.

Change computation using a fresh input name on the same runtime:

```sh
(
set -euC
cd artifacts/first-use-app
test ! -e workspace/inputs/linked-transpose.json
test ! -L workspace/inputs/linked-transpose.json
cat engine/examples/array-program/fused-stages.json > workspace/inputs/linked-transpose.json
./raveil array-check --input linked-transpose.json
./raveil array-run --input linked-transpose.json --timeout-seconds 300
)
```

This example is a long arithmetic map followed by transpose. The separate
[common array source guide](ARRAY_PROGRAM.md) documents stage links, fanout,
reductions and numerical/resource limits. This is not arbitrary CPU-program
translation; image examples do not define the engine's intended scope.

## Ready application directory

From a source checkout with a verified kernel and runtime:

```sh
python3 scripts/prepare_array_app.py --output /path/to/new-app --kernel /path/to/sonatine.elf --build /path/to/verified-runtime
cd /path/to/new-app
./raveil array-doctor
./raveil array-check
./raveil array-run
./raveil array-output
./raveil array-output --format csv > result.csv
```

The output directory must be new. It contains its own Python engine, current RTL
source identity files, copied kernel/runtime and editable workspace. The whole
directory can move. Its launcher locates the adjacent engine/workspace independently
of the current working directory. No original build or research-artifact path is
required. QEMU, the Docker daemon and the exact pinned Docker image remain external
prerequisites. Preparation/doctor never download or install them. The Scala cache
volume and RISC-V compiler are needed to rebuild, not to execute a prepared app.

Edit `workspace/inputs/program.json` and repeat `./raveil array-run`. The default
example is a 24-node map followed by transpose, with two named outputs. More
editable examples are under `engine/examples/array-program/`; copy one over
`workspace/inputs/program.json` to change the workload, then check it before running.

```sh
./raveil arrays
./raveil array-output SAVED_ID --name transpose
./raveil array-diff FIRST_ID SECOND_ID
```

CSV is long-form `output,row,column,value`; values retain uint32 bit patterns.
JSON includes output names, shapes and words. Both formats verify the entire saved
parent first and suppress incomplete/unsealed/tampered results. Saved readers do
not run QEMU or Docker. An omitted output ID chooses the latest timestamp, including
failed attempts; ties require an explicit ID. It never falls back to older success.
Redirection to a file follows ordinary shell overwrite rules; the CLI writes stdout.

The application marker is published atomically without overwriting an earlier
marker. A missing/malformed marker means preparation did not complete; create a
fresh directory. app.json records provenance, not a cryptographic signature.
The launcher disables bytecode writes so ordinary use leaves its engine inventory
unchanged. Edit workspace inputs, not the copied runtime or captured attempts.

## Existing checkout CLI

```sh
scripts/raveil project array-prepare /path/to/new-work --kernel KERNEL_ELF --build VERIFIED_RUNTIME
scripts/raveil project array-doctor --project /path/to/new-work
scripts/raveil project array-run --project /path/to/new-work
scripts/raveil project array-output --project /path/to/new-work --format csv
```

Optional `--source FILE` selects the initial source. Check/run default to
inputs/program.json; `--input FILE.json` remains available. `array-run` accepts
either both `--kernel` and `--build` or neither. Omission uses copied artifacts;
explicit invocation and existing saved records retain their previous behavior.
`array-run --summary` omits captured-file inventory from stdout while retaining
full saved evidence. The local app launcher enables this display option by default.

## Failure and readiness

Doctor exits0 only when prerequisite checks pass, otherwise2 with individual
failures. It is not a proof of kernel ABI compatibility or successful computation;
run the example to establish that. Missing Docker/image/QEMU checks do not trigger
installation. Copied artifact/source-identity damage requires a fresh prepared
workspace. Commas in execution paths are unsupported by the current mount syntax.

Invalid source/admission fails before creating an attempt. Runtime interruption
can leave an incomplete or unsealed attempt, which is retained for diagnosis and
never resumed or overwritten; retry is a fresh run. This common-array path remains
bounded to 64x64 shapes, uint32 arithmetic with explicit signed operators, static
control and existing resource/capture limits. It is not an arbitrary model runtime
or a physical performance result. See [array fusion](ARRAY_FUSION.md) and
[ADR-0134](../decisions/ADR-0134-prepared-array-workspace.md).

## Foreground progress and stopping (T-0239 candidate)

The prepared launcher shows pass/session/job progress on stderr. Redirecting stdout
to a JSON file still captures only the final verified result. The checkout CLI
enables the same stream with `project array-run --progress`. Optional
`--timeout-seconds 300` bounds the whole foreground execution, including preflight
and pre-publication validation. Values must be finite, from 0.01 to 86400 seconds.

Ctrl+C requests cancellation; SIGTERM requests termination. New dispatch stops and
owned processes are cleaned up. Exit codes are 130 (Ctrl+C), 143 (SIGTERM), 124
(timeout), 2 (failure), or 0 (verified success). Cleanup has separate bounded waits
and can finish after the requested deadline. SIGKILL/process crashes cannot ensure
cooperative cleanup. A request racing atomic result publication may find already
completed work; committed proofs are never revoked.

The stderr diagnostic includes the attempt ID when allocated. `arrays` distinguishes
unsealed attempts from verified records. An unsealed attempt has no published
output, so `array ID`/`array-output ID` will reject it. Keep its directory unchanged
and run a fresh attempt. Progress is diagnostic, never a proof or partial output.
See [ADR-0135](../decisions/ADR-0135-foreground-array-run-control.md).
