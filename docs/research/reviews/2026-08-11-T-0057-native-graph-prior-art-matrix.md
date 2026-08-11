# T-0057 native-graph prior-art and design-input matrix

Status: Non-authoritative research draft
Date: 2026-08-11
Task: T-0057
RFC context: RFC-0003, RFC-0004
Evidence class: literature review; no Raveil performance evidence

## Question and correction

This review asks which parts of the proposed low-level Graph study are already
established mechanisms, which comparison controls are still useful, and which
choices must remain blocked before RTL implementation.

The comparison list previously written in RFC-0004 was not yet derived from a
direct-prior-art matrix. That ordering was insufficient. The generic Chisel and
unmodified RISC-V tooling substrate may continue because it selects no Graph
mechanism. T-0042 must not implement Graph RTL until T-0057 records a narrower
contract, source locators, and an IP-risk disposition for the mechanisms it
actually proposes to adopt.

## Primary sources checked

- TRIPS evaluation: M. Gebhart et al., *An Evaluation of the TRIPS
  Computer System*, UT Austin TR-08-31; PDF pp. 1–2 for the EDGE block and
  instruction communication model and the reported comparison limitations.
- TRIPS compiler: A. Smith et al., *Compiling for EDGE Architectures*; PDF p. 1
  for block constraints and direct communication, and p. 7, section 3.6, for
  memory ordering and block termination.
- WaveScalar: S. Swanson et al., *WaveScalar*, MICRO-36; PDF pp. 1–2 for the
  WaveCache, cached instructions, dataflow locality, ISA, and ordered-memory
  claims.
- DySER: V. Govindaraju et al., *Dynamically Specialized Datapaths for Energy
  Efficient Computing*, HPCA 2011; PDF p. 2 for statically routed functional
  units and repeated-phase amortization, p. 7 for the retained processor load
  back-slice and memory disambiguation, and pp. 11–12 for author-reported
  results and limitations.
- BOOM documentation: pipeline, reorder buffer, issue queue, load/store unit,
  and debugging sections. These define observable comparison structures; the
  OoO-disable switch is diagnostic and is not a replacement for an independent
  in-order Rocket control.

The paper summaries below are Raveil-authored paraphrases, not copied source
abstracts. Author-reported performance is not Raveil evidence and is not used
to predict a win.

## Mechanism matrix

| System | Node/granularity and dependency source | Placement/readiness | Memory, control, and commit | Retained general CPU role | Implication for T-0057 | IP state |
|---|---|---|---|---|---|---|
| Conventional OoO / BOOM | decoded micro-operations; hardware rename, issue and wakeup discover dynamic readiness | centralized/distributed issue queues and execution units | LSU orders memory; ROB supplies in-order architectural commit and precise state | the CPU is the complete executor | Use Rocket and BOOM as distinct controls. Record rename, ROB, issue and LSU activity; do not call a diagnostic switch an in-order core. | Upstream license and patent/FTO review remain separate and unreviewed. |
| Itanium / EPIC | compiler bundles instructions and dependencies at ISA level | compiler scheduling plus hardware execution resources | speculation, predication and recovery remain architecturally visible concerns | complete general-purpose CPU | Compiler-exposed parallelism and VLIW-like comparison are prior art, not Raveil novelty. | Unreviewed. |
| TRIPS / EDGE | compiler forms bounded atomic blocks; instructions name consumer targets and communicate values directly | block mapped over execution nodes; dataflow firing within a block | explicit load/store IDs order memory; block termination, architectural outputs and commit bound visibility | EDGE core is a complete CPU and retains block-level control/commit machinery | Direct producer-to-consumer targets, bounded graph blocks and block-atomic execution are prior art. Any adoption needs an independently specified difference and precise-exception analysis. | High similarity. A preliminary search found EDGE/dataflow commit and issue patent families; no clearance. |
| WaveScalar | program is a dataflow graph divided into waves; instructions can remain in a WaveCache across invocations | data arrival enables nodes distributed over the WaveCache | wave ordering supplies total load/store order; dynamic memory behavior remains a limiting problem | proposed complete ISA/microarchitecture | Cached instruction graphs, distributed dataflow firing and wave-ordered memory are prior art. Do not relabel them as a new Graph cache. | High similarity. A preliminary search found US7490218B2, *Building a wavecache*; status/FTO not determined. |
| DySER | compiler extracts a computation slice and configures a heterogeneous functional-unit array | static routes; repeated phase invocations amortize configuration | the main processor retains load back-slice, memory disambiguation and difficult control | explicitly hybrid with a conventional processor | An attached, statically routed graph engine with CPU fallback is also prior art. The hybrid option is an engineering baseline, not a novelty claim. | High mechanism similarity; patent-family search incomplete and no clearance. |
| Spatial CGRA / XDNA class | coarse operations mapped to tiles with local memories and explicit movement | spatial placement and scheduled communication | host/control processor and DMA or memory fabric retain irregular work | hybrid accelerator | Tiles, local memories, streams and explicit DMA do not establish differentiation. | Unreviewed. |
| Proposed Raveil study | not selected; candidate scope is a bounded operation/effect/object region, not host tools | not selected; static, elastic and hybrid are alternatives to falsify | alias proof, memory ordering, exceptions, cancellation, rollback, versioned object publication and fallback are unresolved | likely retain a RISC-V fallback in the first study, but this is not accepted | The study may test whether a lifetime-bound contract reduces repeated discovery/configuration while preserving exact effects. It must not assume the answer or attribute ordinary memoization to Graph. | No novelty or FTO conclusion. Directly similar mechanisms remain blocked from adoption. |

## What the literature changes

The following are not defensible Raveil novelty claims: explicit dependency
graphs; direct instruction-to-instruction communication; cached resident graph
instructions; static spatial placement; token/data readiness; local graph
memories; compiler-scheduled parallelism; an attached graph accelerator; or a
fallback CPU. They are comparison dimensions and prior art.

The first plausible research question is narrower: can a versioned contract
covering operations, dependencies, externally visible effects, aliases,
objects, fallback and semantic validation be installed once and reused across
repeated executions with less dynamic discovery/coordination than matched
controls? Even this is a hypothesis, not a novelty or performance claim. Its
potential distinction is the whole contract lifetime and authority boundary,
not any individual dataflow mechanism. Experience is excluded from the first
isolation because EXP-0003 did not establish useful transfer and because
advice must never become execution authority.

## Required design contract before Graph RTL

T-0057 must choose and justify, with source-backed contrasts:

1. exact node granularity and graph-construction boundary;
2. dependency and alias producer: compiler, admission proof, hardware, or a
   bounded combination;
3. ISA visibility: ordinary RISC-V plus attached commands, a custom extension,
   or an internal microarchitectural encoding;
4. memory ordering and what happens when an alias fact is wrong or unknown;
5. exception, interrupt, cancellation, rollback and precise publication rules;
6. placement/readiness state and a resource bound showing it is not merely a
   renamed ROB/issue window;
7. configuration identity, invalidation and one-time versus repeated cost;
8. a trusted RISC-V fallback and exact semantic oracle;
9. fair Rocket/BOOM controls, identical resource assumptions where possible,
   and declared differences where not;
10. a stopping rule that permits no-go when configuration, retained machinery,
    correctness state or PPA proxies erase the hypothesized benefit.

Until these are fixed, static, elastic, stream and hybrid organizations are
study candidates only. There is no selected ISA and no authorization to
replace OoO machinery.

## Preliminary patent/IP triage

This was a targeted discovery pass, not a patent search or legal opinion.
Public access, academic publication, and open-source code do not establish a
license to implement patent claims or freedom to operate.

- A WaveScalar-related result identified US7490218B2, *Building a wavecache*.
- EDGE-related results identified US10824429B2, *Commit logic and precise
  exceptions in explicit dataflow graph execution architectures*, and
  WO2015069583A1, *Energy efficient multi-modal instruction issue*.
- The search did not establish current claim scope in intended jurisdictions,
  ownership, expiry, enforceability, licensing, or whether a proposed Raveil
  mechanism reads on any claim.
- No definitive DySER family was established in this pass. That is a search
  gap, not a finding of absence.

Vreji must retain these entries as high-similarity, unreviewed risks. Direct
adoption of block-atomic EDGE commit, explicit target instruction encodings,
WaveCache-style resident graph machinery, or the identified multi-modal issue
mechanism remains blocked pending a concrete claim-to-feature review and, if
the work moves beyond research simulation, qualified legal advice.

## Recommendation

Continue T-0105 only through unmodified RISC-V elaboration/execution evidence.
Make this matrix phase A of T-0057. Phase B should write the minimal contract
and explicitly choose whether the first candidate is a narrow attached engine
or an internal execution model. A hybrid is presently the lower-bootstrap-risk
candidate, but DySER and CGRA prior art mean it is not automatically novel or
better. Do not begin T-0042 Graph RTL or T-0044 performance measurement until
that phase-B contract and IP disposition are reviewed.

## Non-claims and gaps

- No source result has been reproduced by Raveil.
- No cited mechanism has been accepted for implementation.
- No paper or patent proves that Raveil can remove OoO, reduce energy, reduce
  area, or beat a commercial ARM CPU.
- The patent pass is incomplete and cannot establish non-infringement or FTO.
- Detailed quantitative extraction, correction/retraction checks, complete
  bibliographic metadata, license review, and claim-chart work remain open.
