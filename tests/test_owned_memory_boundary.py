from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "hardware" / "chisel" / "OwnedFixedLatencyScratchpad.scala"
HARNESS = (
    ROOT
    / "hardware"
    / "chisel"
    / "owned_fixed_latency_scratchpad_sim_main.cpp"
)
INNER_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-fixed-latency-scratchpad.sh"
)
HOST_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-fixed-latency-scratchpad-rtl.sh"
)
CPU_OVERLAY = (
    ROOT / "hardware" / "chisel" / "chipyard-overlay" / "RaveilOwnedTLMemory.scala"
)
DCACHE_ORIGIN_TAGGER = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-overlay"
    / "RaveilDCacheOriginTagger.scala"
)
ROCKET_DCACHE_ORIGIN_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-rocket-dcache-origin-hook.patch"
)
BOOM_DCACHE_ORIGIN_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-dcache-origin-hook.patch"
)
BOOM_LOAD_LIFECYCLE_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-load-lifecycle.patch"
)
BOOM_LOAD_LIFECYCLE_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_boom_load_lifecycle.S"
)
BOOM_LOAD_LIFECYCLE_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_boom_load_lifecycle.py"
)
BOOM_LOAD_LIFECYCLE_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-load-lifecycle.sh"
)
BOOM_MISALIGNED_ROLLBACK_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-misaligned-rollback.patch"
)
BOOM_MISALIGNED_ROLLBACK_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_boom_misaligned_rollback.S"
)
BOOM_MISALIGNED_ROLLBACK_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_boom_misaligned_rollback.py"
)
BOOM_MISALIGNED_ROLLBACK_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-misaligned-rollback.sh"
)
BOOM_STORE_AUTHORIZATION_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-store-authorization.patch"
)
BOOM_STORE_AUTHORIZATION_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_boom_store_authorization.S"
)
BOOM_STORE_AUTHORIZATION_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_boom_store_authorization.py"
)
BOOM_STORE_AUTHORIZATION_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-store-authorization.sh"
)
BOOM_STORE_TOKEN_HANDOFF_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-store-token-handoff.patch"
)
TL_TOKEN_METADATA_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-tl-token-metadata.patch"
)
BOOM_STORE_TOKEN_HANDOFF_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_boom_store_token_handoff.py"
)
BOOM_STORE_TOKEN_HANDOFF_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-store-token-handoff.sh"
)
BOOM_POSTREQUEST_REDIRECT_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-boom-postrequest-redirect.patch"
)
BOOM_POSTREQUEST_REDIRECT_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_boom_postrequest_redirect.S"
)
BOOM_POSTREQUEST_REDIRECT_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_boom_postrequest_redirect.py"
)
BOOM_POSTREQUEST_REDIRECT_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-postrequest-redirect.sh"
)
TLXBAR_REQUEST_DEFAULTS_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-tlxbar-request-defaults.patch"
)
CPU_ELABORATION_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-cpu-memory-elaboration.sh"
)
TL_PROTOCOL_HARNESS = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-overlay"
    / "RaveilOwnedTLProtocolHarness.scala"
)
TL_PROTOCOL_DRIVER = (
    ROOT / "hardware" / "chisel" / "owned_tl_protocol_sim_main.cpp"
)
TL_PROTOCOL_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-tl-protocol.sh"
)
TL_CONTRACT_BRIDGE = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-overlay"
    / "RaveilOwnedTLContractBridge.scala"
)
TL_CONTRACT_BRIDGE_DRIVER = (
    ROOT / "hardware" / "chisel" / "owned_tl_contract_bridge_sim_main.cpp"
)
TL_CONTRACT_BRIDGE_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-tl-contract-bridge.sh"
)
ROCKET_LIFECYCLE_OBSERVER = (
    ROOT / "hardware" / "chisel" / "RaveilRocketLifecycleObserver.scala"
)
ROCKET_LIFECYCLE_DRIVER = (
    ROOT / "hardware" / "chisel" / "rocket_lifecycle_observer_sim_main.cpp"
)
ROCKET_LIFECYCLE_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-rocket-lifecycle-observer.sh"
)
ROCKET_LIFECYCLE_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_rocket_lifecycle_observer.py"
)
ROCKET_REQUEST_RETIRE_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-rocket-request-retire-witness.patch"
)
ROCKET_REQUEST_RETIRE_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_rocket_request_retire.S"
)
ROCKET_REQUEST_RETIRE_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_rocket_request_retire.py"
)
ROCKET_REQUEST_RETIRE_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-rocket-request-retire-witness.sh"
)
ROCKET_REDIRECT_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_rocket_redirect_negative.S"
)
ROCKET_REDIRECT_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_rocket_redirect_negative.py"
)
ROCKET_REDIRECT_RUNNER = (
    ROOT
    / "hardware"
    / "chisel"
    / "run-owned-rocket-postrequest-redirect-negative.sh"
)
ROCKET_REDIRECT_FATE_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-rocket-redirect-dcache-fate.patch"
)
ROCKET_REDIRECT_FATE_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_rocket_redirect_dcache_fate.py"
)
ROCKET_REDIRECT_FATE_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-rocket-redirect-dcache-fate.sh"
)
ROCKET_EXCEPTION_PATCH = (
    ROOT
    / "hardware"
    / "chisel"
    / "chipyard-patches"
    / "t-0042-rocket-postrequest-exception.patch"
)
ROCKET_EXCEPTION_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_rocket_postrequest_exception.S"
)
ROCKET_EXCEPTION_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_rocket_postrequest_exception.py"
)
ROCKET_EXCEPTION_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-rocket-postrequest-exception.sh"
)
ROCKET_MEMORY_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_cpu_smoke.S"
)
ROCKET_MEMORY_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_memory_cpu_signature.py"
)
ROCKET_MEMORY_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-rocket-memory-smoke.sh"
)
BOOM_MEMORY_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-memory-smoke.sh"
)
CPU_SOURCE_MAP_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_cpu_source_map.py"
)
CPU_MEMORY_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-cpu-memory-smoke.sh"
)
LOADER_PROBE_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_loader_probe.S"
)
LOADER_PROBE_LINKER = (
    ROOT / "hardware" / "chisel" / "owned_memory_loader_probe.ld"
)
LOADER_PROBE_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_memory_loader_probe.py"
)
SOURCE_NONIDENTITY_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_cpu_source_nonidentity.py"
)
DEBUG_SBA_WORKLOAD = (
    ROOT / "hardware" / "chisel" / "owned_memory_debug_sba_smoke.S"
)
DEBUG_SBA_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_memory_debug_sba_signature.py"
)
DEBUG_SBA_SOURCE_MAP_VERIFIER = (
    ROOT / "hardware" / "chisel" / "verify_owned_debug_sba_source_map.py"
)
ROCKET_DEBUG_SBA_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-rocket-debug-sba-smoke.sh"
)
BOOM_DEBUG_SBA_RUNNER = (
    ROOT / "hardware" / "chisel" / "run-owned-boom-debug-sba-smoke.sh"
)


class OwnedMemoryBoundaryTests(unittest.TestCase):
    def test_contract_is_owned_bounded_and_attributed(self) -> None:
        source = RTL.read_text(encoding="utf-8")
        self.assertIn("class OwnedFixedLatencyScratchpad", source)
        self.assertIn("ResponseAvailabilityLatencyCycles = 1", source)
        self.assertIn("val requestInitiator", source)
        self.assertIn("val requestPhase", source)
        self.assertIn("val acceptedCount", source)
        self.assertIn("val completedCount", source)
        self.assertIn("val pending", source)
        self.assertIn("assert(acceptedCountReg === completedCountReg", source)
        self.assertNotIn("TileLink", source)
        self.assertNotIn("TLRAM", source)

    def test_harness_covers_read_write_backpressure_and_rejection(self) -> None:
        source = HARNESS.read_text(encoding="utf-8")
        self.assertIn("read_covered=1", source)
        self.assertIn("write_covered=1", source)
        self.assertIn("byte_mask_covered=1", source)
        self.assertIn("request_backpressure_covered=1", source)
        self.assertIn("response_backpressure_covered=1", source)
        self.assertIn("range_rejection_covered=1", source)
        self.assertIn("fixed_end_to_end_latency_claim=0", source)
        self.assertIn("resource_match_verified=0", source)
        self.assertIn("performance=not-measured", source)

    def test_runners_are_executable_isolated_and_non_claiming(self) -> None:
        self.assertNotEqual(INNER_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(HOST_RUNNER.stat().st_mode & 0o111, 0)
        inner = INNER_RUNNER.read_text(encoding="utf-8")
        host = HOST_RUNNER.read_text(encoding="utf-8")
        self.assertIn("--assert", inner)
        self.assertIn("--server=false", inner)
        self.assertIn("OwnedFixedLatencyScratchpad.scala", inner)
        self.assertIn("platform=linux/amd64", host)
        self.assertIn("no-new-privileges=true", host)
        self.assertIn("--network none", host)
        self.assertIn("performance=not-measured", host)
        self.assertNotIn("run-tlram-latency-observer.sh", host)

    def test_cpu_overlay_adds_owned_target_without_claiming_execution(self) -> None:
        overlay = CPU_OVERLAY.read_text(encoding="utf-8")
        config_overlay = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        runner = CPU_ELABORATION_RUNNER.read_text(encoding="utf-8")
        self.assertIn("class RaveilOwnedTLMemory", overlay)
        self.assertIn("new testchipip.soc.WithNoScratchpads", config_overlay)
        self.assertIn("TLFragmenter(4, bus.blockBytes)", overlay)
        self.assertIn("TLWidthWidget(bus.beatBytes)", overlay)
        self.assertIn("busWhere: TLBusWrapperLocation = PBUS", overlay)
        self.assertIn("regionType = RegionType.IDEMPOTENT", overlay)
        self.assertIn("mayDenyPut = true", overlay)
        self.assertIn("phaseByteEnabled = tl.a.bits.mask(0)", overlay)
        self.assertIn("responseControlData := controlReadData", overlay)
        self.assertIn("bus.generateSynchronousDomain", overlay)
        self.assertIn("val memory = domain { LazyModule", overlay)
        self.assertIn("RaveilOwnedMemoryPhase", overlay)
        self.assertIn("responseDue = RegNext(tl.a.fire", overlay)
        self.assertNotIn("class TLRAM", overlay)
        self.assertNotEqual(CPU_ELABORATION_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("source=$chipyard,target=/source,readonly", runner)
        self.assertIn("source=$overlay,target=/overlay", runner)
        self.assertIn("RaveilDCacheOriginTagger.scala", runner)
        self.assertIn("git -C generators/rocket-chip apply --check", runner)
        self.assertIn("git -C generators/boom apply --check", runner)
        self.assertIn("RaveilDCacheOriginTagger", runner)
        self.assertIn("OWNED-CPU-MEMORY-ELABORATION-V2", runner)
        self.assertIn("dcache_origin_path=structurally-elaborated", runner)
        self.assertIn("execution=not-run", runner)
        self.assertIn("bus=pbus-uncached", runner)
        self.assertIn("initiator_attribution=unverified", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("matched_comparison_ready=0", runner)
        self.assertIn("performance=not-measured", runner)

    def test_owned_tl_protocol_runner_is_bounded_and_non_claiming(self) -> None:
        harness = TL_PROTOCOL_HARNESS.read_text(encoding="utf-8")
        driver = TL_PROTOCOL_DRIVER.read_text(encoding="utf-8")
        runner = TL_PROTOCOL_RUNNER.read_text(encoding="utf-8")
        self.assertIn("class RaveilOwnedTLProtocolHarness", harness)
        self.assertIn("sourceId = IdRange(0, 4)", harness)
        self.assertIn("expectedClientSourceStart = 1", harness)
        self.assertIn("expectedClientSourceEnd = 3", harness)
        self.assertIn("memory.node := client.node", harness)
        self.assertIn("response_backpressure=covered", driver)
        self.assertIn("max_one_outstanding=covered", driver)
        self.assertIn("byte_masks=0x5,0xa", driver)
        self.assertIn("invalid_phase_denial=covered", driver)
        self.assertIn("response_metadata=param,size,source,sink,denied,corrupt", driver)
        self.assertIn("expected-source accepted counter mismatch", driver)
        self.assertIn("unexpected-source completed counter mismatch", driver)
        self.assertIn("last completed phase mismatch", driver)
        self.assertIn("same_source_reuse_blocking=covered", driver)
        self.assertIn("unexpected_boundary_sources=0,3", driver)
        self.assertIn("expected_source_accepted=3", driver)
        self.assertIn("unexpected_source_accepted=4", driver)
        self.assertIn("OWNED-TL-PROTOCOL-V4", driver)
        self.assertIn("OWNED-TL-ORIGIN-STRIP-V1", driver)
        self.assertIn("RAVEIL_ORIGIN_STRIP_HARNESS", driver)
        self.assertIn("dcache_origin_accepted=0", driver)
        self.assertIn("non_dcache_origin_accepted=7", driver)
        self.assertIn("upstream_origin=true downstream_origin=absent", driver)
        self.assertIn("metadata_loss=fail-closed", driver)
        self.assertIn("model=test-only-not-loader-debug", driver)
        self.assertNotEqual(TL_PROTOCOL_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("--assert --cc", runner)
        self.assertIn("assembly_cache=content-addressed-verified", runner)
        self.assertIn("sha256sum -c", runner)
        self.assertIn('shasum -a 256 "$runner" "$memory_overlay"', runner)
        self.assertIn("--provenance=false", runner)
        self.assertIn("docker image inspect", runner)
        self.assertIn("cpu_execution=not-run", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)

    def test_tl_to_owned_contract_bridge_is_bounded_and_non_claiming(self) -> None:
        bridge = TL_CONTRACT_BRIDGE.read_text(encoding="utf-8")
        driver = TL_CONTRACT_BRIDGE_DRIVER.read_text(encoding="utf-8")
        runner = TL_CONTRACT_BRIDGE_RUNNER.read_text(encoding="utf-8")
        self.assertIn("class RaveilOwnedTLContractBridge", bridge)
        self.assertIn("class RaveilOwnedContractScratchpad", bridge)
        self.assertIn("val ownedRequest = IO(Decoupled", bridge)
        self.assertIn("val ownedResponse = IO(Flipped(Decoupled", bridge)
        self.assertIn("ownedRequest.bits.initiator := requestInitiator", bridge)
        self.assertIn("ownedRequest.bits.phase := requestPhase", bridge)
        self.assertIn("responseSource := tl.a.bits.source", bridge)
        self.assertIn("responseSize := tl.a.bits.size", bridge)
        self.assertIn("val addressInRange = tl.a.bits.address", bridge)
        self.assertIn("val supported = addressInRange && (get || put)", bridge)
        self.assertIn("assert(acceptedCount === completedCount + busy.asUInt)", bridge)
        self.assertIn("assert(ownedResponse.bits.initiator === responseInitiator)", bridge)
        self.assertIn("assert(ownedResponse.bits.phase === responsePhase)", bridge)
        self.assertIn("OWNED-TL-CONTRACT-BRIDGE-V1", driver)
        self.assertIn("owned_accepted=6 owned_completed=6", driver)
        self.assertIn("single_outstanding_request_blocking=covered", driver)
        self.assertIn("attribution=adapter-input-only", driver)
        self.assertNotEqual(TL_CONTRACT_BRIDGE_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("source=$chipyard,target=/source,readonly", runner)
        self.assertIn("no-new-privileges=true", runner)
        self.assertIn("assembly_cache=content-addressed-verified", runner)
        self.assertIn("sha256sum -c", runner)
        self.assertIn('shasum -a 256 "$runner" "$bridge_overlay"', runner)
        self.assertIn("semantic_initiator=not-proven", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)

    def test_rocket_lifecycle_observer_is_synthetic_and_fail_closed(self) -> None:
        observer = ROCKET_LIFECYCLE_OBSERVER.read_text(encoding="utf-8")
        driver = ROCKET_LIFECYCLE_DRIVER.read_text(encoding="utf-8")
        runner = ROCKET_LIFECYCLE_RUNNER.read_text(encoding="utf-8")
        verifier = ROCKET_LIFECYCLE_VERIFIER.read_text(encoding="utf-8")
        self.assertIn("class RaveilRocketLifecycleObserver", observer)
        self.assertIn("eventMatchesActive", observer)
        self.assertIn("sequenceExhausted", observer)
        self.assertIn("epochExhausted", observer)
        self.assertIn("PostTerminalSideEffect", observer)
        self.assertIn("activeDCompleted || validDCompletion", observer)
        self.assertIn("activeRetired || validRetirement", observer)
        self.assertIn("activeStoreAuthorized || validStoreAuthorization", observer)
        self.assertIn("commitEligibleEvent", observer)
        self.assertIn("allocatedCount === committedLoadCount", observer)
        self.assertIn("ROCKET-LIFECYCLE-OBSERVER-V1", driver)
        self.assertIn("load_positive=covered", driver)
        self.assertIn("store_positive=covered", driver)
        self.assertIn("post_a_exception=covered", driver)
        self.assertIn("reset_outstanding=covered", driver)
        self.assertIn("stale_epoch=covered", driver)
        self.assertIn("stripped_metadata=covered", driver)
        self.assertIn("duplicate_token=covered", driver)
        self.assertIn("invalid_completion=covered", driver)
        self.assertIn("sequence_exhaustion=covered", driver)
        self.assertIn("event_source=synthetic", driver)
        self.assertIn("cpu_execution=not-run", driver)
        self.assertIn("semantic_initiator=not-proven", driver)
        self.assertNotEqual(ROCKET_LIFECYCLE_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("--network none", runner)
        self.assertIn("--assert --cc", runner)
        self.assertIn("--provenance=false", runner)
        self.assertIn(
            'shasum -a 256 "$rtl" "$driver" "$verifier" "$runner"', runner
        )
        self.assertIn('python3 "$verifier" "$observer_log"', runner)
        self.assertIn('"semantic_initiator": "not-proven"', verifier)
        self.assertIn("terminal outcome conservation mismatch", verifier)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)

    def test_rocket_lifecycle_marker_rejects_mutation_and_duplicates(self) -> None:
        marker = (
            "ROCKET-LIFECYCLE-OBSERVER-V1 status=OK allocated=21 "
            "committed_load=3 committed_store=1 noncommitted=17 "
            "core_attempts=8 core_replays=1 dcache_retries=1 a_accepted=7 "
            "d_completed=7 retired=5 store_authorized=1 unknown=2 violations=8 "
            "load_positive=covered store_positive=covered pre_a_kill=covered "
            "post_a_exception=covered reset_outstanding=covered stale_epoch=covered "
            "stripped_metadata=covered duplicate_token=covered "
            "duplicate_outcome=covered invalid_completion=covered "
            "untagged_event=covered d_error=covered "
            "sequence_exhaustion=covered event_source=synthetic "
            "cpu_execution=not-run semantic_initiator=not-proven "
            "resource_match_verified=0 matched_comparison_ready=0 "
            "evidence=rtl-simulation-functional performance=not-measured\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "observer.log"
            log.write_text(marker, encoding="utf-8")
            accepted = subprocess.run(
                ["python3", str(ROCKET_LIFECYCLE_VERIFIER), str(log)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertIn("schema=exact", accepted.stdout)

            for mutation in (
                marker.replace("stale_epoch=covered ", ""),
                marker.replace("violations=8", "violations=7"),
                marker + marker,
            ):
                log.write_text(mutation, encoding="utf-8")
                rejected = subprocess.run(
                    ["python3", str(ROCKET_LIFECYCLE_VERIFIER), str(log)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(rejected.returncode, 0)

    def test_rocket_request_retire_witness_is_pinned_and_non_claiming(self) -> None:
        patch = ROCKET_REQUEST_RETIRE_PATCH.read_text(encoding="utf-8")
        workload = ROCKET_REQUEST_RETIRE_WORKLOAD.read_text(encoding="utf-8")
        verifier = ROCKET_REQUEST_RETIRE_VERIFIER.read_text(encoding="utf-8")
        runner = ROCKET_REQUEST_RETIRE_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("io.dmem.req.bits.addr === raveilWitnessAddress", patch)
        self.assertIn("raveilWitnessRequest", patch)
        self.assertIn("when(raveilWitnessRequest && !raveilWitnessActive)", patch)
        self.assertNotIn("when(raveilWitnessCandidate && !raveilWitnessActive)", patch)
        self.assertIn("wb_valid && wb_ctrl.mem", patch)
        self.assertIn("isWrite(wb_ctrl.mem_cmd)", patch)
        self.assertIn("io.dmem.resp.bits.tag === raveilWitnessTag", patch)
        self.assertIn("event=response", patch)
        self.assertNotIn("assert(dmem_resp_valid", patch)
        self.assertIn("not carry the token through DCache/TL", patch)
        self.assertIn("li      s0, 0x08000100", workload)
        self.assertIn("sw      t0, 0(s0)", workload)
        self.assertIn("lw      t1, 0(s0)", workload)
        self.assertLess(workload.index("sw      t0, 0(s0)"), workload.index("lw      t1, 0(s0)"))
        self.assertLess(workload.index("lw      t1, 0(s0)"), workload.index("sw      t1, 4(s1)"))
        self.assertLess(workload.index("sw      t1, 4(s1)"), workload.index("bne     t0, t1, fail"))
        self.assertEqual(workload.count("sw      t1, 4(s1)"), 1)
        self.assertIn("dcache_response_tag_match=covered", verifier)
        self.assertIn("d_token_correlation=not-run", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertNotEqual(ROCKET_REQUEST_RETIRE_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=rocket-request-retire", runner)
        self.assertIn("t-0042-rocket-request-retire-witness.patch", shared_runner)
        self.assertIn("0435dce882f4ad37", shared_runner)
        self.assertIn("29a1032a10aeb744", shared_runner)
        self.assertIn("timeout --foreground 180", shared_runner)
        self.assertIn('2>&1 | tee "$witness_log"', shared_runner)
        self.assertIn("cache initialization raced another invocation", shared_runner)
        self.assertIn("performance=not-measured", shared_runner)

    def test_rocket_request_retire_verifier_rejects_event_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    1 pc=0x8000000c address=0x08000100 store=1 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    1 attempt=1 pc=0x8000000c address=0x08000100 store=1 tag=0x0a",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    1 pc=0x8000000c store=1 wb_valid=1 store_wb_predicate=1",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    2 pc=0x80000014 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    2 attempt=1 pc=0x80000014 address=0x08000100 store=0 tag=0x0c",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    2 pc=0x80000014 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    2 tag=0x0c store=0 response_valid=1 response_has_data=1",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "witness.log"
            signature = Path(tmp) / "witness.signature"
            signature.write_text("00000001\n4b1d2e3f\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("response_has_data=1", "response_has_data=0"), 1),
                (records.replace("tag=0x0c store=0 response", "tag=0x0d store=0 response"), 1),
                (records.replace("store_wb_predicate=1", "store_wb_predicate=0"), 1),
                (records.replace("sequence=    2", "sequence=    1"), 1),
                (records + records.splitlines()[0] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(ROCKET_REQUEST_RETIRE_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_rocket_postrequest_redirect_probe_is_bounded_and_non_claiming(self) -> None:
        patch = ROCKET_REQUEST_RETIRE_PATCH.read_text(encoding="utf-8")
        workload = ROCKET_REDIRECT_WORKLOAD.read_text(encoding="utf-8")
        verifier = ROCKET_REDIRECT_VERIFIER.read_text(encoding="utf-8")
        runner = ROCKET_REDIRECT_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("when(take_pc_mem)", patch)
        self.assertIn("event=kill", patch)
        self.assertIn("direction_misprediction=%d", patch)
        self.assertIn("promotion=blocked", patch)
        self.assertLess(workload.index("lw      s2, 0(s0)"), workload.index("beq     t2, t2"))
        self.assertIn("xor     t3, s2, s2", workload)
        self.assertLess(workload.index("beq     t2, t2"), workload.index("sw      t0, 0(s0)"))
        self.assertLess(workload.index("sw      t0, 0(s0)"), workload.index("lw      t1, 0(s0)"))
        self.assertIn("bne     t1, s2, fail", workload)
        self.assertIn(".fill 3, 4, 0", workload)
        self.assertIn("before_value == MAGIC", verifier)
        self.assertIn("before_value != after_value", verifier)
        self.assertIn("wrong_path_core_requests=1", verifier)
        self.assertIn("wrong_path_retirements=0", verifier)
        self.assertIn("before_after_equal=1", verifier)
        self.assertIn("pre_request_kill=not-run", verifier)
        self.assertIn("dcache_s1_kill_correlation=not-run", verifier)
        self.assertIn("a_d_correlation=not-run", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertNotEqual(ROCKET_REDIRECT_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=rocket-postrequest-redirect", runner)
        self.assertIn("rocket-postrequest-redirect:RaveilOwnedRocketConfig", shared_runner)
        self.assertIn(
            '"$rocket_witness_patch" "$rocket_fate_patch" "$rocket_exception_patch" "$boom_hook_patch"',
            shared_runner,
        )
        self.assertIn("29a1032a10aeb744", shared_runner)
        self.assertIn("source_sha256=%s", shared_runner)

    def test_rocket_redirect_verifier_rejects_lifecycle_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    1 pc=0x80000008 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    1 attempt=1 pc=0x80000008 address=0x08000100 store=0 tag=0x12",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    1 pc=0x80000008 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    1 tag=0x12 store=0 response_valid=1 response_has_data=1",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    2 pc=0x80000020 address=0x08000100 store=1 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    2 attempt=1 pc=0x80000020 address=0x08000100 store=1 tag=0x00",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=kill epoch= 1 sequence=    2 branch_pc=0x8000001c pc=0x80000020 store=1 reason=mem-redirect request_accepted=1 branch=1 taken=1 direction_misprediction=1 promotion=blocked",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    3 pc=0x80000024 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    3 attempt=1 pc=0x80000024 address=0x08000100 store=0 tag=0x0c",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    3 pc=0x80000024 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    3 tag=0x0c store=0 response_valid=1 response_has_data=1",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "redirect.log"
            signature = Path(tmp) / "redirect.signature"
            signature.write_text("00000001\nc5686cac\nc5686cac\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("request_accepted=1", "request_accepted=0"), 1),
                (records.replace("direction_misprediction=1", "direction_misprediction=0"), 1),
                (records.replace("promotion=blocked", "promotion=allowed"), 1),
                (records.replace("tag=0x0c store=0 response", "tag=0x0d store=0 response"), 1),
                (records.replace("tag=0x12 store=0 response", "tag=0x13 store=0 response"), 1),
                (records + records.splitlines()[6] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(ROCKET_REDIRECT_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_rocket_redirect_dcache_fate_probe_is_direct_and_non_claiming(self) -> None:
        overlay = CPU_OVERLAY.read_text(encoding="utf-8")
        origin = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        patch = ROCKET_REDIRECT_FATE_PATCH.read_text(encoding="utf-8")
        verifier = ROCKET_REDIRECT_FATE_VERIFIER.read_text(encoding="utf-8")
        runner = ROCKET_REDIRECT_FATE_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("fateAuditAddress: Option[BigInt] = None", overlay)
        self.assertIn("RAVEIL-OWNED-TL-FATE-V1 event=a", overlay)
        self.assertIn("RAVEIL-OWNED-TL-FATE-V1 event=d", overlay)
        self.assertIn("class RaveilOwnedRocketFateConfig", origin)
        self.assertIn("WithRaveilOwnedMemorySourceRangeAndFateAudit(8224, 8256, 0x08000100L)", origin)
        self.assertIn("RegNext(raveilRedirectAccepted, false.B)", patch)
        self.assertIn("io.dmem.s1_kill", patch)
        self.assertIn("RAVEIL-ROCKET-DCACHE-FATE-V1 event=s1", patch)
        self.assertIn("dcache_s1_kill=observed", verifier)
        self.assertIn("wrong_path_store_tl_a=not-observed", verifier)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=rocket-redirect-dcache-fate", runner)
        self.assertIn("rocket-redirect-dcache-fate:RaveilOwnedRocketFateConfig", shared_runner)
        self.assertIn("de13ae897d3df31d", shared_runner)
        self.assertLess(
            shared_runner.index("verify_owned_rocket_redirect_negative.py", shared_runner.index("rocket-redirect-dcache-fate ]; then")),
            shared_runner.index("verify_owned_rocket_redirect_dcache_fate.py", shared_runner.index("rocket-redirect-dcache-fate ]; then")),
        )
        self.assertNotEqual(ROCKET_REDIRECT_FATE_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(ROCKET_REDIRECT_FATE_VERIFIER.stat().st_mode & 0o111, 0)

    def test_rocket_redirect_dcache_fate_verifier_rejects_transport_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    1 pc=0x80000008 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    1 attempt=1 pc=0x80000008 address=0x08000100 store=0 tag=0x24",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    1 pc=0x80000008 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    1 tag=0x24 store=0 response_valid=1 response_has_data=1",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    2 pc=0x80000024 address=0x08000100 store=1 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    2 attempt=1 pc=0x80000024 address=0x08000100 store=1 tag=0x00",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=kill epoch= 1 sequence=    2 branch_pc=0x80000020 pc=0x80000024 store=1 reason=mem-redirect request_accepted=1 branch=1 taken=1 direction_misprediction=1 promotion=blocked",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    3 pc=0x80000028 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    3 attempt=1 pc=0x80000028 address=0x08000100 store=0 tag=0x0c",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    3 pc=0x80000028 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    3 tag=0x0c store=0 response_valid=1 response_has_data=1",
                "RAVEIL-ROCKET-DCACHE-FATE-V1 event=s1 epoch= 1 sequence=    2 pc=0x80000024 address=0x08000100 store=1 tag=0x00 s1_kill=1 s2_kill=0 correlation=accepted-request-next-cycle",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=    1 address=0x08000100 source= 8224 opcode= 4 size= 2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=    1 source= 8224 opcode= 1 size= 2 denied=0 corrupt=0 request_opcode= 4 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=    2 address=0x08000100 source= 8224 opcode= 4 size= 2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=    2 source= 8224 opcode= 1 size= 2 denied=0 corrupt=0 request_opcode= 4 phase=0",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "fate.log"
            signature = Path(tmp) / "fate.signature"
            signature.write_text("00000001\nc5686cac\nc5686cac\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("s1_kill=1", "s1_kill=0"), 1),
                (records.replace("tag=0x00 s1_kill", "tag=0x01 s1_kill"), 1),
                (records + records.splitlines()[0] + "\n", 1),
                (records.replace("source= 8224", "source= 9000", 1), 1),
                (records.replace("opcode= 4", "opcode= 0", 1), 1),
                (records.replace("denied=0", "denied=1", 1), 1),
                (records.rsplit("\n", 2)[0] + "\n", 1),
                (records + records.splitlines()[-1] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(ROCKET_REDIRECT_FATE_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_rocket_postrequest_exception_probe_is_bounded_and_non_claiming(self) -> None:
        patch = ROCKET_EXCEPTION_PATCH.read_text(encoding="utf-8")
        workload = ROCKET_EXCEPTION_WORKLOAD.read_text(encoding="utf-8")
        verifier = ROCKET_EXCEPTION_VERIFIER.read_text(encoding="utf-8")
        runner = ROCKET_EXCEPTION_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("io.dmem.req.fire", patch)
        self.assertIn('val raveilExceptionAddress = "h08000101"', patch)
        self.assertIn("wb_xcpt &&", patch)
        self.assertIn("wb_cause === Causes.misaligned_load.U", patch)
        self.assertIn("io.dmem.s2_xcpt.ma.ld", patch)
        self.assertIn("promotion=blocked", patch)
        self.assertIn("not carried through DCache/TL", patch)
        self.assertIn("lw      t1, 1(s0)", workload)
        self.assertIn("csrr    t0, mcause", workload)
        self.assertIn("csrr    t1, mtval", workload)
        self.assertIn("csrr    t3, mepc", workload)
        self.assertIn("post_tl_a_exception=not-run", verifier)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("general_rollback=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=rocket-postrequest-exception", runner)
        self.assertIn("rocket-postrequest-exception:RaveilOwnedRocketConfig", shared_runner)
        self.assertIn("f3015d47932074f7", shared_runner)
        self.assertNotEqual(ROCKET_EXCEPTION_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(ROCKET_EXCEPTION_VERIFIER.stat().st_mode & 0o111, 0)

    def test_rocket_postrequest_exception_verifier_rejects_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    1 pc=0x80000018 address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    1 attempt=1 pc=0x80000018 address=0x08000100 store=0 tag=0x24",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    1 attempt=2 pc=0x80000018 address=0x08000100 store=0 tag=0x24",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    1 pc=0x80000018 store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    1 tag=0x24 store=0 response_valid=1 response_has_data=1",
                "RAVEIL-ROCKET-POSTREQUEST-EXCEPTION-V1 event=request epoch=1 sequence=1 attempt=1 pc=0x80000024 address=0x08000101 store=0 tag=0x0c request_accepted=1 event_source=rocket-pinned",
                "RAVEIL-ROCKET-POSTREQUEST-EXCEPTION-V1 event=exception epoch=1 sequence=1 pc=0x80000024 address=0x08000101 store=0 tag=0x0c cause=4 ma_ld=1 ma_st=0 take_pc_wb=1 promotion=blocked",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=allocate epoch= 1 sequence=    2 pc=0x8000002c address=0x08000100 store=0 event_source=rocket-pinned",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    2 attempt=1 pc=0x8000002c address=0x08000100 store=0 tag=0x26",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=request epoch= 1 sequence=    2 attempt=2 pc=0x8000002c address=0x08000100 store=0 tag=0x26",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=retire epoch= 1 sequence=    2 pc=0x8000002c store=0 wb_valid=1 store_wb_predicate=0",
                "RAVEIL-ROCKET-REQUEST-RETIRE-V1 event=response epoch= 1 sequence=    2 tag=0x26 store=0 response_valid=1 response_has_data=1",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "exception.log"
            signature = Path(tmp) / "exception.signature"
            signature.write_text(
                "00000001\n682513da\n682513da\n00000004\n08000101\n00000001\n",
                encoding="ascii",
            )
            for text, expected_returncode in (
                (records, 0),
                (records.replace("request_accepted=1", "request_accepted=0"), 1),
                (records.replace("cause=4", "cause=5"), 1),
                (records.replace("ma_ld=1", "ma_ld=0"), 1),
                (records.replace("take_pc_wb=1", "take_pc_wb=0"), 1),
                (records.replace("promotion=blocked", "promotion=allowed"), 1),
                (records.replace("tag=0x0c cause", "tag=0x0d cause"), 1),
                (records.replace("store_wb_predicate=0", "store_wb_predicate=1", 1), 1),
                (records.replace("response_has_data=1", "response_has_data=0", 1), 1),
                (records + records.splitlines()[5] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(ROCKET_EXCEPTION_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_boom_load_lifecycle_probe_is_bounded_and_non_claiming(self) -> None:
        patch = BOOM_LOAD_LIFECYCLE_PATCH.read_text(encoding="utf-8")
        workload = BOOM_LOAD_LIFECYCLE_WORKLOAD.read_text(encoding="utf-8")
        verifier = BOOM_LOAD_LIFECYCLE_VERIFIER.read_text(encoding="utf-8")
        runner = BOOM_LOAD_LIFECYCLE_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("io.dmem.req.fire", patch)
        self.assertIn('val raveilBoomAuditAddress = "h08000100"', patch)
        self.assertIn("io.dmem.resp(w).valid", patch)
        self.assertIn("io.core.commit.arch_valids(w)", patch)
        self.assertIn("repository sequence is the identity", patch)
        self.assertIn("not carried through DCache or TileLink", patch)
        self.assertIn("lwu     t0, 0(s0)", workload)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("store_authorization=not-run", verifier)
        self.assertIn("general_boom_lifecycle=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=boom-load-lifecycle", runner)
        self.assertIn("boom-load-lifecycle:RaveilOwnedSmallBoomConfig", shared_runner)
        self.assertIn("d96fa9f10ddc07c5", shared_runner)
        self.assertNotEqual(BOOM_LOAD_LIFECYCLE_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(BOOM_LOAD_LIFECYCLE_VERIFIER.stat().st_mode & 0o111, 0)

    def test_boom_load_lifecycle_verifier_rejects_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-BOOM-LOAD-LIFECYCLE-V1 event=request epoch=1 sequence=1 pc=0x80000008 address=0x08000100 rob_idx=6 ldq_idx=1 br_mask=0x0 lane=0 request_accepted=1 event_source=boom-pinned",
                "RAVEIL-BOOM-LOAD-LIFECYCLE-V1 event=response epoch=1 sequence=1 pc=0x80000008 address=0x08000100 rob_idx=6 ldq_idx=1 br_mask=0x0 lane=0 response_valid=1 data=0x682513da",
                "RAVEIL-BOOM-LOAD-LIFECYCLE-V1 event=retire epoch=1 sequence=1 pc=0x80000008 address=0x08000100 rob_idx=6 ldq_idx=1 br_mask=0x0 lane=0 commit_valid=1 arch_valid=1 promotion=eligible",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "boom-lifecycle.log"
            signature = Path(tmp) / "boom-lifecycle.signature"
            signature.write_text("00000001\n682513da\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("request_accepted=1", "request_accepted=0"), 1),
                (records.replace("response_valid=1", "response_valid=0"), 1),
                (records.replace("arch_valid=1", "arch_valid=0"), 1),
                (records.replace("promotion=eligible", "promotion=blocked"), 1),
                (records.replace("rob_idx=6", "rob_idx=7", 1), 1),
                (records.replace("ldq_idx=1", "ldq_idx=2", 1), 1),
                (records.replace("pc=0x80000008", "pc=0x8000000c", 1), 1),
                (records.replace("br_mask=0x0", "br_mask=0x1", 1), 1),
                (records.replace("lane=0", "lane=1", 1), 1),
                (records + records.splitlines()[1] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(BOOM_LOAD_LIFECYCLE_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_boom_misaligned_rollback_probe_is_bounded_and_non_claiming(self) -> None:
        patch = BOOM_MISALIGNED_ROLLBACK_PATCH.read_text(encoding="utf-8")
        workload = BOOM_MISALIGNED_ROLLBACK_WORKLOAD.read_text(encoding="utf-8")
        verifier = BOOM_MISALIGNED_ROLLBACK_VERIFIER.read_text(encoding="utf-8")
        runner = BOOM_MISALIGNED_ROLLBACK_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("val raveilBoomNegativeAddress", patch)
        self.assertIn("ma_ld(w)", patch)
        self.assertIn("mem_xcpt_valids(w)", patch)
        self.assertIn("io.core.commit.rollback", patch)
        self.assertIn("io.core.commit.arch_valids", patch)
        self.assertIn("repository sequence is allocated", patch)
        self.assertIn("not carried through DCache or TileLink", patch)
        self.assertIn("lw      t1, 1(s0)", workload)
        self.assertIn("csrr    t0, mcause", workload)
        self.assertIn("csrr    t1, mtval", workload)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("post_exception_request=observed", verifier)
        self.assertIn("postrequest_exception=not-covered", verifier)
        self.assertIn("rob_rollback_state=observed", verifier)
        self.assertIn("rob_rollback_state_events=1", verifier)
        self.assertNotIn("rob_rollbacks=1", verifier)
        self.assertIn("general_rollback=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=boom-misaligned-rollback", runner)
        self.assertIn(
            "boom-misaligned-rollback:RaveilOwnedSmallBoomConfig", shared_runner
        )
        self.assertIn(
            "request_boundary=after-exception-before-rollback", shared_runner
        )
        self.assertIn("matching_rbk=0", shared_runner)
        self.assertIn("1a12fdf33d797d2a", shared_runner)
        self.assertNotEqual(BOOM_MISALIGNED_ROLLBACK_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(BOOM_MISALIGNED_ROLLBACK_VERIFIER.stat().st_mode & 0o111, 0)

    def test_boom_misaligned_rollback_verifier_rejects_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-BOOM-MISALIGNED-ROLLBACK-V1 event=candidate epoch=1 sequence=1 pc=0x80000024 address=0x08000101 rob_idx=9 ldq_idx=2 br_mask=0x0 lane=0 cause=4 ma_ld=1 request_accepted=0 event_source=boom-pinned",
                "RAVEIL-BOOM-MISALIGNED-ROLLBACK-V1 event=exception epoch=1 sequence=1 pc=0x80000024 address=0x08000101 rob_idx=9 ldq_idx=2 br_mask=0x0 lane=0 cause=4 mem_xcpt_valid=1 promotion=blocked",
                "RAVEIL-BOOM-MISALIGNED-ROLLBACK-V1 event=request epoch=1 sequence=1 pc=0x80000024 address=0x08000101 rob_idx=9 ldq_idx=2 br_mask=0x0 lane=0 request_accepted=1 after_exception=1",
                "RAVEIL-BOOM-MISALIGNED-ROLLBACK-V1 event=rollback epoch=1 sequence=1 pc=0x80000024 address=0x08000101 rob_idx=9 ldq_idx=2 br_mask=0x0 lane=0 rollback=1 matching_rbk=0 request_accepted=1 request_count=1 response_seen=0 core_exception_seen=1 commit_valid=0 arch_valid=0 promotion=blocked",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "boom-negative.log"
            signature = Path(tmp) / "boom-negative.signature"
            signature.write_text(
                "00000001\n682513da\n682513da\n00000004\n08000101\n00000001\n",
                encoding="ascii",
            )
            for text, expected_returncode in (
                (records, 0),
                (records.replace("cause=4", "cause=5", 1), 1),
                (records.replace("ma_ld=1", "ma_ld=0"), 1),
                (records.replace("mem_xcpt_valid=1", "mem_xcpt_valid=0"), 1),
                (records.replace("after_exception=1", "after_exception=0"), 1),
                (records.replace("rollback=1", "rollback=0"), 1),
                (records.replace("matching_rbk=0", "matching_rbk=1"), 1),
                (records.replace("request_accepted=0", "request_accepted=1", 1), 1),
                (records.replace("request_accepted=1", "request_accepted=0", 1), 1),
                (records.replace("request_count=1", "request_count=0"), 1),
                (records.replace("response_seen=0", "response_seen=1"), 1),
                (records.replace("core_exception_seen=1", "core_exception_seen=0"), 1),
                (records.replace("commit_valid=0", "commit_valid=1"), 1),
                (records.replace("arch_valid=0", "arch_valid=1"), 1),
                (records.replace("promotion=blocked", "promotion=allowed", 1), 1),
                (records.replace("rob_idx=9", "rob_idx=10", 1), 1),
                (records.replace("ldq_idx=2", "ldq_idx=3", 1), 1),
                (records.replace("pc=0x80000024", "pc=0x80000028", 1), 1),
                (records.replace("br_mask=0x0", "br_mask=0x1", 1), 1),
                (records.replace("lane=0", "lane=1", 1), 1),
                (records + records.splitlines()[1] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(BOOM_MISALIGNED_ROLLBACK_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_boom_store_authorization_is_bounded_and_non_claiming(self) -> None:
        patch = BOOM_STORE_AUTHORIZATION_PATCH.read_text(encoding="utf-8")
        workload = BOOM_STORE_AUTHORIZATION_WORKLOAD.read_text(encoding="utf-8")
        verifier = BOOM_STORE_AUTHORIZATION_VERIFIER.read_text(encoding="utf-8")
        runner = BOOM_STORE_AUTHORIZATION_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        origin = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        self.assertIn("io.core.commit.arch_valids(w)", patch)
        self.assertIn("stq(idx).bits.committed := true.B", patch)
        self.assertIn("stq(idx).valid && stq(idx).bits.addr.valid", patch)
        self.assertIn("dmem_req_fire(w)", patch)
        self.assertIn("io.dmem.resp(w).bits.uop.uses_stq", patch)
        self.assertIn("when (clear_store)", patch)
        self.assertIn("repository sequence is the identity", patch)
        self.assertIn("not carried through DCache or TileLink", patch)
        self.assertIn("sw      t0, 0(s0)", workload)
        self.assertIn("lwu     t1, 0(s0)", workload)
        self.assertIn("boom_local_request_response_clear=observed", verifier)
        self.assertIn("manager_put_a_d=independently-observed", verifier)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("store_attribution=not-proven", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("class RaveilOwnedSmallBoomFateConfig", origin)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=boom-store-authorization", runner)
        self.assertIn(
            "boom-store-authorization:RaveilOwnedSmallBoomFateConfig",
            shared_runner,
        )
        self.assertIn("beaf195dfed44573", shared_runner)
        self.assertNotEqual(BOOM_STORE_AUTHORIZATION_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(BOOM_STORE_AUTHORIZATION_VERIFIER.stat().st_mode & 0o111, 0)

    def test_boom_store_authorization_verifier_rejects_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-BOOM-STORE-AUTH-V1 event=authorize epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 commit_valid=1 arch_valid=1 committed_write=1 event_source=boom-pinned",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=request epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 request_accepted=1 store=1",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=response epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 response_valid=1 uses_stq=1 succeeded_write=1",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=clear epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 request_seen=1 response_seen=1 stq_succeeded=1 promotion=eligible-local",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=1 address=0x08000100 source=8304 opcode=0 size=2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=1 source=8304 opcode=0 size=2 denied=0 corrupt=0 request_opcode=0 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=2 address=0x08000100 source=8288 opcode=4 size=2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=2 source=8288 opcode=1 size=2 denied=0 corrupt=0 request_opcode=4 phase=0",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "boom-store.log"
            signature = Path(tmp) / "boom-store.signature"
            signature.write_text("00000001\n51a7c0de\n51a7c0de\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("arch_valid=1", "arch_valid=0"), 1),
                (records.replace("committed_write=1", "committed_write=0"), 1),
                (records.replace("request_accepted=1", "request_accepted=0"), 1),
                (records.replace("response_valid=1", "response_valid=0"), 1),
                (records.replace("stq_succeeded=1", "stq_succeeded=0"), 1),
                (records.replace("promotion=eligible-local", "promotion=blocked"), 1),
                (records.replace("rob_idx=7", "rob_idx=8", 1), 1),
                (records.replace("stq_idx=1", "stq_idx=2", 1), 1),
                (records.replace("pc=0x80000010", "pc=0x80000014", 1), 1),
                (records.replace("br_mask=0x0", "br_mask=0x1", 1), 1),
                (records.replace("lane=0", "lane=1", 1), 1),
                (records.replace("source=8304", "source=8320", 1), 1),
                (records.replace("opcode=0 size=2 dcache_origin", "opcode=3 size=2 dcache_origin"), 1),
                (records.replace("denied=0", "denied=1", 1), 1),
                (records + records.splitlines()[2] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(BOOM_STORE_AUTHORIZATION_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_boom_store_token_handoff_is_cpu_owned_and_fail_closed(self) -> None:
        boom_patch = BOOM_STORE_TOKEN_HANDOFF_PATCH.read_text(encoding="utf-8")
        tl_patch = TL_TOKEN_METADATA_PATCH.read_text(encoding="utf-8")
        overlay = CPU_OVERLAY.read_text(encoding="utf-8")
        origin = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        verifier = BOOM_STORE_TOKEN_HANDOFF_VERIFIER.read_text(encoding="utf-8")
        runner = BOOM_STORE_TOKEN_HANDOFF_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("val raveilTokenValid = Bool()", boom_patch)
        self.assertIn("val raveilTokenEpoch = UInt(16.W)", boom_patch)
        self.assertIn("val raveilTokenSequence = UInt(32.W)", boom_patch)
        self.assertIn("RaveilCpuTokenValidField()", boom_patch)
        self.assertIn("req.raveilTokenSequence", boom_patch)
        self.assertIn(
            "mshrs.io.req(w).bits.raveilTokenSequence := "
            "s2_req(w).raveilTokenSequence",
            boom_patch,
        )
        self.assertIn("Cached refills and prefetches never carry", boom_patch)
        self.assertIn("ControlKey[Bool]", tl_patch)
        self.assertIn("false.B", tl_patch)
        self.assertIn("Output(UInt(16.W)), 0.U", tl_patch)
        self.assertIn("Output(UInt(32.W)), 0.U", tl_patch)
        self.assertIn("tokenAuditAddress", overlay)
        self.assertIn("tokenWellFormed", overlay)
        self.assertIn("RAVEIL-OWNED-TL-TOKEN-V1 event=a", overlay)
        self.assertIn("RAVEIL-OWNED-TL-TOKEN-V1 event=d", overlay)
        self.assertIn("class RaveilOwnedSmallBoomTokenConfig", origin)
        self.assertIn("transport_token_correlation=same-token-observed", verifier)
        self.assertIn("semantic_initiator=not-promoted", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=boom-store-token-handoff", runner)
        self.assertIn(
            "boom-store-token-handoff:RaveilOwnedSmallBoomTokenConfig",
            shared_runner,
        )
        self.assertIn(
            "RaveilOwnedSmallBoomTokenConfig",
            CPU_SOURCE_MAP_VERIFIER.read_text(encoding="utf-8"),
        )
        self.assertIn("boom-store-token-handoff-build-v4", runner)
        self.assertNotEqual(BOOM_STORE_TOKEN_HANDOFF_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(BOOM_STORE_TOKEN_HANDOFF_VERIFIER.stat().st_mode & 0o111, 0)

    def test_boom_store_token_handoff_verifier_rejects_identity_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-BOOM-STORE-AUTH-V1 event=authorize epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 commit_valid=1 arch_valid=1 committed_write=1 event_source=boom-pinned",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=request epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 request_accepted=1 store=1",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=1 address=0x08000100 source=8304 opcode=0 size=2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-TOKEN-V1 event=a valid=1 epoch=1 sequence=1 address=0x08000100 source=8304 opcode=0 size=2 dcache_origin=1 classification=1",
                "RAVEIL-OWNED-TL-TOKEN-V1 event=d valid=1 epoch=1 sequence=1 source=8304 opcode=0 size=2 denied=0 corrupt=0 classification=1",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=1 source=8304 opcode=0 size=2 denied=0 corrupt=0 request_opcode=0 phase=0",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=response epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 response_valid=1 uses_stq=1 succeeded_write=1",
                "RAVEIL-BOOM-STORE-AUTH-V1 event=clear epoch=1 sequence=1 pc=0x80000010 address=0x08000100 rob_idx=7 stq_idx=1 br_mask=0x0 lane=0 request_seen=1 response_seen=1 stq_succeeded=1 promotion=eligible-local",
                "RAVEIL-OWNED-TL-FATE-V1 event=a manager_sequence=2 address=0x08000100 source=8288 opcode=4 size=2 dcache_origin=1 expected_source=1 phase=0",
                "RAVEIL-OWNED-TL-FATE-V1 event=d manager_sequence=2 source=8288 opcode=1 size=2 denied=0 corrupt=0 request_opcode=4 phase=0",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "boom-store-token.log"
            signature = Path(tmp) / "boom-store-token.signature"
            signature.write_text("00000001\n51a7c0de\n51a7c0de\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("event=a valid=1", "event=a valid=0"), 1),
                (records.replace("event=d valid=1", "event=d valid=0"), 1),
                (records.replace("event=a valid=1 epoch=1", "event=a valid=1 epoch=2"), 1),
                (records.replace("event=d valid=1 epoch=1", "event=d valid=1 epoch=2"), 1),
                (records.replace("event=a valid=1 epoch=1 sequence=1", "event=a valid=1 epoch=1 sequence=2"), 1),
                (records.replace("event=d valid=1 epoch=1 sequence=1", "event=d valid=1 epoch=1 sequence=2"), 1),
                (records.replace("classification=1", "classification=0", 1), 1),
                (records.replace("dcache_origin=1", "dcache_origin=0", 1), 1),
                (records.replace("source=8304 opcode=0", "source=8320 opcode=0", 1), 1),
                (records.replace("address=0x08000100 source=8304 opcode=0", "address=0x08000104 source=8304 opcode=0", 1), 1),
                (records.replace("event=d valid=1 epoch=1 sequence=1 source=8304", "event=d valid=1 epoch=1 sequence=1 source=8305"), 1),
                (records.replace("manager_sequence=1", "manager_sequence=3", 1), 1),
                (records.replace("denied=0", "denied=1", 1), 1),
                (records.replace("RAVEIL-BOOM-STORE-AUTH-V1 event=response", "RAVEIL-REMOVED event=response"), 1),
                (records.replace("RAVEIL-OWNED-TL-TOKEN-V1 event=d", "RAVEIL-REMOVED event=d"), 1),
                (records + records.splitlines()[3] + "\n", 1),
                (records + records.splitlines()[4] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(BOOM_STORE_TOKEN_HANDOFF_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_boom_postrequest_redirect_is_bounded_and_non_claiming(self) -> None:
        patch = BOOM_POSTREQUEST_REDIRECT_PATCH.read_text(encoding="utf-8")
        workload = BOOM_POSTREQUEST_REDIRECT_WORKLOAD.read_text(encoding="utf-8")
        verifier = BOOM_POSTREQUEST_REDIRECT_VERIFIER.read_text(encoding="utf-8")
        runner = BOOM_POSTREQUEST_REDIRECT_RUNNER.read_text(encoding="utf-8")
        shared_runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("dmem_req_fire(w)", patch)
        self.assertIn("dmem_req(w).bits.uop.br_mask =/= 0.U", patch)
        self.assertIn("IsKilledByBranch(io.core.brupdate", patch)
        self.assertIn("io.core.commit.valids(w)", patch)
        self.assertIn("repository sequence is identity", patch)
        self.assertIn("No token is carried through DCache or TileLink", patch)
        self.assertIn("li      s0, 0x80010000", workload)
        self.assertIn("divu    t2, t0, t1", workload)
        self.assertIn("xor     t2, t2, t2", workload)
        self.assertIn("bne     t2, zero, wrong_path_load", workload)
        self.assertIn("j       redirect_landed", workload)
        self.assertIn("lwu     t4, 0(s0)", workload)
        self.assertIn("postrequest_redirect=covered", verifier)
        self.assertIn("owned_manager=not-exercised", verifier)
        self.assertIn("post_tl_a_redirect=not-proven", verifier)
        self.assertIn("transport_cancellation=not-proven", verifier)
        self.assertIn("side_effect_absence=not-proven", verifier)
        self.assertIn("transport_token_correlation=not-carried", verifier)
        self.assertIn("semantic_initiator=not-proven", verifier)
        self.assertIn("performance=not-measured", verifier)
        self.assertIn("RAVEIL_OWNED_CPU_MODE=boom-postrequest-redirect", runner)
        self.assertIn(
            "boom-postrequest-redirect:RaveilOwnedSmallBoomConfig", shared_runner
        )
        self.assertIn("d4a331e3d69e62f2", shared_runner)
        self.assertNotEqual(BOOM_POSTREQUEST_REDIRECT_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(BOOM_POSTREQUEST_REDIRECT_VERIFIER.stat().st_mode & 0o111, 0)

    def test_boom_postrequest_redirect_verifier_rejects_mutation(self) -> None:
        records = "\n".join(
            (
                "RAVEIL-BOOM-POSTREQUEST-REDIRECT-V1 event=request epoch=1 sequence=1 pc=0x80000048 address=0x80010000 rob_idx=9 ldq_idx=1 br_mask=0x1 lane=0 request_accepted=1 branch_context=1 event_source=boom-pinned",
                "RAVEIL-BOOM-POSTREQUEST-REDIRECT-V1 event=response epoch=1 sequence=1 pc=0x80000048 address=0x80010000 rob_idx=9 ldq_idx=1 br_mask=0x1 lane=0 response_valid=1 before_redirect=1",
                "RAVEIL-BOOM-POSTREQUEST-REDIRECT-V1 event=redirect epoch=1 sequence=1 pc=0x80000048 address=0x80010000 rob_idx=9 ldq_idx=1 br_mask=0x1 lane=0 request_seen=1 response_seen=1 branch_killed=1 commit_valid=0 arch_valid=0 promotion=blocked",
            )
        ) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "boom-redirect.log"
            signature = Path(tmp) / "boom-redirect.signature"
            signature.write_text("00000001\n682513da\n682513da\n", encoding="ascii")
            for text, expected_returncode in (
                (records, 0),
                (records.replace("request_accepted=1", "request_accepted=0"), 1),
                (records.replace("branch_context=1", "branch_context=0"), 1),
                (records.replace("response_valid=1", "response_valid=0"), 1),
                (records.replace("before_redirect=1", "before_redirect=0"), 1),
                (records.replace("request_seen=1", "request_seen=0"), 1),
                (records.replace("response_seen=1", "response_seen=0"), 1),
                (records.replace("branch_killed=1", "branch_killed=0"), 1),
                (records.replace("commit_valid=0", "commit_valid=1"), 1),
                (records.replace("arch_valid=0", "arch_valid=1"), 1),
                (records.replace("promotion=blocked", "promotion=eligible"), 1),
                (records.replace("br_mask=0x1", "br_mask=0x0"), 1),
                (records.replace("address=0x80010000", "address=0x80010004"), 1),
                (records.replace("pc=0x80000048", "pc=0x8000004c"), 1),
                (records.replace("rob_idx=9", "rob_idx=10", 1), 1),
                (records.replace("ldq_idx=1", "ldq_idx=2", 1), 1),
                (records.replace("pc=0x80000048", "pc=0x8000004c", 1), 1),
                (records.replace("lane=0", "lane=1", 1), 1),
                (records + records.splitlines()[1] + "\n", 1),
            ):
                log.write_text(text, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(BOOM_POSTREQUEST_REDIRECT_VERIFIER),
                        str(log),
                        str(signature),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, expected_returncode, result.stderr)

    def test_cpu_workload_reaches_owned_memory_with_phase_fences(self) -> None:
        workload = ROCKET_MEMORY_WORKLOAD.read_text(encoding="utf-8")
        verifier = ROCKET_MEMORY_VERIFIER.read_text(encoding="utf-8")
        source_map_verifier = CPU_SOURCE_MAP_VERIFIER.read_text(encoding="utf-8")
        runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        rocket_runner = ROCKET_MEMORY_RUNNER.read_text(encoding="utf-8")
        boom_runner = BOOM_MEMORY_RUNNER.read_text(encoding="utf-8")
        self.assertIn("li      s0, 0x08000000", workload)
        self.assertIn("li      s1, 0x08010000", workload)
        self.assertGreaterEqual(workload.count("fence   iorw, iorw"), 4)
        self.assertIn("sb      t2, 1(s0)", workload)
        self.assertIn("sb      t2, 3(s0)", workload)
        self.assertIn("lwu     t3, 4(s0)", workload)
        self.assertIn("lw      a3, 0x20(s1)", workload)
        self.assertIn("lw      a4, 0x24(s1)", workload)
        self.assertIn("0x5522AA44", verifier)
        self.assertIn("0xCAFEBABE", verifier)
        self.assertIn("accepted=8 completed=8", verifier)
        self.assertIn("signature_sha256=", verifier)
        self.assertIn('"rocket": (8224, 8256)', verifier)
        self.assertIn('"boom": (8288, 8320)', verifier)
        self.assertIn("Core 0 DCache MMIO", source_map_verifier)
        self.assertIn("fragmenter_factor=32", source_map_verifier)
        self.assertIn('"RaveilOwnedRocketFateConfig"', source_map_verifier)
        self.assertIn("graph.name ==", source_map_verifier)
        for entrypoint in (
            CPU_MEMORY_RUNNER,
            ROCKET_MEMORY_RUNNER,
            BOOM_MEMORY_RUNNER,
        ):
            self.assertNotEqual(entrypoint.stat().st_mode & 0o111, 0)
        self.assertIn('CONFIG="$RAVEIL_OWNED_CPU_CONFIG"', runner)
        self.assertIn(
            "rocket:raveil-chipyard-owned-rocket-sim-build-v1", runner
        )
        self.assertIn(
            "boom:raveil-chipyard-owned-boom-sim-build-v1", runner
        )
        self.assertIn('"$linker" "$runner" "$dockerfile"', runner)
        self.assertIn("CONFIG_PACKAGE=chipyard.raveil", runner)
        self.assertIn("persistent simulator source cache contains an unexpected", runner)
        self.assertIn("submodule foreach --quiet --recursive", runner)
        self.assertIn("cpu_execution=%s-rtl-simulation", runner)
        self.assertIn("source_client_class=dcache-mmio-verified", runner)
        self.assertIn("dcache_origin_path=observed", runner)
        self.assertIn("semantic_initiator=not-proven", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)
        self.assertIn("RaveilOwnedRocketConfig", rocket_runner)
        self.assertIn("RAVEIL_OWNED_CPU_LABEL=rocket", rocket_runner)
        self.assertIn("RaveilOwnedSmallBoomConfig", boom_runner)
        self.assertIn("RAVEIL_OWNED_CPU_LABEL=boom", boom_runner)

    def test_dcache_origin_sideband_is_structural_and_fail_closed(self) -> None:
        overlay = CPU_OVERLAY.read_text(encoding="utf-8")
        tagger = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        rocket_patch = ROCKET_DCACHE_ORIGIN_PATCH.read_text(encoding="utf-8")
        boom_patch = BOOM_DCACHE_ORIGIN_PATCH.read_text(encoding="utf-8")
        xbar_patch = TLXBAR_REQUEST_DEFAULTS_PATCH.read_text(encoding="utf-8")
        runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")
        workload = ROCKET_MEMORY_WORKLOAD.read_text(encoding="utf-8")
        verifier = ROCKET_MEMORY_VERIFIER.read_text(encoding="utf-8")

        self.assertIn('DataKey[Bool]("raveil_dcache_origin")', overlay)
        self.assertIn("DCacheTLNodeTransformKey", tagger)
        self.assertIn("out.a.bits.user(RaveilDCacheOrigin) := true.B", tagger)
        self.assertIn("Connectable.waiveUnmatched", tagger)
        self.assertIn("not identify an instruction, PC, ELF", tagger)
        self.assertIn("tl.a.bits.user.lift(RaveilDCacheOrigin)", overlay)
        self.assertIn("requestKeys = Seq(", overlay)
        self.assertIn("RaveilDCacheOrigin,", overlay)
        self.assertIn("pinned, ephemeral TLXbar patch", tagger)
        self.assertIn("responseDcacheOrigin := dcacheOriginRequest", overlay)
        self.assertIn(
            "dcacheOriginAcceptedCount === dcacheOriginCompletedCount", overlay
        )
        self.assertIn(
            "nonDcacheOriginAcceptedCount === nonDcacheOriginCompletedCount",
            overlay,
        )
        self.assertIn("HellaCache.scala", rocket_patch)
        self.assertIn("src/main/scala/common/tile.scala", boom_patch)
        self.assertIn("p(DCacheTLNodeTransformKey)(p)(dcache.node)", rocket_patch)
        self.assertIn("p(DCacheTLNodeTransformKey)(p)(dcache.node)", boom_patch)
        self.assertIn("BundleMap.setAlignedDefaults(in(i).a.bits.user)", xbar_patch)
        self.assertIn("BundleMap.setAlignedDefaults(in(i).c.bits.user)", xbar_patch)
        self.assertIn("cache_key=$RAVEIL_SOURCE_SHA256", runner)
        self.assertIn("persistent simulator source cache is incomplete", runner)
        self.assertIn("RAVEIL_ROCKET_HOOK_PATCH_SHA256", runner)
        self.assertIn("RAVEIL_BOOM_HOOK_PATCH_SHA256", runner)
        self.assertIn("RAVEIL_XBAR_REQUEST_PATCH_SHA256", runner)
        self.assertIn("src/main/scala/tilelink/Xbar.scala", runner)
        self.assertIn(".fill 30, 4, 0", workload)
        self.assertIn("OWNED-MEMORY-CPU-SIGNATURE-V3", verifier)

        protocol_harness = TL_PROTOCOL_HARNESS.read_text(encoding="utf-8")
        protocol_runner = TL_PROTOCOL_RUNNER.read_text(encoding="utf-8")
        self.assertIn("class RaveilOriginStrippingAdapter", protocol_harness)
        self.assertIn("filterNot(_.key == RaveilDCacheOrigin)", protocol_harness)
        self.assertIn("tl.a.bits.user(RaveilDCacheOrigin) := true.B", protocol_harness)
        self.assertIn("not a real loader/debug path", protocol_harness)
        self.assertIn("RaveilOwnedTLOriginStripHarness", protocol_runner)
        self.assertIn("verified protocol assembly cache is unavailable", protocol_runner)

    def test_dcache_origin_signature_rejects_legacy_and_bad_origin(self) -> None:
        source_start = 8224
        values = [
            1, 0, 0x11223344, 0x5522AA44, 0xCAFEBABE, 2, 8, 8,
            2, 3, 2, 1, source_start, 8256, 8, 8, 0, 0,
            source_start, source_start, 2, 2, 8, 8, 0, 0,
            source_start, source_start, 2, 2,
        ]

        def verify(candidate: list[int]) -> subprocess.CompletedProcess[str]:
            with tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as sig:
                sig.write("".join(f"{value:08x}\n" for value in candidate))
                sig.flush()
                return subprocess.run(
                    ["python3", str(ROCKET_MEMORY_VERIFIER), "rocket", sig.name],
                    text=True,
                    capture_output=True,
                    check=False,
                )

        self.assertEqual(verify(values).returncode, 0)
        self.assertNotEqual(verify(values[:22]).returncode, 0)
        bad_origin = values.copy()
        bad_origin[24] = 1
        self.assertNotEqual(verify(bad_origin).returncode, 0)
        bad_source = values.copy()
        bad_source[27] = 8256
        self.assertNotEqual(verify(bad_source).returncode, 0)

        with tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as sig:
            sig.write("not-hex\n")
            sig.flush()
            malformed = subprocess.run(
                ["python3", str(ROCKET_MEMORY_VERIFIER), "rocket", sig.name],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(malformed.returncode, 0)

        extra_word = values + [0]
        self.assertNotEqual(verify(extra_word).returncode, 0)
        bad_prefix = values.copy()
        bad_prefix[2] ^= 1
        self.assertNotEqual(verify(bad_prefix).returncode, 0)

    def test_loader_probe_is_pt_load_bounded_and_fail_closed(self) -> None:
        workload = LOADER_PROBE_WORKLOAD.read_text(encoding="utf-8")
        linker = LOADER_PROBE_LINKER.read_text(encoding="utf-8")
        verifier = LOADER_PROBE_VERIFIER.read_text(encoding="utf-8")
        runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")

        self.assertIn("li      s0, 0x08000000", workload)
        self.assertIn(".word 0x6c6f6164", workload)
        self.assertIn(".fill 33, 4, 0", workload)
        self.assertIn("probe PT_LOAD FLAGS(6)", linker)
        self.assertIn(". = 0x08000000", linker)
        self.assertIn("OWNED-MEMORY-LOADER-PROBE-V1", verifier)
        self.assertIn('"rocket": (8224, 8256)', verifier)
        self.assertIn('"boom": (8288, 8320)', verifier)
        self.assertNotEqual(LOADER_PROBE_VERIFIER.stat().st_mode & 0o111, 0)
        self.assertIn('"$loader_probe" "$loader_probe_linker"', runner)
        self.assertIn('"$loader_probe_verifier" "$source_nonidentity_verifier"', runner)
        self.assertIn('"$source_nonidentity_verifier" "$source_map_verifier"', runner)
        self.assertIn("riscv64-unknown-elf-readelf -lW", runner)
        self.assertIn("exactly one PT_LOAD at 0x08000000", runner)
        self.assertIn("owned_memory_loader_probe.signature", runner)
        self.assertIn("OWNED-CPU-LOADER-PROBE-AUDIT-V1", runner)
        self.assertIn('sha256sum "$graph" | cut -c1-64', runner)
        self.assertIn("preload_bypass=absent", runner)
        self.assertIn("verify_owned_cpu_source_nonidentity.py", runner)
        self.assertNotIn("+loadmem", runner)

    def test_same_dcache_source_does_not_identify_one_elf(self) -> None:
        source = SOURCE_NONIDENTITY_VERIFIER.read_text(encoding="utf-8")
        self.assertIn("OWNED-CPU-SOURCE-NONIDENTITY-V1", source)
        self.assertIn("semantic_identity=not-carried", source)
        self.assertNotEqual(SOURCE_NONIDENTITY_VERIFIER.stat().st_mode & 0o111, 0)

        cpu_source = 8224
        cpu_signature = [
            1, 0, 0x11223344, 0x5522AA44, 0xCAFEBABE, 2, 8, 8,
            2, 3, 2, 1, 8224, 8256, 8, 8, 0, 0,
            cpu_source, cpu_source, 2, 2, 8, 8, 0, 0,
            cpu_source, cpu_source, 2, 2,
        ]
        loader_signature = [
            1, 2, 2, 0, 0, 2, 2, 0, 0, 2, 2,
            16, 16, 0, 0, 0x6C6F6164,
            3, 3, 1, 1, 2, 2, 1, 1, 2, 2,
            cpu_source, cpu_source, 0, 0, 8224, 8256, 0,
        ]

        def verify(
            cpu_values: list[int], loader_values: list[int], same_elf: bool = False
        ) -> subprocess.CompletedProcess[str]:
            with (
                tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as cpu_sig,
                tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as loader_sig,
                tempfile.NamedTemporaryFile(mode="wb") as cpu_elf,
                tempfile.NamedTemporaryFile(mode="wb") as loader_elf,
            ):
                cpu_sig.write("".join(f"{value:08x}\n" for value in cpu_values))
                loader_sig.write("".join(f"{value:08x}\n" for value in loader_values))
                cpu_elf.write(b"cpu-elf")
                loader_elf.write(b"cpu-elf" if same_elf else b"loader-elf")
                for temporary in (cpu_sig, loader_sig, cpu_elf, loader_elf):
                    temporary.flush()
                return subprocess.run(
                    [
                        "python3", str(SOURCE_NONIDENTITY_VERIFIER), "rocket",
                        cpu_sig.name, loader_sig.name, cpu_elf.name, loader_elf.name,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

        self.assertEqual(verify(cpu_signature, loader_signature).returncode, 0)
        different_source = loader_signature.copy()
        different_source[26] += 1
        self.assertNotEqual(verify(cpu_signature, different_source).returncode, 0)
        self.assertNotEqual(verify(cpu_signature, loader_signature, same_elf=True).returncode, 0)
        bad_origin = loader_signature.copy()
        bad_origin[22] = 0
        self.assertNotEqual(verify(cpu_signature, bad_origin).returncode, 0)
        same_payload = loader_signature.copy()
        same_payload[15] = cpu_signature[2]
        self.assertNotEqual(verify(cpu_signature, same_payload).returncode, 0)
        self.assertNotEqual(verify(cpu_signature[:-1], loader_signature).returncode, 0)

    def test_loader_probe_signature_rejects_bad_paths(self) -> None:
        source_start = 8224
        values = [
            1, 2, 2, 0, 0, 2, 2, 0, 0, 2, 2,
            0, 0, 0, 0, 0x6C6F6164,
            3, 3, 1, 1, 2, 2, 1, 1, 2, 2,
            source_start, source_start, 0, 0, source_start, 8256, 0,
        ]

        def verify(candidate: list[int]) -> subprocess.CompletedProcess[str]:
            with tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as sig:
                sig.write("".join(f"{value:08x}\n" for value in candidate))
                sig.flush()
                return subprocess.run(
                    ["python3", str(LOADER_PROBE_VERIFIER), "rocket", sig.name],
                    text=True,
                    capture_output=True,
                    check=False,
                )

        self.assertEqual(verify(values).returncode, 0)
        bad_serial_source = values.copy()
        bad_serial_source[11] = 8192
        self.assertNotEqual(verify(bad_serial_source).returncode, 0)
        bad_origin = values.copy()
        bad_origin[7] = 1
        self.assertNotEqual(verify(bad_origin).returncode, 0)
        bad_dcache_source = values.copy()
        bad_dcache_source[27] = 8256
        self.assertNotEqual(verify(bad_dcache_source).returncode, 0)
        self.assertNotEqual(verify(values[:-1]).returncode, 0)

    def test_debug_sba_path_is_dedicated_bounded_and_fail_closed(self) -> None:
        overlay = CPU_OVERLAY.read_text(encoding="utf-8")
        config = DCACHE_ORIGIN_TAGGER.read_text(encoding="utf-8")
        workload = DEBUG_SBA_WORKLOAD.read_text(encoding="utf-8")
        verifier = DEBUG_SBA_VERIFIER.read_text(encoding="utf-8")
        source_verifier = DEBUG_SBA_SOURCE_MAP_VERIFIER.read_text(encoding="utf-8")
        runner = CPU_MEMORY_RUNNER.read_text(encoding="utf-8")

        self.assertIn("lastNonDcacheOriginAcceptedSource", overlay)
        self.assertIn("controlOffset === 0xa4.U", overlay)
        self.assertIn("class RaveilDebugSBADriver", config)
        self.assertIn("class WithRaveilDebugSBAHarness", config)
        self.assertIn("new chipyard.config.WithDMIDTM", config)
        self.assertIn("new freechips.rocketchip.subsystem.WithDebugSBA", config)
        self.assertIn("WithRaveilOwnedMemorySourceRange(16416, 16448)", config)
        self.assertIn("WithRaveilOwnedMemorySourceRange(16480, 16512)", config)
        self.assertIn("io.reqValid && io.reqReady", config)
        self.assertIn("io.respValid && io.respReady", config)
        self.assertIn("assert(waiting || requestFire", config)
        self.assertIn("Debug SBA system bus error", config)
        self.assertIn("Debug SBA DMI driver timed out", config)
        self.assertIn("li      t1, 32768", workload)
        self.assertIn("bnez    t0, 2f", workload)
        self.assertIn("lbu     t0, 0(s0)", workload)
        self.assertIn(".fill 37, 4, 0", workload)
        self.assertIn('"debug": (8192, 8224)', verifier)
        self.assertIn('"dcache": (16416, 16448)', verifier)
        self.assertIn('"dcache": (16480, 16512)', verifier)
        self.assertIn('"debug_input": (256, 257)', source_verifier)
        self.assertIn('observed["fragmenter"] != (0, 32800)', source_verifier)
        self.assertIn("GraphML repeats a master", source_verifier)
        self.assertIn("source_client_class=topology-only", source_verifier)
        self.assertIn(
            "RAVEIL_OWNED_CPU_MODE=debug-sba",
            ROCKET_DEBUG_SBA_RUNNER.read_text(encoding="utf-8"),
        )
        self.assertIn("OWNED-CPU-DEBUG-SBA-SMOKE-V1", runner)
        self.assertIn('timeout --foreground 180 "$sim"', runner)
        for entrypoint in (ROCKET_DEBUG_SBA_RUNNER, BOOM_DEBUG_SBA_RUNNER):
            self.assertNotEqual(entrypoint.stat().st_mode & 0o111, 0)

    def test_debug_sba_signature_rejects_wrong_origin_and_source(self) -> None:
        debug_source = 8192
        dcache_source = 16416
        values = [
            1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1,
            debug_source, debug_source, 0, 0,
            debug_source, debug_source, 0, 0, 0xA5,
            2, 2, 1, 1, 1, 1, 1, 1, 1, 1,
            dcache_source, dcache_source, 0, 0,
            debug_source, debug_source,
        ]

        def verify(candidate: list[int]) -> subprocess.CompletedProcess[str]:
            with tempfile.NamedTemporaryFile(mode="w", encoding="ascii") as sig:
                sig.write("".join(f"{value:08x}\n" for value in candidate))
                sig.flush()
                return subprocess.run(
                    ["python3", str(DEBUG_SBA_VERIFIER), "rocket", sig.name],
                    text=True,
                    capture_output=True,
                    check=False,
                )

        self.assertEqual(verify(values).returncode, 0)
        bad_origin = values.copy()
        bad_origin[27] = 0
        self.assertNotEqual(verify(bad_origin).returncode, 0)
        bad_debug_source = values.copy()
        bad_debug_source[12] = 8224
        self.assertNotEqual(verify(bad_debug_source).returncode, 0)
        bad_dcache_source = values.copy()
        bad_dcache_source[31] = 16448
        self.assertNotEqual(verify(bad_dcache_source).returncode, 0)
        self.assertNotEqual(verify(values[:-1]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
