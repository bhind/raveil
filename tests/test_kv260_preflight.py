from argparse import Namespace
import hashlib
import io
import os
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import stat
import tempfile
import unittest

from raveil import cli
from raveil.kv260_preflight import (
    Kv260PreflightError,
    collect_preflight,
    render_preflight,
)


class Kv260PreflightTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path]:
        proc_root = root / "proc"
        sys_root = root / "sys"
        (proc_root / "device-tree").mkdir(parents=True)
        (proc_root / "device-tree" / "model").write_bytes(
            b"Xilinx Kria KV260 Vision AI Starter Kit\0"
        )
        uio_root = sys_root / "class" / "uio" / "uio0"
        (uio_root / "maps" / "map0").mkdir(parents=True)
        (uio_root / "dev").write_text("240:0\n", encoding="ascii")
        (uio_root / "maps" / "map0" / "addr").write_text(
            "0xa0000000\n", encoding="ascii"
        )
        (uio_root / "maps" / "map0" / "size").write_text(
            "0x4000\n", encoding="ascii"
        )
        manager = sys_root / "class" / "fpga_manager" / "fpga0"
        manager.mkdir(parents=True)
        (manager / "state").write_text("operating\n", encoding="ascii")
        return proc_root, sys_root

    @staticmethod
    def character_device(*, major: int = 240, minor: int = 0):
        return SimpleNamespace(
            st_mode=stat.S_IFCHR | 0o600,
            st_rdev=os.makedev(major, minor),
        )

    def inspect(self, proc_root: Path, sys_root: Path, **changes):
        arguments = {
            "system": "linux",
            "machine": "aarch64",
            "kernel_release": "6.8.0-xilinx",
            "proc_root": proc_root,
            "sys_root": sys_root,
            "lstat_fn": lambda path: self.character_device(),
        }
        arguments.update(changes)
        return collect_preflight("/dev/uio0", **arguments)

    def test_valid_target_is_observed_without_device_open(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            proc_root, sys_root = self.fixture(Path(temporary))
            calls = []

            def inspect(path):
                calls.append(path)
                return self.character_device()

            value = self.inspect(proc_root, sys_root, lstat_fn=inspect)
        self.assertEqual(calls, ["/dev/uio0"])
        self.assertEqual(value["machine"], "aarch64")
        self.assertEqual(value["kernel"], "6.8.0-xilinx")
        self.assertEqual(value["uio"], "/dev/uio0")
        self.assertEqual(value["device"], "240:0")
        self.assertEqual(value["map0_addr"], "0xa0000000")
        self.assertEqual(value["map0_size"], "0x4000")
        self.assertEqual(value["fpga_manager_state"], "operating")
        self.assertEqual(
            value["model_sha256"],
            hashlib.sha256(b"Xilinx Kria KV260 Vision AI Starter Kit\0").hexdigest(),
        )

    def test_platform_and_device_identity_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            proc_root, sys_root = self.fixture(Path(temporary))
            cases = (
                ("non-linux", {"system": "darwin"}, "requires Linux"),
                ("non-arm64", {"machine": "x86_64"}, "requires Linux aarch64"),
                ("bad-kernel", {"kernel_release": "bad release"}, "kernel release"),
                ("regular-device", {"lstat_fn": lambda path: SimpleNamespace(
                    st_mode=stat.S_IFREG | 0o600, st_rdev=0)}, "not a character"),
                ("minor-mismatch", {"lstat_fn": lambda path: self.character_device(minor=1)},
                 "path number differs"),
                ("identity-mismatch", {"lstat_fn": lambda path: self.character_device(major=241)},
                 "identities differ"),
            )
            for label, changes, message in cases:
                with self.subTest(label=label), self.assertRaisesRegex(
                    Kv260PreflightError, message
                ):
                    self.inspect(proc_root, sys_root, **changes)
            for unsafe in ("uio0", "/tmp/uio0", "/dev/uio00", "/dev/uio0/extra"):
                with self.subTest(path=unsafe), self.assertRaisesRegex(
                    Kv260PreflightError, "canonical /dev/uioN"
                ):
                    collect_preflight(
                        unsafe,
                        system="linux",
                        machine="aarch64",
                        kernel_release="6.8.0-xilinx",
                        proc_root=proc_root,
                        sys_root=sys_root,
                        lstat_fn=lambda path: self.character_device(),
                    )

    def test_target_properties_fail_closed(self) -> None:
        def rejected(label, relative, content, message):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                proc_root, sys_root = self.fixture(Path(temporary))
                base = proc_root if relative.parts[0] == "device-tree" else sys_root
                (base / relative).write_bytes(content)
                with self.assertRaisesRegex(Kv260PreflightError, message):
                    self.inspect(proc_root, sys_root)

        rejected("model", Path("device-tree/model"), b"Other board\0", "not KV260")
        rejected("model-nul", Path("device-tree/model"), b"KV260", "NUL-terminated")
        rejected("model-oversized", Path("device-tree/model"), b"KV260" + b"x" * 508,
                 "oversized")
        rejected("sysfs-id", Path("class/uio/uio0/dev"), b"240:00\n", "malformed")
        rejected("address", Path("class/uio/uio0/maps/map0/addr"), b"0xa0000001\n",
                 "0x4000-aligned")
        rejected("address-format", Path("class/uio/uio0/maps/map0/addr"), b"a0000000\n",
                 "canonical hexadecimal")
        rejected("size", Path("class/uio/uio0/maps/map0/size"), b"0x2000\n",
                 "exactly 0x4000")
        rejected("manager", Path("class/fpga_manager/fpga0/state"), b"bad/state\n",
                 "bounded printable")

    def test_missing_manager_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            proc_root, sys_root = self.fixture(Path(temporary))
            (sys_root / "class" / "fpga_manager" / "fpga0" / "state").unlink()
            with self.assertRaisesRegex(Kv260PreflightError, "unavailable"):
                self.inspect(proc_root, sys_root)

    def test_cli_reports_expected_host_failure_without_traceback(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            ["graph-device", "kv260-preflight", "--device", "/dev/uio0"]
        )
        stderr = io.StringIO()
        with mock.patch(
            "raveil.cli.render_preflight",
            side_effect=Kv260PreflightError("expected target property is missing"),
        ), mock.patch("sys.stderr", stderr):
            self.assertEqual(args.handler(args), 2)
        self.assertEqual(
            stderr.getvalue(),
            "kv260-preflight: expected target property is missing\n"
        )

    def test_success_marker_is_deterministic_and_explicitly_read_only(self) -> None:
        observed = {
            "machine": "aarch64",
            "kernel": "6.8.0-xilinx",
            "model_sha256": "a" * 64,
            "uio": "/dev/uio0",
            "device": "240:0",
            "map0_addr": "0xa0000000",
            "map0_size": "0x4000",
            "fpga_manager_state": "operating",
        }
        with mock.patch(
            "raveil.kv260_preflight.collect_preflight", return_value=observed
        ):
            marker = render_preflight("/dev/uio0")
        self.assertEqual(
            marker,
            "KV260-PREFLIGHT-V1 status=PASS machine=aarch64 "
            "kernel=6.8.0-xilinx model_sha256=" + "a" * 64 +
            " uio=/dev/uio0 device=240:0 map0_addr=0xa0000000 "
            "map0_size=0x4000 fpga_manager_state=operating "
            "device_opened=0 mmio=0 evidence=target-host-observation "
            "performance=not-measured",
        )

    def test_source_has_no_uio_open_or_mapping_primitive(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "raveil/kv260_preflight.py").read_text()
        self.assertNotIn("os.open", source)
        self.assertNotIn("mmap", source)
        self.assertNotIn("read32", source)
        self.assertNotIn("write32", source)
        self.assertIn("inspect_stat(device)", source)


if __name__ == "__main__":
    unittest.main()
