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
        expected_tag = configuration_id()[:16]
        self.assertIn(f'val ConfigurationTag = "{expected_tag}"', source)
        self.assertIn("runtime_ready_slots=0", source)
        self.assertNotIn("IssueQueue", source)
        self.assertNotIn("ReorderBuffer", source)

    def test_owned_rtl_entrypoints_are_executable_and_non_claiming(self) -> None:
        self.assertNotEqual(HOST_RUNNER.stat().st_mode & 0o111, 0)
        self.assertNotEqual(CONTAINER_RUNNER.stat().st_mode & 0o111, 0)
        host = HOST_RUNNER.read_text(encoding="utf-8")
        inner = CONTAINER_RUNNER.read_text(encoding="utf-8")
        self.assertIn("platform=linux/amd64", host)
        self.assertIn("no-new-privileges=true", host)
        self.assertIn("run-static-stencil.sh", host)
        self.assertIn("performance=not-measured", host)
        self.assertIn("StaticStencilRegion.scala", inner)


if __name__ == "__main__":
    unittest.main()
