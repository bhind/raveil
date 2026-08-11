from pathlib import Path
import os
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOST_SCRIPT = ROOT / "hardware" / "chisel" / "run-rocket-reference.sh"
CONTAINER_SCRIPT = (
    ROOT / "hardware" / "chisel" / "rocket-reference-in-container.sh"
)
PIN_FILE = ROOT / "hardware" / "chisel" / "rocket-pin.env"


class RocketReferenceScriptTests(unittest.TestCase):
    def test_owned_entrypoints_are_executable(self) -> None:
        self.assertNotEqual(HOST_SCRIPT.stat().st_mode & 0o111, 0)
        self.assertNotEqual(CONTAINER_SCRIPT.stat().st_mode & 0o111, 0)

    def test_cache_volume_name_cannot_inject_mount_options(self) -> None:
        environment = dict(os.environ)
        environment["RAVEIL_ROCKET_NIX_VOLUME"] = "bad,target=elsewhere"
        completed = subprocess.run(
            [str(HOST_SCRIPT)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("contains an invalid character", completed.stderr)

    def test_reference_revision_matches_fetch_pin(self) -> None:
        pin = dict(
            line.split("=", 1)
            for line in PIN_FILE.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        )
        script = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(f"ROCKET_REVISION={pin['ROCKET_REVISION']}", script)
        self.assertIn(f"ROCKET_ORIGIN={pin['ROCKET_URL']}", script)

    def test_environment_is_immutable_and_avoids_upstream_shell_hook(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        inner = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "nixos/nix:2.13.3@sha256:"
            "1f8fa57de6f2f9ea5ea8d115b339fa68d2f98f20b59438bdb9d3a082ad64d4bf",
            host,
        )
        self.assertIn("platform=linux/amd64", host)
        self.assertIn('output_volume="${cache_volume}-mill-out-v1"', host)
        self.assertIn('user_cache_volume="${cache_volume}-user-cache-v1"', host)
        self.assertIn('*[!A-Za-z0-9_.-]*', host)
        self.assertIn("target=/rocket/out", host)
        self.assertIn("target=/root/.cache", host)
        self.assertIn("git+file://$ROCKET_SOURCE?rev=$ROCKET_REVISION", inner)
        self.assertIn("--option filter-syscalls false", inner)
        self.assertNotIn("--out", inner)
        self.assertNotIn("nix develop", inner)
        self.assertNotIn("pip install", inner)

    def test_smoke_remains_functional_and_non_claiming(self) -> None:
        script = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("DefaultSmallConfig", script)
        self.assertIn("DefaultConfig", script)
        self.assertIn("TEST_SUITE=rv64mi-p", script)
        self.assertIn("EXPECTED_TESTS=16", script)
        self.assertIn("evidence=rtl-simulation-functional", script)
        self.assertIn("graph_rtl=not-implemented", script)
        self.assertIn("performance=not-measured", script)


if __name__ == "__main__":
    unittest.main()
