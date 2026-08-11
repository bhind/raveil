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
