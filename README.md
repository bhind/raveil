# Raveil v0.0000000000001

This is the smallest executable Raveil seed with two connected bootstrap tracks:

1. a bootable Sonatine authority on QEMU/RISC-V `virt`;
2. a host-side bounded Experience experiment.

It deliberately contains no LLM, neural network, RTL, TVM adapter, or real accelerator backend.

## Sonatine boot target

```text
QEMU / RISC-V virt
        ↓
Raveil boot
        ↓
Sonatine kernel
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

## Repository map

```text
raveil/model.py       Context, hardware, candidate and metric contracts
raveil/backend.py     deterministic ToyDaphnis measurement model
raveil/experience.py  append-only evidence and bounded consolidation
raveil/policy.py      nearest-Experience ranking and tuning loop
raveil/cli.py         demo, benchmark and inspection commands
sonatine/             freestanding RV64 Sonatine kernel and shell
tests/                executable acceptance tests
docs/SCOPE.md         explicit boundary and next experiment
```

## Important limitation

ToyDaphnis is deterministic analytical scaffolding. Its results prove the software loop and metrics, not an architecture speedup. The Sonatine kernel proves the boot/control skeleton, not isolation or scheduling completeness.

## Versioning

The runtime and Experience schema use the exact version requested: `0.0000000000001` (`10^-13`). This intentionally predates semantic release numbering.

## License

Apache-2.0. See `LICENSE`.
