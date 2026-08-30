import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from raveil.graph_device_axi4lite_execute import (
    GENERATED_FILES,
    IMAGE_ID,
    SOURCE_FILES,
    GraphDeviceAxi4LiteExecuteError,
    finalize,
    prepare,
)

ROOT = Path(__file__).resolve().parents[1]


class GraphDeviceAxi4LiteExecuteTests(unittest.TestCase):
    def _write_transcript(self, root: Path) -> None:
        transactions = []

        def write(address: int, data: int, *, response: int = 0, held: int = 0) -> None:
            transactions.append(
                f"AXI4LITE-TRACE-V1 seq={len(transactions)} op=write "
                f"address=0x{address:08x} data=0x{data:08x} strobe=0xf "
                f"response={response} held_b={held}"
            )

        def read(address: int, *, response: int = 0, held: int = 0) -> None:
            transactions.append(
                f"AXI4LITE-TRACE-V1 seq={len(transactions)} op=read "
                f"address=0x{address:08x} data=0x00000000 "
                f"response={response} held_r={held}"
            )

        def words(name: str) -> tuple[int, ...]:
            payload = (root / name).read_bytes()
            return struct.unpack(f"<{len(payload) // 4}I", payload)

        def stage(seed: int) -> None:
            for index, value in enumerate(words(f"input-seed-{seed}.bin")):
                write(0x0400 + 4 * index, value)

        def output(seed: int, *, hold_first: bool = False) -> None:
            for index, value in enumerate(words(f"oracle-seed-{seed}.bin")):
                read(
                    0x1000 + 4 * index,
                    held=4 if hold_first and index == 0 else 0,
                )
                transactions[-1] = transactions[-1].replace(
                    "data=0x00000000", f"data=0x{value:08x}"
                )

        read(0x1000, response=2)
        write(0x0010, 4)
        stage(1)
        write(0x0010, 1, held=4)
        output(1, hold_first=True)
        write(0x0010, 4)
        stage(3)
        write(0x0010, 1)
        read(0x1000, response=2)
        write(0x0010, 2, held=4096)
        read(0x1000, response=2)
        write(0x0010, 4)
        stage(2)
        write(0x0010, 1)
        output(2)
        while len(transactions) < 7160:
            read(0x0014)
        (root / "axi-transcript.log").write_text(
            "\n".join(transactions) + "\n", encoding="ascii"
        )

    def _complete_evidence(self, root: Path) -> None:
        lines = []
        for name in sorted(SOURCE_FILES):
            location = root / name if name in GENERATED_FILES else ROOT / name
            lines.append(f"{name} {hashlib.sha256(location.read_bytes()).hexdigest()}")
        (root / "source.manifest").write_text("\n".join(lines) + "\n")
        for manifest, directory in (
            ("rtl-first.manifest", "rtl-first"),
            ("rtl-second.manifest", "rtl-second"),
        ):
            target = root / directory
            target.mkdir()
            rtl = target / "GraphDeviceAxi4LiteTop.sv"
            rtl.write_text("module x; endmodule\n")
            digest = hashlib.sha256(rtl.read_bytes()).hexdigest()
            (root / manifest).write_text(f"GraphDeviceAxi4LiteTop.sv {digest}\n")
        (root / "simulator.bin").write_bytes(b"simulator")
        (root / "simulator.sha256").write_text(
            hashlib.sha256(b"simulator").hexdigest() + "\n"
        )
        (root / "environment.txt").write_text(
            "schema=raveil.graph-device-axi4lite-execute-environment/v1\n"
            f"platform=linux/amd64\nimage_id={IMAGE_ID}\n"
        )
        (root / "toolchain.txt").write_text(
            "Scala CLI version: test\nVerilator test\n"
        )
        (root / "device.log").write_text(
            "GraphDevice-AXI4LITE-EXECUTE-V1 status=OK inputs=324 "
            "outputs=256 oracle=match cancel=denied-output restart=match "
            "evidence=rtl-simulation-functional performance=not-measured\n"
        )
        (root / "device.stderr").write_bytes(b"")
        (root / "container.stderr").write_bytes(b"")
        self._write_transcript(root)
        for seed in (1, 2):
            (root / f"output-seed-{seed}.bin").write_bytes(
                (root / f"oracle-seed-{seed}.bin").read_bytes()
            )

    def test_prepare_generates_vectors_and_finalizes_once(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            evidence = Path(temporary) / "evidence"
            prepare(evidence)
            self.assertEqual((evidence / "input-seed-1.bin").stat().st_size, 324 * 4)
            self.assertEqual((evidence / "oracle-seed-1.bin").stat().st_size, 256 * 4)
            self.assertIn("kSeed3Input", (evidence / "graph_device_axi4lite_execute_vectors.h").read_text())
            self._complete_evidence(evidence)
            receipt = finalize(evidence)
            self.assertEqual(
                receipt["schema"],
                "raveil.graph-device-axi4lite-execute-receipt/v1",
            )
            self.assertEqual(receipt["axi_trace_summary"]["held_b_cycles"], 4100)
            self.assertEqual(receipt["axi_trace_summary"]["held_r_cycles"], 4)
            self.assertEqual(finalize(evidence, verify_existing=True), receipt)
            with self.assertRaisesRegex(
                GraphDeviceAxi4LiteExecuteError, "append-once"
            ):
                finalize(evidence)

    def test_finalizer_rejects_vector_output_and_stderr_substitution(self):
        for target, expected in (
            ("input-seed-1.bin", "unexpected size"),
            ("output-seed-1.bin", "unexpected size"),
            ("device.stderr", "not empty"),
            ("axi-transcript.log", "AXI transcript"),
        ):
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                evidence = Path(temporary) / "evidence"
                prepare(evidence)
                self._complete_evidence(evidence)
                (evidence / target).write_bytes(b"substituted")
                with self.assertRaisesRegex(GraphDeviceAxi4LiteExecuteError, expected):
                    finalize(evidence)

    def test_top_has_nonaliased_windows_sticky_status_and_core_handshakes(self):
        source = (ROOT / "hardware/chisel/GraphDeviceAxi4LiteTop.scala").read_text()
        self.assertIn("savedAw(12, 2)", source)
        self.assertIn("araddr(12, 2)", source)
        self.assertIn("stagedWords === 324.U", source)
        self.assertIn("inputActive && !inputIssued", source)
        self.assertIn("outputActive && !outputIssued", source)
        self.assertIn("!inputActive && !outputActive", source)
        self.assertIn("completedSticky || core.io.done", source)
        self.assertIn("outputSuppressed", source)
        harness = (
            ROOT / "hardware/chisel/graph_device_axi4lite_execute_verilator.cpp"
        ).read_text()
        self.assertIn('transcript.open(evidence / "axi-transcript.log"', harness)
        self.assertIn("hold_start && index == 0 ? 4 : 0", harness)
        self.assertIn("abi::kControlCancel, Okay, 0xf, 4096", harness)


if __name__ == "__main__":
    unittest.main()
