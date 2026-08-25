from copy import deepcopy
from pathlib import Path
import unittest

from raveil.static_region import (
    StaticRegionContractError,
    compile_static_stencil_descriptor,
    configuration_id,
    static_stencil_oracle,
    validate_static_stencil_descriptor,
)


ROOT = Path(__file__).resolve().parents[1]
RTL = ROOT / "hardware" / "chisel" / "StaticStencilRegion.scala"
CORE = (
    ROOT / "hardware" / "chisel" / "chipyard-overlay"
    / "RaveilStaticStencilCore.scala"
)
HOST_RUNNER = ROOT / "hardware" / "chisel" / "run-static-stencil-rtl.sh"
CONTAINER_RUNNER = ROOT / "hardware" / "chisel" / "run-static-stencil.sh"


class StaticRegionContractTests(unittest.TestCase):
    def test_compiler_is_deterministic_and_validator_accepts_it(self) -> None:
        first = compile_static_stencil_descriptor()
        second = compile_static_stencil_descriptor()
        self.assertEqual(first, second)
        validate_static_stencil_descriptor(first)
        self.assertEqual(configuration_id(first), configuration_id(second))

    def test_validator_rejects_dependency_rewrite(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["edges"][0] = {
            "producer": "add_0",
            "consumer": "load_center",
            "input": 0,
        }
        with self.assertRaisesRegex(StaticRegionContractError, "dependency|acyclic|schedule"):
            validate_static_stencil_descriptor(descriptor)

    def test_validator_rejects_unknown_field(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["runtime_hint"] = "not-part-of-the-contract"
        with self.assertRaisesRegex(StaticRegionContractError, "fields"):
            validate_static_stencil_descriptor(descriptor)

    def test_validator_rejects_alternate_schedule(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["schedule"][1]["nodes"].reverse()
        with self.assertRaisesRegex(StaticRegionContractError, "schedule"):
            validate_static_stencil_descriptor(descriptor)

    def test_validator_rejects_effect_kind_change(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["nodes"][0]["effect"]["kind"] = "WRITE"
        with self.assertRaisesRegex(StaticRegionContractError, "effect"):
            validate_static_stencil_descriptor(descriptor)

    def test_validator_rejects_alias_boundary_change(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["objects"][0]["requires_disjoint_from"] = []
        with self.assertRaisesRegex(StaticRegionContractError, "disjoint"):
            validate_static_stencil_descriptor(descriptor)

    def test_validator_rejects_dynamic_issue(self) -> None:
        descriptor = deepcopy(compile_static_stencil_descriptor())
        descriptor["resources"]["runtime_ready_slots"] = 1
        with self.assertRaisesRegex(StaticRegionContractError, "resource"):
            validate_static_stencil_descriptor(descriptor)

    def test_oracle_has_exact_shape_and_wraps_uint32(self) -> None:
        words = [0xFFFFFFFF] * 324
        output = static_stencil_oracle(words)
        self.assertEqual(len(output), 256)
        self.assertEqual(set(output), {0xFFFFFFFB})

    def test_rtl_binds_configuration_tag(self) -> None:
        source = RTL.read_text(encoding="utf-8")
        core = CORE.read_text(encoding="utf-8")
        expected_tag = configuration_id()[:16]
        self.assertIn(f'val ConfigurationTag = "{expected_tag}"', source)
        self.assertIn("runtime_ready_slots=0", source)
        self.assertIn("new OwnedFixedLatencyScratchpad(1024, 580)", source)
        self.assertEqual(source.count("new OwnedFixedLatencyScratchpad"), 1)
        self.assertIn("graphInputReadsAccepted", source)
        self.assertIn("graphOutputWritesAccepted", source)
        self.assertIn("val core = Module(new RaveilStaticStencilCore)", source)
        self.assertIn("core.io.memory.request.ready := scratchpad.io.requestReady", source)
        self.assertIn("core.io.memory.response.valid := scratchpad.io.responseValid", source)
        self.assertIn("scratchpad.io.requestInitiator === OwnedMemoryContract.InitiatorGraph.U", source)
        self.assertIn("scratchpad.io.responsePhase === OwnedMemoryContract.PhaseExecution.U", source)
        self.assertNotIn("IssueQueue", source)
        self.assertNotIn("ReorderBuffer", source)
        self.assertIn("package chipyard.raveil", core)
        self.assertIn("class RaveilStaticStencilMemoryPort", core)
        self.assertIn("val address = UInt(10.W)", core)
        self.assertIn("outputAddress := 324.U + outputRowBase + logicalColumn", core)
        self.assertIn("logicalRow := outputIndex / io.columns", core)
        self.assertIn("logicalColumn := outputIndex % io.columns", core)
        self.assertIn("center - io.inputStride", core)
        self.assertIn("center + io.inputStride", core)
        self.assertIn(
            "324.U(10.W) + io.outputValidationAddress.pad(10)", source
        )
        self.assertIn("val request = Decoupled", core)
        self.assertIn("val response = Flipped(Decoupled", core)
        self.assertIn("class RaveilStaticStencilCore", core)
        self.assertIn("Enum(6)", core)
        self.assertIn("io.program(programCounter)", core)
        self.assertIn("val opcode = instruction(31, 28)", core)
        self.assertIn("io.memory.request.bits.initiator := 2.U", core)
        self.assertIn("io.memory.request.bits.phase := 2.U", core)
        self.assertIn("busyReg && !cancelling && state === storeResponse", core)
        self.assertIn("val lastOutput = outputIndex.pad(9) === io.activeOutputs - 1.U", core)
        self.assertIn("lastOutput && responseFire", core)
        self.assertIn("val requestFire = io.memory.request.valid && io.memory.request.ready", core)
        self.assertIn("val responseFire = io.memory.response.valid && io.memory.response.ready", core)
        self.assertIn("one outstanding request", core)
        self.assertNotIn("TLClientNode", core)

        harness = (ROOT / "hardware" / "chisel" /
                   "static_stencil_sim_main.cpp").read_text(encoding="utf-8")
        self.assertIn("final-store cancel exposed completion or publication", harness)
        self.assertIn("cancelled=2", harness)

    def test_owned_rtl_entrypoints_are_executable_and_non_claiming(self) -> None:
        self.assertNotEqual(HOST_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(CONTAINER_RUNNER.stat().st_mode & 0o111, 0)
        host = HOST_RUNNER.read_text(encoding="utf-8")
        inner = CONTAINER_RUNNER.read_text(encoding="utf-8")
        self.assertIn("platform=linux/amd64", host)
        self.assertIn("no-new-privileges=true", host)
        self.assertIn("--network none", host)
        self.assertIn("run-static-stencil.sh", host)
        self.assertIn("performance=not-measured", host)
        self.assertIn("StaticStencilRegion.scala", inner)
        self.assertIn("RaveilStaticStencilCore.scala", inner)
        self.assertIn("OwnedFixedLatencyScratchpad.scala", inner)


if __name__ == "__main__":
    unittest.main()
