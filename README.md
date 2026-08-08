# Raveil v0.0000000000001

This is the smallest executable Raveil seed with two connected bootstrap tracks:

1. a bootable Sonatine Microkernel (Sonatine) authority on QEMU/RISC-V `virt`;
2. a host-side bounded Experience experiment.

It deliberately contains no LLM, neural network, RTL, completed TVM
MetaSchedule implementation, or real accelerator backend. Gate 1 now includes a
fixed native C measurement harness, but no performance result is claimed.

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
Raveil shell
        ↓
raveil>
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

Or run it without installing the cross-toolchain on the host:

```bash
cd sonatine
docker build -t raveil-sonatine .
docker run --rm -it raveil-sonatine
```

`make smoke` boots QEMU non-interactively, exercises the inspection commands,
checks capability-protected IPC, and exits through the QEMU test finisher.

Expected final boot lines:

```text
starting init task id=1

Raveil shell v0.0000000000001
type 'help' for commands

raveil>
```

Available commands are `help`, `info`, `mem`, `ps`, `caps`, `ticks`, `ipc`,
`alloc`, and `reboot`.

This version runs directly in machine mode with one hart and no paging. Tasks
are fixed kernel task records; there is not yet a preemptive context switch or
U-mode address-space isolation. That distinction is intentional and visible in
the `info` command.

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

The persistent log defaults to `experience/local.jsonl`.

## Commands

```bash
python -m raveil --version
python -m raveil demo --reset --budget 2 --active-limit 64
python -m raveil bench --budget 2 --active-limit 64
python -m raveil inspect --experience experience/local.jsonl
```

Gate 1 research runs use a committed manifest and an immutable lifecycle:

```bash
python -m raveil experiment run --manifest benchmarks/manifests/gate1-powermetrics-pilot-v1.json
python -m raveil experiment analyze --run RUN_ID
python -m raveil experiment seal --run RUN_ID
python -m raveil experiment sync --run RUN_ID
```

The pilot validates power-sampling and thermal stability but cannot produce a
Gate conclusion. Use `gate1-fixed-c-v1.json` only after the pilot is remotely
verified. Run requires a clean Git worktree. Authenticate in the same terminal
with `sudo -v` first; the runner invokes only `/usr/bin/powermetrics` through
non-interactive `sudo -n`. Missing privilege, insufficient power samples, or
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
