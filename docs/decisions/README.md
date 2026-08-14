# Architecture Decision Records

Accepted records are historical authority. Change an accepted conclusion by
adding a later ADR and marking the earlier record Superseded; do not silently
rewrite it.

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](ADR-0001-four-plane-adaptive-harvard.md) | Accepted | Four-plane adaptive Harvard model |
| [ADR-0002](ADR-0002-experience-advises-measurement-governs.md) | Accepted | Experience advises; measurement governs commit |
| [ADR-0003](ADR-0003-risc-v-control-and-daphnis-execution.md) | Accepted | RISC-V control/fallback plus Daphnis Execution Subsystem |
| [ADR-0004](ADR-0004-languages-follow-responsibility.md) | Accepted | Languages follow responsibility |
| [ADR-0005](ADR-0005-append-only-and-bounded-experience.md) | Accepted | Append-only evidence plus bounded online Experience |
| [ADR-0006](ADR-0006-own-contracts-use-upstreams.md) | Accepted | Own contracts; use and progressively replace upstreams |
| [ADR-0007](ADR-0007-two-minimal-executable-seeds.md) | Accepted | Bootstrap Sonatine Microkernel and Experience separately |
| [ADR-0008](ADR-0008-staged-adaptive-council.md) | Proposed | Staged multi-policy Adaptive Council |
| [ADR-0009](ADR-0009-gate1-measurement-and-bundle-boundaries.md) | Accepted | Measured adapters and immutable research bundles |
| [ADR-0010](ADR-0010-least-privilege-powermetrics-helper.md) | Accepted | Least-privilege passwordless powermetrics helper |
| [ADR-0012](ADR-0012-policy-selection-is-pre-registered-evidence.md) | Accepted | Policy selection is pre-registered evidence |
| [ADR-0013](ADR-0013-policy-selection-registers-a-candidate-slate.md) | Accepted | Policy selection registers an equal-budget candidate slate |
| [ADR-0014](ADR-0014-vreji-triages-prior-art-and-ip-risk.md) | Accepted | Vreji triages prior-art similarity and IP risk without legal authority |
| [ADR-0015](ADR-0015-attenuated-leaf-capability-delegation.md) | Accepted | Gate 2 delegates only attenuated, non-recursive leaf capabilities |
| [ADR-0016](ADR-0016-contain-user-faults-and-reject-timer-reentry.md) | Accepted | Contain U-mode faults and reject nested timer dispatch |
| [ADR-0017](ADR-0017-current-task-bound-user-syscalls.md) | Accepted | Persistent U-mode syscalls derive authority from the current task |
| [ADR-0018](ADR-0018-pointer-free-bounded-vfs-seed.md) | Accepted | Bounded pointer-free VFS seed |
| [ADR-0019](ADR-0019-linux-is-a-non-authoritative-driver-host.md) | Accepted | Linux is a non-authoritative driver-development host |
| [ADR-0020](ADR-0020-jobs-are-bounded-non-authoritative-envelopes.md) | Accepted | Jobs and completions are bounded non-authoritative envelopes |
| [ADR-0021](ADR-0021-sonatine-owns-boot-scoped-job-rings.md) | Accepted | Sonatine owns boot-scoped bounded job rings |
| [ADR-0022](ADR-0022-completion-telemetry-is-segregated-cold-evidence.md) | Accepted | Completion telemetry is segregated cold evidence |
| [ADR-0023](ADR-0023-shadow-finalization-publishes-versions-only-after-approval.md) | Accepted | Shadow finalization publishes versions only after approval |
| [ADR-0024](ADR-0024-linux-userspace-mvp-precedes-specialized-authority.md) | Accepted | Linux userspace MVP precedes specialized authority |
| [ADR-0025](ADR-0025-userspace-graph-mvp-keeps-advice-non-authoritative.md) | Accepted | Userspace graph MVP keeps advice non-authoritative |
| [ADR-0026](ADR-0026-failures-stay-canonical-and-actionable-bugs-use-issues.md) | Accepted | Failures stay canonical and actionable bugs use GitHub Issues |
| [ADR-0027](ADR-0027-owned-graph-artifacts-bind-lineage-before-execution.md) | Accepted | Owned graph artifacts bind lineage before execution |
| [ADR-0028](ADR-0028-u-mode-shell-keeps-bounded-scalar-state.md) | Accepted | U-mode command shell keeps bounded scalar state |
| [ADR-0029](ADR-0029-sonatine-graph-transport-is-bounded-emulation.md) | Accepted | Sonatine graph transport is bounded emulation |
| [ADR-0030](ADR-0030-four-plane-writes-require-distinct-capabilities.md) | Accepted | Four-plane writes require distinct capabilities |
| [ADR-0031](ADR-0031-byte-shadows-freeze-before-atomic-publication.md) | Accepted | Byte shadows freeze before atomic publication |
| [ADR-0032](ADR-0032-pinned-mlir-import-stays-behind-owned-lineage.md) | Accepted | Pinned MLIR import stays behind owned lineage |
| [ADR-0033](ADR-0033-sonatine-operator-demo-is-brokered-and-replayable.md) | Accepted | Sonatine operator demo is brokered and replayable |
| [ADR-0034](ADR-0034-native-interactive-session-wraps-the-guarded-graph-loop.md) | Accepted | Native interactive Session wraps the guarded graph loop |
| [ADR-0035](ADR-0035-native-workspace-precedes-platform-sandbox.md) | Accepted | Bounded Native workspace precedes platform-enforced sandboxing |
| [ADR-0036](ADR-0036-command-graphs-compile-a-bounded-shell-subset.md) | Accepted | Command graphs compile a bounded shell subset before general shell compatibility |
| [ADR-0037](ADR-0037-synthetic-showcase-keeps-cache-outside-command-authority.md) | Accepted | Synthetic showcase keeps derived-artifact cache outside command authority |
| [ADR-0038](ADR-0038-rocket-reference-uses-a-locked-git-nix-boundary.md) | Accepted | Rocket reference uses a locked Git/Nix boundary |
| [ADR-0039](ADR-0039-bounded-static-region-is-simulation-only.md) | Accepted | Bounded static Graph region is authorized only for repository-owned RTL simulation |
| [ADR-0040](ADR-0040-boom-reference-is-a-pinned-control-not-a-candidate.md) | Accepted | BOOM is an exact pinned OoO control and its disable-OoO mode is a retained-structure diagnostic |
| [ADR-0041](ADR-0041-functional-semantics-do-not-imply-matched-resources.md) | Accepted | Functional semantic agreement does not imply matched memory or comparison readiness |
| [ADR-0042](ADR-0042-shared-tlram-is-an-unmatched-functional-prototype.md) | Accepted | Shared subsystem TileLink RAM is an unmatched functional prototype, not fixed-latency comparison evidence |
| [ADR-0043](ADR-0043-owned-local-memory-contract-precedes-common-adapters.md) | Accepted | An owned attributed local scratchpad transaction contract precedes common CPU/Graph adapters |
| [ADR-0044](ADR-0044-cpu-translation-adapter-starts-uncached-and-unmatched.md) | Accepted | The first CPU TileLink translation adapter uses an observable uncached path and remains resource-unmatched |
| [ADR-0045](ADR-0045-semantic-attribution-is-commit-aware-and-cpu-owned.md) | Accepted | CPU semantic attribution uses implementation-owned tokens and requires memory completion plus architectural commit |
| [ADR-0046](ADR-0046-controlled-run-matched-comparison-precedes-token-hardening.md) | Accepted | A controlled-run matched comparison precedes general CPU token-lifecycle hardening |
| [ADR-0047](ADR-0047-fixture-owned-input-staging-precedes-repeated-campaign.md) | Accepted | A fixture-owned phase-exclusive input provider precedes repeated measurement |
| [ADR-0048](ADR-0048-t0044-results-require-sealed-durable-evidence.md) | Accepted | T-0044 results require sealed, immutable, download-verified evidence before promotion |
