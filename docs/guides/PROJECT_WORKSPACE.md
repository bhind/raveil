# Raveil project workspace

Status: T-0149 development guide

This is the shell-first path for editing a small workload, seeing its Graph,
running it more than once and comparing retained results. Use your normal
bash/zsh, editor, Git and file tools around the `raveil project` commands.

## Create and inspect

From the repository root:

```sh
export PATH="$PWD/scripts:$PATH"
raveil project init /tmp/my-raveil-project
cd /tmp/my-raveil-project
raveil project show logs
raveil project show files
raveil project show gemm
```

The generated `recipes/` and `inputs/` files are ordinary JSON and text. The
Command recipes use only the bounded allowlisted syntax documented in
`NATIVE_COMMAND_GRAPH.md`; they do not accept arbitrary shell commands.

## Edit, run and compare

```sh
raveil project run logs
printf 'ERROR changed\n' >> inputs/events.txt
raveil project run logs
raveil project runs
raveil project diff RUN_A RUN_B
```

Replace `RUN_A` and `RUN_B` with the two IDs printed by `run` or `runs`. Each
run keeps its exact recipe and input copy, compiled Graph, output workspace and
result record under `runs/RUN_ID/`. You can inspect those files with your usual
editor or command-line tools.

Run history is cooperative local development evidence. The reader detects
later artifact mutation, but this is not a signed audit log, production cache
or hostile-code sandbox.

## Native and Sonatine GEMM

```sh
raveil project run gemm --backend native

make -C /path/to/raveil/sonatine
raveil project run gemm --backend sonatine-qemu \
  --sonatine-kernel /path/to/raveil/sonatine/build/sonatine.elf
```

The Sonatine backend accepts only the generated GEMM family with dimensions
from 1 through 8. Native results are Host Functional evidence; Sonatine/QEMU
results are QEMU Emulation Correctness evidence. Do not compare their timing.

## Enter the microkernel console

```sh
raveil project console sonatine \
  --sonatine-kernel /path/to/raveil/sonatine/build/sonatine.elf
```

At `raveil-u>` enter `help`. Enter `exit` to leave. The console is a direct way
to touch the current Sonatine seed; console text grants no execution approval
or evidence authority.

## Linux parity check

The commands use the same grammar on Python 3.11+ GNU/Linux. Tool identities
and therefore Command Graph IDs may differ from macOS because the resolved
allowlisted binaries differ. Semantic output, not a cross-host binary identity
or timing comparison, is the compatibility requirement.
