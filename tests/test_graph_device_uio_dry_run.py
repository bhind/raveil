import builtins
from contextlib import contextmanager
import io
from pathlib import Path
import tempfile
import unittest
import inspect
from unittest.mock import patch

from raveil.graph_device_dynamic_sealed import GraphDeviceDynamicSealError, seal
from raveil.graph_device_uio_dry_run import handoff_verified_for_test, plan
import raveil.graph_device_uio_dry_run as dry_run_module


ROOT = Path(__file__).resolve().parents[1]
GRAPH = "tests/fixtures/graph_device_dynamic/fanout-five-live.json"


def _device_path(path):
    if isinstance(path, int):
        return None
    try:
        rendered = bytes(path).decode() if isinstance(path, bytes) else str(path)
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return rendered if rendered == "/dev/mem" or rendered.startswith("/dev/uio") else None


@contextmanager
def forbid_device_access():
    """Reject device opens/maps before delegating ordinary file operations."""
    real_os_open = dry_run_module.os.open
    real_builtin_open = builtins.open
    real_io_open = io.open
    ordinary_os_opens = []
    forbidden = []

    def guarded_os_open(path, flags, *args, **kwargs):
        device = _device_path(path)
        if device is not None:
            forbidden.append(("os.open", device, flags))
            raise AssertionError(f"forbidden device open: {device}")
        ordinary_os_opens.append((path, flags, kwargs.get("dir_fd")))
        return real_os_open(path, flags, *args, **kwargs)

    def guarded_open(real_open, api):
        def invoke(path, *args, **kwargs):
            device = _device_path(path)
            if device is not None:
                forbidden.append((api, device, args[0] if args else kwargs.get("mode", "r")))
                raise AssertionError(f"forbidden device open: {device}")
            return real_open(path, *args, **kwargs)
        return invoke

    def guarded_mmap(*args, **kwargs):
        forbidden.append(("mmap.mmap", args, kwargs))
        raise AssertionError("forbidden mmap")

    with patch("os.open", side_effect=guarded_os_open), \
            patch("builtins.open", side_effect=guarded_open(real_builtin_open, "builtins.open")), \
            patch("io.open", side_effect=guarded_open(real_io_open, "io.open")), \
            patch("mmap.mmap", side_effect=guarded_mmap):
        yield ordinary_os_opens, forbidden


class GraphDeviceUioDryRunTests(unittest.TestCase):
    def test_verified_plan_stops_before_open_mmap_or_mmio(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "sealed"
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                result = plan(bundle, "/dev/uio17", ROOT)
            self.assertEqual(result["device_opened"], 0)
            self.assertEqual(result["mmap"], 0)
            self.assertEqual(result["mmio"], 0)
            self.assertEqual(result["aperture_bytes"], 0x4000)
            self.assertEqual(result["performance"], "not-measured")

    def test_invalid_device_or_unverified_payload_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "sealed"
            with patch("raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()):
                bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/mem", ROOT)
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/uio00", ROOT)
            with self.assertRaisesRegex(ValueError, "canonical"):
                plan(bundle, "/dev/uio0/x", ROOT)
            (bundle / "program.bin").write_bytes(b"x")
            with self.assertRaises(GraphDeviceDynamicSealError):
                plan(bundle, "/dev/uio0", ROOT)

    def test_plan_module_has_no_transport_syscall_or_mapping_import(self):
        source = inspect.getsource(plan)
        self.assertNotIn("import mmap", source)
        self.assertNotIn("os.open", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("/dev/mem", source)

    def test_plan_and_valid_handoff_allow_files_but_never_open_or_map_device(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()
        ), patch(
            "raveil.graph_device_dynamic_sealed._dynamic_parent", return_value=Path(temporary).resolve()
        ):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            calls = []
            with forbid_device_access() as (ordinary_os_opens, forbidden):
                result = plan(bundle, "/dev/uio17", ROOT)
                projected = handoff_verified_for_test(
                    bundle, "/dev/uio17", ROOT,
                    lambda device, root: calls.append((device, root)),
                )

            self.assertEqual(result["device_opened"], 0)
            self.assertEqual(calls, [("/dev/uio17", projected)])
            self.assertEqual(forbidden, [])
            self.assertTrue(any(dir_fd is not None for _, _, dir_fd in ordinary_os_opens))
            repository_opens = [flags for path, flags, _ in ordinary_os_opens if Path(path) == ROOT]
            self.assertTrue(repository_opens)
            self.assertTrue(all(flags & (dry_run_module.os.O_WRONLY | dry_run_module.os.O_RDWR) == 0
                                for flags in repository_opens))
            self.assertEqual((projected / "request.bin").read_bytes(), (bundle / "request.bin").read_bytes())

    def test_tampered_handoff_calls_runner_zero_times_without_device_access(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "raveil.graph_device_dynamic_sealed._sealed_parent", return_value=Path(temporary).resolve()
        ), patch(
            "raveil.graph_device_dynamic_sealed._dynamic_parent", return_value=Path(temporary).resolve()
        ):
            bundle = Path(seal(GRAPH, 3, ROOT)["path"])
            (bundle / "program.bin").write_bytes(b"tampered")
            calls = []
            with forbid_device_access() as (_, forbidden):
                with self.assertRaises(GraphDeviceDynamicSealError):
                    handoff_verified_for_test(
                        bundle, "/dev/uio9", ROOT,
                        lambda *_: calls.append("called"),
                    )
            self.assertEqual(calls, [])
            self.assertEqual(forbidden, [])

    def test_instrumented_python_open_apis_and_mmap_reject_device_paths_before_call(self):
        with forbid_device_access() as (_, forbidden):
            for opener in (
                lambda: dry_run_module.os.open("/dev/uio4", dry_run_module.os.O_RDONLY),
                lambda: builtins.open("/dev/mem", "rb"),
                lambda: Path("/dev/uio5").open("rb"),
            ):
                with self.assertRaisesRegex(AssertionError, "forbidden device open"):
                    opener()
            import mmap
            with self.assertRaisesRegex(AssertionError, "forbidden mmap"):
                mmap.mmap(-1, 4096)
        self.assertEqual([entry[0] for entry in forbidden],
                         ["os.open", "builtins.open", "io.open", "mmap.mmap"])


if __name__ == "__main__":
    unittest.main()
