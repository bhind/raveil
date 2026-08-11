from __future__ import annotations

import hashlib
from pathlib import Path
import re
import struct
import subprocess
import tempfile

from .experiment_schema import BenchmarkCandidate, WorkloadSpec
from .native_backend import NativeMeasurement


REQUEST_MAGIC = 0x52475131
REQUEST_SCHEMA = 1
REQUEST_SIZE = 128
REQUEST_ADDRESS = "0x87ff0000"
RESULT_PREFIX = "RAVEIL-GRAPH-RESULT-V1 "
_RESULT_KEYS = {
    "request", "status", "detail", "job", "epoch", "sequence",
    "cookie", "checksum", "reference", "approved",
}


class SonatineQEMUBackend:
    """Bounded replayable QEMU adapter; never a hardware timing backend."""

    def __init__(
        self,
        kernel: Path,
        *,
        qemu: str = "qemu-system-riscv64",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.kernel = kernel
        self.qemu = qemu
        self.timeout_seconds = timeout_seconds
        self._sequence = 0

    @staticmethod
    def _identity(value: str) -> bytes:
        return hashlib.sha256(value.encode("utf-8")).digest()[:16]

    def _request(
        self, context: WorkloadSpec, candidate: BenchmarkCandidate
    ) -> tuple[int, bytes]:
        if context.family != "gemm" or max(context.m, context.n, context.k) > 8:
            raise ValueError("sonatine-qemu v1 accepts only GEMM dimensions 1..8")
        if candidate.trusted_baseline:
            candidate_kind = 1
        elif candidate.loop_order == "ikj":
            candidate_kind = 2
        elif candidate.loop_order == "tiled":
            candidate_kind = 3
        else:
            raise ValueError("candidate is outside sonatine-qemu v1")
        self._sequence += 1
        binding = (
            f"{context.workload_id}:{context.family}:{context.m}:{context.n}:"
            f"{context.k}:{candidate.candidate_id}:{self._sequence}"
        )
        request_id = int.from_bytes(hashlib.sha256(binding.encode()).digest()[:8], "little") or 1
        packed = struct.pack(
            "<IHHIIIIIIIIQ16s16s16s32s",
            REQUEST_MAGIC, REQUEST_SCHEMA, REQUEST_SIZE, 0, 1,
            context.m, context.n, context.k, candidate_kind, 0, 0, request_id,
            self._identity(context.workload_id),
            self._identity(candidate.candidate_id),
            self._identity("posix-cpu-userspace-v1"),
            bytes(32),
        )
        if len(packed) != REQUEST_SIZE:
            raise AssertionError("graph request ABI size drift")
        return request_id, packed

    @staticmethod
    def parse_result(output: str, request_id: int) -> NativeMeasurement:
        lines = [line.strip() for line in output.splitlines() if line.startswith(RESULT_PREFIX)]
        if len(lines) != 1:
            return NativeMeasurement(None, None, None, False, "missing or duplicate graph result")
        fields: dict[str, str] = {}
        for token in lines[0][len(RESULT_PREFIX):].split():
            if token.count("=") != 1:
                return NativeMeasurement(None, None, None, False, "malformed graph result")
            key, value = token.split("=", 1)
            if key in fields:
                return NativeMeasurement(None, None, None, False, "duplicate graph result field")
            fields[key] = value
        if set(fields) != _RESULT_KEYS:
            return NativeMeasurement(None, None, None, False, "unknown or missing graph result field")
        if not re.fullmatch(r"[0-9a-f]{16}", fields["request"]) or int(
            fields["request"], 16
        ) != request_id:
            return NativeMeasurement(None, None, None, False, "stale graph result binding")
        if not re.fullmatch(r"[0-9a-f]{32}", fields["cookie"]) or not re.fullmatch(
            r"[0-9a-f]{16}", fields["checksum"]
        ) or not re.fullmatch(r"[0-9a-f]{16}", fields["reference"]):
            return NativeMeasurement(None, None, None, False, "malformed graph result identity")
        try:
            status, detail, job, epoch, sequence, approved = (
                int(fields[name])
                for name in ("status", "detail", "job", "epoch", "sequence", "approved")
            )
        except ValueError:
            return NativeMeasurement(None, None, None, False, "non-integer graph result field")
        if status not in {1, 2, 3, 4} or approved not in {0, 1}:
            return NativeMeasurement(None, None, None, False, "unknown graph result state")
        if status != 1 or detail != 0 or job != request_id or epoch == 0 or sequence == 0:
            return NativeMeasurement(
                None, fields["checksum"], fields["reference"], False,
                f"sonatine completion rejected status={status} detail={detail}",
            )
        valid = bool(approved and fields["checksum"] == fields["reference"])
        return NativeMeasurement(
            None,
            fields["checksum"],
            fields["reference"],
            valid,
            "" if valid else "completion lacked approval or semantic equality",
        )

    def measure(self, context: WorkloadSpec, candidate: BenchmarkCandidate) -> NativeMeasurement:
        try:
            request_id, request = self._request(context, candidate)
        except ValueError as error:
            return NativeMeasurement(None, None, None, False, str(error))
        if not self.kernel.is_file():
            return NativeMeasurement(None, None, None, False, "Sonatine kernel is missing")
        with tempfile.TemporaryDirectory(prefix="raveil-sonatine-qemu-") as directory:
            request_path = Path(directory) / "graph-request-v1.bin"
            request_path.write_bytes(request)
            command = (
                self.qemu, "-machine", "virt", "-cpu", "rv64", "-m", "128M",
                "-smp", "1", "-bios", "none", "-nographic", "-kernel",
                str(self.kernel), "-device",
                f"loader,file={request_path},addr={REQUEST_ADDRESS},force-raw=on",
            )
            try:
                completed = subprocess.run(
                    command, capture_output=True, text=True, timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return NativeMeasurement(None, None, None, False, "sonatine-qemu timeout")
        if completed.returncode != 0:
            return NativeMeasurement(
                None, None, None, False,
                f"sonatine-qemu exited {completed.returncode}",
            )
        return self.parse_result(completed.stdout, request_id)
