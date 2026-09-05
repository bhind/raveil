# Linux driver-development harness

This directory is a non-authoritative Linux transport harness for Raveil-owned
contracts. It does not replace Sonatine, admit real Daphnis jobs, expose DMA or
MMIO, or write Experience.

Build on Linux with `make -C linux`. Run `raveil-linuxd` and `raveilctl` as the
same unprivileged user with `XDG_RUNTIME_DIR` set. The daemon creates a mode
`0600` `SOCK_SEQPACKET` endpoint, verifies `SO_PEERCRED`, accepts one client and
one fixed-size request at a time, and removes the socket on normal shutdown.

The v1 ABI supports only `PING` and transport-test `NOP`. It contains no
pointers, paths, file descriptors, credentials, capability handles, physical
addresses, or Linux-private structures. A real job schema remains T-0030.

Run the non-root end-to-end check with:

```sh
runtime_dir="$(mktemp -d)"
XDG_RUNTIME_DIR="$runtime_dir" make -C linux smoke
rmdir "$runtime_dir"
```

The harness deliberately has no network listener, root requirement, kernel
module, `ioctl`, `mmap`, DMA, MMIO, interrupt, or filesystem-data operation.

## Bounded Graph-device UIO transport (provisional)

`raveil-graph-device-uio-run` is deliberately separate from the socket
harness.  On a Linux system with a board-specific `/dev/uioN` already exposed,
it maps only UIO map 0 as a fixed 16 KiB relative register aperture.  It takes
no physical address, never opens `/dev/mem`, and implements neither DMA, IRQ,
cache management nor a kernel module.  A regular file or anonymous mapping is
not an accepted device and cannot produce a Graph execution claim.

Build the optional Linux-only runner:

```sh
python3 -m raveil.graph_device_axi4lite_request prepare \
  --output "$evidence" \
  --graph contracts/graph_device_dags/vertical-three-point.json --seed 7
make -C linux graph-device-uio GENERATED_DIR="$evidence"
linux/build/raveil-graph-device-uio-run \
  /dev/uioN "$evidence"
```

The selected device must have `/sys/class/uio/uioN/maps/map0/size` equal to
`0x4000`; the runner rejects every other span before mapping it.

On the tentative KV260 target, run the separate read-only readiness check
before attempting the UIO runner:

```sh
python3 -m raveil graph-device kv260-preflight --device /dev/uioN
```

It requires Linux aarch64, a KV260 device-tree model, bounded FPGA-manager
state, exact character-device/sysfs identity, and one aligned 0x4000-byte map
0. It uses `lstat` on the explicit path and reads fixed procfs/sysfs leaves; it
does not open or map the device, issue MMIO, load an overlay or mutate the
host. A PASS is only `target-host-observation`, and its marker states
`device_opened=0 mmio=0 performance=not-measured`. The later UIO runner must
still repeat its opened-object checks.

### Sealed dynamic UIO dry-run

Before any future dynamic UIO transport, a sealed dynamic request can be
converted to a relative-aperture plan without opening its named device:

```sh
python3 -m raveil graph-device dynamic-uio-dry-run \
  --sealed artifacts/graph_device_dynamic_sealed/<manifest-sha256> --device /dev/uio0
```

The command first verifies the sealed payload inventory and compiler identity,
then reports only the 16 KiB relative execution, affine, and program namespaces.
It performs no `open`, `mmap`, or MMIO (`device_opened=0 mmap=0 mmio=0`). This
is Host Functional planning evidence, not RTL simulation, FPGA/KV260, hardware
performance, or device-success evidence.

Version-2 sealed requests may contain exactly the T-0143 `MAX_U32` opcode in
addition to the v1 LOAD/ADD/STORE alphabet. The dry-run derives the same seven
relative ABI operations from either admitted version and still performs no
device operation. Request/program cross-version pairs and opcode 4 under v1
fail before a plan is returned. The program-install, affine-install and
execution transport ABIs remain v1 and the 16 KiB aperture is unchanged.

The shared C++ request reader also admits the T-0148 version-3 simulation
request after validating signed one-cell relative loads and the exact program
digest. That does not extend the sealed/UIO path: T-0148 stops at the existing
AXI4-Lite Verilator runner, and the version-1/2 sealed transport behavior above
remains unchanged.

T-0145 adds the next no-device boundary. The ADR-0079 verifier projects one
verified sealed-v2 request into a private request root, then a Linux host
adapter consumes that root through an injected `RegisterIo`. The adapter has
no UIO backend, `/dev/uioN` argument, opener, mapping or MMIO primitive; tests
use a fake register transport to prove install, input, start, poll, output and
oracle equality. The ARM64 build target compiles an object only:

```sh
make -C linux graph-device-dynamic-uio GENERATED_DIR="$generated"
```

It is intentionally not a runnable device command. Connecting
`UioRegisterIo` requires a later physical task with an unbypassable verified
handoff, fresh T-0139 observation and ADR-0071 opened-object checks.

An ARM64 Linux build can be reproduced on the development host with:

```sh
docker build -f linux/Dockerfile.graph-device-uio \
  -t raveil-graph-device-uio:local .
```

The command is only a host transport.  Successful opening is not FPGA,
bitstream, performance, or authority evidence; actual board enablement remains
a separate reviewed gate.

From the repository root, `docker build -f linux/Dockerfile -t
raveil-linux-driver .` builds the Linux-only sources and shared job contract.
A non-root smoke is:

```sh
docker run --rm --user 65534:65534 \
  --tmpfs /runtime:uid=65534,gid=65534,mode=700 \
  -e XDG_RUNTIME_DIR=/runtime raveil-linux-driver
```

The Dockerfile is verification scaffolding, not a deployment image.
`BASE_IMAGE` may be overridden with an already-audited local Debian-derived
image when registry metadata is temporarily unavailable; the default remains
the public `debian:bookworm-slim` base.

## Userspace graph MVP

T-0086 uses a separate container definition so the transport harness above is
not widened into an authority service:

```sh
docker build -f linux/Dockerfile.graph-mvp -t raveil-graph-mvp:t-0086 .
docker run --rm raveil-graph-mvp:t-0086
```

When registry metadata is unavailable, an already-audited Debian-derived base
can be selected explicitly:

```sh
docker build --build-arg BASE_IMAGE=raveil-linux-driver:latest \
  -f linux/Dockerfile.graph-mvp -t raveil-graph-mvp:t-0086 .
```

This executes the owned graph/contract and native-C adapter entirely in
GNU/Linux userspace. Its JSON is segregated host-correctness evidence; the
container does not gain Sonatine, Experience, commit, or measurement authority.

The optional pinned MLIR import slice has its own image and retains the same
native graph backend after import:

```sh
docker build -f linux/Dockerfile.iree-import -t raveil-iree-import:t-0040 .
docker run --rm raveil-iree-import:t-0040
```

The image verifies the locked IREE wheel, compiles the one admitted MLIR
fixture, and runs the owned graph loop. It does not execute IREE VMFB or create
runtime/performance evidence.

If public registry metadata is unavailable, the already-audited local
`raveil-graph-mvp:t-0041` image can be supplied explicitly with
`--build-arg BASE_IMAGE=raveil-graph-mvp:t-0041`; this override must be
recorded as local-base evidence rather than a clean-registry build.

## Sonatine/QEMU graph backend

T-0090 keeps the same graph frontend and adds an explicit emulation adapter.
Build it from the repository root using the locally audited Sonatine toolchain
image:

```sh
docker build -f linux/Dockerfile.sonatine-graph-mvp \
  -t raveil-sonatine-graph:t-0090 .
docker run --rm raveil-sonatine-graph:t-0090
```

The corresponding host command is:

```sh
python3 -m raveil graph-mvp \
  --backend sonatine-qemu \
  --family gemm --m 8 --n 8 --k 8 \
  --sonatine-kernel sonatine/build/sonatine.elf \
  --output /tmp/raveil-sonatine-result.json
```

The adapter passes a fixed 128-byte pointer-free v1 request through QEMU's
loader device, then accepts exactly one bounded serial result bound to that
request and the existing job/completion lifecycle. The output evidence class
is `qemu-emulation-correctness`; its absent latency is deliberate and cannot be
used for performance selection or a silicon claim.
