import json
from pathlib import Path
import tempfile
import unittest

from raveil import t0044_pilot


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks/manifests/t0044-static-latency-traffic-pilot-v1.json"


class T0044PilotTests(unittest.TestCase):
    def test_frozen_manifest_is_exact(self) -> None:
        value = t0044_pilot.load_manifest(MANIFEST)
        self.assertEqual(value["sampling"]["pilot_accounts"], [1, 4])
        self.assertEqual(value["workload"]["fresh_input_seeds"], [1, 2, 3, 4])
        self.assertTrue(value["decision_rules"]["pilot_cannot_decide_go"])

    def test_existing_run_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(t0044_pilot.PilotError):
                t0044_pilot.collect(
                    ROOT, Path(directory), MANIFEST, ROOT / "external/chipyard"
                )

    def test_marker_rejects_duplicates(self) -> None:
        with self.assertRaises(t0044_pilot.PilotError):
            t0044_pilot._marker(
                "T0044-CPU-ACTIVITY-V1 a=1\nT0044-CPU-ACTIVITY-V1 a=1\n",
                "T0044-CPU-ACTIVITY-V1",
            )

    def test_marker_accepts_rtl_fixed_width_decimal_spacing(self) -> None:
        self.assertEqual(
            t0044_pilot._marker(
                "T0044-CPU-ACTIVITY-V1 stalls=          0 reads=800\n",
                "T0044-CPU-ACTIVITY-V1",
            ),
            {"stalls": "0", "reads": "800"},
        )

    def test_marker_rejects_unparsed_payload(self) -> None:
        with self.assertRaises(t0044_pilot.PilotError):
            t0044_pilot._marker(
                "T0044-CPU-ACTIVITY-V1 stalls=0 stray reads=800\n",
                "T0044-CPU-ACTIVITY-V1",
            )

    def test_raw_seal_requires_report_and_is_single_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            raw_dir = run_dir / "raw"
            derived_dir = run_dir / "derived"
            raw_dir.mkdir()
            derived_dir.mkdir()
            (raw_dir / "evidence.log").write_text("raw\n", encoding="utf-8")
            with self.assertRaises(t0044_pilot.PilotError):
                t0044_pilot.seal_raw(run_dir)
            (derived_dir / "report.json").write_text("{}\n", encoding="utf-8")
            seal = t0044_pilot.seal_raw(run_dir)
            self.assertEqual(seal["files"][0]["path"], "evidence.log")
            with self.assertRaises(t0044_pilot.PilotError):
                t0044_pilot.seal_raw(run_dir)

    def test_manifest_is_canonical_json_object(self) -> None:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(value["schema"], t0044_pilot.SCHEMA)


if __name__ == "__main__":
    unittest.main()
