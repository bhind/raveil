# T-0187: remove repeated build work from the editable Graph loop

Status: technically accepted planning decision; runtime behavior unchanged
Date: 2026-09-19
Authority: owner explicitly requested T-0187 and accelerated generalization
Base: main b5fc667; existing ADR-0074, ADR-0075, ADR-0090 and ADR-0101
Evidence class: Planning with retained RTL-functional observations

## Decision and the user-visible target

Select a separately versioned **compiled simulator reuse** implementation as
the next bounded task. No result cache, daemon, scheduler or device access.
Success means the second edited run actually executes the Graph and verifier,
but does not invoke Scala elaboration or Verilator compilation when the full
build identity is unchanged. Do not call this a measured speedup before timing
is preregistered and collected. A build-count reduction is the immediate gate.

The existing two-request batch is useful for commissioning, but is not the
selected interactive optimization: after a successful old run already exists,
both an ordinary new run and a before/after batch still require one build.
The batch additionally repeats old computation. It does not remove the user's
wait on each edit. This corrects the initial read-only review recommendation.

## Evidence and alternatives

`raveil/graph_device_dynamic.py:_run_dynamic` creates private request roots and
always invokes `run-graph-device-axi4lite-dynamic.sh`. The inner runner copies
source, elaborates Scala, compiles Verilator and executes one or two requests.
`run_snapshot` exposes the single-request path to `project run`.

Retained T-0182 sessions `run.uqg__pan` and `run.u601jxd3` have identical
simulator, source/RTL/ABI manifests and all four generated headers, despite
different requests and oracle outputs. The primary rechecked these bytes in
the persistent local copy. These are two builds producing the same binary,
not a cold/warm latency study. No new RTL build was needed for this decision.

| Option | Edit-after-success build work | Benefit | Main cost / reason |
|---|---|---|---|
| Always rebuild | one elaboration and compilation | simplest baseline | repeats unchanged work; retain explicit fallback |
| Existing exact-two batch | still one build per batch | two fresh requests share one build | does not eliminate build on the next interactive edit |
| Verified compiled binary reuse | zero elaborations/compilations on a valid hit | directly removes repeated build work | new local identity/integrity/concurrency boundary; selected bounded successor |
| Long-lived simulator service | potentially no build/process startup | future throughput option | state isolation, cancellation, lifetime and client authority; deferred |

## Required implementation contract

- Key every compiled C++/Chisel/header source, generated-header bytes,
  orchestration scripts, ABI/program/request contracts, pinned Docker image,
  toolchain/build flags/top and dependency-cache identity. Never key only by
  Graph, input, a mutable image tag, old output or simulator hash.
- Recipe/input edits may hit only when compiled inputs are unchanged. Source,
  generated header, contract, tool/dependency or runner changes must miss.
- Keep a private repository-owned cache outside project-controlled recipes.
  Accept only bounded regular files and direct directories; reject symlinks,
  unexpected members, inconsistent sizes/hashes and incomplete entries.
- Publish complete entries atomically without overwriting an accepted entry;
  concurrent writers cannot expose partial builds. Copy a validated bundle
  into each fresh session before execution; validate that private copy again.
- Cache binary and build provenance only. Every invocation independently
  snapshots input, admits the request, runs RTL/C++ fallback, checks all256
  oracle words and writes new request/output/trace/receipt files.
- Retain cold/miss/hit/build-origin information explicitly. A hit must not
  emit the old marker claiming a new elaboration/build happened. Existing
  receipts remain readable; new evidence fields need an explicit version.
- Default to ordinary build on absent/stale entries; unsafe/corrupt entries
  fail closed with actionable diagnosis, not an unverified execution. Preserve
  failed evidence. An explicit fresh-build mode remains available.
- Bound entry count and bytes. When full, build without caching; no automatic
  recursive deletion or unbounded eviction process in the first slice.
- Trust boundary is cooperative local development, not hostile same-user
  isolation, signed provenance or remote binary distribution. Keep Docker
  offline, immutable-image checked and source readonly. Sealed UIO stays out.

## Acceptance and measurement plan

First test key changes, corrupt/missing members, no-follow reads, atomic
publication/races, bounded size/count and cold fallback without Docker. Then
run an actual cold threshold Graph followed by an edited warm Graph: require
one cold build, zero warm builds, fresh execution and exact256-word equality.
Run an old-program compatibility control and source-change invalidation.
Do not add another large measurement framework.

Any later latency claim must preregister clock/source/environment, exact paired
workload, cold versus warm definition, process/build/execution boundaries,
repetitions/order, failures and summary before collecting timing data. The
present task claims only source inspection and identical retained artifacts.

## Delivery sequence: efficiency serves generalization

1. **Immediate: T-0196 compiled-build reuse.** One bounded implementation,
   negative tests and an edit/run demo; no daemon or output reuse. Proposed5SP
   relative risk, not an elapsed-time promise. Accept a visible avoided build.
2. **Next: T-0183 multi-output decision.** Use the existing sensor workload
   needing raw and biased outputs. Compare two current single-output Graphs,
   host composition and a versioned multi-output boundary. Do not expand STORE
   authority merely to make an example pass.
3. **Next: T-0186 standard-IR increment.** One additional owned workload through
   the existing pinned import route, with semantic differential tests. Avoid a
   new general-purpose language or unbounded frontend rewrite.
4. **Later: capacity by workload, following T-0184.** Distinguish expression
   size, retained-register scheduling and spatial tiling. A larger image needs
   halo/assembly/partial-failure rules; an18-op per-cell expression needs a
   different remedy. Prefer compiler/runtime composition before widening RTL.
5. **Long term: backend portability.** Preserve Graph/contract semantics across
   simulator and FPGA reference integration; physical work remains behind the
   existing KV260/owner gates. RISC-V extensions/ASIC require measured benefit
   and matched-resource evidence, not the success of a CLI demonstration.

Alternate an infrastructure increment with a user-program increment. Required
tests/review remain; avoid new dashboards, framework rewrites or measurement
campaigns that do not unblock an actual edit/run experience. No dates are
promised from story points; reassess after the first avoided-build demo.
