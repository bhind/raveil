"""Source-bound offline board boundary bundle; not a synthesized board design.

Private cooperative directories only, like the underlying RTL export. Hashes
bind local inputs, not a signature or proof that a vendor accepted the design.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import tempfile

from raveil import graph_device_axi4lite_export as rtl

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "raveil.graph-device-board-bundle/v1"
TEMPLATES = {
    "graph_device_board_bridge.sv": "hardware/fpga/graph_device_board_bridge.sv",
    "synth_board_bridge.tcl": "hardware/fpga/synth_board_bridge.tcl",
}


class BoardBundleError(ValueError):
    pass


def _settings(base: int, clock_mhz: int) -> bytes:
    if type(base) is not int or not 0 <= base <= 0xffffc000 or base % 0x4000:
        raise BoardBundleError("base must be an aligned 32-bit 16 KiB window")
    if type(clock_mhz) is not int or not 1 <= clock_mhz <= 1000:
        raise BoardBundleError("clock must be an integer target in 1..1000 MHz")
    return f"base={base:08x}\nclock_mhz={clock_mhz}\n".encode("ascii")


def _xdc(clock_mhz: int) -> bytes:
    # Target constraint only; no claim of timing closure.
    return f"create_clock -name board_clock -period {1000 / clock_mhz:.9f} [get_ports aclk]\n".encode("ascii")


def _source() -> str:
    return rtl._sha(ROOT / "raveil/graph_device_board_bundle.py")


def verify(bundle: Path) -> dict:
    manifest = json.loads(rtl._regular(bundle / "manifest.json"))
    if set(manifest) != {"schema", "base", "clock_mhz", "source_sha256", "core_source_sha256", "core_rtl_sha256", "files"} or manifest["schema"] != SCHEMA:
        raise BoardBundleError("invalid board manifest")
    if manifest["files"] != rtl._tree(bundle, omit_manifest=True):
        raise BoardBundleError("board tree or digest mismatch")
    allowed = {"core", *TEMPLATES, "settings.txt", "clock.xdc"}
    if {p.name for p in bundle.iterdir()} != allowed | {"manifest.json"}:
        raise BoardBundleError("unexpected board entry")
    if manifest["source_sha256"] != _source():
        raise BoardBundleError("board generator source differs")
    for name, rel in TEMPLATES.items():
        if rtl._regular(bundle / name) != rtl._regular(ROOT / rel):
            raise BoardBundleError("board template differs")
    expected = _settings(manifest["base"], manifest["clock_mhz"])
    if rtl._regular(bundle / "settings.txt") != expected or rtl._regular(bundle / "clock.xdc") != _xdc(manifest["clock_mhz"]):
        raise BoardBundleError("board settings or clock differs")
    core = rtl.verify(bundle / "core")
    if (manifest["core_source_sha256"], manifest["core_rtl_sha256"]) != (core["source_sha256"], core["rtl_manifest_sha256"]):
        raise BoardBundleError("core identity differs")
    return manifest


def create(export: Path, output: Path, *, base: int, clock_mhz: int) -> dict:
    settings = _settings(base, clock_mhz)
    core = rtl.verify(export)
    # Delegate final publication's artifacts confinement and no-replacement rule.
    with tempfile.TemporaryDirectory(prefix="raveil-board-") as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        shutil.copytree(export, staging / "core", symlinks=True)
        for name, rel in TEMPLATES.items():
            rtl._exclusive(staging / name, rtl._regular(ROOT / rel))
        rtl._exclusive(staging / "settings.txt", settings)
        rtl._exclusive(staging / "clock.xdc", _xdc(clock_mhz))
        manifest = {
            "schema": SCHEMA, "base": base, "clock_mhz": clock_mhz,
            "source_sha256": _source(), "core_source_sha256": core["source_sha256"],
            "core_rtl_sha256": core["rtl_manifest_sha256"], "files": rtl._tree(staging),
        }
        rtl._exclusive(staging / "manifest.json", rtl._canonical(manifest))
        verify(staging)
        # rtl.publish verifies an RTL-only manifest, so use its confined path
        # validation rules here with an exclusive target directory.
        if output.is_symlink() or output.exists():
            raise BoardBundleError("output already exists")
        target = output.resolve()
        artifacts = (ROOT / "artifacts").resolve()
        if not target.is_relative_to(artifacts) or target == artifacts:
            raise BoardBundleError("output must be below repository artifacts")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir()
        try:
            shutil.copytree(staging, target, dirs_exist_ok=True)
            return verify(target)
        except BaseException:
            shutil.rmtree(target)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("create")
    make.add_argument("export", type=Path); make.add_argument("output", type=Path)
    make.add_argument("--base", type=lambda value: int(value, 0), required=True)
    make.add_argument("--clock-mhz", type=int, required=True)
    check = commands.add_parser("verify"); check.add_argument("bundle", type=Path)
    args = parser.parse_args()
    if args.command == "create":
        result = create(args.export, args.output, base=args.base, clock_mhz=args.clock_mhz)
    else:
        result = verify(args.bundle)
    print(json.dumps({"status": "OK", "schema": result["schema"], "base": result["base"], "evidence": "source-bundle-only"}, sort_keys=True))


if __name__ == "__main__":
    main()
