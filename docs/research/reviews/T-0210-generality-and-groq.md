# T-0210: Generalize the execution region; keep the Groq claim falsifiable

Date: 2026-10-10. Local candidate, not an accepted architectural pivot.
Evidence classes: primary-source reading, host functional checks, RTL functional
simulation. No Groq execution, FPGA measurement or comparative performance.

## Engineering choice

The missing abstraction is a structured iteration region whose semantics do
not depend on exact memory timing. It should express indexing, scalar work and
reduction once, then permit different implementation schedules underneath it.
T-0210 implements only a small sequential version of that region. It replaces
neither Groq's tensor throughput nor Raveil's existing verified workspace path.

Two readonly inputs, eight affine views, a short scalar program and one fold
express elementwise joins, broadcasts, transposes, row reductions, dot products
and matrix products. The same RTL accepts their runtime configurations.
This removes a real Raveil execution limitation, rather than adding another
host-side wrapper around the fixed stencil.

## Claim matrix

| Atomic claim / proposed advantage | Evidence or prior-art conflict | Disposition |
|---|---|---|
| Explicit dependencies are new | Existing Groq/compiler/dataflow work; T-0057 audit | Rejected |
| Static schedules are new | Groq deterministic compiler schedule | Rejected |
| Affine indexing and map/reduce are new | MLIR Linalg structured operations | Rejected |
| Runtime dimensions alone distinguish us | Dynamic shape handling is established; public Groq sources do not establish its absence | Rejected as a novelty claim |
| Groq cannot run programmable elementwise operations | Groq3 VXM is programmable | False premise |
| Groq has no runtime memory management | Groq3 describes compiler/runtime placement of weights, activations and KV data | False premise |
| Host/device or heterogeneous composition distinguishes us | Groq3 LPX describes GPU/LPU task division and Dynamo routing | Rejected |
| Static regions plus dynamic interfaces are new | Groq HotChips2022 static/dynamic boundary; Fifer and hybrid HLS prior art | Rejected |
| Request/response stalls invalidate this candidate's results | Same executable is functionally tested under several bounded stall sequences | Falsifiable functional property only |
| It needs no RTL regeneration when admitted dimensions/kernel change | One simulator runs distinct configurations and families | Local implementation property, not new in the field |
| A small region contract can reduce required specialization/host orchestration | Candidate directly executes joins/reductions absent from integrated RTL | Demonstrated expressiveness improvement within Raveil; total cost unmeasured |
| Raveil beats Groq in latency, energy, cost or generality | No matched Groq run, no board area/timing/power, narrow uint32 limits | Not established |

## What pursuing an advantage would actually require

Target a small affordable device serving varying structured computations and
memory service times. Hypothesis: one compact implementation with runtime
indexing/folds could reduce host intervention and variant management enough to
justify its serial execution overhead. Admission work, configuration transfers,
lost parallelism, memory traffic and recovery all count as costs.

First compare two owned implementations of exactly the same admitted semantics:
a specialized baseline and this configurable region. Freeze workload families,
input distributions, memory-service traces and complete-cost boundaries before
claim-bearing collection. Report unsupported cases and admission failures,
not only favorable cases. RTL cycles alone cannot establish device latency,
area, energy or economics. Later synthesis and a single-board experiment decide
whether the simplicity has practical value. If specialization dominates after
all costs, reject this proposed advantage; do not rename the loss as novelty.

A Groq comparison additionally needs a runnable matched workload, supported
numeric semantics and a declared boundary (compile/configure/transfer/execute).
Public vendor architecture descriptions alone cannot supply those measurements.
Groq inference service endpoints would not be a fair proxy for custom uint32
kernel execution. No superiority statement is warranted by this candidate.

## Primary sources read and bounded interpretation

- [NVIDIA, Inside Groq3 LPX, March16,2026](https://developer.nvidia.com/blog/inside-nvidia-groq-3-lpx-the-low-latency-inference-accelerator-for-the-nvidia-vera-rubin-platform/):
  sections describing MXM/VXM/SXM, deterministic communication, compiler/runtime
  SRAM placement, and heterogeneous GPU/LPU execution. The public design trades
  dedicated on-chip capacity and scheduled communication for inference speed.
  It does not prove that Groq cannot support runtime dimensions or variable
  interfaces. Vendor performance numbers are not adopted here.
- [Groq, HotChips34,2022](https://hc34.hotchips.org/assets/program/conference/day2/Machine%20Learning/HotChips34%20-%20Groq%20-%20Abts%20-%20final.pdf):
  static/dynamic interface and runtime framing; scheduled stream communication
  sections. A queue-free internal path does not imply absence of all runtime
  control. Network indirection is not evidence of arbitrary data indirection.
- [MLIR Linalg documentation](https://mlir.llvm.org/docs/Dialects/Linalg/):
  generic structured operations, indexing maps, parallel/reduction iterators.
  The proposed abstraction substantially overlaps established compiler models.
- [Fifer, MICRO2021](https://people.csail.mit.edu/qmn/papers/nguyen_fifer_micro_2021.pdf)
  and [Compiler Discovered Dynamic Scheduling,2023](https://arxiv.org/abs/2308.15120):
  regular/irregular decomposition and selective dynamic scheduling are prior-art
  directions, not unoccupied territory.

No external code was copied. Public reading does not establish patent clearance;
patent-family, jurisdiction and implementation-adoption review remain unreviewed.
Retain the28-claim T-0057 audit and T-0202's seven rejected novelty candidates.
This bounded continuation does not reverse either negative result.
