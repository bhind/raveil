"""Host verifier fault injection only; stub fixtures are never RTL evidence."""
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

from raveil import graph_device_board_execute as e
from raveil import graph_device_board_bundle as board
from raveil import graph_device_axi4lite_export as rtl
from tests import test_graph_device_board_bundle as bundle_fixture

class BoardExecuteTests(unittest.TestCase):
    def setUp(self):
        helper = bundle_fixture.BoardBundleTests()
        helper.setUp(); self.addCleanup(helper.doCleanups)
        helper.make(); self.root = helper.root / "execution"
        self.packet = e.prepare(helper.output, self.root)

    def synthetic_result(self):
        # Deliberately fabricated host fixture; never invoked as a simulator.
        result = self.root / "result"; shutil.copytree(self.root / "inputs", result)
        for phase, cases in (("matrix", e.CASES), ("recovery", (("five-point", 1),))):
            for graph, seed in cases:
                oracle = self.root / "inputs" / phase / "dag-oracles" / f"{graph}-seed-{seed}.bin"
                for prefix in ("private", "fallback"):
                    shutil.copyfile(oracle, result / phase / f"{prefix}-output-{graph}-seed-{seed}.bin")
        shutil.copyfile(self.root / "inputs/matrix/dag-oracles/compact-horizontal-three-point-seed-3.bin", result / "matrix/fallback-output-compact-horizontal-three-point-seed-3.bin")
        (result / "simulator.bin").write_bytes(b"host-fixture-not-a-binary")
        (result / "simulator.sha256").write_text(e.sha((result / "simulator.bin").read_bytes()) + "  /out/simulator.bin\n")
        (result / "toolchain.txt").write_text("Verilator host fixture only\n")
        (result / "build.log").write_text("mock\n"); (result / "device.stderr").write_bytes(b"")
        cases = (("five-point",1,"complete",True),("compact-horizontal-three-point",2,"complete",True),
                 ("compact-horizontal-three-point",3,"cancel",False),("vertical-three-point",4,"complete",True),
                 ("five-point",5,"factory-restart",True),("five-point",1,"complete",True))
        log = "".join(f"GraphDevice-DAG-RUN-V1 graph={graph} seed={seed} mode={mode} status={'COMPLETED' if done else 'CANCELLED'} output_published={int(done)} polls=1\n" for graph,seed,mode,done in cases).encode()
        log += b"BoardReset-V1 busy=1 cleared=1 stale_output=denied\n" + e.MARKER
        (result / "device.log").write_bytes(log)
        lines = ["reset"]; seq = 0
        def add(op, rel, value=0, response=0):
            nonlocal seq
            lines.append(f"{seq} {op} {rel} {self.packet['base'] + rel} {value} {response} {1 + seq % 3}"); seq += 1
        for graph, seed in e.CASES:
            payload = (self.root / "inputs/matrix/dag-oracles" / f"{graph}-seed-{seed}.bin").read_bytes()
            for index, word in enumerate(struct.unpack("<256I", payload)): add("read", 0x1000 + 4 * index, word)
        for _ in range(80): add("write", 0x2400)
        for _ in range(160): add("write", 0x3400)
        add("write", 0x10, 1); add("read", 0x14, 1); lines.append("reset")
        add("read", 0x14); add("read", 0x1000, response=2)
        payload = (self.root / "inputs/recovery/dag-oracles/five-point-seed-1.bin").read_bytes()
        for index, word in enumerate(struct.unpack("<256I", payload)): add("read", 0x1000 + 4 * index, word)
        (result / "transactions.log").write_text("\n".join(lines) + "\n")
        (self.root / "container-result.json").write_bytes(rtl._canonical({"returncode": 0, "stdout": "", "stderr": ""}))
        (self.root / "command.json").write_bytes(rtl._canonical(e.command(self.root, self.packet)))
        receipt = e._results(self.root, self.packet)
        (self.root / "receipt.json").write_bytes(rtl._canonical(receipt))
        return result

    def test_roundtrip_and_no_overwrite(self):
        self.assertEqual(e.verify_inputs(self.root), self.packet)
        result = self.synthetic_result()
        self.assertEqual(e.verify(self.root)["completed"], 5)
        with self.assertRaisesRegex(e.BoardExecuteError, "already exists"): e.run(self.root)
        with self.assertRaisesRegex(e.BoardExecuteError, "already exists"):
            e.prepare(self.root / "bundle", self.root)
        self.assertTrue((result / "simulator.bin").exists())

    def test_generated_input_drift_rejected_before_docker(self):
        path = self.root / "inputs/matrix/inputs/seed-1.bin"; path.write_bytes(b"wrong")
        with patch.object(e.subprocess, "run") as process:
            with self.assertRaisesRegex(e.BoardExecuteError, "identity differs"): e.run(self.root)
            process.assert_not_called()
        self.assertFalse((self.root / "result").exists())

    def test_rehashed_source_cannot_hide_current_source_drift(self):
        with patch.object(e, "sources", return_value={}):
            with self.assertRaisesRegex(e.BoardExecuteError, "identity differs"): e.verify_inputs(self.root)

    def test_output_and_fallback_corruption_rejected(self):
        result = self.synthetic_result()
        for prefix in ("private", "fallback"):
            path = result / f"matrix/{prefix}-output-five-point-seed-1.bin"
            original = path.read_bytes(); path.write_bytes(b"\0" * 1024)
            with self.assertRaisesRegex(e.BoardExecuteError, "output/oracle mismatch"): e.verify(self.root)
            path.write_bytes(original)

    def test_cancelled_output_and_input_substitution_rejected(self):
        result = self.synthetic_result()
        path = result / "matrix/private-output-compact-horizontal-three-point-seed-3.bin"; path.write_bytes(b"\0" * 1024)
        with self.assertRaisesRegex(e.BoardExecuteError, "inventory differs"): e.verify(self.root)
        path.unlink(); (result / "matrix/inputs/seed-1.bin").write_bytes(b"wrong")
        with self.assertRaisesRegex(e.BoardExecuteError, "input drift"): e.verify(self.root)

    def test_address_alias_reset_and_sequence_tamper_rejected(self):
        result = self.synthetic_result(); path = result / "transactions.log"; original = path.read_text()
        for wrong in (original.replace(str(self.packet['base'] + 0x1000), "4096", 1),
                      original.replace("0 read", "7 read", 1), original.replace("reset\n", "", 1),
                      original.replace(" 20 " + str(self.packet['base'] + 20) + " 1 0", " 20 " + str(self.packet['base'] + 20) + " 0 0", 1)):
            path.write_text(wrong)
            with self.assertRaises(e.BoardExecuteError): e.verify(self.root)
        path.write_text(original)

    def test_trace_data_and_log_case_substitution_rejected(self):
        result = self.synthetic_result(); path = result / "transactions.log"
        original = path.read_text(); lines = original.splitlines(); fields = lines[1].split(); fields[4] = str(int(fields[4]) ^ 1)
        lines[1] = " ".join(fields); path.write_text("\n".join(lines) + "\n")
        with self.assertRaisesRegex(e.BoardExecuteError, "trace output"): e.verify(self.root)
        path.write_text(original)
        path = result / "device.log"; path.write_bytes(path.read_bytes().replace(b"seed=2", b"seed=4", 1))
        with self.assertRaisesRegex(e.BoardExecuteError, "case order/identity"): e.verify(self.root)

    def test_failed_container_cannot_verify_and_no_receipt_on_failure(self):
        result = self.synthetic_result()
        (self.root / "container-result.json").write_text('{"returncode":1}')
        with self.assertRaisesRegex(e.BoardExecuteError, "container outcome"): e.verify(self.root)
        shutil.rmtree(result); (self.root / "receipt.json").unlink(); (self.root / "command.json").unlink(); (self.root / "container-result.json").unlink()
        import subprocess
        with patch.object(e.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"fixture failure")):
            with self.assertRaisesRegex(e.BoardExecuteError, "container failed"): e.run(self.root)
        self.assertFalse((self.root / "receipt.json").exists())
        self.assertEqual(json.loads((self.root / "container-result.json").read_text())["returncode"], 1)

    def test_symlink_and_extra_entries_rejected(self):
        result = self.synthetic_result(); path = result / "build.log"; path.unlink(); path.symlink_to(self.root / "input.json")
        with self.assertRaises(e.BoardExecuteError): e.verify(self.root)
        path.unlink(); path.write_text("mock\n"); (self.root / "extra").write_text("unexpected")
        with self.assertRaisesRegex(e.BoardExecuteError, "run inventory"): e.verify(self.root)

if __name__ == "__main__": unittest.main()
