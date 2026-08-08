from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import time
from typing import Callable, TypeVar


T = TypeVar("T")
POWERMETRICS_HELPER = "/usr/local/libexec/raveil-powermetrics"
DEFAULT_COMMAND_PREFIX = ("/usr/bin/sudo", "-n", POWERMETRICS_HELPER)
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
    sample_count: int = 0


def parse_powermetrics(
    text: str, stable_levels: tuple[str, ...], minimum_samples: int = 1
) -> PowerSample:
    powers = []
    for number, unit in POWER_RE.findall(text):
        power = float(number)
        powers.append(power * 1000.0 if unit.lower() == "w" else power)
    thermal = [value.strip() for value in THERMAL_RE.findall(text)]
    if not powers:
        return PowerSample(None, thermal[-1] if thermal else None, False, "powermetrics CPU power sample missing")
    if len(powers) < minimum_samples:
        return PowerSample(
            None,
            thermal[-1] if thermal else None,
            False,
            f"powermetrics samples missing: required {minimum_samples}, found {len(powers)}",
            len(powers),
        )
    if not thermal:
        return PowerSample(None, None, False, "powermetrics thermal sample missing", len(powers))
    if len(set(thermal)) != 1:
        return PowerSample(None, thermal[-1], False, "thermal level changed during measurement", len(powers))
    if thermal[-1].casefold() not in {level.casefold() for level in stable_levels}:
        return PowerSample(None, thermal[-1], False, f"unstable thermal level: {thermal[-1]}", len(powers))
    return PowerSample(sum(powers) / len(powers), thermal[-1], True, sample_count=len(powers))


class PowermetricsSampler:
    def __init__(
        self,
        interval_ms: int,
        stable_levels: tuple[str, ...],
        minimum_samples: int = 3,
        command_prefix: tuple[str, ...] | None = None,
    ) -> None:
        self.interval_ms = interval_ms
        self.stable_levels = stable_levels
        self.minimum_samples = minimum_samples
        if command_prefix is None:
            command_prefix = DEFAULT_COMMAND_PREFIX
            self.helper_path: Path | None = Path(POWERMETRICS_HELPER)
        else:
            self.helper_path = None
        if not command_prefix:
            raise ValueError("powermetrics command prefix must not be empty")
        self.command_prefix = command_prefix

    def _helper_installation_failure(self) -> str:
        if self.helper_path is None:
            return ""
        try:
            helper = self.helper_path.lstat()
        except OSError:
            return "powermetrics helper is not installed"
        if stat.S_ISLNK(helper.st_mode) or not stat.S_ISREG(helper.st_mode):
            return "powermetrics helper must be a regular non-symlink file"
        checked = (("helper", helper),)
        try:
            directories = tuple(
                (f"helper directory {directory}", directory.lstat())
                for directory in self.helper_path.parents
            )
        except OSError:
            return "powermetrics helper installation path is unavailable"
        for label, metadata in (*checked, *directories):
            if label != "helper" and (
                stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode)
            ):
                return f"powermetrics {label} must be a non-symlink directory"
            if metadata.st_uid != 0:
                return f"powermetrics {label} must be owned by root"
            if metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                return f"powermetrics {label} must not be group/other writable"
        return ""

    def _command(self, sample_count: int) -> tuple[str, ...]:
        return (
            *self.command_prefix,
            "--sample-rate",
            str(self.interval_ms),
            "--sample-count",
            str(sample_count),
        )

    def preflight(self) -> PowerSample:
        """Verify non-interactive privilege and sampler fields before a run exists."""
        installation_failure = self._helper_installation_failure()
        if installation_failure:
            return PowerSample(None, None, False, installation_failure)
        try:
            completed = subprocess.run(
                self._command(1),
                check=False,
                capture_output=True,
                text=True,
                timeout=max(5.0, self.interval_ms / 1000.0 + 2.0),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return PowerSample(None, None, False, f"powermetrics preflight failed: {error}")
        if completed.returncode != 0:
            detail = completed.stderr.strip() or f"powermetrics exited {completed.returncode}"
            if "password is required" in detail.casefold():
                detail = "powermetrics helper is not authorized for passwordless sudo"
            elif any(
                phrase in detail.casefold()
                for phrase in ("no such file", "command not found", "unable to execute")
            ):
                detail = "powermetrics helper is not installed"
            return PowerSample(None, None, False, detail)
        return parse_powermetrics(completed.stdout, self.stable_levels, minimum_samples=1)

    def _wait_for_ready(
        self, process: subprocess.Popen[bytes]
    ) -> tuple[bytes, PowerSample]:
        """Consume and exclude one complete sampler observation before work starts."""
        if process.stdout is None:
            return b"", PowerSample(None, None, False, "powermetrics stdout unavailable")
        deadline = time.monotonic() + max(5.0, self.interval_ms / 1000.0 + 2.0)
        prelude = bytearray()
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            readable, _, _ = select.select([process.stdout.fileno()], [], [], remaining)
            if not readable:
                break
            chunk = os.read(process.stdout.fileno(), 4096)
            if not chunk:
                break
            prelude.extend(chunk)
            text = prelude.decode("utf-8", errors="replace")
            if POWER_RE.search(text) and THERMAL_RE.search(text):
                return bytes(prelude), parse_powermetrics(
                    text, self.stable_levels, minimum_samples=1
                )
        return bytes(prelude), PowerSample(
            None, None, False, "powermetrics sampler readiness sample missing"
        )

    def measure(self, operation: Callable[[], T], raw_output: Path) -> tuple[T | None, PowerSample]:
        installation_failure = self._helper_installation_failure()
        if installation_failure:
            return None, PowerSample(None, None, False, installation_failure)
        command = self._command(-1)
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            return None, PowerSample(None, None, False, f"powermetrics unavailable: {error}")
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            raw_output.write_bytes(stdout + stderr)
            detail = stderr.decode("utf-8", errors="replace").strip()
            detail = detail or "powermetrics exited before measurement"
            return None, PowerSample(None, None, False, detail)
        prelude, readiness = self._wait_for_ready(process)
        if not readiness.valid:
            if process.poll() is None:
                process.terminate()
            stdout, stderr = process.communicate()
            raw_output.parent.mkdir(parents=True, exist_ok=True)
            raw_output.write_bytes(prelude + stdout + stderr)
            return None, readiness
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
        measurement_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        raw_output.write_text(
            prelude.decode("utf-8", errors="replace")
            + "\n*** RAVEIL MEASUREMENT WINDOW ***\n"
            + measurement_text
            + stderr_text,
            encoding="utf-8",
        )
        if process.returncode not in {0, -signal.SIGTERM} and not stdout:
            detail = stderr_text.strip() or f"powermetrics exited {process.returncode}"
            return result, PowerSample(None, None, False, detail)
        return result, parse_powermetrics(
            measurement_text, self.stable_levels, minimum_samples=self.minimum_samples
        )
