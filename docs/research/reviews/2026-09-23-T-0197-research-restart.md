# T-0199: Research restart and known-optimization control

Date: 2026-09-23
Status: Local preflight evidence; integration follows T-0199 / #268
Evidence: primary-source review, code inspection, host functional checks and analytical counts
Original base: cached `ecf5655`. September 26 integration base: fresh `bdfac7f`.
Original filename/receipt retain the provisional ID; live T-0197 is Issue #266.

## What changed in direction

Owner instruction selects reconsideration and resumption from the original
Raveil thesis, not acceptance of any claimed invention in the discussion.
ADR-0103 keeps semantic authority and repeated-work amortization, but requires
work reduction beyond known controls before selecting new execution hardware.
The narrow region/buffer and installed-control/lookup suggestions are deferred
alternatives. The 28-claim audit is retained, not overwritten or relabelled as
an audit of the newer mainline code. Its original checkout was `7c38a36`.

## Primary-source comparison packet

| Source / locator | What it already covers | Consequence for Raveil |
|---|---|---|
| Groq, [ISC 2020 slides](https://mlhardware.github.io/2020/groq.pdf), pp.8–9, 15–16 | Weight loading/install, explicit timing, reusable kernels/components | Reuse and static execution are controls, not novelty |
| Groq, [US20230385125A1](https://patents.google.com/patent/US20230385125A1/en), description `Live State Driven Partitioning` | Peak live-state/resource-aware graph partitioning and device count; preference for resident weights | Capacity management/partitioning is not a missing Groq feature; publication is not proof of every current product implementation |
| NVIDIA, [Groq 3 LPX](https://developer.nvidia.com/blog/inside-nvidia-groq-3-lpx-the-low-latency-inference-accelerator-for-the-nvidia-vera-rubin-platform/), March 16 2026, MEM and deterministic execution body sections | Compiler/runtime placement, SRAM-first capacity, explicit movement and heterogeneous GPU/LPU execution | Do not argue that Groq cannot use external orchestration or support variable applications |
| [Intel RDT](https://www.intel.com/content/www/us/en/architecture-and-technology/resource-director-technology.html), framework; [AMD PQOS](https://docs.amd.com/api/khub/documents/VuNrmUG_yfhPVgGYcFlkZg/content), Nov.2025 chapters 2 and 6 | Monitoring, cache/bandwidth allocation and dynamic resource control | Resource statistics and allocation are established engineering |
| [REVEL](https://polyarch.cs.ucla.edu/papers/hpca2020-revel.pdf), HPCA 2020 §V; [selective dynamic HLS](https://arxiv.org/abs/2308.15120), abstract | Systolic/dataflow combination and selective dynamic scheduling | Regional dynamism is not a new principle |
| [da4ml](https://arxiv.org/abs/2507.04535), abstract; [constant-matrix CSE](https://arxiv.org/abs/2303.16106), abstract | Known fixed-matrix arithmetic specialization and sharing | Treat as applicable controls; do not extrapolate small quantized FPGA results to dense LLMs |
| [Mirage](https://www.usenix.org/conference/osdi25/presentation/wu-mengdi), OSDI 2025 abstract | Joint algebraic/schedule transformations and generated kernels with equivalence checking | Search plus verification is not a unique integration claim |

This is a provisional screening packet from the prior conversation; source
links are not archived/version-sealed evidence or defeated controls. This packet is
not an exhaustive literature or patent search, legal clearance or license
approval. No external implementation was imported. Relevant implementation
licenses and mechanism-specific IP overlap remain unreviewed until adoption.

## First concrete work: establish a known algebraic control

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/research/probes/constant_work_baseline.py
```

The probe reads the existing T-0182 threshold/cross-dilation descriptor and
input, constructs one hand-authored comparison descriptor in memory, and
uses the unchanged owned compiler. It changes no source graph or production
optimizer. For one common threshold t and unsigned operands, monotonicity gives
`max_i [x_i >= t] = [max_i x_i >= t]`. This identity holds over the full uint32
domain; the tests are supporting checks, not its proof. Different thresholds
provide a retained counterexample to unrestricted interchange.

Four thresholds (0, 1, 100, maximum encodable immediate) cover 91 input cases,
including the existing fixture, constant extremes, boundary patterns, seeded
full-range and near-threshold values. For every case, both descriptors' Graph
oracles and encoded software fallbacks equal an independently written direct
five-address specification on all 256 output words, including zero padding.
The finite boundary alphabet additionally checks 16,819 five-value tuples.

| Quantity | Existing graph | Known control |
|---|---:|---:|
| Instructions per output cell | 15 | 11 |
| Threshold comparisons per output cell | 5 | 1 |
| LOAD / MAX / STORE per output cell | 5 / 4 / 1 | 5 / 4 / 1 |
| Fixed installation payload | 128 bytes | 128 bytes |
| Logical load/store bytes over 64 cells | 1,536 | 1,536 |

Receipt: [T-0197-known-control.json](../receipts/T-0197-known-control.json).
The reported source hashes cover named probe dependencies/fixtures, not a full
sealed hardware toolchain. No timing, RTL, physical traffic, area, energy,
trained model, performance comparison or gate result was collected.

## Findings and next work

The current bounded Graph corpus exposes immediate constants and mutable
input snapshots, not an immutable trained-weight tensor interface. The fixture
already permits a known algebraic reduction using unchanged instructions.
It does not demonstrate a new architecture, partial-evaluation engine or
the benefit of learned Experience. The unchanged payload/traffic also show why
operation count alone cannot be called a speedup.

Next: T-0200 pins one representative workload and numerical/binding contract
under RFC-0007 and selects the strongest applicable baseline. No automatic
production rewrite, ISA extension or matrix accelerator is authorized by this
probe. T-0183 planning is complete; its T-0197 / #266 implementation and
T-0186 remain preserved, deferred product work.
