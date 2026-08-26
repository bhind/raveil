import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import raveil.graph_device_submit as submit
from raveil.graph_device_submit import (
    CATALOGUE,
    GraphDeviceSubmissionError,
    admit,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "contracts/graph_device_dags/five-point.json"
ENVELOPE_KEYS = {
    "schema", "task", "slice", "graph_path", "graph_id", "descriptor_sha256",
    "program_sha256", "seed", "evidence_class", "execution", "non_claims",
}
NON_CLAIMS = [
    "rtl-simulation", "arbitrary-graph", "general-graph", "performance", "latency",
    "throughput", "resource", "area", "energy", "emulation", "kv260", "fpga",
    "asic", "silicon", "novelty", "patent", "legal-clearance", "data-publication",
    "experience-authority", "production-security",
]


class GraphDeviceSubmitTests(unittest.TestCase):
    def test_admits_exact_canonical_descriptor_without_execution(self) -> None:
        result = admit(CANONICAL, 7)
        self.assertEqual(result["schema"], "raveil.graph-device-submission/v1")
        self.assertEqual(set(result), ENVELOPE_KEYS)
        self.assertEqual(result["task"], "T-0128")
        self.assertEqual(result["slice"], "S01")
        self.assertEqual(result["graph_path"], CANONICAL)
        self.assertEqual(result["graph_id"], "five-point")
        self.assertEqual(result["descriptor_sha256"], CATALOGUE[CANONICAL]["descriptor_sha256"])
        self.assertEqual(result["program_sha256"], CATALOGUE[CANONICAL]["program_sha256"])
        self.assertEqual(result["seed"], 7)
        self.assertEqual(result["evidence_class"], "host-functional")
        self.assertEqual(result["execution"], "not-started")
        self.assertEqual(result["non_claims"], NON_CLAIMS)

    def test_rejects_noncanonical_paths_and_invalid_seed(self) -> None:
        for graph in (
            "/tmp/five-point.json", "./" + CANONICAL,
            "contracts/graph_device_dags/../graph_device_dags/five-point.json",
            "contracts/graph_device_dags/unknown.json",
        ):
            with self.subTest(graph=graph), self.assertRaises(GraphDeviceSubmissionError):
                admit(graph, 1)
        for seed in (-1, 0x1_0000_0000):
            with self.subTest(seed=seed), self.assertRaises(GraphDeviceSubmissionError):
                admit(CANONICAL, seed)

    def test_rejects_symlink_and_byte_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in CATALOGUE:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            target = root / CANONICAL
            target.write_bytes(target.read_bytes() + b"\n")
            with self.assertRaises(GraphDeviceSubmissionError):
                admit(CANONICAL, 1, root)
            target.write_bytes((ROOT / CANONICAL).read_bytes())
            link = root / "contracts" / "graph_device_dags" / "five-point.json"
            link.unlink()
            try:
                link.symlink_to(ROOT / CANONICAL)
            except OSError as error:
                self.skipTest(f"symbolic links unavailable: {error}")
            with self.assertRaises(GraphDeviceSubmissionError):
                admit(CANONICAL, 1, root)

    def test_rejects_malformed_and_extra_field_descriptor_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in CATALOGUE:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((ROOT / relative).read_bytes())
            target = root / CANONICAL
            target.write_bytes(b"{not-json}\n")
            with self.assertRaises(GraphDeviceSubmissionError):
                admit(CANONICAL, 1, root)
            descriptor = json.loads((ROOT / CANONICAL).read_text(encoding="ascii"))
            descriptor["unexpected"] = True
            target.write_text(json.dumps(descriptor), encoding="ascii")
            with self.assertRaises(GraphDeviceSubmissionError):
                admit(CANONICAL, 1, root)

    def test_rejects_duplicate_catalogue_identity_after_entry_validation(self) -> None:
        original = dict(CATALOGUE)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = ROOT / CANONICAL
                raw = source.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                duplicate = {
                    "descriptor_sha256": digest,
                    "graph_id": "five-point",
                    "program_sha256": original[CANONICAL]["program_sha256"],
                }
                paths = (
                    "contracts/graph_device_dags/one.json",
                    "contracts/graph_device_dags/two.json",
                )
                for relative in paths:
                    destination = root / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(raw)
                CATALOGUE.clear()
                CATALOGUE.update({relative: dict(duplicate) for relative in paths})
                with self.assertRaisesRegex(GraphDeviceSubmissionError, "duplicate identity"):
                    admit(paths[0], 1, root)
        finally:
            CATALOGUE.clear()
            CATALOGUE.update(original)

    def test_cli_emits_deterministic_json_and_rejects_without_traceback(self) -> None:
        command = [sys.executable, "-m", "raveil", "graph-device", "submit", "--graph", CANONICAL, "--seed", "7"]
        first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(json.loads(first.stdout)["execution"], "not-started")
        rejected = subprocess.run(
            command[:-3] + ["--graph", "unknown.json", "--seed", "7"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("error:", rejected.stderr)
        self.assertNotIn("Traceback", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
