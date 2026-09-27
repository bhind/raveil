# ADR-0105: Build and measure an affordable FPGA demonstrator

Status: Accepted
Date: 2026-09-27
Task: T-0203 / Issue276; continuation T-0188 / Issue194, T-0189 / Issue195
Authority: owner explicitly selected real hardware implementation and measurement
on an individual budget even if differentiation from Groq remains modest.
Supersedes: ADR-0103's novelty/work-reduction prerequisite for this bounded FPGA
prototype; ADR-0039's simulation-only transition restriction and ADR-0049's
pre-FPGA comparative-advantage gate for this demonstrator only.

## Decision

Make a reproducible single-board implementation and honest measurement the
immediate objective. Novelty and superiority are questions to investigate, not
entry conditions. Negative performance is an acceptable result. Existing
prior-art findings and EXP outcomes remain unchanged; no historical gate passes.

Reuse the owned bounded Graph executor, AXI4-Lite boundary, CPU fallback and
oracle. First commission two currently admitted requests on one loaded design,
then require three semantically different supported graphs before describing
the demonstrator as reconfigurable across workloads. Editable simulator opcodes
do not automatically become admitted UIO operations. Close any parity gap in a
separate concrete slice; do not silently weaken seals or regenerate RTL per job.

The first useful engineering question is the break-even point of a small
repeated data-processing job: when does FPGA execution repay staging,
installation, polling and result validation versus optimized native CPU code?
Measure it before adding DMA, widening memory, increasing graph capacity or
designing another architecture. A small commissioning fixture alone cannot
establish application value. Select one representative sensor/image-processing
trace and its semantics before the performance study, using the existing
bounded integer path rather than importing the affine research contract.

## Budget and scope

The owner has a MacBook and Windows PC, no FPGA, a monthly budget described as
a few tens of thousands of yen, and existing Codex spending of USD100/month.
No exact hardware remainder or lifetime cap is inferred. Initial incremental
spend is zero. Reuse cached tools and hardware already owned; add no cloud,
subscription, multi-board cluster, HBM card or ASIC/tapeout dependency.

KV260 is a provisional reference because the owned AXI/UIO work targets it,
not an instruction to buy it. Check the Windows host and generate/verify RTL
before a board order. Establish a concrete all-in quote and exact remaining
budget before purchase. If the total cannot fit, borrow or select one cheaper
board only after source fit and the cost of a different transport/toolchain
are known. Do not develop several board ports in parallel.

Board-independent export, tests, supported-host inventory, and repository-owned
integration preparation may proceed now. Board-specific synthesis requires
the actual supported tool/license environment; programming requires the exact
reviewed design and a physically available target. Purchases, EULA acceptance,
host installation and media/device writes remain explicit concrete actions.

## What remains authoritative

This decision updates the authority and sequencing of the historical T-0138
packet explicitly. Its checks1–6 remain required at their applicable stages:
board identity before physical operations; supported host, tool terms and
source provenance before vendor builds; boot/recovery and target capability
before device execution. Missing board observations do not prohibit offline
source preparation. Check7's PM authorization for this scoped owned
demonstrator is supplied by this ADR and the owner's direction; exact external
source/license questions and targeted qualified legal escalation remain open
until reviewed. This is not blanket legal clearance. Checks8–12 remain the
design, address/reset, Linux, functional and recovery acceptance conditions.
The old packet's "implementation not authorized" status describes its own
September2 authority, not the new authorization recorded here.

Numerical/effect contracts, independent admission, bounded resources, private
output publication, cancellation/fallback and identity checks remain intact.
Experience remains advice. Preserve source/license provenance for every reused
tool or input. This ADR supplies the PM scope decision for an owned personal
prototype, not a legal clearance or a claim of a research exemption. Specific
unresolved external-source or patent issues still receive targeted escalation;
publication or vendor availability alone establishes no clearance.

ADR-0049's comparison requirements still apply to a custom-architecture
superiority claim; T-0044 remains its own experiment line. They no longer block
an honest functional FPGA demonstrator. Historical EXP manifests and thresholds
are not altered. A new measurement plan must distinguish FPGA cycles, vendor
timing estimates, host wall time, transfers and end-to-end latency; power is
reported only if the measurement boundary and instrument are valid.

Groq is a design reference. No apples-to-oranges ranking of this small integer
prototype against Groq cloud LLM tokens/s is meaningful. The concrete outputs
are source, design/tool identities, resource reports, reproducible board runs,
CPU comparisons and limitations. Those remain valuable without a new invention.

## Delivery order

T-0203 records this decision and refreshes executable prerequisites. T-0188
collects host and budget readiness in stages; board-dependent checks remain
explicitly pending until acquisition. T-0189 follows with one exact wrapper,
clock/reset/address design and functional recovery. Then allocate the bounded
measurement experiment before candidate timing collection. Do not substitute
another broad novelty survey for the next executable prerequisite.
