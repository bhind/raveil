"""Read-only KV260 target readiness checks before any UIO device access."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import platform
import re
import stat
import sys
from typing import Callable


_UIO_PATH = re.compile(r"/dev/uio(?P<number>0|[1-9][0-9]*)")
_DEVICE_ID = re.compile(r"(?P<major>0|[1-9][0-9]*):(?P<minor>0|[1-9][0-9]*)")
_HEX_VALUE = re.compile(r"0x[0-9a-fA-F]+")
_KERNEL_RELEASE = re.compile(r"[A-Za-z0-9._+~-]{1,128}")
_MANAGER_STATE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,126}")
_APERTURE_BYTES = 0x4000
_MAX_PROPERTY_BYTES = 512


class Kv260PreflightError(RuntimeError):
    """The target did not satisfy the no-device-access readiness boundary."""


def _read_bounded(path: Path, *, limit: int = _MAX_PROPERTY_BYTES) -> bytes:
    try:
        with path.open("rb") as stream:
            value = stream.read(limit + 1)
    except OSError as error:
        raise Kv260PreflightError(f"required target property is unavailable: {path}") from error
    if not value:
        raise Kv260PreflightError(f"required target property is empty: {path}")
    if len(value) > limit:
        raise Kv260PreflightError(f"required target property is oversized: {path}")
    return value


def _read_line(path: Path) -> str:
    value = _read_bounded(path)
    if value.endswith(b"\n"):
        value = value[:-1]
    if not value or b"\n" in value or b"\r" in value or b"\0" in value:
        raise Kv260PreflightError(f"target property is not one bounded line: {path}")
    try:
        return value.decode("ascii")
    except UnicodeDecodeError as error:
        raise Kv260PreflightError(f"target property is not ASCII: {path}") from error


def _parse_hex(path: Path) -> int:
    value = _read_line(path)
    if _HEX_VALUE.fullmatch(value) is None:
        raise Kv260PreflightError(f"target property is not canonical hexadecimal: {path}")
    parsed = int(value, 16)
    if parsed > 0xFFFFFFFFFFFFFFFF:
        raise Kv260PreflightError(f"target property exceeds 64 bits: {path}")
    return parsed


def _model(path: Path) -> tuple[str, str]:
    value = _read_bounded(path)
    if not value.endswith(b"\0") or value.count(b"\0") != 1:
        raise Kv260PreflightError("device-tree model is not one NUL-terminated string")
    raw_model = value[:-1]
    if not raw_model or any(byte < 0x20 or byte > 0x7E for byte in raw_model):
        raise Kv260PreflightError("device-tree model is not bounded printable ASCII")
    model = raw_model.decode("ascii")
    if "KV260" not in model:
        raise Kv260PreflightError("device-tree model is not KV260")
    return model, hashlib.sha256(value).hexdigest()


def collect_preflight(
    device: str,
    *,
    system: str | None = None,
    machine: str | None = None,
    kernel_release: str | None = None,
    proc_root: Path = Path("/proc"),
    sys_root: Path = Path("/sys"),
    lstat_fn: Callable[[str], os.stat_result] | None = None,
) -> dict[str, str]:
    """Inspect fixed kernel metadata without opening or mapping ``device``."""
    current_system = sys.platform if system is None else system
    current_machine = platform.machine() if machine is None else machine
    current_kernel = platform.release() if kernel_release is None else kernel_release
    if current_system != "linux":
        raise Kv260PreflightError("KV260 preflight requires Linux")
    if current_machine != "aarch64":
        raise Kv260PreflightError("KV260 preflight requires Linux aarch64")
    if _KERNEL_RELEASE.fullmatch(current_kernel) is None:
        raise Kv260PreflightError("kernel release is not one bounded token")

    match = _UIO_PATH.fullmatch(device)
    if match is None:
        raise Kv260PreflightError("UIO path must be canonical /dev/uioN")
    number = int(match.group("number"))
    inspect_stat = os.lstat if lstat_fn is None else lstat_fn
    try:
        device_stat = inspect_stat(device)
    except OSError as error:
        raise Kv260PreflightError("UIO device identity is unavailable") from error
    if not stat.S_ISCHR(device_stat.st_mode):
        raise Kv260PreflightError("UIO path is not a character device")
    if os.minor(device_stat.st_rdev) != number:
        raise Kv260PreflightError("UIO path number differs from device minor")

    uio_root = sys_root / "class" / "uio" / f"uio{number}"
    identity = _read_line(uio_root / "dev")
    identity_match = _DEVICE_ID.fullmatch(identity)
    if identity_match is None:
        raise Kv260PreflightError("UIO sysfs device identity is malformed")
    sys_major = int(identity_match.group("major"))
    sys_minor = int(identity_match.group("minor"))
    if (sys_major, sys_minor) != (
        os.major(device_stat.st_rdev),
        os.minor(device_stat.st_rdev),
    ):
        raise Kv260PreflightError("UIO sysfs and device identities differ")

    map_root = uio_root / "maps" / "map0"
    map_address = _parse_hex(map_root / "addr")
    map_size = _parse_hex(map_root / "size")
    if map_size != _APERTURE_BYTES:
        raise Kv260PreflightError("UIO map 0 must be exactly 0x4000 bytes")
    if map_address % _APERTURE_BYTES != 0:
        raise Kv260PreflightError("UIO map 0 address must be 0x4000-aligned")

    _, model_sha256 = _model(proc_root / "device-tree" / "model")
    manager_state = _read_line(sys_root / "class" / "fpga_manager" / "fpga0" / "state")
    if _MANAGER_STATE.fullmatch(manager_state) is None:
        raise Kv260PreflightError("FPGA manager state is not bounded printable text")

    return {
        "machine": current_machine,
        "kernel": current_kernel,
        "model_sha256": model_sha256,
        "uio": device,
        "device": f"{sys_major}:{sys_minor}",
        "map0_addr": f"0x{map_address:x}",
        "map0_size": f"0x{map_size:x}",
        "fpga_manager_state": manager_state.lower().replace(" ", "_"),
    }


def render_preflight(device: str) -> str:
    value = collect_preflight(device)
    return (
        "KV260-PREFLIGHT-V1 status=PASS "
        f"machine={value['machine']} kernel={value['kernel']} "
        f"model_sha256={value['model_sha256']} uio={value['uio']} "
        f"device={value['device']} map0_addr={value['map0_addr']} "
        f"map0_size={value['map0_size']} "
        f"fpga_manager_state={value['fpga_manager_state']} "
        "device_opened=0 mmio=0 evidence=target-host-observation "
        "performance=not-measured"
    )
