from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from raveil.graph_device_mvp import (
    EVIDENCE_CLASS,
    GraphDeviceMvpError,
    compile_artifact,
    device_abi_id,
    finalize,
    load_device_abi,
    prepare,
    source_id,
    validate_artifact,
    validate_device_abi,
)


ROOT = Path(__file__).resolve().parents[1]
CHISEL = ROOT / "hardware" / "chisel"


class GraphDeviceMvpTests(unittest.TestCase):
    def _prepared(self, root: Path) -> Path:
        evidence = root / "evidence"
        prepare(evidence)
        return evidence

    def _complete_fake_device(self, evidence: Path) -> None:
        artifact = json.loads((evidence / "artifact.json").read_text())
        lines = [
            "GraphDevice-ABI-V1 status=OK identity=52560101 "
            f"descriptor={artifact['descriptor_sha256']} "
            f"configuration={artifact['configuration_sha256']} "
            f"implementation={artifact['implementation_sha256']}",
        ]
        for seed in (1, 2):
            oracle = evidence / "oracles" / f"seed-{seed}.bin"
            output = evidence / f"private-output-seed-{seed}.bin"
            output.write_bytes(oracle.read_bytes())
            words = [
                int.from_bytes(oracle.read_bytes()[index:index + 4], "little")
                for index in range(0, oracle.stat().st_size, 4)
            ]
            lines.append(
                f"GraphDevice-RUN-{seed}-V1 status=COMPLETED staged_words=324 "
                f"polls=3073 output_valid=1 output_words=256 "
                f"checksum={sum(words) & 0xffffffffffffffff:016x}"
            )
        lines.extend([
            "GraphDevice-CANCEL-V1 seed=3 status=CANCELLED output_valid=0 "
            "output_words=0 blocked_read=1 published=0",
            "GraphDevice-RESET-RESTART-V1 status=OK seed=2",
            "GraphDevice-DEVICE-RUNTIME-V1 status=OK completed=2 cancelled=1 "
            "resets=2 evidence=rtl-simulation-functional performance=not-measured",
        ])
        (evidence / "device.log").write_text("\n".join(lines) + "\n", encoding="ascii")
        (evidence / "simulator.sha256").write_text("a" * 64 + "\n", encoding="ascii")
        (evidence / "environment.txt").write_text(
            "schema=raveil.graph-device-environment/v1\nplatform=linux/amd64\n",
            encoding="ascii",
        )

    def test_owned_abi_is_exact_bounded_and_pointer_free(self) -> None:
        abi = load_device_abi()
        validate_device_abi(abi)
        self.assertEqual(len(device_abi_id(abi)), 64)
        self.assertEqual(abi["identity_word"], 0x52560101)
        self.assertEqual(abi["byte_order"], "little-endian")
        self.assertTrue(abi["pointer_free"])
        self.assertEqual(abi["input_window"]["count_words"], 324)
        self.assertEqual(abi["output_window"]["count_words"], 256)
        self.assertLess(
            abi["input_window"]["base_word"] + abi["input_window"]["count_words"],
            abi["output_window"]["base_word"],
        )
        mutated = deepcopy(abi)
        mutated["status_bits"]["output_valid"] = 32
        with self.assertRaisesRegex(GraphDeviceMvpError, "ABI fields"):
            validate_device_abi(mutated)

    def test_compiler_emits_one_deterministic_versioned_artifact(self) -> None:
        first = compile_artifact()
        second = compile_artifact()
        self.assertEqual(first, second)
        validate_artifact(first)
        self.assertEqual(first["schema"], "raveil.graph-device-static-artifact/v1")
        self.assertEqual(first["successful_seeds"], [1, 2])
        self.assertEqual(first["cancel_seed"], 3)
        self.assertEqual(first["evidence_class"], EVIDENCE_CLASS)
        self.assertEqual(first["source_sha256"], source_id())

    def test_prepare_binds_inputs_oracles_and_generated_abi_header(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            for seed in (1, 2, 3):
                self.assertEqual((evidence / "inputs" / f"seed-{seed}.bin").stat().st_size, 324 * 4)
                self.assertEqual((evidence / "oracles" / f"seed-{seed}.bin").stat().st_size, 256 * 4)
            header = (evidence / "graph_device_abi_generated.h").read_text()
            self.assertIn("kIdentity = 0x52560101U", header)
            self.assertIn("kInputCount = 324U", header)
            self.assertIn("kOutputCount = 256U", header)
            self.assertIn(compile_artifact()["configuration_sha256"], header)

    def test_runtime_and_transport_keep_external_types_outside_owned_abi(self) -> None:
        abi = (ROOT / "contracts" / "graph_device_abi_v1.json").read_text()
        runtime = (CHISEL / "graph_device_runtime.cpp").read_text()
        runtime_header = (CHISEL / "graph_device_runtime.h").read_text()
        device = (CHISEL / "graph_device_verilator.cpp").read_text()
        for forbidden in ("Verilator", "TileLink", "Chipyard", "AXI", "UIO", "AMD", "Linux"):
            self.assertNotIn(forbidden, abi)
            self.assertNotIn(forbidden, runtime)
            self.assertNotIn(forbidden, runtime_header)
        self.assertIn("class DeviceTransport", runtime_header)
        self.assertIn("VStaticStencilRegion", device)
        self.assertIn("kMaxStatusPolls", runtime)
        self.assertLess(runtime.index("kStatusOutputValid"), runtime.index("kOutputBase + index"))

    def test_finalizer_requires_two_oracle_matches_cancel_and_restart(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_fake_device(evidence)
            receipt = finalize(evidence)
            self.assertEqual(receipt["status"], "complete")
            self.assertEqual(receipt["evidence_class"], EVIDENCE_CLASS)
            self.assertEqual(len(receipt["runs"]), 2)
            self.assertTrue(all(run["oracle_match"] for run in receipt["runs"]))
            self.assertTrue(all(not run["published"] for run in receipt["runs"]))
            self.assertFalse(receipt["cancel"]["published"])
            self.assertEqual(len(receipt["cancel"]["input_sha256"]), 64)
            self.assertEqual(len(receipt["cancel"]["oracle_sha256"]), 64)
            self.assertTrue(receipt["reset_restart"]["passed"])
            with self.assertRaisesRegex(GraphDeviceMvpError, "append-once"):
                finalize(evidence)

    def test_oracle_mismatch_and_cancel_output_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_fake_device(evidence)
            output = evidence / "private-output-seed-1.bin"
            data = bytearray(output.read_bytes())
            data[0] ^= 1
            output.write_bytes(data)
            with self.assertRaisesRegex(GraphDeviceMvpError, "Pavane mismatch"):
                finalize(evidence)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = self._prepared(Path(temporary))
            self._complete_fake_device(evidence)
            (evidence / "private-output-seed-3.bin").write_bytes(b"\0" * 1024)
            with self.assertRaisesRegex(GraphDeviceMvpError, "cancelled output"):
                finalize(evidence)

    def test_runners_are_one_command_offline_and_non_claiming(self) -> None:
        outer = CHISEL / "run-graph-device-sim-mvp.sh"
        inner = CHISEL / "run-graph-device-sim-mvp-in-container.sh"
        self.assertNotEqual(outer.stat().st_mode & 0o111, 0)
        self.assertNotEqual(inner.stat().st_mode & 0o111, 0)
        outer_text = outer.read_text()
        inner_text = inner.read_text()
        self.assertIn("--network none", outer_text)
        self.assertIn("no-new-privileges=true", outer_text)
        self.assertIn("python3 -m raveil.graph_device_mvp prepare", outer_text)
        self.assertIn("python3 -m raveil.graph_device_mvp finalize", outer_text)
        self.assertIn("run-graph-device-sim-mvp-in-container.sh", outer_text)
        self.assertIn("graph_device_runtime.cpp", inner_text)
        self.assertIn("graph_device_verilator.cpp", inner_text)
        for text in (outer_text, inner_text):
            self.assertNotIn("performance=measured", text)
            self.assertNotIn("vivado", text.lower())
            self.assertNotIn("bitstream", text.lower())


if __name__ == "__main__":
    unittest.main()
