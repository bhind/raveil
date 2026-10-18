# Integer image demonstration

This one pipeline uses existing Raveil operations: clamped horizontal difference,
signed ReLU, then2x2 maximum pooling. Input pixels are0..255; height and width must
be even and between2 and64. Admission may reject a large scalar baseline or a
resource-heavy request. The demo does not introduce a new image/model importer.

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
decoded. Prepare uses exclusive ordinary file creation; if interrupted, inspect
or choose a fresh output filename. It never overwrites an existing file. Viewing
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
