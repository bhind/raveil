# T-0202: No new mechanism selected; retain the known-CSE control

Date: 2026-09-27. [Issue274](https://github.com/bhind/raveil/issues/274).
Context ADR-0103 / proposed RFC-0007. Evidence: primary-source analysis,
analytical identities/counts and host-functional checks. No EXP or Gate decision.

**Decision:** none of the seven concretely scoped proposals qualifies as a
new Raveil mechanism. Retain same-column product sharing as a **known control**;
reject exact dense low-rank and the specified Hadamard realization for this W.
The other families lack an identified beyond-known algorithm and complete-cost
case. This rejects these proposals as currently formulated, not all future
linear-circuit algorithms, all workloads, or all exact specialization.

The [prospective plan](T-0202-screen-plan.md) was committed at `59774ef` before
new structural scans. It fixes the candidate set, source, inputs and decision
rules. T-0200/0201 already inspected/used this W; the plan does not imply blind
selection of a previously unseen matrix. [The receipt](../receipts/T-0202-candidate-screen.json)
binds the unchanged layer0 source, probe/reference and plan hashes.

## Source and mechanism matrix

Sources were read on September27,2026. Locator text below is a bounded paraphrase,
not copied algorithms or a claim to have executed the published implementations.

| Source | Exact primary locator/version read | Relevant mechanism and remaining gap |
|---|---|---|
| S1 | [Oppelstrup, JCP247 (2013), DOI10.1016/j.jcp.2013.03.042](https://www.sciencedirect.com/science/article/pii/S0021999113002209), publisher preview: Introduction / Compression algorithm | Reusable matrix preprocessing, repeated patterns and rank-one submatrices. General matrix CSE predates this proposal. Preview access does not establish our FP envelope. |
| S2 | [Common Subexpression-based Compression and Multiplication of Sparse Constant Matrices, arXiv2303.16106v1 (2023)](https://arxiv.org/html/2303.16106v1), §II, §III-A, §III-B.1–3 | Explicitly computes each distinct column coefficient times its input once; also searches repeated two-term forms and stores weights/indices. Direct overlap with C1/C3. Its quantized/sparse evaluation is not our dense F16 experiment. |
| S3 | [Mohammadi Sarband/Gustafsson/Garrido, 2020, DOI10.1007/s11265-020-01560-z](https://link.springer.com/article/10.1007/s11265-020-01560-z), §1 and abstract | Constant matrix multiplication, MCM, shared add/subtract/shift networks and transposition. Hardware adder objectives are not host FP costs. |
| S4 | [da4ml, arXiv2507.04535v1 (July6,2025)](https://arxiv.org/html/2507.04535v1), §1.1.1, §2, §3.1–3.4; [2026 publication metadata](https://authors.library.caltech.edu/records/mbekq-xv638) | Exact fixed-point CMVM, decomposition and CSE across signed/power-of-two-scaled terms. Dyadic F16 has an exact integer-grid embedding, so this family cannot be dismissed merely by calling the workload floating point. Width, rounding and backend costs still require a separate implementation. |
| S5 | [US3777130A](https://patents.google.com/patent/US3777130A/en), description of input-bit-addressed memory and shifted accumulation; publication December4,1973 | Historical DA/LUT overlap. This is a mechanism locator only; no present legal-status, family, jurisdiction or FTO conclusion. |
| S6 | [Mirage, OSDI2025 paper](https://www.usenix.org/system/files/osdi25-wu-mengdi.pdf), §5 Numerical stability (PDF page10), §6 | Multi-level algebra/schedule search; finite-field/real equivalence and separate FP testing. Its tests do not establish our universal gamma258 bound. A missing FP certificate is not itself a new scheduling mechanism. |
| S7 | [Prism, arXiv2604.15272v1 (2026)](https://arxiv.org/html/2604.15272v1), §3–4, §6, §7 | Symbolic parameterized graphs, e-graph equivalence, then tuning. §4 says a formal soundness proof is outside its scope; algebraic axioms and random checks cannot be imported as our FP proof. Symbolic search alone is prior-art territory. |
| S8 | [Daisy, TACAS2018, DOI10.1007/978-3-319-89960-2_15](https://link.springer.com/chapter/10.1007/978-3-319-89960-2_15), §1 / optimization overview | Sound roundoff analysis and rewriting already coexist in prior work. Adding a numerical checker to an algebraic optimizer does not by itself define a new contribution. |
| S9 | [Dao et al., ICML2019](https://proceedings.mlr.press/v97/dao19a.html), abstract and sparse-factorization framing | Fast transforms via sparse factors / butterfly structure. Learning or approximating another matrix does not preserve this fixed W; a cheap factorization needs an exact identity, not just a familiar basis name. |

No source code, paper tables or model weights are redistributed. The repository
contains owned arithmetic probes and derived non-weight receipts. Model rights
remain as recorded in T-0200; reading papers is not patent or implementation
clearance. Source-reuse/IP review is bounded and not exhaustive. Groq paper/blog
links attempted in this screen returned404/502; no fresh vendor-internal claim
is based on those failed fetches.

## Candidate-by-candidate outcome

| ID / proposed simple solution | Identity or discriminator | Observed result / full-cost obstacle | Novelty and selection disposition |
|---|---|---|---|
| C1: compute a repeated coefficient product once, distribute it | `p[j,c]=c*x[j]`; original per-row sum order | 63,659 products versus65,536, all65,536 additions/incidence uses retained. Defined packed representation388,272B versus264,192B widened dense parameters; indexing/scratch added. | **Reject novelty**, direct S2 §II/III-B.1 overlap. **Retain as functional known control**. Runtime benefit unmeasured, not disproved. |
| C2: strip sign and powers of two, share odd-significand products | `w = sign*m*2^k`, odd m; count bases per input column | 62,147 absolute-value bases /51,306 odd bases. There are65,536 nontrivial power-of-two scales and33,003 negative uses; sign/scale, routing and encoding are not free. No optimized implementation or complete cost result. | **Do not select**: proposed identity is known MCM/CMVM territory (S3/S4); no new algorithm beyond it specified. Counts alone are not a benefit. |
| C3: compute common input linear forms, then reuse across rows | Shared two-term forms / rank-one submatrices | One repeated occurrence among the64 preselected adjacent-column pairs; zero zero-coefficients and zero duplicate rows. Other pairings, scaled forms and recursive CSE were not searched. | **Reject the broad novelty pitch**, S1/S2. **General efficacy inconclusive**; bounded scan is not a defeat of published CSE. |
| C4: replace the matrix by a smaller exact bottleneck | `W=UV`, rank r; dense cost640r | Modular rank128 in both declared prime fields proves exact rational rank128. Dense r<=102 is needed to beat65,536 products; r128 costs81,920. | **Reject this exact dense low-rank candidate for this W**. Does not reject sparse full-rank factors or approximate models under another contract. |
| C5: change to a cheap Hadamard basis to expose zeros | `W'=WH/128`, `t=Hx`, `W't=Wx` | No zero in W';896 input-transform additions;54 transformed coefficients are not exactly representable as one F32 constant. | **Reject the specified dense-F32 Hadamard realization**. Rounding coefficients changes the real function; multi-term representations would need new cost/error analysis. Other bases remain untested; basis ideas are known (S1/S9). |
| C6: replace multiplication with DA tables/bit-plane accumulation | Exact dyadic integer-grid embedding | Generic input requires29 signed bits, generic exact result76 signed bits. Explicit uncompressed group4 example1,572,864 table bytes /475,136 bit-plane lookups; group8 example12,582,912B /237,568 lookups. Neither is a minimum over DA. | **Reject novelty** (S3–S5); **do not select these cost-unjustified examples**. No claim that optimized da4ml/DA is defeated or intrinsically slower. |
| C7: search equivalent graphs with a verified error constraint | Algebraic identity plus gamma258 proof, then schedule/cost search | No concrete residual search rule, proof acceleration, cost advantage or exact-domain implementation beyond known ingredients supplied. | **Do not select the combination as a new mechanism** (S6–S8). A new algorithm inside these families remains possible; family membership is not a proof of non-novelty. |

The novelty decision is about these concrete proposals. In particular, a new
search algorithm can still be novel while outputting an ordinary CSE DAG.
Conversely, merely relabeling a known DAG or moving it onto Raveil hardware
does not establish such an algorithm. No missing baseline is called defeated.

## Known-control witness and exactness

C1 reuses products only within the same input column, never across different
inputs merely because their coefficients match. The dictionary key preserves
all F16 bits, including signed zero. Each finite binary16 product has at most
22 significand bits. In this bounded domain it is exactly representable in
binary32 without overflow or underflow. Reuse therefore reproduces the same
rounded product; retaining each row's original j-order retains the serial
binary32 recurrence for every admitted input under the stated arithmetic.
No new cancellation or reassociation is introduced.

Eight existing commissioning vectors compare shared-product, repeated-call
and ordinary serial outputs against the independent exact-integer oracle:
12,288 component checks, with bitwise serial agreement. This does not claim
bitwise equality to FMA/Accelerate, whole-model quality, or representative
activation performance. Six focused tests cover same-column isolation, signed
zero, nonfinite/source corruption, cancellation, a direct Hadamard matrix,
rank against an independent rational-basis routine and a bad-modulus example.

The product saving is1,877/65,536 = approximately2.864%. This is a real
analytical reduction achieved by a known method, even though T-0201's four
compiler outputs retained every coefficient lane. Those compiler observations
must not be generalized into an impossibility result.

## Representation, lifecycle and uncertainty

The C1 hypothetical packed layout is254,636B F32 dictionary +131,072B uint16
local IDs +516B uint32 column offsets +2,048B F32 bias =388,272B. It increases
this particular representation by124,080B (approximately46.966%) against
264,192B widened dense W+b. Maximum one-column F32 product scratch is2,032B;
output is2,048B. Each invocation generates63,659 scratch products and follows
65,536 incidence entries, with65,536 row additions. Preparation builds/verifies
the dictionary and indices; changed W invalidates both. These counts do not
measure bandwidth, CPU instructions, time, working set or economic break-even.

The actual witness uses Python containers and has larger overhead. It does not
implement this packed layout or an optimized native backend. Smaller IDs,
F16 dictionaries, grouped fan-out or emitted code can change the tradeoff and
add widening/decode/code costs. Thus representation expansion here is not a
lower bound, and no speed ranking against Accelerate is established.

For C4, W is an integer matrix times2^-24. A nonzero128×128 minor modulo an
odd prime is nonzero over the rationals; rank cannot exceed128. Primary and independent Tester also computed the first
128-row minor: determinant25194 modulo65521 and6628 modulo65519. Deficiency in
one modular image would only be a lower bound, not proof of low rational rank.
C5 computes WH in integers at scale2^-24, then represents W' at2^-31 without
rounding the identity test. C6 table estimates use the entire exact dyadic grid,
including points not representable as F16, and generic width bounds; exploiting
the smaller domain or shared tables could reduce them. Full128-input addressing
would have2^128 entries **per output row and bit plane lookup function**, which
explains partitioning, not a lower bound on every DA implementation.

All preparation, code/configuration growth, product distribution, numerical
verification, replacement, cache/port constraints and execution must be charged
before a performance claim. No inference about Groq's unpublished optimizer or
current product limits follows. A useful frontend reduction could also be used
on conventional hardware; a separate backend contribution remains unproved.

## Result and project consequence

Close T-0202 as **candidate-selection work completed with no qualifying new
mechanism**. Do not open an RTL or speed experiment on the strength of these
seven pitches. Keep C1 as a stronger known-control witness and retain the
negative/inconclusive records. Existing functional Raveil work is unaffected.

This completes the authorized question rather than deferring the same vague
proposal to another optimization task. Reopening novelty needs an explicitly
specified algorithmic difference with the relevant known method, or an
explicitly changed workload/contract and a new rationale. Product integration
of known methods is a valid separate engineering direction, but is not evidence
of the originally sought architectural differentiation.
