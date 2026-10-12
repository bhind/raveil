# EXP-0002: Sonatine Microkernel RV64 reproducibility

## T-0236 common-source functional execution — 2026-10-12

Fresh real QEMU/RTL acceptance verifies27 sealed array parents:24 successful,
3 intended incomplete,4562 published words.177 distinct sealed DAG receipts record
177 processed jobs,174 approvals and3 injected rejections. A separately preserved
unsealed attempt contains one verified real RTL cancellation, followed by coupled
option-binding rejection. Do not count it as a sealed/approved DAG session or as
a supported public cancellation command.

Coverage includes long24-node maps,9 live values, all source operators, two GEMM
shapes,3 boundaries, wrapped fold then post,17x19 tiling,64x64 broadcast,8 inputs,
8 stages/outputs and fanout/join. Frozen source edits compare correctly. All sealed
parents revalidate without execution. Full failed-tree preservation including seals
is established by the supplementary failure/retry; the main campaign establishes
captured-content inventory preservation and valid failed-parent reinspection.

Existing kernel SHA256 `35db85f0018595fe4c68d425f5071c39072b9eb35095477b8d4cdec1ebee49f9`
and runtime identity `bdb6eefe93fe768fa2aa656b9354dcf5c7a4c28107b7dd979c49902b322a18ab`
are reused with current-source verification. Evidence is functional QEMU emulation
plus RTL simulation, never FPGA/silicon timing, energy or Groq comparison. This
entry adds functional evidence without changing scientific fields or gate/EXP
conclusions. Exact commands and receipts: local T-0236 packet and October12 log.

Status: Completed
Evidence class: QEMU emulation and host-tool inspection
Last updated: 2026-10-11

## Objective

Reproduce the freestanding RV64 build and Sonatine Microkernel (Sonatine) shell from the real Git tree,
verify command-line QEMU/GDB independently of the IDE, and record enough
environment information for Gate 0.

## Environment observed

- MacBook Air `Mac14,15`, Apple M2, 24 GB;
- macOS 26.5.1 build 25F80, arm64;
- original smoke evidence Git revision:
  `d4204e10f62b4d232c6fdcf8a02a098cee595d3a`;
- debug/GDB evidence base revision:
  `88b44d11b777c02f1963c835e99bb317f6d94dbd`, with the Makefile, test,
  and matching record updates uncommitted during collection;
- `riscv64-elf-gcc (GCC) 16.1.0`;
- `GNU gdb (GDB) 17.2`;
- `QEMU emulator version 11.0.3`;
- Homebrew executable prefix: `/opt/homebrew/bin/`.

Machine serials and unique identifiers are intentionally not recorded.

## Build evidence

A user-operated native build had already generated
`sonatine/build/sonatine.elf`. On 2026-08-08, `file` identified it as:

```text
ELF 64-bit LSB executable, UCB RISC-V, RVC, soft-float ABI,
version 1 (SYSV), statically linked, not stripped
```

`riscv64-elf-nm` confirmed `_start`, `trap_entry`, and `kmain`.

## QEMU smoke command

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  smoke
```

Exit status: 0.

Console transcript:

```text
Raveil boot v0.0000000000001
Sonatine kernel (RV64 QEMU virt)
  [ok] console / ns16550a polled UART
  [ok] physical memory / 4 KiB bitmap allocator
  [ok] capability / generation-checked fixed table
  [ok] task / init + idle kernel tasks
  [ok] IPC / bounded mailbox protected by capabilities
  [ok] timer / CLINT machine timer at 100 Hz
starting init task id=1

Raveil shell v0.0000000000001
type 'help' for commands

raveil> info
Raveil 0.0000000000001 / Sonatine RV64 / QEMU virt / M-mode
authority: one hart; paging: off; user isolation: not yet
raveil> mem
RAM pages total=32768 free=32759 first-free=0x80009000
raveil> ps
id  state    name
1   running  init
2   ready    idle
raveil> caps
handle      owner type object rights
0x10001  1     2    1      0x1c
0x10002  1     1    1      0x11
raveil> ticks
0
raveil> ipc
ipc: received tag=0x52 sender=1 word0=0x52415645494c
raveil> alloc
alloc: page=0x80009000 free 32759 -> 32758 -> 32759 (released)
raveil> reboot
leaving QEMU
raveil>
```

Raw ignored log: `sonatine/build/smoke.log`
SHA-256:
`314c185549dfd5e11e48f467320ac871e3862960bdb4d02d40ba86c909c0475f`

## Clean release and debug builds

Commands:

```bash
make -C sonatine clean
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf-
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- check-debug
```

All commands exited 0. The release compiler command retained `-Os` and its ELF
had no `.debug_info` or `.debug_line`. The debug build used `-Og -g3` for
C and `-g3` for assembly in a separate `build/debug/` directory.

```text
[ 9] .debug_info  PROGBITS
[15] .debug_line  PROGBITS
[17] .debug_line_str PROGBITS
```

`file` identified the debug artifact as a 64-bit RISC-V ELF with
`debug_info`, not stripped. Its SHA-256 was
`a2852e69e65c21130f19d8b7f2872640a6510eec11a321ef35f40ea499b42125`.

The rebuilt release ELF then passed `make ... smoke` with exit status 0.

## Command-line GDB evidence

Terminal 1:

```bash
make -C sonatine \
  CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf- \
  QEMU=/opt/homebrew/bin/qemu-system-riscv64 \
  debug
```

Terminal 2 used the equivalent of the repository's interactive `make gdb`
target while enabling an ignored raw log:

```bash
/opt/homebrew/bin/riscv64-elf-gdb -q -batch \
  sonatine/build/debug/sonatine.elf \
  -ex 'target remote 127.0.0.1:1234' \
  -ex 'break kmain' \
  -ex 'continue' \
  -ex 'info breakpoints' \
  -ex 'frame' \
  -ex 'list' \
  -ex 'detach'
```

Exit status: 0.

```text
Breakpoint 1 at 0x800006ce: file src/kernel.c, line 25.

Breakpoint 1, kmain () at src/kernel.c:25
25  void kmain(void) {
breakpoint already hit 1 time
#0  kmain () at src/kernel.c:25
```

Raw ignored log: `sonatine/build/debug/gdb-kmain.log`

SHA-256:
`26f0eadfe5a71803e58e554486479b5d7d927de599181fdf886d50f64e0780fd`

The interactive `make debug` plus `make gdb` path was also run and stopped at
the same source line. The first sandboxed attempt could not bind/connect to
localhost; the successful evidence was collected with local TCP permission.

## Clean Docker build and smoke

Environment:

- Docker Desktop 4.85.0;
- Docker client/engine 29.6.2;
- client `darwin/arm64`, engine `linux/arm64`;
- LinuxKit kernel 6.12.76, overlayfs;
- container GCC 12.2.0;
- container QEMU 7.2.22.

The first no-cache image build exposed a validity defect: host
`sonatine/build/` occupied a 1.01 MB context and the Dockerfile reported
`Nothing to be done for 'all'`. That image was rejected as Gate evidence.
`sonatine/.dockerignore` now excludes `build/`, and the Dockerfile runs
`make clean && make`.

Successful clean command:

```bash
docker build --no-cache --progress=plain \
  --iidfile <temporary-iid-file> \
  -t raveil-sonatine:gate0-clean-20260808 \
  sonatine
```

Exit status: 0. The context was 1.18 kB. The log showed `rm -rf build`, all
ten C compilations, both assembly compilations, and the final RV64 link with
release `-Os`. Base image:
`debian:bookworm-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241`.
Result image ID:
`sha256:3225bf6bc3ae06f872e384704499e93f3069629a11dba70f6c4b23a3ad71bf9c`.

Smoke command:

```bash
docker run --rm raveil-sonatine:gate0-clean-20260808 make smoke
```

Exit status: 0. The console contained all six boot `[ok]` lines, the shell,
task and capability tables, successful IPC, page allocation/release, QEMU
finisher exit, and both final grep checks.

Raw temporary smoke log: `raveil-gate0-docker-smoke-20260808.log`

Size: 1018 bytes

SHA-256:
`e6d9a39352cbf598abe834e59365c8f0616db91352b5d2433be5c25542aba0c2`

Evidence class: Docker Desktop Linux/arm64 QEMU emulation, not FPGA or silicon.

## IntelliJ configuration inspection

The installed IntelliJ IDEA 2026.2.0.1 C/C++ and Native Debug plugins expose
`Remote Debug` (type `CLion_Remote`) for an existing GDB stub. `Remote GDB
Server` is a different SSH/upload workflow and is not appropriate for
Sonatine. No Sonatine Remote Debug configuration currently exists, and
IDE-driven `kmain` attachment was not claimed.

## Public clean-clone and CI verification

Public commit: `33470874dd54f577ad3a60320487f6e14b096b9b`

The repository was cloned from `https://github.com/bhind/raveil.git` into a
new temporary directory. The following commands all exited 0:

```bash
python3 -m unittest discover -s tests -v
make -C sonatine clean all CROSS_COMPILE=riscv64-elf-
make -C sonatine check-debug CROSS_COMPILE=riscv64-elf-
make -C sonatine smoke CROSS_COMPILE=riscv64-elf-
```

All nine tests passed. The release and isolated debug builds completed,
`.debug_info` and `.debug_line` were present in the debug ELF, and the smoke
log contained the shell and successful IPC markers.

The same verification is exposed locally as:

```bash
scripts/ci-local.sh
```

A GitHub Actions workflow run (`31248762110`) completed successfully before
the project owner clarified that hosted CI/CD must not be used because of cost.
The workflow was removed immediately afterward. This historical run is not the
current CI policy or a dependency of Gate 0.

The public tracked-file list contained no build directories, IDEA state,
Python bytecode, generated JSONL evidence, or `.env` files. A content scan
found no private-key marker, GitHub credential pattern, or machine-local home
directory path.

Evidence class: fresh public Git clone plus local macOS/QEMU emulation. This
remains software/emulation evidence, not FPGA or silicon evidence.

## Remaining work

None for Gate 0.

QEMU success is emulation evidence only; it does not establish U-mode
isolation, preemptive scheduling, FPGA timing, or silicon behavior.

## 2026-10-10 — T-0206 native continuation (separate evidence)

The current implementation clone at `e74fbe0` freshly built Sonatine with existing
GCC16.1.0, passed the current full QEMU11.0.3 smoke and ran the supported project
GEMM8x8x8 baseline with equal checksum/reference `c102cc36c72f8e5c`. Policy
abstained; no optimized-variant or timing claim. Kernel hash, exact commands,
source manifest, complete console and log hashes are in
[T-0206](../research/reviews/T-0206-simulation-maturity.md) and the October10 log.
This is native QEMU emulation, not FPGA or silicon. No new Docker reproduction,
debug/GDB or IDE attachment was tested. Historical Gate0 evidence and task
completion remain unchanged; this continuation does not re-certify those surfaces.

## 2026-10-11: T-0212 local native regression evidence

The local candidate over canonical a58e5a5 adds an MF01 software interpreter.
Existing native RV64 build, Sonatine shell smoke and graph-smoke all pass using
riscv64-elf-gcc16.1.0 and QEMU11.0.3 on macOS arm64. The retained command and
raw-log inventory is in artifacts/research/T-0212 inside the candidate. Commands:

```sh
make -C sonatine CROSS_COMPILE=/opt/homebrew/bin/riscv64-elf-
make -C sonatine smoke graph-smoke
python3 scripts/sonatine_fold_acceptance.py --kernel sonatine/build/sonatine.elf --output artifacts/research/T-0212/acceptance-01
```

All exited0.34 functional emulation successes checked2,174 words;29 invalid
requests were rejected. These are local QEMU correctness results, not Gate0
reopening or performance measurements. No new debug-symbol, GDB, IDE, Docker
Sonatine reproduction or clean-clone claim is made. The separate RTL comparison
is recorded in the October11 log, not attributed to QEMU hardware.

## 2026-10-11: T-0213 local regression and coupling boundary

After adding guest UART dispatch/response handling, native `make -C sonatine`
and `make -C sonatine smoke graph-smoke` again exited0. Tool versions remain
GCC16.1.0/QEMU11.0.3 on macOS26.6.2 arm64. Candidate raw build and smoke logs,
source identities and kernel SHA are under artifacts/research/T-0213. Gate0
and earlier debug/IDE claims do not change. The42 coupled runs have their own
class, host-mediated-QEMU-RTL-functional-coupling, described in Proposed
ADR-0117 and the dated log; they are not silicon or timing measurements.

## 2026-10-11: T-0214 local native session regression

Existing GCC16.1.0/QEMU11.0.3 build and `make -C sonatine smoke graph-smoke`
exit0 after adding bounded sessions. Complete logs and kernel/source hashes are
under candidate artifacts/research/T-0214. This is native functional regression
only; Gate0, debug/GDB/IDE and earlier emulation evidence remain unchanged.
Coupled session results have their own functional class in ADR-0118 and the log.

## 2026-10-11: T-0215 local native dependency regression

Native RV64 build and shell/GEMM smoke again pass with existing GCC16.1.0/QEMU11.0.3.
The new chain has independent functional evidence in ADR-0119 and the dated log.
No Gate0/debug/IDE, physical performance or hardware claim changes. Raw command
logs/source/kernel identities are retained under local artifacts/research/T-0215.

## 2026-10-11: T-0216 local native DAG regression

Existing GCC16.1.0 native build and QEMU11.0.3 shell/GEMM smoke pass after adding
whole-DAG admission. Main coupled evidence is separately classified in ADR-0120
and the dated log. Initial build-01 failed on misleading C indentation; build-02
passes after explicit line separation. Both logs are retained. Gate0 and prior
debug/IDE/hardware/performance conclusions remain unchanged.

## 2026-10-11: T-0219 local subrange native regression

Existing GCC16.1.0/QEMU11.0.3 on macOS26.6.2 arm64 builds the v1/v2 DAG decoder
and segmented submission-snapshot reader. Final build-02 and smoke-02 logs pass
native shell/GEMM regression after the zero-length linked-input correction.
Exact commands/hashes are in the dated log. Fresh coupled range cases are
separately classified as functional host-mediated QEMU/RTL evidence. Gate0,
Docker clean-clone, debug/IDE, physical and performance conclusions are unchanged.

## T-0223 local clean-archive supplement — 2026-10-11

Canonical a58e5a5 plus the retained T-0222 cumulative patch reproduces all 112
candidate file hashes. A fresh native release build with Homebrew GCC 16.1.0
is byte-identical to T-0219; shell smoke and legacy QEMU/native GEMM comparison
pass under QEMU 11.0.3 on macOS 26.6.2 arm64. The 131 selected host tests pass.
Commands, exact paths, environment and raw-log hashes are in the dated log.

Offline Chisel/runtime rebuilding also passes using the existing image/cache.
All 14 source/emitted-RTL/simulator/toolchain files match the retained runtime;
no build-log/manifest identity is inferred. Eight coupled grid cases reproduce
40 sessions/806 words, and a maximum-input case using both rebuilt executables
checks 36 more words and saved revalidation. These are functional QEMU/RTL
and host-tool facts, not physical performance or an experiment/gate transition.

This is a fresh archive plus patch, not a fresh remote clone or new Docker image
rebuild. No new debug-symbol, GDB or IDE evidence was collected; historical Gate 0
task statuses and conclusions remain unchanged.

## T-0233: fresh unsigned flow continuation, October 11

Current host source is a clean canonical archive plus the T-0232 cumulative patch;
all144 inherited file hashes match before and after execution. Existing T-0223
Sonatine ELF SHA256 `35db85f0018595fe4c68d425f5071c39072b9eb35095477b8d4cdec1ebee49f9`
and RTL runtime digest `bdb6eefe93fe768fa2aa656b9354dcf5c7a4c28107b7dd979c49902b322a18ab`
are reused. QEMU11.0.3 and the existing amd64 Docker image
`sha256:2efc059cf07eb054d93fc1fa32decd7a13c2cdb97069dac29138275b22e5c57c`
run on Darwin25.6.0 arm64; Docker client/server29.7.2, Python3.14.6.

Eight new flow parents execute61 QEMU/RTL sessions and76 jobs:75 accepted and one
intentionally wrong transport word rejected. Seven complete parents publish201
final words; the incomplete parent publishes none. Fresh eight-stage retry produces
64, preserves the full failed tree and matches the earlier successful output.
Selected diamond uses four sessions and agrees with the freshly executed16-session
baseline. The copied baseline in the planner workspace is excluded from counts.
Receipt-derived counting and saved validation pass with process creation disabled.

Exact commands, complete raw logs and hashes are in the October11 T-0233 log and
local evidence manifest. This is functional host-mediated QEMU/RTL coupling.
No new RV64/RTL build, clean Docker build, debug-symbol or IDE/GDB verification was
performed. Existing Gate0 task states are unchanged. No latency, power, physical
hardware or Groq advantage is established; T-0229 signed semantics are excluded.

## T-0229 resumed: signed source ordering, October 11

Explicit owner approval permits the local signed32 max/ReLU continuation. The
current host candidate combines T-0233 fixes with Proposed ADR-0130 and reuses the
same T-0223 kernel/runtime and immutable Docker image recorded above. No new RV64
or RTL build, debug/GDB or hardware acquisition was performed.

Nine new parents execute14 coupled sessions/17 jobs. Sixteen jobs are accepted;
one deliberate wrong-word response in the post job is rejected and suppresses the
parent output. Eight complete parents publish240 expected words. Both partition
choices, signed boundaries, repeated comparisons at the map-node limit, wrapped
reduction, small GEMM+bias+ReLU and full-range wrapped GEMM+bias+ReLU pass. All saved
parents revalidate without execution. These are functional emulation/RTL simulation
results and do not establish latency, power, silicon performance or Groq advantage.
Exact commands and hashes: October11 T-0229 resumed log and its evidence manifest.

## T-0229 generated signed interaction evidence (2026-10-11)

The generated-coordinate harness now accepts `--numeric signed32`, using the
existing v4 source contract. With seed 229, 1,000 generated sources exercise
zero/clamp/wrap, unsigned sum/max folds, optional post maps and one/two inputs.
989 sources have an admitted tested partition; 11 have none. All
2729 admitted partitions match 51,094 independently computed words.
Rejected partitions remain explicit and are never counted as successful execution.

Actual QEMU/RTL verification passes 24 representative parents, 24 distinct
sessions and 36 approved jobs, producing 850 correct words. Each selected
case differs from a signed-to-unsigned counterfactual, samples outside input bounds,
and changes when any declared input is zeroed. The counterfactual changes
541 final cells across the suite. Kernel signed max, kernel ReLU and
post ReLU each have observable cases across the suite; not every placement is
observable in every category. Outside sampling does not prove changing boundary
mode changes the output. All actual parents revalidate without execution.

24 selected host tests pass, including six new harness tests; together with the
previous 203 distinct tests, the retained successful inventory contains 209 unique
test IDs. This continuation does not rerun all 209. The original unsigned fixture
bytes are unchanged. Production compiler/runtime/RTL and numeric limits are unchanged.
Local functional validation continues under ADR-0107 and Proposed ADR-0130;
public adoption and physical/performance conclusions remain separate.
Latest packet: `artifacts/research/T-0229/generated-01/`.


## T-0234 prepared acceptance, not executed (2026-10-11)

The proposed v5 signed-transform sharing has host checks and retained old-version
proof revalidation. A new coupled acceptance command binds the existing T-0223
kernel/runtime, but automatic approval review rejected launch pending explicit
owner scope approval. At that initial closeout there was no new QEMU/RTL result for T-0234. Gate0 and previous
functional results are unchanged. See STATUS/ADR-0131 and the dated log.

## T-0234 resumed functional evidence (2026-10-11)

The owner replied “続けて” directly to the concrete T-0234/V5 local implementation
and QEMU/RTL validation question. The resumed candidate reproduces all157 prior
file hashes; source/test code is unchanged. The earlier local execution hold is
resolved. Public/canonical adoption remains separate and ADR-0131 stays Proposed.

Fresh functional execution passes eight parents through12 coupled sessions and14
processed jobs (13 accepted and one injected post rejection). Seven complete
parents publish267 correct final words; the failed parent publishes no output.
Coverage includes the17-to14-node signed chain, the meaningful16-to15-node modular
branch, post-map sharing after wrapped reduction, linked GEMM composition and
partition equivalence. An additional new v4/v5 pair produces49 identical words
per version while reducing15 to13 map nodes. These are static source counts and
functional QEMU/RTL results, not measured speed, energy or physical performance.

All new parents revalidate with process creation prohibited; nested DAG receipts
independently establish counts without duplicate sessions. A copied actual v4
parent is changed to v5 with source/lowering/plan/inventory/hash coherently updated.
Its unchanged child is rejected specifically for captured-batch/source mismatch,
even though mathematical output is identical. Original parent record bytes remain
unchanged and both original versions revalidate; no whole-tree identity is claimed.

The previous46 host tests, 1,000-source/2,729-partition/51,094-word comparison and33
retained-parent checks remain valid for the unchanged candidate; they are retained
evidence, not rerun here. Ordinary15-node/8-register admission and old-version
lowering remain unchanged. Local implementation and runtime validation are complete.
Latest packet: `artifacts/research/T-0234/resumed-01/`.
