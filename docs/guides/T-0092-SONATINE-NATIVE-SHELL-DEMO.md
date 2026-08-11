# T-0092 Sonatine native operator-shell demo packet

Status: planned owner packet
Priority: next demo P0 after already in-flight work reaches a clean milestone
Evidence boundary: host correctness and QEMU emulation correctness only

## Objective

Make the existing `raveil-u>` shell visibly operate Raveil-owned filesystem and
graph state without building Unix compatibility. The fixed demo command set is:

| Command | Minimum honest behavior |
|---|---|
| `ls` | enumerate the current bounded VFS nodes and print `/hello` and `/scratch` from VFS metadata |
| `cat` | read and print the documented default `/hello` through the read capability |
| `echo` | print a documented fixed U-mode demo string through the console capability |
| `write` | append or replace one documented fixed value in `/scratch` through the write capability |
| `stat` | print size and writable state for both current VFS nodes |
| `jobs` | report the real state and ID of the single bounded demo-job slot, or `EMPTY` |
| `run` | submit the fixed built-in bounded GEMM demo through existing validation and authority seams |
| `cancel` | perform a real allowed cancellation transition or report `EMPTY`/`TOO_LATE`; never fake success |
| `result` | report the last real completion/cancellation state and checksum/semantic status when present |

Argument-free `cat`, `echo`, and `write` are deliberate MVP semantics and must
be stated in `help`; they are not claims of coreutils compatibility. User-mode
requests remain scalar or fixed-width. Kernel pointers, arbitrary user
pointers, paths, file descriptors, and raw graph bytes do not cross the syscall
boundary.

## Delivery order and ownership

1. Ciste owns the Sonatine/RV64/VFS/job-state implementation, QEMU smoke, and
   machine-readable serial frames. Ciste does not edit canonical records.
2. The PM reviews and freezes the serial frame and command semantics.
3. Lifri owns the Python host runner, strict result schema, CLI wiring, and
   focused Python tests. Lifri does not edit Sonatine or canonical records.
4. The PM integrates both slices, updates STATUS/TODO/ROADMAP/log and any ADR
   only if an invariant actually changes, then runs full local CI.

Do not run Ciste and Lifri concurrently on this coherent change. Lifri starts
only from Ciste's reviewed commit or immutable patch hash.

## Acceptance

- Existing `help`, `info`, `ticks`, `ipc`, `fs`, `selftest`, editing,
  overflow, preemption, capability-denial, and `exit` regressions still pass.
- `ls`, `cat`, `echo`, `write`, and `stat` are derived from real capability/VFS
  operations; shell code does not merely print success literals.
- `run`, `jobs`, `cancel`, and `result` expose one bounded real state machine
  and reuse validation, job/completion binding, commit/rollback, and
  cancellation seams already present in the tree.
- Invalid command order, missing result, second inflight run, denied
  capability, stale completion, and cancel-after-complete fail closed with
  deterministic results.
- QEMU smoke drives both a completed run and a genuinely cancelled or
  explicitly non-cancellable terminal case without timing races.
- Machine-readable serial output is versioned and bounded; host parsing never
  treats arbitrary console prose as authority.
- The host runner exclusively creates one JSON result with input/kernel hashes,
  command transcript, per-command status, final job state, semantic status,
  evidence class, QEMU/tool versions, and exit status. It records no performance
  metric.
- `scripts/ci-local.sh` and the record checker pass before PM closeout.

## Explicit non-goals

No BusyBox source, ELF loader, libc port, `fork`, `exec`, pipe, signal, tty job
control, general path parser, arbitrary argv/environment, persistent disk,
network command, multi-user shell, DMA/MMIO driver, latency/energy claim, or
POSIX/Linux compatibility statement. BusyBox is GPLv2; any later source reuse
requires a separately pinned source/license/provenance review.

## Prompt for Ciste

```text
You are Ciste, the Raveil Systems Implementer. Implement the Sonatine-owned
first slice of T-0092 on a dedicated feat/t-0092-sonatine-shell-demo branch.
You are not alone in the repository: preserve all existing work and do not
revert or rewrite unrelated changes.

Read AGENTS.md, docs/README.md, TODO T-0092, this guide, executable Sonatine
shell/VFS/job code, focused tests, STATUS's Sonatine section, and accepted ADRs
that own U-mode capability, job/completion, Four-plane, and byte-shadow
boundaries. Return a short must-read packet before editing.

Ownership: edit only explicitly necessary Sonatine/RV64/native-C/QEMU-smoke
files. Do not edit STATUS, TODO, ROADMAP, OPEN_QUESTIONS, ADR, RFC, EXP, dated
logs, Python Experience code, or Lifri's future host runner.

Implement ls, cat, echo, write, stat, jobs, run, cancel, and result with the
exact minimum semantics and non-goals in this guide. Reuse real VFS metadata and
the existing bounded graph job/completion/finalization/cancellation seams.
Never implement a command by printing success without the underlying state
transition. Keep the U-mode boundary scalar or fixed-width and pointer-free.
Freeze a bounded versioned machine-readable serial frame for Lifri; ordinary
human-readable console prose is not authority.

Preserve every existing shell, preemption, fault, capability-denial, graph,
telemetry, and rollback regression. Add deterministic native-C/QEMU coverage
for completed, cancelled/too-late, empty, busy, stale, denied, and invalid-order
paths. Do not add BusyBox, ELF/POSIX process support, general paths, or timing.

Run focused host tests, release/debug Sonatine builds, make -C sonatine smoke,
the graph smoke/differential, and any proportionate local CI available. Label
all QEMU output emulation correctness. Return changed paths, exact commands and
exit codes, tool versions, evidence class, machine-readable frame contract,
findings, and unresolved risks. Do not mark T-0092 complete.
```

## Prompt for Lifri

```text
You are Lifri, the Raveil Experience Implementer. Start only after the PM gives
you Ciste's reviewed T-0092 commit or immutable patch hash and freezes the
machine-readable serial frame. Work on a dedicated non-overlapping branch. You
are not alone in the repository: preserve all existing work and do not revert
unrelated changes.

Read AGENTS.md, docs/README.md, TODO T-0092, this guide, Ciste's frozen frame,
the existing graph/sonatine backend adapters, CLI conventions, and focused
Python tests. Do not infer facts from chat; verify the supplied commit.

Ownership: edit only the assigned Python host-runner/schema/CLI/test files. Do
not edit Sonatine, native C, STATUS, TODO, ROADMAP, OPEN_QUESTIONS, ADR, RFC,
EXP, or dated logs.

Add a bounded host demo command that launches the pinned Sonatine QEMU kernel,
feeds the fixed T-0092 transcript, accepts only Ciste's exact versioned frames,
and exclusively creates one strict JSON result. Bind the record to repository
revision, kernel hash, command transcript, frame version, QEMU/tool versions,
per-command status, final job state, semantic/checksum result, exit status, and
evidence_class=qemu-emulation-correctness. Reject missing, duplicate, unknown,
late, oversized, stale, malformed, nonzero-exit, timeout, and prose-only
results. Never record latency or promote the record into Experience.

Add focused unit tests with a fake subprocess plus one real-QEMU integration
entry that remains explicit and bounded. Preserve existing graph, evidence,
and CLI behavior. Do not add BusyBox, parse arbitrary shell text, or broaden
the product runtime to require an LLM.

Run focused Python tests and proportionate local regression. Return changed
paths, exact commands and exit codes, environment/tool versions, evidence
class, schema/frame assumptions, findings, and unresolved risks. Do not mark
T-0092 complete.
```
