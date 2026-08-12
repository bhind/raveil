from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "hardware" / "chisel" / "boom-pin.env"
FETCH = ROOT / "hardware" / "chisel" / "fetch-boom-reference.sh"
VERIFY = ROOT / "hardware" / "chisel" / "verify-boom-reference.sh"


class BoomReferenceTests(unittest.TestCase):
    def test_entrypoints_are_executable(self) -> None:
        self.assertNotEqual(FETCH.stat().st_mode & 0o111, 0)
        self.assertNotEqual(VERIFY.stat().st_mode & 0o111, 0)

    def test_pin_is_exact_and_has_license_hashes(self) -> None:
        fields = dict(
            line.split("=", 1)
            for line in PIN.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        )
        self.assertEqual(fields["CHIPYARD_TAG"], "1.11.0")
        self.assertEqual(len(fields["CHIPYARD_REVISION"]), 40)
        self.assertEqual(len(fields["BOOM_REVISION"]), 40)
        self.assertEqual(fields["BOOM_CONFIG"], "chipyard.SmallBoomConfig")
        self.assertEqual(fields["BOOM_DISABLE_OOO_CSR"], "0x7c1")
        self.assertEqual(fields["BOOM_DISABLE_OOO_MASK"], "0x8")
        self.assertEqual(len(fields["BOOM_LICENSE_SHA256"]), 64)
        self.assertEqual(len(fields["BOOM_SIFIVE_LICENSE_SHA256"]), 64)

    def test_fetch_is_fail_closed_and_source_only(self) -> None:
        source = FETCH.read_text(encoding="utf-8")
        self.assertIn("--filter=blob:none", source)
        self.assertIn("checkout --detach", source)
        self.assertIn("submodule update --init generators/boom", source)
        self.assertIn("--ignore-submodules=none", source)
        self.assertNotIn("submodule update --init --recursive", source)
        self.assertIn("performance=not-measured", source)

    def test_verify_records_diagnostic_not_structural_ablation(self) -> None:
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn("diagnostic=serialize-dispatch", source)
        self.assertIn("structures=retained", source)
        self.assertIn("disableOOO", source)
        self.assertIn("chickenCSRId = 0x7c1", source)

    def test_local_source_pin_when_available(self) -> None:
        boom = ROOT / "external" / "chipyard" / "generators" / "boom" / ".git"
        if not boom.exists():
            self.skipTest("ignored BOOM checkout is not present")
        completed = subprocess.run(
            [str(VERIFY)], cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("BOOM-SOURCE-REFERENCE-V1 status=OK", completed.stdout)
        self.assertIn("evidence=source-verification", completed.stdout)


if __name__ == "__main__":
    unittest.main()
