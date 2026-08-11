from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import raveil
from raveil.backend import ToyDaphnis
from raveil.experience import ExperienceStore
from raveil.model import Context, seed_candidates
from raveil.policy import NearestExperiencePolicy, Tuner


def make_tuner(store: ExperienceStore) -> Tuner:
    return Tuner(ToyDaphnis(), store, NearestExperiencePolicy(), seed_candidates())


class MinimumLoopTests(unittest.TestCase):
    def test_exact_version(self) -> None:
        self.assertEqual(raveil.__version__, "0.0000000000002")

    def test_experience_is_append_only_and_active_memory_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experience.jsonl"
            store = ExperienceStore(path, active_limit=8)
            tuner = make_tuner(store)
            for shape in range(128, 128 + 24 * 32, 32):
                tuner.tune(Context("branching-mlp", shape, 32), budget=2)

            self.assertEqual(store.cold_count, 48)
            self.assertLessEqual(store.active_count, 8)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 48)
            self.assertTrue(all(json.loads(line)["schema"].startswith("raveil.experience/") for line in lines))

            reloaded = ExperienceStore(path, active_limit=8)
            self.assertEqual(reloaded.cold_count, 48)
            self.assertLessEqual(reloaded.active_count, 8)

    def test_nearby_experience_improves_two_measurement_search(self) -> None:
        warm_store = ExperienceStore(active_limit=64)
        warm_tuner = make_tuner(warm_store)
        for shape in (256, 512, 1024, 2048):
            warm_tuner.tune(Context("branching-mlp", shape, 32), budget=3)

        target = Context("branching-mlp", 1536, 32)
        cold = make_tuner(ExperienceStore(active_limit=64)).tune(target, budget=2)
        warm = warm_tuner.tune(target, budget=2)

        self.assertEqual(cold.best.candidate.candidate_id, "vector8")
        self.assertEqual(warm.best.candidate.candidate_id, warm.oracle.candidate.candidate_id)
        self.assertGreater(warm.headroom_capture, cold.headroom_capture)

    def test_low_memory_experience_avoids_known_invalid_keep_candidate(self) -> None:
        store = ExperienceStore(active_limit=64)
        tuner = make_tuner(store)
        for shape in (512, 1024, 2048):
            tuner.tune(Context("branching-mlp", shape, 8), budget=4)
        result = tuner.tune(Context("branching-mlp", 1536, 8), budget=2)
        self.assertTrue(result.best.metrics.valid)
        self.assertNotEqual(result.trials[1].candidate.candidate_id, "vector16")

    def test_experience_load_rejects_missing_or_duplicate_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experience.jsonl"
            store = ExperienceStore(path, active_limit=8)
            tuner = make_tuner(store)
            tuner.tune(Context("branching-mlp", 128, 32), budget=2)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            records[1]["sequence"] = records[0]["sequence"]
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expected sequence 2"):
                ExperienceStore(path, active_limit=8)

    def test_experience_load_rejects_corrupt_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experience.jsonl"
            path.write_text("{broken\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 1"):
                ExperienceStore(path, active_limit=8)


if __name__ == "__main__":
    unittest.main()
