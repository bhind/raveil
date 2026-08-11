from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from raveil.cli import main
from raveil.sonatine_demo import (
    COMMAND_TRANSCRIPT,
    COMPLETED_CHECKSUM,
    FRAME_PREFIX,
    INPUT_SHA256,
    MAX_KERNEL_BYTES,
    MAX_OUTPUT_BYTES,
    SonatineDemoResult,
    _run_bounded_process,
    parse_demo_frames,
    run_sonatine_demo,
)


REVISION = "dabea20e85bf9f0097904528fcfc3fc9152bb7ee"


def transcript_frames() -> bytes:
    rows = (
        ("ls", "OK", 0, "EMPTY", 0, "0000000000000000"),
        ("cat", "OK", 0, "EMPTY", 0, "0000000000000000"),
        ("echo", "OK", 0, "EMPTY", 0, "0000000000000000"),
        ("write", "OK", 0, "EMPTY", 0, "0000000000000000"),
        ("stat", "OK", 0, "EMPTY", 0, "0000000000000000"),
        ("jobs", "EMPTY", 0, "EMPTY", 0, "0000000000000000"),
        ("result", "EMPTY", 0, "EMPTY", 0, "0000000000000000"),
        ("run", "OK", 37376, "DISPATCHED", 0, "0000000000000000"),
        ("run", "BUSY", 37376, "DISPATCHED", 0, "0000000000000000"),
        ("jobs", "OK", 37376, "DISPATCHED", 0, "0000000000000000"),
        ("result", "COMPLETED", 37376, "COMPLETED", 1, COMPLETED_CHECKSUM),
        ("cancel", "TOO_LATE", 37376, "COMPLETED", 1, COMPLETED_CHECKSUM),
        ("result", "COMPLETED", 37376, "COMPLETED", 1, COMPLETED_CHECKSUM),
        ("run", "OK", 37377, "DISPATCHED", 0, "0000000000000000"),
        ("cancel", "OK", 37377, "CANCEL_REQUESTED", 0, "0000000000000000"),
        ("jobs", "OK", 37377, "CANCEL_REQUESTED", 0, "0000000000000000"),
        ("result", "CANCELLED", 37377, "CANCELLED", 0, "0000000000000000"),
        ("cancel", "TOO_LATE", 37377, "CANCELLED", 0, "0000000000000000"),
    )
    return b"".join(
        (
            f"{FRAME_PREFIX}command={command} seq={sequence} status={status} "
            f"job={job} state={state} semantic={semantic} checksum={checksum}\n"
        ).encode("ascii")
        for sequence, (command, status, job, state, semantic, checksum) in enumerate(rows, 1)
    )


class FakeProcessRunner:
    def __init__(self, qemu_output: bytes, *, qemu_returncode: int = 0) -> None:
        self.qemu_output = qemu_output
        self.qemu_returncode = qemu_returncode
        self.qemu_input: bytes | None = None

    def __call__(self, command, *, input_data, timeout_seconds):  # type: ignore[no-untyped-def]
        if command[0] == "git":
            return subprocess.CompletedProcess(command, 0, REVISION.encode() + b"\n", b"")
        if command[1:] == ("--version",):
            return subprocess.CompletedProcess(command, 0, b"QEMU emulator version test\n", b"")
        self.qemu_input = input_data
        return subprocess.CompletedProcess(command, self.qemu_returncode, self.qemu_output, b"")


class SonatineDemoTests(unittest.TestCase):
    def test_fake_qemu_creates_one_strict_bound_result(self) -> None:
        fake = FakeProcessRunner(transcript_frames())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            kernel = root / "sonatine.elf"
            kernel.write_bytes(b"pinned kernel")
            output = root / "result.json"
            result = run_sonatine_demo(kernel, output, repository=root, process_runner=fake)
            self.assertEqual(fake.qemu_input, b"".join(f"{item}\r".encode() for item in COMMAND_TRANSCRIPT))
            self.assertTrue(output.is_file())
            stored = SonatineDemoResult.from_dict(json.loads(output.read_text(encoding="utf-8")))
            self.assertEqual(stored, result)
            self.assertEqual(result.kernel_sha256, hashlib.sha256(b"pinned kernel").hexdigest())
            self.assertEqual(result.input_sha256, INPUT_SHA256)
            invalid = result.to_dict()
            invalid["input_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "input hash"):
                SonatineDemoResult.from_dict(invalid)
            self.assertEqual(result.evidence_class, "qemu-emulation-correctness")
            self.assertEqual(result.final_job_state, "CANCELLED")
            self.assertNotIn("latency", output.read_text(encoding="utf-8"))

    def test_rejects_duplicate_stale_malformed_unknown_and_prose_only_frames(self) -> None:
        valid = transcript_frames()
        malformed = valid.replace(b"seq=3", b"seq=03", 1)
        stale = valid.replace(b"seq=3", b"seq=2", 1)
        unknown = valid.replace(b"status=OK", b"status=UNKNOWN", 1)
        wrong_checksum = valid.replace(COMPLETED_CHECKSUM.encode(), b"0123456789abcdef", 1)
        for output, message in (
            (valid + valid.splitlines()[0] + b"\n", "missing, duplicate, or late"),
            (malformed, "malformed"),
            (stale, "stale or out-of-order"),
            (unknown, "malformed"),
            (wrong_checksum, "lacks semantic approval"),
            (b"RAVEIL-SONATINE-DEMO-V2 command=ls\n", "unknown Sonatine demo frame version"),
            (b"ordinary console prose\n", "missing, duplicate, or late"),
            (b"x" * 172 + FRAME_PREFIX.encode() + b"command=ls\n", "exceeds"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    parse_demo_frames(output)

    def test_failure_never_creates_a_partial_result_or_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            kernel = root / "sonatine.elf"
            kernel.write_bytes(b"kernel")
            output = root / "result.json"
            fake = FakeProcessRunner(transcript_frames(), qemu_returncode=1)
            with self.assertRaisesRegex(RuntimeError, "exited 1"):
                run_sonatine_demo(kernel, output, repository=root, process_runner=fake)
            self.assertFalse(output.exists())
            output.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                run_sonatine_demo(kernel, output, repository=Path(directory))
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve")

    def test_cli_entry_is_explicit_and_uses_exclusive_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            kernel = root / "sonatine.elf"
            kernel.write_bytes(b"kernel")
            output = root / "result.json"
            result = mock.Mock(evidence_class="qemu-emulation-correctness", final_job_state="CANCELLED")
            with mock.patch("raveil.cli.run_sonatine_demo", return_value=result):
                self.assertEqual(0, main([
                    "sonatine-demo", "--sonatine-kernel", str(kernel), "--output", str(output),
                ]))

    def test_kernel_and_output_paths_fail_closed_before_fake_qemu(self) -> None:
        fake = FakeProcessRunner(transcript_frames())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            valid_kernel = root / "kernel.elf"
            valid_kernel.write_bytes(b"kernel")
            symlink_kernel = root / "kernel-link.elf"
            symlink_kernel.symlink_to(valid_kernel)
            for kernel, message in (
                (symlink_kernel, "non-symlink regular"),
                (root, "non-symlink regular"),
            ):
                with self.subTest(kernel=kernel):
                    with self.assertRaisesRegex(ValueError, message):
                        run_sonatine_demo(kernel, root / "result.json", repository=root, process_runner=fake)
            oversized = root / "oversized.elf"
            with oversized.open("wb") as stream:
                stream.truncate(MAX_KERNEL_BYTES + 1)
            with self.assertRaisesRegex(ValueError, "single-link regular"):
                run_sonatine_demo(oversized, root / "oversized.json", repository=root, process_runner=fake)
            target = root / "target"
            target.mkdir()
            parent_link = root / "parent-link"
            parent_link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "parent must not be a symlink"):
                run_sonatine_demo(valid_kernel, parent_link / "result.json", repository=root, process_runner=fake)
            leaf_link = root / "leaf.json"
            leaf_link.symlink_to(target / "missing.json")
            with self.assertRaisesRegex(FileExistsError, "leaf symlink"):
                run_sonatine_demo(valid_kernel, leaf_link, repository=root, process_runner=fake)

    def test_production_bounded_process_collects_and_fails_closed(self) -> None:
        completed = _run_bounded_process(
            (sys.executable, "-c", "import sys; sys.stdout.write('ok'); sys.stderr.write('warn')"),
            input_data=None, timeout_seconds=2,
        )
        self.assertEqual((completed.stdout, completed.stderr), (b"ok", b"warn"))
        with self.assertRaisesRegex(RuntimeError, "stdout exceeds"):
            _run_bounded_process(
                (sys.executable, "-c", f"import sys; sys.stdout.write('x'*{MAX_OUTPUT_BYTES + 1})"),
                input_data=None, timeout_seconds=2,
            )

    def test_timeout_must_be_finite_and_bounded(self) -> None:
        fake = FakeProcessRunner(transcript_frames())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            kernel = root / "kernel.elf"
            kernel.write_bytes(b"kernel")
            for value in (float("nan"), 61.0):
                with self.subTest(timeout=value), self.assertRaisesRegex(ValueError, "finite"):
                    run_sonatine_demo(
                        kernel, root / f"timeout-{len(str(value))}.json", repository=root,
                        timeout_seconds=value, process_runner=fake,
                    )


@unittest.skipUnless(
    os.environ.get("RAVEIL_RUN_SONATINE_DEMO_QEMU") == "1",
    "set RAVEIL_RUN_SONATINE_DEMO_QEMU=1 to run the bounded real-QEMU integration",
)
class SonatineDemoQEMUIntegration(unittest.TestCase):
    def test_real_qemu_fixed_transcript(self) -> None:
        root = Path(__file__).resolve().parents[1]
        kernel = root / "sonatine/build/sonatine.elf"
        self.assertTrue(kernel.is_file(), "build the pinned Sonatine kernel first")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve() / "sonatine-demo-result.json"
            result = run_sonatine_demo(kernel, output, repository=root)
            self.assertEqual(result.evidence_class, "qemu-emulation-correctness")
            self.assertEqual(result.final_job_state, "CANCELLED")


if __name__ == "__main__":
    unittest.main()
