# Native CLI workspace guide

This guide covers the T-0099 application-level workspace containment on macOS
and GNU/Linux. It is a host-correctness development interface, not an OS
security boundary.

## Update an existing clone

Fetch the approved branch or release, then switch to the exact reviewed commit.
Do not discard local changes; inspect `git status` before switching.

## Create and open a workspace

From the repository root:

```sh
mkdir -p /tmp/raveil-demo
python3 -m raveil shell --workspace /tmp/raveil-demo
```

The host directory `/tmp/raveil-demo` appears inside the CLI as `/`. For
example, virtual `/output/result.json` maps to host
`/tmp/raveil-demo/output/result.json`. Virtual `/etc` means the workspace's
`etc` directory; it never means host `/etc`.

## Graph and file walkthrough

```text
raveil> pwd
/
raveil> mkdir output
directory created: /output
raveil> graph create gemm --m 8 --n 8 --k 8
raveil> graph show
raveil> variants
raveil> propose
raveil> execute
raveil> result /output/result.json
saved /output/result.json
raveil> ls /output
result.json
raveil> stat /output/result.json
raveil> cat /output/result.json
raveil> exit
bye
```

This uses the existing GraphCompiler, analytical adviser, Miroirs/Pavane
validation, GraphExecutor, and NativeCBackend. The trusted baseline still runs
first, advice may abstain, and the executor explicitly commits or rolls back.

## Limits and exits

- Paths are limited to 4,096 UTF-8 bytes.
- `cat` and `write` are limited to 64 KiB.
- `ls` rejects directories containing more than 256 entries.
- `write` and `result PATH` never overwrite an existing path.
- Symlinks, broken symlinks, parent traversal, and special files are rejected.
- Press `Ctrl+C`, send EOF (`Ctrl+D` in a normal terminal), or enter `exit` to
  leave the CLI.

The CLI provides no external command execution, pipes, redirection, globbing,
network access, deletion, or package manager. Its checks constrain cooperative
CLI operations, but they do not isolate hostile native code or eliminate all
path races. T-0100 retains descriptor-relative resolution and platform-enforced
worker isolation as follow-up work.
