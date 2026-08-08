from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import signal
import subprocess
import time
from typing import Callable, TypeVar


T = TypeVar("T")
POWER_RE = re.compile(r"CPU Power:\s*([0-9]+(?:\.[0-9]+)?)\s*(mW|W)", re.IGNORECASE)
THERMAL_RE = re.compile(
    r"(?:Current pressure level|Thermal pressure):\s*([A-Za-z][A-Za-z -]*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PowerSample:
    cpu_power_mw: float | None
    thermal_level: str | None
    valid: bool
    failure: str = ""


def parse_powermetrics(text: str, stable_levels: tuple[str, ...]) -> PowerSample:
    powers = []
    for number, unit in POWER_RE.findall(text):
        power = float(number)
        powers.append(power * 1000.0 if unit.lower() == "w" else power)
    thermal = [value.strip() for value in THERMAL_RE.findall(text)]
    if not powers:
        return PowerSample(None, thermal[-1] if thermal else None, False, "powermetrics CPU power sample missing")
    if not thermal:
        return PowerSample(None, None, False, "powermetrics thermal sample missing")
    if len(set(thermal)) != 1:
        return PowerSample(None, thermal[-1], False, "thermal level changed during measurement")
    if thermal[-1].casefold() not in {level.casefold() for level in stable_levels}:
        return PowerSample(None, thermal[-1], False, f"unstable thermal level: {thermal[-1]}")
    return PowerSample(sum(powers) / len(powers), thermal[-1], True)


class PowermetricsSampler:
    def __init__(
        self,
        interval_ms: int,
        stable_levels: tuple[str, ...],
        executable: str = "/usr/bin/powermetrics",
    ) -> None:
        self.interval_ms = interval_ms
        self.stable_levels = stable_levels
        self.executable = executable

    def measure(self, operation: Callable[[], T], raw_output: Path) -> tuple[T | None, PowerSample]:
        command = (
            self.executable,
            "--samplers",
            "cpu_power,thermal",
            "--sample-rate",
            str(self.interval_ms),
            "--sample-count",
            "-1",
            "--format",
            "text",
            "--buffer-size",
            "1",
            "--handle-invalid-values",
        )
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as error:
            return None, PowerSample(None, None, False, f"powermetrics unavailable: {error}")
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            raw_output.write_text(stdout + stderr, encoding="utf-8")
            detail = stderr.strip() or "powermetrics exited before measurement"
            return None, PowerSample(None, None, False, detail)
        result: T | None = None
        try:
            result = operation()
            if process.poll() is None:
                process.send_signal(signal.SIGINFO)
                time.sleep(self.interval_ms / 1000.0)
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        raw_output.write_text(stdout + stderr, encoding="utf-8")
        if process.returncode not in {0, -signal.SIGTERM} and not stdout:
            detail = stderr.strip() or f"powermetrics exited {process.returncode}"
            return result, PowerSample(None, None, False, detail)
        return result, parse_powermetrics(stdout, self.stable_levels)
