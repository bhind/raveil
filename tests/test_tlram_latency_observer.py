import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from raveil.tlram_latency_observer import (
    TlramLatencyObserverError,
    parse_observer_log,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "hardware" / "chisel" / "run-tlram-latency-observer.sh"
OBSERVER = ROOT / "hardware" / "chisel" / "tlram_endpoint_latency_observer.sv"
MARKER = (
    "TLRAM-ENDPOINT-LATENCY-OBSERVER-V1 "
    "instance=TOP.bank.raveil_tlram_endpoint_latency_observer "
    "transactions=7 reads=4 writes=3 other=0 input_region=2 output_region=4 "
    "other_region=1 min_cycles=2 max_cycles=5 "
    "variable=1 unmatched=0 source_reuse=0 pending=0 "
    "evidence=rtl-simulation-functional-diagnostic performance=not-measured "
    "fixed_latency_claim=0 resource_match_verified=0"
)


class TlramLatencyObserverTests(unittest.TestCase):
    def test_runner_and_bind_preserve_functional_only_boundary(self) -> None:
        self.assertNotEqual(RUNNER.stat().st_mode & 0o111, 0)
        runner = RUNNER.read_text(encoding="utf-8")
        observer = OBSERVER.read_text(encoding="utf-8")
        completed = subprocess.run(
            ["sh", "-n", str(RUNNER)], capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("model_dir=", runner)
        self.assertNotIn("clean-sim", runner)
        self.assertIn("--network none", runner)
        self.assertIn("bind TLRAM", observer)
        self.assertNotIn("bind ScratchpadBank", observer)
        self.assertIn("performance=not-measured", observer)
        self.assertIn("fixed_latency_claim=0", observer)
        self.assertIn("resource_match_verified=0", observer)

    def test_valid_diagnostic_stays_non_claiming(self) -> None:
        result = parse_observer_log(MARKER, "rocket-in-order")
        self.assertEqual(result["transactions"], 7)
        self.assertTrue(result["variable_observed_latency"])
        self.assertFalse(result["performance_claim"])
        self.assertFalse(result["fixed_latency_claim"])
        self.assertFalse(result["resource_match_verified"])
        self.assertFalse(result["matched_comparison_ready"])
        self.assertTrue(result["write_path_observed"])
        self.assertFalse(result["initiator_and_phase_attribution_available"])

    def test_rejects_consistency_failure(self) -> None:
        marker = MARKER.replace("pending=0", "pending=1")
        with self.assertRaisesRegex(TlramLatencyObserverError, "pending"):
            parse_observer_log(marker, "boom-ooo")

    def test_rejects_ambiguous_marker(self) -> None:
        with self.assertRaisesRegex(TlramLatencyObserverError, "exactly one"):
            parse_observer_log(f"{MARKER}\n{MARKER}", "rocket-in-order")

    def test_rejects_address_region_mismatch(self) -> None:
        marker = MARKER.replace("other_region=1", "other_region=2")
        with self.assertRaisesRegex(TlramLatencyObserverError, "address-region"):
            parse_observer_log(marker, "rocket-in-order")

    def test_rejects_zero_or_invalid_latency(self) -> None:
        with self.assertRaisesRegex(TlramLatencyObserverError, "no completed"):
            parse_observer_log(
                MARKER.replace("transactions=7", "transactions=0")
                .replace("reads=4", "reads=0")
                .replace("writes=3", "writes=0")
                .replace("input_region=2", "input_region=0")
                .replace("output_region=4", "output_region=0")
                .replace("other_region=1", "other_region=0"),
                "rocket-in-order",
            )
        with self.assertRaisesRegex(TlramLatencyObserverError, "latency range"):
            parse_observer_log(
                MARKER.replace("min_cycles=2", "min_cycles=0"), "rocket-in-order"
            )
        with self.assertRaisesRegex(TlramLatencyObserverError, "variability"):
            parse_observer_log(MARKER.replace("variable=1", "variable=0"), "boom-ooo")

    def test_rejects_wrong_implementation_or_instance_boundary(self) -> None:
        with self.assertRaisesRegex(TlramLatencyObserverError, "unsupported"):
            parse_observer_log(MARKER, "unknown")
        with self.assertRaisesRegex(TlramLatencyObserverError, "instance boundary"):
            parse_observer_log(
                MARKER.replace(
                    "raveil_tlram_endpoint_latency_observer", "different_monitor"
                ),
                "rocket-in-order",
            )

    def test_cli_emits_canonical_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "observer.log"
            log.write_text(f"boot\n{MARKER}\ndone\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "raveil.tlram_latency_observer",
                    "--log",
                    str(log),
                    "--implementation",
                    "boom-ooo-disabled-diagnostic",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["schema"], "raveil.tlram-endpoint-latency-observer/v1")
        self.assertEqual(result["implementation"], "boom-ooo-disabled-diagnostic")
        self.assertEqual(result["transactions"], 7)
        self.assertEqual(result["minimum_observed_cycles"], 2)
        self.assertEqual(result["maximum_observed_cycles"], 5)
        self.assertEqual(result["evidence_class"], "rtl-simulation-functional-diagnostic")
        self.assertFalse(result["performance_claim"])
        self.assertFalse(result["fixed_latency_claim"])
        self.assertFalse(result["resource_match_verified"])
        self.assertFalse(result["matched_comparison_ready"])


if __name__ == "__main__":
    unittest.main()
