# ADR-0045: Semantic attribution is commit-aware and CPU-owned

Status: Accepted
Date: 2026-08-13

## Context

ADR-0044 intentionally places the first CPU translation target on an
observable, uncached, resource-unmatched path. Subsequent T-0042 diagnostics
identified the generated DCache TileLink client ranges, carried a structural
DCache-origin bit, and separated one SimTSI/FESVR PT_LOAD path plus one Debug
SBA path. A cross-workload verifier then showed that two distinct ELF binaries
reuse the exact same final DCache source and origin class in each CPU
configuration. Those fields identify a transport class, not an instruction,
ELF, or architectural commit.

The standalone ADR-0043 bridge already accepts explicit initiator and phase
metadata, but its harness supplies those values. Promoting a software phase,
TileLink source, DCache-origin bit, PC alone, or request acceptance into semantic
identity would leave replay, redirect, exception, reset, and retirement
ambiguous. BOOM additionally permits speculative issue and tracks memory
operations through ROB and load/store queues; Rocket has distinct MEM, WB,
kill, exception, and replay paths. A common downstream tag cannot reconstruct
those CPU-specific facts.

This decision supersedes ADR-0044 only for the unresolved semantic-attribution
policy. ADR-0044 remains authoritative for the uncached, unmatched translation
topology and its claim boundaries.

## Decision

Semantic attribution for the owned CPU adapter is assigned inside the CPU
boundary that still knows the instruction lifecycle. It is not derived from a
final TileLink source range, a DCache-local origin bit, or software-writable
state. The first implementation is diagnostic and CPU-specific before any
common-contract promotion.

Each candidate memory operation receives an implementation-owned token and
epoch before its first DCache request:

- Rocket binds a sequence to the EX/MEM pipeline PC corresponding to the same
  `io.dmem.req` candidate, operation, address, and redirect/reset epoch before
  request acceptance, then preserves that token through MEM/WB correlation;
- BOOM binds a sequence and redirect/reset epoch as the primary identity, with
  ROB index, branch mask, operation, and address as lifecycle-validation
  context and PC as supporting context. ROB index and branch mask are not
  unique identities and cannot substitute for the sequence and epoch;
- loader, FESVR, Debug SBA, recovery, and untagged traffic cannot mint a CPU
  token and remain explicit non-CPU or unknown classes;
- no token field is software writable, and an absent, stripped, stale, or
  malformed token at the CPU-to-owned-adapter metadata handoff fails closed to
  unknown rather than CPU-attributed.

Token and epoch widths are implementation-bounded and explicit. Neither may
silently wrap into an identity that is live or retained by the diagnostic.
Sequence exhaustion blocks new admission and reports failure. An epoch may
advance only under the separately checked redirect/reset rule; exhaustion or
alias risk also fails closed. ROB index reuse never authorizes token reuse.

The token names one candidate architectural memory operation, not one DCache or
TileLink attempt. Core pipeline replay and downstream DCache retry are distinct
attempt events but retain the same token and increment their respective
accounting. A new token for either replay, reuse across epochs, two live
operations with one token, or two committed outcomes for one token is an
assertion failure. TileLink A acceptance and D completion remain separately
conserved transport events.

A candidate becomes commit-attributed only after all required CPU and memory
events agree:

- a speculative load remains pending after a successful memory response and
  requires exactly one matching architectural retirement before attribution;
- a store requires three matching conditions for one token: architectural
  retirement, the CPU-specific store-commit authorization, and actual owned
  manager D completion. Conditions may coincide in one cycle, but each predicate
  is checked and no subset is sufficient. Rocket uses exception-free
  WB/retire-valid state for its store authorization and retirement correlation;
  BOOM separately records ROB retirement and the matching STQ committed
  authorization. Their signal names are not treated as one common upstream
  contract;
- a kill, redirect, exception, rollback, or reset prevents promotion. If a
  side effect completed for such a candidate, the diagnostic reports a
  fail-closed lifecycle violation rather than relabeling it committed;
- reset advances the epoch, invalidates every unresolved token, and forbids a
  later response or retirement from matching an earlier epoch;
- response backpressure, same-transport-source serialization, and D completion
  do not change token ownership or the one-outcome rule.

An exception, redirect, or rollback after TileLink A acceptance does not cancel
the transport. If D completion or an irreversible side effect follows, the
operation remains non-commit-attributed and the diagnostic records an explicit
lifecycle violation; the decision does not claim absence or rollback of that
side effect.

Implement and verify Rocket and BOOM event diagnostics separately. Each must
correlate issue, every replay attempt, kill/exception outcome, A acceptance, D
completion, and retirement/commit before its token may feed the owned
initiator field. Only after both CPU-specific diagnostics pass the same
fail-closed lifecycle contract may a later change connect this attribution to
the ADR-0043 bridge or call it a common CPU adapter.

The revision-specific source and license locators for those diagnostics are
recorded in
`docs/research/reviews/2026-08-13-T-0042-semantic-attribution-source-survey.md`.
Implementation must bind to those pins, record exact patch/source hashes, and
stop for renewed review if its mechanism expands beyond the surveyed
CPU-specific probes.

Required positive coverage includes one load reaching response plus retirement
and one store satisfying retirement, its CPU-specific authorization, and owned
manager D completion. Required negative coverage
includes replay without duplicate commit, pre-request kill, post-request
exception or rollback, reset with an outstanding token, stripped metadata,
stale-epoch response, duplicate token, and untagged loader/FESVR/Debug traffic.
The verifier must retain the existing source/origin classifiers as transport
evidence while refusing to use either as semantic identity.

## Consequences

The first implementation will touch pinned Rocket and BOOM lifecycle paths and
is therefore larger than the current DCache-local hook. CPU-specific event
probes are preferred over prematurely forcing unlike pipeline and ROB signals
into one upstream type. The repository-owned output contract may normalize the
event vocabulary only after each adapter has established its own correlations.

This decision defines ownership and fail-closed acceptance criteria; it does
not implement the probes or prove that a particular ELF was the semantic
initiator. Passing the future diagnostics will be bounded functional RTL
evidence for the exercised lifecycle cases, not a general security proof.

Resource matching remains a separate ADR-0043/T-0044 prerequisite. This
decision supplies no latency, throughput, performance, energy, power, area,
timing, FPGA, silicon, OoO-removal, novelty, non-infringement, patent-clearance,
or freedom-to-operate conclusion. No EXP is created until a separately
preregistered measurement question exists.
