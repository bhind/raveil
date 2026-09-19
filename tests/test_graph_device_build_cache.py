"""Host-functional cache boundaries; these tests claim no RTL execution."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from raveil.graph_device_build_cache import BuildCache, BuildCacheError, MEMBERS, _json
from raveil.graph_device_build_cache import finish, identity, HEADERS
from raveil.graph_device_dynamic import _marker, GraphDeviceDynamicError


class BuildCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        for name in MEMBERS:
            (self.source / name).write_bytes(name.encode())
        (self.source / "identity.json").write_bytes(_json({"identity": "fixture"}))
        self.key = hashlib.sha256((self.source / "identity.json").read_bytes()).hexdigest()
        self.cache = BuildCache(self.root / "cache")

    def test_miss(self):
        self.assertIsNone(self.cache.read(self.key))
        self.assertFalse(self.cache.stage(self.key, self.root / "staged"))
        self.assertFalse((self.root / "staged").exists())

    def test_publish_stage_only_build_members(self):
        (self.source / "private-output.bin").write_bytes(b"must not copy")
        self.assertTrue(self.cache.publish(self.key, self.source))
        self.assertTrue(self.cache.stage(self.key, self.root / "staged"))
        self.assertEqual({p.name for p in (self.root / "staged").iterdir()}, {*MEMBERS, "bundle.sha256"})
        self.assertEqual((self.root / "staged/simulator.bin").read_bytes(), b"simulator.bin")
        self.assertEqual((self.cache.root.stat().st_mode & 0o777), 0o700)

    def test_existing_never_replaced(self):
        self.cache.publish(self.key, self.source)
        (self.source / "simulator.bin").write_bytes(b"different")
        self.assertFalse(self.cache.publish(self.key, self.source))
        self.assertEqual(self.cache.read(self.key)["simulator.bin"], b"simulator.bin")

    def test_wrong_identity(self):
        with self.assertRaises(BuildCacheError):
            self.cache.publish("0" * 64, self.source)

    def test_whole_valid_bundle_at_wrong_key(self):
        self.cache.publish(self.key, self.source)
        (self.cache.root / self.key).rename(self.cache.root / ("0" * 64))
        with self.assertRaises(BuildCacheError):
            self.cache.read("0" * 64)

    def test_corrupt_binary(self):
        self.cache.publish(self.key, self.source)
        (self.cache.root / self.key / "simulator.bin").write_bytes(b"corrupt")
        with self.assertRaises(BuildCacheError):
            self.cache.read(self.key)

    def test_unexpected_member(self):
        self.cache.publish(self.key, self.source)
        (self.cache.root / self.key / "output.bin").write_bytes(b"x")
        with self.assertRaises(BuildCacheError):
            self.cache.read(self.key)

    def test_symlink_entry(self):
        (self.cache.root / self.key).symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(BuildCacheError):
            self.cache.read(self.key)

    def test_symlink_member(self):
        (self.source / "simulator.bin").unlink()
        (self.source / "simulator.bin").symlink_to(self.source / "source.manifest")
        with self.assertRaises((OSError, BuildCacheError)):
            self.cache.publish(self.key, self.source)

    def test_hardlink_member(self):
        os.link(self.source / "simulator.bin", self.source / "linked")
        with self.assertRaises(BuildCacheError):
            self.cache.publish(self.key, self.source)

    def test_fifo_member(self):
        (self.source / "simulator.bin").unlink()
        os.mkfifo(self.source / "simulator.bin")
        with self.assertRaises(BuildCacheError):
            self.cache.publish(self.key, self.source)

    def test_capacity_does_not_evict(self):
        with patch("raveil.graph_device_build_cache.MAX_ENTRIES", 1):
            abandoned = self.cache.root / "stage.abandoned"
            abandoned.mkdir(mode=0o700)
            self.assertFalse(self.cache.publish(self.key, self.source))
            self.assertTrue(abandoned.exists())

    def test_byte_budget(self):
        with patch("raveil.graph_device_build_cache.LIMIT", 1):
            with self.assertRaises(BuildCacheError):
                self.cache.publish(self.key, self.source)

    def test_exact_payload_cap_and_manifest_allowance(self):
        total = sum((self.source / name).stat().st_size for name in MEMBERS)
        with patch("raveil.graph_device_build_cache.LIMIT", total):
            self.assertTrue(self.cache.publish(self.key, self.source))
            manifest_size = (self.cache.root / self.key / "manifest.json").stat().st_size
            self.assertLessEqual(manifest_size, 8192)
            self.assertEqual(sum(p.stat().st_size for p in (self.cache.root / self.key).iterdir()), total + manifest_size)
            (self.source / "simulator.bin").write_bytes(b"simulator.bin+")
            with self.assertRaises(BuildCacheError):
                self.cache.publish(self.key, self.source)

    def test_concurrent_publication(self):
        with concurrent.futures.ThreadPoolExecutor(2) as workers:
            results = list(workers.map(lambda _: self.cache.publish(self.key, self.source), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(self.cache.read(self.key)["simulator.bin"], b"simulator.bin")
        self.assertEqual({p.name for p in self.cache.root.iterdir()}, {self.key, "lock"})

    def test_private_root_required(self):
        self.cache.root.chmod(0o755)
        with self.assertRaises(BuildCacheError):
            BuildCache(self.cache.root)

    def test_invalid_key(self):
        for key in ("../source", "x" * 64, "A" * 64):
            with self.assertRaises(BuildCacheError):
                self.cache.read(key)

    def test_changed_dependencies_prevent_publication(self):
        context = {"dependencies": "0" * 64, "key": self.key, "cache": self.cache, "hit": False}
        with patch("raveil.graph_device_build_cache.dependency_digest", return_value="1" * 64):
            with self.assertRaisesRegex(BuildCacheError, "dependency identity changed"):
                finish(context, self.root, self.root, self.source)
        self.assertIsNone(self.cache.read(self.key))

    def test_changed_source_prevents_publication(self):
        context = {"dependencies": "0" * 64, "key": self.key, "cache": self.cache, "hit": False}
        with patch("raveil.graph_device_build_cache.dependency_digest", return_value="0" * 64), \
                patch("raveil.graph_device_build_cache.identity", return_value=b"changed"):
            with self.assertRaisesRegex(BuildCacheError, "source identity changed"):
                finish(context, self.root, self.root, self.source)
        self.assertIsNone(self.cache.read(self.key))

    def test_reuse_marker_requires_host_staged_hit(self):
        line = ("GraphDevice-AXI4LITE-DYNAMIC-EVIDENCE-V2 status=PASS requests=1 "
                "same_simulator=1 invoked_once=1 rtl_emitted_once=0 simulator_built_once=0 "
                "build_reused=1 rejected_before_axi=1 simulator_sha256=" + "a" * 64 +
                " path=artifacts/graph_device_axi4lite_dynamic/run.12345678 "
                "evidence=rtl-simulation-functional performance=not-measured")
        session = Path("run.12345678")
        self.assertEqual(_marker(line, session, 1, reused=True), line)
        with self.assertRaises(GraphDeviceDynamicError):
            _marker(line, session, 1)
        with self.assertRaises(GraphDeviceDynamicError):
            _marker(line.replace("simulator_built_once=0", "simulator_built_once=1"), session, 1, reused=True)

    def test_source_header_image_dependency_invalidation(self):
        for relative in ("raveil/graph_device_build_cache.py", "hardware/chisel/build-cache-dependencies.sh"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"source")
        for name in HEADERS:
            (self.source / name).write_bytes(b"header")
        with patch("raveil.graph_device_dynamic_sealed.SOURCE_PATHS", ()):
            original = identity(self.root, self.source, "0" * 64)
            self.assertNotEqual(original, identity(self.root, self.source, "1" * 64))
            with patch("raveil.graph_device_build_cache.IMAGE", "another-image"):
                self.assertNotEqual(original, identity(self.root, self.source, "0" * 64))
            for name in HEADERS:
                (self.source / name).write_bytes(b"changed")
                self.assertNotEqual(original, identity(self.root, self.source, "0" * 64))
                (self.source / name).write_bytes(b"header")
            (self.root / "raveil/graph_device_build_cache.py").write_bytes(b"changed")
            self.assertNotEqual(original, identity(self.root, self.source, "0" * 64))


if __name__ == "__main__":
    unittest.main()
