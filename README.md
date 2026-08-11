# Raveil v0.0000000000002

This feature release is a source demo of the owned graph control loop on native
POSIX C and Sonatine/QEMU. It is intended for hands-on correctness evaluation,
not as a latency, energy, FPGA, ASIC, or silicon-performance release.

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
help info ticks ipc fs exit
raveil-u> info
u-cmd info=ok
```

Input is line-oriented. CR, LF, and CRLF are accepted; backspace and delete
erase one character. Commands are bounded to eight ASCII bytes. An overlong or
unknown command reports an error and returns to the prompt without stopping the
kernel. `help`, `info`, `ticks`, `ipc`, `fs`, and `exit` are available. Their
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
help info ticks ipc fs exit
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

### Hands-on graph demo

Clone the release and run the native path first:

```bash
git clone https://github.com/bhind/raveil.git
cd raveil
git checkout v0.0000000000002
python3 -m raveil graph-mvp --backend native \
  --family gemm_bias_relu --m 128 --n 128 --k 128 \
  --inner-iterations 20 --warmups 3 \
  --output /tmp/raveil-native-demo.json
python3 -m json.tool /tmp/raveil-native-demo.json
```

The JSON shows the canonical variants, advisory proposal or abstention,
baseline-first observations, semantic checks, selected variant, and explicit
commit or rollback. Timing fields are local development observations only.

For the Sonatine/QEMU correctness path, install a freestanding RISC-V compiler,
GNU Make, and `qemu-system-riscv64`, then run:

```bash
make -C sonatine CROSS_COMPILE=riscv64-elf-
python3 -m raveil graph-mvp --backend sonatine-qemu \
  --family gemm --m 8 --n 8 --k 8 \
  --sonatine-kernel sonatine/build/sonatine.elf \
  --output /tmp/raveil-sonatine-demo.json
python3 -m json.tool /tmp/raveil-sonatine-demo.json
```

If the installed toolchain prefix is `riscv64-unknown-elf-`, substitute that
value for `CROSS_COMPILE`. The QEMU result deliberately contains no execution
latency and is classified as emulation correctness evidence.

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

The runtime release is `0.0000000000002`. The append-only Experience schema
retains its original `raveil.experience/v0.0000000000001` identifier for
backward compatibility; a feature release does not silently rewrite persisted
evidence.

## License

Apache-2.0. See `LICENSE`.
