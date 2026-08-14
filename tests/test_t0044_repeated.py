from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from raveil.controlled_run import (
    ControlledRunError,
    _input_words,
    owned_resource_tuple_id,
)
from raveil.static_region import static_stencil_oracle
from raveil.t0044_repeated import verify_graph_log


ROOT = Path(__file__).resolve().parents[1]


def _graph_log(account: int) -> str:
    sha = "a" * 64
    lines = [
        f"CONTROLLED-GRAPH-IDENTITY-V1 artifact_sha256={sha} toolchain_sha256={sha}"
    ]
    for invocation in range(1, account + 1):
        for index, word in enumerate(static_stencil_oracle(_input_words(invocation))):
            lines.append(
                "RAVEIL-CONTROLLED-OUTPUT-V1 "
                f"invocation={invocation} index={index} value={word:08x}"
            )
        lines.append(
            "RAVEIL-REPEATED-GRAPH-COMPLETE-V1 status=OK "
            f"invocation={invocation} seed={invocation} installation_cycles=0 "
            "staging_cycles=648 execution_cycles=3073 completion_cycles=1 "
            "validation_cycles=512 publication_cycles=0 total_cycles=4234 "
            "quiescence_before=1 quiescence_after=1 traffic_accepted=1536 "
            "traffic_completed=1536 traffic_pending=0 graph_traffic=1536 "
            f"unaccounted_window_traffic=0 resource_sha256={owned_resource_tuple_id()} "
            "resource_contract_verified=1 resource_equality_verified=0 "
            "comparison_eligible=0 performance=not-measured"
        )
        lines.append(
            "T0044-REPEATED-GRAPH-ACTIVITY-V1 "
            f"invocation={invocation} request_stall_cycles=0"
        )
    lines.append(
        "RAVEIL-REPEATED-GRAPH-ACCOUNT-V1 status=OK "
        f"account={account} installation_count=1 simulator_processes=1 "
        f"resets=1 artifact_reloads=0 total_cycles={4234 * account} "
        "performance=not-measured"
    )
    return "\n".join(lines) + "\n"


class RepeatedBoundaryTests(unittest.TestCase):
    def test_graph_four_inputs_are_one_ordered_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(_graph_log(4), encoding="utf-8")
            session = verify_graph_log(path, 4)
        self.assertEqual(session["installation_count"], 1)
        self.assertEqual(session["simulator_processes"], 1)
        self.assertEqual(session["resets"], 1)
        self.assertEqual(session["artifact_reloads"], 0)
        self.assertEqual(
            [record["invocation"] for record in session["observations"]],
            [1, 2, 3, 4],
        )
        self.assertEqual(session["prefix_total_cycles"], [4234, 8468, 12702, 16936])
        self.assertEqual(
            len({record["input_sha256"] for record in session["observations"]}),
            4,
        )

    def test_graph_output_corruption_fails_closed(self) -> None:
        text = _graph_log(1).replace("index=0 value=", "index=0 value=deadbeef # ", 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ControlledRunError):
                verify_graph_log(path, 1)

    def test_graph_duplicate_input_account_is_rejected(self) -> None:
        text = _graph_log(2).replace("invocation=2", "invocation=1")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(ControlledRunError):
                verify_graph_log(path, 2)

    def test_cpu_workload_uses_one_runtime_loop_and_one_tohost(self) -> None:
        source = (ROOT / "hardware/chisel/riscv_stencil_repeated.c").read_text()
        startup = (ROOT / "hardware/chisel/riscv_stencil_repeated.S").read_text()
        runner = (ROOT / "hardware/chisel/run-owned-cpu-memory-smoke.sh").read_text()
        self.assertIn("for (uint32_t seed = 1U", source)
        self.assertEqual(startup.count("sd      a0, 0(t0)"), 1)
        self.assertIn('timeout --foreground 3600 "$sim"', runner)
        self.assertNotIn("RAVEIL_STENCIL_SEED", source)

    def test_repeated_configs_preserve_owned_resource_shape(self) -> None:
        overlay = (
            ROOT / "hardware/chisel/chipyard-overlay/RaveilOwnedTLMemory.scala"
        ).read_text()
        configs = (
            ROOT / "hardware/chisel/chipyard-overlay/RaveilDCacheOriginTagger.scala"
        ).read_text()
        self.assertIn("validWords = Some(580)", overlay)
        self.assertIn("repeatedControlledRun = true", overlay)
        self.assertIn("class RaveilRepeatedMatchedRocketConfig", configs)
        self.assertIn("class RaveilRepeatedMatchedSmallBoomConfig", configs)


if __name__ == "__main__":
    unittest.main()
