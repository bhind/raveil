from copy import deepcopy
from pathlib import Path
import unittest

from raveil.simulation_adapter import (
    ACCOUNTING_PHASES,
    SimulationAdapterError,
    compile_simulation_adapter_contract,
    cpu_functional_observation,
    simulation_adapter_contract_id,
    static_graph_cancelled_observation,
    static_graph_functional_observation,
    validate_simulation_adapter_contract,
    validate_simulation_observation,
)


ROOT = Path(__file__).resolve().parents[1]
RTL_HARNESS = ROOT / "hardware" / "chisel" / "static_stencil_sim_main.cpp"
HOST_RUNNER = ROOT / "hardware" / "chisel" / "run-static-stencil-rtl.sh"


class SimulationAdapterTests(unittest.TestCase):
    def test_contract_is_deterministic_and_exact(self) -> None:
        first = compile_simulation_adapter_contract()
        second = compile_simulation_adapter_contract()
        self.assertEqual(first, second)
        validate_simulation_adapter_contract(first)
        self.assertEqual(len(simulation_adapter_contract_id()), 64)

    def test_contract_rejects_upstream_or_unknown_field(self) -> None:
        contract = deepcopy(compile_simulation_adapter_contract())
        contract["boom_micro_op"] = "leaked-upstream-type"
        with self.assertRaisesRegex(SimulationAdapterError, "contract"):
            validate_simulation_adapter_contract(contract)

    def test_current_graph_record_is_functional_but_not_measurement_ready(self) -> None:
        observation = static_graph_functional_observation(1)
        validate_simulation_observation(observation)
        self.assertFalse(observation["accounting_complete"])
        self.assertEqual(observation["memory_model"], "owned-private-scratchpads")
        self.assertFalse(observation["resource_match_verified"])
        self.assertFalse(observation["matched_comparison_ready"])
        self.assertIsNone(observation["total_cycles"])
        self.assertEqual(
            observation["missing_accounting"],
            [
                "installation_cycles",
                "completion_cycles",
                "publication_cycles",
            ],
        )

    def test_incomplete_record_cannot_report_total(self) -> None:
        observation = static_graph_functional_observation(1)
        observation["total_cycles"] = 1860
        with self.assertRaisesRegex(SimulationAdapterError, "incomplete accounting"):
            validate_simulation_observation(observation)

    def test_completed_record_requires_full_semantic_counts(self) -> None:
        observation = static_graph_functional_observation(1)
        observation["useful_loads"] -= 1
        with self.assertRaisesRegex(SimulationAdapterError, "operation counts"):
            validate_simulation_observation(observation)

    def test_cancelled_record_cannot_publish_or_validate(self) -> None:
        observation = static_graph_cancelled_observation(1)
        self.assertEqual(observation["execution_cycles"], 17)
        self.assertEqual(observation["useful_loads"], 7)
        self.assertEqual(observation["useful_adds"], 5)
        self.assertEqual(observation["useful_stores"], 1)
        self.assertEqual(observation["validation_cycles"], 0)
        observation["output_published"] = True
        with self.assertRaisesRegex(SimulationAdapterError, "publish"):
            validate_simulation_observation(observation)

    def test_complete_accounting_total_is_derived(self) -> None:
        observation = static_graph_functional_observation(2)
        for field, value in {
            "installation_cycles": 64,
            "completion_cycles": 3,
            "publication_cycles": 2,
        }.items():
            observation[field] = value
        observation["missing_accounting"] = []
        observation["accounting_complete"] = True
        observation["total_cycles"] = 64 + 648 + 3072 + 3 + 512 + 2
        validate_simulation_observation(observation)

    def test_unmatched_memory_cannot_be_comparison_ready(self) -> None:
        observation = static_graph_functional_observation(2)
        observation["resource_match_verified"] = True
        with self.assertRaisesRegex(SimulationAdapterError, "RFC-0005 memory"):
            validate_simulation_observation(observation)

    def test_matched_readiness_requires_resources_and_complete_accounting(self) -> None:
        observation = static_graph_functional_observation(2)
        observation["memory_model"] = "matched-fixed-latency-banked-scratchpad"
        observation["resource_match_verified"] = True
        observation["matched_comparison_ready"] = True
        with self.assertRaisesRegex(SimulationAdapterError, "readiness"):
            validate_simulation_observation(observation)

    def test_cpu_semantics_do_not_imply_matched_memory(self) -> None:
        for implementation in (
            "rocket-in-order",
            "boom-ooo",
            "boom-ooo-disabled-diagnostic",
        ):
            observation = cpu_functional_observation(implementation, 4)
            self.assertTrue(observation["semantic_valid"])
            self.assertEqual(
                observation["memory_model"], "cache-backed-variable-latency"
            )
            self.assertFalse(observation["resource_match_verified"])
            self.assertFalse(observation["matched_comparison_ready"])
            self.assertEqual(observation["missing_accounting"], list(ACCOUNTING_PHASES))

    def test_shared_tlram_prototype_does_not_imply_fixed_latency(self) -> None:
        observation = cpu_functional_observation(
            "rocket-in-order",
            5,
            "shared-tilelink-banked-scratchpad-unverified-latency",
        )
        self.assertTrue(observation["semantic_valid"])
        self.assertFalse(observation["resource_match_verified"])
        self.assertFalse(observation["matched_comparison_ready"])

    def test_module_cli_emits_validated_json(self) -> None:
        import json
        import subprocess
        import sys

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "raveil.simulation_adapter",
                "--invocation",
                "3",
                "--status",
                "cancelled",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        observation = json.loads(completed.stdout)
        validate_simulation_observation(observation)
        self.assertEqual(observation["status"], "cancelled")

    def test_rtl_harness_and_host_runner_bind_the_owned_adapter(self) -> None:
        harness = RTL_HARNESS.read_text(encoding="utf-8")
        runner = HOST_RUNNER.read_text(encoding="utf-8")
        self.assertIn(simulation_adapter_contract_id(), harness)
        self.assertIn("accounting_complete=0", harness)
        self.assertIn("total_cycles=UNAVAILABLE", harness)
        self.assertEqual(runner.count("python3 -m raveil.simulation_adapter"), 3)


if __name__ == "__main__":
    unittest.main()
