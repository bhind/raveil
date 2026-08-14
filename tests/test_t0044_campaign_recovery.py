from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from raveil.controlled_run import ControlledRunError
from raveil.t0044_campaign import _seal_failed_raw
from raveil.t0044_campaign_recovery import (
    PRIMARY_VARIANTS,
    _verify_failed_evidence,
)
from raveil.t0044_repeated import _canonical_bytes, _sha256


ROOT = Path(__file__).resolve().parents[1]


def _failed_attempt(root: Path) -> tuple[Path, dict]:
    run = root / "failed-campaign256"
    raw = run / "raw"
    raw.mkdir(parents=True)
    base_manifest = b'{"base":"manifest"}\n'
    (raw / "frozen-manifest.json").write_bytes(base_manifest)
    primary_raw = {}
    records = []
    for variant in PRIMARY_VARIANTS:
        path = raw / f"{variant}.log"
        path.write_text(f"complete {variant}\n", encoding="utf-8")
        primary_raw[variant] = {
            "path": path.name, "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        records.append({"exit_code": 0, "log": path.name})
    diagnostic = raw / "boom-serialize-dispatch.log"
    diagnostic.write_text("partial diagnostic\n", encoding="utf-8")
    records.append({"exit_code": 124, "log": diagnostic.name})
    (raw / "commands.jsonl").write_bytes(b"".join(
        _canonical_bytes(record) + b"\n" for record in records))
    _seal_failed_raw(run, "campaign command failed with 124")
    recovery = {
        "authority": {"base_manifest_sha256": _sha256(raw / "frozen-manifest.json")},
        "incident": {
            "failed_run_id": run.name,
            "failed_raw_seal_sha256": _sha256(run / "failed-raw-seal.json"),
        },
        "primary_raw": primary_raw,
    }
    return run, recovery


class CampaignRecoveryTests(unittest.TestCase):
    def test_sealed_primary_is_imported_without_deterministic_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            failed, recovery = _failed_attempt(Path(directory))
            commands = _verify_failed_evidence(failed, recovery)
        self.assertEqual([record["exit_code"] for record in commands],
                         [0, 0, 0, 124])

    def test_changed_primary_log_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            failed, recovery = _failed_attempt(Path(directory))
            (failed / "raw/static-graph.log").write_text(
                "changed\n", encoding="utf-8")
            with self.assertRaises(ControlledRunError):
                _verify_failed_evidence(failed, recovery)

    def test_repeat_timeout_is_explicit_and_keeps_legacy_default(self) -> None:
        source = (ROOT / "hardware/chisel/run-owned-cpu-memory-smoke.sh").read_text(
            encoding="utf-8")
        self.assertIn(
            "repeat_timeout_seconds=${RAVEIL_REPEAT_TIMEOUT_SECONDS:-3600}",
            source,
        )
        self.assertIn(
            'timeout --foreground "$RAVEIL_REPEAT_TIMEOUT_SECONDS" "$sim"',
            source,
        )
        self.assertIn(
            '--env "RAVEIL_REPEAT_TIMEOUT_SECONDS=$repeat_timeout_seconds"',
            source,
        )


if __name__ == "__main__":
    unittest.main()
