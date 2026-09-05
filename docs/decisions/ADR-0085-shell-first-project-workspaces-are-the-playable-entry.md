# ADR-0085: Shell-first project workspaces are the playable Raveil entry

Status: Accepted
Date: 2026-09-05
Task: T-0149
Related: ADR-0025, ADR-0029, ADR-0034, ADR-0035, ADR-0036, ADR-0084

## Context

Raveil has a Native CLI, a bounded Command Graph, a small GEMM path into
Sonatine/QEMU, a microkernel console and a growing RTL simulation line. These
parts prove useful boundaries, but most operator demonstrations replay a fixed
fixture. They do not yet form a place where a person can edit their own input,
inspect its Graph, run it, keep the result, change it and immediately compare a
second attempt.

The next product question is therefore experiential before it is a performance
question: can Raveil feel like a small system that is worth opening and growing
from an ordinary work shell? This does not invalidate T-0042, EXP-0003 or the
simulation Graph line. It changes the primary development slice from another
isolated mechanism to a runnable composition of mechanisms already present.

## Decision

Add `raveil project` as the shell-first playable entry. A project is an
ordinary local directory containing:

- `project.json` with an exact versioned layout;
- editable `recipes/` and `inputs/` directories;
- append-by-new-ID `runs/` directories that copy the exact recipe and input
  snapshot, materialize outputs, and retain an integrity-checked run record.

The first command surface is `init`, `show`, `run`, `runs`, `diff` and
`console sonatine`. `show` exposes nodes, dependencies, declared inputs and
declared outputs before execution. `run` recompiles the recipe every time and
uses a fresh run directory. `diff` compares the saved recipe, backend,
evidence class, status, inputs and outputs; bounded UTF-8 inputs and outputs
also receive human-readable before/after previews. The generated examples cover log
aggregation, two independent file transforms and GEMM no larger than 8.

A repository-owned POSIX launcher in `scripts/raveil` makes the intended
`raveil` command usable from inside the project after one explicit PATH setup.
Project and run directories are created mode `0700`; run artifacts are mode
`0600`. Existing project roots are tightened only through an
`O_DIRECTORY|O_NOFOLLOW` descriptor and `fchmod`, never a path-following
`chmod`.

Command recipes keep ADR-0036's bounded syntax and allowlisted host tools.
Arbitrary commands, editing, Git and file inspection remain in the person's
normal bash or zsh. Native GEMM reuses the existing strict-C adapter.
`sonatine-qemu` accepts only the existing bounded GEMM envelope and keeps the
`qemu-emulation-correctness` evidence label. `console sonatine` is an explicit
terminal attachment to the existing QEMU microkernel and grants no Graph,
Program, Data, Experience, approval or publication authority.

The first acceptance loop must run on the current macOS host and in a Linux
environment with the same CLI grammar. It must include an actual input edit,
two retained runs, an observable diff, Native GEMM, Sonatine/QEMU GEMM, and a
real Sonatine console session. The two host environments need semantic
agreement, not identical executable or Graph identities.

## Consequences

- Raveil gains one reusable edit-run-observe-change-rerun loop instead of a
  fixed presentation-only demo.
- Run history is cooperative local development evidence. Its checks detect
  later mutation but are not a signed audit log, hostile-code sandbox,
  production cache or isolation boundary.
- macOS and Linux host identities may differ because their allowlisted tool
  binaries differ; no cross-host performance or identity equivalence follows.
- T-0148's relative-load simulation result and the blocked physical research
  inputs remain preserved. They are not deleted or promoted by this product
  entry.
- This task makes no Native-versus-QEMU speed comparison and adds no CPU,
  FPGA, ASIC, silicon, area, timing, energy, novelty or commercial-readiness
  claim.

## Supersession

This ADR composes the accepted Native workspace, Command Graph, GEMM and
Sonatine/QEMU boundaries. It supersedes no evidence or authority rule. It
changes only the immediate product-development entry and roadmap emphasis.
