# RFC-0001 industry prior-art review

Status: Non-authoritative research memo
Stage: Prior-art review
Date: 2026-08-09

## Provenance

This memo integrates Frontispice handoff sequence 2,
`RAVEIL_PRIOR_INDUSTRY_APPROACHES_INTEL_AMD_APPLE.md`, ID
`5604e8cd-f216-4c42-8c05-c35572828242`, SHA-256
`613dbdbb1026aaeb51ea7c38d46365620c381a244688865b37c3b55ba5e8d70a`.
The handoff is research input, not repository authority. The primary sources
linked below were re-opened on 2026-08-09; interpretations remain hypotheses.

## Question

Does Raveil merely repeat prior attempts to move scheduling work from
general-purpose out-of-order hardware into software or specialized execution,
and what distinction remains testable?

## Verified evidence inventory

- Intel documents Itanium as EPIC, with explicit parallelism, predication,
  speculation, compiler-to-processor communication, and software-pipelined loop
  support.
- Intel's 2024 Lion Cove presentation expands rather than removes the OoO
  engine: retirement 8 to 12 wide, allocation/rename 6 to 8 wide, execution
  ports 12 to 18, and the instruction window 512 to 576. It also splits integer
  and vector renaming/scheduling domains.
- Intel HWPGO uses PMU samples to produce compiler optimization profiles. This
  is verified execution feedback, but it is a compiler workflow rather than a
  continuously selecting runtime Experience system.
- AMD describes XDNA as a tiled spatial-dataflow NPU. Its tiles combine VLIW
  SIMD vector processing, a RISC scalar processor, local program/data memory,
  dedicated connectivity, and DMA-scheduled movement.
- Apple's WWDC20 description of Rosetta 2 says translations may begin at
  install time, are code-signed and stored per machine, are loaded on later
  launches, and fall back to on-the-fly translation for unseen code. Translated
  applications can still reach native Metal GPU and Core ML Neural Engine
  paths.

## Existing Raveil alignment

The handoff reinforces existing boundaries rather than changing them:

- ADR-0003 already retains RISC-V for control, trusted baseline, cold code, and
  irregular fallback; it does not claim total OoO elimination.
- RFC-0001 and `docs/ARCHITECTURE.md` already separate explicit causality and
  effects from physically variable timing. Readiness, backpressure, arbitration,
  and completion remain dynamic.
- ADR-0005 and `docs/EXPERIENCE.md` already separate persistent evidence from a
  bounded online retrieval set and budget optimization by expected reuse,
  verification, storage, and risk.
- T-0057 already owns comparison of the explicit graph contract against
  sequential and VLIW-like baselines.

## Adoptable research framing

Raveil should not be presented as a novel VLIW, CGRA, spatial fabric, PGO
system, translation cache, or heterogeneous dispatcher. Each has substantial
prior art. A narrower falsifiable question is:

> For repeated structured regions, can an explicit dependency/effect contract,
> local elastic timing, and persistent context-aware Experience replace enough
> repeated general OoO dependency discovery to improve lifetime latency and
> energy after lookup, verification, failure recovery, and storage costs?

Daphnis hardware alone is not the differentiator. The candidate integration is
verified `GraphVariant` lineage, context-dependent selection, measured
promotion, negative evidence, shadow execution, rollback, and durable
Experience. Cold, irregular, branch-heavy, pointer-heavy, or uncertain work
must remain eligible for RISC-V, a generic backend, or bounded dynamic islands.

## Counterevidence and non-claims

Lion Cove is direct counterevidence to a blanket assertion that OoO machinery
is no longer worth its cost. XDNA is counterevidence to novelty claims based on
tiled spatial dataflow, local memory, VLIW/SIMD compute, or explicit movement.
Rosetta and HWPGO are counterevidence to novelty claims based only on retaining
expensive prior work or feeding execution profiles back into optimization.

This review does **not** establish that:

- Raveil is more energy-efficient than OoO execution;
- Daphnis has a PPA advantage over XDNA, GPU, NPU, or FPGA substrates;
- nearly matching Experience has an adequate hit rate;
- general-purpose workloads mostly admit graph-native execution;
- no commercial or research system implements a comparable integration.

Those are experiment or broader literature-review questions, not conclusions
from the handoff.

## Implications

No ADR, gate, or implementation status changes. Continue Gate 1 to establish a
real Experience boundary before hardware claims. When RFC-0001 advances under
T-0057, compare static, elastic, stream, and hybrid variants against a generic
fallback and account for boundary crossings, variable latency, verification,
and lifetime optimization cost.

## Primary sources checked

- `intel-itanium-sdm-v1` — [Intel Itanium Architecture Software Developer's Manual, Volume 1](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/itanium-architecture-software-developer-rev-2-3-vol-1-manual.pdf)
- `intel-lion-cove-architecture` — [Intel Lion Cove Architecture](https://cdrdv2-public.intel.com/824430/2024_Intel_Tech%20Tour%20TW_Next%20Gen%20P-core%20The%20Lion%20Cove%20Architecture-4.pdf)
- `intel-hwpgo` — [Intel Hardware-based Profile Guided Optimization](https://www.intel.com/content/www/us/en/developer/articles/technical/hwpgo.html)
- `amd-xdna-architecture` — [AMD XDNA Architecture](https://www.amd.com/en/technologies/xdna.html)
- `apple-wwdc20-10686` — [Apple WWDC20: Explore the new system architecture of Apple silicon Macs](https://developer.apple.com/videos/play/wwdc2020/10686/)

The keys above are registered as draft metadata in
[`docs/references/catalog.json`](../../references/catalog.json). Their exact
source revisions, rights, and page or timestamp locators remain unverified.

## Recommendation

`continue`: use the handoff as a prior-art and falsification map. Preserve the
accepted RISC-V fallback and timing-dynamic boundaries, avoid novelty claims for
individual mechanisms, and require measured lifetime economics before claiming
that Experience can make general OoO discovery exceptional rather than default.
