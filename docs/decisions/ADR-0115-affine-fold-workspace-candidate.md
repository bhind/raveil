# ADR-0115: Runtime-file affine-fold execution in the workspace

Status: Proposed
Date: 2026-10-11
Task: T-0211 local candidate
Context: ADR-0107 simulation-first; T-0210 / Proposed ADR-0114 MF01 core

## Boundary and authority

The owner requested continued work. This local candidate connects the previously
verified standalone core to the project workflow without changing MF01 semantics.
It depends on the separate unpublished T-0210 packet. T-0209 composition remains
independent. No public Issue, Project item, delivery branch, accepted architectural
decision, EXP conclusion or hardware permission is inferred.

## Build once, configure each execution

A reusable Verilator runtime consumes a little-endian request file, not embedded
test vectors. The file is eight transport words followed by65 MF01 configuration
words and exactly both input spans. Header: magic0x4d465231,version1,lengthA,
lengthB,stallSeed,cancelAfterResponses,faultAtTransaction,reserved0.
The last two controls are functional-test injection hooks, disabled by default.
Transport lengths must equal the MF01 input lengths. Reject malformed/trailing
requests; hardware configuration admission remains active.

The same RTL and executable accept different programs, shapes and inputs without
rebuilding. A separate build command uses the existing pinned image with
--pull=never and no network, readonly repository/dependency mounts, and an existing
verified cache volume. The receipt binds copied Scala/C++/port-adapter/build
script, emitted SV, simulator bytes, toolchain and build log. It is local
integrity evidence, not signed provenance or dependency-cache completeness.

## Workspace lifecycle

The existing project gains fold-check, fold-run, fold, folds and fold-diff.
A region uses ADR0114's descriptor; a separate input JSON has exact keys
schema=raveil.fold-input/v1 and buffers=[A,B]. Both are bounded project inputs.
Admission and reference evaluation happen before run creation.

Each fresh folds/ID directory captures region/input bytes, compiled request,
execution options and a private copy of the bound build. Only the executable
bit changes during copying. Data is mounted readonly; a separate device
directory receives binary trace, output and device receipt. No live source
input is read after capture. The same copied build identity must hold after
execution.

The adapter reconstructs the exact affine request sequence and successful store
values from the captured SSA computation. Responses must match readonly input
data and the fault-injection ordinal. Successful execution requires complete
ordered traffic, matching counts, no errors, matching output bytes and an
independent SSA reference. Failures may retain raw private bytes but expose no
published output. Record.json is the atomic publication point; a keyboard
interrupt after rename preserves already published success. No fsync/crash
durability or hostile concurrent-writer guarantee is added.

All saved reads verify inventory, plan, inputs and the frozen request.
Successful records additionally verify the build and transaction semantics,
without running Docker or the simulator. Incomplete records retain potentially
invalid build/device diagnostics without authorizing their output. Comparisons
require successful records with the same build and output shape. Unsealed
attempts are visible as unsealed in history; they are not valid results.
The existing16MiB/1024-entry snapshot bounds remain; maximum admitted trace is
11,808,768bytes and fits with the retained build.

## Interrupts and unfinished work

MF01 cancellation injected through the request drains the offered transaction.
Host interruption/timeout instead removes the named container and reaps its
client before recording an incomplete attempt. Any uncertainty during cleanup,
including interruption, timeout or OS failure, raises CleanupUncertain and leaves
the attempt unsealed. Killing the Docker client alone is insufficient.
The build wrapper uses the same named-container cleanup boundary.

This adapter has no physical timing meaning. Stall seeds exercise finite
patterns, not every interleaving. No QEMU/AXI integration, floating point,
multi-region scheduling, standard-IR lowering, coordinated in-flight hardware
reset proof, FPGA fit or Groq performance advantage is added.

## Supplemental reset acceptance

A separate fixture executable reuses the identical emitted RTL to test six
coordinated core/responder resets: validation; a read offer under backpressure;
an accepted read awaiting response; a write offer under backpressure; an accepted
write awaiting response; and one completed private output write. In each case,
reset clears control/completion state while preserving private memory contents;
a new ADD→MUL configuration and new inputs produce33,91 with four reads and two
acknowledged writes. All six pass. Offered-request cases reset at the first
blocked offer, not after a prolonged stall. This is finite synchronous
coordinated-reset simulation, not asynchronous/skewed/AXI reset evidence.
