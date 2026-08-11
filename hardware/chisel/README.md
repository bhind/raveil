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
