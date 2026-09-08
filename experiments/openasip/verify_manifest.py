#!/usr/bin/env python3
"""Fail-closed identity validation for the T-0191 external-tool scaffold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"
EXPECTED_OPENASIP = "f2282048f4c78d18190a9b77e7497e29a164721d"
EXPECTED_LLVM = "b47e651cc052ba9e097701efa8840e8f3081c84d"


def load_manifest() -> dict[str, Any]:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("manifest must be an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(*, require_container: bool) -> dict[str, Any]:
    value = load_manifest()
    if value.get("schema") != "raveil.t0191-openasip-input/v1":
        raise ValueError("manifest schema is not exact")
    if value.get("task") != "T-0191":
        raise ValueError("task identity is not exact")
    if value.get("upstream", {}).get("revision") != EXPECTED_OPENASIP:
        raise ValueError("OpenASIP revision is not exact")
    if value.get("llvm", {}).get("revision") != EXPECTED_LLVM:
        raise ValueError("LLVM revision is not exact")
    programs = value.get("programs")
    if not isinstance(programs, list) or len(programs) != 3 or len(set(programs)) != 3:
        raise ValueError("exactly three unique programs are required")
    receipts = value.get("program_receipts")
    if not isinstance(receipts, dict) or set(receipts) != set(programs):
        raise ValueError("program receipts are not exact")
    hashes: dict[str, str] = {}
    program_root = (ROOT / "programs").resolve(strict=True)
    for relative in programs:
        if not isinstance(relative, str):
            raise ValueError("program path is outside the allowlist")
        relative_path = Path(relative)
        if (
            relative_path.is_absolute()
            or relative_path.parts[:1] != ("programs",)
            or any(part in {"", ".", ".."} for part in relative_path.parts)
            or relative_path.suffix != ".c"
        ):
            raise ValueError("program path is outside the allowlist")
        path = ROOT / relative_path
        resolved = path.resolve(strict=True)
        if (
            not resolved.is_relative_to(program_root)
            or resolved != path.absolute()
            or not path.is_file()
            or path.is_symlink()
        ):
            raise ValueError(f"program is not an exact regular file: {relative}")
        digest = sha256(path)
        expected = receipts.get(relative)
        receipt_fields = {
            "bytes", "sha256", "topology", "dependence", "access_footprint",
            "input_bytes", "result_bytes",
        }
        if not isinstance(expected, dict) or set(expected) != receipt_fields:
            raise ValueError(f"program receipt is malformed: {relative}")
        if expected["bytes"] != path.stat().st_size or expected["bytes"] > 4096:
            raise ValueError(f"program size is not exact and bounded: {relative}")
        if expected["sha256"] != digest:
            raise ValueError(f"program hash is not exact: {relative}")
        if not all(
            isinstance(expected[field], str) and expected[field]
            for field in ("topology", "dependence", "access_footprint")
        ):
            raise ValueError(f"program feature matrix is malformed: {relative}")
        if (
            not isinstance(expected["input_bytes"], int)
            or expected["input_bytes"] <= 0
            or expected["result_bytes"] != 4
        ):
            raise ValueError(f"program byte footprint is malformed: {relative}")
        hashes[relative] = digest
    authority = value.get("authority", {})
    if set(authority) != {
        "upstream_output_private_until_oracle",
        "cpu_fallback_owned",
        "publication_owned_by_raveil",
    } or not all(item is True for item in authority.values()):
        raise ValueError("authority boundary is incomplete")
    container = value.get("container", {})
    if container.get("platform") != "linux/amd64":
        raise ValueError("container platform is not exact")
    image = container.get("base_image")
    if set(container) != {
        "platform", "base_image", "base_identity_source",
        "identity_observed_at", "status",
    }:
        raise ValueError("container identity fields are not exact")
    if (
        container.get("status") != "pinned"
        or not isinstance(image, str)
        or "@sha256:" not in image
    ):
        raise ValueError("container base image is not pinned")
    return {"manifest_sha256": sha256(MANIFEST), "program_sha256": hashes}


def main() -> None:
    print(json.dumps(validate(require_container=True), sort_keys=True))


if __name__ == "__main__":
    main()
