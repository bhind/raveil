# Raveil v0.0000000000001

> This heading names the latest immutable feature release. Current development
> is unreleased. The manufacturing line is active after the GNU/Linux graph MVP
> and failure-governance milestones. Current work preserves those artifacts
> while growing the Sonatine U-mode shell and backend integration. See
> `docs/STATUS.md` and `docs/ROADMAP.md` for current state.

This is the smallest executable Raveil seed with two connected bootstrap tracks:

1. a bootable Sonatine Microkernel (Sonatine) authority on QEMU/RISC-V `virt`;
2. a host-side bounded Experience experiment.

It deliberately contains no production LLM, neural network, RTL, or real
accelerator backend. A pinned TVM MetaSchedule adapter and completed negative
Gate 1 evidence now exist; no latency or energy improvement is claimed.

## Sonatine Microkernel boot target

```text
QEMU / RISC-V virt
        ↓
Raveil boot
        ↓
Sonatine Microkernel
        ├─ physical memory
        ├─ capability
        ├─ task
        ├─ IPC
        ├─ timer
        └─ console
        ↓
init task
        ↓
U-mode command shell
        ↓
raveil-u>
```

The subsystems are small but executable: the shell can inspect tasks and
capabilities, allocate/release a physical page, read timer ticks, and exercise
a capability-checked IPC loopback.

### Build and run the RV64 kernel

Prerequisites: `riscv64-unknown-elf-gcc`, GNU Make, and
`qemu-system-riscv64`.

```bash
cd sonatine
make
make run
```

The normal boot path now enters the persistent U-mode command shell:

```text
raveil-u> help
help info ticks ipc fs ls cat echo write stat jobs run cancel result exit
raveil-u> info
u-cmd info=ok
```

Input is line-oriented. CR, LF, and CRLF are accepted; backspace and delete
erase one character. Commands are bounded to eight ASCII bytes. An overlong or
unknown command reports an error and returns to the prompt without stopping the
kernel. `help`, `info`, `ticks`, `ipc`, `fs`, `ls`, `cat`, `echo`, `write`,
`stat`, `jobs`, `run`, `cancel`, `result`, and `exit` are available. `cat`,
`echo`, and `write` deliberately use fixed documented values rather than
general paths or arguments. Their
kernel operations derive caller identity from the current U-mode task and
resolve the corresponding capabilities; the line buffer never crosses as a
user pointer.

Or run it without installing the cross-toolchain on the host:

```bash
cd sonatine
docker build -t raveil-sonatine .
docker run --rm -it raveil-sonatine
```

`make smoke` boots QEMU non-interactively, exercises CR/LF handling, editing,
overflow recovery, all public U-mode commands, timer preemption, capability
denials and IPC, and exits through the QEMU test finisher.

Expected interactive prompt:

```text
raveil-u> help
help info ticks ipc fs ls cat echo write stat jobs run cancel result exit
```

The retained M-mode diagnostic shell separately provides `help`, `info`,
`mem`, `ps`, `caps`, `ticks`, `ipc`, `alloc`, and `reboot`, but it is not the
normal boot path.

The published tag began as a one-hart machine-mode seed. Current unreleased
development adds Sv39 construction, a persistent U-mode task, timer-driven
preemption, capability IPC, a bounded VFS/RamFS, job authority, telemetry, and
metadata-shadow finalization. These are QEMU correctness results, not physical
hardware or production-isolation claims.

## Experience experiment

```text
Context
  -> retrieve bounded nearby Experience
  -> rank typed candidates
  -> measure with ToyDaphnis
  -> append immutable JSONL evidence
  -> consolidate active memory to a fixed limit
```

All cold evidence remains in the JSONL log. Only a fixed number of consolidated records participate in online retrieval. Invalid variants and performance-tail records receive higher retention priority.

## Quick start

Requires Python 3.11 or newer. There are no third-party runtime dependencies.

```bash
python -m raveil demo --reset
python -m raveil bench
python -m unittest discover -s tests -v
```

The demo trains on four shapes, then tunes a held-out shape with a two-measurement budget. It prints cold-start and warm-transfer Headroom Capture Rate (HCR).

The owned graph MVP selects its backend explicitly. Native POSIX C remains the
default; the bounded Sonatine/QEMU correctness path currently accepts only the
8-or-smaller GEMM seed:

```bash
python3 -m raveil graph-mvp --backend native \
  --family gemm --m 8 --n 8 --k 8 --output /tmp/raveil-native.json
python3 -m raveil graph-mvp --backend sonatine-qemu \
  --family gemm --m 8 --n 8 --k 8 \
  --sonatine-kernel sonatine/build/sonatine.elf \
  --output /tmp/raveil-sonatine-result.json
```

The latter is QEMU emulation correctness only. It deliberately reports no
latency or energy and cannot establish a hardware-performance result.

The bounded interactive operator demo can also be captured as one strict,
exclusive evidence record after building Sonatine:

```bash
make -C sonatine
python3 -m raveil sonatine-demo \
  --sonatine-kernel sonatine/build/sonatine.elf \
  --output sonatine/build/raveil-sonatine-demo.json
```

The command drives the fixed VFS and completed/cancelled job transcript. Its
result is `qemu-emulation-correctness`, not Experience, measurement, latency,
energy, or hardware-performance evidence.

The optional pinned IREE adapter validates one repository-owned MLIR fixture
before running the same native guarded loop. Install the compiler in an
isolated environment using `tools/iree/requirements.lock`, then run:

```bash
python3 -m raveil graph-mvp --backend native \
  --import-manifest benchmarks/iree/gemm-8x8x8-i32-i64.import.json \
  --iree-compile /path/to/iree-compile \
  --output /tmp/raveil-iree-import.json
```

The graph result keeps the exact `raveil.graph-mvp-result/v1` schema; import
provenance is written separately as `<output>.import.json`. This is import/host
correctness, not IREE runtime or performance evidence.

The persistent log defaults to `experience/local.jsonl`.

## Commands

```bash
python -m raveil --version
python -m raveil demo --reset --budget 2 --active-limit 64
python -m raveil bench --budget 2 --active-limit 64
python -m raveil inspect --experience experience/local.jsonl
python -m raveil experiment preflight --manifest benchmarks/manifests/gate1-powermetrics-pilot-v1.json
```

Gate 1 research runs use a committed manifest and an immutable lifecycle:

```bash
python -m raveil experiment run --manifest benchmarks/manifests/gate1-powermetrics-pilot-v1.json
python -m raveil experiment analyze --run RUN_ID
python -m raveil experiment seal --run RUN_ID
python -m raveil experiment sync --run RUN_ID
```

First collect, analyze, and seal the registered disjoint-workload history run.
It is source evidence and cannot produce a Gate conclusion by itself:

```bash
python -m raveil experiment run \
  --manifest benchmarks/manifests/gate1-fixed-c-history-v1.json
python -m raveil experiment analyze --run SOURCE_RUN_ID
python -m raveil experiment seal --run SOURCE_RUN_ID
```

Then pre-register the six equal-budget policy slates before starting the target
run:

```bash
python -m raveil experiment plan \
  --manifest benchmarks/manifests/gate1-fixed-c-v1.json \
  --source-run SOURCE_RUN_ID \
  --output /tmp/gate1-policy-selections.jsonl

python -m raveil experiment run \
  --manifest benchmarks/manifests/gate1-fixed-c-v1.json \
  --policy-selections /tmp/gate1-policy-selections.jsonl
```

`experiment analyze` derives outcomes only from each pre-registered candidate
slate and keeps the exhaustive target matrix as offline oracle evidence.

The pilot validates power-sampling and thermal stability but cannot produce a
Gate conclusion. Use `gate1-fixed-c-v1.json` only after the pilot is remotely
verified. Run requires a clean Git worktree. After the one-time
[least-privilege helper setup](docs/guides/POWERMETRICS_HELPER.md), the runner
uses passwordless `sudo -n` only for the fixed root-owned powermetrics helper.
Missing helper authority, insufficient power samples, or
unstable thermal state fail closed. Raw bundles remain ignored under
`artifacts/research/`; rclone configuration and Google credentials stay outside
the repository. A run is incomplete until remote content verification passes
and the completion marker is copied last. Seal immediately, but sync successful
stage milestones and selected unique failures rather than every redundant
retry; queued local bundles remain incomplete until later batch verification.

## Repository map

```text
raveil/model.py       Context, hardware, candidate and metric contracts
raveil/backend.py     deterministic ToyDaphnis measurement model
raveil/experience.py  append-only evidence and bounded consolidation
raveil/policy.py      nearest-Experience ranking and tuning loop
raveil/cli.py         demo, benchmark and inspection commands
benchmarks/            Gate 1 native C source and committed manifests
sonatine/             freestanding RV64 Sonatine Microkernel and shell
tests/                executable acceptance tests
docs/SCOPE.md         explicit boundary and next experiment
```

## Project knowledge base

Raveil is treated as a research program, not only as a source tree. The
repository records the concept, current implementation, open work, experiments,
and architectural decisions in Markdown.

- [`docs/README.md`](docs/README.md) — documentation index and recording rules
- [`docs/VISION.md`](docs/VISION.md) — research thesis and intended end state
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Four-plane architecture and component boundaries
- [`docs/EXPERIENCE.md`](docs/EXPERIENCE.md) — persistent Experience model and evaluation metrics
- [`docs/STATUS.md`](docs/STATUS.md) — what is actually implemented now
- [`TODO.md`](TODO.md) — actionable work queue
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — gated long-term roadmap
- [`docs/decisions/`](docs/decisions/README.md) — Architecture Decision Records
- [`docs/experiments/`](docs/experiments/README.md) — experiment plans and results

The repository rule is simple: architectural changes require a decision record;
performance claims require an experiment record; implementation changes update
the status and TODO documents in the same commit.

## Important limitation

ToyDaphnis is deterministic analytical scaffolding. Its results prove the
software loop and metrics, not an architecture speedup. Native C checksum and
unit-test results prove harness behavior, not a Gate 1 latency/energy outcome.
The Sonatine Microkernel proves the boot/control skeleton, not isolation or
scheduling completeness.

## Versioning

The runtime and Experience schema use the exact version requested: `0.0000000000001` (`10^-13`). This intentionally predates semantic release numbering.

## License

Apache-2.0. See `LICENSE`.
