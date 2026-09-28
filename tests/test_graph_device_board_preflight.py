"""Host fault-injection fixtures, not tool/RTL proof."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from raveil import graph_device_board_preflight as p
from raveil import graph_device_axi4lite_export as rtl
from tests import test_graph_device_board_bundle as fixture

class StructuralPreflightTests(unittest.TestCase):
    def setUp(self):
        self.helper = fixture.BoardBundleTests(); self.helper.setUp()
        self.addCleanup(self.helper.doCleanups); self.helper.make()
        self.output = self.helper.root / "preflight"
        self.netlist = {"modules": {"GraphDeviceBoardBridge": {
            "parameter_default_values": {"BASE_ADDR": format(0xa0000000, "032b")},
            "ports": {name: {"direction": direction, "bits": list(range(width))} for name,(direction,width) in p.PORTS.items()},
            "cells": {"fixture": {"type": "$dff"}}, "attributes": {}}}}

    def fake_tool(self, args, **kwargs):
        out = self.output / "result"
        (out / "toolchain.txt").write_text("Yosys 0.27+3 host fixture only\n")
        (out / "yosys.sha256").write_text(p.YOSYS_SHA + "\n")
        (out / "yosys.log").write_text("Found and reported 0 problems.\nFound and expected 0 SCCs.\n")
        (out / "structural.json").write_text(json.dumps(self.netlist))
        return subprocess.CompletedProcess(args, 0, b"", b"")

    def make(self):
        with patch.object(p.subprocess, "run", side_effect=self.fake_tool):
            return p.run(self.helper.output, self.output)

    def test_roundtrip_and_no_overwrite(self):
        self.assertEqual(self.make(), p.verify(self.output))
        with self.assertRaisesRegex(p.BoardPreflightError, "already exists"): self.make()

    def test_corrupt_bundle_rejected_before_tool(self):
        (self.helper.output / "clock.xdc").write_text("changed")
        with patch.object(p.subprocess, "run") as call:
            with self.assertRaises(ValueError): p.run(self.helper.output, self.output)
            call.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_failed_tool_has_no_success_receipt(self):
        with patch.object(p.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"ERROR fixture")):
            with self.assertRaisesRegex(p.BoardPreflightError, "diagnostics retained"): p.run(self.helper.output, self.output)
        self.assertFalse((self.output / "receipt.json").exists())
        self.assertEqual(json.loads((self.output / "outcome.json").read_text())["returncode"], 1)

    def test_bad_structure_cannot_pass(self):
        top = self.netlist["modules"]["GraphDeviceBoardBridge"]
        for mutation in (lambda t: t["attributes"].update(blackbox="1"),
                         lambda t: t["cells"]["fixture"].update(type="$dlatch"),
                         lambda t: t["cells"]["fixture"].update(type="missing_module"),
                         lambda t: t["ports"]["s_axi_awaddr"].update(bits=[0]),
                         lambda t: t["parameter_default_values"].update(BASE_ADDR="0")):
            candidate = copy.deepcopy(top); mutation(candidate)
            with self.assertRaises(p.BoardPreflightError):
                p.check_netlist(json.dumps({"modules": {"GraphDeviceBoardBridge": candidate}}).encode(), 0xa0000000)

    def test_script_and_source_changes_rejected(self):
        self.make(); path = self.output / "preflight.ys"; original = path.read_bytes()
        path.write_bytes(original.replace(b"check -assert", b"check"))
        with self.assertRaisesRegex(p.BoardPreflightError, "script differs"): p.verify(self.output)
        path.write_bytes(original)
        with patch.object(p, "source_identity", return_value={}):
            with self.assertRaisesRegex(p.BoardPreflightError, "source identity"): p.verify(self.output)

    def test_failed_check_log_and_outcome_rejected(self):
        self.make(); path = self.output / "result/yosys.log"; original = path.read_bytes()
        path.write_bytes(original + b"ERROR: deliberate fault\n")
        with self.assertRaisesRegex(p.BoardPreflightError, "strict checks"): p.verify(self.output)
        path.write_bytes(original)
        (self.output / "outcome.json").write_text('{"returncode":1,"stdout":"","stderr":"failed"}')
        with self.assertRaisesRegex(p.BoardPreflightError, "did not succeed"): p.verify(self.output)

    def test_extra_symlink_and_receipt_drift_rejected(self):
        self.make(); extra = self.output / "result/extra"; extra.symlink_to(self.output / "input.json")
        with self.assertRaises(ValueError): p.verify(self.output)
        extra.unlink(); path = self.output / "receipt.json"; value = json.loads(path.read_text()); value["mapping"] = "complete"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(p.BoardPreflightError, "receipt differs"): p.verify(self.output)

if __name__ == "__main__": unittest.main()
