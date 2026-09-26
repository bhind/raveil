# RFC-0007: Immutable-function work reduction before a Daphnis mechanism

Status: Proposed
Scope: evaluation contract; no performance experiment frozen
Date: 2026-09-23
Task: T-0200; parent direction ADR-0103 / T-0199

## Question

For a fixed function F, declared immutable parameters W and changing input x,
can a residual program P_W preserve the numerical/effect contract while
reducing total execution cost beyond the strongest applicable known controls?
Selecting this question neither establishes novelty nor changes native Graph
semantics. The minimum project outcome may be a software optimization or a
negative result; custom hardware is conditional.

## Entry deliverable (T-0200)

Pin one workload with real reusable parameter content, source/revision,
license/access state, exact parameter hashes, shapes, input provenance,
immutable/mutable split, numerical behavior, reproducible independent oracle,
and installation/reuse lifecycle. Do not download a large model, quantize it,
change its quality target or assume permission to redistribute its weights
merely to fill this packet. Prefer a bounded extract of an approved workload.
Repository synthetic examples are controls, not representative learned models.

Select the workload before examining which proposed transform wins. Separate
development parameters/inputs from held-out parameter instances and inputs;
derive exact identities before collection. No holdout may tune a proposal.

## Required controls

1. An ordinary optimized implementation of the same function. Naive loops or
   a deliberately unoptimized graph cannot be the only reference.
2. The same implementation with known constant propagation, simplification,
   applicable common subexpressions/fusion and fixed-parameter specialization.
3. The closest applicable published method: da4ml/constant-matrix methods for
   compatible quantized integer functions, Mirage-like algebra/schedule search
   for compatible tensor programs, or another precisely justified baseline.
   An incompatible numerical domain is not a defeated baseline.
4. The proposed residual change, specified beyond those controls. If no such
   change exists, retain an empirical baseline study and stop a novelty claim.

For a later hardware comparison, use the same optimized residual computation
on the reference and proposed backend; separately report frontend-only and
backend-only contributions. A static model is not a measured Groq product.

## Accounting before speed claims

Report separately: dynamic operation categories, parameter representation,
code/configuration bytes, live storage, logical memory accesses, actual bytes
crossing each named hardware boundary, compilation/search, verification,
installation, steady execution, replacement/invalidation and fallback costs.
Logical load/store counts do not establish physical memory traffic. Fewer
operations do not establish lower latency, area or energy. Statically captured
information may move into configuration or wiring rather than disappear.

For an eventual timing study, total cost at reuse N is compile/search + verify
+ install + the N measured executions + lifecycle costs. Equal amortization
and resource budgets apply to all controls. Count reduction and the economic
break-even point must not be conflated. No numeric speedup threshold or sample
count is chosen after seeing data; allocate/freeze a separate EXP when the
workload, environment, baseline and proposed treatment are ready.

## Semantic rules

Use an independent specification oracle. For modular uint32, preserve wrap,
comparison interpretation and effect ordering. For floating point, specify
rounding, reduction order, NaN/Inf and any permitted error before transforms.
No random test suite alone proves equivalence. State the mathematical argument
or proof scope, then exercise boundary and adversarial cases. An unproved
approximation never inherits exact-function authority. Changed immutable
parameters invalidate a prior specialized artifact.

## Stops

- Only synthetic, deliberately repetitive weights benefit.
- Standard optimizations account for the complete improvement.
- Parameter/code/configuration expansion or data movement offsets savings.
- A result depends on extra resources, changed precision or weaker semantics.
- The only remaining advantage is an unmeasured product assumption about Groq.

The first diagnostic in T-0199 deliberately demonstrates a known control,
not the RFC's unimplemented proposed treatment or a passed research gate.
