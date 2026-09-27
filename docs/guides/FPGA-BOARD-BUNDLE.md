# Offline FPGA boundary bundle — T-0189/S01

This prepares the existing Graph device for later board integration. It is not
a board image. The wrapper expects absolute32-bit AXI4-Lite addresses, one
aligned16-KiB window, a single clock and active-low reset. ADR-0106 specifies
the address/reset contract. Production Graph core and ABI are unchanged.

## Build and verify without purchases

Run from the matching repository checkout. The input export must already pass
its existing source/repeat/ABI checks. Output must be new, below `artifacts/`.
The following base and100MHz constraint are commissioning examples only:

```sh
python3 -m raveil.graph_device_board_bundle create \
  artifacts/research/T-0203/axi-rtl artifacts/research/T-0189-S01/board-bundle-v2 \
  --base 0xa0000000 --clock-mhz 100
python3 -m raveil.graph_device_board_bundle verify \
  artifacts/research/T-0189-S01/board-bundle-v2
python3 -m unittest tests.test_graph_device_board_bundle tests.test_graph_device_axi4lite_export -v
```

The bundle includes the complete verified export under `core/`, the owned
wrapper, candidate Tcl, plain numeric settings and generated clock constraint.
Keep the matching checkout alongside it when transferring to Windows. Hashes
are input-integrity checks, not a trust signature or physical-design identity.
Verification compares exact bytes; use a checkout preserving repository LF
line endings. Do not source a downloaded/untrusted Tcl before inspecting it.

## Actual-core simulation

Use the already-cached image; this command does not fetch tools. Create a new
empty run directory (nonempty output is rejected), and preserve stdout/error and returned exit status. The
script tests all three bases independently (0,a0000000,ffffc000), regardless of
the bundle's candidate synthesis base; it also requires base4 to fail elaboration.

```sh
mkdir -p artifacts/research/T-0189-S01/rtl-run-reviewed
docker run --rm --pull=never --network none --platform linux/amd64 \
  --mount type=bind,src="$PWD/artifacts/research/T-0189-S01/board-bundle-v2",dst=/bundle,readonly \
  --mount type=bind,src="$PWD/hardware/fpga",dst=/src,readonly \
  --mount type=bind,src="$PWD/artifacts/research/T-0189-S01/rtl-run-reviewed",dst=/out \
  sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c \
  bash /src/test-board-bridge-in-container.sh
```

Tests cover identity in all three relative apertures, out-of-window/high aliases,
unaligned addresses, partial strobes, holes/readonly words, split AW/W, held
responses, reset abort of each partial write and each held response, release
with VALIDs held, and the original software-reset response/barrier. This is
control-plane RTL simulation, not a workload benchmark or board commissioning.
The host test fixture and mocked vendor commands supply no RTL/vendor evidence.

## Candidate vendor step — not executed yet

After T-0188 confirms the actual supported Windows host and an authorized
Vivado2025.1 environment, run from a separate working directory with explicit
log/journal paths. Supply the exact installed part chosen for the prospective
board; no guessed part is embedded. `python` must identify the interpreter for
the matching checkout. Paths can be quoted normally in the host shell.

```text
vivado -mode batch -source <bundle>/synth_board_bridge.tcl
  -tclargs <matching-repository> <bundle> <new-output-directory> <exact-part> <python-executable>
```

This is one shell command; the display line break above is explanatory. The
recipe verifies the bundle, validates version/part, reads only root production
SV modules, applies base/clock, synthesizes out of context and rejects black
boxes. It saves estimated timing, utilization and a checkpoint. Failed runs
may leave partial diagnostic output; preserve it and choose a new directory
for retry. A partial directory or checkpoint alone is not success.

No Vivado command, part availability, resource fit or timing closure has been
observed here. The recipe's syntax/control flow was checked with Tcl mocks.
Command choices follow AMD UG8352025.1 `synth_design`, Usage and `-mode`:
https://docs.amd.com/r/2025.1-English/ug835-vivado-tcl-commands/synth_design

Later board integration must establish PS/PL clock/reset wiring, address
convention and assigned segment, physical reset recovery/removal and CDC checks,
implementation constraints, exact board/pin/part identity, deployment and matching
UIO map. It must quiesce the upstream master around resets. This wrapper does
not convert clocks, add transport, isolate initiators or provide interrupts.
T-0189 remains open until that design and real execution/recovery are verified.
Initial incremental spend remains zero; nothing in this recipe authorizes an
installation, license acceptance, purchase or device write.
