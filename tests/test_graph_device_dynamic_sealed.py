from pathlib import Path
import os
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from raveil.graph_device_dynamic_sealed import GraphDeviceDynamicSealError, run_sealed, seal, verify

ROOT = Path(__file__).resolve().parents[1]
GRAPH = "tests/fixtures/graph_device_dynamic/fanout-five-live.json"
MAX_GRAPH = "tests/fixtures/graph_device_dynamic/cross-dilation-u32.json"
RELATIVE_GRAPH = "tests/fixtures/graph_device_dynamic/eight-neighbor-dilation-u32.json"


class GraphDeviceDynamicSealedTests(unittest.TestCase):
    def _resign(self, bundle: Path, changed: str) -> Path:
        """Forge a self-consistent inventory digest; semantic verification must reject it."""
        manifest = json.loads((bundle / "manifest.json").read_text("ascii"))
        data = (bundle / changed).read_bytes()
        manifest["files"][changed] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if changed == "request.bin": manifest["request_sha256"] = hashlib.sha256(data).hexdigest()
        if changed == "program.bin": manifest["program_sha256"] = "0" * 64
        if changed == "descriptor.json": manifest["descriptor_sha256"] = hashlib.sha256(data).hexdigest()
        raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        digest = hashlib.sha256(raw).hexdigest()
        (bundle / "manifest.json").write_bytes(raw)
        (bundle / "SEALED").write_text(digest + "\n", encoding="ascii")
        target = bundle.with_name(digest); bundle.rename(target)
        return target
    def test_auto_digest_bundle_is_closed_and_reseal_rejects(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()), patch("raveil.graph_device_dynamic_sealed._dynamic_parent", return_value=Path(directory).resolve()):
            result = seal(GRAPH, 3, ROOT)
            bundle = Path(result["path"])
            self.assertEqual(bundle.name, result["manifest_sha256"])
            self.assertEqual(verify(bundle, ROOT)["seal_sha256"], bundle.name)
            with self.assertRaisesRegex(GraphDeviceDynamicSealError, "already exists"):
                seal(GRAPH, 3, ROOT)

    def test_v1_and_v2_seals_verify_and_schema_pair_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
            v1 = Path(seal(GRAPH, 3, ROOT)["path"])
            v2 = Path(seal(MAX_GRAPH, 3, ROOT)["path"])
            self.assertEqual(verify(v1, ROOT)["manifest"]["version"], 1)
            self.assertEqual(verify(v2, ROOT)["manifest"]["version"], 2)
            manifest = json.loads((v2 / "manifest.json").read_text("ascii"))
            manifest["schema"] = "raveil.graph-device-dynamic-sealed/v1"
            raw = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
            (v2 / "manifest.json").write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            (v2 / "SEALED").write_text(digest + "\n", encoding="ascii")
            forged = v2.with_name(digest); v2.rename(forged)
            with self.assertRaisesRegex(GraphDeviceDynamicSealError, "version pair"):
                verify(forged, ROOT)

    def test_v3_is_rejected_before_sealed_transport_materialization(self):
        with tempfile.TemporaryDirectory() as directory, patch(
            "raveil.graph_device_dynamic_sealed._sealed_parent",
            return_value=Path(directory).resolve(),
        ):
            with self.assertRaisesRegex(GraphDeviceDynamicSealError, "version 3 remains simulation-only"):
                seal(RELATIVE_GRAPH, 9, ROOT)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_each_inventory_byte_fails_closed(self):
        for name in ("program.bin", "affine.bin", "input.bin", "seed-1.bin", "oracle.bin", "descriptor.json", "request.bin", "source.manifest", "graph_device_abi_generated.h", "graph_device_affine_generated.h", "graph_device_dag_generated.h", "graph_device_axi4lite_aperture_generated.h", "manifest.json", "SEALED"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
                data = (bundle / name).read_bytes()
                (bundle / name).write_bytes(bytes([data[0] ^ 1]) + data[1:])
                with self.assertRaises(GraphDeviceDynamicSealError):
                    verify(bundle, ROOT)

    def test_fd_materialization_uses_verified_snapshot_without_descriptor_parse(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()), patch("raveil.graph_device_dynamic_sealed._dynamic_parent", return_value=Path(directory).resolve()):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            verified = verify(bundle, ROOT)
            target = Path(directory) / "replay"; target.mkdir()
            fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
            from raveil.graph_device_dynamic_sealed import _materialize_verified_at
            with patch("raveil.graph_device_dynamic_sealed.json.loads", side_effect=AssertionError("descriptor reparse")):
                _materialize_verified_at(fd, verified)
            os.close(fd)
            self.assertEqual((target / "request.bin").read_bytes(), verified["request"])

    def test_extra_missing_symlink_and_hardlink_are_rejected(self):
        for mode in ("extra", "missing", "symlink", "hardlink"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
                leaf = bundle / "oracle.bin"
                if mode == "extra": (bundle / "extra").write_bytes(b"x")
                elif mode == "missing": leaf.unlink()
                elif mode == "symlink": leaf.unlink(); leaf.symlink_to(bundle / "input.bin")
                else: os.link(leaf, bundle / "oracle-copy.bin")
                with self.assertRaises(GraphDeviceDynamicSealError): verify(bundle, ROOT)

    def test_truncate_append_directory_parent_link_and_external_copy_fail_closed(self):
        for mode in ("truncate", "append", "directory", "parent-link", "external-copy"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
                parent = Path(directory).resolve()
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
                if mode == "truncate":
                    (bundle / "oracle.bin").write_bytes(b"")
                    target = bundle
                elif mode == "append":
                    with (bundle / "oracle.bin").open("ab") as stream: stream.write(b"x")
                    target = bundle
                elif mode == "directory":
                    (bundle / "oracle.bin").unlink(); (bundle / "oracle.bin").mkdir()
                    target = bundle
                elif mode == "parent-link":
                    # A lexical child of a symlinked parent is never admitted.
                    link = parent / "sealed-parent-link"; link.symlink_to(parent, target_is_directory=True)
                    target = link / bundle.name
                else:
                    external = parent / "external-copy"; os.mkdir(external)
                    target = external
                with self.assertRaises(GraphDeviceDynamicSealError): verify(target, ROOT)

    def test_self_consistent_forged_payload_or_metadata_is_not_authority(self):
        for changed in ("program.bin", "affine.bin", "input.bin", "request.bin"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
                raw = bytearray((bundle / changed).read_bytes()); raw[0] ^= 1; (bundle / changed).write_bytes(raw)
                forged = self._resign(bundle, changed)
                with self.assertRaises(GraphDeviceDynamicSealError): verify(forged, ROOT)

    def test_same_name_replacement_during_verification_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            from raveil.graph_device_dynamic_sealed import _read_at as real_read
            changed = False
            def raced(fd, name, limit=65536):
                nonlocal changed
                value = real_read(fd, name, limit)
                if not changed:
                    changed = True
                    leaf = bundle / "oracle.bin"; payload = leaf.read_bytes(); leaf.unlink(); leaf.write_bytes(payload)
                return value
            with patch("raveil.graph_device_dynamic_sealed._read_at", side_effect=raced):
                with self.assertRaisesRegex(GraphDeviceDynamicSealError, "changed while read"):
                    verify(bundle, ROOT)

    def test_real_verified_snapshot_never_reparses_descriptor_and_does_not_mutate_seal(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            before = {item.name: item.read_bytes() for item in bundle.iterdir()}
            verified = verify(bundle, ROOT)
            from raveil.graph_device_dynamic_sealed import _materialize_verified_at
            target = Path(directory).resolve() / "materialized"; target.mkdir()
            fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
            with patch("raveil.graph_device_dynamic_sealed.json.loads", side_effect=AssertionError("descriptor reparse")):
                _materialize_verified_at(fd, verified)
            os.close(fd)
            self.assertEqual(before, {item.name: item.read_bytes() for item in bundle.iterdir()})

    def test_mocked_runner_binds_complete_raw_evidence_and_rejects_bad_output(self):
        with tempfile.TemporaryDirectory() as directory, patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(directory).resolve()), patch("raveil.graph_device_dynamic_sealed._dynamic_parent", return_value=Path(directory).resolve()):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            def runner(argv, **_kwargs):
                request = Path(argv[2]); session = request.parent
                oracle = (request / "request-oracle.bin").read_bytes()
                (request / "private-output-fanout-five-live-seed-3.bin").write_bytes(oracle)
                (request / "fallback-output-fanout-five-live-seed-3.bin").write_bytes(oracle)
                for name in ("source.manifest", "abi.manifest", "rtl.manifest", "toolchain.txt", "device.log"):
                    (request / name).write_bytes(name.encode("ascii"))
                from raveil.graph_device_dynamic_sealed import _expected_runner_source_manifest
                (request / "source.manifest").write_bytes(_expected_runner_source_manifest(verify(bundle, ROOT)))
                # These are intentionally above ordinary evidence-leaf limits.
                (request / "axi-transcript.log").write_bytes(b"a" * 70000)
                simulator = b"s" * 70000; (request / "simulator.bin").write_bytes(simulator)
                digest = hashlib.sha256(simulator).hexdigest(); (request / "simulator.sha256").write_text(digest + "\n", encoding="ascii")
                marker = f"GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V1 status=PASS requests=1 same_simulator=1 invoked_once=1 rtl_emitted_once=1 simulator_built_once=1 rejected_before_axi=1 simulator_sha256={digest} path=artifacts/graph_device_axi4lite_dynamic/{session.name} evidence=rtl-simulation-functional performance=not-measured"
                return SimpleNamespace(returncode=0, stdout=marker + "\n")
            with patch("raveil.graph_device_dynamic_sealed.subprocess.run", side_effect=runner):
                receipt = run_sealed(bundle, ROOT)
            for key in ("graph_id", "seed", "affine", "descriptor_sha256", "program_sha256", "request_sha256", "source_sha256", "abi_sha256", "rtl_sha256", "toolchain_sha256", "simulator_sha256", "axi_trace_sha256", "oracle_sha256", "fallback_sha256", "output_sha256", "sealed_manifest_sha256"):
                self.assertIn(key, receipt)
            def bad_runner(argv, **kwargs):
                result = runner(argv, **kwargs)
                (Path(argv[2]) / "private-output-fanout-five-live-seed-3.bin").write_bytes(b"bad")
                return result
            with patch("raveil.graph_device_dynamic_sealed.subprocess.run", side_effect=bad_runner):
                with self.assertRaisesRegex(GraphDeviceDynamicSealError, "output differs"):
                    run_sealed(bundle, ROOT)


if __name__ == "__main__":
    unittest.main()
