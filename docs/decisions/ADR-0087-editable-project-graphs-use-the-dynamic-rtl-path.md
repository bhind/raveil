# ADR-0087: Editable project Graphs use the existing dynamic RTL path

Status: Accepted
Date: 2026-09-05
Task: T-0148/S02
Related: ADR-0035, ADR-0077, ADR-0078, ADR-0080, ADR-0084, ADR-0085

## Context

Identifier reconciliation: this decision was drafted and accepted on the
continuation branch as ADR-0086 before the canonical inventory decision
acquired that identifier on main. Integration assigns ADR-0087 without
changing the accepted design; the original remains in branch history.
Canonical ADR-0086 continues to govern inventory and session synchronization.

T-0148 supplies bounded address generality and T-0149 supplies an editable
project workspace, but the project recipes only reach Command Graph and GEMM
backends. A user cannot yet edit the dynamic Graph and observe its RTL result
through that workspace. The owner explicitly selected that connection as the
next development slice.

## Decision

Extend project-recipe/v1 with an explicitly admitted `graph-device` kind:
`descriptor` is a flat JSON filename under `inputs/`, and `seed` is uint32.
This kind requires the new project backend name `rtl-sim`. Existing command
and GEMM recipes and their backend choices retain their semantics.

`init` includes an editable four-node relative-load neighborhood Graph.
`show` invokes the existing compiler and reports nodes, dependencies, load
coordinates, shape and instruction count. It rejects profiles that the
existing dynamic request transport cannot run. Editing `ADD_U32` to `MAX_U32`
or changing a coordinate within the existing halo changes the installed
program, without editing the Chisel source or instruction set.

`run` snapshots project inputs, captures descriptor bytes once, checks the
snapshot digest, and compiles those exact bytes. The dynamic adapter places
a data-only copy under the repository's private artifact tree and invokes
the existing dynamic request preparation, offline runner and verifier.
Project paths never select executables, simulator images, ABIs or a device.
The ordinary strict admission, independent descriptor oracle, C++ fallback,
and RTL output byte comparison remain required.

Before saving success, require the returned descriptor, program and output
digests to match the captured descriptor, compiled Graph and returned bytes;
require the saved input tree to remain equal to the initial snapshot. A
failed check retains a failed run and publishes no successful output.

Retain the recipe, descriptor, compiled Graph/lowering trace, generated input,
receipt and full output in the project history. `output.bin` contains the
unchanged 256-word little-endian transport window; `output.txt` projects only
active rows using the admitted output stride. `diff` compares content and
reports whether simulator, RTL-manifest and program hashes match. Raw AXI,
source, ABI, toolchain and simulator artifacts remain under the existing
repository artifact directory, referenced by the receipt and run record.

Input data still uses the existing deterministic seed generator. Arbitrary
user-supplied tensor bytes are not introduced. The backend is Verilator RTL
simulation, not Sonatine or CPU QEMU. Its evidence label is
`rtl-simulation-functional` and it makes no performance claim.

## Consequences

- The operator can edit a supported Graph and observe a second or third
  execution through the project loop, including a changed operation/address.
- The compiler still admits the existing four opcodes, eight value registers,
  sixteen instructions, two dynamic affine profiles, and one-cell halo.
- The existing offline runner builds the generic simulator for each run.
  Matching binary/RTL hashes can be verified in history; persistent simulator
  caching or an interactive resident execution service is deferred.
- History remains cooperative local development storage, not a signed audit
  store or hostile-code isolation boundary.
- No Chisel/C++ execution logic, transport ABI, physical backend, performance
  experiment, research gate, or CPU comparison changes.

## Supersession

This extends ADR-0085's admitted recipe/backend combinations and composes
ADR-0084's existing simulation capability. It supersedes no execution or
evidence authority rule.
