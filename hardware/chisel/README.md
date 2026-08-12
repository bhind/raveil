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
requires the disjoint input/private-output objects, fixed six-phase logical schedule,
one read port, one adder, one write port, zero runtime-ready slots, RV64IM
fallback declaration, and ADR-0039 exclusions. Its canonical SHA-256 is
`d4bf9395a510385f42ba4a193ae2c747f308ad502a8fe807843ed19c2fa4d1e2`;
the RTL exposes the first 64 bits only as a binding tag.

The Chisel module applies that schedule to all 256 output points. The C++
testbench computes the uint32 stencil independently, checks all outputs and the
checksum for two different inputs, cancels a third invocation, requires the
private output to become invalid, and then restarts successfully. Success emits:

```text
STATIC-STENCIL-RTL-V1 status=OK runs=2 cancelled=1 outputs=512 cycles_per_run=3072 graph_input_reads_per_run=1280 graph_output_writes_per_run=256 configuration_tag=d4bf9395a510385f memory_model=owned-private-banked-scratchpads cpu_connected=0 fixed_end_to_end_latency_claim=0 resource_match_verified=0 matched_comparison_ready=0 evidence=rtl-simulation-functional performance=not-measured
```

The six logical load/store phases now traverse two disjoint instances of the
owned request/response scratchpad. Its conservative one-outstanding protocol
uses an acceptance cycle and a response-retirement cycle for each of five reads
and one write, so the current functional FSM checks 3,072 execution cycles per
run. Input staging takes 648 local cycles and independent output validation
takes 512. These are implementation accounting facts, not a Rocket/BOOM
comparison or performance result. The Docker path reuses the existing
owned-counter Chisel 7.2.0 tool coordinate and a disposable Scala/Coursier
cache. T-0044 must define a fresh matched and immutable environment before any
comparison.

After a successful RTL run the host wrapper emits three strict
`raveil.simulation-adapter/v2` JSON records: completed, cancelled, then
completed after restart. The common adapter fixes semantic and useful-operation
counts and exposes separate installation, staging, execution, completion,
validation, and publication phases. The current records explicitly use
`accounting_complete=false` and `total_cycles=null` because three phases remain
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

Observe the bank-local TLRAM single-beat request/response boundary with:

```sh
./hardware/chisel/run-tlram-latency-observer.sh
```

The wrapper builds separate non-tracing Rocket and BOOM simulator models with
a passive SystemVerilog bind, leaving the validated normal simulators intact.
It matches each accepted TileLink A beat to its completed D beat by source ID,
checks unmatched responses, premature source reuse, and pending requests, and
classifies accepted addresses into the RFC-0005 input, output, or other region.
The current pinned run observed 296 completed beats in every CPU mode, all
classified as reads: 162 input-region, 128 output-region, and 6 other-region
beats, each with one cycle from bank-local TLRAM acceptance to response
completion. No write beat was observed. Initiator and lifecycle phase are not
identifiable at this boundary, so cache refill, execution, and FESVR signature recovery traffic
cannot be separated. This is functional diagnostic telemetry for one pinned
run, not fixed end-to-end latency, resource matching, comparison readiness, or
performance evidence.

The local simulator image tag and persistent build volumes are functional
bootstrap caches, not immutable evidence inputs. The wrapper checks the pinned
source revision, lock identity, tracked source cleanliness, and tool versions,
and disables container networking; T-0044 still requires a separately frozen
measurement environment.

Exercise the first Raveil-owned local scratchpad transaction boundary with:

```sh
./hardware/chisel/run-owned-fixed-latency-scratchpad-rtl.sh
```

This is a standalone Graph/CPU adapter target, not yet either adapter. It has
one decoupled request stream, one decoupled response stream, at most one
outstanding transaction, explicit read/write plus byte mask, and bounded
initiator/lifecycle-phase attribution. An accepted request makes exactly one
response available on the following module-local cycle. A held response keeps
all fields stable until consumed. The assert-enabled Verilator harness covers
reads, writes, partial writes, request and response backpressure, deterministic
range rejection, attribution, and accepted/completed/pending accounting.

The successful marker deliberately reports
`fixed_end_to_end_latency_claim=0`, `resource_match_verified=0`, and
`matched_comparison_ready=0`. The standalone module is now also instantiated by
the static Graph region, but it is not connected to either CPU; its local
one-cycle protocol is not a
CPU/Graph latency, throughput, energy, area, FPGA, silicon, or performance
result.

Elaborate the first CPU-side translation target with:

```sh
./hardware/chisel/run-owned-cpu-memory-elaboration.sh
```

The runner installs one repository-owned overlay into an ephemeral copy of the
pinned Chipyard source and generates dedicated Rocket and Small BOOM systems.
The overlay removes the inherited scratchpad configuration, adds the owned
32-bit TileLink manager at `0x08000000` plus its control page at `0x08010000`,
and attaches it to the uncached peripheral bus. This is intentionally not the
same resource topology as the private Graph memories. The phase register is a
software-declared label, and initiator attribution is still unverified.

Success means both RTL topologies elaborate and contain the owned manager. It
does not mean either CPU executed a program, the TileLink protocol corner cases
ran in simulation, the manager-local response property became end-to-end CPU
latency, or the resources are matched. The marker keeps execution not run,
resource matching and comparison readiness false, and performance not
measured. ADR-0044 requires a later phase-fenced functional workload and direct
protocol testing before promotion.

Run the direct owned-manager protocol simulation with:

```sh
./hardware/chisel/run-owned-tl-protocol.sh
```

This builds a pinned Chipyard assembly in an ephemeral source copy, emits the
raw-client/owned-manager harness through FIRRTL, compiles it with assert-enabled
Verilator, and runs 30 legal negotiated TileLink transactions. The test covers
full and partial writes, masks `0x5` and `0xa`, invalid phase denial, response
backpressure and metadata stability, maximum-one-outstanding admission, reset
phase, aggregate counters, expected/unexpected source-class conservation, and
preservation of accepted source/phase through D completion. Its content-addressed
assembly cache is keyed by the overlay, pinned Chipyard revision, and built
image identity and verifies the cached JAR checksum before reuse. It remains a
functional-development optimization, not immutable
measurement evidence. The raw client bypasses Rocket and BOOM; success remains
`rtl-simulation-functional`, with CPU execution not run, initiator attribution
unverified, resource matching false, and performance not measured.

Protocol V4 intentionally narrows the expected classifier range to `[1,3)`
inside the client's legal `[0,4)` range. The 30-transaction run reports
expected accepted/completed 3/3 and unexpected accepted/completed 4/4 for
deliberate boundary sources 0 and 3. It also re-presents the same source while a
D response is held and verifies that the one-outstanding manager refuses it.
Because this raw client supplies no DCache-origin request field, it also reports
DCache-origin accepted/completed 0/0 and non-origin 7/7. This is negative
source-class, structural-origin, and conservation evidence for the raw harness,
not proof of CPU execution, target-ELF semantic initiator identity, or complete
loader/debug exclusion.

The same runner also elaborates `RaveilOwnedTLOriginStripHarness`. Its test-only
raw client advertises the request field and drives origin true on every request,
then `RaveilOriginStrippingAdapter` removes that field from downstream
negotiation. The same 30-transaction driver reports
`OWNED-TL-ORIGIN-STRIP-V1` with upstream origin true, downstream origin absent,
origin accepted/completed 0/0, and non-origin 7/7. This proves that loss of this
metadata fails closed at the owned manager and remains correlated across A/D;
it is not a model or execution of an actual FESVR, loader, or debugger path.

Run the standalone TileLink-to-owned-contract bridge with:

```sh
./hardware/chisel/run-owned-tl-contract-bridge.sh
```

This uses a real post-fragmenter TileLink client/manager connection but keeps
both CPUs out of the harness. The bridge retains TileLink source and size for D
while translating operation, word address, data, byte mask, and explicit
adapter inputs for initiator/phase into an upstream-type-free owned
request/response. The assert-enabled target covers full and partial writes,
masks `0x5` and `0xa`, readback, range denial, single-outstanding request
blocking, response backpressure, metadata stability, and 6/6 conservation.
The assembly cache key covers the exact overlay, pinned Chipyard revision, and
built image identity; reuse verifies the cached JAR checksum before
elaboration. The successful marker says `attribution=adapter-input-only` and
`semantic_initiator=not-proven`: this is translation-mechanics evidence, not a
claim that a CPU, ELF, loader, or debugger supplied the request. CPU connection,
matched resources, end-to-end latency, performance, power, and area remain
open.

Run the same CPU workload through the owned manager on Rocket and BOOM with:

```sh
./hardware/chisel/run-owned-rocket-memory-smoke.sh
./hardware/chisel/run-owned-boom-memory-smoke.sh
```

The two thin entrypoints select an allowlisted configuration and call one shared
runner. Separate content-addressed simulator volumes compile the same bare-metal
RV64 ELF and execute real Rocket or BOOM RTL load/store instructions against
the owned data page at `0x08000000` and control page at `0x08010000`.
Before simulation, the shared runner verifies the exact generated graph. It
requires the Rocket DCache-MMIO range to expand to `[8224,8256)`, the BOOM
range to `[8288,8320)`, and the SimTSI/FESVR serial range to `[0,8192)` at the
manager-adjacent fragmenter. These are config/Xbar/fragmenter-derived source
coordinates, not ISA-level IDs.
The ELF uses `fence iorw,iorw`, covers a full write and two byte-lane writes,
changes the software phase, and records data plus aggregate counters in a
30-word signature whose first 22 words retain the previous layout and which is
independently decoded on the host. It additionally
requires expected-source accepted/completed 8/8, unexpected-source 0/0,
in-range last accepted/completed sources, and phases 2/2. A successful marker is
`rtl-simulation-functional` evidence for each mapped path only. Both runs
produce the same decoded data, phase, and counter signature. The composite
payload hash covers the overlay, ELF source, linker script, source-map verifier,
signature verifier, and shared runner; CPU/configuration is reported separately
in the marker.
Before reuse, the runner rejects unexpected tracked or untracked source-cache
changes while allowing only the intended overlay and task-local SBT `target/`
outputs.
The observed source range establishes only a TileLink client class. A
repository-owned adapter immediately after each DCache sets a one-bit request
field. A pinned ephemeral TLXbar patch preserves negotiated request fields and
applies their declared false defaults to clients without the field; runners
verify the patch and exact pre/post Xbar hashes. The manager latches the field
at A acceptance and correlates it internally to D completion. Both CPU runs
require origin accepted/completed 8/8, non-origin 0/0, in-range final origin
sources, and origin phases 2/2. This proves bounded structural DCache-boundary
crossing, not the target ELF's semantic initiator, instruction, or PC, and it
does not exclude all untested loader/debug DCache activity. The phase remains a
software-declared adapter label rather than
ADR-0043 owned initiator/phase metadata. Resources are unmatched, OoO is not
isolated, and performance is not measured.

Each CPU entrypoint also builds and runs `owned_memory_loader_probe.S` with
`owned_memory_loader_probe.ld`. The probe ELF has exactly one four-byte
writable `PT_LOAD` at `0x08000000`; code, its 33-word signature, and `tohost`
remain in main RAM. The shared runner verifies the exact program-header and
symbol addresses, does not pass `+loadmem`, and then checks two snapshots from
one simulator process. Before CPU access, accepted/completed are 2/2, the
sources are in SimTSI/FESVR `[0,8192)`, origin is 0/0, and non-origin is 2/2.
The pinned FESVR transport aligns the partial segment write using a read then a
write, so the two transport requests are not evidence that every ELF segment
has a fixed request multiplicity. The CPU then reads payload `0x6c6f6164`;
totals become 3/3, origin becomes 1/1, non-origin remains 2/2, and the final
origin source falls in the selected Rocket or BOOM DCache range. The
`OWNED-MEMORY-LOADER-PROBE-V1` and `OWNED-CPU-LOADER-PROBE-AUDIT-V1` markers
are bounded `rtl-simulation-functional` evidence for this PT_LOAD path only.
They do not prove a semantic ELF initiator, cover Debug SBA or every loader/
debug path, establish resource matching, isolate OoO, or measure performance.

`run-owned-rocket-debug-sba-smoke.sh` and
`run-owned-boom-debug-sba-smoke.sh` select dedicated configurations with an
exported DMI port and a repository-owned finite driver. The driver activates
the Debug Module, confirms an 8-bit `sbaccess`, writes `0xa5` to `0x08000000`
through SBA, and checks busy/error completion. Exact generated graph checks
require Debug `[8192,8224)`, Rocket DCache `[16416,16448)`, or BOOM DCache
`[16480,16512)`. The 37-word signature then requires the Debug write to be
unexpected/non-origin 1/1 and the CPU read to be expected/origin 1/1, with
aggregate 2/2 and accepted/completed phase zero. The driver has finite RTL and
simulator watchdogs and accepts a DMI response only when paired with an
outstanding or same-cycle accepted request. These are bounded functional RTL
and TileLink client-class checks; no halt/resume, instruction/PC, semantic ELF
initiator, complete debug exclusion, resource match, OoO, or measurement claim
is made.

Pinned Rocket/BOOM source hooks now place the structural marker after the
DCache and before the tile master Xbar. This distinguishes tagged DCache traffic
from the separate SimTSI/FESVR master in the bounded positive, raw-client
absence, test-only field-stripping, and concrete PT_LOAD probe runs, but it
does not prove which ELF instruction or PC semantically initiated a request.
Durable owned attribution requires a later decision plus remaining loader/debug
path testing.

After the regular CPU and PT_LOAD signature verifiers pass,
`verify_owned_cpu_source_nonidentity.py` compares both artifacts and ELF
binaries. It requires two distinct ELF hashes and distinct semantic payload
witnesses while also requiring the same exact final tagged DCache source:
8224 for Rocket or 8288 for BOOM. The
`OWNED-CPU-SOURCE-NONIDENTITY-V1` marker is an executable counterexample to
treating a TileLink source or DCache-origin bit as ELF identity. It supplies no
replacement identity, instruction/PC attribution, security property, resource
match, or performance result.

ADR-0045 defines the next diagnostic before any additional pinned-core patch.
Rocket must correlate a bounded CPU-owned sequence with the matching EX/MEM PC,
operation, and reset/redirect epoch across DCache issue,
replay/kill/exception, response, and retirement. BOOM uses sequence/epoch as
identity and ROB index plus branch mask as lifecycle context through its LSU and
commit paths. Exhaustion or alias fails closed. Replay keeps one token; loads
require response plus retirement, stores require retirement plus CPU-specific
store authorization and owned-manager D completion, and killed,
exceptional, reset, stale, duplicated, stripped, loader/FESVR, Debug, or
untagged cases fail closed. A post-A exception cannot cancel transport and a
later side effect is a lifecycle violation.

`./hardware/chisel/run-rocket-lifecycle-observer.sh` now exercises a standalone
repository-owned Chisel ledger with synthetic events. The assert-enabled
`linux/amd64` RTL simulation reports exactly one
`ROCKET-LIFECYCLE-OBSERVER-V1` marker: 21 allocations resolve to 3 committed
loads, 1 committed store, and 17 noncommitted operations; A/D counts are 7/7,
with 5 retirements, 2 unknown inputs, and 8 violations. The cases include
load/store positives plus replay, retry, kill, exception after A, reset with an
outstanding request, stale epoch, stripped/untagged metadata, duplicate token
and outcome, invalid completion, D error, and finite sequence exhaustion. The
host verifier requires the exact schema and bounded claim fields, checks
terminal conservation, and rejects field deletion, counter mutation, or marker
duplication. The recorded input hash is for the repository inputs, not a
content-addressed proof of the mutable Docker/APT/Scala cache dependencies.

This observer is not either CPU probe: `event_source=synthetic`,
`cpu_execution=not-run`, `semantic_initiator=not-proven`,
`resource_match_verified=0`, `matched_comparison_ready=0`, and
`performance=not-measured`. The pinned Rocket signal hook and BOOM probe are
still unimplemented, and the token must not enter the owned common bridge until
both CPU-specific lifecycle suites pass.

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
