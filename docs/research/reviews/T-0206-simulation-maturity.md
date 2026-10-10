# T-0206 — bounded simulation maturity review

Date: 2026-10-10. Task: [Issue290](https://github.com/bhind/raveil/issues/290),
S-0007,2SP. Authority: ADR-0107, after T-0197/PR289 and T-0205/PR291.
Reviewed implementation: `e74fbe0fdbd6eb01d3a78db35fe91e0f3c1f58aa`.
Primary owns the decision; independent review is advisory. No production code
changes, new EXP/performance claim or weekly Sprint Review acceptance.

## Decision and boundary

The five ADR-0107 criteria are met for the documented bounded project workflow.
This is an editable functional prototype, not arbitrary programs or a complete
processor/product. Graph limits remain16 instructions, eight registers,
324 input/256 output words and admitted8x8 or16x16 transport profiles; named
composition remains one/two sequential private children. QEMU supports the
separate generated GEMM family at dimensions1..8. No shared arithmetic,
QEMU-to-RTL device integration, FPGA fit/timing, energy or superiority is proved.

This closes the simulation-evidence prerequisite for later host/budget planning.
It does not select a board, authorize purchase/install/programming, resolve actual
Windows facts or pass historical performance gates. T-0188/#194 is the existing
next no-install host/budget inventory; physical work remains deferred until its
facts and an affordable reviewed target exist. T-0186 standard-IR work remains
an available later software increment, not an invented blocker to this review.

## Criterion matrix

| ADR-0107 criterion | Applicable executable evidence | Disposition / evidence class |
|---|---|---|
| 1. Edit input/computation, check/run/inspect/compare, retain old snapshots | T-0205 final demo creates A, changes input index11 and bias17→23, reverses child order, creates B, invokes actual comparison CLI, re-inspects A and compares full saved inventories. All1,024 words equal scalar expectations; raw1/64 and biased64/64 changed. Current QEMU `project check` followed by actual run also passes. | Met for bounded workflow. RTL execution + Host Functional comparison; separate QEMU path. |
| 2. Different Graphs on same RTL, independent oracle/fallback | T-0197 raw multiplication and biased multiplication use the same recorded simulator/RTL/source hashes, with both existing oracle and C++ fallback checks. T-0205 changed immediate and input execute on the same build. | Met. Retained final RTL Simulation receipts, source-bound and revalidated now. No elapsed-time benefit inferred from reuse. |
| 3. Frozen input, named private outputs, all-or-incomplete and fresh attempts | T-0197 final complete2-child and cancelled1-child parents revalidate. Host fault/cancel/retry tests cover second-child failure, five publication boundaries, snapshot edits/tamper and fresh retry identities. T-0205 preserves earlier saved parents. | Met. Actual RTL children/between-child host cancellation, plus explicitly labelled host fault injection. No in-flight device-cancel claim from parent demo. |
| 4. Invalid bounds, backpressure, cancellation, reset/recovery | Actual dynamic runner retains malformed-request rejection and eight program-install negative cases. Retained S03 execution verifier passes current source/bundle/input identity: five full256-word completions/fallbacks and1,280 bus-read values, one cancellation, held B/R responses, external reset during BUSY and recovery. Current Sonatine smoke passes owned failure/cancel/rollback checks. | Met at the relevant separate boundaries. Retained RTL device evidence plus fresh QEMU smoke; host tests are not promoted to device execution. |
| 5. Exact source/tools/commands, runnable outcome, limits | Final T-0197/T-0205 receipts and dated log; source-bound replay below; current native build/smoke/project run; retained generic structural verifier. All commands exit0. | Met. Host/RTL/QEMU/structural classes remain separate; no physical or performance evidence. |

## Revalidation and source drift

`artifacts/research/T-0206/revalidation.json` records current saved-parent checks.
T-0197's receipt hashes match the source objects at90cf7a1, not the later whole
composition module. Comparing parsed function ASTs confirms every prior
composition function is unchanged; T-0205 adds the comparison function. Current
readers revalidate the old complete and incomplete parents. This is source
continuity plus retained execution evidence, not a new RTL execution today.
T-0205's three implementation hashes exactly match current files; both parents
and the comparison report regenerate successfully without execution or writes.
No authentication or hostile concurrent-writer guarantee is implied.

Retained checks, rerun now without Docker/Yosys/Verilator invocation:

```sh
python3 -m raveil.graph_device_board_execute verify artifacts/research/T-0189-S03/execution
python3 -m raveil.graph_device_board_preflight verify artifacts/research/T-0189-S03/structural-final
```

Both exit0. Generic structural evidence remains mapping=`not-run`, not FPGA
resource fit. The relevant kernel/core/board source identities still match;
Project CLI changes and the separate dynamic-driver READY fix do not change
that retained board model.

## Fresh native Sonatine / QEMU check

The clean implementation clone initially had no ELF. Existing tools suffice:
`/opt/homebrew/bin/riscv64-elf-gcc`16.1.0, QEMU11.0.3,
`/usr/bin/clang`21; macOS26.6.2 arm64 and Python3.14.6. No installation/download.
Full commands, exit statuses and raw-log hashes: `artifacts/research/T-0206/commands.json`.
The adjacent source manifest covers selected direct sources at revision
`e74fbe0`, not a complete Python import or environment closure. The ignored collector only runs
existing commands; it changes no tracked source.

```sh
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf-
file sonatine/build/sonatine.elf
/opt/homebrew/bin/riscv64-elf-nm -n sonatine/build/sonatine.elf
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- QEMU=/opt/homebrew/bin/qemu-system-riscv64 smoke
python3 -m raveil project init artifacts/research/T-0206/qemu-project
python3 -m raveil project check gemm --backend sonatine-qemu --project artifacts/research/T-0206/qemu-project --sonatine-kernel sonatine/build/sonatine.elf --qemu /opt/homebrew/bin/qemu-system-riscv64 --compiler /usr/bin/clang
python3 -m raveil project run gemm --backend sonatine-qemu --project artifacts/research/T-0206/qemu-project --sonatine-kernel sonatine/build/sonatine.elf --qemu /opt/homebrew/bin/qemu-system-riscv64 --compiler /usr/bin/clang
```

All exit0. ELF is static64-bit RISC-V soft-float ABI. Kernel SHA-256
`8afe23f87a75fb27972087736bd031d1b864ec1de508def15a6e20a887860733`.
Project run `20261010T080918Z-d06f254389cb` is succeeded,
GEMM8x8x8, `qemu-emulation-correctness`, checksum/reference both
`c102cc36c72f8e5c`. Policy outcome is **abstained** and selected variant is
**baseline-ijk**: this verifies the trusted baseline, not a newly optimized
variant or measured performance. The preflight alone said execution not checked;
actual run supplies the execution evidence. Full smoke console is retained.
No fresh debug/GDB/IDE or Docker reproduction was performed; earlier EXP-0002
results remain historical. QEMU is not a physical target measurement.

## Evidence identities and remaining work

- `commands.json`: `1b6cb0c16ab4637cb4528ac966e2d5b7972208cf1fa0db7a8b86c37dce10a63e`.
- `source-manifest.json`: `b501becc3b737dff9d5041855026c304fa72d746a4bcbc37a94d8ec7c7c3d4b9`.
- `revalidation.json`: `fbf598f127159dc210271ca1bbeded7573b1cdf8322f6e9be839e03ade9467e7`.
- `native-build.log`: `59fa38573d776a07f7ac7057e0cf36c49c8a652477061388f2838ff5abba6bc6`.
- `qemu-smoke.log`: `66730772e080cd91c8ccffa756dada784633cad60d85bc9528fd24723116b35e`.
- `project-run.log`: `544f273a512c47ebdd5db7cf93baa6e65f0a8760e1b217b774d73444e53fc777`.
- `board-execution-verify.log`: `19816f8cc938017fbceb975f97e54b0f5684d6ee0b3d67d3651859613ffca5d5`.
- `structural-verify.log`: `003126e7ecdf2a7d1a41147c5e0a9b09eeb77e8bb0d09bae33afefe4da69ce9b`.

T-0188 still needs actual Windows OS/CPU/RAM/free-disk facts and a concrete later
budget/target decision. It does not require buying or installing anything to
collect those facts. Those facts are external to this Mac session; do not infer
them from ownership of a Windows PC. Existing T-0189 hardware work stays Backlog.
No new platform or arbitrary successor was created to hide that dependency.
