# Chisel/RISC-V simulation substrate

Status: T-0105 tooling smoke; not a Graph or CPU performance experiment.

This directory first proves a pinned Chisel-to-SystemVerilog-to-Verilator path
with a repository-owned four-bit counter. It does not implement the proposed
Graph microarchitecture, execute a RISC-V core yet, or provide latency, energy,
area, OoO-removal, ISA, FPGA, or silicon evidence.

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

The base-image digest and apt-resolved package versions must be captured when
promoting this smoke into durable evidence. External licenses, notices,
source-reuse boundaries, patents, standards, and freedom-to-operate remain a
separate review requirement; public source availability is not clearance.

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
`external/rocket-chip/`; it is not
vendored, copied into Raveil contracts, or silently updated. Fetching it does
not mean that it builds or executes in the T-0105 container yet.

## IntelliJ warning in `Counter.scala`

The Chisel build currently runs inside Docker. IntelliJ therefore needs its own
local SDK for code analysis:

1. click `Setup SDK` and select or download a JDK 17;
2. ensure the JetBrains Scala plugin is enabled;
3. click `Setup Scala SDK` and select Scala 2.13.17 if it is offered.

Do not select the host's current Java 8. Project-local `.idea` state stays
ignored and is not a reproducibility record. The Docker smoke remains the
authoritative build until a host BSP/Mill import is deliberately added.
