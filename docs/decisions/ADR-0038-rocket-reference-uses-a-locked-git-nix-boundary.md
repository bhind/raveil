# ADR-0038: Rocket reference uses a locked Git/Nix boundary

Status: Accepted
Date: 2026-08-12

## Context

T-0105 needs an unmodified RISC-V reference core to prove that the RTL research
substrate works before any owned Graph mechanism is designed. Rocket's upstream
Nix development shell resolves a fixed flake, but its shell hook also installs
current Python packages into an untracked `venv/`. The complete shell builds
tools not needed by this smoke. A path-based flake input can also scan ignored
Mill output, including a live Unix socket, and fail before evaluation. Under
Apple Silicon amd64 emulation, Nix's nested builder seccomp BPF load fails even
though Docker's container seccomp remains available.

## Decision

Keep Rocket and its fixed CDE, Chisel, and HardFloat submodules in the ignored
external-source checkout selected by `rocket-pin.env`. Run it in the
`linux/amd64` variant of `nixos/nix:2.13.3` fixed by manifest-list digest
`sha256:1f8fa57de6f2f9ea5ea8d115b339fa68d2f98f20b59438bdb9d3a082ad64d4bf`.

Resolve only the named Mill, CIRCT, DTC, Verilator, CMake, Ninja, clang, Spike,
RISC-V tests, coreutils, and findutils attributes through a
`git+file` flake input bound to Rocket commit
`749a3eae9678bc70b029c5b9091fae33fad539c4`. The committed `flake.lock` remains
package authority. Do not enter the upstream development shell, run its Python
hook, or include ignored/untracked output in flake identity.

Disable only Nix's nested builder syscall filter for this emulated environment.
Retain Docker's default seccomp boundary and add `no-new-privileges`. Pair the
named Nix-store volume with version-matched Mill-output and Mill/Coursier
user-cache volumes; never reuse the host checkout's `out/`, discard a worker
cache while retaining its Mill output, or combine state created against another
Nix store. Treat all three volumes as disposable caches, never source, evidence
authority, or performance state. Verify exact source and submodule
revisions before each run, require 16 `rv64mi-p` passed logs and no failed log,
and emit an explicit functional-only, Graph-not-implemented,
performance-not-measured marker.

Retain upstream license files in the external checkout and do not copy upstream
implementation into Raveil-owned contracts. License availability does not
decide patent scope, infringement, legal clearance, or freedom to operate.

## Consequences

The reference smoke avoids mutable Python resolution, unnecessary upstream
development packages, and generated-file contamination while remaining based
on the upstream locked package graph. A cold run still requires network access
and a substantial download; the cache only reduces repeated setup cost.

The resulting elaboration and ISA tests are RTL functional simulation evidence.
They authorize neither an owned Graph mechanism nor latency, energy, area,
timing, OoO-removal, FPGA, silicon, or CPU/ISA claims. T-0057B remains the
mechanism-contract gate before T-0042, and T-0044 must define a fresh matched
measurement environment. Changing the source boundary, package authority,
container platform, or evidence class requires a later decision and new
verification.
