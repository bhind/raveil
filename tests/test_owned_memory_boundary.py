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
        self.assertIn('"$rocket_witness_patch" "$boom_hook_patch"', shared_runner)
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
        self.assertIn("requestKeys = Seq(RaveilDCacheOrigin)", overlay)
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
