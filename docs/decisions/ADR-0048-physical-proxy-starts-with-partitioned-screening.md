# ADR-0048: Physical proxy starts with partitioned screening

Status: Accepted
Date: 2026-08-15

## Context

EXP-0008 completed the frozen 256-input RTL latency/traffic matrix and returned
`advance-partial-latency-traffic`. The static Graph candidate therefore reaches
the remaining RFC-0005 physical-proxy gates, but the current executable design
is a standalone Graph region. It does not instantiate the required Rocket
fallback in one physically integrated hierarchy. Reporting the Graph island
alone as a whole-system area, static-power, or dynamic-energy result would
contradict RFC-0005.

The pinned Chipyard source contains an older Sky130/Yosys/OpenROAD tutorial
coordinate, but Raveil had no owned synthesis, timing, area, or activity
collector. A candidate-independent toy smoke is needed before any candidate
data so tool installation failures cannot be mistaken for a design result.

## Decision

T-0044 physical evidence proceeds in two separately gated stages.

The first stage is a partitioned synthesis screening under one pinned
linux/amd64 Yosys 0.27+3, OpenSTA 2.3.3, and Sky130 HD typical-corner Liberty
coordinate. Static Graph versus Rocket is primary. BOOM may be added as a
secondary physical control, while BOOM serialize-dispatch remains a runtime
diagnostic and is never a distinct physical organization.

The screening reports:

- Graph candidate-local incremental logic separately from the common fixture
  provider, common owned scratchpad or abstract memory, and fallback;
- Rocket core logic under the same library and clock constraint;
- the analytical logic-area composition `Rocket fallback + Graph incremental`
  as well as each partition;
- mapped cell area, cell counts, clock constraint, setup slack and critical
  path for each admitted partition; and
- exact generated-RTL, source, configuration, image, binary, library,
  constraint, raw-report, and parser identities.

The first stage is a synthesis estimate and lower-bound screening, not a placed
design, static-power result, dynamic-energy result, FPGA result, or silicon
result. Common memory area may cancel only when the same explicit macro or
black-box boundary is used on both sides. It is never replaced by registers on
one side only. Integration, clock tree, interconnect, physical memory, and
fallback-idle overhead remain unmeasured and must be disclosed.

RFC-0005's 25% incremental Rocket-core area rule may reject the candidate if
the complete Graph incremental partition alone already exceeds the threshold;
missing integration overhead cannot rescue that lower bound. A Graph timing
miss may reject the candidate only when Rocket meets the exact same constraint
and both timing reports are complete. Passing either screen authorizes only the
next whole-system boundary; it does not establish RFC-0005 go.

Dynamic-energy evaluation requires a later integrated or equivalently complete
composition that includes Rocket fallback idle/active behavior, common memory
read/write/idle energy, adapters, clocks, and all six lifecycle phases over at
least 64 fresh inputs. RTL transition counts, simulator wall-clock, default
toggle assumptions, Graph-only activity, or zero-imputed unavailable CPU
activity cannot substitute for that boundary.

Before candidate data, EXP-0009 must freeze the exact matrix, partitions,
generated-RTL closure, tool/library identities, clock, estimator, raw schema,
and fail-closed conditions. Repeated deterministic synthesis checks
reproducibility only and is not an independent statistical sample.

## Consequences

The repository may implement and run a candidate-independent toolchain smoke
before the EXP-0009 candidate freeze. Candidate synthesis reports remain
prohibited until the implementation authority and machine-readable manifest
are committed.

The accepted T-0057/ADR-0039 mechanism remains unchanged and repository-owned.
This decision adds no elastic/token mechanism, external RTL, FPGA/product use,
patent clearance, non-infringement conclusion, or freedom-to-operate claim.
Any missing organization still requires its own mechanism-specific review
before implementation.
