from pathlib import Path
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
        runner = CPU_ELABORATION_RUNNER.read_text(encoding="utf-8")
        self.assertIn("class RaveilOwnedTLMemory", overlay)
        self.assertIn("new testchipip.soc.WithNoScratchpads", overlay)
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
        self.assertIn("OWNED-TL-PROTOCOL-V3", driver)
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
        self.assertIn('"$linker" "$runner"', runner)
        self.assertIn("CONFIG_PACKAGE=chipyard.raveil", runner)
        self.assertIn("persistent simulator source cache contains an unexpected", runner)
        self.assertIn("submodule foreach --quiet --recursive", runner)
        self.assertIn("cpu_execution=%s-rtl-simulation", runner)
        self.assertIn("source_client_class=dcache-mmio-verified", runner)
        self.assertIn("semantic_initiator=not-proven", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)
        self.assertIn("RaveilOwnedRocketConfig", rocket_runner)
        self.assertIn("RAVEIL_OWNED_CPU_LABEL=rocket", rocket_runner)
        self.assertIn("RaveilOwnedSmallBoomConfig", boom_runner)
        self.assertIn("RAVEIL_OWNED_CPU_LABEL=boom", boom_runner)


if __name__ == "__main__":
    unittest.main()
