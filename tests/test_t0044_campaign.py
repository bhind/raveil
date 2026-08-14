from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from raveil.controlled_run import _input_words, _word_digest
from raveil.static_region import static_stencil_oracle
from raveil.t0044_campaign import (
    FULL_ACCOUNT,
    PREFIXES,
    _seal_failed_raw,
    _tail_has_prefix,
    build_report,
)
from raveil.t0044_fixture import _observation, _session, verify_graph_log
from tests.test_t0044_fixture import _graph_log


ROOT = Path(__file__).resolve().parents[1]


def _sessions() -> dict[str, dict]:
    definitions = {
        "static-graph": (
            "static-graph", "StaticStencilRegion:d4bf9395a510385f:fixture-v1",
            "1" * 64, "2" * 64, 3072, 0, 648, 1, 512, 1536, False,
        ),
        "rocket-in-order": (
            "rocket-in-order",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedRocketConfig",
            "3" * 64, "4" * 64, 14539, 46186, 677, 16, 4339, 1056, False,
        ),
        "boom-ooo": (
            "boom-ooo",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig",
            "5" * 64, "6" * 64, 21893, 46285, 682, 14, 6631, 1056, False,
        ),
        "boom-serialize-dispatch": (
            "boom-ooo",
            "chipyard.raveil.RaveilFixtureRepeatedMatchedSmallBoomConfig",
            "7" * 64, "8" * 64, 70774, 46524, 786, 102, 15811, 1056, True,
        ),
    }
    sessions = {}
    toolchain = "9" * 64
    for variant, definition in definitions.items():
        (implementation, configuration, source, artifact, execution,
         installation, staging, completion, validation, traffic,
         diagnostic) = definition
        observations = []
        for invocation in range(1, FULL_ACCOUNT + 1):
            inputs = _input_words(invocation)
            output = _word_digest(static_stencil_oracle(inputs))
            phase = {
                "installation": installation if invocation == 1 else 0,
                "staging": 648 if invocation == 1 else staging,
                "execution": execution + (invocation & 1),
                "completion": completion,
                "validation": validation,
                "publication": 0,
            }
            observations.append(_observation(
                implementation, configuration, invocation, source, artifact,
                toolchain, phase, output, _word_digest(inputs), traffic,
            ))
        sessions[variant] = _session(observations, FULL_ACCOUNT, diagnostic)
    return sessions


class FullCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sessions = _sessions()

    def test_graph_parser_scales_past_commissioning_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.log"
            path.write_text(_graph_log(16), encoding="utf-8")
            session = verify_graph_log(path, 16)
        self.assertEqual(session["account"], 16)
        self.assertEqual(len(session["observations"]), 16)

    def test_one_full_session_derives_all_nested_prefixes(self) -> None:
        with mock.patch("raveil.t0044_campaign.BOOTSTRAP_RESAMPLES", 100):
            report = build_report(copy.deepcopy(self.sessions), "a" * 64)
        self.assertEqual(report["prefixes"], list(PREFIXES))
        self.assertEqual(set(report["prefix_summaries"]),
                         {str(prefix) for prefix in PREFIXES})
        self.assertEqual(
            report["prefix_summaries"]["256"]["candidate_rows"]
            ["static-graph"]["execution_transactions"]["exact"],
            [1536] * 256,
        )
        self.assertFalse(report["rfc0005_latency_decision"]
                         ["latency_no_go_triggered"])
        self.assertEqual(report["decision"],
                         "advance-partial-latency-traffic")

    def test_latency_threshold_fails_closed_to_early_no_go(self) -> None:
        sessions = copy.deepcopy(self.sessions)
        for observation in sessions["static-graph"]["observations"]:
            observation["phase_cycles"]["execution"] = 30000
            observation["window_cycles"] = 30000
            observation["total_cycles"] = sum(observation["phase_cycles"].values())
        with mock.patch("raveil.t0044_campaign.BOOTSTRAP_RESAMPLES", 100):
            report = build_report(sessions, "a" * 64)
        self.assertTrue(report["rfc0005_latency_decision"]
                        ["latency_no_go_triggered"])
        self.assertEqual(report["decision"], "early-no-go")

    def test_terminal_marker_detection_reads_only_tail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.log"
            path.write_text("prefix\nRAVEIL-FIXTURE-CPU-HOST-V1 status=OK\n",
                            encoding="utf-8")
            self.assertTrue(_tail_has_prefix(
                path, "RAVEIL-FIXTURE-CPU-HOST-V1"))
            self.assertFalse(_tail_has_prefix(path, "missing"))

    def test_failed_raw_is_sealed_without_derived_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / "failed"
            raw = run / "raw"
            raw.mkdir(parents=True)
            (raw / "candidate.log").write_text("failure\n", encoding="utf-8")
            _seal_failed_raw(run, "intentional")
            self.assertTrue((raw / "failure.json").is_file())
            self.assertTrue((run / "failed-raw-seal.json").is_file())
            self.assertFalse((run / "derived").exists())

    def test_exp0007_collector_remains_commissioning_only(self) -> None:
        source = (ROOT / "raveil/t0044_fixture.py").read_text(encoding="utf-8")
        self.assertIn("EXP-0007 commissioning account must be 1 or 4", source)
        self.assertIn("choices=(1, 4)", source)

if __name__ == "__main__":
    unittest.main()
