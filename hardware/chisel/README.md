# Chisel/RISC-V simulation substrate

Status: T-0105 functional substrate complete; T-0042 first bounded Graph RTL
slice functional; not a CPU performance experiment.

This directory proves three functional paths: a pinned
Chisel-to-SystemVerilog-to-Verilator path with a repository-owned four-bit
counter, and an unmodified pinned Rocket Chip reference elaboration plus ISA
test smoke, plus the ADR-0039 simulation-only bounded static stencil region.
Only the third path implements owned operation-level Graph RTL. None provides
comparative latency, energy, area, OoO-removal, ISA-advantage, FPGA, or silicon
evidence.

Run from the repository root:

```sh
docker build --platform linux/amd64 -f hardware/chisel/Dockerfile \
  -t raveil-chisel-smoke .
docker run --rm --platform linux/amd64 raveil-chisel-smoke
```

Success ends with `CHISEL-SMOKE-V1 status=OK cycles=10 value=8` and prints the
tool versions. Generated RTL and Verilator build output stay inside the
ephemeral container.

The image is deliberately linux/amd64 even on Apple Silicon. Chisel 7.2.0
resolves firtool 1.133.0, whose Maven artifact is available for Linux x86-64
but not Linux aarch64. Docker therefore uses CPU emulation for this first
functional smoke. This is not a performance environment; an arm64-native
firtool build is a separate reproducibility/cost decision.

Pinned direct dependencies:

- Eclipse Temurin 17 container tag `eclipse-temurin:17-jdk-jammy`;
- Scala CLI 1.10.1 from its upstream GitHub release;
- Scala 2.13.17, matching the upstream Chisel 7.2.0 Scala CLI example;
- Chisel and Chisel compiler plugin 7.2.0;
- firtool 1.133.0 resolved by Chisel 7.2.0;
- Ubuntu Jammy's packaged Verilator (the exact resolved version is printed).

The owned-counter base image is not the Rocket reference environment. Its
base-image digest and apt-resolved package versions must still be captured if
that earlier smoke is promoted beyond local tooling evidence.

## Pinned Rocket Chip source

Fetch the external reference checkout from the repository root:

```sh
./hardware/chisel/fetch-rocket.sh
```

The script checks out Rocket Chip commit
`749a3eae9678bc70b029c5b9091fae33fad539c4`, the exact gitlink selected by
Chipyard 1.11.0 at commit
`ac58f38d77c99e9d1cafa64dfd6d4b00bdcd43e1`. It prints a
`ROCKET-CHECKOUT-V1` line after verifying the origin, revision, and clean
worktree. Its commit-pinned Chisel, CDE, and HardFloat submodules are initialized
recursively with shallow history. The source lives under ignored
`external/rocket-chip/`; it is not vendored, copied into Raveil contracts, or
silently updated.

## Rocket reference functional smoke

After fetching the source, run:

```sh
./hardware/chisel/run-rocket-reference.sh
```

The wrapper fixes all of these inputs:

- `nixos/nix:2.13.3` manifest-list digest
  `sha256:1f8fa57de6f2f9ea5ea8d115b339fa68d2f98f20b59438bdb9d3a082ad64d4bf`;
- Docker platform `linux/amd64`, including on Apple Silicon;
- Rocket revision `749a3eae9678bc70b029c5b9091fae33fad539c4` and its
  CDE, Chisel, and HardFloat submodule revisions;
- Rocket's committed `flake.lock`, including nixpkgs
  `f5892ddac112a1e9b3612c39af1b72987ee5783a`;
- one generation-matched set of named Nix-store, Mill-output, and Mill/Coursier
  user-cache volumes. They accelerate later runs and prevent host,
  foreign-store, or vanished-container state from entering the build, but are
  never evidence or package authority.

The first run needs network access and can download hundreds of megabytes (the
verified cold run resolved about 856 MiB compressed and 3.2 GiB unpacked). It
uses selected `nix shell` package attributes from the fixed Git revision. It
does not use the upstream `devShell` hook, install Python packages, or import
ignored/untracked build output into Nix evaluation. Under Docker's own seccomp
and `no-new-privileges` boundary, only Nix's nested builder syscall filter is
disabled because that BPF program fails under amd64 emulation on the current
Apple Silicon Docker host.

The dedicated Mill output and user-cache volumes are versioned from
`RAVEIL_ROCKET_NIX_VOLUME` and mounted over Mill 0.11.1's fixed `/rocket/out`
and `/root/.cache` locations, so its absolute Nix-store and downloaded worker
references cannot be silently paired with another store or an ephemeral
container. The smoke first elaborates unmodified
`DefaultSmallConfig`. It then builds the
unmodified `DefaultConfig` Verilator emulator and runs the official `rv64mi-p`
suite. Success requires exactly 16 `*.passed.log` files, no `*.failed.log`, and
ends with a line containing:

```text
ROCKET-REFERENCE-SMOKE-V1 status=OK ... suite=rv64mi-p passed=16 failed=0 evidence=rtl-simulation-functional graph_rtl=not-implemented performance=not-measured
```

The verified environment reported Nix 2.13.3, Mill 0.11.1 with OpenJDK 19.0.2,
Scala 2.13.12 and Chisel 5.1.0 from the Rocket build, CIRCT firtool 1.56.1,
Verilator 5.012, clang 11.1.0, CMake 3.26.4, Ninja 1.11.1, and DTC 1.7.0.
This Rocket coordinate is independent of the earlier owned-counter Chisel
7.2.0 coordinate.

## Bounded static stencil RTL

ADR-0039 permits only the RFC-0005 fixed-schedule research simulation. Run its
complete owned compiler/validator checks and RTL smoke from the repository
root:

```sh
python3 -m unittest tests.test_static_region -v
./hardware/chisel/run-static-stencil-rtl.sh
```

The deterministic Python compiler constructs a ten-operation graph—five
`LOAD_U32`, four `ADD_U32`, and one `STORE_U32`—and the independent validator
requires the disjoint input/private-output objects, fixed six-cycle schedule,
one read port, one adder, one write port, zero runtime-ready slots, RV64IM
fallback declaration, and ADR-0039 exclusions. Its canonical SHA-256 is
`d4bf9395a510385f42ba4a193ae2c747f308ad502a8fe807843ed19c2fa4d1e2`;
the RTL exposes the first 64 bits only as a binding tag.

The Chisel module applies that schedule to all 256 output points. The C++
testbench computes the uint32 stencil independently, checks all outputs and the
checksum for two different inputs, cancels a third invocation, requires the
private output to become invalid, and then restarts successfully. Success emits:

```text
STATIC-STENCIL-RTL-V1 status=OK runs=2 cancelled=1 outputs=512 cycles_per_run=1536 configuration_tag=d4bf9395a510385f evidence=rtl-simulation-functional performance=not-measured
```

The 1,536-cycle check proves only that the implemented six-phase functional
schedule terminates within `max_cycles`. It is not a Rocket/BOOM comparison or
a performance result. The Docker path reuses the existing owned-counter Chisel
7.2.0 tool coordinate and a disposable Scala/Coursier cache. T-0044 must define
a fresh matched and immutable environment before any comparison.

After a successful RTL run the host wrapper emits three strict
`raveil.simulation-adapter/v2` JSON records: completed, cancelled, then
completed after restart. The common adapter fixes semantic and useful-operation
counts and exposes separate installation, staging, execution, completion,
validation, and publication phases. The current records explicitly use
`accounting_complete=false` and `total_cycles=null` because four phases remain
unknown. ADR-0041 also requires actual memory model and resource-match state:
the current Graph records use owned private scratchpads but explicitly set
resource matching and matched-comparison readiness false. They are functional
evidence and cannot be consumed as a benchmark.

To inspect the same validated record without rebuilding RTL:

```sh
python3 -m raveil.simulation_adapter --invocation 1 --status completed
python3 -m raveil.simulation_adapter --invocation 2 --status cancelled
```

Rocket, BOOM, and its OoO-disabled diagnostic must eventually emit this owned
schema through wrappers; no upstream implementation type is part of the
contract. T-0042 does not close until those functional records exist.

## Pinned BOOM control source

ADR-0040 selects the BOOM control through Chipyard 1.11.0 rather than a moving
checkout or unrelated prebuilt container:

```sh
./hardware/chisel/fetch-boom-reference.sh
./hardware/chisel/verify-boom-reference.sh
./hardware/chisel/run-boom-project-compile.sh
./hardware/chisel/fetch-boom-elaboration-deps.sh
./hardware/chisel/run-boom-elaboration.sh
```

The scripts fix Chipyard `ac58f38...bd43e1`, its BOOM gitlink
`9459af0c...10847c`, `chipyard.SmallBoomConfig`, both upstream license hashes,
and the exact source path for chicken CSR `0x7c1` bit 3. A successful check
prints `BOOM-SOURCE-REFERENCE-V1` with `diagnostic=serialize-dispatch` and
`structures=retained`.

The elaboration wrapper copies the checked-in Chipyard boot images into an ephemeral
target directory, prints the device-tree compiler version, and requires
non-empty FIRRTL plus annotation output containing `BoomCore`. The observed
functional marker is `BOOM-ELABORATION-V1 status=OK ... execution=not-run
performance=not-measured`.

Fetch the additional explicit public simulator gitlinks and run the minimal
RISC-V functional smoke with:

```sh
./hardware/chisel/fetch-boom-simulator-deps.sh
./hardware/chisel/run-boom-functional-smoke.sh
```

The runner verifies the pinned source and Chipyard lean lockfile hash, builds a
linux/amd64 Docker tool host, retains the locked toolchain and generated
simulator in named Docker volumes, compiles the tracked assembly/linker script,
and runs it on `chipyard.SmallBoomConfig`. The program sums 1 through 16,
stores and reloads the value, checks 136, then writes success to `tohost`. A
successful run ends with:

```text
BOOM-FUNCTIONAL-SMOKE-V1 status=OK config=chipyard.SmallBoomConfig workload=sum-store-load-tohost evidence=rtl-simulation-functional adapter=not-emitted performance=not-measured
BOOM-SERIALIZE-DISPATCH-SMOKE-V1 status=OK config=chipyard.SmallBoomConfig csr=0x7c1 mask=0x8 diagnostic=serialize-dispatch structures=retained workload=sum-store-load-tohost evidence=rtl-simulation-functional adapter=not-emitted performance=not-measured
```

Both ELFs come from the same tracked assembly. The second is built with one
preprocessor flag: before the shared workload it sets CSR `0x7c1` bit 3 and
reads the bit back. A missing readback takes a failing `tohost` path. This
isolates the functional difference to the pinned BOOM diagnostic setting; it
does not establish a performance effect or remove OoO hardware.

The named volumes are build caches, not evidence authority. Source mounts are
read-only, and the wrapper revalidates the source revision, lockfile, tool
versions, and installed firtool hash. The `conda-lock` reader installed in the
Docker image is still an unlocked bootstrap solve, so this path is suitable for
functional reproduction only.

Run the exact RFC-0005 semantic fallback on both BOOM modes with:

```sh
./hardware/chisel/run-boom-stencil-functional.sh
```

This compiles one tracked RV64 C/assembly workload twice, extracts its private
256-word `begin_signature`/`end_signature` range through FESVR, and validates
every word with the independent Python oracle. It then emits adapter v2 records
for `boom-ooo` and `boom-ooo-disabled-diagnostic`. These executions use the
normal `SmallBoomConfig` cache-backed memory path, so the records deliberately
leave every lifecycle cycle unknown and set resource matching and comparison
readiness false.

Run the identical fallback on the pinned in-order Rocket control with:

```sh
./hardware/chisel/run-rocket-stencil-functional.sh
```

The first run builds `chipyard.RocketConfig` in its own Docker volume using the
same pinned Chipyard source and functional toolchain. It compiles the same
tracked C/assembly source, extracts the same 256-word signature, and validates
it through the same independent oracle before emitting a `rocket-in-order`
adapter v2 record. This normal Rocket configuration is also cache-backed and
unmatched; its functional success does not authorize a comparison.

Exercise the inherited subsystem TLRAM on all three CPU control identities:

```sh
./hardware/chisel/run-shared-scratchpad-stencil-functional.sh
```

The wrapper revalidates both pinned simulators, compiles the same source with a
dedicated linker, requires `input_words=0x08000000` and
`begin_signature=0x08000510`, and validates all three 256-word signatures. Code
and `tohost` stay in the normal `0x80000000` region. The inherited device is one
64 KiB Mbus TLRAM bank shared by both configurations. Its successful use is
reported as `shared-tilelink-banked-scratchpad-unverified-latency`; TileLink and
CPU request paths have not been proven constant-latency or equivalent to the
Graph RTL, so resource matching remains false.

The diagnostic waits for an empty ROB/LSU but retains the OoO hardware, so it
is not an in-order core or an area/energy ablation. Elaboration is not program
execution; the separate smoke above is program execution but not a Graph or
comparison workload. Neither functional container can support measurement
claims, and an unofficial prebuilt image is not evidence authority.

The external checkout retains `LICENSE.Berkeley` (BSD-3-Clause-style),
`LICENSE.SiFive` (Apache-2.0), `LICENSE.jtag` (BSD-3-Clause-style), and the
submodule license files for Chisel/CDE (Apache-2.0) and HardFloat
(BSD-3-Clause-style). These locators record the source boundary; they are not a
patent search, infringement decision, legal clearance, or freedom-to-operate
opinion.

## IntelliJ warning in `Counter.scala`

The Chisel build currently runs inside Docker. IntelliJ therefore needs its own
local SDK for code analysis:

1. click `Setup SDK` and select or download a JDK 17;
2. ensure the JetBrains Scala plugin is enabled;
3. click `Setup Scala SDK` and select Scala 2.13.17 if it is offered.

Do not select the host's current Java 8. Project-local `.idea` state stays
ignored and is not a reproducibility record. The Docker smoke remains the
authoritative build until a host BSP/Mill import is deliberately added.
