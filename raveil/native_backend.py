from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
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
        semantic_valid = bool(value.get("semantic_valid", False))
        failure = str(value.get("failure", ""))
        if completed.returncode != 0 and not failure:
            failure = f"native benchmark exited {completed.returncode}"
        return NativeMeasurement(
            latency_ns=int(value["latency_ns"]) if value.get("latency_ns") is not None else None,
            checksum=str(value["checksum"]) if value.get("checksum") is not None else None,
            reference_checksum=(
                str(value["reference_checksum"])
                if value.get("reference_checksum") is not None
                else None
            ),
            semantic_valid=semantic_valid,
            failure=failure,
        )
