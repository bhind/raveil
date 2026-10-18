# Integer image demonstration

This one pipeline uses existing Raveil operations: clamped horizontal difference,
signed ReLU, then2x2 maximum pooling. Input pixels are0..255; height and width must
be even and between2 and64. Admission may reject a large scalar baseline or a
resource-heavy request. The demo does not introduce a new image/model importer.

## Run your image with one command

From the repository checkout, select the existing Sonatine kernel and verified
RTL runtime build explicitly, then choose a fresh output folder:

```sh
python3 -B scripts/image_demo_cli.py run --image my-image.pgm --output "my image run" --kernel /absolute/path/to/sonatine.elf --build /absolute/path/to/verified-runtime --timeout-seconds 900
```

The command admits the image, copies a portable app and its helpers, runs the
existing array coordinator, validates the saved proof and image oracle, and writes
`my image run/report.html`. Stdout gives the exact run ID and report path; progress
and failure diagnostics go to stderr. Open that HTML directly. No server or browser
automation is required. This is a custom functional run, not a performance campaign.

Prerequisites remain Python >=3.11 on POSIX, existing `qemu-system-riscv64`, Docker,
and the exact already-local image identified by the supplied verified runtime.
The kernel/runtime must match the checkout's current RTL sources. This command
does not install, download or compile those prerequisites. See
[the array workspace guide](ARRAY_WORKSPACE.md) for artifact preparation.

Move the whole output folder freely, including to paths with spaces (commas are
unsupported by the existing runtime). `START_HERE.md` contains edited-input and
saved-view commands. Its `scripts/image_demo_cli.py run` also works from any cwd,
using the copied engine; the existing copied kernel/runtime can be supplied again:

```sh
python3 -B "my image run/scripts/image_demo_cli.py" run --image edited.pgm --output "second image run" --kernel "my image run/app/workspace/array-runtime/kernel.elf" --build "my image run/app/workspace/array-runtime/runtime"
```

Every run destination must be new. Invalid inputs or artifacts fail before its
creation. Interrupted preparation or execution retains its incomplete directory;
retry with a fresh destination. Stop exit codes remain130/143/124. Array result
commit and HTML publication are separate: if report creation fails after a valid
array commit, the error identifies the saved attempt and `array_committed=true`.
Use the packaged `view` command below with that ID and a fresh HTML filename.
A stop arriving after the array commit can finish displaying the completed result.
No failed or incomplete array is rendered as a success. Exclusive atomic report
publication preserves any existing destination and never exposes a partial HTML.

## Preserved experiment delivery

The EXP-0013 delivery folder contains report.html, raw evidence, an app/ folder,
owned PGM examples under data/, and scripts/ for new images and verified views.
Open report.html to compare measured outputs and the frozen scalar/fused runs.
The report runs locally without a server or network.

From the delivery folder, reuse a packaged example:

```sh
./app/raveil array-doctor
./app/raveil array-run --input blocks-16-fused.json --timeout-seconds 900
./app/raveil array-output --format csv
```

To replace its16x16 input with an integer CSV, preserving every old input/result:

```sh
./app/raveil array-import --stage gradient --slot 0 --csv my-16x16.csv --input blocks-16-fused.json --output my-image.json
./app/raveil array-run --input my-image.json --timeout-seconds 900
python3 -B scripts/image_demo_cli.py view --project app/workspace --id PRINTED_RUN_ID --output my-result.html
```

For a different image shape, generate the matching computation from a binary PGM:

```sh
python3 -B scripts/image_demo_cli.py prepare --image data/diagonal-24.pgm --output app/workspace/inputs/my-pgm.json
./app/raveil array-run --input my-pgm.json --timeout-seconds 900
python3 -B scripts/image_demo_cli.py view --project app/workspace --id PRINTED_RUN_ID --output my-pgm-result.html
```

PGM input uses the explicit byte header `P5\nWIDTH HEIGHT\n255\n`, followed by
exactly WIDTH*HEIGHT pixel bytes. No comments or alternate image formats are
decoded. Prepare and view use exclusive atomic file publication. Choose a fresh output
filename; neither command overwrites an existing file. Viewing
fully validates saved evidence and the exact image pipeline without executing it.
The displayed activated and pooled values are actual verified outputs. Raw signed
gradients are available as uint32 bit patterns in array-output.

The new input's actual shape must equal the declared computation for this viewer;
array-import alone does not reshape computation. Keep all captured array folders
unchanged. Ctrl+C and timeout use the existing foreground cleanup and fresh-retry
contract. Existing installed Python/QEMU/Docker and the pinned local image are
required. No hardware is needed for this simulation demo.

The frozen experiment and custom interactive runs are separate. A later custom
run does not enter the comparison table or revise its conclusion. See
[EXP-0013](../experiments/EXP-0013-image-fusion-comparison.md) for exact measurement
boundaries and inference limits.
