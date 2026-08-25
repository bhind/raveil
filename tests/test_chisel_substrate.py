from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOST_SCRIPT = ROOT / "hardware" / "chisel" / "run-rocket-reference.sh"
CONTAINER_SCRIPT = (
    ROOT / "hardware" / "chisel" / "rocket-reference-in-container.sh"
)
PIN_FILE = ROOT / "hardware" / "chisel" / "rocket-pin.env"
BOOM_RUNNERS = [
    ROOT / "hardware/chisel" / name
    for name in (
        "export-physical-rocket-rtl.sh",
        "run-boom-functional-smoke.sh",
        "run-boom-stencil-functional.sh",
        "run-exp0011-rtl-export.sh",
        "run-g1c-active-common-owned-memory.sh",
        "run-g1d-rocket-fallback-owned-memory.sh",
        "run-g1e-runtime-selector.sh",
        "run-owned-cpu-memory-smoke.sh",
        "run-rocket-stencil-functional.sh",
        "run-shared-scratchpad-stencil-functional.sh",
        "run-tlram-latency-observer.sh",
    )
]
BOOM_VERIFIER = ROOT / "hardware" / "chisel" / "verify-boom-functional-sim-image.sh"
BOOM_BUILDER = ROOT / "hardware" / "chisel" / "build-boom-functional-sim-image.sh"


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

    def test_boom_runners_use_only_pinned_read_only_image(self) -> None:
        forbidden = ("docker build", "docker buildx", "docker tag", "docker pull", "raveil-boom-functional-sim:v1")
        for path in BOOM_RUNNERS:
            source = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, source, path.name)
            self.assertIn("verify-boom-functional-sim-image.sh", source)
            self.assertLess(source.index("verify-boom-functional-sim-image.sh"), source.index("docker run"))
            if 'image=' in source:
                self.assertRegex(
                    source,
                    r'image=\$\("\$repo_root/hardware/chisel/verify-boom-functional-sim-image\.sh"\)',
                )
            else:
                self.assertRegex(
                    source,
                    r'runtime_image_id=\$\((\"\$repo_root/hardware/chisel/verify-boom-functional-sim-image\.sh\"|\"\$image_verifier\")\)',
                )
            self.assertNotIn("awk -F= '$1==\"RUNTIME_IMAGE_ID\"", source)
            docker_runs = source.count("docker run")
            isolated_runs = source.count("--network none")
            if path.name == "run-boom-functional-smoke.sh":
                self.assertEqual(docker_runs, 3)
                self.assertEqual(isolated_runs, 2)
            else:
                self.assertEqual(isolated_runs, docker_runs, path.name)

        shared_tag_users = [
            path.name
            for path in (ROOT / "hardware" / "chisel").glob("*.sh")
            if "raveil-boom-functional-sim:v1" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(shared_tag_users, [])

    def test_boom_image_contract_and_builder_are_explicit(self) -> None:
        verifier = BOOM_VERIFIER.read_text(encoding="utf-8")
        builder = BOOM_BUILDER.read_text(encoding="utf-8")
        self.assertIn("expected_payload=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822", verifier)
        self.assertIn("expected_platform=linux/amd64", verifier)
        self.assertIn("expected_config_view=32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522", verifier)
        self.assertIn("expected_rootfs=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c", verifier)
        self.assertIn("{{json .Config}}", verifier)
        self.assertIn("{{.Descriptor.digest}}|{{.Descriptor.mediaType}}|{{.Descriptor.size}}", verifier)
        self.assertIn("docker buildx history inspect", verifier)
        self.assertIn("docker buildx build", builder)
        self.assertIn("--provenance=mode=min", builder)
        self.assertIn("--iidfile", builder)
        self.assertNotIn("--tag", builder)
        self.assertIn("docker buildx history inspect", builder)
        self.assertIn('"RUNTIME_DESCRIPTOR_SIZE=$descriptor_size"', builder)
        self.assertIn('"BUILD_REF=$build_ref_short"', builder)
        self.assertNotIn("BUILD_REF=metadata", builder)
        self.assertLess(
            builder.index('verified_image_id=$("$verifier" "$tmp_receipt")'),
            builder.index('mkdir -m 0700 "$record_dir"'),
        )
        self.assertLess(
            builder.index('mkdir -m 0700 "$record_dir"'),
            builder.index('mv "$tmp_receipt" "$record_dir/receipt"'),
        )
        self.assertIn("boom-functional-sim-image.current", builder)

    def test_boom_scripts_are_executable(self) -> None:
        for path in [*BOOM_RUNNERS, BOOM_VERIFIER, BOOM_BUILDER]:
            self.assertNotEqual(path.stat().st_mode & 0o111, 0, path.name)

    def test_boom_receipt_parser_rejects_malformed_records_before_docker(self) -> None:
        valid_lines = [
            "SCHEMA=raveil.boom-functional-sim-image/v2",
            "RUNTIME_IMAGE_ID=sha256:" + "a" * 64,
            "RUNTIME_DESCRIPTOR_DIGEST=sha256:" + "a" * 64,
            "RUNTIME_DESCRIPTOR_MEDIA_TYPE=application/vnd.oci.image.index.v1+json",
            "RUNTIME_DESCRIPTOR_SIZE=856",
            "PAYLOAD_MANIFEST=sha256:9009a923ce829097efacd97fe62cbef79dfdcafc70dc435d4bf5e1a66fdaf822",
            "PAYLOAD_MEDIA_TYPE=application/vnd.oci.image.manifest.v1+json",
            "CONFIG_VIEW_SHA256=32a509e843f24ac9a49c679f967a4626a6614f158775e352f3b38fdc7d8ed522",
            "ROOTFS_LAYERS_SHA256=154dc63d7967ea4dce962f002ee10be12f598b5358f6b0ffc524a80d72bb8b9c",
            "PLATFORM=linux/amd64",
            "BUILD_REF=abcdefghijklmnopqrstuvwxy",
        ]
        mutations = {
            "missing": valid_lines[:-1],
            "unknown": [*valid_lines, "UNKNOWN=value"],
            "duplicate": [*valid_lines, valid_lines[-1]],
            "empty": [*valid_lines[:-1], "BUILD_REF="],
        }
        with tempfile.TemporaryDirectory() as directory:
            fake_docker = Path(directory) / "docker"
            fake_docker.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
            fake_docker.chmod(0o700)
            environment = dict(os.environ)
            environment["PATH"] = f"{directory}:{environment['PATH']}"
            for name, lines in mutations.items():
                receipt = Path(directory) / f"{name}.receipt"
                receipt.write_text("\n".join(lines) + "\n", encoding="utf-8")
                completed = subprocess.run(
                    [str(BOOM_VERIFIER), str(receipt)],
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 11, name)
                self.assertIn("receipt malformed", completed.stderr, name)

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
