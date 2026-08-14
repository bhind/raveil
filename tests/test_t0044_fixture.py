from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from raveil.controlled_run import (
    ControlledRunError,
    _input_words,
    fixture_owned_resource_tuple,
    fixture_owned_resource_tuple_id,
)
from raveil.static_region import static_stencil_oracle
from raveil.t0044_fixture import RESOURCE_FIELDS, fixture_contract, verify_graph_log


ROOT = Path(__file__).resolve().parents[1]


def _graph_log(account: int) -> str:
    sha = "a" * 64
    resource = fixture_owned_resource_tuple_id()
    lines = [
        f"CONTROLLED-GRAPH-IDENTITY-V1 artifact_sha256={sha} toolchain_sha256={sha}"
    ]
    for invocation in range(1, account + 1):
        lines.append(
            "RAVEIL-FIXTURE-PHASE-V1 "
            f"invocation={invocation} from={'0' if invocation == 1 else '1'} "
            f"to=1 cycle={(invocation - 1) * 4233} "
            "accepted=0 completed=0 pending=0"
        )
        for index, word in enumerate(_input_words(invocation)):
            lines.append(
                "RAVEIL-FIXTURE-INPUT-V1 "
                f"invocation={invocation} seed={invocation} "
                f"index={index} data={word:08x}"
            )
        lines.append(
            "RAVEIL-FIXTURE-PHASE-V1 "
            f"invocation={invocation} from=1 to=2 "
            f"cycle={(invocation - 1) * 4233 + 648} "
            "accepted=324 completed=324 pending=0"
        )
        lines.append(
            "RAVEIL-FIXTURE-STAGING-V1 "
            f"invocation={invocation} seed={invocation} accepted=324 completed=324 "
            "writes=324 first_word=0 last_word=323 pending=0 "
            "candidate_accepted_before_release=0 release_count=1"
        )
        lines.append(
            "RAVEIL-FIXTURE-RESOURCE-V1 "
            f"invocation={invocation} resource_sha256={resource} " +
            " ".join(f"{key}={value}" for key, value in RESOURCE_FIELDS.items())
        )
        for index, word in enumerate(static_stencil_oracle(_input_words(invocation))):
            lines.append(
                "RAVEIL-CONTROLLED-OUTPUT-V1 "
                f"invocation={invocation} index={index} value={word:08x}"
            )
        lines.append(
            "RAVEIL-FIXTURE-REARM-V1 "
            f"invocation={invocation} from=4 to=1 "
            f"cycle={invocation * 4233} pending=0 "
            "validation_responses=256 rearm_count=1"
        )
        lines.append(
            "RAVEIL-FIXTURE-GRAPH-COMPLETE-V1 status=OK "
            f"invocation={invocation} seed={invocation} installation_cycles=0 "
            "staging_cycles=648 execution_cycles=3072 completion_cycles=1 "
            "validation_cycles=512 publication_cycles=0 total_cycles=4233 "
            "quiescence_before=1 quiescence_after=1 traffic_accepted=1536 "
            "traffic_completed=1536 traffic_pending=0 graph_traffic=1536 "
            f"unaccounted_window_traffic=0 resource_sha256={resource} "
            "resource_contract_verified=1 resource_equality_verified=0 "
            "comparison_eligible=0 performance=not-measured"
        )
        lines.append(
            "T0044-FIXTURE-GRAPH-ACTIVITY-V1 "
            f"invocation={invocation} request_stall_cycles=0 "
            "response_backpressure_cycles=0 read_transactions=1280 "
            "write_transactions=256 read_bytes=5120 write_bytes=1024 "
            "useful_loads=1280 useful_adds=1024 useful_stores=256 outputs=256 "
            "schedule_active_cycles=3072 launch_cycles=0 "
            "frontend_activity=unavailable rename_rob_issue_lsu=not-applicable"
        )
    lines.append(
        "RAVEIL-FIXTURE-GRAPH-ACCOUNT-V1 status=OK "
        f"account={account} installation_count=1 simulator_processes=1 "
        f"resets=1 artifact_reloads=0 total_cycles={4233 * account} "
        "performance=not-measured"
    )
    return "\n".join(lines) + "\n"


class FixtureBoundaryTests(unittest.TestCase):
    def _verify(self, text: str, account: int = 1) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(text, encoding="utf-8")
            verify_graph_log(path, account)

    def test_graph_fixture_four_fresh_inputs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(_graph_log(4), encoding="utf-8")
            session = verify_graph_log(path, 4)
        self.assertEqual(session["installation_count"], 1)
        self.assertEqual(session["artifact_reloads"], 0)
        self.assertEqual(
            [item["window_cycles"] for item in session["observations"]],
            [3072] * 4,
        )
        self.assertEqual(
            len({item["input_sha256"] for item in session["observations"]}), 4
        )

    def test_overlap_fails_closed(self) -> None:
        with self.assertRaises(ControlledRunError):
            self._verify(_graph_log(1).replace(
                "candidate_accepted_before_release=0",
                "candidate_accepted_before_release=1", 1))

    def test_input_byte_corruption_fails_closed(self) -> None:
        with self.assertRaises(ControlledRunError):
            self._verify(_graph_log(1).replace("index=0 data=", "index=0 data=deadbeef#", 1))

    def test_phase_reorder_or_early_release_fails_closed(self) -> None:
        for source, replacement in (
            ("cycle=648", "cycle=647"),
            ("from=1 to=2", "from=1 to=1"),
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ControlledRunError):
                    self._verify(_graph_log(1).replace(source, replacement, 1))

    def test_early_or_duplicate_rearm_fails_closed(self) -> None:
        for source, replacement in (
            ("validation_responses=256", "validation_responses=255"),
            ("rearm_count=1", "rearm_count=2"),
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ControlledRunError):
                    self._verify(_graph_log(1).replace(source, replacement, 1))

    def test_missing_or_duplicate_count_fails_closed(self) -> None:
        for source, replacement in (
            ("accepted=324 completed=324 writes=324",
             "accepted=323 completed=324 writes=324"),
            ("accepted=324 completed=324 writes=324",
             "accepted=324 completed=325 writes=324"),
            ("release_count=1", "release_count=2"),
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ControlledRunError):
                    self._verify(_graph_log(1).replace(source, replacement, 1))

    def test_order_output_access_and_pending_fail_closed(self) -> None:
        for source, replacement in (
            ("first_word=0", "first_word=1"),
            ("last_word=323", "last_word=324"),
            ("pending=0", "pending=1"),
        ):
            with self.subTest(replacement=replacement):
                with self.assertRaises(ControlledRunError):
                    self._verify(_graph_log(1).replace(source, replacement, 1))

    def test_resource_identity_drift_fails_closed(self) -> None:
        with self.assertRaises(ControlledRunError):
            self._verify(_graph_log(1).replace(
                fixture_owned_resource_tuple_id(), "0" * 64, 1))

    def test_resource_identity_binds_fixture_release_and_single_ingress(self) -> None:
        resource = fixture_owned_resource_tuple()
        provider = resource["staging_provider"]
        self.assertEqual(resource["request_ports"], 1)
        self.assertEqual(resource["maximum_outstanding_requests"], 1)
        self.assertEqual(provider["request_buffer_depth"], 0)
        self.assertEqual(provider["release_edge"], "response-consume-for-word-323")
        self.assertEqual(
            fixture_owned_resource_tuple_id(),
            "87be95fa8293da4b251675e9f81aea003e69e27ea6454a1d1db3c1611539e1f7",
        )
        contract = fixture_contract()
        self.assertEqual(contract["fixture_provider_window_cycles"], 648)
        self.assertEqual(
            contract["rearm_edge"], "validation-response-consume-for-word-255")

    def test_provider_is_shared_and_cpu_kernel_has_no_input_generator(self) -> None:
        provider = (ROOT / "hardware/chisel/chipyard-overlay/RaveilFixtureInputProvider.scala").read_text()
        graph = (ROOT / "hardware/chisel/StaticStencilRegion.scala").read_text()
        cpu = (ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala").read_text()
        kernel = (ROOT / "hardware/chisel/riscv_stencil_fixture_repeated.c").read_text()
        self.assertIn("class RaveilFixtureInputProvider", provider)
        self.assertIn("Module(new RaveilFixtureInputProvider)", graph)
        self.assertIn("fixtureCanStageReg", graph)
        self.assertIn("fixtureValidationResponsesReg === 255.U", graph)
        self.assertIn("Module(new RaveilFixtureInputProvider)", cpu)
        self.assertEqual(cpu.count("val memory = SyncReadMem"), 1)
        self.assertEqual(cpu.count("memory.write("), 1)
        self.assertIn("tl.a.ready := !busy && !fixtureBlocksCandidate", cpu)
        self.assertIn("provider.io.release", cpu)
        self.assertIn("tl.a.bits.user.keydata.map", cpu)
        self.assertIn('__asm__ volatile ("" ::: "memory")', kernel)
        self.assertNotIn("fence iorw", kernel)
        self.assertNotIn("2654435761", kernel)
        self.assertNotIn("input_words[index] =", kernel)


if __name__ == "__main__":
    unittest.main()
