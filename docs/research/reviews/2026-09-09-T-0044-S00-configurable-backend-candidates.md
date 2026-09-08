# T-0044/S00 configurable backend candidate qualification

Date: 2026-09-09  
Evidence class: Planning  
Decision authority: none; this review qualifies a later bounded experiment and
does not adopt source, a backend, or an architecture.

## Question and method

ADR-0049 requires a public configurable control before Raveil may advance a
custom configurable executor. This review inspected three candidates at exact
public revisions. The screen asks whether one fixed hardware organization can
accept at least three topology- and memory-distinct programs, whether Raveil's
CPU fallback and effect boundary can remain outside the candidate, and whether
compilation and configuration costs can be exposed. Repository licenses were
read as copyright metadata only. No patent search, freedom-to-operate opinion,
standards clearance, build, source import, simulation, FPGA execution, or PPA
measurement was performed.

## Result

No candidate is qualified for adoption or direct use as T-0044 evidence.
OpenASIP v2.2 is the only qualified **feasibility-spike candidate**: it exposes
a complete retargetable compiler/simulator/RTL flow and separates the machine
description from separately compiled program images. A later task may attempt
three programs on one frozen machine and simulator. Failure to build or retain
one unchanged machine/RTL ends that spike. OpenEdgeCGRA and VTA remain public
controls, not adapter candidates.

| Candidate | Fixed identity and copyright metadata | Interface and configurability | ADR-0049 gaps | Disposition |
| --- | --- | --- | --- | --- |
| OpenASIP 2.2 / TTA | [`f2282048f4c78d18190a9b77e7497e29a164721d`](https://github.com/cpc/openasip/tree/f2282048f4c78d18190a9b77e7497e29a164721d); project LGPL-2.1, generated HDL described as MIT | An architecture definition describes the machine; the toolchain compiles programs to instruction-parallel binaries and supplies simulation plus synthesizable VHDL/Verilog generation. This is the closest temporal schedule-memory control. | The fixed revision has not been built by Raveil. Its patched LLVM and Linux dependencies are substantial; macOS support is described as experimental. Three programs on one frozen ADF/RTL, configuration bytes/time, lifecycle parity and PPA are unproved. | One Linux-container, simulator-first feasibility spike; no import or adoption. |
| OpenEdgeCGRA | [`4a179fcf6faee18765f66baa0a30af91e3840728`](https://github.com/esl-epfl/OpenEdgeCGRA/tree/4a179fcf6faee18765f66baa0a30af91e3840728); core manifest says `Apache-2.0 WITH SHL-2.1` and refers to `LICENSE.md` | A two-dimensional instruction CGRA loads kernel and PE instruction memories; a kernel ID can select and reload an instruction image without reloading it for repeated execution. | `LICENSE.md` returns 404 at the fixed revision, so the repository's referenced license terms are incomplete. File headers also contain differing SHL and Apache identifiers; the manifest string is upstream metadata, not a validated SPDX conclusion. The external simulator, X-HEEP/common-cells dependencies, pinned build, three-program receipt, full configuration cost and Raveil lifecycle parity are unverified. | Stop before source use. Retain as prior-art/control only until upstream license and reproducibility gaps are resolved. |
| Apache VTA | [`d4a15f627d5cc9762a82270d1be60a136e6af9c2`](https://github.com/apache/tvm-vta/tree/d4a15f627d5cc9762a82270d1be60a136e6af9c2); Apache-2.0 | The driver allocates a device, accepts an instruction stream and bounded wait-cycle count, and reports timeout. The instruction format covers load, store, GEMM, finish and a small ALU. Simulator and FPGA backends are documented. | Tensor blocking, quantized data and TVM coupling do not naturally match Raveil's current exact unsigned-32 Graph semantics. Hardware configuration changes can require rebuilding the runtime/hardware. Three matching Graphs, full configuration cost and effect/fallback parity are unproved. | Retain as a programmable accelerator control; not the primary adapter spike. |

## Bounded OpenASIP spike contract

A successor may proceed only as an experiment-private adapter around an
unmodified, exact-revision OpenASIP installation. It must:

1. pin a Linux container, upstream revision, dependency identities, licenses,
   build command and build receipt;
2. freeze one reference ADF and generated-RTL identity before compiling any
   candidate program;
3. compile and simulate three small programs with different operation-graph
   topology and memory behavior: a neighborhood transform, an elementwise
   multiply/add chain and a reduction;
4. record source/IR/program hashes, compile wall time, program/configuration
   bytes, simulator command and output, admitted reads/writes and independent
   oracle equality for each program;
5. keep staging, capability/effect checks, timeout, cancellation, fallback and
   publication in a Raveil-owned wrapper, then exercise the same owned contract
   on the CPU and candidate paths, including rejection, cancellation,
   unpublished failure, fallback and successful publication. Upstream output
   remains private until validation succeeds; and
6. identify and independently demonstrate at least one contract-lifetime or
   authority property that the public compiler/runtime does not already supply;
   renaming its mapper, scheduler or execution API is not sufficient; and
7. stop on any RTL regeneration or machine-description change between the
   three programs, missing license/dependency identity, reproducible
   candidate-attributable build failure in the pinned supported environment,
   unbounded execution, semantic mismatch, or inability to expose costs.

A build failure rejects the candidate only when it is reproducible in the
pinned supported Linux environment and attributable to the candidate. Network,
registry, host-resource and other infrastructure failures are retained with
receipts and retried within the ordinary resource boundary.

This spike is functional and diagnostic. It makes no latency, energy, area,
FPGA, ASIC, silicon, product-readiness, novelty, patent, or FTO claim. It does
not mutate the current frozen simulation adapter, whose stencil-specific
contract remains evidence for its existing experiment only.

Passing the spike does not close ADR-0049 criterion 4 or the T-0044 gate. A
later preregistered comparison must count installation, compilation,
configuration, execution and fallback crossings and compare area, timing and
energy proxies against the hardwired FSM, matched CPU and retained public
control. S00 authorizes none of that measurement.

## Why this is the smallest next step

Starting from a large spatial CGRA would combine mapping, routing, external
memory integration and lifecycle adaptation before proving the key question:
whether Raveil can load materially different computations into one public
programmable organization. OpenASIP makes that question falsifiable in a
software simulator and exposes scheduling/program-image costs. VTA offers a
stronger packaged runtime but would first require semantic translation into a
tensor-specific machine. A new Raveil executor would violate the purpose of
the non-reinvention gate.

## Primary public sources

- [OpenASIP README at the fixed revision](https://github.com/cpc/openasip/blob/f2282048f4c78d18190a9b77e7497e29a164721d/README.md)
- [OpenASIP license file at the fixed revision](https://github.com/cpc/openasip/blob/f2282048f4c78d18190a9b77e7497e29a164721d/LICENSE.txt)
- [OpenEdgeCGRA README at the fixed revision](https://github.com/esl-epfl/OpenEdgeCGRA/blob/4a179fcf6faee18765f66baa0a30af91e3840728/README.md)
- [OpenEdgeCGRA core manifest at the fixed revision](https://github.com/esl-epfl/OpenEdgeCGRA/blob/4a179fcf6faee18765f66baa0a30af91e3840728/OpenEdgeCGRA.core)
- [VTA README at the fixed revision](https://github.com/apache/tvm-vta/blob/d4a15f627d5cc9762a82270d1be60a136e6af9c2/README.md)
- [VTA driver interface at the fixed revision](https://github.com/apache/tvm-vta/blob/d4a15f627d5cc9762a82270d1be60a136e6af9c2/include/vta/driver.h)
- [VTA instruction constants at the fixed revision](https://github.com/apache/tvm-vta/blob/d4a15f627d5cc9762a82270d1be60a136e6af9c2/include/vta/hw_spec_const.h)
- [VTA license at the fixed revision](https://github.com/apache/tvm-vta/blob/d4a15f627d5cc9762a82270d1be60a136e6af9c2/LICENSE)
