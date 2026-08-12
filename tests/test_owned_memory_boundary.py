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
        self.assertIn("memory.node := client.node", harness)
        self.assertIn("response_backpressure=covered", driver)
        self.assertIn("max_one_outstanding=covered", driver)
        self.assertIn("byte_masks=0x5,0xa", driver)
        self.assertIn("invalid_phase_denial=covered", driver)
        self.assertIn("response_metadata=param,size,source,sink,denied,corrupt", driver)
        self.assertNotEqual(TL_PROTOCOL_RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("--assert --cc", runner)
        self.assertIn("assembly_cache=content-addressed", runner)
        self.assertIn("cpu_execution=not-run", runner)
        self.assertIn("resource_match_verified=0", runner)
        self.assertIn("performance=not-measured", runner)


if __name__ == "__main__":
    unittest.main()
