import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from raveil import graph_device_axi4lite_export as rtl
from raveil import graph_device_board_bundle as board


class BoardBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=board.ROOT / "artifacts")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = self.root / "core"
        rtl.prepare(self.core)
        generated = self.core / "generated-src"; generated.mkdir()
        # Packaging fixture only. Actual behavioral checks use the real core in Verilator.
        data = b"module GraphDeviceAxi4LiteTop; endmodule\n"
        (generated / "GraphDeviceAxi4LiteTop.sv").write_bytes(data)
        manifest = "GraphDeviceAxi4LiteTop.sv " + hashlib.sha256(data).hexdigest() + "\n"
        for name in ("rtl.manifest", "rtl-repeat.manifest"):
            (self.core / name).write_text(manifest)
        (self.core / "toolchain.txt").write_text("Scala CLI version: packaging fixture\njava test\n")
        rtl.finalize(self.core, "sha256:" + "a" * 64)
        self.output = self.root / "board"

    def make(self, **kwargs):
        return board.create(self.core, self.output, base=kwargs.get("base", 0xa0000000), clock_mhz=kwargs.get("clock_mhz", 100))

    def rehash(self):
        path = self.output / "manifest.json"
        data = json.loads(path.read_text())
        data["files"] = rtl._tree(self.output, omit_manifest=True)
        path.write_bytes(rtl._canonical(data))

    def test_roundtrip_extreme_windows_and_repeat(self):
        for base in (0, 0xa0000000, 0xffffc000):
            self.output = self.root / f"board-{base}"
            result = self.make(base=base)
            self.assertEqual(board.verify(self.output), result)
            other = self.root / f"repeat-{base}"
            self.assertEqual(board.create(self.core, other, base=base, clock_mhz=100), result)

    def test_invalid_parameters_never_publish(self):
        for base in (True, -1, 4, 0x100000000, "0", 1.0):
            with self.subTest(base=base), self.assertRaises(board.BoardBundleError):
                self.make(base=base)
            self.assertFalse(self.output.exists())
        for clock in (True, 0, 1001, "100", 1.5):
            with self.subTest(clock=clock), self.assertRaises(board.BoardBundleError):
                self.make(clock_mhz=clock)
            self.assertFalse(self.output.exists())

    def test_corrupt_core_rejected_before_publish(self):
        (self.core / "generated-src/GraphDeviceAxi4LiteTop.sv").write_text("corrupt\n")
        with self.assertRaises(rtl.GraphDeviceAxi4LiteExportError): self.make()
        self.assertFalse(self.output.exists())

    def test_no_replacement_symlink_or_escape(self):
        self.make()
        before = (self.output / "manifest.json").read_bytes()
        with self.assertRaisesRegex(board.BoardBundleError, "already exists"): self.make()
        self.assertEqual(before, (self.output / "manifest.json").read_bytes())
        self.output = self.root / "link"; self.output.symlink_to(self.root / "absent")
        with self.assertRaises(board.BoardBundleError): self.make()
        with tempfile.TemporaryDirectory() as outside:
            self.output = Path(outside) / "escape"
            with self.assertRaisesRegex(board.BoardBundleError, "below repository"): self.make()
            self.assertFalse(self.output.exists())

    def test_corruption_and_rehashed_template_substitution(self):
        self.make()
        path = self.output / "graph_device_board_bridge.sv"
        path.write_text("module fake; endmodule\n")
        with self.assertRaisesRegex(board.BoardBundleError, "tree or digest"): board.verify(self.output)
        self.rehash()
        with self.assertRaisesRegex(board.BoardBundleError, "template differs"): board.verify(self.output)

    def test_rehashed_settings_and_extra_files_rejected(self):
        self.make()
        path = self.output / "settings.txt"
        original = path.read_bytes(); path.write_text("base=00000000\nclock_mhz=100\n")
        self.rehash()
        with self.assertRaisesRegex(board.BoardBundleError, "settings or clock"): board.verify(self.output)
        path.write_bytes(original)
        (self.output / "extra.sv").write_text("unlisted source\n"); self.rehash()
        with self.assertRaisesRegex(board.BoardBundleError, "unexpected board"): board.verify(self.output)

    def test_rehashed_clock_core_identity_and_source_drift(self):
        self.make()
        path = self.output / "clock.xdc"
        original = path.read_bytes(); path.write_text("create_clock -period 999\n"); self.rehash()
        with self.assertRaisesRegex(board.BoardBundleError, "settings or clock"): board.verify(self.output)
        path.write_bytes(original); self.rehash()
        with patch.object(board, "_source", return_value="0" * 64):
            with self.assertRaisesRegex(board.BoardBundleError, "source differs"): board.verify(self.output)
        path = self.output / "manifest.json"; data = json.loads(path.read_text())
        data["core_rtl_sha256"] = "0" * 64; path.write_bytes(rtl._canonical(data))
        with self.assertRaisesRegex(board.BoardBundleError, "core identity"): board.verify(self.output)

    def test_symlink_inside_bundle_rejected(self):
        self.make()
        path = self.output / "clock.xdc"; path.unlink(); path.symlink_to(self.core / "toolchain.txt")
        with self.assertRaises(rtl.GraphDeviceAxi4LiteExportError): board.verify(self.output)

    @unittest.skipUnless(shutil.which("tclsh"), "Tcl unavailable")
    def test_tcl_candidate_control_flow_with_mock_vendor_commands(self):
        self.make()
        output = self.root / "synthesis"
        # Tcl syntax/control flow only: these mocks cannot validate Vivado APIs.
        script = self.root / "mock.tcl"
        script.write_text('''
proc version {args} {return $::env(TEST_VIVADO_VERSION)}
proc get_parts {args} {return fixture-part}
proc get_cells {args} {return {}}
proc read_verilog {args} {}
proc read_xdc {args} {}
proc synth_design {args} {
  if {[lsearch -exact $args out_of_context] < 0 || [lsearch -exact $args "BASE_ADDR=32'ha0000000"] < 0} {error "wrong synthesis settings"}
}
proc report_utilization {args} {}
proc report_timing_summary {args} {}
proc write_checkpoint {args} {}
set recipe [lindex $argv 0]
set argv [lrange $argv 1 end]
set argc [llength $argv]
source $recipe
''')
        import os
        args = ["tclsh", str(script), str(self.output / "synth_board_bridge.tcl"), str(board.ROOT), str(self.output), str(output), "fixture-part", sys.executable]
        env = dict(os.environ, TEST_VIVADO_VERSION="2025.1")
        good = subprocess.run(args, env=env, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertIn("vendor-synthesis-only", (output / "synthesis-settings.txt").read_text())
        duplicate = subprocess.run(args, env=env, capture_output=True, text=True)
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("output already exists", duplicate.stderr)
        args[5] = str(self.root / "other-synthesis")
        bad = subprocess.run(args, env=dict(env, TEST_VIVADO_VERSION="2024.1"), capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0); self.assertIn("requires Vivado", bad.stderr)
        self.assertFalse(Path(args[5]).exists())
        (self.output / "clock.xdc").write_text("corruption\n")
        bad = subprocess.run(args, env=env, capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0); self.assertFalse(Path(args[5]).exists())


if __name__ == "__main__": unittest.main()
