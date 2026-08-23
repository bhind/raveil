from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
CLIENT = ROOT / "hardware/chisel/chipyard-overlay/RaveilStaticStencilTLClient.scala"
CONFIG = ROOT / "hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
RUNNER = ROOT / "hardware/chisel/run-g1b-common-owned-memory-elaboration.sh"


class G1bCommonOwnedMemoryStructureTests(unittest.TestCase):
    def test_integrated_only_graph_origin_is_distinct(self) -> None:
        client = CLIENT.read_text(encoding="utf-8")
        memory = MEMORY.read_text(encoding="utf-8")
        self.assertIn('RaveilGraphOrigin extends DataKey[Bool]', memory)
        self.assertIn('name = "raveil-static-stencil-graph"', client)
        self.assertIn("requestFields = Seq(RaveilGraphOriginField())", client)
        self.assertIn("tl.a.bits.user(RaveilGraphOrigin) := true.B", client)
        self.assertIn('core.io.memory.request.bits.writeMask, "hf".U', client)
        self.assertNotIn("RaveilDCacheOrigin", client)
        self.assertIn("integratedGraph: Boolean = false", memory)
        self.assertIn("if (params.integratedGraph) Seq(RaveilGraphOrigin)", memory)
        self.assertIn("Raveil Graph request impersonated DCache origin", memory)
        self.assertIn("graphOriginAcceptedCount", memory)
        self.assertIn("graphOriginCompletedCount", memory)

    def test_top_has_one_manager_and_attached_core_not_wrapper(self) -> None:
        client = CLIENT.read_text(encoding="utf-8")
        memory = MEMORY.read_text(encoding="utf-8")
        self.assertIn("class RaveilStaticStencilTLClient", client)
        self.assertIn("Module(new RaveilStaticStencilCore)", client)
        self.assertNotIn("StaticStencilRegion", client)
        self.assertNotIn("OwnedFixedLatencyScratchpad", client)
        self.assertIn('bus.coupleFrom("raveil-static-stencil-graph")', client)
        self.assertNotIn("with CanHaveRaveilStaticStencilAttachment", memory)
        self.assertIn("class RaveilIntegratedGraphDigitalTop", client)
        self.assertIn("with CanHaveRaveilStaticStencilAttachment", client)
        self.assertEqual(memory.count("val memory = SyncReadMem"), 1)

    def test_named_rocket_config_keeps_existing_dcache_path(self) -> None:
        config = CONFIG.read_text(encoding="utf-8")
        self.assertIn("class RaveilIntegratedGraphRocketConfig", config)
        self.assertIn("new WithRaveilIntegratedGraphBuildSystem", config)
        self.assertNotIn(
            "new WithRaveilOwnedBuildSystem ++\n"
            "  new WithRaveilIntegratedGraphMemorySourceRange",
            config,
        )
        self.assertIn("new WithRaveilDCacheOriginTagger", config)
        self.assertIn("new chipyard.RocketConfig", config)
        self.assertIn("WithRaveilIntegratedGraphMemorySourceRange(8224, 8256)", config)

    def test_elaboration_runner_records_topology_only(self) -> None:
        runner = RUNNER.read_text(encoding="utf-8")
        self.assertNotEqual(RUNNER.stat().st_mode & 0o111, 0)
        self.assertIn("RaveilIntegratedGraphRocketConfig", runner)
        self.assertIn("RaveilStaticStencilTLClient", runner)
        self.assertIn("manager_instances=1", runner)
        self.assertIn("compared_data_sync_read_mem_definitions=1", runner)
        self.assertIn("graph_source=elaboration-derived", runner)
        self.assertIn("graph_manager_source_range=%s", runner)
        self.assertIn('fragmenter_range" = "0:32800"', runner)
        self.assertIn("client_state=dormant", runner)
        self.assertIn("checkpoint_a=0", runner)
        self.assertIn("performance=not-measured", runner)
        self.assertIn("--network none", runner)
        self.assertIn("runner_sha256=", runner)
        self.assertIn("dockerfile_sha256=", runner)
        self.assertIn("chipyard_revision=", runner)
        self.assertIn("RaveilFixtureInputProvider.scala", runner)
        self.assertIn("t-0042-tl-token-metadata.patch", runner)
        self.assertIn("graph_origin_count=", runner)
        self.assertIn("G1B-COMMON-OWNED-MEMORY-TOPOLOGY-CHECK-V1", runner)
        self.assertIn("generated FIR does not contain exactly one owned manager instance", runner)
        self.assertNotIn("head -n 1", runner)
        self.assertNotIn("run-physical", runner)

    def test_graph_client_checks_response_routing(self) -> None:
        client = CLIENT.read_text(encoding="utf-8")
        self.assertIn("assert(tl.d.bits.source === 0.U)", client)
        self.assertIn("assert(tl.d.bits.size === 2.U)", client)
        self.assertIn("TLMessages.AccessAck, TLMessages.AccessAckData", client)


if __name__ == "__main__":
    unittest.main()
