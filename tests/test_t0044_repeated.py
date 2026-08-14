from __future__ import annotations

from pathlib import Path
import hashlib
import tempfile
import unittest

from raveil.controlled_run import (
    ControlledRunError,
    _input_words,
    owned_resource_tuple_id,
)
from raveil.static_region import static_stencil_oracle
from raveil.t0044_repeated import verify_graph_log
from raveil.t0044_repeated import load_manifest, seal_raw


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
        self.assertIn("li      sp, 0x80010000", startup)
        self.assertIn('timeout --foreground 3600 "$sim"', runner)
        self.assertIn("pending-completed-outer-raw-verification", runner)
        collector = (ROOT / "raveil/t0044_repeated.py").read_text()
        self.assertIn("completed command log did not drain required markers", collector)
        graph_runner = (
            ROOT / "hardware/chisel/run-static-stencil-rtl.sh"
        ).read_text()
        self.assertIn('if [ -n "$repeat_account" ]; then', graph_runner)
        self.assertIn('cat "$rtl_log"', graph_runner)
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
        self.assertIn("installation_writes=%d", overlay)
        self.assertIn("class RaveilRepeatedMatchedRocketConfig", configs)
        self.assertIn("class RaveilRepeatedMatchedSmallBoomConfig", configs)

    def test_manifest_loader_rejects_wrong_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text('{"schema":"raveil.t0044-repeated-manifest/v1",'
                            '"experiment_id":"EXP-0005"}\n')
            with self.assertRaises(ControlledRunError):
                load_manifest(path)

    def test_frozen_manifest_is_exact(self) -> None:
        path = (
            ROOT / "benchmarks/manifests/t0044-static-repeated-invocation-v1.json"
        )
        manifest = load_manifest(path)
        self.assertEqual(manifest["sampling"]["commissioning_accounts"], [1, 4])
        self.assertEqual(
            manifest["sampling"]["campaign_prefix_accounts"],
            [1, 4, 16, 64, 256],
        )
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "ce395548c48b269f72f82f9cc33c22b6fa2cddd29293aeb8b4c1c8bc47359968",
        )

    def test_raw_seal_is_single_use_and_binds_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            raw = run_dir / "raw"
            derived = run_dir / "derived"
            raw.mkdir(parents=True)
            derived.mkdir()
            (raw / "sample.log").write_text("raw\n")
            (derived / "report.json").write_text("{}\n")
            seal = seal_raw(run_dir)
            self.assertEqual(len(seal["files"]), 1)
            self.assertEqual(len(seal["derived_report_sha256"]), 64)
            with self.assertRaises(ControlledRunError):
                seal_raw(run_dir)


if __name__ == "__main__":
    unittest.main()
