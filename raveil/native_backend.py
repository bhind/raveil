from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess

from .experiment_schema import BenchmarkCandidate, WorkloadSpec


@dataclass(frozen=True)
class NativeMeasurement:
    latency_ns: int | None
    checksum: str | None
    reference_checksum: str | None
    semantic_valid: bool
    failure: str = ""


class NativeCBackend:
    """Pinned-source native C adapter; subprocess time is outside the metric."""

    def __init__(
        self,
        source: Path,
        binary: Path,
        compiler: str = "cc",
        compiler_flags: tuple[str, ...] = ("-O3", "-std=c11", "-Wall", "-Wextra", "-Werror"),
        timeout_seconds: float = 30.0,
        warmups: int = 1,
    ) -> None:
        self.source = source
        self.binary = binary
        self.compiler = compiler
        self.compiler_flags = compiler_flags
        self.timeout_seconds = timeout_seconds
        self.warmups = warmups

    def compile(self) -> tuple[str, ...]:
        self.binary.parent.mkdir(parents=True, exist_ok=True)
        command = (self.compiler, *self.compiler_flags, str(self.source), "-o", str(self.binary))
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"native benchmark compilation failed: {detail}")
        return command

    def measure(self, context: WorkloadSpec, candidate: BenchmarkCandidate) -> NativeMeasurement:
        command = (
            str(self.binary),
            context.family,
            str(context.m),
            str(context.n),
            str(context.k),
            candidate.loop_order,
            str(candidate.tile),
            candidate.materialization,
            str(self.warmups),
            str(context.inner_iterations),
        )
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return NativeMeasurement(None, None, None, False, "timeout")
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError:
            detail = completed.stderr.strip() or "invalid native benchmark output"
            return NativeMeasurement(None, None, None, False, detail)
        expected = {
            "latency_ns", "checksum", "reference_checksum", "semantic_valid", "failure"
        }
        if type(value) is not dict or set(value) != expected:
            return NativeMeasurement(None, None, None, False, "invalid native benchmark schema")
        latency = value["latency_ns"]
        checksum = value["checksum"]
        reference = value["reference_checksum"]
        semantic_valid = value["semantic_valid"]
        failure = value["failure"]
        if (
            type(latency) is not int
            or latency < 0
            or type(checksum) is not str
            or re.fullmatch(r"[0-9a-f]{16}", checksum) is None
            or type(reference) is not str
            or re.fullmatch(r"[0-9a-f]{16}", reference) is None
            or type(semantic_valid) is not bool
            or type(failure) is not str
        ):
            return NativeMeasurement(None, None, None, False, "invalid native benchmark field")
        if completed.returncode != 0 and not failure:
            failure = f"native benchmark exited {completed.returncode}"
        return NativeMeasurement(
            latency_ns=latency,
            checksum=checksum,
            reference_checksum=reference,
            semantic_valid=semantic_valid,
            failure=failure,
        )
