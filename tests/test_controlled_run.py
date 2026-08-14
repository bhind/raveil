from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from raveil.controlled_run import (
    ControlledRunError,
    aggregate_controlled_logs,
    aggregate_controlled_observations,
    controlled_run_contract_id,
    owned_resource_tuple,
    owned_resource_tuple_id,
    static_graph_controlled_observation,
    validate_controlled_observation,
    verify_cpu_log,
    verify_static_graph_log,
)
from raveil.riscv_stencil_signature import input_words
from raveil.static_region import static_stencil_oracle


class ControlledRunTests(unittest.TestCase):
    graph_artifact_sha256 = "a" * 64
    graph_toolchain_sha256 = "b" * 64

    def _graph_observation(
        self, invocation: int, seed: int
    ) -> dict[str, object]:
        return static_graph_controlled_observation(
            invocation, seed,
            self.graph_artifact_sha256, self.graph_toolchain_sha256,
        )

    def _cpu_observation(
        self, implementation: str, invocation: int
    ) -> dict[str, object]:
        resource = owned_resource_tuple_id()
        log_text = "\n".join((
            "RAVEIL-CONTROLLED-PHASE-V1 from=0 to=1 cycle=       100 accepted=       580 completed=       580 busy_before=0",
            "RAVEIL-CONTROLLED-PHASE-V1 from=1 to=2 cycle=200 accepted=904 completed=904 busy_before=1",
            f"RAVEIL-CONTROLLED-RESOURCE-V1 resource_sha256={resource} data_width_bits=32 operation_width_bytes=4 request_ports=1 response_ports=1 maximum_outstanding_requests=1 request_buffer_depth=0 response_buffer_depth=1 physical_banks=1 physical_words=1024 valid_words=580 arbitration=none-at-owned-contract-ingress accepted_operations=read,write-byte-mask response_rule=one-module-local-cycle-after-acceptance response_hold=stable-until-consumed",
            "RAVEIL-CONTROLLED-PHASE-V1 from=2 to=3 cycle=1200 accepted=1960 completed=1960 busy_before=1",
            "RAVEIL-CONTROLLED-WINDOW-V1 start_cycle=       200 end_cycle=      1200 cycles=      1000 accepted=      1056 completed=      1056 reads=       800 writes=       256 expected_accepted=      1056 expected_completed=      1056 unexpected_accepted=         0 unexpected_completed=         0 origin_accepted=      1056 origin_completed=      1056 nonorigin_accepted=         0 nonorigin_completed=         0 pending=0 quiescence_before=1 quiescence_after=1",
            "RAVEIL-CONTROLLED-PHASE-V1 from=3 to=4 cycle=1210 accepted=1960 completed=1960 busy_before=0",
            "RAVEIL-CONTROLLED-PHASE-V1 from=4 to=5 cycle=1400 accepted=2216 completed=2216 busy_before=1",
            "RAVEIL-CONTROLLED-CPU-COMPLETE-V1 installation_cycles=100 staging_cycles=100 execution_cycles=1000 completion_cycles=10 validation_cycles=190 publication_cycles=0 total_cycles=1400 accepted=2216 completed=2216 staging_writes=324 execution_reads=800 execution_writes=256 validation_reads=256",
        )) + "\n"
        signature_text = "".join(
            f"{word:08x}\n"
            for word in static_stencil_oracle(input_words(1))
        )
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "cpu.log"
            signature = Path(directory) / "cpu.signature"
            log.write_text(log_text, encoding="utf-8")
            signature.write_text(signature_text, encoding="ascii")
            return verify_cpu_log(
                log, signature, implementation, invocation,
                "1" * 64, "2" * 64, "3" * 64,
                {
                    "rocket-in-order": "chipyard.raveil.RaveilMatchedRocketConfig",
                    "boom-ooo": "chipyard.raveil.RaveilMatchedSmallBoomConfig",
                }[implementation],
            )

    def test_resource_tuple_is_exact_and_hash_bound(self) -> None:
        resource = owned_resource_tuple()
        self.assertEqual(resource["request_ports"], 1)
        self.assertEqual(resource["response_ports"], 1)
        self.assertEqual(resource["data_width_bits"], 32)
        self.assertEqual(resource["byte_mask_bits"], 4)
        self.assertEqual(resource["operation_width_bytes"], 4)
        self.assertEqual(resource["maximum_outstanding_requests"], 1)
        self.assertEqual(resource["request_buffer_depth"], 0)
        self.assertEqual(resource["response_buffer_depth"], 1)
        self.assertEqual(resource["physical_banks"], 1)
        self.assertEqual(resource["physical_words"], 1024)
        self.assertEqual(resource["valid_words"], 580)
        self.assertEqual(len(resource["regions"]), 2)
        self.assertEqual(len(owned_resource_tuple_id()), 64)
        self.assertEqual(len(controlled_run_contract_id()), 64)

    def test_first_graph_slice_is_complete_but_peer_ineligible(self) -> None:
        record = self._graph_observation(1, 1)
        validate_controlled_observation(record)
        self.assertEqual(record["total_cycles"], 4234)
        self.assertEqual(record["traffic_accepted"], 1536)
        self.assertEqual(record["traffic_completed"], 1536)
        self.assertEqual(
            record["semantic_operations"],
            {"reads": 1280, "writes": 256, "outputs": 256},
        )
        self.assertTrue(record["resource_contract_verified"])
        self.assertFalse(record["resource_equality_verified"])
        self.assertFalse(record["comparison_eligible"])

    def test_oracle_and_input_identities_change_with_seed(self) -> None:
        first = self._graph_observation(1, 1)
        second = self._graph_observation(2, 3)
        self.assertNotEqual(first["input_sha256"], second["input_sha256"])
        self.assertNotEqual(
            first["oracle_output_sha256"], second["oracle_output_sha256"]
        )

    def test_mutations_fail_closed(self) -> None:
        baseline = self._graph_observation(1, 1)
        mutations = []
        for field, value in (
            ("observed_output_sha256", "0" * 64),
            ("unaccounted_window_traffic", 1),
            ("traffic_completed", 1535),
            ("resource_equality_verified", True),
            ("artifact_sha256", "0" * 63),
            ("toolchain_sha256", "0" * 64),
            ("performance_claim", True),
        ):
            changed = deepcopy(baseline)
            changed[field] = value
            mutations.append(changed)
        changed = deepcopy(baseline)
        changed["phase_cycles"]["completion"] = 2
        mutations.append(changed)
        changed = deepcopy(baseline)
        changed["traffic"]["debug"] = 1
        mutations.append(changed)
        changed = deepcopy(baseline)
        changed["semantic_operations"]["reads"] = 1279
        mutations.append(changed)
        for mutation in mutations:
            with self.assertRaises(ControlledRunError):
                validate_controlled_observation(mutation)

    def test_resource_identity_and_fail_closed_marker_are_source_bound(self) -> None:
        root = Path(__file__).resolve().parents[1]
        resource = owned_resource_tuple_id()
        graph_source = (
            root / "hardware/chisel/static_stencil_sim_main.cpp"
        ).read_text(encoding="utf-8")
        cpu_source = (
            root
            / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
        ).read_text(encoding="utf-8")
        self.assertIn(resource, graph_source)
        self.assertIn(resource, cpu_source)
        self.assertIn("admitted unaccounted traffic", cpu_source)
        self.assertIn("quiescence_before=1 quiescence_after=1", cpu_source)
        self.assertIn(
            "tl.a.bits.size === log2Ceil(beatBytes).U", cpu_source
        )

    def test_exact_rtl_markers_bind_to_records(self) -> None:
        records = []
        for invocation, seed in ((1, 1), (3, 3)):
            observation = self._graph_observation(invocation, seed)
            phases = observation["phase_cycles"]
            records.append(
                "CONTROLLED-GRAPH-WINDOW-V1 status=OK "
                f"invocation={invocation} seed={seed} "
                f"installation_cycles={phases['installation']} "
                f"staging_cycles={phases['staging']} "
                f"execution_cycles={phases['execution']} "
                f"completion_cycles={phases['completion']} "
                f"validation_cycles={phases['validation']} "
                f"publication_cycles={phases['publication']} "
                f"total_cycles={observation['total_cycles']} "
                "quiescence_before=1 quiescence_after=1 "
                f"traffic_accepted={observation['traffic_accepted']} "
                f"traffic_completed={observation['traffic_completed']} "
                "traffic_pending=0 "
                f"graph_traffic={observation['traffic']['graph']} "
                "unaccounted_window_traffic=0 "
                f"resource_sha256={observation['resource_sha256']} "
                "resource_contract_verified=1 resource_equality_verified=0 "
                "comparison_eligible=0 performance=not-measured"
            )
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "static.log"
            baseline = (
                "CONTROLLED-GRAPH-IDENTITY-V1 "
                f"artifact_sha256={self.graph_artifact_sha256} "
                f"toolchain_sha256={self.graph_toolchain_sha256}\n"
                + "\n".join(records) + "\n"
            )
            log.write_text(baseline, encoding="utf-8")
            self.assertEqual(len(verify_static_graph_log(log)), 2)
            for mutation in (
                baseline.replace("traffic_pending=0", "traffic_pending=1", 1),
                baseline.replace("quiescence_before=1", "quiescence_before=0", 1),
                baseline.replace(self.graph_artifact_sha256, "0" * 63, 1),
                baseline + records[0] + "\n",
            ):
                log.write_text(mutation, encoding="utf-8")
                with self.assertRaises(ControlledRunError):
                    verify_static_graph_log(log)

    def test_cpu_log_binds_optimized_frozen_traffic(self) -> None:
        rocket = self._cpu_observation("rocket-in-order", 2)
        self.assertEqual(rocket["traffic_accepted"], 1056)
        self.assertEqual(rocket["traffic"]["cpu"], 1056)
        self.assertEqual(rocket["semantic_operations"]["reads"], 1280)
        self.assertEqual(rocket["phase_cycles"]["execution"], 1000)
        self.assertFalse(rocket["comparison_eligible"])

    def test_cpu_log_accepts_chisel_decimal_padding(self) -> None:
        baseline = self._cpu_observation("rocket-in-order", 2)
        self.assertEqual(baseline["total_cycles"], 1400)
        self.assertEqual(baseline["traffic_accepted"], 1056)

    def test_three_way_aggregate_promotes_resource_equality_only(self) -> None:
        graph = self._graph_observation(1, 1)
        rocket = self._cpu_observation("rocket-in-order", 2)
        boom = self._cpu_observation("boom-ooo", 3)
        aggregate = aggregate_controlled_observations([graph, rocket, boom])
        self.assertTrue(aggregate["resource_equality_verified"])
        self.assertTrue(aggregate["comparison_eligible"])
        self.assertFalse(aggregate["dynamic_memory_traffic_equal"])
        self.assertFalse(aggregate["t0044_measurement_claim_ready"])
        self.assertFalse(aggregate["performance_claim"])
        self.assertEqual(set(aggregate["artifacts"]), {
            "static-graph", "rocket-in-order", "boom-ooo"
        })
        self.assertEqual(set(aggregate["toolchains"]), {
            "static-graph", "rocket-in-order", "boom-ooo"
        })
        self.assertEqual(set(aggregate["configuration_ids"]), {
            "static-graph", "rocket-in-order", "boom-ooo"
        })

        for mutation in (
            [graph, rocket],
            [graph, rocket, deepcopy(rocket)],
        ):
            with self.assertRaises(ControlledRunError):
                aggregate_controlled_observations(mutation)
        changed = deepcopy(boom)
        changed["traffic_pending"] = 1
        with self.assertRaises(ControlledRunError):
            aggregate_controlled_observations([graph, rocket, changed])
        changed = deepcopy(boom)
        changed["resource_sha256"] = "0" * 64
        with self.assertRaises(ControlledRunError):
            aggregate_controlled_observations([graph, rocket, changed])

    def test_wrapper_logs_select_graph_seed_one_and_exact_cpu_peers(self) -> None:
        graph_one = self._graph_observation(1, 1)
        graph_three = self._graph_observation(3, 3)
        rocket = self._cpu_observation("rocket-in-order", 2)
        boom = self._cpu_observation("boom-ooo", 3)
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("graph", "rocket", "boom")]
            paths[0].write_text(
                "noise\n" + "\n".join(
                    json.dumps(value, sort_keys=True)
                    for value in (graph_one, graph_three)
                ) + "\n",
                encoding="utf-8",
            )
            for path, value in zip(paths[1:], (rocket, boom), strict=True):
                path.write_text(
                    json.dumps(value, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            aggregate = aggregate_controlled_logs(paths)
            self.assertTrue(aggregate["comparison_eligible"])


if __name__ == "__main__":
    unittest.main()
